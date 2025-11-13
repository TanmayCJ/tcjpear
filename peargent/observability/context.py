import threading
from typing import Optional

_context = threading.local()

def set_session_id(session_id: str) -> None:
    """Set global session ID for all traces."""
    _context.session_id = session_id

def set_user_id(user_id: str) -> None:
    """Set global user ID for all traces."""
    _context.user_id = user_id

def get_session_id() -> Optional[str]:
    """Get current session ID."""
    return getattr(_context, 'session_id', None)

def get_user_id() -> Optional[str]:
    """Get current user ID."""
    return getattr(_context, 'user_id', None)

def clear_context() -> None:
    """Clear all context."""
    _context.session_id = None
    _context.user_id = None