"""
Leads & CRM API Endpoints
Gerencia leads, funil de vendas, scripts e playbooks
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import structlog

from app.api.v1.dependencies.auth import get_api_key
from app.services.leads_service import leads_service, LeadStatus, LeadSource

router = APIRouter(prefix="/leads", tags=["Leads & CRM"])
logger = structlog.get_logger()

# Hardcoded user_id para single-user (pode ser substituído por auth real)
DEFAULT_USER_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


# ==========================================
# MODELS
# ==========================================

class LeadCreate(BaseModel):
    name: str = Field(..., description="Nome do lead/contato")
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    source: str = Field(default="other", description="Origem do lead")
    notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "João Silva",
                "email": "joao@empresa.com",
                "company": "Empresa XYZ",
                "source": "linkedin",
                "notes": "Interessado em consultoria"
            }
        }


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    score: Optional[int] = None


class LeadContact(BaseModel):
    contact_type: str = Field(..., description="Tipo: call, email, whatsapp, meeting")
    notes: str = Field(..., description="Resumo do contato")
    next_followup_days: int = Field(default=3, description="Dias até próximo follow-up")


class FollowupSchedule(BaseModel):
    followup_date: datetime
    notes: Optional[str] = None


class PlaybookCreate(BaseModel):
    title: str
    category: str = Field(..., description="script, email_template, objection, pitch")
    content: str
    tags: Optional[List[str]] = None


# ==========================================
# LEADS ENDPOINTS
# ==========================================

@router.post("")
async def create_lead(lead: LeadCreate, api_key: str = Depends(get_api_key)):
    """Cria um novo lead"""
    try:
        result = leads_service.create_lead(
            user_id=DEFAULT_USER_ID,
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            company=lead.company,
            source=lead.source,
            notes=lead.notes
        )
        return {"success": True, "lead": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_leads(
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    api_key: str = Depends(get_api_key)
):
    """Lista todos os leads com filtros opcionais"""
    leads = leads_service.get_leads(
        user_id=DEFAULT_USER_ID,
        status=status,
        source=source,
        limit=limit
    )
    return {"leads": leads, "total": len(leads)}


@router.get("/sources")
async def get_lead_sources(api_key: str = Depends(get_api_key)):
    """Lista todas as fontes de lead disponíveis"""
    return {
        "sources": [s.value for s in LeadSource],
        "descriptions": {
            "instagram": "Lead captado via Instagram",
            "linkedin": "Lead captado via LinkedIn",
            "website": "Lead do site/landing page",
            "referral": "Indicação de cliente",
            "cold_outreach": "Prospecção ativa",
            "event": "Evento/webinar",
            "other": "Outra origem"
        }
    }


@router.get("/statuses")
async def get_lead_statuses(api_key: str = Depends(get_api_key)):
    """Lista todos os status do funil"""
    return {
        "statuses": [s.value for s in LeadStatus],
        "funnel_order": ["new", "contacted", "qualified", "proposal", "negotiation", "won"],
        "descriptions": {
            "new": "Novo lead - primeiro contato pendente",
            "contacted": "Primeiro contato realizado",
            "qualified": "Lead qualificado - tem fit",
            "proposal": "Proposta enviada",
            "negotiation": "Em negociação",
            "won": "Fechado com sucesso",
            "lost": "Perdido",
            "inactive": "Inativo"
        }
    }


@router.get("/followups")
async def get_pending_followups(api_key: str = Depends(get_api_key)):
    """Lista leads que precisam de follow-up"""
    followups = leads_service.get_pending_followups(DEFAULT_USER_ID)
    return {
        "pending_followups": followups,
        "total": len(followups),
        "message": f"Você tem {len(followups)} follow-ups pendentes"
    }


@router.get("/funnel")
async def get_funnel_stats(days: int = 30, api_key: str = Depends(get_api_key)):
    """Estatísticas do funil de vendas"""
    stats = leads_service.get_funnel_stats(DEFAULT_USER_ID, days)
    return stats


@router.get("/analytics")
async def get_conversion_analytics(days: int = 90, api_key: str = Depends(get_api_key)):
    """Análise de conversão por fonte"""
    analytics = leads_service.get_conversion_analytics(DEFAULT_USER_ID, days)
    return analytics


@router.get("/predictions")
async def get_lead_predictions(api_key: str = Depends(get_api_key)):
    """Predições de conversão para leads ativos"""
    predictions = leads_service.get_lead_predictions(DEFAULT_USER_ID)
    return {
        "predictions": predictions,
        "high_probability": [p for p in predictions if p["conversion_probability"] > 60],
        "total_active": len(predictions)
    }


@router.get("/{lead_id}")
async def get_lead(lead_id: str, api_key: str = Depends(get_api_key)):
    """Obtém detalhes de um lead"""
    lead = leads_service.get_lead(DEFAULT_USER_ID, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return lead


@router.patch("/{lead_id}")
async def update_lead(
    lead_id: str,
    updates: LeadUpdate,
    api_key: str = Depends(get_api_key)
):
    """Atualiza um lead"""
    update_data = updates.model_dump(exclude_unset=True)
    result = leads_service.update_lead(DEFAULT_USER_ID, lead_id, update_data)
    if not result:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return {"success": True, "lead": result}


@router.delete("/{lead_id}")
async def delete_lead(lead_id: str, api_key: str = Depends(get_api_key)):
    """Remove um lead"""
    success = leads_service.delete_lead(DEFAULT_USER_ID, lead_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return {"success": True, "message": "Lead removido"}


@router.post("/{lead_id}/advance")
async def advance_lead(lead_id: str, api_key: str = Depends(get_api_key)):
    """Avança o lead para o próximo estágio do funil"""
    result = leads_service.advance_lead(DEFAULT_USER_ID, lead_id)
    if not result:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return {"success": True, "lead": result, "new_status": result["status"]}


@router.post("/{lead_id}/contact")
async def log_contact(
    lead_id: str,
    contact: LeadContact,
    api_key: str = Depends(get_api_key)
):
    """Registra um contato com o lead"""
    result = leads_service.log_contact(
        user_id=DEFAULT_USER_ID,
        lead_id=lead_id,
        contact_type=contact.contact_type,
        notes=contact.notes,
        next_followup_days=contact.next_followup_days
    )
    if not result:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return {"success": True, "lead": result}


@router.post("/{lead_id}/followup")
async def schedule_followup(
    lead_id: str,
    schedule: FollowupSchedule,
    api_key: str = Depends(get_api_key)
):
    """Agenda um follow-up"""
    result = leads_service.schedule_followup(
        user_id=DEFAULT_USER_ID,
        lead_id=lead_id,
        followup_date=schedule.followup_date,
        notes=schedule.notes
    )
    if not result:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return {"success": True, "lead": result}


@router.get("/{lead_id}/script")
async def get_script_for_lead(lead_id: str, api_key: str = Depends(get_api_key)):
    """Obtém script recomendado para o estágio atual do lead"""
    lead = leads_service.get_lead(DEFAULT_USER_ID, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    
    script = leads_service.get_script_for_stage(DEFAULT_USER_ID, lead["status"])
    return {
        "lead_status": lead["status"],
        "script": script,
        "has_script": script is not None
    }


# ==========================================
# PLAYBOOKS ENDPOINTS
# ==========================================

@router.get("/playbooks/list")
async def list_playbooks(api_key: str = Depends(get_api_key)):
    """Lista todos os playbooks/scripts"""
    playbooks = leads_service.get_playbooks(DEFAULT_USER_ID)
    return {"playbooks": playbooks, "total": len(playbooks)}


@router.post("/playbooks")
async def create_playbook(
    playbook: PlaybookCreate,
    api_key: str = Depends(get_api_key)
):
    """Cria um novo playbook/script"""
    try:
        result = leads_service.create_playbook(
            user_id=DEFAULT_USER_ID,
            title=playbook.title,
            category=playbook.category,
            content=playbook.content,
            tags=playbook.tags
        )
        return {"success": True, "playbook": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
