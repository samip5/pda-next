import logging
import platform
import sys

from django.conf import settings
from django.http import JsonResponse
from rest_framework import status

from pda.utils.api_logging import get_request_log
from pda.utils.sentry import capture_exception, set_request_context

logger = logging.getLogger(__name__)

__all__ = (
    "handle_rest_api_exception",
)


def handle_rest_api_exception(request, *args, **kwargs):
    """
    Handle REST API exceptions with Sentry integration and request logging.
    
    Args:
        request: Django HttpRequest object
        *args: Additional positional arguments
        **kwargs: Additional keyword arguments
    
    Returns:
        JsonResponse with error details and request log
    """
    type_, error, traceback = sys.exc_info()
    
    # Capture exception in Sentry
    if error:
        # Set additional context for Sentry
        set_request_context(
            request_id=str(getattr(request, 'id', None)),
            method=getattr(request, 'method', 'UNKNOWN'),
            path=getattr(request, 'path', 'UNKNOWN'),
        )
        
        # Capture exception with traceback
        event_id = capture_exception(error)
        logger.error(
            f"API Exception: {type_.__name__}: {error} [Sentry Event ID: {event_id}]",
            exc_info=True,
        )
    
    # Build error response data
    data = {
        "error": str(error) if error else "Unknown error",
        "exception": type_.__name__ if type_ else "UnknownException",
        "python_version": platform.python_version(),
    }
    
    # Add version if available
    if hasattr(settings, 'PDA_VERSION'):
        data["pda_version"] = settings.PDA_VERSION
    
    # Include request log if available
    request_log = get_request_log(request)
    if request_log:
        request_log.finalize(status.HTTP_500_INTERNAL_SERVER_ERROR)
        data["request_log"] = request_log.to_dict()
    
    return JsonResponse(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)