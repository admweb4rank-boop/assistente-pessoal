"""
TB Personal OS - Test Suite
Testes básicos para validar os novos serviços
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
import json


# ==========================================
# MEMORY SERVICE TESTS
# ==========================================

class TestMemoryService:
    """Testes para o MemoryService."""
    
    @pytest.fixture
    def memory_service(self):
        from app.services.memory_service import MemoryService
        service = MemoryService()
        service._supabase = MagicMock()
        return service
    
    @pytest.mark.asyncio
    async def test_remember_saves_memory(self, memory_service):
        """Testa se remember salva memória corretamente."""
        memory_service.supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "test-id",
                "content": "Test memory",
                "context_type": "general",
                "source": "user",
                "created_at": datetime.utcnow().isoformat()
            }]
        )
        
        result = await memory_service.remember(
            user_id="user-123",
            content="Test memory",
            category="general"
        )
        
        assert result["content"] == "Test memory"
        assert result["context_type"] == "general"
    
    @pytest.mark.asyncio
    async def test_search_memories(self, memory_service):
        """Testa busca de memórias."""
        memory_service.supabase.table.return_value.select.return_value.eq.return_value.ilike.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[
                {"id": "1", "content": "Test result", "context_type": "general"}
            ]
        )
        
        results = await memory_service.search_memories(
            user_id="user-123",
            query="test"
        )
        
        assert len(results) == 1
        assert "Test result" in results[0]["content"]


# ==========================================
# INSIGHTS SERVICE TESTS
# ==========================================

class TestInsightsService:
    """Testes para o InsightsService."""
    
    @pytest.fixture
    def insights_service(self):
        from app.services.insights_service import InsightsService
        service = InsightsService()
        service._supabase = MagicMock()
        return service
    
    @pytest.mark.asyncio
    async def test_productivity_score_calculation(self, insights_service):
        """Testa cálculo do score de produtividade."""
        # Mock de tarefas
        insights_service.supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = MagicMock(
            data=[
                {"id": "1", "status": "done", "completed_at": datetime.utcnow().isoformat()},
                {"id": "2", "status": "done", "completed_at": datetime.utcnow().isoformat()},
                {"id": "3", "status": "todo", "completed_at": None},
            ]
        )
        
        result = await insights_service.get_productivity_score(
            user_id="user-123",
            days=7
        )
        
        assert "score" in result
        assert "level" in result
        assert result["score"] >= 0 and result["score"] <= 100
    
    @pytest.mark.asyncio
    async def test_recommendations_generation(self, insights_service):
        """Testa geração de recomendações."""
        # Mock para tarefas pendentes
        insights_service.supabase.table.return_value.select.return_value.eq.return_value.neq.return_value.execute.return_value = MagicMock(
            data=[
                {"id": "1", "priority": "high", "due_date": (datetime.utcnow() - timedelta(days=1)).isoformat()},
            ]
        )
        
        recommendations = await insights_service.generate_recommendations(
            user_id="user-123"
        )
        
        assert isinstance(recommendations, list)


# ==========================================
# AUTONOMY SERVICE TESTS
# ==========================================

class TestAutonomyService:
    """Testes para o AutonomyService."""
    
    @pytest.fixture
    def autonomy_service(self):
        from app.services.autonomy_service import AutonomyService
        service = AutonomyService()
        service._supabase = MagicMock()
        return service
    
    @pytest.mark.asyncio
    async def test_can_perform_action_allowed(self, autonomy_service):
        """Testa verificação de ação permitida."""
        autonomy_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"autonomy_level": 4}
        )
        
        result = await autonomy_service.can_perform_action(
            user_id="user-123",
            action="read_tasks"
        )
        
        assert result["allowed"] is True
    
    @pytest.mark.asyncio
    async def test_can_perform_action_requires_confirmation(self, autonomy_service):
        """Testa ação que requer confirmação."""
        autonomy_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"autonomy_level": 2}  # SUGGESTER
        )
        
        result = await autonomy_service.can_perform_action(
            user_id="user-123",
            action="create_task"  # Requer CONFIRMER (3)
        )
        
        assert result["allowed"] is True
        assert result["requires_confirmation"] is True
    
    def test_level_descriptions(self, autonomy_service):
        """Testa descrições dos níveis."""
        for level in range(1, 6):
            desc = autonomy_service.get_level_description(level)
            assert "name" in desc
            assert "description" in desc
            assert "examples" in desc


# ==========================================
# CONTENT SERVICE TESTS
# ==========================================

class TestContentService:
    """Testes para o ContentService."""
    
    @pytest.fixture
    def content_service(self):
        from app.services.content_service import ContentService
        service = ContentService()
        service._supabase = MagicMock()
        return service
    
    @pytest.mark.asyncio
    async def test_create_idea(self, content_service):
        """Testa criação de ideia."""
        content_service.supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "idea-123",
                "title": "Test Idea",
                "status": "new",
                "created_at": datetime.utcnow().isoformat()
            }]
        )
        
        result = await content_service.create_idea(
            user_id="user-123",
            title="Test Idea"
        )
        
        assert result["title"] == "Test Idea"
        assert result["status"] == "new"


# ==========================================
# FINANCE SERVICE TESTS
# ==========================================

class TestFinanceService:
    """Testes para o FinanceService."""
    
    @pytest.fixture
    def finance_service(self):
        from app.services.finance_service import FinanceService
        service = FinanceService()
        service._supabase = MagicMock()
        return service
    
    @pytest.mark.asyncio
    async def test_quick_transaction(self, finance_service):
        """Testa transação rápida."""
        finance_service.supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "trans-123",
                "amount": 100.0,
                "type": "income",
                "description": "Test"
            }]
        )
        
        result = await finance_service.quick_transaction(
            user_id="user-123",
            amount=100.0,
            description="Test",
            transaction_type="income"
        )
        
        assert result["amount"] == 100.0
        assert result["type"] == "income"
    
    @pytest.mark.asyncio
    async def test_get_summary(self, finance_service):
        """Testa resumo financeiro."""
        # Mock para income
        finance_service.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.lte.return_value.execute.return_value = MagicMock(
            data=[{"amount": 1000.0}]
        )
        
        result = await finance_service.get_summary(
            user_id="user-123"
        )
        
        assert "total_income" in result
        assert "total_expense" in result
        assert "balance" in result


# ==========================================
# API ENDPOINTS TESTS
# ==========================================

class TestAPIEndpoints:
    """Testes básicos para endpoints da API."""
    
    @pytest.fixture
    def client(self):
        """Cria cliente de teste."""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    def test_api_root(self, client):
        """Testa endpoint raiz da API."""
        response = client.get("/api/v1/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
    
    def test_autonomy_levels_list(self, client):
        """Testa listagem de níveis de autonomia."""
        response = client.get("/api/v1/autonomy/levels")
        assert response.status_code == 200
        data = response.json()
        assert "levels" in data
        assert len(data["levels"]) == 5
    
    def test_memory_categories(self, client):
        """Testa listagem de categorias de memória."""
        response = client.get("/api/v1/memory/categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data


# ==========================================
# INTEGRATION TESTS
# ==========================================

class TestIntegration:
    """Testes de integração básicos."""
    
    def test_services_import(self):
        """Testa se todos os serviços podem ser importados."""
        from app.services.memory_service import memory_service
        from app.services.insights_service import insights_service
        from app.services.autonomy_service import autonomy_service
        from app.services.content_service import content_service
        from app.services.finance_service import finance_service
        from app.services.gmail_service import gmail_service
        from app.services.drive_service import drive_service
        
        assert memory_service is not None
        assert insights_service is not None
        assert autonomy_service is not None
        assert content_service is not None
        assert finance_service is not None
        assert gmail_service is not None
        assert drive_service is not None
    
    def test_api_routers_import(self):
        """Testa se todos os routers podem ser importados."""
        from app.api.v1.endpoints import (
            memory, insights, autonomy, content, finance, gmail, drive
        )
        
        assert memory.router is not None
        assert insights.router is not None
        assert autonomy.router is not None
        assert content.router is not None
        assert finance.router is not None
        assert gmail.router is not None
        assert drive.router is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
