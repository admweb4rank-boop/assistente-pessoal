"""
TB Personal OS - Pytest Configuration
Fixtures e configurações de teste
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from datetime import datetime
from uuid import uuid4
import os

# Configurar ambiente de teste
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "true"
os.environ["LOG_LEVEL"] = "WARNING"


@pytest.fixture(scope="session")
def event_loop():
    """Cria event loop para testes async."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_user() -> dict:
    """Usuário mock para testes."""
    return {
        "id": str(uuid4()),
        "telegram_id": "123456789",
        "name": "Test User",
        "email": "test@example.com",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def mock_user_id() -> str:
    """ID de usuário mock."""
    return str(uuid4())


@pytest.fixture
def auth_headers(mock_user) -> dict:
    """Headers de autenticação para testes de API."""
    # Em testes, podemos mockar o token
    return {
        "Authorization": f"Bearer test-token-{mock_user['id']}",
        "Content-Type": "application/json"
    }


# ==========================================
# FIXTURES DE SERVIÇOS
# ==========================================

@pytest.fixture
def mock_supabase(mocker):
    """Mock do cliente Supabase."""
    mock_client = mocker.MagicMock()
    mocker.patch("supabase.create_client", return_value=mock_client)
    return mock_client


@pytest.fixture
def mock_gemini(mocker):
    """Mock do Gemini API."""
    mock_model = mocker.MagicMock()
    mock_model.generate_content.return_value.text = "Resposta mock do Gemini"
    
    mocker.patch("google.generativeai.GenerativeModel", return_value=mock_model)
    mocker.patch("google.generativeai.configure")
    
    return mock_model


@pytest.fixture
def mock_redis(mocker):
    """Mock do Redis."""
    mock_redis = mocker.AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.ping.return_value = True
    
    mocker.patch("redis.asyncio.from_url", return_value=mock_redis)
    
    return mock_redis


# ==========================================
# FIXTURES DE DADOS
# ==========================================

@pytest.fixture
def sample_task() -> dict:
    """Tarefa exemplo para testes."""
    return {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "title": "Tarefa de teste",
        "description": "Descrição da tarefa",
        "status": "pending",
        "priority": "medium",
        "due_date": "2025-01-25",
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_inbox_item() -> dict:
    """Item de inbox exemplo."""
    return {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "content": "Item de inbox para teste",
        "source": "telegram",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_checkin() -> dict:
    """Check-in exemplo."""
    return {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "checkin_type": "morning",
        "checkin_date": "2025-01-22",
        "data": {
            "sleep_hours": 7.5,
            "sleep_quality": 8,
            "energy": 7,
            "mood": 8
        },
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_memory() -> dict:
    """Memória exemplo."""
    return {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "content": "Memória de teste",
        "memory_type": "fact",
        "importance": 5,
        "created_at": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_transaction() -> dict:
    """Transação financeira exemplo."""
    return {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "amount": 100.00,
        "type": "expense",
        "category": "alimentacao",
        "description": "Almoço",
        "transaction_date": "2025-01-22",
        "created_at": datetime.utcnow().isoformat()
    }


# ==========================================
# CLIENTE DE TESTE FASTAPI
# ==========================================

@pytest.fixture
def app():
    """Aplicação FastAPI para testes."""
    from app.main import app
    return app


@pytest.fixture
def client(app):
    """Cliente de teste síncrono."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Cliente de teste assíncrono."""
    from httpx import AsyncClient
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ==========================================
# HELPERS
# ==========================================

class MockResponse:
    """Mock de resposta HTTP."""
    
    def __init__(self, data=None, status_code=200):
        self.data = data or []
        self.status_code = status_code
    
    def execute(self):
        return self


def make_mock_response(data=None, status_code=200):
    """Factory para criar mock responses."""
    return MockResponse(data=data, status_code=status_code)


# ==========================================
# FIXTURES ESPECÍFICAS
# ==========================================

@pytest.fixture
def google_credentials() -> dict:
    """Credenciais Google mock."""
    return {
        "access_token": "mock-access-token",
        "refresh_token": "mock-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "mock-client-id",
        "client_secret": "mock-client-secret",
        "scopes": ["email", "calendar", "gmail.readonly"]
    }


@pytest.fixture
def calendar_event() -> dict:
    """Evento de calendário mock."""
    return {
        "id": "event123",
        "summary": "Reunião de teste",
        "start": {"dateTime": "2025-01-22T10:00:00-03:00"},
        "end": {"dateTime": "2025-01-22T11:00:00-03:00"},
        "description": "Descrição do evento"
    }


@pytest.fixture
def email_message() -> dict:
    """Email mock."""
    return {
        "id": "email123",
        "threadId": "thread123",
        "from": "sender@example.com",
        "to": "user@example.com",
        "subject": "Email de teste",
        "body": "Conteúdo do email",
        "date": datetime.utcnow().isoformat()
    }
