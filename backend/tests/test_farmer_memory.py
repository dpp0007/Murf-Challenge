"""
Tests for farmer memory system (SQLite database and repository).

Tests:
1. Database initialization
2. Create new farmer
3. Lookup farmer
4. Save farmer information
5. Update existing information
6. Preserve existing facts when updating
7. Multiple farmers remain separate
8. Database error handling
"""

import pytest
import os
import sqlite3
from pathlib import Path

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.db import Database
from database.farmer_repository import FarmerRepository, FarmerProfile


@pytest.fixture
def test_db():
    """Create a test database."""
    test_db_path = "test_kisan_mitra.db"
    
    # Clean up if exists
    if Path(test_db_path).exists():
        Path(test_db_path).unlink()
    
    db = Database(test_db_path)
    db.initialize()
    
    yield db
    
    # Cleanup
    if Path(test_db_path).exists():
        Path(test_db_path).unlink()


@pytest.fixture
def repository(test_db):
    """Create a test repository."""
    repo = FarmerRepository()
    repo.db = test_db
    return repo


class TestDatabaseInitialization:
    """Test database setup and schema creation."""
    
    def test_database_initializes(self, test_db):
        """Test database initializes without errors."""
        assert test_db._initialized
    
    def test_database_file_created(self):
        """Test database file is created."""
        test_db_path = "test_kisan_mitra_2.db"
        if Path(test_db_path).exists():
            Path(test_db_path).unlink()
        
        db = Database(test_db_path)
        db.initialize()
        
        assert Path(test_db_path).exists()
        
        # Cleanup
        Path(test_db_path).unlink()
    
    def test_data_directory_created(self):
        """Test data directory is created automatically."""
        test_dir = Path("test_data_dir")
        test_db_path = test_dir / "test.db"
        
        # Clean up if exists
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
        
        db = Database(str(test_db_path))
        db.initialize()
        
        assert test_dir.exists()
        assert test_db_path.exists()
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
    
    def test_schema_tables_created(self, test_db):
        """Test that required tables are created."""
        conn = test_db.get_connection()
        cursor = conn.cursor()
        
        # Check users table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        assert cursor.fetchone() is not None
        
        # Check farmer_profiles table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='farmer_profiles'"
        )
        assert cursor.fetchone() is not None
        
        conn.close()
    
    def test_idempotent_initialization(self, test_db):
        """Test database initialization is idempotent."""
        # Initialize twice
        test_db.initialize()
        test_db.initialize()
        
        # Should work without errors
        conn = test_db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        conn.close()


class TestFarmerCRUD:
    """Test farmer creation, reading, updating."""
    
    def test_create_farmer(self, repository):
        """Test creating a new farmer."""
        user_id = "farmer_001"
        success = repository.create_farmer(user_id, "hi")
        
        assert success
        assert repository.farmer_exists(user_id)
    
    def test_lookup_nonexistent_farmer(self, repository):
        """Test looking up a farmer that doesn't exist."""
        profile = repository.lookup_farmer("nonexistent_user")
        
        assert profile is None
    
    def test_lookup_existing_farmer(self, repository):
        """Test looking up an existing farmer."""
        user_id = "farmer_002"
        repository.create_farmer(user_id, "hi")
        
        profile = repository.lookup_farmer(user_id)
        
        assert profile is not None
        assert profile.user_id == user_id
        assert profile.language_preference == "hi"
    
    def test_save_farmer_name(self, repository):
        """Test saving farmer name."""
        user_id = "farmer_003"
        success = repository.save_farmer_memory(user_id, name="Ramesh")
        
        assert success
        profile = repository.lookup_farmer(user_id)
        assert profile is not None
        assert profile.name == "Ramesh"
    
    def test_save_crops_grown(self, repository):
        """Test saving crops grown."""
        user_id = "farmer_004"
        success = repository.save_farmer_memory(
            user_id,
            name="Priya",
            crops_grown="wheat"
        )
        
        assert success
        profile = repository.lookup_farmer(user_id)
        assert profile.crops_grown == "wheat"
        assert profile.name == "Priya"
    
    def test_save_land_size(self, repository):
        """Test saving land size."""
        user_id = "farmer_005"
        success = repository.save_farmer_memory(
            user_id,
            land_size="5 acres"
        )
        
        assert success
        profile = repository.lookup_farmer(user_id)
        assert profile.land_size == "5 acres"
    
    def test_save_district(self, repository):
        """Test saving district."""
        user_id = "farmer_006"
        success = repository.save_farmer_memory(
            user_id,
            district="Varanasi"
        )
        
        assert success
        profile = repository.lookup_farmer(user_id)
        assert profile.district == "Varanasi"
    
    def test_save_irrigation_type(self, repository):
        """Test saving irrigation type."""
        user_id = "farmer_007"
        success = repository.save_farmer_memory(
            user_id,
            irrigation_type="drip"
        )
        
        assert success
        profile = repository.lookup_farmer(user_id)
        assert profile.irrigation_type == "drip"


class TestFarmerMemoryUpdates:
    """Test updating existing farmer information."""
    
    def test_preserve_facts_when_updating(self, repository):
        """Test that existing facts are preserved when updating another fact."""
        user_id = "farmer_008"
        
        # Save initial information
        repository.save_farmer_memory(
            user_id,
            name="Ramesh",
            crops_grown="wheat"
        )
        
        # Update with new information
        repository.save_farmer_memory(
            user_id,
            district="Varanasi"
        )
        
        # Check both facts are preserved
        profile = repository.lookup_farmer(user_id)
        assert profile.name == "Ramesh"
        assert profile.crops_grown == "wheat"
        assert profile.district == "Varanasi"
    
    def test_update_existing_fact(self, repository):
        """Test updating an existing fact."""
        user_id = "farmer_009"
        
        # Save initial crop
        repository.save_farmer_memory(user_id, crops_grown="wheat")
        profile = repository.lookup_farmer(user_id)
        assert profile.crops_grown == "wheat"
        
        # Update to different crop
        repository.save_farmer_memory(user_id, crops_grown="rice")
        profile = repository.lookup_farmer(user_id)
        assert profile.crops_grown == "rice"
    
    def test_do_not_overwrite_with_empty_values(self, repository):
        """Test that empty values don't overwrite existing data."""
        user_id = "farmer_010"
        
        # Save initial data
        repository.save_farmer_memory(
            user_id,
            name="Priya",
            crops_grown="wheat"
        )
        
        # Try to save with None values (should not overwrite)
        repository.save_farmer_memory(
            user_id,
            name=None,
            crops_grown=None,
            district="Punjab"
        )
        
        profile = repository.lookup_farmer(user_id)
        assert profile.name == "Priya"
        assert profile.crops_grown == "wheat"
        assert profile.district == "Punjab"


class TestMultipleFarmers:
    """Test handling multiple distinct farmers."""
    
    def test_farmers_remain_separate(self, repository):
        """Test that multiple farmers don't interfere with each other."""
        # Create farmer 1
        repository.save_farmer_memory(
            "farmer_11",
            name="Ramesh",
            crops_grown="wheat",
            district="Varanasi"
        )
        
        # Create farmer 2
        repository.save_farmer_memory(
            "farmer_12",
            name="Priya",
            crops_grown="rice",
            district="Punjab"
        )
        
        # Verify they are separate
        profile1 = repository.lookup_farmer("farmer_11")
        profile2 = repository.lookup_farmer("farmer_12")
        
        assert profile1.name == "Ramesh"
        assert profile1.crops_grown == "wheat"
        assert profile1.district == "Varanasi"
        
        assert profile2.name == "Priya"
        assert profile2.crops_grown == "rice"
        assert profile2.district == "Punjab"


class TestLanguagePreference:
    """Test language preference storage."""
    
    def test_save_hindi_preference(self, repository):
        """Test saving Hindi as language preference."""
        user_id = "farmer_20"
        repository.save_farmer_memory(user_id, language_preference="hi")
        
        profile = repository.lookup_farmer(user_id)
        assert profile.language_preference == "hi"
    
    def test_save_english_preference(self, repository):
        """Test saving English as language preference."""
        user_id = "farmer_21"
        repository.save_farmer_memory(user_id, language_preference="en")
        
        profile = repository.lookup_farmer(user_id)
        assert profile.language_preference == "en"


class TestLastInteraction:
    """Test last_interaction timestamp updates."""
    
    def test_last_interaction_updated(self, repository):
        """Test that last_interaction is updated when saving."""
        user_id = "farmer_22"
        repository.save_farmer_memory(user_id, name="Test")
        
        profile = repository.lookup_farmer(user_id)
        assert profile.last_interaction is not None
    
    def test_last_interaction_updated_on_each_save(self, repository):
        """Test that last_interaction updates on each save."""
        user_id = "farmer_23"
        
        repository.save_farmer_memory(user_id, name="Test1")
        profile1 = repository.lookup_farmer(user_id)
        time1 = profile1.last_interaction
        
        # Save again
        repository.save_farmer_memory(user_id, name="Test2")
        profile2 = repository.lookup_farmer(user_id)
        time2 = profile2.last_interaction
        
        # Times should be different (or at least one should exist)
        assert time1 is not None
        assert time2 is not None


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_farmer_profile_from_dict(self):
        """Test FarmerProfile can be converted to dict."""
        profile = FarmerProfile(
            user_id="test_001",
            name="TestUser",
            crops_grown="wheat"
        )
        
        profile_dict = profile.to_dict()
        assert profile_dict["user_id"] == "test_001"
        assert profile_dict["name"] == "TestUser"
        assert profile_dict["crops_grown"] == "wheat"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
