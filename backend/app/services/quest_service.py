"""
TB Personal OS - Quest Service
Sistema de quests: diárias, semanais, reflexivas.
FOCO: Ação prática + reflexão inteligente.
"""

import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from supabase import create_client, Client
import random

logger = structlog.get_logger(__name__)


class QuestService:
    """
    Gerencia quests (não tarefas genéricas).
    3 tipos: diária (simples), semanal (estratégica), reflexiva (1 pergunta poderosa).
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
    
    def get_daily_quest(self, user_id: str) -> Dict[str, Any]:
        """
        Retorna quest diária ADAPTATIVA baseada no perfil.
        Motor de decisão inteligente.
        """
        try:
            # Buscar perfil para personalizar
            from app.services.profile_editor_service import profile_editor
            from app.services.gamification_service import gamification
            
            profile = profile_editor.get_profile(user_id)
            attributes = gamification.get_attributes(user_id)
            
            energy = attributes.get('energy', 50)
            execution = attributes.get('execution', 50)
            areas = profile.get('life_areas', [])
            
            # MOTOR DE DECISÃO
            # 1. Energia < 50 → quests leves
            if energy < 50:
                quests_pool = self._get_recovery_quests()
            
            # 2. Execução alta → quests desafiadoras
            elif execution > 75:
                quests_pool = self._get_high_performance_quests(areas)
            
            # 3. Renda é prioridade → quests financeiras
            elif 'money' in areas or 'business' in areas:
                quests_pool = self._get_income_quests()
            
            # 4. Corpo negligenciado → quests físicas
            elif 'body' in areas and energy < 65:
                quests_pool = self._get_body_quests()
            
            # 5. Mente em foco → quests de clareza
            elif 'mind' in areas:
                quests_pool = self._get_focus_quests()
            
            # 6. Default → quests de execução
            else:
                quests_pool = self._get_execution_quests()
            
            # Selecionar quest
            quest = random.choice(quests_pool) if quests_pool else self._default_daily_quest()
            
            # Salvar quest do dia
            quest_data = {
                'user_id': user_id,
                'type': 'daily',
                'title': quest['title'],
                'description': quest['description'],
                'xp_reward': quest['xp'],
                'attribute': quest['attribute'],
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=1)).isoformat(),
                'completed': False
            }
            
            self.supabase.table('quests').insert(quest_data).execute()
            
            return quest
            
        except Exception as e:
            logger.error("get_daily_quest_failed", error=str(e))
            return self._default_daily_quest()
    
    def _get_recovery_quests(self) -> List[Dict]:
        """Quests para energia baixa - foco em recuperação."""
        return [
            {
                'title': '⚡ Recuperação',
                'description': 'Hoje não é sobre vencer o mundo. É sobre recuperar o eixo.\n\n5 min de respiração consciente OU alongamento leve',
                'xp': 40,
                'attribute': 'energy'
            },
            {
                'title': '🧘 Reset mental',
                'description': 'Desligue notificações por 30 minutos e faça uma pausa total',
                'xp': 35,
                'attribute': 'energy'
            },
            {
                'title': '💤 Priorize o básico',
                'description': 'Durma 8h hoje OU tire um cochilo de 20 minutos',
                'xp': 40,
                'attribute': 'energy'
            }
        ]
    
    def _get_high_performance_quests(self, areas: List[str]) -> List[Dict]:
        """Quests para alta execução - aproveitar o fluxo."""
        quests = [
            {
                'title': '🔥 Momento de fluxo',
                'description': 'Você está no ritmo. Vamos aproveitar.\n\nConcluir 1 tarefa crítica que estava adiando',
                'xp': 80,
                'attribute': 'execution'
            },
            {
                'title': '🎯 Avanço estratégico',
                'description': 'Avance 1 módulo/etapa do seu projeto principal',
                'xp': 90,
                'attribute': 'execution'
            },
            {
                'title': '🧹 Fechar pendência',
                'description': 'Resolva 1 pendência antiga que drena energia mental',
                'xp': 70,
                'attribute': 'execution'
            }
        ]
        return quests
    
    def _get_income_quests(self) -> List[Dict]:
        """Quests focadas em renda."""
        return [
            {
                'title': '💰 Movimento financeiro',
                'description': 'Faça 1 contato, proposta ou venda hoje',
                'xp': 70,
                'attribute': 'income'
            },
            {
                'title': '📊 Mapeamento de renda',
                'description': 'Liste 3 possíveis novas fontes de renda (mesmo que pequenas)',
                'xp': 60,
                'attribute': 'income'
            },
            {
                'title': '🧠 Otimização financeira',
                'description': 'Identifique 1 processo que pode gerar renda ou economizar tempo',
                'xp': 65,
                'attribute': 'income'
            }
        ]
    
    def _get_body_quests(self) -> List[Dict]:
        """Quests de corpo/movimento."""
        return [
            {
                'title': '🏋️ Corpo em ação',
                'description': 'Qualquer atividade física por 20+ minutos',
                'xp': 50,
                'attribute': 'energy'
            },
            {
                'title': '🚶 Movimento básico',
                'description': 'Caminhada de 15 minutos OU alongamento completo',
                'xp': 40,
                'attribute': 'energy'
            },
            {
                'title': '💪 Reativar energia',
                'description': '10 flexões + 10 agachamentos + 1 min prancha (ou adaptado)',
                'xp': 45,
                'attribute': 'energy'
            }
        ]
    
    def _get_focus_quests(self) -> List[Dict]:
        """Quests de foco e clareza mental."""
        return [
            {
                'title': '🧠 Sessão de foco',
                'description': '1 hora de trabalho profundo (zero distração, timer ligado)',
                'xp': 60,
                'attribute': 'focus'
            },
            {
                'title': '📝 Planejamento simples',
                'description': 'Escreva as 3 prioridades de hoje (não 10, apenas 3)',
                'xp': 40,
                'attribute': 'focus'
            },
            {
                'title': '🎯 Decisão pendente',
                'description': 'Tome 1 decisão que está adiando (não precisa ser perfeita)',
                'xp': 55,
                'attribute': 'focus'
            }
        ]
    
    def _get_execution_quests(self) -> List[Dict]:
        """Quests padrão de execução."""
        return [
            {
                'title': '🎯 Ação de impacto',
                'description': 'Execute UMA ação que empurre sua meta principal para frente',
                'xp': 60,
                'attribute': 'execution'
            },
            {
                'title': '✅ Micro-vitória',
                'description': 'Complete 1 tarefa pequena que está na lista há dias',
                'xp': 45,
                'attribute': 'execution'
            },
            {
                'title': '🔨 Consistência',
                'description': 'Trabalhe 30 min no projeto que importa (não precisa terminar)',
                'xp': 50,
                'attribute': 'execution'
            }
        ]
    
    def get_weekly_quest(self, user_id: str) -> Dict[str, Any]:
        """
        Retorna quest semanal (mais estratégica).
        Relacionada às metas principais.
        """
        try:
            from app.services.profile_editor_service import profile_editor
            profile = profile_editor.get_profile(user_id)
            
            main_goal = profile.get('main_goal', '')
            areas = profile.get('life_areas', [])
            
            quests_pool = self._get_weekly_quests_pool(main_goal, areas)
            quest = random.choice(quests_pool) if quests_pool else self._default_weekly_quest()
            
            quest_data = {
                'user_id': user_id,
                'type': 'weekly',
                'title': quest['title'],
                'description': quest['description'],
                'xp_reward': quest['xp'],
                'attribute': quest['attribute'],
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                'completed': False
            }
            
            self.supabase.table('quests').insert(quest_data).execute()
            
            return quest
            
        except Exception as e:
            logger.error("get_weekly_quest_failed", error=str(e))
            return self._default_weekly_quest()
    
    def get_reflective_quest(self, user_id: str) -> Dict[str, Any]:
        """
        Quest reflexiva: 1 pergunta poderosa.
        Estimula consciência e direcionamento.
        """
        questions = [
            "O que está drenando sua atenção hoje?",
            "O que você está evitando fazer que sabe que deveria?",
            "Se você tivesse que escolher apenas 1 coisa para focar hoje, qual seria?",
            "Qual decisão você está adiando?",
            "O que mudaria se você tivesse 10x mais energia agora?",
            "Qual hábito te custa mais do que vale?",
            "Se dinheiro não fosse problema, o que você faria diferente hoje?",
            "Qual é a coisa mais importante que você não está fazendo?",
            "O que te drena energia e você ainda não cortou?",
            "Se você fosse dar um conselho para si mesmo, qual seria?",
            "Qual resultado você quer mas não está agindo pra ter?",
            "O que você faria se soubesse que não pode falhar?",
            "Qual é o custo de continuar adiando essa decisão?"
        ]
        
        question = random.choice(questions)
        
        quest = {
            'type': 'reflective',
            'title': '🧠 Reflexão do dia',
            'question': question,
            'description': f'{question}\n\n(Responda quando estiver pronto)',
            'xp': 50,
            'attribute': 'focus'
        }
        
        return quest
    
    def complete_quest(self, user_id: str, quest_id: str) -> Dict[str, Any]:
        """Marca quest como completa e concede XP."""
        try:
            # Buscar quest
            result = self.supabase.table('quests')\
                .select('*')\
                .eq('id', quest_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if not result.data:
                return {'success': False, 'message': 'Quest não encontrada'}
            
            quest = result.data[0]
            
            if quest.get('completed'):
                return {'success': False, 'message': 'Quest já completada'}
            
            # Marcar como completa
            self.supabase.table('quests').update({
                'completed': True,
                'completed_at': datetime.utcnow().isoformat()
            }).eq('id', quest_id).execute()
            
            # Conceder XP
            from app.services.gamification_service import gamification
            xp_reward = quest.get('xp_reward', 50)
            attribute = quest.get('attribute', 'execution')
            
            gamification.add_xp(
                user_id, 
                xp_reward, 
                f"Quest completada: {quest.get('title')}"
            )
            
            # Atualizar atributo específico
            gamification.increase_attribute(user_id, attribute, 5)
            
            logger.info("quest_completed", 
                       user_id=user_id, 
                       quest_type=quest.get('type'),
                       xp=xp_reward)
            
            return {
                'success': True,
                'xp': xp_reward,
                'attribute': attribute,
                'title': quest.get('title')
            }
            
        except Exception as e:
            logger.error("complete_quest_failed", error=str(e))
            return {'success': False, 'message': 'Erro ao completar quest'}
    
    def _get_daily_quests_pool(self, energy: str, areas: List[str]) -> List[Dict]:
        """Pool de quests diárias baseadas em perfil."""
        quests = []
        
        # Quests de energia
        if energy == 'low':
            quests.extend([
                {
                    'title': '⚡ Recuperação',
                    'description': 'Durma 8h hoje ou tire 1 cochilo de 20min',
                    'xp': 30,
                    'attribute': 'energy'
                },
                {
                    'title': '🧘 Reset mental',
                    'description': '10 minutos de pausa total (sem tela)',
                    'xp': 25,
                    'attribute': 'energy'
                }
            ])
        
        # Quests de execução
        if 'business' in areas or 'money' in areas:
            quests.extend([
                {
                    'title': '🎯 Ação de impacto',
                    'description': 'Qual ação pequena hoje move sua meta principal?',
                    'xp': 50,
                    'attribute': 'execution'
                },
                {
                    'title': '💰 Movimento financeiro',
                    'description': 'Faça 1 contato/proposta/venda hoje',
                    'xp': 60,
                    'attribute': 'income'
                }
            ])
        
        # Quests de foco
        if 'mind' in areas:
            quests.extend([
                {
                    'title': '🧠 Sessão de foco',
                    'description': '1 hora de trabalho profundo (zero distração)',
                    'xp': 40,
                    'attribute': 'focus'
                }
            ])
        
        # Quests de corpo
        if 'body' in areas:
            quests.extend([
                {
                    'title': '🏋️ Movimento',
                    'description': 'Qualquer atividade física por 20+ minutos',
                    'xp': 35,
                    'attribute': 'energy'
                }
            ])
        
        return quests if quests else [self._default_daily_quest()]
    
    def _get_weekly_quests_pool(self, main_goal: str, areas: List[str]) -> List[Dict]:
        """Pool de quests semanais (mais estratégicas)."""
        quests = [
            {
                'title': '📊 Revisão semanal',
                'description': 'Revise o que funcionou e o que travar esta semana',
                'xp': 100,
                'attribute': 'focus'
            },
            {
                'title': '🎯 Progresso na meta',
                'description': f'Avance concretamente em: {main_goal or "sua meta principal"}',
                'xp': 150,
                'attribute': 'execution'
            },
            {
                'title': '💡 Aprendizado aplicado',
                'description': 'Aprenda algo novo e aplique na prática',
                'xp': 120,
                'attribute': 'focus'
            }
        ]
        
        return quests
    
    def _default_daily_quest(self) -> Dict[str, Any]:
        """Quest diária padrão."""
        return {
            'title': '⚡ Ação do dia',
            'description': 'Complete 1 tarefa importante hoje',
            'xp': 30,
            'attribute': 'execution'
        }
    
    def _default_weekly_quest(self) -> Dict[str, Any]:
        """Quest semanal padrão."""
        return {
            'title': '🎯 Progresso semanal',
            'description': 'Avance em sua meta principal esta semana',
            'xp': 100,
            'attribute': 'execution'
        }


# Instância global
quest_service = QuestService()
