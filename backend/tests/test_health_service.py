"""
TB Personal OS - Testes do Health Service
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock, patch


class TestHealthService:
    """Testes para HealthService."""
    
    @pytest.fixture
    def health_service(self, mock_supabase):
        """Fixture do health service com mocks."""
        from app.services.health_service import HealthService
        
        service = HealthService()
        service.supabase = mock_supabase
        return service
    
    @pytest.fixture
    def mock_checkins_data(self, mock_user_id):
        """Dados de checkins para testes."""
        base_date = datetime.utcnow().date()
        
        return [
            {
                "id": str(uuid4()),
                "user_id": mock_user_id,
                "checkin_type": "morning",
                "checkin_date": (base_date - timedelta(days=i)).isoformat(),
                "data": {
                    "sleep_hours": 7 + (i % 3) * 0.5,
                    "energy": 6 + (i % 4),
                    "mood": 7 + (i % 3)
                },
                "created_at": datetime.utcnow().isoformat()
            }
            for i in range(10)
        ]
    
    # ==========================================
    # TESTES DE CHECK-INS
    # ==========================================
    
    @pytest.mark.asyncio
    async def test_create_checkin_success(self, health_service, mock_user_id, mock_supabase):
        """Deve criar check-in com sucesso."""
        # Arrange
        checkin_type = "morning"
        data = {"sleep_hours": 7.5, "energy": 8}
        
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{
            "id": str(uuid4()),
            "user_id": mock_user_id,
            "checkin_type": checkin_type,
            "data": data
        }]
        
        # Mock get_checkins para correlações
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
        
        # Act
        result = await health_service.create_checkin(
            user_id=mock_user_id,
            checkin_type=checkin_type,
            data=data
        )
        
        # Assert
        assert result is not None
        assert result["checkin_type"] == checkin_type
    
    @pytest.mark.asyncio
    async def test_create_checkin_invalid_type(self, health_service, mock_user_id):
        """Deve rejeitar tipo de check-in inválido."""
        from app.core.exceptions import ValidationError
        
        with pytest.raises(ValidationError):
            await health_service.create_checkin(
                user_id=mock_user_id,
                checkin_type="invalid_type",
                data={"test": 1}
            )
    
    @pytest.mark.asyncio
    async def test_get_checkins_empty(self, health_service, mock_user_id, mock_supabase):
        """Deve retornar lista vazia quando não há check-ins."""
        # Arrange
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
        
        # Act
        result = await health_service.get_checkins(user_id=mock_user_id)
        
        # Assert
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_checkins_with_filter(self, health_service, mock_user_id, mock_supabase, mock_checkins_data):
        """Deve filtrar check-ins por tipo."""
        # Arrange
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = mock_checkins_data
        
        # Act
        result = await health_service.get_checkins(
            user_id=mock_user_id,
            checkin_type="morning"
        )
        
        # Assert
        assert len(result) > 0
        assert all(c["checkin_type"] == "morning" for c in result)
    
    # ==========================================
    # TESTES DE STREAK
    # ==========================================
    
    @pytest.mark.asyncio
    async def test_get_streak_with_consecutive_days(self, health_service, mock_user_id, mock_supabase):
        """Deve calcular streak corretamente."""
        # Arrange - 5 dias consecutivos
        base_date = datetime.utcnow().date()
        consecutive_checkins = [
            {
                "id": str(uuid4()),
                "checkin_type": "morning",
                "checkin_date": (base_date - timedelta(days=i)).isoformat(),
                "data": {}
            }
            for i in range(5)
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = consecutive_checkins
        
        # Act
        result = await health_service.get_checkin_streak(
            user_id=mock_user_id,
            checkin_type="morning"
        )
        
        # Assert
        assert result["current_streak"] == 5
        assert result["total_checkins"] == 5
    
    @pytest.mark.asyncio
    async def test_get_streak_with_gap(self, health_service, mock_user_id, mock_supabase):
        """Streak deve quebrar com gap."""
        # Arrange - gap no dia 2
        base_date = datetime.utcnow().date()
        checkins_with_gap = [
            {"checkin_date": base_date.isoformat(), "checkin_type": "morning", "data": {}},
            {"checkin_date": (base_date - timedelta(days=1)).isoformat(), "checkin_type": "morning", "data": {}},
            # Gap no dia 2
            {"checkin_date": (base_date - timedelta(days=3)).isoformat(), "checkin_type": "morning", "data": {}},
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = checkins_with_gap
        
        # Act
        result = await health_service.get_checkin_streak(
            user_id=mock_user_id,
            checkin_type="morning"
        )
        
        # Assert
        assert result["current_streak"] == 2  # Apenas os 2 primeiros
    
    # ==========================================
    # TESTES DE METAS
    # ==========================================
    
    @pytest.mark.asyncio
    async def test_create_health_goal(self, health_service, mock_user_id, mock_supabase):
        """Deve criar meta de saúde."""
        # Arrange
        goal_data = {
            "id": str(uuid4()),
            "user_id": mock_user_id,
            "goal_type": "sleep",
            "target_value": 7.5,
            "unit": "hours"
        }
        
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [goal_data]
        
        # Act
        result = await health_service.create_health_goal(
            user_id=mock_user_id,
            goal_type="sleep",
            target_value=7.5,
            unit="hours"
        )
        
        # Assert
        assert result["goal_type"] == "sleep"
        assert result["target_value"] == 7.5
    
    @pytest.mark.asyncio
    async def test_get_health_goals(self, health_service, mock_user_id, mock_supabase):
        """Deve listar metas ativas."""
        # Arrange
        goals = [
            {"id": str(uuid4()), "goal_type": "sleep", "target_value": 7.5, "is_active": True},
            {"id": str(uuid4()), "goal_type": "exercise", "target_value": 30, "is_active": True}
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = goals
        
        # Act
        result = await health_service.get_health_goals(user_id=mock_user_id)
        
        # Assert
        assert len(result) == 2
    
    # ==========================================
    # TESTES DE CORRELAÇÃO
    # ==========================================
    
    def test_pearson_correlation_positive(self, health_service):
        """Deve calcular correlação positiva."""
        series1 = {"d1": 5, "d2": 6, "d3": 7, "d4": 8, "d5": 9}
        series2 = {"d1": 3, "d2": 4, "d3": 5, "d4": 6, "d5": 7}
        
        corr = health_service._pearson_correlation(series1, series2)
        
        assert corr is not None
        assert corr > 0.9  # Correlação forte positiva
    
    def test_pearson_correlation_negative(self, health_service):
        """Deve calcular correlação negativa."""
        series1 = {"d1": 9, "d2": 8, "d3": 7, "d4": 6, "d5": 5}
        series2 = {"d1": 1, "d2": 2, "d3": 3, "d4": 4, "d5": 5}
        
        corr = health_service._pearson_correlation(series1, series2)
        
        assert corr is not None
        assert corr < -0.9  # Correlação forte negativa
    
    def test_pearson_correlation_insufficient_data(self, health_service):
        """Deve retornar None com dados insuficientes."""
        series1 = {"d1": 5, "d2": 6}  # Apenas 2 pontos
        series2 = {"d1": 3, "d2": 4, "d3": 5}
        
        corr = health_service._pearson_correlation(series1, series2)
        
        assert corr is None  # Precisa de pelo menos 5 pontos comuns
    
    # ==========================================
    # TESTES DE TENDÊNCIAS
    # ==========================================
    
    @pytest.mark.asyncio
    async def test_get_trends_improving(self, health_service, mock_user_id, mock_supabase):
        """Deve identificar tendência de melhora."""
        # Arrange - valores crescentes
        base_date = datetime.utcnow().date()
        checkins = [
            {"checkin_date": (base_date - timedelta(days=6-i)).isoformat(), "data": {"energy": 4 + i}}
            for i in range(7)
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.gte.return_value.order.return_value.limit.return_value.execute.return_value.data = checkins
        
        # Act
        result = await health_service.get_health_trends(
            user_id=mock_user_id,
            metric="energy",
            period_days=7
        )
        
        # Assert
        assert result["trend"] == "improving"
    
    # ==========================================
    # TESTES DE RESUMO
    # ==========================================
    
    @pytest.mark.asyncio
    async def test_get_health_summary(self, health_service, mock_user_id, mock_supabase, mock_checkins_data):
        """Deve gerar resumo completo."""
        # Arrange
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = mock_checkins_data
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []  # goals
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []  # correlations
        
        # Act
        result = await health_service.get_health_summary(
            user_id=mock_user_id,
            period_days=7
        )
        
        # Assert
        assert "streak" in result
        assert "averages" in result
        assert "insights" in result
        assert result["period_days"] == 7
    
    def test_generate_health_insights_low_sleep(self, health_service):
        """Deve gerar insight para sono baixo."""
        averages = {"sleep_hours": 5.5, "energy": 6}
        correlations = []
        
        insights = health_service._generate_health_insights(averages, correlations)
        
        assert any("sono" in i.lower() for i in insights)
    
    def test_generate_health_insights_good_energy(self, health_service):
        """Deve gerar insight positivo para boa energia."""
        averages = {"energy": 8}
        correlations = []
        
        insights = health_service._generate_health_insights(averages, correlations)
        
        assert any("energia" in i.lower() for i in insights)
