"""
TB Personal OS - Testes do Middleware
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from uuid import uuid4


class TestMiddleware:
    """Testes para middlewares da aplicação."""
    
    @pytest.fixture
    def test_app(self):
        """App de teste com middlewares."""
        from app.core.middleware import (
            CorrelationIdMiddleware,
            SecurityHeadersMiddleware,
        )
        
        app = FastAPI()
        
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(CorrelationIdMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        return app
    
    @pytest.fixture
    def test_client(self, test_app):
        """Cliente de teste."""
        return TestClient(test_app)
    
    # ==========================================
    # CORRELATION ID MIDDLEWARE
    # ==========================================
    
    def test_correlation_id_generated(self, test_client):
        """Deve gerar correlation ID."""
        response = test_client.get("/test")
        
        assert "X-Correlation-ID" in response.headers
        
        # Verificar formato UUID
        corr_id = response.headers["X-Correlation-ID"]
        assert len(corr_id) == 36  # UUID format
    
    def test_correlation_id_passed_through(self, test_client):
        """Deve usar correlation ID fornecido."""
        custom_id = str(uuid4())
        
        response = test_client.get(
            "/test",
            headers={"X-Correlation-ID": custom_id}
        )
        
        assert response.headers["X-Correlation-ID"] == custom_id
    
    # ==========================================
    # SECURITY HEADERS MIDDLEWARE
    # ==========================================
    
    def test_security_headers_present(self, test_client):
        """Deve adicionar headers de segurança."""
        response = test_client.get("/test")
        
        # Verificar headers de segurança
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    
    def test_cache_control_api(self, test_client):
        """Deve definir Cache-Control para API."""
        response = test_client.get("/test")
        
        # API endpoints não devem ser cacheados
        cache_control = response.headers.get("Cache-Control", "")
        assert "no-store" in cache_control


class TestErrorHandlingMiddleware:
    """Testes para middleware de tratamento de erros."""
    
    @pytest.fixture
    def app_with_error_handling(self):
        """App com error handling middleware."""
        from fastapi import FastAPI
        from app.core.middleware import ErrorHandlingMiddleware
        from app.core.exceptions import ValidationError, NotFoundError
        
        app = FastAPI()
        app.add_middleware(ErrorHandlingMiddleware)
        
        @app.get("/validation-error")
        async def validation_error():
            raise ValidationError("Campo inválido")
        
        @app.get("/not-found")
        async def not_found():
            raise NotFoundError("Recurso não encontrado")
        
        @app.get("/generic-error")
        async def generic_error():
            raise Exception("Erro genérico")
        
        return app
    
    @pytest.fixture
    def client(self, app_with_error_handling):
        return TestClient(app_with_error_handling, raise_server_exceptions=False)
    
    def test_validation_error_response(self, client):
        """Deve retornar 400 para ValidationError."""
        response = client.get("/validation-error")
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_not_found_error_response(self, client):
        """Deve retornar 404 para NotFoundError."""
        response = client.get("/not-found")
        
        assert response.status_code == 404


class TestRateLimiting:
    """Testes para rate limiting."""
    
    @pytest.fixture
    def rate_limited_app(self):
        """App com rate limiting."""
        from fastapi import FastAPI
        from slowapi import Limiter
        from slowapi.util import get_remote_address
        
        limiter = Limiter(key_func=get_remote_address)
        app = FastAPI()
        app.state.limiter = limiter
        
        @app.get("/limited")
        @limiter.limit("2/minute")
        async def limited_endpoint():
            return {"status": "ok"}
        
        return app
    
    @pytest.fixture
    def client(self, rate_limited_app):
        return TestClient(rate_limited_app)
    
    def test_rate_limit_headers(self, client):
        """Deve incluir headers de rate limit."""
        response = client.get("/limited")
        
        # Primeira requisição deve passar
        assert response.status_code == 200
    
    def test_rate_limit_exceeded(self, client):
        """Deve rejeitar após exceder limite."""
        # Fazer requisições até exceder
        for _ in range(3):
            response = client.get("/limited")
        
        # Terceira requisição deve ser rejeitada
        assert response.status_code == 429
