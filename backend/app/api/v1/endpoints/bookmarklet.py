"""
Bookmarklet API Endpoints
Recebe dados capturados do bookmarklet e salva na inbox
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime
import structlog

from app.api.v1.dependencies.auth import get_current_user, get_api_key
from app.core.config import settings

router = APIRouter(prefix="/bookmarklet", tags=["Bookmarklet"])
logger = structlog.get_logger()


# ===========================================
# MODELS
# ===========================================

class BookmarkletCapture(BaseModel):
    """Dados capturados pelo bookmarklet"""
    url: str = Field(..., description="URL da página capturada")
    title: str = Field(..., description="Título da página")
    selected_text: Optional[str] = Field(None, description="Texto selecionado na página")
    description: Optional[str] = Field(None, description="Meta description da página")
    favicon: Optional[str] = Field(None, description="URL do favicon")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags opcionais")
    notes: Optional[str] = Field(None, description="Notas do usuário")
    action: str = Field(default="save", description="Ação: 'save', 'summarize', 'task'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/article",
                "title": "Artigo Interessante",
                "selected_text": "Parágrafo importante do artigo...",
                "description": "Um artigo sobre produtividade",
                "tags": ["leitura", "produtividade"],
                "action": "save"
            }
        }


class BookmarkletResponse(BaseModel):
    """Resposta do processamento do bookmarklet"""
    success: bool
    message: str
    inbox_id: Optional[str] = None
    action_taken: str
    summary: Optional[str] = None


class BookmarkletToken(BaseModel):
    """Token para autenticação do bookmarklet"""
    token: str
    expires_at: datetime
    user_id: str


# ===========================================
# HELPER FUNCTIONS
# ===========================================

def classify_url(url: str) -> str:
    """Classifica a categoria baseado na URL"""
    url_lower = url.lower()
    
    # Redes sociais / Conteúdo
    if any(domain in url_lower for domain in ['youtube.com', 'twitter.com', 'x.com', 'linkedin.com', 'instagram.com', 'tiktok.com']):
        return 'content'
    
    # Notícias
    if any(domain in url_lower for domain in ['news', 'blog', 'medium.com', 'substack.com', 'dev.to']):
        return 'content'
    
    # Trabalho / Produtividade
    if any(domain in url_lower for domain in ['notion.so', 'trello.com', 'asana.com', 'github.com', 'gitlab.com', 'jira']):
        return 'work'
    
    # Finanças
    if any(domain in url_lower for domain in ['bank', 'finance', 'invest', 'crypto', 'nubank', 'itau', 'bradesco']):
        return 'finance'
    
    # Saúde
    if any(domain in url_lower for domain in ['health', 'fitness', 'gym', 'workout', 'nutrition']):
        return 'health'
    
    # Compras
    if any(domain in url_lower for domain in ['amazon', 'mercadolivre', 'aliexpress', 'shopee', 'magalu']):
        return 'other'
    
    return 'other'


def extract_domain(url: str) -> str:
    """Extrai o domínio de uma URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')
    except:
        return url


# ===========================================
# ENDPOINTS
# ===========================================

@router.post("/capture", response_model=BookmarkletResponse)
async def capture_from_bookmarklet(
    capture: BookmarkletCapture,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """
    Recebe dados capturados do bookmarklet e salva na inbox.
    
    Actions:
    - `save`: Apenas salva na inbox
    - `summarize`: Salva e gera resumo com IA
    - `task`: Cria uma tarefa a partir do link
    """
    try:
        from supabase import Client
        from app.core.config import get_supabase_client
        
        supabase: Client = get_supabase_client()
        
        # Obter user_id do owner (single-user por enquanto)
        user_result = supabase.table("users").select("id").limit(1).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        user_id = user_result.data[0]["id"]
        
        # Determinar categoria
        category = classify_url(capture.url)
        domain = extract_domain(capture.url)
        
        # Montar conteúdo para a inbox
        content_parts = [f"🔗 {capture.title}"]
        content_parts.append(f"URL: {capture.url}")
        
        if capture.selected_text:
            content_parts.append(f"\n📝 Texto selecionado:\n{capture.selected_text[:500]}")
        
        if capture.description:
            content_parts.append(f"\n📄 Descrição: {capture.description[:200]}")
        
        if capture.notes:
            content_parts.append(f"\n💭 Notas: {capture.notes}")
        
        content = "\n".join(content_parts)
        
        # Preparar tags
        tags = capture.tags or []
        tags.append(f"via:bookmarklet")
        tags.append(f"domain:{domain}")
        
        # Metadata
        metadata = {
            "source": "bookmarklet",
            "url": capture.url,
            "domain": domain,
            "favicon": capture.favicon,
            "has_selection": bool(capture.selected_text),
            "action_requested": capture.action,
            "captured_at": datetime.utcnow().isoformat()
        }
        
        # Salvar na inbox
        inbox_data = {
            "user_id": user_id,
            "content": content,
            "content_type": "link",
            "category": category,
            "status": "new",
            "tags": tags,
            "source": "bookmarklet",
            "source_metadata": metadata
        }
        
        result = supabase.table("inbox_items").insert(inbox_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Falha ao salvar na inbox")
        
        inbox_id = result.data[0]["id"]
        summary = None
        action_taken = "saved"
        
        # Ações adicionais
        if capture.action == "summarize":
            # Gerar resumo com Gemini
            try:
                from app.services.gemini_service import gemini_service
                
                prompt = f"""Resuma este conteúdo de forma concisa:

Título: {capture.title}
URL: {capture.url}
Descrição: {capture.description or 'N/A'}
Texto selecionado: {capture.selected_text or 'N/A'}

Faça um resumo em 2-3 frases focando nos pontos principais."""

                summary = gemini_service.generate_text(prompt)
                
                # Atualizar inbox com o resumo
                supabase.table("inbox_items").update({
                    "suggested_actions": {"summary": summary}
                }).eq("id", inbox_id).execute()
                
                action_taken = "saved_and_summarized"
            except Exception as e:
                logger.warning("bookmarklet_summarize_failed", error=str(e))
                summary = "Resumo não disponível"
        
        elif capture.action == "task":
            # Criar tarefa a partir do link
            try:
                task_data = {
                    "user_id": user_id,
                    "title": f"📖 Ler: {capture.title[:100]}",
                    "description": f"Link: {capture.url}\n\n{capture.notes or ''}",
                    "status": "todo",
                    "priority": "medium",
                    "tags": ["reading", "bookmarklet"]
                }
                
                supabase.table("tasks").insert(task_data).execute()
                action_taken = "saved_and_task_created"
            except Exception as e:
                logger.warning("bookmarklet_task_failed", error=str(e))
        
        logger.info(
            "bookmarklet_capture_success",
            inbox_id=inbox_id,
            url=capture.url,
            action=capture.action,
            category=category
        )
        
        return BookmarkletResponse(
            success=True,
            message=f"Link salvo com sucesso na inbox!",
            inbox_id=inbox_id,
            action_taken=action_taken,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("bookmarklet_capture_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao processar: {str(e)}")


@router.get("/script")
async def get_bookmarklet_script():
    """
    Retorna o código JavaScript do bookmarklet.
    O usuário deve arrastar este código para a barra de favoritos.
    """
    api_url = f"{settings.API_URL or 'http://localhost:8090'}/api/v1/bookmarklet/capture"
    api_key = settings.API_KEY
    
    # JavaScript minificado do bookmarklet
    bookmarklet_code = f"""
(function(){{
    var API_URL='{api_url}';
    var API_KEY='{api_key}';
    
    var selection=window.getSelection().toString().trim();
    var meta=document.querySelector('meta[name="description"]');
    var description=meta?meta.content:'';
    var favicon='';
    var link=document.querySelector('link[rel*="icon"]');
    if(link)favicon=link.href;
    
    var data={{
        url:window.location.href,
        title:document.title,
        selected_text:selection||null,
        description:description||null,
        favicon:favicon||null,
        action:'save'
    }};
    
    var action=prompt('Ação:\\n1 = Salvar\\n2 = Salvar + Resumir\\n3 = Criar Tarefa\\n\\nEscolha (1-3):','1');
    if(!action)return;
    if(action==='2')data.action='summarize';
    if(action==='3')data.action='task';
    
    var notes=prompt('Adicionar notas (opcional):','');
    if(notes)data.notes=notes;
    
    fetch(API_URL,{{
        method:'POST',
        headers:{{
            'Content-Type':'application/json',
            'X-API-Key':API_KEY
        }},
        body:JSON.stringify(data)
    }})
    .then(r=>r.json())
    .then(d=>{{
        if(d.success){{
            alert('✅ '+d.message+(d.summary?'\\n\\nResumo: '+d.summary:''));
        }}else{{
            alert('❌ Erro: '+d.message);
        }}
    }})
    .catch(e=>alert('❌ Erro: '+e.message));
}})();
""".replace('\n', '').replace('    ', '')
    
    return {
        "bookmarklet": f"javascript:{bookmarklet_code}",
        "instructions": [
            "1. Copie o código do campo 'bookmarklet'",
            "2. Crie um novo favorito no seu navegador",
            "3. Cole o código no campo 'URL' do favorito",
            "4. Dê um nome como 'Salvar no Igor'",
            "5. Quando estiver em qualquer página, clique no favorito para salvar"
        ],
        "features": [
            "Captura URL, título e descrição da página",
            "Salva texto selecionado",
            "Opção de gerar resumo com IA",
            "Opção de criar tarefa de leitura"
        ]
    }


@router.get("/install")
async def get_install_page():
    """
    Retorna HTML da página de instalação do bookmarklet.
    """
    api_url = f"{settings.API_URL or 'http://localhost:8090'}/api/v1/bookmarklet/capture"
    api_key = settings.API_KEY
    
    bookmarklet_code = f"""javascript:(function(){{var API_URL='{api_url}';var API_KEY='{api_key}';var selection=window.getSelection().toString().trim();var meta=document.querySelector('meta[name="description"]');var description=meta?meta.content:'';var favicon='';var link=document.querySelector('link[rel*="icon"]');if(link)favicon=link.href;var data={{url:window.location.href,title:document.title,selected_text:selection||null,description:description||null,favicon:favicon||null,action:'save'}};var action=prompt('Ação:\\n1 = Salvar\\n2 = Salvar + Resumir\\n3 = Criar Tarefa\\n\\nEscolha (1-3):','1');if(!action)return;if(action==='2')data.action='summarize';if(action==='3')data.action='task';var notes=prompt('Adicionar notas (opcional):','');if(notes)data.notes=notes;fetch(API_URL,{{method:'POST',headers:{{'Content-Type':'application/json','X-API-Key':API_KEY}},body:JSON.stringify(data)}}).then(r=>r.json()).then(d=>{{if(d.success){{alert('✅ '+d.message+(d.summary?'\\n\\nResumo: '+d.summary:''));}}else{{alert('❌ Erro: '+d.message);}}}}).catch(e=>alert('❌ Erro: '+e.message));}})();"""
    
    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instalar Bookmarklet - TB Personal OS</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 700px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }}
        .bookmarklet-container {{
            background: #f8f9fa;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .bookmarklet-btn {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px 32px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 18px;
            font-weight: 600;
            cursor: grab;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .bookmarklet-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }}
        .bookmarklet-btn:active {{
            cursor: grabbing;
        }}
        .drag-hint {{
            color: #888;
            font-size: 14px;
            margin-top: 15px;
        }}
        .instructions {{
            margin-bottom: 30px;
        }}
        .instructions h2 {{
            color: #333;
            font-size: 20px;
            margin-bottom: 15px;
        }}
        .instructions ol {{
            color: #555;
            padding-left: 25px;
        }}
        .instructions li {{
            margin-bottom: 12px;
            line-height: 1.6;
        }}
        .features {{
            background: #e8f5e9;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        .features h3 {{
            color: #2e7d32;
            margin-bottom: 10px;
        }}
        .features ul {{
            list-style: none;
            color: #333;
        }}
        .features li {{
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
        }}
        .features li::before {{
            content: '✓';
            position: absolute;
            left: 0;
            color: #4caf50;
            font-weight: bold;
        }}
        .usage {{
            background: #fff3e0;
            border-radius: 12px;
            padding: 20px;
        }}
        .usage h3 {{
            color: #e65100;
            margin-bottom: 10px;
        }}
        .usage p {{
            color: #555;
            line-height: 1.6;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #888;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📌 Salvar no Igor</h1>
        <p class="subtitle">Bookmarklet para capturar links e páginas rapidamente</p>
        
        <div class="bookmarklet-container">
            <a class="bookmarklet-btn" href="{bookmarklet_code}">
                📌 Salvar no Igor
            </a>
            <p class="drag-hint">⬆️ Arraste este botão para sua barra de favoritos</p>
        </div>
        
        <div class="instructions">
            <h2>📋 Como Instalar</h2>
            <ol>
                <li><strong>Arraste o botão</strong> "Salvar no Igor" para sua barra de favoritos</li>
                <li>Se a barra não estiver visível, pressione <kbd>Ctrl+Shift+B</kbd> (Windows) ou <kbd>Cmd+Shift+B</kbd> (Mac)</li>
                <li>Pronto! Agora você pode salvar qualquer página com um clique</li>
            </ol>
        </div>
        
        <div class="features">
            <h3>✨ Funcionalidades</h3>
            <ul>
                <li>Captura URL, título e descrição automaticamente</li>
                <li>Salva texto selecionado na página</li>
                <li>Opção de gerar resumo com IA (Gemini)</li>
                <li>Opção de criar tarefa de leitura</li>
                <li>Adiciona notas personalizadas</li>
                <li>Classifica automaticamente por categoria</li>
            </ul>
        </div>
        
        <div class="usage">
            <h3>🚀 Como Usar</h3>
            <p>
                1. Navegue até qualquer página interessante<br>
                2. (Opcional) Selecione um trecho de texto<br>
                3. Clique no bookmarklet "Salvar no Igor"<br>
                4. Escolha a ação: Salvar, Resumir ou Criar Tarefa<br>
                5. Adicione notas se quiser<br>
                6. Pronto! O link está na sua Inbox
            </p>
        </div>
        
        <p class="footer">
            TB Personal OS - Seu segundo cérebro 🧠
        </p>
    </div>
</body>
</html>
"""
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


@router.get("/stats")
async def get_bookmarklet_stats(api_key: str = Depends(get_api_key)):
    """
    Retorna estatísticas de uso do bookmarklet.
    """
    try:
        from app.core.config import get_supabase_client
        
        supabase = get_supabase_client()
        
        # Contar itens salvos via bookmarklet
        result = supabase.table("inbox_items").select(
            "id", count="exact"
        ).eq("source", "bookmarklet").execute()
        
        total_captures = result.count or 0
        
        # Itens por categoria
        categories_result = supabase.table("inbox_items").select(
            "category"
        ).eq("source", "bookmarklet").execute()
        
        categories = {}
        for item in categories_result.data or []:
            cat = item.get("category", "other")
            categories[cat] = categories.get(cat, 0) + 1
        
        # Últimos 5 capturados
        recent_result = supabase.table("inbox_items").select(
            "id, content, created_at"
        ).eq("source", "bookmarklet").order(
            "created_at", desc=True
        ).limit(5).execute()
        
        return {
            "total_captures": total_captures,
            "by_category": categories,
            "recent": [
                {
                    "id": item["id"],
                    "preview": item["content"][:100] + "..." if len(item["content"]) > 100 else item["content"],
                    "created_at": item["created_at"]
                }
                for item in recent_result.data or []
            ]
        }
        
    except Exception as e:
        logger.error("bookmarklet_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
