import json
from rest_framework.renderers import JSONRenderer
from pda.utils.api_logging import get_request_log


class APIRequestLogRenderer(JSONRenderer):
    """
    Custom JSON renderer that includes request log information in API error responses.
    
    The request log is included in a 'request_log' field only for error responses (4xx, 5xx).
    Successful responses (2xx, 3xx) are returned without the request log to keep them clean.
    """
    media_type = 'application/json'
    format = 'json'
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render data into JSON, including request log information for error responses only.
        
        Args:
            data: Response data to render
            accepted_media_type: Accepted media type
            renderer_context: Context dictionary containing request, response, etc.
        
        Returns:
            JSON-encoded string with request log included (only for errors)
        """
        if renderer_context is None:
            renderer_context = {}
        
        request = renderer_context.get('request')
        response = renderer_context.get('response')
        
        request_log = None
        if request and response:
            status_code = getattr(response, 'status_code', None)
            
            # Only add request log for error status codes
            if status_code and status_code >= 400:
                request_log_obj = get_request_log(request)
                if request_log_obj:
                    request_log_obj.finalize(status_code)
                    request_log = request_log_obj.to_dict()
        
        if request_log:
            if isinstance(data, dict):
                wrapped_data = {
                    **data,
                    'request_log': request_log,
                }
            else:
                wrapped_data = {
                    'data': data,
                    'request_log': request_log,
                }
        else:
            wrapped_data = data
        
        # Render to JSON
        return json.dumps(
            wrapped_data,
            cls=self.encoder_class,
            ensure_ascii=self.ensure_ascii,
            allow_nan=not self.strict,
            indent=self.get_indent(accepted_media_type, renderer_context),
        ).encode('utf-8')

