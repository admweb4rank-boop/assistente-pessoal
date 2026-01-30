"""
TB Personal OS - Onboarding Service V2
Sistema de quiz inteligente estilo Life Hacker
"""

import structlog
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.config import settings
from supabase import create_client, Client

logger = structlog.get_logger(__name__)


class OnboardingServiceV2:
    """
    Onboarding inteligente e rápido (5-7 min).
    Tom: Life hacker, direto, inteligente, zero motivacional forçado.
    """
    
    def __init__(self):
        self._supabase: Optional[Client] = None
        self.questions = self._init_questions()
    
    @property
    def supabase(self) -> Client:
        """Lazy load do Supabase."""
        if self._supabase is None:
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return self._supabase
    
    def _init_questions(self) -> List[Dict[str, Any]]:
        """Perguntas do onboarding - ESCOPO FINAL Performance Points."""
        return [
            # ETAPA 1 — IDENTIDADE BASE
            {
                'id': 'communication_style',
                'number': 1,
                'question': '1️⃣ Como você quer que o assistente te trate?',
                'options': [
                    ('direct', '🎯 Direto e prático'),
                    ('calm', '🧘 Calmo e reflexivo'),
                    ('strategic', '🔥 Estratégico e provocador'),
                    ('custom', '✏️ Personalizado (digitar)')
                ],
                'allow_custom': True
            },
            
            # ETAPA 2 — ÁREAS DA VIDA (RODA)
            {
                'id': 'life_areas',
                'number': 2,
                'question': '2️⃣ Quais áreas da sua vida você quer dar atenção agora?',
                'subtitle': '(Escolha as que fazem sentido)',
                'multiple': True,
                'max_choices': 8,
                'options': [
                    ('body_energy', '🏋️ Corpo & Energia'),
                    ('mind_emotions', '🧠 Mente & Emoções'),
                    ('work_business', '💼 Trabalho / Negócios'),
                    ('income_finances', '💰 Renda & Finanças'),
                    ('relationships', '❤️ Relacionamentos'),
                    ('spirituality_presence', '🧘 Espiritualidade / Presença'),
                    ('lifestyle_leisure', '🗺️ Estilo de vida / Lazer'),
                    ('custom', '✏️ Personalizado (digitar)')
                ],
                'allow_custom': True
            },
            
            # ETAPA 3 — HABILIDADES A DESENVOLVER
            {
                'id': 'skills',
                'number': 3,
                'question': '3️⃣ Quais habilidades você quer fortalecer?',
                'subtitle': '(Escolha até 4)',
                'multiple': True,
                'max_choices': 4,
                'options': [
                    ('presence', '🎤 Presença'),
                    ('discipline', '🎯 Disciplina'),
                    ('execution', '🛠️ Execução'),
                    ('mental_clarity', '🧠 Clareza mental'),
                    ('project_management', '📊 Gestão de projetos'),
                    ('communication', '💬 Comunicação'),
                    ('consistency', '🔁 Consistência'),
                    ('custom', '✏️ Personalizado (digitar)')
                ],
                'allow_custom': True
            },
            
            # ETAPA 4 — METAS DO ANO
            {
                'id': 'year_goals',
                'number': 4,
                'question': '4️⃣ Quais são suas principais metas este ano?',
                'subtitle': '(1 a 3 metas, texto livre)',
                'text_input': True,
                'hint': 'Exemplo: Criar meu negócio digital | Ganhar R$10k/mês | Correr 5km'
            },
            
            # ETAPA 5 — BLOQUEIOS ATUAIS
            {
                'id': 'blockers',
                'number': 5,
                'question': '5️⃣ O que mais te impede de avançar hoje?',
                'subtitle': '(Escolha 1 ou 2)',
                'multiple': True,
                'max_choices': 2,
                'options': [
                    ('energy', '🔋 Falta de energia'),
                    ('focus', '🎯 Falta de foco'),
                    ('tasks', '📋 Excesso de tarefas'),
                    ('procrastination', '⏳ Procrastinação'),
                    ('insecurity', '😰 Insegurança'),
                    ('disorganization', '🌀 Desorganização'),
                    ('custom', '✏️ Personalizado (digitar)')
                ],
                'allow_custom': True
            },
            
            # ETAPA 6 — ATIVIDADE FÍSICA
            {
                'id': 'physical_activity',
                'number': 6,
                'question': '6️⃣ Com que frequência você se movimenta hoje?',
                'options': [
                    ('sedentary', '❌ Sedentário'),
                    ('low', '🚶 1–2x por semana'),
                    ('moderate', '🏃 3–4x por semana'),
                    ('high', '🏋️ 5x ou mais'),
                    ('variable', '🔄 Variável')
                ]
            },
            
            # ETAPA 7 — QUALIDADE DO SONO
            {
                'id': 'sleep_quality',
                'number': 7,
                'question': '7️⃣ Como está seu sono ultimamente?',
                'options': [
                    ('excellent', '😴 Excelente (7-9h, qualidade alta)'),
                    ('good', '😊 Bom (6-8h, razoável)'),
                    ('irregular', '😅 Irregular (varia muito)'),
                    ('poor', '😴 Ruim (pouco ou fragmentado)'),
                    ('very_poor', '😵 Muito ruim (insônia / <5h)')
                ]
            },
            
            # ETAPA 8 — RENDA
            {
                'id': 'income_situation',
                'number': 8,
                'question': '8️⃣ Como está sua situação de renda hoje?',
                'options': [
                    ('single_source', '💼 1 fonte principal'),
                    ('multiple_sources', '🔁 Múltiplas fontes'),
                    ('variable', '📊 Variável / instável'),
                    ('building', '🚀 Construindo nova renda'),
                    ('prefer_not_say', '🔒 Prefiro não dizer')
                ]
            }
        ]
    
    def start_onboarding(self, user_id: str) -> Dict[str, Any]:
        """Inicia o onboarding."""
        try:
            # Não precisa salvar estado no banco, vamos usar context.user_data
            # Apenas retorna primeira pergunta
            return self.get_question(user_id, 0)
            
        except Exception as e:
            logger.error("start_onboarding_failed", error=str(e))
            return {}
    
    def get_question(self, user_id: str, step: int) -> Dict[str, Any]:
        """Retorna pergunta baseada no step."""
        if step >= len(self.questions):
            return {'completed': True}
        
        q = self.questions[step]
        
        result = {
            'completed': False,
            'step': step + 1,
            'total_steps': len(self.questions),
            'question_id': q['id'],
            'question': q['question'],
            'subtitle': q.get('subtitle', ''),
            'multiple': q.get('multiple', False),
            'max_choices': q.get('max_choices', 1),
            'text_input': q.get('text_input', False),
            'hint': q.get('hint', '')
        }
        
        # Adicionar options apenas se existir
        if 'options' in q:
            result['options'] = q['options']
        
        return result
    
    def save_answer(self, user_id: str, question_id: str, answer: str, current_answers: Dict = None, is_final: bool = False) -> Dict[str, Any]:
        """Salva resposta e avança (usando dicionário em memória).
        
        Para perguntas múltipla escolha:
        - Acumula respostas separadas por vírgula
        - Só avança quando is_final=True
        """
        try:
            # Usar answers passado como parâmetro
            answers = current_answers or {}
            
            # Verificar se é pergunta de múltipla escolha
            question_obj = None
            for q in self.questions:
                if q['id'] == question_id:
                    question_obj = q
                    break
            
            is_multiple = question_obj and question_obj.get('multiple', False)
            
            logger.info("save_answer_called", 
                       question_id=question_id, 
                       answer=answer, 
                       is_final=is_final,
                       is_multiple=is_multiple,
                       current_answers=answers)
            
            # Para múltipla escolha, acumular respostas
            if is_multiple and not is_final:
                # Adicionar à lista existente ou criar nova
                if question_id in answers:
                    existing = answers[question_id]
                    if answer not in existing.split(','):
                        answers[question_id] = f"{existing},{answer}"
                else:
                    # Primeira resposta de múltipla escolha
                    answers[question_id] = answer
                    
                logger.info("accumulated_answer", question_id=question_id, accumulated=answers[question_id])
            else:
                # Resposta única ou múltipla finalizada
                answers[question_id] = answer
                logger.info("final_answer_saved", question_id=question_id, answer=answer)
            
            # Contar steps (número de perguntas respondidas)
            current_step = len([k for k in answers.keys() if not k.startswith('_')])
            
            logger.info("step_calculation", 
                       current_step=current_step, 
                       total_questions=len(self.questions),
                       answers_keys=list(answers.keys()),
                       will_complete=current_step >= len(self.questions))
            
            # Se não é final (e é múltipla escolha), retornar a mesma pergunta
            if is_multiple and not is_final:
                # Buscar a pergunta atual
                question_idx = None
                for idx, q in enumerate(self.questions):
                    if q['id'] == question_id:
                        question_idx = idx
                        break
                
                if question_idx is not None:
                    result = self.get_question(user_id, question_idx)
                    result['answers'] = answers
                    result['current_step'] = current_step
                    result['accumulated'] = True  # Flag para indicar que está acumulando
                    return result
            
            # Verificar se completou todas as perguntas
            if current_step >= len(self.questions):
                result = self.complete_onboarding(user_id, answers)
                result['answers'] = answers
                return result
            
            # Próxima pergunta
            result = self.get_question(user_id, current_step)
            result['answers'] = answers
            result['current_step'] = current_step
            return result
            
        except Exception as e:
            logger.error("save_answer_failed", error=str(e), exc_info=True)
            return {}
    
    def complete_onboarding(self, user_id: str, answers: Dict[str, str]) -> Dict[str, Any]:
        """Finaliza onboarding e gera perfil."""
        try:
            # Analisar respostas
            profile = self._analyze_answers(answers)
            
            # Salvar apenas nos campos que existem na tabela
            self.supabase.table('profiles').update({
                'onboarding_completed': True,
                'quiz_answers': answers,
                'personality_profile': profile,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()
            
            logger.info("onboarding_completed", user_id=user_id, answers=answers)
            
            # XP e conquista
            try:
                from app.services.gamification_service import gamification
                gamification.unlock_achievement(
                    user_id,
                    'onboarding_complete',
                    '✨ Sistema Ativado',
                    'Completou onboarding Performance Points',
                    xp_reward=500
                )
            except Exception as xp_error:
                logger.warning("gamification_failed", error=str(xp_error))
            
            # Extrair dados para mensagem personalizada
            life_areas_str = answers.get('life_areas', '')
            life_areas_list = [a.strip() for a in life_areas_str.split(',') if a.strip()]
            year_goals = answers.get('year_goals', '')
            blockers_str = answers.get('blockers', '')
            blockers_list = [b.strip() for b in blockers_str.split(',') if b.strip()]
            
            # Área labels para exibição
            area_map = {
                'body_energy': '💪 Corpo',
                'mind_emotions': '🧠 Mente',
                'work_business': '💼 Trabalho',
                'income_finances': '💰 Renda',
                'relationships': '❤️ Relacionamentos',
                'spirituality_presence': '🧘 Presença',
                'lifestyle_leisure': '🗺️ Lifestyle'
            }
            
            areas_display = ', '.join([area_map.get(a, a) for a in life_areas_list[:3]])
            
            # Mensagem final personalizada
            completion_message = f"""🎉 *Perfil Performance Points criado!*

{profile.get('archetype_emoji', '🎖️')} *{profile.get('archetype', 'Explorador')}*
_{profile.get('description', 'Pronto para evoluir')}_

━━━━━━━━━━━━━━━━━━

📊 *SEU PERFIL:*

🎯 Foco: {areas_display}
🏆 Meta: {year_goals[:60] if year_goals else 'Definir metas'}
⚠️ Desafio: {blockers_list[0] if blockers_list else 'Manter consistência'}

━━━━━━━━━━━━━━━━━━

*PRÓXIMOS PASSOS:*

1️⃣ /status → Ver seu dashboard completo
2️⃣ /quest → Pegar primeira missão
3️⃣ Conversa natural → Só falar comigo

💡 *Dica:* A partir de agora, cada ação gera XP. Tarefas, check-ins, quests... tudo conta.

Use /help para ver todos os comandos ou apenas me mande uma mensagem!
"""
            
            return {
                'completed': True,
                'profile': profile,
                'message': completion_message
            }
            
        except Exception as e:
            logger.error("complete_onboarding_failed", error=str(e), exc_info=True)
            return {'completed': False}
    
    def _analyze_answers(self, answers: Dict[str, str]) -> Dict[str, Any]:
        """Analisa respostas e define arquétipo baseado no perfil."""
        comm_style = answers.get('communication_style', '')
        life_areas = answers.get('life_areas', '')
        blockers = answers.get('blockers', '')
        physical = answers.get('physical_activity', '')
        income = answers.get('income_situation', '')
        
        # Determinar arquétipo baseado em padrões
        
        # Arquétipo: Fundador em Ação
        if 'work_business' in life_areas and 'building' in income and 'execution' in answers.get('skills', ''):
            archetype = 'Fundador em Ação'
            emoji = '🚀'
            desc = 'Construindo império, foco em execução'
        
        # Arquétipo: Estrategista de Performance
        elif 'strategic' in comm_style and ('project_management' in answers.get('skills', '') or 'mental_clarity' in answers.get('skills', '')):
            archetype = 'Estrategista de Performance'
            emoji = '🧠'
            desc = 'Pensamento claro, decisões precisas'
        
        # Arquétipo: Guerreiro em Recuperação
        elif 'energy' in blockers or 'sedentary' in physical or 'low' in physical:
            archetype = 'Guerreiro em Recuperação'
            emoji = '⚡'
            desc = 'Reconstruindo energia e presença'
        
        # Arquétipo: Profissional Multifonte
        elif 'multiple_sources' in income:
            archetype = 'Profissional Multifonte'
            emoji = '💼'
            desc = 'Diversificação e liberdade financeira'
        
        # Arquétipo: Criador Consistente
        elif 'consistency' in answers.get('skills', '') and 'execution' in answers.get('skills', ''):
            archetype = 'Criador Consistente'
            emoji = '🛠️'
            desc = 'Pequenas ações, grandes resultados'
        
        # Arquétipo: Explorador de Equilíbrio
        elif 'body_energy' in life_areas and 'mind_emotions' in life_areas and 'spirituality_presence' in life_areas:
            archetype = 'Explorador de Equilíbrio'
            emoji = '🧘'
            desc = 'Vida integrada, presença ativa'
        
        # Arquétipo: Executor Pragmático
        elif 'direct' in comm_style and ('execution' in answers.get('skills', '') or 'discipline' in answers.get('skills', '')):
            archetype = 'Executor Pragmático'
            emoji = '🎯'
            desc = 'Ação direta, zero fluff'
        
        # Arquétipo: Buscador de Clareza
        elif 'focus' in blockers or 'disorganization' in blockers:
            archetype = 'Buscador de Clareza'
            emoji = '🧭'
            desc = 'Organizando caos, criando direção'
        
        # Default: Realizador em Evolução
        else:
            archetype = 'Realizador em Evolução'
            emoji = '⚡'
            desc = 'Progresso contínuo, sem pressa'
        
        return {
            'archetype': archetype,
            'archetype_emoji': emoji,
            'description': desc
        }


# Instância global
onboarding_v2 = OnboardingServiceV2()
