"""
TB Personal OS - Profile Editor Service
Sistema de perfil vivo: editável, revisável, evolutivo.
PRINCÍPIO: Nada no perfil é definitivo. O usuário evolui → o personagem evolui.
"""

import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from supabase import create_client, Client

logger = structlog.get_logger(__name__)


class ProfileEditorService:
    """
    Gerencia edição e evolução do perfil do usuário.
    Perfil vivo: tudo tem timestamp, nada é fixo.
    """
    
    def __init__(self):
        self._supabase: Optional[Client] = None
    
    @property
    def supabase(self) -> Client:
        """Lazy load do Supabase."""
        if self._supabase is None:
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return self._supabase
    
    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Retorna perfil completo do usuário."""
        try:
            result = self.supabase.table('profiles')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            return {}
        except Exception as e:
            logger.error("get_profile_failed", error=str(e))
            return {}
    
    def should_review_profile(self, user_id: str) -> bool:
        """
        Verifica se é hora de revisar o perfil.
        Triggers: 30-45 dias OU mudanças comportamentais.
        """
        try:
            profile = self.get_profile(user_id)
            
            if not profile:
                return False
            
            # Verificar última revisão
            last_review = profile.get('last_profile_review')
            if last_review:
                last_review_date = datetime.fromisoformat(last_review)
                days_since = (datetime.utcnow() - last_review_date).days
                
                if days_since >= 30:
                    return True
            else:
                # Nunca revisou - verificar tempo desde criação
                created = profile.get('created_at')
                if created:
                    created_date = datetime.fromisoformat(created)
                    days_since = (datetime.utcnow() - created_date).days
                    
                    if days_since >= 45:
                        return True
            
            # TODO: Verificar mudanças comportamentais
            # - Queda de energia
            # - Procrastinação frequente
            # - Mudança de foco nas conversas
            
            return False
            
        except Exception as e:
            logger.error("should_review_failed", error=str(e))
            return False
    
    def update_field(self, user_id: str, field: str, value: Any) -> bool:
        """
        Atualiza campo específico do perfil.
        Mantém histórico e timestamp.
        """
        try:
            # Buscar valor atual para histórico
            current = self.get_profile(user_id)
            old_value = current.get(field)
            
            # Atualizar campo
            update_data = {
                'user_id': user_id,
                field: value,
                f'{field}_updated_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Salvar no histórico se campo importante
            if field in ['life_areas', 'skills_focus', 'main_goal', 'blockers']:
                history_entry = {
                    'user_id': user_id,
                    'field': field,
                    'old_value': old_value,
                    'new_value': value,
                    'changed_at': datetime.utcnow().isoformat()
                }
                
                # Adicionar ao histórico
                try:
                    self.supabase.table('profile_history').insert(history_entry).execute()
                except:
                    pass  # Histórico é nice-to-have
            
            # Atualizar perfil
            self.supabase.table('profiles').upsert(update_data).execute()
            
            logger.info("profile_updated", 
                       user_id=user_id, 
                       field=field, 
                       changed=old_value != value)
            
            return True
            
        except Exception as e:
            logger.error("update_field_failed", error=str(e))
            return False
    
    def edit_life_areas(self, user_id: str, areas: List[str]) -> Dict[str, Any]:
        """Edita áreas prioritárias (até 5)."""
        if len(areas) > 5:
            areas = areas[:5]
        
        success = self.update_field(user_id, 'life_areas', areas)
        
        return {
            'success': success,
            'areas': areas,
            'count': len(areas)
        }
    
    def edit_skills(self, user_id: str, skills: List[str]) -> Dict[str, Any]:
        """Edita habilidades em desenvolvimento (até 3)."""
        if len(skills) > 3:
            skills = skills[:3]
        
        success = self.update_field(user_id, 'skills_focus', skills)
        
        return {
            'success': success,
            'skills': skills,
            'count': len(skills)
        }
    
    def edit_goal(self, user_id: str, goal: str) -> Dict[str, Any]:
        """Edita meta principal."""
        success = self.update_field(user_id, 'main_goal', goal)
        
        return {
            'success': success,
            'goal': goal
        }
    
    def edit_body(self, user_id: str, exercise: str, energy: str) -> Dict[str, Any]:
        """Edita informações de corpo/energia."""
        success1 = self.update_field(user_id, 'exercise_frequency', exercise)
        success2 = self.update_field(user_id, 'energy_level', energy)
        
        return {
            'success': success1 and success2,
            'exercise': exercise,
            'energy': energy
        }
    
    def edit_income(self, user_id: str, sources: List[str], goal: str) -> Dict[str, Any]:
        """Edita fontes de renda e objetivo financeiro."""
        success1 = self.update_field(user_id, 'income_sources', sources)
        success2 = self.update_field(user_id, 'financial_goal', goal)
        
        return {
            'success': success1 and success2,
            'sources': sources,
            'goal': goal
        }
    
    def mark_reviewed(self, user_id: str):
        """Marca perfil como revisado agora."""
        try:
            self.supabase.table('profiles').upsert({
                'user_id': user_id,
                'last_profile_review': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            logger.error("mark_reviewed_failed", error=str(e))
    
    def get_edit_options(self, field: str) -> List[tuple]:
        """
        Retorna opções para edição de campo específico.
        Sempre inclui opção custom.
        """
        options_map = {
            'life_areas': [
                ('business', '💼 Negócios / Carreira'),
                ('money', '💰 Dinheiro / Renda'),
                ('body', '🏋️ Corpo / Saúde / Energia'),
                ('mind', '🧠 Mente / Foco / Disciplina'),
                ('relationships', '❤️ Relacionamentos'),
                ('spirituality', '🧘 Espiritualidade / Propósito'),
                ('creativity', '🎨 Criatividade / Expressão'),
                ('family', '👨‍👩‍👧 Família'),
                ('freedom', '🗺️ Liberdade / Estilo de vida'),
                ('custom', '✍️ Escrever minha resposta')
            ],
            'skills': [
                ('presence', '🎤 Presença e comunicação'),
                ('focus', '🧠 Foco e disciplina'),
                ('projects', '📊 Gestão de projetos'),
                ('creativity', '💡 Criatividade'),
                ('leadership', '🤝 Liderança'),
                ('finance', '💸 Gestão financeira'),
                ('tech', '🤖 Automação / tecnologia'),
                ('emotional', '🧘 Autodomínio emocional'),
                ('custom', '✍️ Escrever minha resposta')
            ],
            'exercise': [
                ('high', '🏋️ 4–6x por semana'),
                ('moderate', '🚶 2–3x por semana'),
                ('rare', '😬 Raramente'),
                ('none', '❌ Não pratico')
            ],
            'energy': [
                ('high', '🔋 Alto'),
                ('medium', '⚖️ Médio'),
                ('low', '🪫 Baixo')
            ],
            'income_sources': [
                ('fixed', '💼 Trabalho fixo'),
                ('business', '📈 Negócio próprio'),
                ('digital', '💻 Digital / online'),
                ('consulting', '🧠 Serviços / consultorias'),
                ('freelance', '🧾 Freelance'),
                ('single', '❌ Apenas uma fonte'),
                ('multiple', '🔁 Múltiplas fontes'),
                ('custom', '✍️ Escrever minha resposta')
            ],
            'financial_goal': [
                ('increase', '💸 Aumentar renda'),
                ('diversify', '🔁 Criar novas fontes'),
                ('organize', '🧠 Organizar finanças'),
                ('freedom', '🕊️ Mais liberdade de tempo')
            ]
        }
        
        return options_map.get(field, [])
    
    def start_profile_review(self, user_id: str) -> Dict[str, Any]:
        """
        Inicia revisão de perfil.
        Periodicidade sugerida: a cada 15 ou 30 dias.
        """
        try:
            profile = self.get_profile(user_id)
            
            if not profile:
                return {
                    'success': False,
                    'message': '❌ Perfil não encontrado. Complete o onboarding primeiro.'
                }
            
            # Campos editáveis na revisão
            editable_fields = {
                'life_areas': '🎯 Áreas da vida',
                'skills': '🧠 Habilidades a desenvolver',
                'main_goal': '🎯 Meta principal do ano',
                'blockers': '🚧 Bloqueios atuais',
                'exercise': '🏋️ Atividade física',
                'income_sources': '💰 Fontes de renda'
            }
            
            message = """
🔄 REVISÃO DE PERFIL

O que mudou desde a última vez?

Escolha o que você quer atualizar:

1️⃣ Áreas da vida
2️⃣ Habilidades a desenvolver
3️⃣ Meta principal do ano
4️⃣ Bloqueios atuais
5️⃣ Atividade física
6️⃣ Fontes de renda
0️⃣ Nada mudou / Cancelar

Digite o número ou /cancelar
"""
            
            logger.info("profile_review_started", user_id=user_id)
            
            return {
                'success': True,
                'message': message,
                'editable_fields': editable_fields,
                'in_review': True
            }
            
        except Exception as e:
            logger.error("start_profile_review_failed", error=str(e), exc_info=True)
            return {
                'success': False,
                'message': '❌ Erro ao iniciar revisão. Tente novamente.'
            }
    
    def complete_profile_review(self, user_id: str) -> Dict[str, Any]:
        """Finaliza revisão e atualiza data da última revisão."""
        try:
            # Atualizar data da última revisão
            self.supabase.table('profiles').update({
                'last_profile_review': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()
            
            # Dar XP pela revisão
            from app.services.gamification_service import gamification
            gamification.add_xp(user_id, 50, 'Revisão de perfil')
            
            message = """
✅ Revisão concluída!
+50 XP

Seu perfil está atualizado e o assistente já se adaptou às mudanças.

💡 Próxima revisão sugerida: 15-30 dias
"""
            
            logger.info("profile_review_completed", user_id=user_id)
            
            return {
                'success': True,
                'message': message
            }
            
        except Exception as e:
            logger.error("complete_profile_review_failed", error=str(e), exc_info=True)
            return {
                'success': False,
                'message': '❌ Erro ao finalizar revisão.'
            }


# Instância global
profile_editor = ProfileEditorService()
