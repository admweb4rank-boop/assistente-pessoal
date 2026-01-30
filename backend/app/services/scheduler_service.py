"""
TB Personal OS - Scheduler Service
Gerencia rotinas automáticas (manhã, noite, semanal)
"""

import structlog
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import pytz

from app.core.config import settings

logger = structlog.get_logger(__name__)


class SchedulerService:
    """
    Serviço de agendamento de rotinas automáticas.
    Usa APScheduler para jobs em background.
    """
    
    _instance: Optional['SchedulerService'] = None
    _scheduler: Optional[BackgroundScheduler] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if SchedulerService._initialized:
            return
        
        self.timezone = pytz.timezone(settings.OWNER_TIMEZONE)
        self._jobs: Dict[str, Any] = {}
        self._callbacks: Dict[str, Callable] = {}
        
        logger.info(
            "scheduler_service_created",
            timezone=str(self.timezone)
        )
        SchedulerService._initialized = True
    
    @property
    def scheduler(self) -> BackgroundScheduler:
        """Lazy load do scheduler."""
        if SchedulerService._scheduler is None:
            SchedulerService._scheduler = BackgroundScheduler(
                timezone=self.timezone,
                job_defaults={
                    'coalesce': True,
                    'max_instances': 1,
                    'misfire_grace_time': 60 * 15  # 15 minutos de tolerância
                }
            )
            logger.info("scheduler_created")
        return SchedulerService._scheduler
    
    def start(self):
        """Inicia o scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("scheduler_started")
    
    def stop(self):
        """Para o scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("scheduler_stopped")
    
    def register_callback(self, job_type: str, callback: Callable):
        """
        Registra um callback para um tipo de job.
        
        Args:
            job_type: 'morning', 'night', 'weekly', 'custom'
            callback: Função a ser chamada (deve aceitar user_id como arg)
        """
        self._callbacks[job_type] = callback
        logger.info("callback_registered", job_type=job_type)
    
    def schedule_morning_routine(
        self,
        user_id: str,
        hour: int = 7,
        minute: int = 0
    ) -> str:
        """
        Agenda rotina da manhã.
        
        Args:
            user_id: ID do usuário
            hour: Hora (0-23)
            minute: Minuto (0-59)
        
        Returns:
            Job ID
        """
        job_id = f"morning_{user_id}"
        
        # Remover job anterior se existir
        self._remove_job_if_exists(job_id)
        
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=self.timezone
        )
        
        job = self.scheduler.add_job(
            self._execute_morning_routine,
            trigger=trigger,
            id=job_id,
            args=[user_id],
            name=f"Morning Routine - {user_id}"
        )
        
        self._jobs[job_id] = {
            "type": "morning",
            "user_id": user_id,
            "schedule": f"{hour:02d}:{minute:02d}",
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        }
        
        logger.info(
            "morning_routine_scheduled",
            user_id=user_id,
            schedule=f"{hour:02d}:{minute:02d}",
            next_run=self._jobs[job_id]["next_run"]
        )
        
        return job_id
    
    def schedule_night_routine(
        self,
        user_id: str,
        hour: int = 21,
        minute: int = 0
    ) -> str:
        """
        Agenda rotina da noite.
        """
        job_id = f"night_{user_id}"
        
        self._remove_job_if_exists(job_id)
        
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=self.timezone
        )
        
        job = self.scheduler.add_job(
            self._execute_night_routine,
            trigger=trigger,
            id=job_id,
            args=[user_id],
            name=f"Night Routine - {user_id}"
        )
        
        self._jobs[job_id] = {
            "type": "night",
            "user_id": user_id,
            "schedule": f"{hour:02d}:{minute:02d}",
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        }
        
        logger.info(
            "night_routine_scheduled",
            user_id=user_id,
            schedule=f"{hour:02d}:{minute:02d}"
        )
        
        return job_id
    
    def schedule_weekly_planning(
        self,
        user_id: str,
        day_of_week: str = "sun",
        hour: int = 19,
        minute: int = 0
    ) -> str:
        """
        Agenda planejamento semanal.
        
        Args:
            day_of_week: 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'
        """
        job_id = f"weekly_{user_id}"
        
        self._remove_job_if_exists(job_id)
        
        trigger = CronTrigger(
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            timezone=self.timezone
        )
        
        job = self.scheduler.add_job(
            self._execute_weekly_planning,
            trigger=trigger,
            id=job_id,
            args=[user_id],
            name=f"Weekly Planning - {user_id}"
        )
        
        self._jobs[job_id] = {
            "type": "weekly",
            "user_id": user_id,
            "schedule": f"{day_of_week} {hour:02d}:{minute:02d}",
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        }
        
        logger.info(
            "weekly_planning_scheduled",
            user_id=user_id,
            schedule=f"{day_of_week} {hour:02d}:{minute:02d}"
        )
        
        return job_id
    
    def schedule_custom_job(
        self,
        job_id: str,
        callback: Callable,
        cron_expression: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        Agenda um job customizado.
        
        Args:
            job_id: ID único do job
            callback: Função a executar
            cron_expression: Dict com parâmetros do CronTrigger
            **kwargs: Argumentos para o callback
        """
        self._remove_job_if_exists(job_id)
        
        trigger = CronTrigger(
            timezone=self.timezone,
            **cron_expression
        )
        
        job = self.scheduler.add_job(
            callback,
            trigger=trigger,
            id=job_id,
            kwargs=kwargs,
            name=f"Custom Job - {job_id}"
        )
        
        self._jobs[job_id] = {
            "type": "custom",
            "schedule": str(cron_expression),
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        }
        
        logger.info("custom_job_scheduled", job_id=job_id)
        
        return job_id
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancela um job agendado."""
        try:
            self.scheduler.remove_job(job_id)
            self._jobs.pop(job_id, None)
            logger.info("job_cancelled", job_id=job_id)
            return True
        except Exception as e:
            logger.error("job_cancel_failed", job_id=job_id, error=str(e))
            return False
    
    def get_scheduled_jobs(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Lista jobs agendados."""
        if user_id:
            return {
                k: v for k, v in self._jobs.items()
                if v.get("user_id") == user_id
            }
        return self._jobs.copy()
    
    def get_next_run(self, job_id: str) -> Optional[datetime]:
        """Obtém a próxima execução de um job."""
        try:
            job = self.scheduler.get_job(job_id)
            return job.next_run_time if job else None
        except:
            return None
    
    def run_job_now(self, job_type: str, user_id: str) -> bool:
        """
        Executa um job imediatamente (para testes).
        """
        try:
            if job_type == "morning":
                self._execute_morning_routine(user_id)
            elif job_type == "night":
                self._execute_night_routine(user_id)
            elif job_type == "weekly":
                self._execute_weekly_planning(user_id)
            else:
                logger.warning("unknown_job_type", job_type=job_type)
                return False
            return True
        except Exception as e:
            logger.error("run_job_now_failed", job_type=job_type, error=str(e))
            return False
    
    # ==========================================
    # JOB EXECUTORS
    # ==========================================
    
    def _execute_morning_routine(self, user_id: str):
        """Executa a rotina da manhã."""
        logger.info("executing_morning_routine", user_id=user_id)
        
        try:
            if "morning" in self._callbacks:
                self._callbacks["morning"](user_id)
            else:
                # Fallback - importar e executar
                from app.jobs.morning_routine import run_morning_routine
                run_morning_routine(user_id)
                
        except Exception as e:
            logger.error("morning_routine_failed", user_id=user_id, error=str(e))
    
    def _execute_night_routine(self, user_id: str):
        """Executa a rotina da noite."""
        logger.info("executing_night_routine", user_id=user_id)
        
        try:
            if "night" in self._callbacks:
                self._callbacks["night"](user_id)
            else:
                from app.jobs.night_routine import run_night_routine
                run_night_routine(user_id)
                
        except Exception as e:
            logger.error("night_routine_failed", user_id=user_id, error=str(e))
    
    def _execute_weekly_planning(self, user_id: str):
        """Executa o planejamento semanal."""
        logger.info("executing_weekly_planning", user_id=user_id)
        
        try:
            if "weekly" in self._callbacks:
                self._callbacks["weekly"](user_id)
            else:
                from app.jobs.weekly_planning import run_weekly_planning
                run_weekly_planning(user_id)
                
        except Exception as e:
            logger.error("weekly_planning_failed", user_id=user_id, error=str(e))
    
    def _remove_job_if_exists(self, job_id: str):
        """Remove um job se existir."""
        try:
            self.scheduler.remove_job(job_id)
            self._jobs.pop(job_id, None)
        except:
            pass
    
    # ==========================================
    # APRENDIZADO AUTOMÁTICO
    # ==========================================
    
    def schedule_pattern_learning(
        self,
        user_id: str,
        hour: int = 23,
        minute: int = 30
    ) -> str:
        """
        Agenda análise de padrões diária.
        Roda automaticamente toda noite para aprender com as interações do dia.
        """
        job_id = f"pattern_learning_{user_id}"
        
        self._remove_job_if_exists(job_id)
        
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=self.timezone
        )
        
        job = self.scheduler.add_job(
            self._execute_pattern_learning,
            trigger=trigger,
            id=job_id,
            args=[user_id],
            name=f"Pattern Learning - {user_id}"
        )
        
        self._jobs[job_id] = {
            "type": "pattern_learning",
            "user_id": user_id,
            "schedule": f"{hour:02d}:{minute:02d}",
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        }
        
        logger.info(
            "pattern_learning_scheduled",
            user_id=user_id,
            schedule=f"{hour:02d}:{minute:02d}"
        )
        
        return job_id
    
    def schedule_proactive_suggestions(
        self,
        user_id: str,
        hours: list = None,
        minute: int = 30
    ) -> list:
        """
        Agenda envio de sugestões proativas em horários específicos.
        """
        hours = hours or [8, 14]  # Manhã e tarde por padrão
        job_ids = []
        
        for hour in hours:
            job_id = f"proactive_{user_id}_{hour}"
            
            self._remove_job_if_exists(job_id)
            
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                timezone=self.timezone
            )
            
            job = self.scheduler.add_job(
                self._execute_proactive_suggestions,
                trigger=trigger,
                id=job_id,
                args=[user_id, hour],
                name=f"Proactive Suggestions {hour}h - {user_id}"
            )
            
            self._jobs[job_id] = {
                "type": "proactive_suggestions",
                "user_id": user_id,
                "schedule": f"{hour:02d}:{minute:02d}",
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            
            job_ids.append(job_id)
            
            logger.info(
                "proactive_suggestions_scheduled",
                user_id=user_id,
                schedule=f"{hour:02d}:{minute:02d}"
            )
        
        return job_ids
    
    def _execute_pattern_learning(self, user_id: str):
        """Executa análise de padrões automaticamente."""
        logger.info("executing_pattern_learning", user_id=user_id)
        
        try:
            import asyncio
            from app.jobs.pattern_analysis import pattern_analysis_job
            
            # Executar análise assíncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(pattern_analysis_job.run(user_id))
                logger.info("pattern_learning_completed", user_id=user_id, result=result)
            finally:
                loop.close()
                
        except Exception as e:
            logger.error("pattern_learning_failed", user_id=user_id, error=str(e))
    
    def _execute_proactive_suggestions(self, user_id: str, hour: int):
        """Envia sugestões proativas baseadas nos padrões aprendidos."""
        logger.info("executing_proactive_suggestions", user_id=user_id, hour=hour)
        
        try:
            import asyncio
            from app.services.proactive_service import proactive_service
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    proactive_service.send_contextual_suggestions(user_id, hour)
                )
            finally:
                loop.close()
                
        except Exception as e:
            logger.error("proactive_suggestions_failed", user_id=user_id, error=str(e))


# Instância global
scheduler_service = SchedulerService()


def init_default_schedules(user_id: str = None):
    """
    Inicializa as rotinas padrão para o owner.
    Chamado no startup da aplicação.
    """
    target_user_id = user_id or settings.OWNER_USER_ID or "11111111-1111-1111-1111-111111111111"
    
    # Iniciar scheduler se não estiver rodando
    scheduler_service.start()
    
    # Agendar rotinas padrão
    scheduler_service.schedule_morning_routine(target_user_id, hour=7, minute=0)
    scheduler_service.schedule_night_routine(target_user_id, hour=21, minute=0)
    scheduler_service.schedule_weekly_planning(target_user_id, day_of_week="sun", hour=19, minute=0)
    
    # Agendar aprendizado automático (todo dia às 23:30)
    scheduler_service.schedule_pattern_learning(target_user_id, hour=23, minute=30)
    
    # Agendar sugestões proativas (todo dia às 8:30 e 14:00)
    scheduler_service.schedule_proactive_suggestions(target_user_id, hours=[8, 14], minute=30)
    
    logger.info(
        "default_schedules_initialized",
        user_id=target_user_id,
        jobs=list(scheduler_service.get_scheduled_jobs().keys())
    )
