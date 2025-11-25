import logging
import uuid

from pda.utils.api_logging import APIRequestLog, get_request_log, set_request_log
from pda.utils.sentry import set_request_context, add_breadcrumb, start_transaction

logger = logging.getLogger(__name__)


def is_api_request(request) -> bool:
    """
    Check if the request is an API request.
    
    Args:
        request: Django HttpRequest object
    
    Returns:
        True if the request path starts with /api/, False otherwise
    """
    return request.path.startswith('/api/')


class CoreMiddleware:
    """
    Middleware for core functionalities like user authentication,
    session management, API request logging, and Sentry tracing.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Assign a random unique ID to the request for logging purposes
        request.id = uuid.uuid4()

        # Initialize Sentry transaction for API requests
        transaction = None
        if is_api_request(request):
            # Start Sentry transaction
            transaction = start_transaction(
                name=f"{request.method} {request.path}",
                op="http.server",
            )
            
            # Set Sentry context
            set_request_context(
                request_id=str(request.id),
                method=request.method,
                path=request.path,
            )
            
            # Create API request log
            api_log = APIRequestLog(request)
            set_request_log(request, api_log)
            
            # Add breadcrumb for request start
            add_breadcrumb(
                message=f"{request.method} {request.path}",
                category="http.request",
                level="info",
                data={
                    "method": request.method,
                    "path": request.path,
                    "request_id": str(request.id),
                },
            )
            
            logger.info(
                f"API Request: {request.method} {request.path} [Request ID: {request.id}]"
            )

        # Process the request
        try:
            response = self.get_response(request)
            status_code = getattr(response, 'status_code', None) if response else None
        except Exception as e:
            # If an exception occurs, still try to finalize logging
            status_code = 500
            response = None
            logger.error(
                f"API Exception: {request.method} {request.path} [Request ID: {request.id}]: {e}",
                exc_info=True,
            )
            raise
        finally:
            # Finalize API request logging and Sentry transaction
            if is_api_request(request) and transaction:
                # Finalize request log if available
                api_log = get_request_log(request)
                if api_log:
                    if status_code:
                        api_log.finalize(status_code)
                    else:
                        # If no status code available, mark as incomplete
                        api_log.status_code = None
                
                # Add breadcrumb for response
                if status_code:
                    add_breadcrumb(
                        message=f"Response: {status_code}",
                        category="http.response",
                        level="info" if status_code < 400 else "error",
                        data={
                            "status_code": status_code,
                            "request_id": str(request.id),
                        },
                    )
                
                # Finish Sentry transaction
                transaction.finish()
                
                if status_code:
                    logger.info(
                        f"API Response: {request.method} {request.path} -> {status_code} "
                        f"[Request ID: {request.id}]"
                    )

        return response
