from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Return a consistent {'error': ...} shape for all API errors.

    - Single 'detail' errors (auth failures, throttle) flatten to {'error': 'msg'}.
    - Validation errors wrap the field dict: {'error': {'email': ['...']}}.
    """
    response = exception_handler(exc, context)
    if response is None:
        return None
    data = response.data
    if isinstance(data, dict) and list(data.keys()) == ['detail']:
        response.data = {'error': data['detail']}
    else:
        response.data = {'error': data}
    return response
