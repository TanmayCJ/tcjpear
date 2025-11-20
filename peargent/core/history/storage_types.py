"""
Storage type configuration classes for history management.

These classes encapsulate the configuration for different storage backends
and provide a more structured API for creating history instances.
"""

from typing import Optional


class StorageType:
    """Base class for storage type configurations."""
    pass


class InMemory(StorageType):
    """Configuration for in-memory storage."""

    def __init__(self):
        """Initialize in-memory storage configuration (no parameters needed)."""
        pass


class File(StorageType):
    """Configuration for file-based storage."""
    
    def __init__(self, storage_dir: str = ".peargent_history"):
        """
        Initialize file storage configuration.
        
        Args:
            storage_dir: Directory to store history files (default: ".peargent_history")
        """
        self.storage_dir = storage_dir


class Sqlite(StorageType):
    """Configuration for SQLite storage."""
    
    def __init__(self, database_path: str = "peargent_history.db", table_prefix: str = "peargent"):
        """
        Initialize SQLite storage configuration.
        
        Args:
            database_path: Path to SQLite database file (default: "peargent_history.db")
            table_prefix: Prefix for table names (default: "peargent")
        """
        self.database_path = database_path
        self.table_prefix = table_prefix


class Postgresql(StorageType):
    """Configuration for PostgreSQL storage."""
    
    def __init__(self, connection_string: str, table_prefix: str = "peargent"):
        """
        Initialize PostgreSQL storage configuration.
        
        Args:
            connection_string: PostgreSQL connection string
                              (e.g., "postgresql://user:pass@localhost/dbname")
            table_prefix: Prefix for table names (default: "peargent")
        """
        self.connection_string = connection_string
        self.table_prefix = table_prefix


class Redis(StorageType):
    """Configuration for Redis storage."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, 
                 password: Optional[str] = None, key_prefix: str = "peargent"):
        """
        Initialize Redis storage configuration.
        
        Args:
            host: Redis server host (default: "localhost")
            port: Redis server port (default: 6379)
            db: Redis database number (default: 0)
            password: Redis password (default: None)
            key_prefix: Prefix for Redis keys (default: "peargent")
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.key_prefix = key_prefix