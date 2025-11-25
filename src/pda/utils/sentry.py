import logging
import sys
from typing import Any, Dict, Optional

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.tracing import Transaction

logger = logging.getLogger(__name__)


def configure_sentry(
    dsn: str,
    environment: Optional[str] = None,
    release: Optional[str] = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
    send_default_pii: bool = False,
    before_send=None,
) -> None:
    """
    Configure Sentry SDK with best practices for Django applications.
    
    Args:
        dsn: Sentry DSN
        environment: Environment name (e.g., 'production', 'staging', 'development')
        release: Release version
        traces_sample_rate: Sample rate for performance monitoring (0.0 to 1.0)
        profiles_sample_rate: Sample rate for profiling (0.0 to 1.0)
        send_default_pii: Whether to send personally identifiable information
        before_send: Optional callback to filter/modify events before sending
    """
    if not dsn or not dsn.strip():
        logger.warning("Sentry DSN not provided, skipping Sentry initialization")
        return

    integrations = [
        DjangoIntegration(
            transaction_style='url',
            middleware_spans=True,
            signals_spans=True,
            cache_spans=True,
        ),
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        ),
    ]

    # Add Celery integration if available
    try:
        integrations.append(CeleryIntegration())
    except ImportError:
        pass

    # Add Redis integration if available
    try:
        integrations.append(RedisIntegration())
    except ImportError:
        pass

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        integrations=integrations,
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        send_default_pii=send_default_pii,
        before_send=before_send,
        # Performance monitoring
        enable_tracing=True,
        # Additional options
        max_breadcrumbs=50,
        attach_stacktrace=True,
        # Ignore common exceptions
        ignore_errors=[
            KeyboardInterrupt,
            SystemExit,
        ],
    )

    logger.info("Sentry initialized successfully")


def set_user_context(user_id: Optional[str] = None, username: Optional[str] = None, email: Optional[str] = None) -> None:
    """
    Set user context for Sentry events.
    
    Args:
        user_id: User ID
        username: Username
        email: User email
    """
    sentry_sdk.set_user({
        "id": user_id,
        "username": username,
        "email": email,
    })


def set_request_context(request_id: Optional[str] = None, **kwargs) -> None:
    """
    Set additional context for the current request.
    
    Args:
        request_id: Unique request identifier
        **kwargs: Additional context key-value pairs
    """
    if request_id:
        sentry_sdk.set_tag("request_id", request_id)
    
    for key, value in kwargs.items():
        sentry_sdk.set_tag(key, value)


def start_transaction(name: str, op: str = "http.server") -> Transaction:
    """
    Start a Sentry transaction for tracing.
    
    Args:
        name: Transaction name (e.g., endpoint path)
        op: Operation type (default: "http.server")
    
    Returns:
        Sentry Transaction object
    """
    transaction = sentry_sdk.start_transaction(
        name=name,
        op=op,
    )
    return transaction


def add_breadcrumb(message: str, category: str = "default", level: str = "info", data: Optional[Dict[str, Any]] = None) -> None:
    """
    Add a breadcrumb to the current Sentry scope.
    
    Args:
        message: Breadcrumb message
        category: Breadcrumb category
        level: Breadcrumb level (debug, info, warning, error, fatal)
        data: Additional data to include
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )


def capture_exception(exception: Exception, **kwargs) -> Optional[str]:
    """
    Capture an exception and send it to Sentry.
    
    Args:
        exception: Exception to capture
        **kwargs: Additional context
    
    Returns:
        Event ID if event was sent, None otherwise
    """
    return sentry_sdk.capture_exception(exception, **kwargs)


def capture_message(message: str, level: str = "info", **kwargs) -> Optional[str]:
    """
    Capture a message and send it to Sentry.
    
    Args:
        message: Message to capture
        level: Message level (debug, info, warning, error, fatal)
        **kwargs: Additional context
    
    Returns:
        Event ID if event was sent, None otherwise
    """
    return sentry_sdk.capture_message(message, level=level, **kwargs)

