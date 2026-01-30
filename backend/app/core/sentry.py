"""
Sentry Integration for Error Monitoring
Provides error tracking and performance monitoring
"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

import logging
from typing import Optional

from app.core.config import settings


def init_sentry(
    dsn: Optional[str] = None,
    environment: str = "development",
    release: str = "1.0.0",
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1
) -> None:
    """
    Initialize Sentry SDK for error tracking and performance monitoring.
    
    Args:
        dsn: Sentry DSN (Data Source Name). If not provided, uses SENTRY_DSN env var.
        environment: Environment name (development, staging, production)
        release: Application release version
        traces_sample_rate: Percentage of transactions to trace (0.0 to 1.0)
        profiles_sample_rate: Percentage of transactions to profile (0.0 to 1.0)
    """
    
    sentry_dsn = dsn or getattr(settings, 'SENTRY_DSN', None)
    
    if not sentry_dsn:
        logging.warning("Sentry DSN not configured. Error tracking disabled.")
        return
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        release=f"igor-assistant@{release}",
        
        # Performance monitoring
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        
        # Integrations
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
            RedisIntegration(),
            HttpxIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],
        
        # Additional settings
        send_default_pii=False,  # Don't send personally identifiable information
        attach_stacktrace=True,
        max_breadcrumbs=50,
        
        # Before send hook for filtering
        before_send=before_send_filter,
        before_send_transaction=before_send_transaction_filter,
    )
    
    logging.info(f"Sentry initialized for environment: {environment}")


def before_send_filter(event: dict, hint: dict) -> Optional[dict]:
    """
    Filter events before sending to Sentry.
    Use this to:
    - Filter out certain errors
    - Sanitize sensitive data
    - Add custom tags
    """
    
    # Don't send 404 errors
    if event.get('exception'):
        values = event['exception'].get('values', [])
        for value in values:
            if 'NotFound' in value.get('type', ''):
                return None
    
    # Sanitize sensitive data in request
    if 'request' in event:
        request = event['request']
        
        # Remove sensitive headers
        if 'headers' in request:
            sensitive_headers = ['authorization', 'x-api-key', 'cookie']
            request['headers'] = {
                k: '[FILTERED]' if k.lower() in sensitive_headers else v
                for k, v in request.get('headers', {}).items()
            }
        
        # Remove sensitive body fields
        if 'data' in request and isinstance(request['data'], dict):
            sensitive_fields = ['password', 'token', 'secret', 'api_key', 'access_token']
            request['data'] = {
                k: '[FILTERED]' if any(s in k.lower() for s in sensitive_fields) else v
                for k, v in request['data'].items()
            }
    
    return event


def before_send_transaction_filter(event: dict, hint: dict) -> Optional[dict]:
    """
    Filter transactions before sending to Sentry.
    Use this to filter out health checks and other noise.
    """
    
    transaction_name = event.get('transaction', '')
    
    # Don't track health check endpoints
    if '/health' in transaction_name or '/metrics' in transaction_name:
        return None
    
    return event


def capture_exception(error: Exception, extra: dict = None, tags: dict = None) -> str:
    """
    Manually capture an exception and send to Sentry.
    
    Args:
        error: The exception to capture
        extra: Additional context data
        tags: Tags for categorization
    
    Returns:
        Sentry event ID
    """
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)
        
        return sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", extra: dict = None, tags: dict = None) -> str:
    """
    Manually capture a message and send to Sentry.
    
    Args:
        message: The message to capture
        level: Log level (debug, info, warning, error, fatal)
        extra: Additional context data
        tags: Tags for categorization
    
    Returns:
        Sentry event ID
    """
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)
        
        return sentry_sdk.capture_message(message, level=level)


def set_user(user_id: str, email: str = None, username: str = None) -> None:
    """
    Set user context for Sentry events.
    
    Args:
        user_id: Unique user identifier
        email: User email (optional)
        username: Username (optional)
    """
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        "username": username
    })


def add_breadcrumb(
    message: str,
    category: str = "custom",
    level: str = "info",
    data: dict = None
) -> None:
    """
    Add a breadcrumb for debugging context.
    
    Args:
        message: Breadcrumb message
        category: Category for grouping
        level: Log level
        data: Additional data
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


class SentryContextManager:
    """Context manager for Sentry transaction tracking"""
    
    def __init__(self, name: str, op: str = "task"):
        self.name = name
        self.op = op
        self.transaction = None
    
    def __enter__(self):
        self.transaction = sentry_sdk.start_transaction(
            name=self.name,
            op=self.op
        )
        return self.transaction
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.transaction:
            if exc_type:
                self.transaction.set_status("internal_error")
            else:
                self.transaction.set_status("ok")
            self.transaction.finish()
