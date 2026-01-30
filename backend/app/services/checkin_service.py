"""
TB Personal OS - Check-in Service
Gerencia check-ins de energia, humor, sono, etc.
"""

import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from supabase import Client, create_client

from app.core.config import settings

logger = structlog.get_logger(__name__)


class CheckinService:
    """
    Serviço de check-ins.
    Registra e analisa dados de bem-estar do usuário.
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
    
    # ==========================================
    # CRUD OPERATIONS
    # ==========================================
    
    async def create_checkin(
        self,
        user_id: str,
        checkin_type: str,
        value: Any,
        notes: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Cria um novo check-in.
        
        Args:
            user_id: ID do usuário
            checkin_type: Tipo (energy, mood, sleep, workout, custom)
            value: Valor (número 1-10, texto, ou dict)
            notes: Notas adicionais
            metadata: Dados extras
        
        Returns:
            Check-in criado
        """
        try:
            # Normalizar valor
            normalized_value = self._normalize_value(checkin_type, value)
            
            data = {
                "user_id": user_id,
                "checkin_type": checkin_type,
                "value": normalized_value,
                "notes": notes,
                "metadata": metadata or {},
                "checkin_date": date.today().isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("checkins").insert(data).execute()
            
            logger.info(
                "checkin_created",
                user_id=user_id,
                type=checkin_type,
                value=normalized_value
            )
            
            return result.data[0] if result.data else data
            
        except Exception as e:
            logger.error("create_checkin_failed", error=str(e))
            raise
    
    async def get_checkins(
        self,
        user_id: str,
        checkin_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Lista check-ins do usuário.
        """
        try:
            query = self.supabase.table("checkins")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)
            
            if checkin_type:
                query = query.eq("checkin_type", checkin_type)
            
            if start_date:
                query = query.gte("checkin_date", start_date.isoformat())
            
            if end_date:
                query = query.lte("checkin_date", end_date.isoformat())
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error("get_checkins_failed", error=str(e))
            return []
    
    async def get_today_checkins(self, user_id: str) -> Dict[str, Any]:
        """
        Retorna check-ins de hoje organizados por tipo.
        """
        today = date.today()
        checkins = await self.get_checkins(
            user_id,
            start_date=today,
            end_date=today
        )
        
        result = {}
        for checkin in checkins:
            ctype = checkin.get("checkin_type")
            if ctype not in result:
                result[ctype] = checkin
        
        return result
    
    async def get_checkin_stats(
        self,
        user_id: str,
        checkin_type: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Calcula estatísticas de check-ins.
        """
        start_date = date.today() - timedelta(days=days)
        
        checkins = await self.get_checkins(
            user_id,
            checkin_type=checkin_type,
            start_date=start_date,
            limit=days * 3  # Pode ter múltiplos por dia
        )
        
        if not checkins:
            return {
                "type": checkin_type,
                "period_days": days,
                "count": 0,
                "average": None,
                "min": None,
                "max": None,
                "trend": None
            }
        
        # Extrair valores numéricos
        values = []
        for c in checkins:
            v = c.get("value")
            if isinstance(v, (int, float)):
                values.append(v)
            elif isinstance(v, dict) and "score" in v:
                values.append(v["score"])
        
        if not values:
            return {
                "type": checkin_type,
                "period_days": days,
                "count": len(checkins),
                "average": None,
                "min": None,
                "max": None,
                "trend": None
            }
        
        avg = sum(values) / len(values)
        
        # Calcular tendência
        trend = None
        if len(values) >= 3:
            first_half = sum(values[:len(values)//2]) / (len(values)//2)
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            diff = second_half - first_half
            
            if diff > 0.5:
                trend = "up"
            elif diff < -0.5:
                trend = "down"
            else:
                trend = "stable"
        
        return {
            "type": checkin_type,
            "period_days": days,
            "count": len(checkins),
            "average": round(avg, 2),
            "min": min(values),
            "max": max(values),
            "trend": trend,
            "values": values[-7:]  # Últimos 7 valores
        }
    
    # ==========================================
    # SPECIFIC CHECK-INS
    # ==========================================
    
    async def checkin_energy(
        self,
        user_id: str,
        level: int,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check-in de energia (1-10).
        """
        if not 1 <= level <= 10:
            raise ValueError("Nível de energia deve ser entre 1 e 10")
        
        return await self.create_checkin(
            user_id=user_id,
            checkin_type="energy",
            value=level,
            notes=notes
        )
    
    async def checkin_mood(
        self,
        user_id: str,
        mood: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check-in de humor.
        
        Aceita emoji ou texto:
        - 😊 / happy / feliz
        - 😐 / neutral / normal
        - 😢 / sad / triste
        - 😤 / angry / irritado
        - 😴 / tired / cansado
        - 🤩 / excited / empolgado
        """
        mood_map = {
            "😊": {"mood": "happy", "score": 8},
            "happy": {"mood": "happy", "score": 8},
            "feliz": {"mood": "happy", "score": 8},
            "😐": {"mood": "neutral", "score": 5},
            "neutral": {"mood": "neutral", "score": 5},
            "normal": {"mood": "neutral", "score": 5},
            "😢": {"mood": "sad", "score": 3},
            "sad": {"mood": "sad", "score": 3},
            "triste": {"mood": "sad", "score": 3},
            "😤": {"mood": "angry", "score": 2},
            "angry": {"mood": "angry", "score": 2},
            "irritado": {"mood": "angry", "score": 2},
            "😴": {"mood": "tired", "score": 4},
            "tired": {"mood": "tired", "score": 4},
            "cansado": {"mood": "tired", "score": 4},
            "🤩": {"mood": "excited", "score": 9},
            "excited": {"mood": "excited", "score": 9},
            "empolgado": {"mood": "excited", "score": 9},
        }
        
        value = mood_map.get(mood.lower().strip(), {"mood": mood, "score": 5})
        
        return await self.create_checkin(
            user_id=user_id,
            checkin_type="mood",
            value=value,
            notes=notes
        )
    
    async def checkin_sleep(
        self,
        user_id: str,
        hours: float,
        quality: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check-in de sono.
        
        Args:
            hours: Horas dormidas
            quality: Qualidade 1-10 (opcional)
        """
        value = {
            "hours": hours,
            "quality": quality,
            "score": min(10, hours + (quality or 5) / 2)  # Score combinado
        }
        
        return await self.create_checkin(
            user_id=user_id,
            checkin_type="sleep",
            value=value,
            notes=notes
        )
    
    async def checkin_workout(
        self,
        user_id: str,
        workout_type: str,
        duration_minutes: int,
        intensity: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check-in de treino.
        
        Args:
            workout_type: Tipo (corrida, musculação, yoga, etc)
            duration_minutes: Duração em minutos
            intensity: low, medium, high
        """
        intensity_score = {"low": 3, "medium": 6, "high": 9}.get(intensity or "medium", 6)
        
        value = {
            "type": workout_type,
            "duration": duration_minutes,
            "intensity": intensity,
            "score": min(10, (duration_minutes / 30) * (intensity_score / 6) * 5)
        }
        
        return await self.create_checkin(
            user_id=user_id,
            checkin_type="workout",
            value=value,
            notes=notes,
            metadata={"workout_type": workout_type}
        )
    
    async def checkin_focus(
        self,
        user_id: str,
        level: int,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check-in de foco/concentração (1-10).
        
        Args:
            user_id: ID do usuário
            level: Nível de foco (1-10)
            notes: Notas opcionais
        """
        if not 1 <= level <= 10:
            raise ValueError("Nível de foco deve ser entre 1 e 10")
        
        return await self.create_checkin(
            user_id=user_id,
            checkin_type="focus",
            value=level,
            notes=notes
        )
    
    async def checkin_nutrition(
        self,
        user_id: str,
        meal_type: str,  # breakfast, lunch, dinner, snack
        quality: int,    # 1-10
        hydration: Optional[int] = None,  # copos de água
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check-in de nutrição.
        
        Args:
            user_id: ID do usuário
            meal_type: Tipo de refeição (breakfast, lunch, dinner, snack)
            quality: Qualidade da refeição (1-10)
            hydration: Copos de água consumidos (opcional)
            notes: Notas opcionais
        """
        if not 1 <= quality <= 10:
            raise ValueError("Qualidade deve ser entre 1 e 10")
        
        value = {
            "meal": meal_type,
            "quality": quality,
            "hydration": hydration,
            "score": quality
        }
        
        return await self.create_checkin(
            user_id=user_id,
            checkin_type="nutrition",
            value=value,
            notes=notes
        )
    
    async def quick_checkin(
        self,
        user_id: str,
        energy: Optional[int] = None,
        mood: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, List]:
        """
        Check-in rápido (energia + humor).
        """
        results = []
        
        if energy is not None:
            r = await self.checkin_energy(user_id, energy, notes)
            results.append({"type": "energy", "value": energy, "id": r.get("id")})
        
        if mood is not None:
            r = await self.checkin_mood(user_id, mood, notes)
            results.append({"type": "mood", "value": mood, "id": r.get("id")})
        
        return {"checkins": results}
    
    # ==========================================
    # HELPERS
    # ==========================================
    
    def _normalize_value(self, checkin_type: str, value: Any) -> Any:
        """Normaliza valor baseado no tipo."""
        if checkin_type in ["energy"] and isinstance(value, (int, float)):
            return max(1, min(10, int(value)))
        return value
    
    async def get_daily_summary(self, user_id: str, target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Gera resumo do dia com todos os check-ins.
        """
        target = target_date or date.today()
        
        checkins = await self.get_checkins(
            user_id,
            start_date=target,
            end_date=target
        )
        
        summary = {
            "date": target.isoformat(),
            "total_checkins": len(checkins),
            "energy": None,
            "mood": None,
            "sleep": None,
            "workout": None,
            "checkins": checkins
        }
        
        for c in checkins:
            ctype = c.get("checkin_type")
            if ctype in summary and summary[ctype] is None:
                summary[ctype] = c.get("value")
        
        return summary
    
    # ==========================================
    # PERFORMANCE POINTS - CHECK-IN DIÁRIO
    # ==========================================
    
    def should_send_daily_checkin(self, user_id: str) -> bool:
        """Verifica se deve enviar check-in automático hoje."""
        try:
            result = self.supabase.table('checkins')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('checkin_type', 'daily_energy')\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if not result.data:
                return True  # Nunca fez check-in
            
            last_checkin = result.data[0]
            last_date = datetime.fromisoformat(last_checkin['created_at'].replace('Z', '+00:00'))
            
            # Enviar se último check-in foi ontem ou antes
            today = datetime.utcnow().date()
            last_date = last_date.date()
            
            return last_date < today
            
        except Exception as e:
            logger.error("should_send_daily_checkin_failed", error=str(e), exc_info=True)
            return False
    
    def get_daily_checkin_message(self) -> str:
        """Retorna mensagem de check-in diário."""
        return """
🌅 CHECK-IN DIÁRIO

📊 Como está sua energia hoje?

Digite um número de 0 a 100:

0 = Esgotado
50 = Neutro
100 = Máxima energia

(Opcional: depois você pode adicionar humor, corpo, foco)
"""
    
    def process_daily_energy(self, user_id: str, energy: int) -> Dict[str, Any]:
        """Processa resposta de energia do check-in diário."""
        try:
            # Validar
            if energy < 0 or energy > 100:
                return {
                    'success': False,
                    'message': '❌ Energia deve ser entre 0 e 100'
                }
            
            # Salvar check-in
            checkin_data = {
                'user_id': user_id,
                'checkin_type': 'daily_energy',
                'value': energy,
                'checkin_date': datetime.utcnow().date().isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('checkins').insert(checkin_data).execute()
            
            # Atualizar atributo de energia no perfil
            from app.services.gamification_service import gamification
            
            # Calcular impacto (energia check-in influencia atributo)
            energy_delta = self._calculate_energy_delta(energy)
            
            if energy_delta > 0:
                gamification.increase_attribute(user_id, 'energy', energy_delta)
            elif energy_delta < 0:
                gamification.decrease_attribute(user_id, 'energy', abs(energy_delta))
            
            # Dar XP por fazer check-in
            gamification.add_xp(user_id, 10, 'Check-in diário')
            
            # Mensagem de feedback
            feedback = self._get_energy_feedback(energy)
            
            response_message = f"""
✅ Check-in registrado!
+10 XP

⚡ Energia: {energy}/100
{feedback}

💡 Dica: Suas quests de hoje serão adaptadas ao seu nível de energia.

Use /quests para ver sua missão do dia
"""
            
            logger.info("daily_checkin_completed", user_id=user_id, energy=energy)
            
            return {
                'success': True,
                'message': response_message,
                'energy': energy
            }
            
        except Exception as e:
            logger.error("process_daily_energy_failed", error=str(e), exc_info=True)
            return {
                'success': False,
                'message': '❌ Erro ao processar check-in. Tente novamente.'
            }
    
    def _calculate_energy_delta(self, energy: int) -> int:
        """Calcula mudança no atributo energia baseado no check-in."""
        # Energia alta (80-100) → +5%
        if energy >= 80:
            return 5
        # Energia boa (60-79) → +2%
        elif energy >= 60:
            return 2
        # Energia média (40-59) → neutro
        elif energy >= 40:
            return 0
        # Energia baixa (20-39) → -2%
        elif energy >= 20:
            return -2
        # Energia crítica (0-19) → -5%
        else:
            return -5
    
    def _get_energy_feedback(self, energy: int) -> str:
        """Retorna feedback baseado no nível de energia."""
        if energy >= 80:
            return "🔥 Energia alta! Momento para ações de impacto."
        elif energy >= 60:
            return "⚡ Energia boa. Aproveite para avançar."
        elif energy >= 40:
            return "🧘 Energia média. Foque no essencial."
        elif energy >= 20:
            return "🔋 Energia baixa. Priorize recuperação."
        else:
            return "❤️‍🩹 Energia crítica. Descanso é prioridade."


# Instância global
checkin_service = CheckinService()
