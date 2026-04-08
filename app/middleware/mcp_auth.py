"""MCP Authentication Middleware.

Extracts user tokens from HTTP headers and makes them available via ContextVar
to downstream MCP tool handlers.

Supports:
- X-User-Token header (preferred for Claude Desktop/Code config)
- Authorization: Bearer <token> header (standard OAuth2 style)
"""
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware

# ContextVar to store the user token for the current request
_user_token_var: ContextVar[str | None] = ContextVar("user_token", default=None)


def get_current_user_token() -> str | None:
    """Get the user token for the current request context.
    
    This should be called from within an MCP tool handler to access
the token provided by the client.
    
    Returns:
        The user token string, or None if not provided.
    """
    return _user_token_var.get()


class MCPAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to extract user tokens from incoming requests.
    
    Checks for tokens in:
    1. X-User-Token header (custom header for Motherbrain)
    2. Authorization: Bearer <token> header (standard OAuth2)
    
    The token is stored in a ContextVar and can be accessed via
    get_current_user_token() from anywhere in the request context.
    """
    
    async def dispatch(self, request, call_next):
        token = None
        
        # Method 1: X-User-Token header (preferred)
        token = request.headers.get("X-User-Token")
        
        # Method 2: Authorization: Bearer xxx header
        if not token:
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                token = auth[7:].strip()
        
        # Store in ContextVar for downstream access
        _user_token_var.set(token)
        
        # Continue processing the request
        response = await call_next(request)
        return response
