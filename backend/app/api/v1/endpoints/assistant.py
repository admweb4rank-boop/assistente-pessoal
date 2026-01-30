"""
TB Personal OS - Assistant API Endpoints
Endpoints para interação direta com o assistente
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import structlog

from supabase import Client
from app.api.v1.dependencies import get_supabase_client, get_current_user, get_current_user_id
from app.services.assistant_service import AssistantService
from app.models.common import SuccessResponse

logger = structlog.get_logger(__name__)

router = APIRouter()


class ProcessMessageRequest(BaseModel):
    """Request para processar mensagem."""
    content: str = Field(..., min_length=1, max_length=10000, description="Conteúdo da mensagem")
    source: str = Field(default="api", pattern="^(api|web|telegram)$")
    source_metadata: Optional[Dict[str, Any]] = None


class AskQuestionRequest(BaseModel):
    """Request para fazer pergunta ao assistente."""
    question: str = Field(..., min_length=1, max_length=5000)
    include_context: bool = Field(default=True, description="Incluir contexto do usuário")


@router.post(
    "/process",
    response_model=SuccessResponse,
    summary="Processar mensagem",
    description="Processa uma mensagem com IA, classifica e salva na inbox"
)
async def process_message(
    request: ProcessMessageRequest,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Processa uma mensagem do usuário:
    1. Classifica com Gemini AI
    2. Extrai entidades
    3. Salva na inbox
    4. Sugere ações
    5. Gera resposta se necessário
    """
    try:
        assistant = AssistantService(supabase)
        
        result = await assistant.process_message(
            user_id=user_id,
            content=request.content,
            source=request.source,
            source_metadata=request.source_metadata
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Processing failed")
            )
        
        return SuccessResponse(
            data=result,
            message="Message processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("process_message_endpoint_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post(
    "/ask",
    response_model=SuccessResponse,
    summary="Fazer pergunta",
    description="Faz uma pergunta ao assistente e recebe uma resposta"
)
async def ask_question(
    request: AskQuestionRequest,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Faz uma pergunta ao assistente."""
    try:
        assistant = AssistantService(supabase)
        
        # Obter contexto se solicitado
        context_text = ""
        user_info = None
        
        if request.include_context:
            context = await assistant.get_user_context(user_id)
            context_text = assistant._format_context_for_ai(context)
            user_info = context.get("profile")
        
        # Gerar resposta
        response = await assistant.gemini.generate_response(
            question=request.question,
            context=context_text,
            user_info=user_info
        )
        
        return SuccessResponse(
            data={"response": response},
            message="Question answered"
        )
        
    except Exception as e:
        logger.error("ask_question_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.get(
    "/summary/morning",
    response_model=SuccessResponse,
    summary="Resumo da manhã",
    description="Gera o resumo matinal com agenda e prioridades"
)
async def get_morning_summary(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Obtém o resumo da manhã."""
    try:
        assistant = AssistantService(supabase)
        result = await assistant.generate_morning_summary(user_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Summary generation failed")
            )
        
        return SuccessResponse(data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("morning_summary_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.get(
    "/summary/night",
    response_model=SuccessResponse,
    summary="Resumo da noite",
    description="Gera o resumo de fechamento do dia"
)
async def get_night_summary(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Obtém o resumo da noite."""
    try:
        assistant = AssistantService(supabase)
        result = await assistant.generate_night_summary(user_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Summary generation failed")
            )
        
        return SuccessResponse(data=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("night_summary_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=SuccessResponse,
    summary="Estatísticas de produtividade",
    description="Obtém estatísticas de produtividade do usuário"
)
async def get_productivity_stats(
    days: int = 7,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Obtém estatísticas de produtividade."""
    try:
        assistant = AssistantService(supabase)
        stats = await assistant.get_productivity_stats(user_id, days)
        
        return SuccessResponse(
            data=stats,
            message=f"Stats for last {days} days"
        )
        
    except Exception as e:
        logger.error("get_stats_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get(
    "/context",
    response_model=SuccessResponse,
    summary="Contexto do usuário",
    description="Obtém o contexto atual do usuário"
)
async def get_user_context(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase_client)
):
    """Obtém o contexto do usuário."""
    try:
        assistant = AssistantService(supabase)
        context = await assistant.get_user_context(user_id)
        
        return SuccessResponse(data=context)
        
    except Exception as e:
        logger.error("get_context_failed", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get context: {str(e)}"
        )
