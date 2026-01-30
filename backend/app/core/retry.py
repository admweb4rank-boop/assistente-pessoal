"""
TB Personal OS - Retry Utils
Padrão de retry com exponential backoff para integrações
"""

import asyncio
import functools
from typing import Callable, TypeVar, Any, Optional, Tuple, Type
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuração de retry."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
        non_retryable_exceptions: Tuple[Type[Exception], ...] = ()
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions
        self.non_retryable_exceptions = non_retryable_exceptions


# Configurações pré-definidas para diferentes integrações
RETRY_CONFIGS = {
    "google": RetryConfig(
        max_retries=3,
        base_delay=1.0,
        retryable_exceptions=(ConnectionError, TimeoutError),
    ),
    "gemini": RetryConfig(
        max_retries=2,
        base_delay=0.5,
        retryable_exceptions=(ConnectionError, TimeoutError),
    ),
    "telegram": RetryConfig(
        max_retries=3,
        base_delay=2.0,
        retryable_exceptions=(ConnectionError, TimeoutError),
    ),
    "supabase": RetryConfig(
        max_retries=2,
        base_delay=0.5,
        retryable_exceptions=(ConnectionError, TimeoutError),
    ),
    "default": RetryConfig(
        max_retries=3,
        base_delay=1.0,
    ),
}


def calculate_delay(
    attempt: int,
    config: RetryConfig,
    jitter: bool = True
) -> float:
    """
    Calcula delay para próxima tentativa usando exponential backoff.
    
    Args:
        attempt: Número da tentativa atual (0-indexed)
        config: Configuração de retry
        jitter: Se deve adicionar variação aleatória
        
    Returns:
        Delay em segundos
    """
    import random
    
    delay = config.base_delay * (config.exponential_base ** attempt)
    delay = min(delay, config.max_delay)
    
    if jitter:
        # Adiciona +/- 25% de variação
        jitter_range = delay * 0.25
        delay = delay + random.uniform(-jitter_range, jitter_range)
    
    return max(0, delay)


def with_retry(
    config: Optional[RetryConfig] = None,
    config_name: str = "default",
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator para adicionar retry a funções async.
    
    Args:
        config: Configuração customizada de retry
        config_name: Nome da configuração pré-definida
        on_retry: Callback chamado em cada retry
        
    Example:
        @with_retry(config_name="google")
        async def fetch_calendar_events():
            ...
    """
    
    retry_config = config or RETRY_CONFIGS.get(config_name, RETRY_CONFIGS["default"])
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(retry_config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except retry_config.non_retryable_exceptions as e:
                    # Não fazer retry para exceções não retryable
                    logger.error(
                        "non_retryable_exception",
                        function=func.__name__,
                        error=str(e)
                    )
                    raise
                    
                except retry_config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < retry_config.max_retries:
                        delay = calculate_delay(attempt, retry_config)
                        
                        logger.warning(
                            "retry_attempt",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=retry_config.max_retries,
                            delay_seconds=round(delay, 2),
                            error=str(e)
                        )
                        
                        if on_retry:
                            on_retry(e, attempt)
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "max_retries_exceeded",
                            function=func.__name__,
                            attempts=retry_config.max_retries + 1,
                            error=str(e)
                        )
            
            if last_exception:
                raise last_exception
        
        return wrapper
    
    return decorator


class CircuitBreaker:
    """
    Circuit breaker para proteger contra falhas cascateadas.
    
    Estados:
    - CLOSED: Funcionamento normal
    - OPEN: Circuito aberto, rejeita chamadas
    - HALF_OPEN: Permite chamada de teste
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = "closed"
    
    @property
    def state(self) -> str:
        """Retorna estado atual do circuit breaker."""
        if self._state == "open":
            # Verificar se é hora de testar
            if self._last_failure_time:
                elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self._state = "half_open"
        
        return self._state
    
    def record_success(self):
        """Registra chamada bem-sucedida."""
        self._failure_count = 0
        self._state = "closed"
    
    def record_failure(self):
        """Registra falha."""
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()
        
        if self._failure_count >= self.failure_threshold:
            self._state = "open"
            logger.warning(
                "circuit_breaker_opened",
                failure_count=self._failure_count,
                threshold=self.failure_threshold
            )
    
    def can_execute(self) -> bool:
        """Verifica se pode executar chamada."""
        return self.state != "open"
    
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Usa como decorator."""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if not self.can_execute():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker aberto para {func.__name__}"
                )
            
            try:
                result = await func(*args, **kwargs)
                self.record_success()
                return result
            except self.expected_exception as e:
                self.record_failure()
                raise
        
        return wrapper


class CircuitBreakerOpenError(Exception):
    """Exceção quando circuit breaker está aberto."""
    pass


# Circuit breakers pré-configurados por integração
circuit_breakers = {
    "google": CircuitBreaker(failure_threshold=5, recovery_timeout=60.0),
    "gemini": CircuitBreaker(failure_threshold=3, recovery_timeout=30.0),
    "telegram": CircuitBreaker(failure_threshold=5, recovery_timeout=60.0),
}


def get_circuit_breaker(integration: str) -> CircuitBreaker:
    """Obtém circuit breaker para uma integração."""
    return circuit_breakers.get(integration, CircuitBreaker())
