"""
TB Personal OS - Gamification Service
Sistema de RPG/Gamificação para o assistente
"""

import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.core.config import settings
from supabase import create_client, Client

logger = structlog.get_logger(__name__)


class GamificationService:
    """
    Sistema de gamificação tipo RPG para o assistente.
    Níveis, XP, conquistas, atributos, etc.
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
    
    # ==========================================
    # SISTEMA DE NÍVEIS E XP
    # ==========================================
    
    def calculate_level(self, xp: int) -> int:
        """Calcula nível baseado no XP total."""
        # Fórmula: Level = sqrt(XP / 100)
        import math
        return int(math.sqrt(xp / 100)) + 1
    
    def xp_for_next_level(self, current_level: int) -> int:
        """XP necessário para próximo nível."""
        return (current_level ** 2) * 100
    
    def add_xp(self, user_id: str, amount: int, reason: str) -> Dict[str, Any]:
        """
        Adiciona XP ao usuário e retorna informações de level up.
        """
        try:
            # Buscar perfil atual
            profile = self.get_profile(user_id)
            
            old_xp = profile.get('xp', 0)
            old_level = profile.get('level', 1)
            
            new_xp = old_xp + amount
            new_level = self.calculate_level(new_xp)
            
            # Atualizar no banco
            self.supabase.table('profiles').upsert({
                'user_id': user_id,
                'xp': new_xp,
                'level': new_level,
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            
            # Verificar level up
            level_up = new_level > old_level
            
            return {
                'xp_gained': amount,
                'total_xp': new_xp,
                'old_level': old_level,
                'new_level': new_level,
                'level_up': level_up,
                'reason': reason,
                'xp_to_next': self.xp_for_next_level(new_level) - new_xp
            }
            
        except Exception as e:
            logger.error("add_xp_failed", error=str(e), user_id=user_id)
            return {}
    
    # ==========================================
    # ATRIBUTOS RPG (4 PRINCIPAIS - SEM FIRULA)
    # ==========================================
    
    def get_attributes(self, user_id: str) -> Dict[str, int]:
        """
        Retorna os 4 atributos base do RPG.
        
        ⚡ Energia: corpo + sono + movimento
        🎯 Foco: atenção + disciplina
        🛠️ Execução: ação consistente
        💰 Renda: jogo financeiro
        
        Tudo que o assistente faz impacta um desses.
        """
        profile = self.get_profile(user_id)
        return profile.get('attributes', {
            'energy': 50,      # ⚡ Energia
            'focus': 50,       # 🎯 Foco
            'execution': 50,   # 🛠️ Execução
            'income': 50       # 💰 Renda
        })
    
    def increase_attribute(self, user_id: str, attribute: str, amount: int = 5):
        """
        Aumenta um atributo específico.
        Usado quando usuário completa quests ou ações.
        """
        try:
            attributes = self.get_attributes(user_id)
            current = attributes.get(attribute, 50)
            new_value = min(100, current + amount)  # Máximo 100
            
            attributes[attribute] = new_value
            
            self.supabase.table('profiles').upsert({
                'user_id': user_id,
                'attributes': attributes,
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            
            logger.info("attribute_increased", 
                       user_id=user_id, 
                       attribute=attribute, 
                       old=current, 
                       new=new_value)
            
            return new_value
        except Exception as e:
            logger.error("increase_attribute_failed", error=str(e))
            return 50
    
    def decrease_attribute(self, user_id: str, attribute: str, amount: int = 3):
        """
        Diminui atributo (decay natural ou ações negativas).
        """
        try:
            attributes = self.get_attributes(user_id)
            current = attributes.get(attribute, 50)
            new_value = max(0, current - amount)  # Mínimo 0
            
            attributes[attribute] = new_value
            
            self.supabase.table('profiles').upsert({
                'user_id': user_id,
                'attributes': attributes,
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            
            return new_value
        except Exception as e:
            logger.error("decrease_attribute_failed", error=str(e))
            return 50
    
    def update_attribute(self, user_id: str, attribute: str, change: int):
        """
        Atualiza um atributo (compatibilidade com código antigo).
        Use increase_attribute() ou decrease_attribute() preferencialmente.
        """
        if change > 0:
            return self.increase_attribute(user_id, attribute, change)
        else:
            return self.decrease_attribute(user_id, attribute, abs(change))
    
    # ==========================================
    # CONQUISTAS (ACHIEVEMENTS)
    # ==========================================
    
    def unlock_achievement(self, user_id: str, achievement_id: str, title: str, 
                          description: str, xp_reward: int = 100) -> bool:
        """Desbloqueia uma conquista para o usuário."""
        try:
            # Verificar se já tem
            existing = self.supabase.table('achievements')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('achievement_id', achievement_id)\
                .execute()
            
            if existing.data:
                return False  # Já tem
            
            # Criar conquista
            self.supabase.table('achievements').insert({
                'user_id': user_id,
                'achievement_id': achievement_id,
                'title': title,
                'description': description,
                'unlocked_at': datetime.utcnow().isoformat()
            }).execute()
            
            # Adicionar XP
            self.add_xp(user_id, xp_reward, f"Conquista: {title}")
            
            logger.info("achievement_unlocked", 
                       user_id=user_id, 
                       achievement=achievement_id)
            
            return True
            
        except Exception as e:
            logger.error("unlock_achievement_failed", error=str(e))
            return False
    
    # ==========================================
    # PERFIL E STATUS
    # ==========================================
    
    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Retorna perfil completo de gamificação."""
        try:
            result = self.supabase.table('profiles')\
                .select('*')\
                .eq('user_id', user_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            
            # Criar perfil padrão
            default_profile = {
                'user_id': user_id,
                'level': 1,
                'xp': 0,
                'attributes': {
                    'energy': 50,
                    'focus': 50,
                    'productivity': 50,
                    'knowledge': 50,
                    'social': 50,
                    'health': 50
                },
                'personality_type': None,
                'work_style': None,
                'goals': [],
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.supabase.table('profiles').insert(default_profile).execute()
            return default_profile
            
        except Exception as e:
            logger.error("get_profile_failed", error=str(e))
            return {
                'user_id': user_id,
                'level': 1,
                'xp': 0,
                'attributes': {
                    'energy': 50,
                    'focus': 50,
                    'productivity': 50,
                    'knowledge': 50,
                    'social': 50,
                    'health': 50
                }
            }
    
    def format_status_message(self, user_id: str, username: str = "Igor") -> str:
        """
        Formata mensagem de status visual tipo RPG.
        """
        profile = self.get_profile(user_id)
        attributes = profile.get('attributes', {})
        
        level = profile.get('level', 1)
        xp = profile.get('xp', 0)
        xp_next = self.xp_for_next_level(level)
        xp_progress = (xp / xp_next) * 100 if xp_next > 0 else 0
        
        # Barra de progresso XP
        xp_bar = self._create_progress_bar(xp_progress, length=10)
        
        # 4 ATRIBUTOS BASE (SEM FIRULA)
        attr_config = {
            'energy': ('⚡', 'Energia'),
            'focus': ('🎯', 'Foco'),
            'execution': ('🛠️', 'Execução'),
            'income': ('💰', 'Renda')
        }
        
        # Formatar atributos
        attr_lines = []
        for attr_key, (emoji, label) in attr_config.items():
            value = attributes.get(attr_key, 50)
            bar = self._create_progress_bar(value, length=8)
            attr_lines.append(f"{emoji} {label:<10} {bar} {value}/100")
        
        # Conquistas recentes
        achievements_count = self._count_achievements(user_id)
        
        # Arquétipo (se tiver)
        archetype = profile.get('personality_type', '')
        
    def format_status_message(self, user_id: str, username: str = "Igor") -> str:
        """
        Formata painel de status tipo Performance Points.
        Usa dados REAIS do quiz, check-ins, tarefas e contexto.
        """
        profile = self.get_profile(user_id)
        
        # Buscar dados do quiz (personality_profile e quiz_answers)
        personality_profile = profile.get('personality_profile', {})
        quiz_answers = profile.get('quiz_answers', {})
        
        # GAMIFICAÇÃO BASE
        level = profile.get('level', 1)
        xp = profile.get('xp', 0)
        xp_next = self.xp_for_next_level(level)
        
        # ARQUÉTIPO REAL do quiz
        archetype = personality_profile.get('archetype', f'Nível {level}')
        archetype_emoji = personality_profile.get('archetype_emoji', '🎖️')
        
        # ÁREAS PRIORITÁRIAS do quiz
        life_areas_raw = quiz_answers.get('life_areas', '')
        if isinstance(life_areas_raw, str):
            life_areas = [a.strip() for a in life_areas_raw.split(',') if a.strip()]
        else:
            life_areas = life_areas_raw if isinstance(life_areas_raw, list) else []
        
        area_labels = {
            'body_energy': '🏋️ Corpo & Energia',
            'mind_emotions': '🧠 Mente & Emoções',
            'work_business': '💼 Trabalho / Negócios',
            'income_finances': '💰 Renda & Finanças',
            'relationships': '❤️ Relacionamentos',
            'spirituality_presence': '🧘 Espiritualidade / Presença',
            'lifestyle_leisure': '🗺️ Estilo de vida / Lazer',
            # Fallbacks antigos
            'health': '💪 Saúde',
            'work': '💼 Trabalho',
            'content': '📱 Conteúdo',
            'business': '🚀 Negócios',
            'money': '💰 Renda',
            'mind': '🧠 Mente',
            'spirituality': '🙏 Espiritualidade',
            'creativity': '🎨 Criatividade',
            'family': '👨‍👩‍👧 Família',
            'freedom': '✈️ Liberdade'
        }
        areas_text = '\n'.join([area_labels.get(a, f"• {a.replace('_', ' ').title()}") for a in life_areas[:5]])
        
        # HABILIDADES em desenvolvimento
        skills_raw = quiz_answers.get('skills', '')
        if isinstance(skills_raw, str):
            skills = [s.strip() for s in skills_raw.split(',') if s.strip()]
        else:
            skills = skills_raw if isinstance(skills_raw, list) else []
        
        skill_labels = {
            'presence': '🎤 Presença',
            'discipline': '🎯 Disciplina',
            'execution': '🛠️ Execução',
            'mental_clarity': '🧠 Clareza mental',
            'project_management': '📊 Gestão de projetos',
            'communication': '💬 Comunicação',
            'consistency': '🔁 Consistência'
        }
        skills_text = '\n'.join([skill_labels.get(s, s.replace('_', ' ').title()) for s in skills[:4]]) if skills else "Não definidas"
        
        # META PRINCIPAL do ano
        year_goal = quiz_answers.get('year_goals', 'Não definida')
        
        # BLOQUEIOS identificados
        blockers_raw = quiz_answers.get('blockers', '')
        if isinstance(blockers_raw, str):
            blockers = [b.strip() for b in blockers_raw.split(',') if b.strip()]
        else:
            blockers = blockers_raw if isinstance(blockers_raw, list) else []
        
        blocker_labels = {
            'energy': '🔋 Falta de energia',
            'focus': '🎯 Falta de foco',
            'tasks': '📋 Excesso de tarefas',
            'procrastination': '⏳ Procrastinação',
            'insecurity': '😰 Insegurança',
            'disorganization': '🌀 Desorganização',
            # Fallbacks
            'organization': '📋 Desorganização',
            'discipline': '💪 Falta de disciplina',
            'clarity': '🔍 Falta de clareza',
            'motivation': '🔥 Desmotivação'
        }
        blockers_text = '\n'.join([blocker_labels.get(b, b.replace('_', ' ').title()) for b in blockers[:3]]) if blockers else "Nenhum identificado"
        
        # CALCULAR MÉTRICAS REAIS baseado em ações
        energy = self._calculate_real_energy(user_id)
        focus = self._calculate_real_focus(user_id)
        execution = self._calculate_real_execution(user_id)
        income = self._calculate_real_income(user_id)
        sleep = self._calculate_real_sleep(user_id, quiz_answers)
        mood_data = self._calculate_real_mood(user_id)
        
        # Conquistas (reais se existirem)
        achievements = self._get_recent_achievements(user_id, limit=3)
        if achievements:
            achievements_text = '\n'.join([f"🏅 {a.get('title', 'Conquista')}" for a in achievements])
        else:
            # Se não tem conquistas, mostrar progresso
            achievements_text = f"🎯 Complete tarefas para desbloquear\n✨ XP atual: {xp}"
        
        # Última revisão
        last_review = profile.get('last_profile_review')
        if last_review:
            from datetime import datetime
            review_date = datetime.fromisoformat(last_review)
            days_ago = (datetime.utcnow() - review_date).days
            review_text = f"há {days_ago} dias"
        else:
            review_text = "nunca"
        
        # Adicionar contador de check-ins de humor
        mood_indicator = f"{mood_data['emoji']} {mood_data['score']}%"
        if mood_data['count'] > 0:
            mood_indicator += f" ({mood_data['count']} reg.)"
        
        message = f"""🧠 *STATUS | PERFORMANCE POINTS*

👤 {username}
{archetype_emoji} {archetype}
✨ Nível {level} • {xp}/{xp_next} XP

━━━━━━━━━━━━━━━━━━

📊 *MÉTRICAS DE PERFORMANCE:*

⚡ Energia: {energy}% | 🎯 Foco: {focus}%
🛠️ Execução: {execution}% | 💰 Renda: {income}%
😴 Sono: {sleep}% | {mood_indicator}

━━━━━━━━━━━━━━━━━━

🎯 *PERFIL ATUAL:*

*Meta 2026:*
{year_goal}

*💪 Habilidades em Foco:*
{skills_text}

*🎨 Áreas Prioritárias:*
{areas_text if areas_text else "Use /quiz para definir"}

*⚠️ Bloqueios Mapeados:*
{blockers_text}

━━━━━━━━━━━━━━━━━━

🏆 *CONQUISTAS:*
{achievements_text}

━━━━━━━━━━━━━━━━━━

📅 Última revisão: {review_text}
💡 Use /quest para missão do dia

_Seu perfil é baseado no quiz. Use /quiz para refazer._
"""
        
        return message.strip()
    
    def _get_recent_achievements(self, user_id: str, limit: int = 3) -> List[Dict]:
        """Busca conquistas recentes."""
        try:
            result = self.supabase.table('achievements')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('unlocked_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
        except:
            return []
    
    def _create_progress_bar(self, percentage: float, length: int = 10) -> str:
        """Cria barra de progresso visual."""
        filled = int((percentage / 100) * length)
        empty = length - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    def _get_title_by_level(self, level: int) -> str:
        """Retorna título baseado no nível."""
        if level < 5:
            return "🌱 Aprendiz"
        elif level < 10:
            return "⚔️ Aventureiro"
        elif level < 20:
            return "🛡️ Veterano"
        elif level < 30:
            return "🏆 Elite"
        elif level < 50:
            return "⭐ Mestre"
        else:
            return "👑 Lenda"
    
    def _count_achievements(self, user_id: str) -> int:
        """Conta conquistas desbloqueadas."""
        try:
            result = self.supabase.table('achievements')\
                .select('id', count='exact')\
                .eq('user_id', user_id)\
                .execute()
            return result.count or 0
        except:
            return 0
    
    # ==========================================
    # CÁLCULO DE MÉTRICAS REAIS
    # ==========================================
    
    def _calculate_real_energy(self, user_id: str) -> int:
        """
        Calcula energia real baseado em check-ins recentes.
        Busca últimos 3 check-ins de energia.
        """
        try:
            result = self.supabase.table('checkins')\
                .select('value')\
                .eq('user_id', user_id)\
                .eq('checkin_type', 'energy')\
                .order('created_at', desc=True)\
                .limit(3)\
                .execute()
            
            if result.data:
                values = [c.get('value', 50) for c in result.data]
                # Converter de 0-10 para 0-100
                avg = sum(values) / len(values)
                return int(avg * 10)
            
            return 50  # Padrão se não tem check-ins
        except:
            return 50
    
    def _calculate_real_focus(self, user_id: str) -> int:
        """
        Calcula foco baseado em tarefas completadas nos últimos 7 dias.
        """
        try:
            from datetime import datetime, timedelta
            
            # Tarefas criadas nos últimos 7 dias
            seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            result = self.supabase.table('tasks')\
                .select('status')\
                .eq('user_id', user_id)\
                .gte('created_at', seven_days_ago)\
                .execute()
            
            if not result.data:
                return 50
            
            total = len(result.data)
            completed = len([t for t in result.data if t.get('status') == 'done'])
            
            # Taxa de conclusão -> foco
            completion_rate = (completed / total * 100) if total > 0 else 50
            return int(completion_rate)
            
        except:
            return 50
    
    def _calculate_real_execution(self, user_id: str) -> int:
        """
        Calcula execução baseado em consistência (tarefas nos últimos 30 dias).
        """
        try:
            from datetime import datetime, timedelta
            
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            
            result = self.supabase.table('tasks')\
                .select('status, completed_at')\
                .eq('user_id', user_id)\
                .eq('status', 'done')\
                .gte('completed_at', thirty_days_ago)\
                .execute()
            
            if not result.data:
                return 50
            
            # Quantidade de tarefas concluídas = execução
            completed_count = len(result.data)
            
            # 0 tarefas = 50%, 1/dia = 100%
            # 30 tarefas em 30 dias = 100%
            execution = min(100, 50 + (completed_count * 2))
            return int(execution)
            
        except:
            return 50
    
    def _calculate_real_income(self, user_id: str) -> int:
        """
        Calcula métrica de renda baseado em transações recentes.
        Se não tem dados financeiros, retorna 50%.
        """
        try:
            from datetime import datetime, timedelta
            
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            
            # Buscar transações positivas (receitas)
            result = self.supabase.table('transactions')\
                .select('amount')\
                .eq('user_id', user_id)\
                .gt('amount', 0)\
                .gte('created_at', thirty_days_ago)\
                .execute()
            
            if not result.data:
                return 50  # Neutro se não tem dados
            
            total_income = sum([t.get('amount', 0) for t in result.data])
            
            # Lógica: quanto mais receita, maior a métrica
            # R$ 1000+ = 100%, R$ 0 = 50%
            if total_income >= 1000:
                return 100
            elif total_income >= 500:
                return 80
            elif total_income > 0:
                return 60
            else:
                return 50
                
        except:
            return 50  # Neutro em caso de erro
    
    def _calculate_real_sleep(self, user_id: str, quiz_answers: Dict) -> int:
        """
        Calcula métrica de sono baseado em check-ins recentes + resposta do quiz.
        """
        try:
            # 1. Buscar check-ins de sono recentes
            result = self.supabase.table('checkins')\
                .select('value')\
                .eq('user_id', user_id)\
                .eq('checkin_type', 'sleep')\
                .order('created_at', desc=True)\
                .limit(7)\
                .execute()
            
            if result.data:
                # Média dos últimos 7 check-ins de sono (0-10 → 0-100)
                values = [c.get('value', 5) for c in result.data]
                avg = sum(values) / len(values)
                return int(avg * 10)
            
            # 2. Se não tem check-ins, usar resposta do quiz
            sleep_quality = quiz_answers.get('sleep_quality', 'good')
            sleep_map = {
                'excellent': 90,
                'good': 70,
                'irregular': 50,
                'poor': 30,
                'very_poor': 15
            }
            return sleep_map.get(sleep_quality, 50)
            
        except:
            return 50
    
    def _calculate_real_mood(self, user_id: str) -> Dict[str, Any]:
        """
        Calcula humor médio da semana.
        Retorna: {emoji, score, trend, count}
        """
        try:
            from datetime import datetime, timedelta
            
            seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            result = self.supabase.table('checkins')\
                .select('value')\
                .eq('user_id', user_id)\
                .eq('checkin_type', 'mood')\
                .gte('created_at', seven_days_ago)\
                .order('created_at', desc=True)\
                .execute()
            
            if not result.data:
                return {"emoji": "😐", "score": 50, "count": 0}
            
            # Extrair scores dos valores JSON
            scores = []
            for c in result.data:
                val = c.get('value')
                if isinstance(val, dict):
                    scores.append(val.get('score', 5))
                elif isinstance(val, (int, float)):
                    scores.append(val)
            
            if not scores:
                return {"emoji": "😐", "score": 50, "count": 0}
            
            avg_score = sum(scores) / len(scores)
            
            # Mapear score → emoji
            if avg_score >= 8:
                emoji = "🤩"
            elif avg_score >= 6:
                emoji = "😊"
            elif avg_score >= 4:
                emoji = "😐"
            elif avg_score >= 3:
                emoji = "😢"
            else:
                emoji = "😤"
            
            return {
                "emoji": emoji,
                "score": int(avg_score * 10),  # 0-100
                "count": len(scores)
            }
            
        except Exception as e:
            logger.error("calculate_mood_failed", error=str(e))
            return {"emoji": "😐", "score": 50, "count": 0}
    
    # ==========================================
    # EVENTOS DE GAMIFICAÇÃO
    # ==========================================
    
    def on_task_completed(self, user_id: str, task_priority: str = "medium"):
        """Gatilho quando tarefa é completada."""
        xp_map = {'low': 10, 'medium': 25, 'high': 50, 'urgent': 100}
        xp = xp_map.get(task_priority, 25)
        
        self.add_xp(user_id, xp, f"Tarefa completada ({task_priority})")
        self.update_attribute(user_id, 'productivity', 2)
    
    def on_checkin_completed(self, user_id: str):
        """Gatilho quando check-in é feito."""
        self.add_xp(user_id, 15, "Check-in diário")
        self.update_attribute(user_id, 'health', 1)
    
    def on_learning_completed(self, user_id: str):
        """Gatilho quando aprende algo novo."""
        self.add_xp(user_id, 30, "Aprendizado")
        self.update_attribute(user_id, 'knowledge', 3)
    
    def on_social_interaction(self, user_id: str):
        """Gatilho para interações sociais."""
        self.add_xp(user_id, 10, "Interação social")
        self.update_attribute(user_id, 'social', 1)
    
    def on_focus_session(self, user_id: str, duration_minutes: int):
        """Gatilho para sessão de foco (Pomodoro)."""
        xp = int(duration_minutes / 5) * 10  # 10 XP por 5 min
        self.add_xp(user_id, xp, f"Foco: {duration_minutes}min")
        self.update_attribute(user_id, 'focus', int(duration_minutes / 10))


# Instância global
gamification = GamificationService()
