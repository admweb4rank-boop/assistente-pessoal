"""
Mode Service - Sistema de Modos/Identidades do Assistente
Gerencia ativação, configuração e prompts de diferentes modos operacionais
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class ModeType(Enum):
    """Tipos de modo disponíveis"""
    DEFAULT = "default"
    EXECUTION = "execution"
    CONTENT = "content"
    HEALTH = "health"
    LEARNING = "learning"
    PRESENCE = "presence"


# Configurações de modos embutidas (fallback caso DB não tenha)
DEFAULT_MODES = {
    "default": {
        "display_name": "Assistente Geral",
        "icon": "🤖",
        "description": "Modo padrão equilibrado para uso geral",
        "system_prompt": """Você é o assistente pessoal do Igor, operando no modo geral.
Você pode ajudar com qualquer área: tarefas, projetos, saúde, conteúdo, finanças, aprendizado.
Mantenha equilíbrio entre todas as áreas.
Sugira mudar para um modo específico quando o contexto pedir.""",
        "greeting": "🤖 Olá! Como posso ajudar?",
        "priority_tools": ["tasks", "calendar", "inbox", "assistant"],
        "tone": "balanced"
    },
    "execution": {
        "display_name": "Execução & Negócios",
        "icon": "⚡",
        "description": "Foco em produtividade, projetos, clientes e decisões",
        "system_prompt": """Você está no MODO EXECUÇÃO. Seu foco agora é:
- Ajudar a completar tarefas e projetos
- Priorizar ações de alto impacto
- Fazer follow-ups com clientes
- Tomar decisões rápidas
- Manter foco e evitar distrações

Tom: Direto, objetivo, orientado a resultados.
Perguntas típicas: "Qual a prioridade agora?", "O que está travando?", "Próximo passo?"
Evite: Conversas longas, reflexões filosóficas, procrastinação.""",
        "greeting": "⚡ *Modo Execução ativado!*\nO que vamos resolver agora?",
        "priority_tools": ["tasks", "projects", "calendar", "leads"],
        "tone": "direct"
    },
    "content": {
        "display_name": "Conteúdo & Marca",
        "icon": "✍️",
        "description": "Foco em ideias, posts, calendário editorial e marca pessoal",
        "system_prompt": """Você está no MODO CONTEÚDO. Seu foco agora é:
- Captar e desenvolver ideias de conteúdo
- Transformar ideias em posts para diferentes plataformas
- Manter consistência no calendário editorial
- Reaproveitar conteúdo em múltiplos formatos
- Construir autoridade e marca pessoal

Tom: Criativo, inspirador, estratégico.
Perguntas típicas: "O que te inspirou hoje?", "Qual mensagem quer passar?", "Para qual plataforma?"
Foco: Qualidade > quantidade, autenticidade, valor para audiência.""",
        "greeting": "✍️ *Modo Conteúdo ativado!*\nQual ideia vamos desenvolver?",
        "priority_tools": ["content", "memory", "calendar"],
        "tone": "creative"
    },
    "health": {
        "display_name": "Corpo & Energia",
        "icon": "💪",
        "description": "Foco em saúde, hábitos, sono, treino e alimentação",
        "system_prompt": """Você está no MODO CORPO & ENERGIA. Seu foco agora é:
- Monitorar e melhorar hábitos de saúde
- Acompanhar sono, treino e alimentação
- Identificar padrões de energia
- Sugerir ajustes comportamentais
- Manter consistência sem radicalismo

Tom: Encorajador, prático, sem julgamento.
Perguntas típicas: "Como dormiu?", "Treinou hoje?", "Como está sua energia?"
Limites: Não diagnosticar, não prescrever, apenas orientar hábitos.""",
        "greeting": "💪 *Modo Corpo & Energia ativado!*\nComo você está se sentindo?",
        "priority_tools": ["health", "checkins", "insights"],
        "tone": "supportive"
    },
    "learning": {
        "display_name": "Aprendizado & Evolução",
        "icon": "📚",
        "description": "Foco em estudos, revisão espaçada e desenvolvimento",
        "system_prompt": """Você está no MODO APRENDIZADO. Seu foco agora é:
- Capturar conhecimentos e insights
- Facilitar revisão espaçada (SM-2)
- Organizar trilhas de estudo
- Conectar aprendizados com aplicação prática
- Manter curiosidade ativa

Tom: Curioso, socrático, estimulante.
Perguntas típicas: "O que aprendeu?", "Como aplicar isso?", "Quer revisar algo?"
Foco: Compreensão profunda, conexões, aplicação real.""",
        "greeting": "📚 *Modo Aprendizado ativado!*\nO que vamos aprender ou revisar?",
        "priority_tools": ["learning", "memory", "content"],
        "tone": "curious"
    },
    "presence": {
        "display_name": "Presença & Atratividade",
        "icon": "✨",
        "description": "Foco em estilo, comunicação, postura e vida social",
        "system_prompt": """Você está no MODO PRESENÇA. Seu foco agora é:
- Melhorar aparência e estilo pessoal
- Desenvolver comunicação e presença
- Planejar exposição social estratégica
- Construir confiança e autenticidade
- Analisar o que funciona em interações

Tom: Elegante, confiante, construtivo.
Perguntas típicas: "Qual o contexto?", "Como quer ser percebido?", "O que funcionou?"
Limites: Sem manipulação, foco em presença genuína e confiança.""",
        "greeting": "✨ *Modo Presença ativado!*\nQual situação vamos preparar?",
        "priority_tools": ["calendar", "memory", "checkins"],
        "tone": "elegant"
    }
}


class ModeService:
    """Service para gerenciar modos/identidades do assistente"""
    
    def __init__(self):
        self.supabase = None
        self._init_supabase()
    
    def _init_supabase(self):
        """Inicializa cliente Supabase"""
        try:
            from supabase import create_client
            self.supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        except Exception as e:
            logger.error("Failed to init Supabase for modes", error=str(e))
    
    # ==========================================
    # MODO ATIVO
    # ==========================================
    
    def get_active_mode(self, user_id: str) -> Dict[str, Any]:
        """Obtém o modo atualmente ativo do usuário"""
        try:
            if self.supabase:
                result = self.supabase.table("user_modes")\
                    .select("*, mode_prompts(*)")\
                    .eq("user_id", user_id)\
                    .eq("is_active", True)\
                    .single()\
                    .execute()
                
                if result.data:
                    mode_data = result.data
                    prompts = mode_data.get("mode_prompts", {})
                    return {
                        "mode_name": mode_data["mode_name"],
                        "display_name": prompts.get("display_name", mode_data["mode_name"]),
                        "icon": prompts.get("icon", "🤖"),
                        "system_prompt": prompts.get("system_prompt", ""),
                        "greeting": prompts.get("greeting_template", ""),
                        "priority_tools": prompts.get("priority_tools", []),
                        "config": mode_data.get("config", {}),
                        "is_active": True
                    }
        except Exception as e:
            logger.warning("Error getting active mode from DB", error=str(e))
        
        # Fallback: modo default
        return self._get_mode_config("default")
    
    def activate_mode(
        self,
        user_id: str,
        mode_name: str,
        trigger_source: str = "manual"
    ) -> Dict[str, Any]:
        """Ativa um modo para o usuário"""
        try:
            # Valida se modo existe
            mode_config = self._get_mode_config(mode_name)
            if not mode_config:
                return {"success": False, "error": f"Modo '{mode_name}' não encontrado"}
            
            if self.supabase:
                # Desativa modo atual
                self.supabase.table("user_modes")\
                    .update({"is_active": False, "updated_at": datetime.now().isoformat()})\
                    .eq("user_id", user_id)\
                    .eq("is_active", True)\
                    .execute()
                
                # Finaliza sessão anterior
                self.supabase.table("mode_sessions")\
                    .update({
                        "ended_at": datetime.now().isoformat(),
                    })\
                    .eq("user_id", user_id)\
                    .is_("ended_at", "null")\
                    .execute()
                
                # Ativa/cria novo modo
                existing = self.supabase.table("user_modes")\
                    .select("id")\
                    .eq("user_id", user_id)\
                    .eq("mode_name", mode_name)\
                    .execute()
                
                if existing.data:
                    # Atualiza existente
                    self.supabase.table("user_modes")\
                        .update({
                            "is_active": True,
                            "activation_count": existing.data[0].get("activation_count", 0) + 1,
                            "last_activated_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat()
                        })\
                        .eq("user_id", user_id)\
                        .eq("mode_name", mode_name)\
                        .execute()
                else:
                    # Cria novo
                    self.supabase.table("user_modes").insert({
                        "user_id": user_id,
                        "mode_name": mode_name,
                        "display_name": mode_config["display_name"],
                        "is_active": True,
                        "activation_count": 1,
                        "last_activated_at": datetime.now().isoformat()
                    }).execute()
                
                # Cria sessão
                self.supabase.table("mode_sessions").insert({
                    "user_id": user_id,
                    "mode_name": mode_name,
                    "trigger_source": trigger_source
                }).execute()
            
            logger.info("Mode activated", user_id=user_id, mode=mode_name)
            
            return {
                "success": True,
                "mode": mode_config,
                "greeting": mode_config.get("greeting", "")
            }
            
        except Exception as e:
            logger.error("Failed to activate mode", error=str(e))
            return {"success": False, "error": str(e)}
    
    def deactivate_mode(self, user_id: str) -> Dict[str, Any]:
        """Desativa o modo atual (volta ao default)"""
        return self.activate_mode(user_id, "default", "deactivate")
    
    # ==========================================
    # CONFIGURAÇÕES DE MODO
    # ==========================================
    
    def _get_mode_config(self, mode_name: str) -> Optional[Dict[str, Any]]:
        """Obtém configuração de um modo (DB ou fallback)"""
        try:
            if self.supabase:
                result = self.supabase.table("mode_prompts")\
                    .select("*")\
                    .eq("mode_name", mode_name)\
                    .single()\
                    .execute()
                
                if result.data:
                    return {
                        "mode_name": result.data["mode_name"],
                        "display_name": result.data["display_name"],
                        "icon": result.data.get("icon", "🤖"),
                        "description": result.data.get("description", ""),
                        "system_prompt": result.data["system_prompt"],
                        "greeting": result.data.get("greeting_template", ""),
                        "priority_tools": result.data.get("priority_tools", []),
                        "tracked_metrics": result.data.get("tracked_metrics", [])
                    }
        except Exception as e:
            logger.warning("Error getting mode from DB", error=str(e))
        
        # Fallback para configuração embutida
        if mode_name in DEFAULT_MODES:
            config = DEFAULT_MODES[mode_name].copy()
            config["mode_name"] = mode_name
            return config
        
        return None
    
    def get_available_modes(self) -> List[Dict[str, Any]]:
        """Lista todos os modos disponíveis"""
        try:
            if self.supabase:
                result = self.supabase.table("mode_prompts")\
                    .select("mode_name, display_name, icon, description")\
                    .eq("is_active", True)\
                    .execute()
                
                if result.data:
                    return result.data
        except Exception as e:
            logger.warning("Error getting modes from DB", error=str(e))
        
        # Fallback
        return [
            {
                "mode_name": name,
                "display_name": config["display_name"],
                "icon": config["icon"],
                "description": config["description"]
            }
            for name, config in DEFAULT_MODES.items()
        ]
    
    def get_mode_prompt(self, mode_name: str) -> str:
        """Obtém o prompt do sistema para um modo"""
        config = self._get_mode_config(mode_name)
        if config:
            return config.get("system_prompt", "")
        return ""
    
    def get_mode_greeting(self, mode_name: str) -> str:
        """Obtém a saudação de um modo"""
        config = self._get_mode_config(mode_name)
        if config:
            return config.get("greeting", "")
        return ""
    
    # ==========================================
    # PROMPT LAYERING
    # ==========================================
    
    def build_full_prompt(
        self,
        user_id: str,
        core_prompt: str,
        include_context: bool = True
    ) -> str:
        """
        Constrói o prompt completo com layers:
        1. Core prompt (base do assistente)
        2. Mode prompt (overlay do modo ativo)
        3. Contexto do usuário (memórias, preferências)
        """
        active_mode = self.get_active_mode(user_id)
        mode_prompt = active_mode.get("system_prompt", "")
        
        # Layer 1: Core
        full_prompt = core_prompt
        
        # Layer 2: Mode
        if mode_prompt:
            full_prompt += f"\n\n--- MODO ATIVO: {active_mode.get('display_name', 'Geral')} ---\n"
            full_prompt += mode_prompt
        
        # Layer 3: Contexto (pode ser expandido)
        if include_context:
            full_prompt += "\n\n--- CONTEXTO ---\n"
            full_prompt += f"Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        return full_prompt
    
    # ==========================================
    # ESTATÍSTICAS
    # ==========================================
    
    def get_mode_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Estatísticas de uso de modos"""
        try:
            if self.supabase:
                start_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # Sessões por modo
                sessions = self.supabase.table("mode_sessions")\
                    .select("mode_name, duration_minutes")\
                    .eq("user_id", user_id)\
                    .gte("started_at", start_date)\
                    .execute()
                
                sessions_data = sessions.data or []
                
                # Agrupa por modo
                mode_usage = {}
                for session in sessions_data:
                    mode = session["mode_name"]
                    duration = session.get("duration_minutes") or 0
                    if mode not in mode_usage:
                        mode_usage[mode] = {"count": 0, "total_minutes": 0}
                    mode_usage[mode]["count"] += 1
                    mode_usage[mode]["total_minutes"] += duration
                
                # Modo atual
                active = self.get_active_mode(user_id)
                
                return {
                    "period_days": days,
                    "active_mode": active.get("mode_name", "default"),
                    "mode_usage": mode_usage,
                    "total_sessions": len(sessions_data),
                    "most_used_mode": max(mode_usage.keys(), key=lambda x: mode_usage[x]["count"]) if mode_usage else "default"
                }
        except Exception as e:
            logger.error("Error getting mode stats", error=str(e))
        
        return {"active_mode": "default", "mode_usage": {}}
    
    # ==========================================
    # CUSTOM MODES (Futuro)
    # ==========================================
    
    def create_custom_mode(
        self,
        user_id: str,
        mode_name: str,
        display_name: str,
        description: str,
        system_prompt: str,
        icon: str = "🎯",
        priority_tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Cria um modo personalizado (para futuro)"""
        try:
            if self.supabase:
                # Cria no mode_prompts (se não existir)
                self.supabase.table("mode_prompts").insert({
                    "mode_name": f"custom_{mode_name}",
                    "display_name": display_name,
                    "description": description,
                    "system_prompt": system_prompt,
                    "icon": icon,
                    "priority_tools": priority_tools or [],
                    "is_system": False
                }).execute()
                
                return {"success": True, "mode_name": f"custom_{mode_name}"}
        except Exception as e:
            logger.error("Error creating custom mode", error=str(e))
            return {"success": False, "error": str(e)}


# Singleton
mode_service = ModeService()
