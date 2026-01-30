"""
TB Personal OS - Pattern Learning Service
Serviço de aprendizado que detecta e armazena padrões de comportamento do usuário
"""

import structlog
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from collections import Counter
from supabase import create_client
from app.core.config import settings
from app.services.context_service import context_service, PatternType, MemoryCategory

logger = structlog.get_logger(__name__)


class PatternLearningService:
    """
    Serviço de aprendizado de padrões que:
    - Analisa comportamento do usuário
    - Detecta padrões de uso
    - Atualiza preferências automaticamente
    - Melhora respostas com base em feedback
    """
    
    def __init__(self):
        self._supabase = None
    
    @property
    def supabase(self):
        if self._supabase is None:
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
        return self._supabase
    
    # ==========================================
    # ANÁLISE DE PADRÕES DE TEMPO
    # ==========================================
    
    async def analyze_time_patterns(self, user_id: str) -> Dict:
        """Analisa padrões de horário de uso."""
        try:
            # Buscar mensagens dos últimos 30 dias
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
            
            messages = self.supabase.table("conversation_messages")\
                .select("created_at")\
                .eq("user_id", user_id)\
                .eq("role", "user")\
                .gte("created_at", start_date)\
                .execute()
            
            if not messages.data or len(messages.data) < 10:
                return {"status": "insufficient_data", "samples": len(messages.data or [])}
            
            # Analisar distribuição por hora
            hours = []
            days_of_week = []
            
            for msg in messages.data:
                dt = datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00"))
                hours.append(dt.hour)
                days_of_week.append(dt.weekday())
            
            # Horas mais ativas
            hour_counts = Counter(hours)
            peak_hours = [h for h, _ in hour_counts.most_common(4)]
            
            # Dias mais ativos
            day_counts = Counter(days_of_week)
            peak_days = [d for d, _ in day_counts.most_common(3)]
            day_names = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
            peak_day_names = [day_names[d] for d in peak_days]
            
            # Detectar período preferido
            morning = sum(1 for h in hours if 6 <= h < 12)
            afternoon = sum(1 for h in hours if 12 <= h < 18)
            evening = sum(1 for h in hours if 18 <= h < 22)
            night = sum(1 for h in hours if h >= 22 or h < 6)
            
            periods = {"morning": morning, "afternoon": afternoon, "evening": evening, "night": night}
            preferred_period = max(periods, key=periods.get)
            
            pattern_data = {
                "peak_hours": peak_hours,
                "peak_days": peak_day_names,
                "preferred_period": preferred_period,
                "activity_distribution": periods,
                "total_samples": len(messages.data)
            }
            
            # Salvar padrão
            await context_service.add_or_update_pattern(
                user_id=user_id,
                pattern_type=PatternType.TIME_PREFERENCE,
                name="Horários de Uso",
                pattern_data=pattern_data,
                description=f"Mais ativo às {peak_hours[0]}h, prefere {preferred_period}"
            )
            
            logger.info("time_patterns_analyzed", user_id=user_id, peak_hours=peak_hours)
            
            return {"status": "success", "pattern": pattern_data}
            
        except Exception as e:
            logger.error("time_pattern_analysis_failed", error=str(e))
            return {"status": "error", "error": str(e)}
    
    # ==========================================
    # ANÁLISE DE PADRÕES DE TAREFAS
    # ==========================================
    
    async def analyze_task_patterns(self, user_id: str) -> Dict:
        """Analisa padrões de categorias de tarefas."""
        try:
            # Buscar tarefas dos últimos 90 dias
            start_date = (datetime.utcnow() - timedelta(days=90)).isoformat()
            
            tasks = self.supabase.table("tasks")\
                .select("title, priority, status, project_id, created_at, completed_at")\
                .eq("user_id", user_id)\
                .gte("created_at", start_date)\
                .execute()
            
            if not tasks.data or len(tasks.data) < 5:
                return {"status": "insufficient_data", "samples": len(tasks.data or [])}
            
            # Analisar prioridades
            priorities = [t.get("priority", 2) for t in tasks.data]
            avg_priority = sum(priorities) / len(priorities)
            
            # Taxa de conclusão
            completed = sum(1 for t in tasks.data if t.get("status") == "completed")
            completion_rate = completed / len(tasks.data)
            
            # Tempo médio de conclusão
            completion_times = []
            for t in tasks.data:
                if t.get("completed_at") and t.get("created_at"):
                    created = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
                    completed_at = datetime.fromisoformat(t["completed_at"].replace("Z", "+00:00"))
                    delta = (completed_at - created).days
                    if delta >= 0:
                        completion_times.append(delta)
            
            avg_completion_days = sum(completion_times) / len(completion_times) if completion_times else None
            
            # Projetos mais usados
            project_ids = [t.get("project_id") for t in tasks.data if t.get("project_id")]
            project_counts = Counter(project_ids)
            
            pattern_data = {
                "total_tasks": len(tasks.data),
                "completed_tasks": completed,
                "completion_rate": round(completion_rate * 100, 1),
                "avg_priority": round(avg_priority, 1),
                "avg_completion_days": round(avg_completion_days, 1) if avg_completion_days else None,
                "top_projects": dict(project_counts.most_common(5))
            }
            
            # Detectar tendência de prioridade
            priority_tendency = "balanced"
            if avg_priority >= 3.5:
                priority_tendency = "high_priority"
            elif avg_priority <= 1.5:
                priority_tendency = "low_priority"
            
            # Salvar padrão
            await context_service.add_or_update_pattern(
                user_id=user_id,
                pattern_type=PatternType.PRIORITY_TENDENCY,
                name="Tendência de Priorização",
                pattern_data=pattern_data,
                description=f"Taxa de conclusão: {pattern_data['completion_rate']}%, tendência: {priority_tendency}"
            )
            
            logger.info("task_patterns_analyzed", user_id=user_id, completion_rate=completion_rate)
            
            return {"status": "success", "pattern": pattern_data}
            
        except Exception as e:
            logger.error("task_pattern_analysis_failed", error=str(e))
            return {"status": "error", "error": str(e)}
    
    # ==========================================
    # ANÁLISE DE ESTILO DE COMUNICAÇÃO
    # ==========================================
    
    async def analyze_communication_style(self, user_id: str) -> Dict:
        """Analisa o estilo de comunicação do usuário."""
        try:
            # Buscar mensagens recentes
            messages = self.supabase.table("conversation_messages")\
                .select("content")\
                .eq("user_id", user_id)\
                .eq("role", "user")\
                .order("created_at", desc=True)\
                .limit(100)\
                .execute()
            
            if not messages.data or len(messages.data) < 10:
                return {"status": "insufficient_data", "samples": len(messages.data or [])}
            
            # Analisar mensagens
            total_chars = 0
            total_words = 0
            uses_emoji = 0
            uses_punctuation = 0
            formal_indicators = 0
            informal_indicators = 0
            
            for msg in messages.data:
                content = msg.get("content", "")
                total_chars += len(content)
                total_words += len(content.split())
                
                # Detectar emojis (simplificado)
                if any(ord(c) > 127462 for c in content):  # Unicode emoji range
                    uses_emoji += 1
                
                # Pontuação
                if content.strip().endswith(('.', '!', '?')):
                    uses_punctuation += 1
                
                # Indicadores de formalidade
                content_lower = content.lower()
                if any(word in content_lower for word in ["por favor", "obrigado", "senhor", "gostaria"]):
                    formal_indicators += 1
                if any(word in content_lower for word in ["aí", "aew", "blz", "vlw", "tmj", "kkk"]):
                    informal_indicators += 1
            
            n = len(messages.data)
            avg_length = total_chars / n
            avg_words = total_words / n
            emoji_rate = uses_emoji / n
            punctuation_rate = uses_punctuation / n
            
            # Determinar estilo
            preferred_length = "concise" if avg_words < 15 else ("detailed" if avg_words > 40 else "moderate")
            
            formality = "neutral"
            if formal_indicators > informal_indicators * 2:
                formality = "formal"
            elif informal_indicators > formal_indicators * 2:
                formality = "informal"
            
            pattern_data = {
                "avg_message_length": round(avg_length),
                "avg_word_count": round(avg_words),
                "preferred_length": preferred_length,
                "emoji_usage": emoji_rate > 0.1,
                "punctuation_usage": punctuation_rate > 0.5,
                "formality": formality,
                "samples": n
            }
            
            # Salvar padrão
            await context_service.add_or_update_pattern(
                user_id=user_id,
                pattern_type=PatternType.COMMUNICATION_STYLE,
                name="Estilo de Comunicação",
                pattern_data=pattern_data,
                description=f"Mensagens {preferred_length}, estilo {formality}"
            )
            
            logger.info("communication_style_analyzed", user_id=user_id, style=preferred_length)
            
            return {"status": "success", "pattern": pattern_data}
            
        except Exception as e:
            logger.error("communication_style_analysis_failed", error=str(e))
            return {"status": "error", "error": str(e)}
    
    # ==========================================
    # ANÁLISE DE CICLOS DE PRODUTIVIDADE
    # ==========================================
    
    async def analyze_productivity_cycles(self, user_id: str) -> Dict:
        """Analisa ciclos de produtividade."""
        try:
            start_date = (datetime.utcnow() - timedelta(days=60)).isoformat()
            
            # Buscar tarefas concluídas
            tasks = self.supabase.table("tasks")\
                .select("completed_at")\
                .eq("user_id", user_id)\
                .eq("status", "completed")\
                .gte("completed_at", start_date)\
                .not_.is_("completed_at", "null")\
                .execute()
            
            if not tasks.data or len(tasks.data) < 10:
                return {"status": "insufficient_data", "samples": len(tasks.data or [])}
            
            # Analisar por dia da semana
            day_productivity = {i: 0 for i in range(7)}
            
            for task in tasks.data:
                dt = datetime.fromisoformat(task["completed_at"].replace("Z", "+00:00"))
                day_productivity[dt.weekday()] += 1
            
            # Encontrar dias mais produtivos
            day_names = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
            sorted_days = sorted(day_productivity.items(), key=lambda x: x[1], reverse=True)
            
            peak_days = [day_names[d] for d, _ in sorted_days[:3]]
            low_days = [day_names[d] for d, _ in sorted_days[-2:]]
            
            pattern_data = {
                "peak_days": peak_days,
                "low_days": low_days,
                "productivity_by_day": {day_names[d]: count for d, count in day_productivity.items()},
                "total_completed": len(tasks.data)
            }
            
            # Salvar padrão
            await context_service.add_or_update_pattern(
                user_id=user_id,
                pattern_type=PatternType.PRODUCTIVITY_CYCLE,
                name="Ciclo de Produtividade",
                pattern_data=pattern_data,
                description=f"Mais produtivo: {', '.join(peak_days)}"
            )
            
            logger.info("productivity_cycles_analyzed", user_id=user_id, peak_days=peak_days)
            
            return {"status": "success", "pattern": pattern_data}
            
        except Exception as e:
            logger.error("productivity_cycle_analysis_failed", error=str(e))
            return {"status": "error", "error": str(e)}
    
    # ==========================================
    # ANÁLISE DE TÓPICOS DE INTERESSE
    # ==========================================
    
    async def analyze_topic_interests(self, user_id: str) -> Dict:
        """Analisa tópicos de interesse baseado em conteúdo."""
        try:
            # Buscar itens de inbox e mensagens
            inbox = self.supabase.table("inbox_items")\
                .select("content, category")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(200)\
                .execute()
            
            messages = self.supabase.table("conversation_messages")\
                .select("content")\
                .eq("user_id", user_id)\
                .eq("role", "user")\
                .order("created_at", desc=True)\
                .limit(100)\
                .execute()
            
            all_content = []
            if inbox.data:
                all_content.extend([i.get("content", "") for i in inbox.data])
            if messages.data:
                all_content.extend([m.get("content", "") for m in messages.data])
            
            if len(all_content) < 20:
                return {"status": "insufficient_data", "samples": len(all_content)}
            
            # Palavras-chave por categoria
            topic_keywords = {
                "trabalho": ["projeto", "reunião", "deadline", "entrega", "cliente", "trabalho", "task"],
                "saúde": ["academia", "treino", "exercício", "correr", "dieta", "sono", "saúde"],
                "finanças": ["pagar", "receber", "investir", "gasto", "economia", "dinheiro", "conta"],
                "conteúdo": ["post", "vídeo", "artigo", "conteúdo", "publicar", "criar", "ideia"],
                "pessoal": ["família", "amigo", "viagem", "hobby", "lazer", "diversão"],
                "aprendizado": ["estudar", "curso", "livro", "aprender", "tutorial", "aula"]
            }
            
            # Contar ocorrências
            topic_scores = {topic: 0 for topic in topic_keywords}
            
            combined_text = " ".join(all_content).lower()
            
            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    topic_scores[topic] += combined_text.count(keyword)
            
            # Ordenar por relevância
            sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
            top_interests = [t for t, score in sorted_topics if score > 0][:5]
            
            pattern_data = {
                "top_interests": top_interests,
                "interest_scores": {t: s for t, s in sorted_topics if s > 0},
                "samples_analyzed": len(all_content)
            }
            
            # Salvar padrão
            if top_interests:
                await context_service.add_or_update_pattern(
                    user_id=user_id,
                    pattern_type=PatternType.TOPIC_INTEREST,
                    name="Tópicos de Interesse",
                    pattern_data=pattern_data,
                    description=f"Principais interesses: {', '.join(top_interests[:3])}"
                )
            
            logger.info("topic_interests_analyzed", user_id=user_id, top=top_interests[:3])
            
            return {"status": "success", "pattern": pattern_data}
            
        except Exception as e:
            logger.error("topic_interest_analysis_failed", error=str(e))
            return {"status": "error", "error": str(e)}
    
    # ==========================================
    # APRENDER COM FEEDBACK
    # ==========================================
    
    async def learn_from_feedback(self, user_id: str) -> Dict:
        """Processa feedback acumulado para melhorar padrões."""
        try:
            # Buscar feedback recente
            feedback = self.supabase.table("response_feedback")\
                .select("id, feedback_type, feedback_content, corrected_response")\
                .eq("user_id", user_id)\
                .eq("applied_to_memory", False)\
                .limit(50)\
                .execute()
            
            if not feedback.data:
                return {"status": "no_new_feedback"}
            
            processed = 0
            
            for fb in feedback.data:
                fb_type = fb.get("feedback_type")
                
                if fb_type == "correction" and fb.get("corrected_response"):
                    # Criar memória de preferência
                    await context_service.add_memory(
                        user_id=user_id,
                        category=MemoryCategory.PREFERENCE,
                        content=f"Preferência de resposta: {fb.get('corrected_response')[:200]}",
                        importance=7
                    )
                    processed += 1
                    
                elif fb_type == "preference" and fb.get("feedback_content"):
                    # Adicionar como preferência direta
                    await context_service.add_memory(
                        user_id=user_id,
                        category=MemoryCategory.PREFERENCE,
                        content=fb.get("feedback_content"),
                        importance=8
                    )
                    processed += 1
                
                # Marcar como processado
                self.supabase.table("response_feedback")\
                    .update({"applied_to_memory": True, "applied_at": datetime.utcnow().isoformat()})\
                    .eq("id", fb["id"])\
                    .execute()
            
            logger.info("feedback_learned", user_id=user_id, processed=processed)
            
            return {"status": "success", "processed": processed}
            
        except Exception as e:
            logger.error("feedback_learning_failed", error=str(e))
            return {"status": "error", "error": str(e)}
    
    # ==========================================
    # ANÁLISE COMPLETA
    # ==========================================
    
    async def run_full_analysis(self, user_id: str) -> Dict:
        """Executa análise completa de todos os padrões."""
        results = {
            "time_patterns": await self.analyze_time_patterns(user_id),
            "task_patterns": await self.analyze_task_patterns(user_id),
            "communication_style": await self.analyze_communication_style(user_id),
            "productivity_cycles": await self.analyze_productivity_cycles(user_id),
            "topic_interests": await self.analyze_topic_interests(user_id),
            "feedback_learning": await self.learn_from_feedback(user_id)
        }
        
        successful = sum(1 for r in results.values() if r.get("status") == "success")
        
        logger.info("full_analysis_completed", user_id=user_id, successful=successful)
        
        return {
            "status": "completed",
            "successful_analyses": successful,
            "total_analyses": len(results),
            "details": results
        }


# Instância global
pattern_learning_service = PatternLearningService()
