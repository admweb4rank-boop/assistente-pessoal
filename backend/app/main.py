"""
TB Personal OS - Main Application
FastAPI Backend Entry Point
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import structlog
from contextlib import asynccontextmanager
import uuid

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.exceptions import AppError
from app.core.middleware import (
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.rate_limiting import limiter
from app.core.metrics import PrometheusMiddleware, get_metrics
from app.core.sentry import init_sentry, capture_exception
from app.api.v1 import api_router

# Setup logging
setup_logging()
logger = structlog.get_logger()

# Initialize Sentry for error monitoring
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting TB Personal OS", env=settings.APP_ENV)
    
    # Startup tasks
    # Initialize scheduler
    try:
        from app.services.scheduler_service import init_default_schedules
        init_default_schedules()
        logger.info("✅ Scheduler initialized")
    except Exception as e:
        logger.warning("⚠️ Scheduler initialization failed", error=str(e))
    
    yield
    
    # Shutdown tasks
    logger.info("👋 Shutting down TB Personal OS")
    
    # Stop scheduler
    try:
        from app.services.scheduler_service import scheduler_service
        scheduler_service.stop()
        logger.info("✅ Scheduler stopped")
    except Exception as e:
        logger.warning("⚠️ Scheduler stop failed", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Personal Operating System - Igor's AI Assistant",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Rate limiter state
app.state.limiter = limiter

# ===========================================
# MIDDLEWARE STACK (ordem importa!)
# ===========================================
# 0. Prometheus Metrics (mais externo - captura tudo)
app.add_middleware(PrometheusMiddleware)

# 1. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 2. Error Handling
app.add_middleware(ErrorHandlingMiddleware)

# 3. Request Logging
app.add_middleware(RequestLoggingMiddleware)

# 4. Correlation ID
app.add_middleware(CorrelationIdMiddleware)

# 5. CORS (mais interno junto com rotas)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================
# HEALTH CHECKS
# ===========================================
@app.get("/health")
async def health_check_simple():
    """
    Health check simples para load balancer.
    Retorna 200 se a aplicação está respondendo.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.APP_ENV,
    }


@app.get("/health/detailed")
async def health_check_detailed():
    """
    Health check detalhado com status de todos os componentes.
    Útil para debugging e monitoramento.
    """
    from app.core.health import health_service
    return await health_service.check_all(include_details=True)


@app.get("/health/ready")
async def readiness_check():
    """
    Readiness probe para Kubernetes/Docker.
    Verifica se a aplicação está pronta para receber tráfego.
    """
    from app.core.health import health_service, HealthStatus
    
    result = await health_service.check_all(include_details=False)
    
    if result["status"] == HealthStatus.UNHEALTHY:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "critical_components_failing"}
        )
    
    return {"status": "ready"}


@app.get("/health/live")
async def liveness_check():
    """
    Liveness probe para Kubernetes/Docker.
    Verifica se a aplicação está viva (não travada).
    """
    return {"status": "alive"}


# ===========================================
# PROMETHEUS METRICS
# ===========================================
@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """
    Endpoint para Prometheus scraping.
    Retorna métricas no formato OpenMetrics/Prometheus.
    """
    return get_metrics()


# ===========================================
# ROOT
# ===========================================
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TB Personal OS API",
        "docs": "/api/docs",
        "health": "/health",
        "health_detailed": "/health/detailed",
        "metrics": "/metrics",
    }


# ===========================================
# EXCEPTION HANDLERS
# ===========================================
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Handler para erros da aplicação."""
    correlation_id = getattr(request.state, "correlation_id", None)
    
    logger.warning(
        "app_error",
        error_code=exc.error_code,
        message=exc.message,
        correlation_id=correlation_id,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "correlation_id": correlation_id,
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler para erros não tratados."""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    # Send to Sentry
    capture_exception(exc, context={
        "correlation_id": correlation_id,
        "path": request.url.path,
        "method": request.method,
    })
    
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        correlation_id=correlation_id,
        path=request.url.path,
        exc_info=exc
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": str(exc) if settings.DEBUG else "An internal error occurred",
            "correlation_id": correlation_id,
        },
    )


# ===========================================
# API ROUTES
# ===========================================
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
