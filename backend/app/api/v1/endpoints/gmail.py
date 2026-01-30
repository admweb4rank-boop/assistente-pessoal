"""
TB Personal OS - Gmail API Endpoints
Endpoints para gerenciamento de emails via Gmail
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from pydantic import BaseModel, EmailStr
import structlog

from app.api.v1.dependencies.auth import get_current_user
from app.services.gmail_service import gmail_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/gmail", tags=["Gmail"])


# ==========================================
# SCHEMAS
# ==========================================

class EmailSummary(BaseModel):
    """Resumo de um email."""
    id: str
    thread_id: str
    from_address: str
    to: str
    subject: str
    date: str
    snippet: str
    is_unread: bool


class EmailFull(BaseModel):
    """Email completo com corpo."""
    id: str
    thread_id: str
    from_address: str
    to: str
    subject: str
    date: str
    body: str
    labels: List[str]
    is_unread: bool


class ThreadResponse(BaseModel):
    """Thread de emails."""
    thread_id: str
    messages: List[dict]
    message_count: int


class DraftCreate(BaseModel):
    """Dados para criar rascunho."""
    to: EmailStr
    subject: str
    body: str


class ReplyDraftCreate(BaseModel):
    """Dados para criar rascunho de resposta."""
    message_id: str
    body: str


class SendEmailRequest(BaseModel):
    """Dados para enviar email."""
    to: EmailStr
    subject: str
    body: str


class InboxSummaryResponse(BaseModel):
    """Resumo do inbox."""
    unread_count: int
    inbox_count: int
    starred_count: int


# ==========================================
# ENDPOINTS - READ
# ==========================================

@router.get("/unread", response_model=List[EmailSummary])
async def get_unread_emails(
    max_results: int = Query(10, ge=1, le=50),
    hours_back: int = Query(24, ge=1, le=168),
    user: dict = Depends(get_current_user)
):
    """
    Lista emails não lidos.
    
    - **max_results**: Máximo de emails (1-50)
    - **hours_back**: Buscar das últimas X horas (1-168)
    """
    try:
        emails = await gmail_service.get_unread_emails(
            user_id=user["id"],
            max_results=max_results,
            hours_back=hours_back
        )
        
        return [
            EmailSummary(
                id=e['id'],
                thread_id=e['thread_id'],
                from_address=e['from'],
                to=e['to'],
                subject=e['subject'],
                date=e['date'],
                snippet=e['snippet'],
                is_unread=e['is_unread']
            )
            for e in emails
        ]
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("get_unread_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar emails: {str(e)}")


@router.get("/messages/{message_id}", response_model=EmailFull)
async def get_email(
    message_id: str,
    user: dict = Depends(get_current_user)
):
    """Obtém um email completo pelo ID."""
    try:
        email = await gmail_service.get_email_full(
            user_id=user["id"],
            message_id=message_id
        )
        
        return EmailFull(
            id=email['id'],
            thread_id=email['thread_id'],
            from_address=email['from'],
            to=email['to'],
            subject=email['subject'],
            date=email['date'],
            body=email['body'],
            labels=email['labels'],
            is_unread=email['is_unread']
        )
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("get_email_failed", user_id=user["id"], message_id=message_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar email: {str(e)}")


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    user: dict = Depends(get_current_user)
):
    """Obtém uma thread completa de emails."""
    try:
        thread = await gmail_service.get_thread(
            user_id=user["id"],
            thread_id=thread_id
        )
        
        return ThreadResponse(**thread)
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("get_thread_failed", user_id=user["id"], thread_id=thread_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar thread: {str(e)}")


@router.get("/summary", response_model=InboxSummaryResponse)
async def get_inbox_summary(
    user: dict = Depends(get_current_user)
):
    """Obtém resumo do inbox (contagens)."""
    try:
        summary = await gmail_service.get_inbox_summary(user_id=user["id"])
        return InboxSummaryResponse(**summary)
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("get_summary_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao buscar resumo: {str(e)}")


@router.get("/search", response_model=List[EmailSummary])
async def search_emails(
    q: str = Query(..., description="Query de busca do Gmail"),
    max_results: int = Query(10, ge=1, le=50),
    user: dict = Depends(get_current_user)
):
    """
    Busca emails com query do Gmail.
    
    Exemplos de query:
    - from:pessoa@email.com
    - subject:reunião
    - has:attachment
    - after:2026/01/01
    """
    try:
        emails = await gmail_service.search_emails(
            user_id=user["id"],
            query=q,
            max_results=max_results
        )
        
        return [
            EmailSummary(
                id=e['id'],
                thread_id=e['thread_id'],
                from_address=e['from'],
                to=e['to'],
                subject=e['subject'],
                date=e['date'],
                snippet=e['snippet'],
                is_unread=e['is_unread']
            )
            for e in emails
        ]
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("search_failed", user_id=user["id"], query=q, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


# ==========================================
# ENDPOINTS - ACTIONS
# ==========================================

@router.post("/messages/{message_id}/read")
async def mark_as_read(
    message_id: str,
    user: dict = Depends(get_current_user)
):
    """Marca um email como lido."""
    try:
        await gmail_service.mark_as_read(
            user_id=user["id"],
            message_id=message_id
        )
        return {"status": "success", "message": "Email marcado como lido"}
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("mark_read_failed", user_id=user["id"], message_id=message_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao marcar como lido: {str(e)}")


@router.post("/messages/{message_id}/unread")
async def mark_as_unread(
    message_id: str,
    user: dict = Depends(get_current_user)
):
    """Marca um email como não lido."""
    try:
        await gmail_service.mark_as_unread(
            user_id=user["id"],
            message_id=message_id
        )
        return {"status": "success", "message": "Email marcado como não lido"}
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("mark_unread_failed", user_id=user["id"], message_id=message_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao marcar como não lido: {str(e)}")


@router.post("/messages/{message_id}/archive")
async def archive_email(
    message_id: str,
    user: dict = Depends(get_current_user)
):
    """Arquiva um email (remove do inbox)."""
    try:
        await gmail_service.archive_email(
            user_id=user["id"],
            message_id=message_id
        )
        return {"status": "success", "message": "Email arquivado"}
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("archive_failed", user_id=user["id"], message_id=message_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao arquivar: {str(e)}")


# ==========================================
# ENDPOINTS - DRAFTS & SEND
# ==========================================

@router.post("/drafts")
async def create_draft(
    data: DraftCreate,
    user: dict = Depends(get_current_user)
):
    """
    Cria um rascunho de email.
    
    O rascunho fica salvo e pode ser enviado depois via /drafts/{id}/send
    """
    try:
        draft = await gmail_service.create_draft(
            user_id=user["id"],
            to=data.to,
            subject=data.subject,
            body=data.body
        )
        return draft
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("create_draft_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao criar rascunho: {str(e)}")


@router.post("/drafts/reply")
async def create_reply_draft(
    data: ReplyDraftCreate,
    user: dict = Depends(get_current_user)
):
    """
    Cria rascunho de resposta a um email.
    
    Automaticamente:
    - Usa o remetente original como destinatário
    - Adiciona "Re:" ao assunto
    - Mantém na mesma thread
    """
    try:
        draft = await gmail_service.create_reply_draft(
            user_id=user["id"],
            message_id=data.message_id,
            body=data.body
        )
        return draft
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("create_reply_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao criar resposta: {str(e)}")


@router.post("/drafts/{draft_id}/send")
async def send_draft(
    draft_id: str,
    user: dict = Depends(get_current_user)
):
    """Envia um rascunho existente."""
    try:
        result = await gmail_service.send_draft(
            user_id=user["id"],
            draft_id=draft_id
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("send_draft_failed", user_id=user["id"], draft_id=draft_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao enviar: {str(e)}")


@router.post("/send")
async def send_email(
    data: SendEmailRequest,
    user: dict = Depends(get_current_user)
):
    """
    Envia email diretamente (sem criar rascunho).
    
    ⚠️ Use com cuidado - envia imediatamente!
    """
    try:
        result = await gmail_service.send_email(
            user_id=user["id"],
            to=data.to,
            subject=data.subject,
            body=data.body
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("send_email_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao enviar: {str(e)}")


# ==========================================
# ENDPOINTS - LABELS
# ==========================================

@router.get("/labels")
async def list_labels(
    user: dict = Depends(get_current_user)
):
    """Lista todas as labels/pastas do Gmail."""
    try:
        labels = await gmail_service.list_labels(user_id=user["id"])
        return {"labels": labels}
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error("list_labels_failed", user_id=user["id"], error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao listar labels: {str(e)}")
