from rest_framework.response import Response


def error_response(message, status_code):
    """
    Helper to return error responses in consistent format.

    Args:
        message (str or dict): Error message or dict of errors.
        status_code (int): HTTP status code.

    Returns:
        Response: DRF Response with given message and status.
    """
    if isinstance(message, str):
        data = {"detail": message}
    else:
        data = message
    return Response(data, status=status_code)
