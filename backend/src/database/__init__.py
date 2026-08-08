"""
Database module for Kisan Mitra persistent farmer memory.

Provides:
- SQLite database connection and initialization
- Farmer profile management
- Memory persistence across calls
"""

from .db import Database, get_database
from .farmer_repository import FarmerRepository

__all__ = ["Database", "get_database", "FarmerRepository"]
