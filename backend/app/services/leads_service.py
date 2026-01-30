"""
Leads & CRM Service
Gerencia leads, funil de vendas, scripts e playbooks
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import structlog

logger = structlog.get_logger()


class LeadStatus(str, Enum):
    """Status do lead no funil"""
    NEW = "new"                    # Novo lead
    CONTACTED = "contacted"        # Primeiro contato feito
    QUALIFIED = "qualified"        # Lead qualificado
    PROPOSAL = "proposal"          # Proposta enviada
    NEGOTIATION = "negotiation"    # Em negociação
    WON = "won"                    # Fechado/ganho
    LOST = "lost"                  # Perdido
    INACTIVE = "inactive"          # Inativo


class LeadSource(str, Enum):
    """Origem do lead"""
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    WEBSITE = "website"
    REFERRAL = "referral"
    COLD_OUTREACH = "cold_outreach"
    EVENT = "event"
    OTHER = "other"


class LeadsService:
    """Serviço de CRM e Leads"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self._ensure_supabase()
    
    def _ensure_supabase(self):
        """Garante que o cliente Supabase está disponível"""
        if not self.supabase:
            try:
                from app.core.config import get_supabase_client
                self.supabase = get_supabase_client()
            except Exception as e:
                logger.warning("supabase_not_available", error=str(e))
    
    # ==========================================
    # LEADS CRUD
    # ==========================================
    
    def create_lead(
        self,
        user_id: str,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        source: str = "other",
        notes: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Cria um novo lead"""
        try:
            lead_data = {
                "user_id": user_id,
                "name": name,
                "email": email,
                "phone": phone,
                "company": company,
                "source": source,
                "status": LeadStatus.NEW.value,
                "notes": notes,
                "metadata": metadata or {},
                "score": self._calculate_initial_score(source),
                "last_contact_at": None,
                "next_followup_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("leads").insert(lead_data).execute()
            
            logger.info("lead_created", lead_id=result.data[0]["id"], name=name)
            return result.data[0]
            
        except Exception as e:
            logger.error("lead_create_error", error=str(e))
            raise
    
    def get_leads(
        self,
        user_id: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Lista leads com filtros"""
        try:
            query = self.supabase.table("leads").select("*").eq("user_id", user_id)
            
            if status:
                query = query.eq("status", status)
            if source:
                query = query.eq("source", source)
            
            result = query.order("created_at", desc=True).limit(limit).execute()
            return result.data or []
            
        except Exception as e:
            logger.error("leads_fetch_error", error=str(e))
            return []
    
    def get_lead(self, user_id: str, lead_id: str) -> Optional[Dict[str, Any]]:
        """Obtém um lead específico"""
        try:
            result = self.supabase.table("leads").select("*").eq(
                "id", lead_id
            ).eq("user_id", user_id).single().execute()
            return result.data
        except Exception as e:
            logger.error("lead_fetch_error", error=str(e))
            return None
    
    def update_lead(
        self,
        user_id: str,
        lead_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Atualiza um lead"""
        try:
            # Track status changes
            if "status" in updates:
                old_lead = self.get_lead(user_id, lead_id)
                if old_lead:
                    self._log_status_change(lead_id, old_lead["status"], updates["status"])
            
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.supabase.table("leads").update(updates).eq(
                "id", lead_id
            ).eq("user_id", user_id).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error("lead_update_error", error=str(e))
            return None
    
    def delete_lead(self, user_id: str, lead_id: str) -> bool:
        """Remove um lead"""
        try:
            self.supabase.table("leads").delete().eq(
                "id", lead_id
            ).eq("user_id", user_id).execute()
            return True
        except Exception as e:
            logger.error("lead_delete_error", error=str(e))
            return False
    
    # ==========================================
    # FUNIL DE VENDAS
    # ==========================================
    
    def get_funnel_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Estatísticas do funil de vendas"""
        try:
            since = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            result = self.supabase.table("leads").select("status, source").eq(
                "user_id", user_id
            ).gte("created_at", since).execute()
            
            leads = result.data or []
            
            # Contar por status
            funnel = {status.value: 0 for status in LeadStatus}
            sources = {}
            
            for lead in leads:
                status = lead.get("status", "new")
                source = lead.get("source", "other")
                funnel[status] = funnel.get(status, 0) + 1
                sources[source] = sources.get(source, 0) + 1
            
            # Calcular conversões
            total = len(leads)
            won = funnel.get("won", 0)
            conversion_rate = (won / total * 100) if total > 0 else 0
            
            return {
                "total_leads": total,
                "funnel": funnel,
                "by_source": sources,
                "conversion_rate": round(conversion_rate, 1),
                "won": won,
                "lost": funnel.get("lost", 0),
                "active": total - won - funnel.get("lost", 0) - funnel.get("inactive", 0),
                "period_days": days
            }
            
        except Exception as e:
            logger.error("funnel_stats_error", error=str(e))
            return {"error": str(e)}
    
    def advance_lead(self, user_id: str, lead_id: str) -> Optional[Dict[str, Any]]:
        """Avança o lead para o próximo estágio do funil"""
        lead = self.get_lead(user_id, lead_id)
        if not lead:
            return None
        
        status_order = [
            LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.QUALIFIED,
            LeadStatus.PROPOSAL, LeadStatus.NEGOTIATION, LeadStatus.WON
        ]
        
        current_status = lead["status"]
        current_index = next(
            (i for i, s in enumerate(status_order) if s.value == current_status), -1
        )
        
        if current_index >= 0 and current_index < len(status_order) - 1:
            next_status = status_order[current_index + 1].value
            return self.update_lead(user_id, lead_id, {"status": next_status})
        
        return lead
    
    # ==========================================
    # FOLLOW-UPS
    # ==========================================
    
    def get_pending_followups(self, user_id: str) -> List[Dict[str, Any]]:
        """Lista leads que precisam de follow-up"""
        try:
            now = datetime.utcnow().isoformat()
            
            result = self.supabase.table("leads").select("*").eq(
                "user_id", user_id
            ).lte("next_followup_at", now).not_.in_(
                "status", ["won", "lost", "inactive"]
            ).order("next_followup_at").execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error("followups_fetch_error", error=str(e))
            return []
    
    def schedule_followup(
        self,
        user_id: str,
        lead_id: str,
        followup_date: datetime,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Agenda um follow-up"""
        updates = {
            "next_followup_at": followup_date.isoformat(),
            "last_contact_at": datetime.utcnow().isoformat()
        }
        
        if notes:
            lead = self.get_lead(user_id, lead_id)
            if lead:
                current_notes = lead.get("notes", "") or ""
                timestamp = datetime.utcnow().strftime("%d/%m %H:%M")
                updates["notes"] = f"{current_notes}\n[{timestamp}] {notes}".strip()
        
        return self.update_lead(user_id, lead_id, updates)
    
    def log_contact(
        self,
        user_id: str,
        lead_id: str,
        contact_type: str,
        notes: str,
        next_followup_days: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Registra um contato com o lead"""
        lead = self.get_lead(user_id, lead_id)
        if not lead:
            return None
        
        # Atualizar histórico
        current_notes = lead.get("notes", "") or ""
        timestamp = datetime.utcnow().strftime("%d/%m %H:%M")
        new_notes = f"{current_notes}\n[{timestamp}] ({contact_type}) {notes}".strip()
        
        # Atualizar score baseado em engajamento
        new_score = min(100, (lead.get("score", 50) or 50) + 5)
        
        updates = {
            "notes": new_notes,
            "last_contact_at": datetime.utcnow().isoformat(),
            "next_followup_at": (datetime.utcnow() + timedelta(days=next_followup_days)).isoformat(),
            "score": new_score
        }
        
        # Se primeiro contato, avançar status
        if lead["status"] == LeadStatus.NEW.value:
            updates["status"] = LeadStatus.CONTACTED.value
        
        return self.update_lead(user_id, lead_id, updates)
    
    # ==========================================
    # SCRIPTS E PLAYBOOKS
    # ==========================================
    
    def get_playbooks(self, user_id: str) -> List[Dict[str, Any]]:
        """Lista playbooks de vendas"""
        try:
            result = self.supabase.table("playbooks").select("*").eq(
                "user_id", user_id
            ).order("created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error("playbooks_fetch_error", error=str(e))
            return []
    
    def create_playbook(
        self,
        user_id: str,
        title: str,
        category: str,
        content: str,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Cria um playbook/script"""
        try:
            data = {
                "user_id": user_id,
                "title": title,
                "category": category,  # "script", "email_template", "objection", "pitch"
                "content": content,
                "tags": tags or [],
                "usage_count": 0
            }
            
            result = self.supabase.table("playbooks").insert(data).execute()
            return result.data[0]
            
        except Exception as e:
            logger.error("playbook_create_error", error=str(e))
            raise
    
    def get_script_for_stage(self, user_id: str, stage: str) -> Optional[Dict[str, Any]]:
        """Obtém script recomendado para estágio do funil"""
        try:
            # Mapear estágio para categoria de script
            stage_to_category = {
                "new": "first_contact",
                "contacted": "qualification",
                "qualified": "pitch",
                "proposal": "proposal",
                "negotiation": "objection_handling"
            }
            
            category = stage_to_category.get(stage, "general")
            
            result = self.supabase.table("playbooks").select("*").eq(
                "user_id", user_id
            ).eq("category", category).limit(1).execute()
            
            if result.data:
                # Incrementar uso
                self.supabase.table("playbooks").update({
                    "usage_count": result.data[0].get("usage_count", 0) + 1
                }).eq("id", result.data[0]["id"]).execute()
                
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error("script_fetch_error", error=str(e))
            return None
    
    # ==========================================
    # ANALYTICS
    # ==========================================
    
    def get_conversion_analytics(self, user_id: str, days: int = 90) -> Dict[str, Any]:
        """Análise de conversão por fonte e padrões"""
        try:
            since = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            result = self.supabase.table("leads").select(
                "status, source, created_at, score"
            ).eq("user_id", user_id).gte("created_at", since).execute()
            
            leads = result.data or []
            
            # Análise por fonte
            source_stats = {}
            for lead in leads:
                source = lead.get("source", "other")
                if source not in source_stats:
                    source_stats[source] = {"total": 0, "won": 0, "avg_score": []}
                
                source_stats[source]["total"] += 1
                source_stats[source]["avg_score"].append(lead.get("score", 50))
                
                if lead.get("status") == "won":
                    source_stats[source]["won"] += 1
            
            # Calcular métricas
            for source, stats in source_stats.items():
                stats["conversion_rate"] = round(
                    (stats["won"] / stats["total"] * 100) if stats["total"] > 0 else 0, 1
                )
                stats["avg_score"] = round(
                    sum(stats["avg_score"]) / len(stats["avg_score"]) if stats["avg_score"] else 0, 1
                )
            
            # Identificar melhor fonte
            best_source = max(
                source_stats.items(),
                key=lambda x: x[1]["conversion_rate"],
                default=(None, {})
            )
            
            return {
                "by_source": source_stats,
                "best_source": best_source[0],
                "best_conversion_rate": best_source[1].get("conversion_rate", 0),
                "total_analyzed": len(leads),
                "period_days": days,
                "insights": self._generate_insights(source_stats)
            }
            
        except Exception as e:
            logger.error("analytics_error", error=str(e))
            return {"error": str(e)}
    
    def get_lead_predictions(self, user_id: str) -> List[Dict[str, Any]]:
        """Predições sobre quais leads têm mais chance de fechar"""
        try:
            # Buscar leads ativos
            result = self.supabase.table("leads").select("*").eq(
                "user_id", user_id
            ).not_.in_("status", ["won", "lost", "inactive"]).execute()
            
            leads = result.data or []
            
            # Calcular probabilidade de conversão
            predictions = []
            for lead in leads:
                probability = self._calculate_conversion_probability(lead)
                predictions.append({
                    "lead_id": lead["id"],
                    "name": lead["name"],
                    "company": lead.get("company"),
                    "status": lead["status"],
                    "score": lead.get("score", 50),
                    "conversion_probability": probability,
                    "recommendation": self._get_recommendation(lead, probability)
                })
            
            # Ordenar por probabilidade
            predictions.sort(key=lambda x: x["conversion_probability"], reverse=True)
            
            return predictions
            
        except Exception as e:
            logger.error("predictions_error", error=str(e))
            return []
    
    # ==========================================
    # HELPERS
    # ==========================================
    
    def _calculate_initial_score(self, source: str) -> int:
        """Calcula score inicial baseado na fonte"""
        source_scores = {
            "referral": 80,
            "website": 60,
            "linkedin": 55,
            "instagram": 50,
            "cold_outreach": 40,
            "event": 65,
            "other": 50
        }
        return source_scores.get(source, 50)
    
    def _calculate_conversion_probability(self, lead: Dict[str, Any]) -> float:
        """Calcula probabilidade de conversão"""
        score = lead.get("score", 50)
        status = lead.get("status", "new")
        
        # Peso do status no funil
        status_weights = {
            "new": 0.1,
            "contacted": 0.2,
            "qualified": 0.4,
            "proposal": 0.6,
            "negotiation": 0.8
        }
        
        status_weight = status_weights.get(status, 0.1)
        
        # Fator de engajamento (baseado em last_contact)
        last_contact = lead.get("last_contact_at")
        engagement_factor = 1.0
        if last_contact:
            days_since_contact = (datetime.utcnow() - datetime.fromisoformat(
                last_contact.replace("Z", "+00:00")
            )).days
            engagement_factor = max(0.5, 1 - (days_since_contact * 0.05))
        
        # Calcular probabilidade
        probability = (score / 100 * 0.4) + (status_weight * 0.4) + (engagement_factor * 0.2)
        return round(probability * 100, 1)
    
    def _get_recommendation(self, lead: Dict[str, Any], probability: float) -> str:
        """Gera recomendação para o lead"""
        status = lead.get("status", "new")
        
        if probability > 70:
            return "🔥 Alta prioridade - Fechar logo!"
        elif probability > 50:
            if status == "proposal":
                return "📞 Ligar para discutir proposta"
            elif status == "qualified":
                return "📄 Enviar proposta personalizada"
            else:
                return "⚡ Qualificar necessidades"
        elif probability > 30:
            return "📧 Manter contato com conteúdo relevante"
        else:
            return "⏸️ Nutrir a longo prazo"
    
    def _generate_insights(self, source_stats: Dict) -> List[str]:
        """Gera insights sobre conversão"""
        insights = []
        
        if not source_stats:
            return ["Dados insuficientes para gerar insights"]
        
        # Melhor fonte
        best = max(source_stats.items(), key=lambda x: x[1]["conversion_rate"], default=None)
        if best and best[1]["conversion_rate"] > 0:
            insights.append(f"📈 Leads de '{best[0]}' convertem {best[1]['conversion_rate']}%")
        
        # Fonte com mais volume
        highest_volume = max(source_stats.items(), key=lambda x: x[1]["total"], default=None)
        if highest_volume:
            insights.append(f"📊 Maior volume vem de '{highest_volume[0]}' ({highest_volume[1]['total']} leads)")
        
        # Comparação referral vs cold
        if "referral" in source_stats and "cold_outreach" in source_stats:
            ref_rate = source_stats["referral"]["conversion_rate"]
            cold_rate = source_stats["cold_outreach"]["conversion_rate"]
            if ref_rate > cold_rate * 1.5:
                insights.append("💡 Referrals convertem muito melhor - investir em programa de indicação")
        
        return insights
    
    def _log_status_change(self, lead_id: str, old_status: str, new_status: str):
        """Registra mudança de status"""
        logger.info(
            "lead_status_changed",
            lead_id=lead_id,
            old_status=old_status,
            new_status=new_status
        )


# Singleton
leads_service = LeadsService()
