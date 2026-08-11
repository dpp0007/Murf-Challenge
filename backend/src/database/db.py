"""
SQLite database initialization and connection management for Kisan Mitra.

Handles:
- Database connection lifecycle
- Schema initialization
- Connection pooling and safety
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger("database")


class Database:
    """
    Manages SQLite database connection and schema initialization.
    
    Safe for multiple concurrent calls.
    Automatically creates database and tables on first run.
    """
    
    def __init__(self, db_path: str = "data/kisan_mitra.db"):
        """
        Initialize database.
        
        Args:
            db_path: Path to SQLite database file (relative to backend root)
        """
        self.db_path = Path(db_path)
        self._ensure_db_directory()
        self._initialized = False
    
    def _ensure_db_directory(self):
        """Create data directory if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Database directory ready: {self.db_path.parent.absolute()}")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a new database connection.
        
        Returns:
            sqlite3.Connection configured with safe defaults
        """
        conn = sqlite3.connect(str(self.db_path))
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        # Return Row objects for dict-like access
        conn.row_factory = sqlite3.Row
        return conn
    
    def initialize(self):
        """
        Initialize database schema.
        
        Safe to call multiple times - uses CREATE TABLE IF NOT EXISTS.
        Creates all required tables and indexes.
        """
        if self._initialized:
            return
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    name TEXT,
                    language_preference TEXT DEFAULT 'hi',
                    outbound_calls_enabled INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_interaction TEXT NOT NULL
                )
            """)
            
            # Create farmer_profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS farmer_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    crops_grown TEXT,
                    land_size TEXT,
                    district TEXT,
                    irrigation_type TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_farmer_profiles_user_id ON farmer_profiles(user_id)
            """)
            
            # Migration: Add outbound_calls_enabled to existing users table
            try:
                cursor.execute("SELECT outbound_calls_enabled FROM users LIMIT 1")
            except sqlite3.OperationalError:
                # Column doesn't exist, add it
                logger.info("Migrating database: adding outbound_calls_enabled column")
                cursor.execute("""
                    ALTER TABLE users ADD COLUMN outbound_calls_enabled INTEGER DEFAULT 1
                """)
                conn.commit()
                logger.info("Migration complete: outbound_calls_enabled added")
            
            # Create escalations table for human-in-the-loop requests
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS escalations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reference_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    farmer_name TEXT NOT NULL,
                    district TEXT,
                    reason TEXT NOT NULL,
                    original_question TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    what_agent_checked TEXT,
                    urgency TEXT DEFAULT 'MEDIUM',
                    language TEXT DEFAULT 'hi',
                    preferred_followup TEXT DEFAULT 'phone',
                    status TEXT DEFAULT 'OPEN',
                    human_answer TEXT,
                    resolution_notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    resolved_at TEXT,
                    callback_status TEXT DEFAULT 'NOT_STARTED',
                    callback_attempts INTEGER DEFAULT 0,
                    callback_started_at TEXT,
                    callback_connected_at TEXT,
                    callback_completed_at TEXT,
                    callback_error TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for escalations
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_escalations_user_id ON escalations(user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_escalations_reference_id ON escalations(reference_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_escalations_status ON escalations(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_escalations_callback_status ON escalations(callback_status)
            """)
            
            conn.commit()
            conn.close()
            
            self._initialized = True
            logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def close(self):
        """Close any open connections (for cleanup if needed)."""
        # SQLite doesn't require explicit cleanup, but this is here for API consistency
        pass


# Global database instance
_database_instance: Optional[Database] = None


def get_database(db_path: str = "data/kisan_mitra.db") -> Database:
    """
    Get or create the global database instance.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        Database instance
    """
    global _database_instance
    if _database_instance is None:
        _database_instance = Database(db_path)
        _database_instance.initialize()
    return _database_instance
