"""API key authentication."""

from functools import wraps

from flask import abort, request

from core.config import API_KEY


def require_api_key(handler):
    """Require X-API-Key header when API_KEY is configured."""

    @wraps(handler)
    def decorated(*args, **kwargs):
        if API_KEY and request.headers.get("X-API-Key") != API_KEY:
            abort(401, description="Invalid or missing API key")
        return handler(*args, **kwargs)

    return decorated
