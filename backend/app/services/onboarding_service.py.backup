"""
Onboarding Service - Sistema de Quiz e Personalização para Novos Usuários
"""

import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import Client

logger = structlog.get_logger(__name__)


class OnboardingService:
    """Serviço para gerenciar onboarding de novos usuários."""
    
    # Perguntas do quiz (hardcoded como fallback se DB falhar)
    QUIZ_QUESTIONS = [
        {
            "id": 1,
            "question": "Qual seu principal objetivo ao usar este assistente?",
            "type": "single",
            "options": [
                {"value": "productivity", "label": "📊 Aumentar produtividade"},
                {"value": "organization", "label": "📁 Organizar vida pessoal"},
                {"value": "health", "label": "💪 Melhorar saúde e bem-estar"},
                {"value": "learning", "label": "📚 Aprender e crescer"},
                {"value": "business", "label": "💼 Gerenciar negócios"},
                {"value": "multiple", "label": "🎯 Múltiplos objetivos"}
            ]
        },
        {
            "id": 2,
            "question": "Como você prefere que eu me comunique?",
            "type": "single",
            "options": [
                {"value": "direct", "label": "💬 Direto e objetivo"},
                {"value": "friendly", "label": "😊 Amigável e casual"},
                {"value": "professional", "label": "👔 Formal e profissional"},
                {"value": "motivational", "label": "🚀 Motivador e energético"}
            ]
        },
        {
            "id": 3,
            "question": "Quanto de autonomia você quer me dar?",
            "type": "single",
            "options": [
                {"value": "suggest", "label": "💡 Apenas sugerir (eu decido tudo)"},
                {"value": "confirm", "label": "✓ Sugerir e pedir confirmação"},
                {"value": "auto", "label": "🤖 Executar automaticamente"}
            ]
        },
        {
            "id": 4,
            "question": "Quais áreas você quer que eu te ajude? (escolha várias)",
            "type": "multiple",
            "options": [
                {"value": "tasks", "label": "✅ Tarefas e projetos"},
                {"value": "calendar", "label": "📅 Calendário e agenda"},
                {"value": "finance", "label": "💰 Finanças pessoais"},
                {"value": "health", "label": "🏃 Saúde e exercícios"},
                {"value": "content", "label": "📱 Criação de conteúdo"},
                {"value": "learning", "label": "📖 Aprendizado"},
                {"value": "habits", "label": "🎯 Hábitos e rotinas"}
            ]
        },
        {
            "id": 5,
            "question": "Em que horário você é mais ativo?",
            "type": "single",
            "options": [
                {"value": "morning", "label": "🌅 Manhã (6h-12h)"},
                {"value": "afternoon", "label": "☀️ Tarde (12h-18h)"},
                {"value": "evening", "label": "🌆 Noite (18h-23h)"},
                {"value": "night", "label": "🌙 Madrugada (23h-6h)"},
                {"value": "flexible", "label": "🔄 Varia muito"}
            ]
        },
        {
            "id": 6,
            "question": "Cole sua chave API do Google Gemini:\n\n_Obtenha em: https://makersuite.google.com/app/apikey_\n_Deixe em branco para usar a chave padrão (limite compartilhado)_",
            "type": "text",
            "optional": True,
            "placeholder": "AIzaSy..."
        },
        {
            "id": 7,
            "question": "Como prefere ser chamado?",
            "type": "text",
            "placeholder": "Digite seu nome ou apelido"
        }
    ]
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    def check_onboarding_status(self, user_id: str) -> Dict[str, Any]:
        """
        Verifica status do onboarding do usuário.
        
        Returns:
            {
                "completed": bool,
                "current_step": int,
                "total_steps": int
            }
        """
        try:
            result = self.supabase.table("profiles")\
                .select("onboarding_completed, onboarding_step, quiz_answers")\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            if result.data:
                return {
                    "completed": result.data.get("onboarding_completed", False),
                    "current_step": result.data.get("onboarding_step", 0),
                    "total_steps": len(self.QUIZ_QUESTIONS),
                    "quiz_answers": result.data.get("quiz_answers", {})
                }
            
            return {
                "completed": False,
                "current_step": 0,
                "total_steps": len(self.QUIZ_QUESTIONS)
            }
            
        except Exception as e:
            logger.error("onboarding_status_check_failed", error=str(e))
            return {
                "completed": False,
                "current_step": 0,
                "total_steps": len(self.QUIZ_QUESTIONS)
            }
    
    def get_next_question(self, user_id: str) -> Optional[Dict]:
        """Retorna próxima pergunta do quiz."""
        status = self.check_onboarding_status(user_id)
        
        if status["completed"]:
            return None
        
        current_step = status["current_step"]
        
        if current_step >= len(self.QUIZ_QUESTIONS):
            return None
        
        return self.QUIZ_QUESTIONS[current_step]
    
    def save_answer(
        self,
        user_id: str,
        question_id: int,
        answer: Any
    ) -> bool:
        """Salva resposta do usuário."""
        try:
            # Buscar respostas existentes
            profile = self.supabase.table("profiles")\
                .select("quiz_answers, onboarding_step")\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            quiz_answers = profile.data.get("quiz_answers", {}) if profile.data else {}
            current_step = profile.data.get("onboarding_step", 0) if profile.data else 0
            
            # Adicionar nova resposta
            quiz_answers[f"question_{question_id}"] = answer
            
            # Atualizar profile
            self.supabase.table("profiles")\
                .update({
                    "quiz_answers": quiz_answers,
                    "onboarding_step": current_step + 1
                })\
                .eq("user_id", user_id)\
                .execute()
            
            logger.info(
                "quiz_answer_saved",
                user_id=user_id,
                question_id=question_id,
                step=current_step + 1
            )
            
            return True
            
        except Exception as e:
            logger.error("save_answer_failed", error=str(e))
            return False
    
    def complete_onboarding(self, user_id: str) -> Dict[str, Any]:
        """Finaliza onboarding e cria perfil personalizado."""
        try:
            # Buscar todas as respostas
            profile = self.supabase.table("profiles")\
                .select("quiz_answers, full_name")\
                .eq("user_id", user_id)\
                .single()\
                .execute()
            
            if not profile.data:
                raise Exception("Profile not found")
            
            quiz_answers = profile.data.get("quiz_answers", {})
            
            # Processar respostas e criar perfil de personalidade
            personality_profile = self._build_personality_profile(quiz_answers)
            
            # Extrair chave API do Gemini (se fornecida)
            gemini_api_key = quiz_answers.get("question_6", {}).get("value")
            
            # Extrair nome
            user_name = quiz_answers.get("question_7", {}).get("value")
            
            # Extrair nível de autonomia
            autonomy = quiz_answers.get("question_3", {}).get("value", "confirm")
            
            # Atualizar profile completo
            update_data = {
                "personality_profile": personality_profile,
                "onboarding_completed": True,
                "onboarded_at": datetime.utcnow().isoformat(),
                "autonomy_level": autonomy
            }
            
            if gemini_api_key and gemini_api_key.strip():
                update_data["gemini_api_key"] = gemini_api_key.strip()
            
            self.supabase.table("profiles")\
                .update(update_data)\
                .eq("user_id", user_id)\
                .execute()
            
            # Atualizar nome do usuário
            if user_name:
                self.supabase.table("users")\
                    .update({"full_name": user_name})\
                    .eq("id", user_id)\
                    .execute()
            
            logger.info(
                "onboarding_completed",
                user_id=user_id,
                has_custom_api_key=bool(gemini_api_key),
                autonomy=autonomy
            )
            
            return {
                "success": True,
                "personality_profile": personality_profile,
                "has_custom_api_key": bool(gemini_api_key)
            }
            
        except Exception as e:
            logger.error("complete_onboarding_failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_personality_profile(self, quiz_answers: Dict) -> Dict:
        """Constrói perfil de personalidade baseado nas respostas."""
        return {
            "main_goal": quiz_answers.get("question_1", {}).get("value", "multiple"),
            "communication_style": quiz_answers.get("question_2", {}).get("value", "friendly"),
            "autonomy_level": quiz_answers.get("question_3", {}).get("value", "confirm"),
            "focus_areas": quiz_answers.get("question_4", {}).get("value", []),
            "active_hours": quiz_answers.get("question_5", {}).get("value", "flexible"),
            "created_at": datetime.utcnow().isoformat()
        }
    
    def format_question_message(self, question: Dict) -> str:
        """Formata pergunta para envio no Telegram."""
        msg = f"*Pergunta {question['id']}/{len(self.QUIZ_QUESTIONS)}*\n\n"
        msg += f"{question['question']}\n\n"
        
        if question["type"] in ["single", "multiple"]:
            for i, option in enumerate(question["options"], 1):
                msg += f"{i}. {option['label']}\n"
            
            if question["type"] == "multiple":
                msg += f"\n_Envie os números separados por vírgula (ex: 1,3,5)_"
            else:
                msg += f"\n_Envie o número da sua escolha_"
        
        elif question["type"] == "text":
            placeholder = question.get("placeholder", "")
            if placeholder:
                msg += f"_{placeholder}_"
        
        if question.get("optional"):
            msg += f"\n\n_Opcional: Digite 'pular' para usar configuração padrão_"
        
        return msg
    
    def parse_answer(self, question: Dict, answer_text: str) -> Dict:
        """Parseia resposta do usuário."""
        if question["type"] == "text":
            # Verificar se pulou
            if answer_text.lower().strip() == "pular" and question.get("optional"):
                return {"value": None, "skipped": True}
            return {"value": answer_text.strip()}
        
        elif question["type"] == "single":
            try:
                choice = int(answer_text.strip())
                if 1 <= choice <= len(question["options"]):
                    option = question["options"][choice - 1]
                    return {
                        "value": option["value"],
                        "label": option["label"]
                    }
            except ValueError:
                pass
            return {"error": "Opção inválida"}
        
        elif question["type"] == "multiple":
            try:
                choices = [int(c.strip()) for c in answer_text.split(",")]
                selected = []
                for choice in choices:
                    if 1 <= choice <= len(question["options"]):
                        option = question["options"][choice - 1]
                        selected.append(option["value"])
                
                if selected:
                    return {"value": selected}
            except ValueError:
                pass
            return {"error": "Opções inválidas"}
        
        return {"error": "Tipo de pergunta não suportado"}
