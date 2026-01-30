"""
TB Personal OS - Health Check Service
Health checks detalhados para monitoramento
"""

import time
import asyncio
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class HealthStatus(str, Enum):
    """Status de saúde de um componente."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheckService:
    """
    Serviço de health check para todos os componentes.
    
    Verifica:
    - Supabase (database)
    - Redis (cache)
    - Gemini (IA)
    - Google APIs
    - Telegram Bot
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 30  # segundos
    
    async def check_all(self, include_details: bool = True) -> Dict[str, Any]:
        """
        Executa todos os health checks.
        
        Args:
            include_details: Se deve incluir detalhes de cada check
            
        Returns:
            Dict com status geral e de cada componente
        """
        start_time = time.perf_counter()
        
        # Executar checks em paralelo
        checks = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_gemini(),
            self.check_telegram(),
            return_exceptions=True
        )
        
        # Processar resultados
        results = {
            "database": self._process_result(checks[0]),
            "redis": self._process_result(checks[1]),
            "gemini": self._process_result(checks[2]),
            "telegram": self._process_result(checks[3])
        }
        
        # Calcular status geral
        statuses = [r["status"] for r in results.values()]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.DEGRADED
        
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        response = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": settings.APP_VERSION if hasattr(settings, 'APP_VERSION') else "1.0.0",
            "uptime_seconds": self._get_uptime(),
            "check_duration_ms": duration_ms
        }
        
        if include_details:
            response["components"] = results
        
        return response
    
    def _process_result(self, result: Any) -> Dict[str, Any]:
        """Processa resultado de um check, tratando exceções."""
        if isinstance(result, Exception):
            return {
                "status": HealthStatus.UNHEALTHY,
                "error": str(result),
                "latency_ms": None
            }
        return result
    
    async def check_database(self) -> Dict[str, Any]:
        """Verifica conexão com Supabase."""
        start_time = time.perf_counter()
        
        try:
            from supabase import create_client
            
            client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            
            # Query simples para testar
            result = client.table("users").select("id").limit(1).execute()
            
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            return {
                "status": HealthStatus.HEALTHY,
                "latency_ms": latency_ms,
                "details": {
                    "host": settings.SUPABASE_URL.split("//")[1].split(".")[0],
                    "connection": "ok"
                }
            }
            
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error("health_check_database_failed", error=str(e))
            
            return {
                "status": HealthStatus.UNHEALTHY,
                "latency_ms": latency_ms,
                "error": str(e)
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Verifica conexão com Redis."""
        start_time = time.perf_counter()
        
        try:
            import redis.asyncio as redis
            
            r = redis.from_url(settings.REDIS_URL)
            
            # Ping para testar
            await r.ping()
            
            # Obter info
            info = await r.info("memory")
            
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            await r.close()
            
            return {
                "status": HealthStatus.HEALTHY,
                "latency_ms": latency_ms,
                "details": {
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connection": "ok"
                }
            }
            
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning("health_check_redis_failed", error=str(e))
            
            # Redis não é crítico, marcar como degraded
            return {
                "status": HealthStatus.DEGRADED,
                "latency_ms": latency_ms,
                "error": str(e),
                "note": "Cache indisponível, sistema funcionando sem cache"
            }
    
    async def check_gemini(self) -> Dict[str, Any]:
        """Verifica conexão com Gemini API."""
        start_time = time.perf_counter()
        
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Listar modelos para testar conexão
            models = list(genai.list_models())
            
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            return {
                "status": HealthStatus.HEALTHY,
                "latency_ms": latency_ms,
                "details": {
                    "model": settings.GEMINI_MODEL,
                    "available_models": len(models)
                }
            }
            
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.warning("health_check_gemini_failed", error=str(e))
            
            return {
                "status": HealthStatus.DEGRADED,
                "latency_ms": latency_ms,
                "error": str(e),
                "note": "IA indisponível, usando fallbacks"
            }
    
    async def check_telegram(self) -> Dict[str, Any]:
        """Verifica conexão com Telegram Bot API."""
        start_time = time.perf_counter()
        
        try:
            import httpx
            
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5.0)
            
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": HealthStatus.HEALTHY,
                    "latency_ms": latency_ms,
                    "details": {
                        "bot_username": data.get("result", {}).get("username"),
                        "connection": "ok"
                    }
                }
            else:
                return {
                    "status": HealthStatus.UNHEALTHY,
                    "latency_ms": latency_ms,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error("health_check_telegram_failed", error=str(e))
            
            return {
                "status": HealthStatus.UNHEALTHY,
                "latency_ms": latency_ms,
                "error": str(e)
            }
    
    def _get_uptime(self) -> int:
        """Retorna uptime em segundos (simplificado)."""
        # Em produção, usar timestamp de início da aplicação
        return 0
    
    async def get_simple_status(self) -> Dict[str, Any]:
        """
        Retorna status simples para load balancer.
        
        Mais rápido que check_all, sem detalhes.
        """
        try:
            # Apenas verificar database (mais crítico)
            db_check = await self.check_database()
            
            if db_check["status"] == HealthStatus.UNHEALTHY:
                return {"status": "unhealthy"}
            
            return {"status": "healthy"}
            
        except Exception:
            return {"status": "unhealthy"}


# Singleton
health_service = HealthCheckService()
