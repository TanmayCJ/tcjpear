"""
History module for peargent.

Provides conversation history management with multiple storage backends.
"""

# Export base classes
from .base import Message, Thread, HistoryStore, FunctionalHistoryStore

# Export concrete implementations
from .session_buffer import InMemoryHistoryStore
from .file import FileHistoryStore

# Export storage type configuration classes
from .storage_types import StorageType, InMemory, File, Sqlite, Postgresql, Redis

# Export high-level interface
from .history import ConversationHistory

# Try to export SQL-based stores
try:
    from .postgresql import PostgreSQLHistoryStore
    __all_sql__ = ['PostgreSQLHistoryStore']
except ImportError:
    PostgreSQLHistoryStore = None
    __all_sql__ = []

try:
    from .sqlite import SQLiteHistoryStore
    __all_sql__ += ['SQLiteHistoryStore']
except ImportError:
    SQLiteHistoryStore = None

# Try to export Redis store
try:
    from .redis import RedisHistoryStore
    __all_redis__ = ['RedisHistoryStore']
except ImportError:
    RedisHistoryStore = None
    __all_redis__ = []

__all__ = [
    'Message',
    'Thread',
    'HistoryStore',
    'FunctionalHistoryStore',
    'InMemoryHistoryStore',
    'FileHistoryStore',
    'ConversationHistory',
    'StorageType',
    'InMemory',
    'File',
    'Sqlite',
    'Postgresql',
    'Redis',
] + __all_sql__ + __all_redis__
