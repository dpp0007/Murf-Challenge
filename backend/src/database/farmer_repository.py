"""
Farmer repository for database operations.

Handles all CRUD operations for farmer profiles and memory.
Provides clean abstraction over SQLite queries.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from .db import get_database

logger = logging.getLogger("farmer_repository")


class FarmerProfile:
    """Data class for farmer information."""
    
    def __init__(
        self,
        user_id: str,
        name: Optional[str] = None,
        language_preference: str = "hi",
        crops_grown: Optional[str] = None,
        land_size: Optional[str] = None,
        district: Optional[str] = None,
        irrigation_type: Optional[str] = None,
        last_interaction: Optional[str] = None,
    ):
        self.user_id = user_id
        self.name = name
        self.language_preference = language_preference
        self.crops_grown = crops_grown
        self.land_size = land_size
        self.district = district
        self.irrigation_type = irrigation_type
        self.last_interaction = last_interaction
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "language_preference": self.language_preference,
            "crops_grown": self.crops_grown,
            "land_size": self.land_size,
            "district": self.district,
            "irrigation_type": self.irrigation_type,
            "last_interaction": self.last_interaction,
        }


class FarmerRepository:
    """
    Repository for farmer profile database operations.
    
    All methods handle None/empty values gracefully.
    Safe for concurrent access.
    """
    
    def __init__(self):
        """Initialize repository with database connection."""
        self.db = get_database()
    
    def _get_utc_timestamp(self) -> str:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc).isoformat()
    
    def lookup_farmer(self, user_id: str) -> Optional[FarmerProfile]:
        """
        Look up a farmer by user_id.
        
        Args:
            user_id: Unique identifier for the farmer
            
        Returns:
            FarmerProfile if found, None otherwise
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get user info
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_row = cursor.fetchone()
            
            if not user_row:
                conn.close()
                return None
            
            # Get farmer profile
            cursor.execute("SELECT * FROM farmer_profiles WHERE user_id = ?", (user_id,))
            profile_row = cursor.fetchone()
            
            conn.close()
            
            # Build farmer profile
            profile = FarmerProfile(
                user_id=user_id,
                name=user_row["name"],
                language_preference=user_row["language_preference"],
                last_interaction=user_row["last_interaction"],
            )
            
            if profile_row:
                profile.crops_grown = profile_row["crops_grown"]
                profile.land_size = profile_row["land_size"]
                profile.district = profile_row["district"]
                profile.irrigation_type = profile_row["irrigation_type"]
            
            logger.info(f"Found farmer profile for {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error looking up farmer {user_id}: {e}")
            return None
    
    def farmer_exists(self, user_id: str) -> bool:
        """Check if farmer exists."""
        return self.lookup_farmer(user_id) is not None
    
    def create_farmer(self, user_id: str, language_preference: str = "hi") -> bool:
        """
        Create a new farmer record.
        
        Args:
            user_id: Unique identifier for the farmer
            language_preference: Preferred language (hi/en)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            timestamp = self._get_utc_timestamp()
            
            # Create user record
            cursor.execute(
                """INSERT INTO users (user_id, language_preference, created_at, last_interaction)
                   VALUES (?, ?, ?, ?)""",
                (user_id, language_preference, timestamp, timestamp)
            )
            
            # Create farmer profile record
            cursor.execute(
                """INSERT INTO farmer_profiles (user_id, created_at, updated_at)
                   VALUES (?, ?, ?)""",
                (user_id, timestamp, timestamp)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created new farmer profile for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating farmer {user_id}: {e}")
            return False
    
    def save_farmer_memory(
        self,
        user_id: str,
        name: Optional[str] = None,
        language_preference: Optional[str] = None,
        crops_grown: Optional[str] = None,
        land_size: Optional[str] = None,
        district: Optional[str] = None,
        irrigation_type: Optional[str] = None,
    ) -> bool:
        """
        Save or update farmer memory.
        
        Only updates non-None values.
        Preserves existing facts when updating.
        Creates farmer if doesn't exist.
        
        Args:
            user_id: Unique identifier for the farmer
            name: Farmer's name
            language_preference: Preferred language
            crops_grown: Crops the farmer grows
            land_size: Size of land
            district: District/region
            irrigation_type: Type of irrigation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if farmer exists
            if not self.farmer_exists(user_id):
                conn.close()
                # Create farmer with default values
                if not self.create_farmer(user_id, language_preference or "hi"):
                    return False
                conn = self.db.get_connection()
                cursor = conn.cursor()
            
            timestamp = self._get_utc_timestamp()
            
            # Update users table
            if name is not None or language_preference is not None:
                updates = []
                values = []
                
                if name is not None:
                    updates.append("name = ?")
                    values.append(name)
                
                if language_preference is not None:
                    updates.append("language_preference = ?")
                    values.append(language_preference)
                
                updates.append("last_interaction = ?")
                values.append(timestamp)
                values.append(user_id)
                
                if updates:
                    query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
                    cursor.execute(query, values)
            else:
                # At minimum, update last_interaction
                cursor.execute(
                    "UPDATE users SET last_interaction = ? WHERE user_id = ?",
                    (timestamp, user_id)
                )
            
            # Update farmer_profiles table
            if any([crops_grown, land_size, district, irrigation_type]):
                updates = []
                values = []
                
                if crops_grown is not None:
                    updates.append("crops_grown = ?")
                    values.append(crops_grown)
                
                if land_size is not None:
                    updates.append("land_size = ?")
                    values.append(land_size)
                
                if district is not None:
                    updates.append("district = ?")
                    values.append(district)
                
                if irrigation_type is not None:
                    updates.append("irrigation_type = ?")
                    values.append(irrigation_type)
                
                updates.append("updated_at = ?")
                values.append(timestamp)
                values.append(user_id)
                
                if updates:
                    query = f"UPDATE farmer_profiles SET {', '.join(updates)} WHERE user_id = ?"
                    cursor.execute(query, values)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated farmer memory for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving farmer memory {user_id}: {e}")
            return False


# Global repository instance
_repository_instance: Optional[FarmerRepository] = None


def get_farmer_repository() -> FarmerRepository:
    """
    Get or create the global farmer repository instance.
    
    Returns:
        FarmerRepository instance
    """
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = FarmerRepository()
    return _repository_instance
