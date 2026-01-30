"""
TB Personal OS - Testes da API Health
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4


class TestHealthAPI:
    """Testes dos endpoints de saúde."""
    
    @pytest.fixture
    def mock_auth(self, mocker, mock_user):
        """Mock da autenticação."""
        mocker.patch(
            "app.api.v1.dependencies.auth.get_current_user",
            return_value=mock_user
        )
        return mock_user
    
    @pytest.fixture
    def mock_health_service(self, mocker):
        """Mock do health service."""
        mock = mocker.MagicMock()
        mocker.patch(
            "app.api.v1.endpoints.health.health_service",
            mock
        )
        return mock
    
    # ==========================================
    # TESTES DE CHECK-INS
    # ==========================================
    
    def test_create_checkin_success(self, client, mock_auth, mock_health_service):
        """Deve criar check-in via API."""
        # Arrange
        mock_health_service.create_checkin = AsyncMock(return_value={
            "id": str(uuid4()),
            "checkin_type": "morning",
            "data": {"sleep_hours": 7.5}
        })
        
        # Act
        response = client.post(
            "/api/v1/health/checkins",
            json={
                "checkin_type": "morning",
                "data": {"sleep_hours": 7.5, "energy": 8}
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["checkin_type"] == "morning"
    
    def test_create_checkin_validation_error(self, client, mock_auth):
        """Deve rejeitar request inválido."""
        response = client.post(
            "/api/v1/health/checkins",
            json={"data": {}}  # Falta checkin_type
        )
        
        assert response.status_code == 422
    
    def test_list_checkins(self, client, mock_auth, mock_health_service):
        """Deve listar check-ins."""
        # Arrange
        mock_health_service.get_checkins = AsyncMock(return_value=[
            {"id": str(uuid4()), "checkin_type": "morning", "data": {}},
            {"id": str(uuid4()), "checkin_type": "evening", "data": {}}
        ])
        
        # Act
        response = client.get("/api/v1/health/checkins")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 2
    
    def test_get_checkin_streak(self, client, mock_auth, mock_health_service):
        """Deve retornar streak."""
        # Arrange
        mock_health_service.get_checkin_streak = AsyncMock(return_value={
            "current_streak": 5,
            "max_streak": 10,
            "total_checkins": 30
        })
        
        # Act
        response = client.get("/api/v1/health/checkins/streak")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["current_streak"] == 5
    
    # ==========================================
    # TESTES DE METAS
    # ==========================================
    
    def test_create_health_goal(self, client, mock_auth, mock_health_service):
        """Deve criar meta de saúde."""
        # Arrange
        mock_health_service.create_health_goal = AsyncMock(return_value={
            "id": str(uuid4()),
            "goal_type": "sleep",
            "target_value": 7.5,
            "unit": "hours"
        })
        
        # Act
        response = client.post(
            "/api/v1/health/goals",
            json={
                "goal_type": "sleep",
                "target_value": 7.5,
                "unit": "hours"
            }
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["goal_type"] == "sleep"
    
    def test_list_health_goals(self, client, mock_auth, mock_health_service):
        """Deve listar metas."""
        # Arrange
        mock_health_service.get_health_goals = AsyncMock(return_value=[
            {"id": str(uuid4()), "goal_type": "sleep", "target_value": 7.5}
        ])
        
        # Act
        response = client.get("/api/v1/health/goals")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
    
    def test_get_goal_progress(self, client, mock_auth, mock_health_service):
        """Deve retornar progresso da meta."""
        # Arrange
        goal_id = str(uuid4())
        mock_health_service.get_goal_progress = AsyncMock(return_value={
            "goal": {"id": goal_id, "target_value": 7.5},
            "progress_percentage": 85,
            "average_value": 6.4,
            "adherence_rate": 75
        })
        
        # Act
        response = client.get(f"/api/v1/health/goals/{goal_id}/progress")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["progress_percentage"] == 85
    
    # ==========================================
    # TESTES DE CORRELAÇÕES
    # ==========================================
    
    def test_list_correlations(self, client, mock_auth, mock_health_service):
        """Deve listar correlações."""
        # Arrange
        mock_health_service.get_correlations = AsyncMock(return_value=[
            {
                "metric_1": "sleep_hours",
                "metric_2": "productivity",
                "correlation_value": 0.75
            }
        ])
        
        # Act
        response = client.get("/api/v1/health/correlations")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["correlation_value"] == 0.75
    
    # ==========================================
    # TESTES DE TENDÊNCIAS
    # ==========================================
    
    def test_get_health_trend(self, client, mock_auth, mock_health_service):
        """Deve retornar tendência de métrica."""
        # Arrange
        mock_health_service.get_health_trends = AsyncMock(return_value={
            "metric": "energy",
            "trend": "improving",
            "average": 7.2,
            "data_points": 15
        })
        
        # Act
        response = client.get("/api/v1/health/trends/energy")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["trend"] == "improving"
    
    # ==========================================
    # TESTES DE RESUMO
    # ==========================================
    
    def test_get_health_summary(self, client, mock_auth, mock_health_service):
        """Deve retornar resumo completo."""
        # Arrange
        mock_health_service.get_health_summary = AsyncMock(return_value={
            "period_days": 7,
            "total_checkins": 14,
            "streak": {"current_streak": 5},
            "averages": {"sleep_hours": 7.2, "energy": 6.8},
            "insights": ["✅ Sono adequado"]
        })
        
        # Act
        response = client.get("/api/v1/health/summary")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 7
        assert "averages" in data
        assert "insights" in data
