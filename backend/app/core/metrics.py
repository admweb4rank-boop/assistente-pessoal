"""
Prometheus Metrics Configuration
Provides observability metrics for the Igor Assistant API
"""
import time
from functools import wraps
from typing import Callable, Any

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# =============================================================================
# Application Info
# =============================================================================
APP_INFO = Info('igor_app', 'Igor Assistant Application Information')
APP_INFO.info({
    'version': '1.0.0',
    'environment': 'production',
    'service': 'igor-backend'
})

# =============================================================================
# HTTP Metrics
# =============================================================================

# Request counter
HTTP_REQUESTS_TOTAL = Counter(
    'igor_http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# Request latency histogram
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    'igor_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# Active requests gauge
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    'igor_http_requests_in_progress',
    'Number of HTTP requests currently being processed',
    ['method', 'endpoint']
)

# Request size histogram
HTTP_REQUEST_SIZE_BYTES = Histogram(
    'igor_http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000)
)

# Response size histogram
HTTP_RESPONSE_SIZE_BYTES = Histogram(
    'igor_http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000)
)

# =============================================================================
# Business Metrics
# =============================================================================

# Tasks metrics
TASKS_CREATED_TOTAL = Counter(
    'igor_tasks_created_total',
    'Total number of tasks created'
)

TASKS_COMPLETED_TOTAL = Counter(
    'igor_tasks_completed_total',
    'Total number of tasks completed'
)

TASKS_PENDING = Gauge(
    'igor_tasks_pending',
    'Number of pending tasks'
)

# Inbox metrics
INBOX_MESSAGES_TOTAL = Counter(
    'igor_inbox_messages_total',
    'Total number of inbox messages received',
    ['source']
)

INBOX_PROCESSED_TOTAL = Counter(
    'igor_inbox_processed_total',
    'Total number of inbox messages processed'
)

# Telegram metrics
TELEGRAM_MESSAGES_TOTAL = Counter(
    'igor_telegram_messages_total',
    'Total number of Telegram messages received',
    ['command']
)

TELEGRAM_RESPONSE_TIME = Histogram(
    'igor_telegram_response_time_seconds',
    'Telegram bot response time in seconds',
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# =============================================================================
# External Service Metrics
# =============================================================================

# Gemini AI metrics
GEMINI_REQUESTS_TOTAL = Counter(
    'igor_gemini_requests_total',
    'Total number of Gemini API requests',
    ['operation', 'status']
)

GEMINI_RESPONSE_TIME = Histogram(
    'igor_gemini_response_time_seconds',
    'Gemini API response time in seconds',
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
)

GEMINI_TOKENS_USED = Counter(
    'igor_gemini_tokens_total',
    'Total tokens used in Gemini requests',
    ['type']  # input, output
)

# Supabase metrics
SUPABASE_QUERIES_TOTAL = Counter(
    'igor_supabase_queries_total',
    'Total number of Supabase queries',
    ['table', 'operation', 'status']
)

SUPABASE_QUERY_DURATION = Histogram(
    'igor_supabase_query_duration_seconds',
    'Supabase query duration in seconds',
    ['table', 'operation'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# Redis metrics
REDIS_OPERATIONS_TOTAL = Counter(
    'igor_redis_operations_total',
    'Total number of Redis operations',
    ['operation', 'status']
)

REDIS_OPERATION_DURATION = Histogram(
    'igor_redis_operation_duration_seconds',
    'Redis operation duration in seconds',
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25)
)

# Google API metrics
GOOGLE_API_REQUESTS_TOTAL = Counter(
    'igor_google_api_requests_total',
    'Total number of Google API requests',
    ['service', 'operation', 'status']
)

GOOGLE_API_RESPONSE_TIME = Histogram(
    'igor_google_api_response_time_seconds',
    'Google API response time in seconds',
    ['service'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# =============================================================================
# Health Metrics
# =============================================================================

CHECKINS_TOTAL = Counter(
    'igor_checkins_total',
    'Total number of check-ins recorded',
    ['type']
)

HEALTH_SCORE = Gauge(
    'igor_health_score',
    'Current health score',
    ['user_id']
)

# =============================================================================
# System Metrics
# =============================================================================

SCHEDULER_JOBS_TOTAL = Counter(
    'igor_scheduler_jobs_total',
    'Total number of scheduled jobs executed',
    ['job_name', 'status']
)

SCHEDULER_JOB_DURATION = Histogram(
    'igor_scheduler_job_duration_seconds',
    'Scheduled job duration in seconds',
    ['job_name'],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0)
)

ERROR_TOTAL = Counter(
    'igor_errors_total',
    'Total number of errors',
    ['type', 'endpoint']
)

# =============================================================================
# Middleware
# =============================================================================

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method
        
        # Normalize endpoint path (remove IDs for grouping)
        path = request.url.path
        endpoint = self._normalize_path(path)
        
        # Skip metrics endpoint itself
        if endpoint == '/metrics':
            return await call_next(request)
        
        # Track request in progress
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
        
        # Track request size
        content_length = request.headers.get('content-length', 0)
        if content_length:
            HTTP_REQUEST_SIZE_BYTES.labels(method=method, endpoint=endpoint).observe(int(content_length))
        
        # Time the request
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            ERROR_TOTAL.labels(type=type(e).__name__, endpoint=endpoint).inc()
            raise
        finally:
            # Calculate duration
            duration = time.perf_counter() - start_time
            
            # Record metrics
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()
        
        # Track response size
        response_size = response.headers.get('content-length', 0)
        if response_size:
            HTTP_RESPONSE_SIZE_BYTES.labels(method=method, endpoint=endpoint).observe(int(response_size))
        
        return response
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path by replacing IDs with placeholders"""
        import re
        
        # Replace UUIDs
        path = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '{id}',
            path
        )
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        return path


# =============================================================================
# Decorators for Manual Instrumentation
# =============================================================================

def track_time(histogram: Histogram, labels: dict = None):
    """Decorator to track function execution time"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start_time
                if labels:
                    histogram.labels(**labels).observe(duration)
                else:
                    histogram.observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start_time
                if labels:
                    histogram.labels(**labels).observe(duration)
                else:
                    histogram.observe(duration)
        
        if asyncio_iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def asyncio_iscoroutinefunction(func):
    """Check if function is async"""
    import asyncio
    return asyncio.iscoroutinefunction(func)


# =============================================================================
# Metrics Endpoint
# =============================================================================

def get_metrics() -> Response:
    """Generate Prometheus metrics response"""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )
