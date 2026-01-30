"""
TB Personal OS - Autonomy Service
Sistema de níveis de autonomia do assistente
"""

import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import IntEnum
import pytz

from supabase import Client, create_client
from app.core.config import settings

logger = structlog.get_logger(__name__)


class AutonomyLevel(IntEnum):
    """
    Níveis de autonomia do assistente.
    
    1 - OBSERVADOR: Apenas observa e reporta
    2 - SUGESTOR: Sugere ações, mas não executa
    3 - CONFIRMADOR: Executa após confirmação
    4 - EXECUTOR: Executa ações comuns automaticamente
    5 - PROATIVO: Antecipa necessidades e age
    """
    OBSERVER = 1      # Apenas observa e reporta
    SUGGESTER = 2     # Sugere ações
    CONFIRMER = 3     # Executa após confirmação
    EXECUTOR = 4      # Executa automaticamente
    PROACTIVE = 5     # Antecipa e age


# Definição das ações e seus níveis mínimos
ACTION_LEVELS = {
    # Leitura - sempre permitido
    "read_tasks": AutonomyLevel.OBSERVER,
    "read_calendar": AutonomyLevel.OBSERVER,
    "read_emails": AutonomyLevel.OBSERVER,
    "read_inbox": AutonomyLevel.OBSERVER,
    "read_finances": AutonomyLevel.OBSERVER,
    
    # Sugestões
    "suggest_task_priority": AutonomyLevel.SUGGESTER,
    "suggest_schedule": AutonomyLevel.SUGGESTER,
    "suggest_email_response": AutonomyLevel.SUGGESTER,
    "suggest_content": AutonomyLevel.SUGGESTER,
    
    # Criação com confirmação
    "create_task": AutonomyLevel.CONFIRMER,
    "create_event": AutonomyLevel.CONFIRMER,
    "create_draft": AutonomyLevel.CONFIRMER,
    "create_idea": AutonomyLevel.CONFIRMER,
    "create_transaction": AutonomyLevel.CONFIRMER,
    
    # Edição automática
    "update_task_status": AutonomyLevel.EXECUTOR,
    "reschedule_event": AutonomyLevel.EXECUTOR,
    "mark_email_read": AutonomyLevel.EXECUTOR,
    "archive_email": AutonomyLevel.EXECUTOR,
    "complete_task": AutonomyLevel.EXECUTOR,
    
    # Proativo
    "auto_schedule_tasks": AutonomyLevel.PROACTIVE,
    "send_reminders": AutonomyLevel.PROACTIVE,
    "auto_respond_email": AutonomyLevel.PROACTIVE,
    "auto_reschedule": AutonomyLevel.PROACTIVE,
    "auto_categorize": AutonomyLevel.PROACTIVE,
}


class AutonomyService:
    """
    Serviço de controle de autonomia.
    
    Controla o que o assistente pode fazer baseado no nível
    de autonomia configurado pelo usuário.
    """
    
    def __init__(self, supabase: Optional[Client] = None):
        self._supabase = supabase
    
    @property
    def supabase(self) -> Client:
        """Lazy load Supabase client."""
        if self._supabase is None:
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return self._supabase
    
    async def get_user_autonomy_level(self, user_id: str) -> int:
        """Obtém o nível de autonomia do usuário."""
        try:
            result = self.supabase.table("profiles") \
                .select("autonomy_level") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            
            if result.data:
                return result.data.get("autonomy_level", AutonomyLevel.SUGGESTER)
            
            return AutonomyLevel.SUGGESTER  # Default
            
        except Exception as e:
            logger.error("get_autonomy_level_failed", user_id=user_id, error=str(e))
            return AutonomyLevel.SUGGESTER
    
    async def set_user_autonomy_level(
        self,
        user_id: str,
        level: int
    ) -> bool:
        """Define o nível de autonomia do usuário."""
        try:
            # Validar nível
            if level < 1 or level > 5:
                raise ValueError(f"Nível inválido: {level}. Use 1-5.")
            
            result = self.supabase.table("profiles") \
                .update({
                    "autonomy_level": level,
                    "updated_at": datetime.utcnow().isoformat()
                }) \
                .eq("user_id", user_id) \
                .execute()
            
            if result.data:
                logger.info("autonomy_level_updated", 
                           user_id=user_id, 
                           level=level,
                           level_name=AutonomyLevel(level).name)
                return True
            
            return False
            
        except Exception as e:
            logger.error("set_autonomy_level_failed", user_id=user_id, error=str(e))
            raise
    
    async def can_perform_action(
        self,
        user_id: str,
        action: str
    ) -> Dict[str, Any]:
        """
        Verifica se o assistente pode executar uma ação.
        
        Args:
            user_id: ID do usuário
            action: Nome da ação (ex: "create_task")
            
        Returns:
            Dict com:
            - allowed: bool - se pode executar
            - requires_confirmation: bool - se precisa confirmar
            - reason: str - explicação
        """
        try:
            user_level = await self.get_user_autonomy_level(user_id)
            required_level = ACTION_LEVELS.get(action, AutonomyLevel.CONFIRMER)
            
            if user_level >= required_level:
                # Pode executar
                return {
                    "allowed": True,
                    "requires_confirmation": False,
                    "action": action,
                    "user_level": user_level,
                    "required_level": required_level,
                    "reason": "Ação permitida no seu nível de autonomia"
                }
            elif user_level >= required_level - 1:
                # Pode, mas precisa confirmar
                return {
                    "allowed": True,
                    "requires_confirmation": True,
                    "action": action,
                    "user_level": user_level,
                    "required_level": required_level,
                    "reason": "Ação requer sua confirmação"
                }
            else:
                # Não permitido
                return {
                    "allowed": False,
                    "requires_confirmation": False,
                    "action": action,
                    "user_level": user_level,
                    "required_level": required_level,
                    "reason": f"Ação requer nível {required_level} ({AutonomyLevel(required_level).name})"
                }
                
        except Exception as e:
            logger.error("can_perform_action_failed", 
                        user_id=user_id, 
                        action=action, 
                        error=str(e))
            return {
                "allowed": False,
                "requires_confirmation": True,
                "reason": "Erro ao verificar permissão"
            }
    
    async def get_allowed_actions(
        self,
        user_id: str
    ) -> Dict[str, List[str]]:
        """
        Lista todas as ações permitidas para o usuário.
        
        Returns:
            Dict com categorias:
            - automatic: Ações que podem ser executadas sem perguntar
            - with_confirmation: Ações que precisam confirmação
            - not_allowed: Ações não permitidas
        """
        try:
            user_level = await self.get_user_autonomy_level(user_id)
            
            automatic = []
            with_confirmation = []
            not_allowed = []
            
            for action, required_level in ACTION_LEVELS.items():
                if user_level >= required_level:
                    automatic.append(action)
                elif user_level >= required_level - 1:
                    with_confirmation.append(action)
                else:
                    not_allowed.append(action)
            
            return {
                "user_level": user_level,
                "user_level_name": AutonomyLevel(user_level).name,
                "automatic": sorted(automatic),
                "with_confirmation": sorted(with_confirmation),
                "not_allowed": sorted(not_allowed)
            }
            
        except Exception as e:
            logger.error("get_allowed_actions_failed", user_id=user_id, error=str(e))
            raise
    
    def get_level_description(self, level: int) -> Dict[str, Any]:
        """Obtém descrição detalhada de um nível."""
        descriptions = {
            1: {
                "level": 1,
                "name": "Observador",
                "code": "OBSERVER",
                "description": "O assistente apenas observa e reporta. Não faz sugestões proativas.",
                "examples": [
                    "Responde quando perguntado",
                    "Mostra informações solicitadas",
                    "Não sugere ações"
                ]
            },
            2: {
                "level": 2,
                "name": "Sugestor",
                "code": "SUGGESTER",
                "description": "O assistente sugere ações, mas nunca executa sem pedir.",
                "examples": [
                    "Sugere tarefas baseado no contexto",
                    "Recomenda horários para eventos",
                    "Propõe respostas para emails"
                ]
            },
            3: {
                "level": 3,
                "name": "Confirmador",
                "code": "CONFIRMER",
                "description": "O assistente pode executar ações após sua confirmação.",
                "examples": [
                    "Cria tarefas se você confirmar",
                    "Agenda eventos com sua aprovação",
                    "Salva rascunhos de email"
                ]
            },
            4: {
                "level": 4,
                "name": "Executor",
                "code": "EXECUTOR",
                "description": "O assistente executa ações comuns automaticamente.",
                "examples": [
                    "Marca tarefas como concluídas",
                    "Reorganiza agenda automaticamente",
                    "Arquiva emails processados"
                ]
            },
            5: {
                "level": 5,
                "name": "Proativo",
                "code": "PROACTIVE",
                "description": "O assistente antecipa necessidades e age preventivamente.",
                "examples": [
                    "Agenda tarefas automaticamente",
                    "Envia lembretes proativos",
                    "Responde emails de rotina"
                ]
            }
        }
        return descriptions.get(level, descriptions[2])
    
    def get_all_levels(self) -> List[Dict[str, Any]]:
        """Lista todos os níveis de autonomia."""
        return [self.get_level_description(i) for i in range(1, 6)]
    
    async def log_action(
        self,
        user_id: str,
        action: str,
        was_automatic: bool,
        was_confirmed: bool,
        details: Optional[Dict] = None
    ) -> None:
        """
        Registra uma ação executada para auditoria.
        """
        try:
            self.supabase.table("assistant_logs").insert({
                "user_id": user_id,
                "action_type": "autonomy_action",
                "input_data": {
                    "action": action,
                    "automatic": was_automatic,
                    "confirmed": was_confirmed
                },
                "output_data": details or {},
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
        except Exception as e:
            logger.error("log_action_failed", user_id=user_id, error=str(e))
    
    async def get_action_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Obtém histórico de ações automáticas."""
        try:
            result = self.supabase.table("assistant_logs") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("action_type", "autonomy_action") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error("get_action_history_failed", user_id=user_id, error=str(e))
            return []


# Singleton
autonomy_service = AutonomyService()
