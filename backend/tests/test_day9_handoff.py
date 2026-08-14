"""
Tests for Day 9 Handoff/Handback Feature

Tests the crop context manager and handoff workflow.
"""

import pytest
import time
from src.crop_context import (
    CropContextManager,
    CropProblemContext,
    get_crop_context_manager,
)


class TestCropProblemContext:
    """Test the CropProblemContext data class."""
    
    def test_context_creation(self):
        """Test creating a crop problem context."""
        ctx = CropProblemContext(
            crop="wheat",
            problem_description="Yellow leaves on wheat plant",
            farmer_name="Ram Kumar",
            district="Punjab"
        )
        
        assert ctx.crop == "wheat"
        assert ctx.problem_description == "Yellow leaves on wheat plant"
        assert ctx.farmer_name == "Ram Kumar"
        assert ctx.district == "Punjab"
        assert ctx.is_active is False  # Default
        assert ctx.specialist_mode is False  # Default
    
    def test_context_to_dict(self):
        """Test converting context to dictionary."""
        ctx = CropProblemContext(
            crop="rice",
            problem_description="Brown spots on leaves",
            farmer_name="Priya Singh",
            district="Haryana",
            specialist_mode=True
        )
        
        ctx_dict = ctx.to_dict()
        
        assert ctx_dict["crop"] == "rice"
        assert ctx_dict["problem"] == "Brown spots on leaves"
        assert ctx_dict["farmer_name"] == "Priya Singh"
        assert ctx_dict["district"] == "Haryana"
        assert ctx_dict["specialist_mode"] is True


class TestCropContextManager:
    """Test the CropContextManager class."""
    
    def setup_method(self):
        """Reset global context manager before each test."""
        import src.crop_context
        src.crop_context._crop_context_manager = None
    
    def test_manager_initialization(self):
        """Test manager initializes with no context."""
        mgr = CropContextManager()
        
        assert mgr.current_context is None
        assert len(mgr.history) == 0
    
    def test_start_crop_discussion(self):
        """Test starting a crop discussion."""
        mgr = CropContextManager()
        
        ctx = mgr.start_crop_discussion(
            crop="cotton",
            problem_description="White flies attacking plants",
            farmer_name="Suresh",
            district="Gujarat"
        )
        
        assert ctx.crop == "cotton"
        assert ctx.problem_description == "White flies attacking plants"
        assert ctx.is_active is True
        assert ctx.specialist_mode is True
        assert ctx.started_at > 0
        
        # Current context should be set
        assert mgr.current_context == ctx
    
    def test_is_in_specialist_mode(self):
        """Test specialist mode detection."""
        mgr = CropContextManager()
        
        # Should be False initially
        assert mgr.is_in_specialist_mode() is False
        
        # Start discussion
        mgr.start_crop_discussion(
            crop="wheat",
            problem_description="Rust disease",
            farmer_name="Farmer"
        )
        
        # Should be True now
        assert mgr.is_in_specialist_mode() is True
    
    def test_get_active_context(self):
        """Test retrieving active context."""
        mgr = CropContextManager()
        
        # No context initially
        assert mgr.get_active_context() is None
        
        # Start discussion
        ctx = mgr.start_crop_discussion(
            crop="rice",
            problem_description="Blast disease",
            farmer_name="Farmer"
        )
        
        # Should return the context
        active = mgr.get_active_context()
        assert active == ctx
        assert active.is_active is True
    
    def test_get_context_for_prompt(self):
        """Test getting context for prompt injection."""
        mgr = CropContextManager()
        
        # No context initially
        assert mgr.get_context_for_prompt() is None
        
        # Start discussion
        mgr.start_crop_discussion(
            crop="sugarcane",
            problem_description="Insect pest infestation",
            farmer_name="Rajesh",
            district="Maharashtra"
        )
        
        # Should return dict
        ctx_dict = mgr.get_context_for_prompt()
        assert ctx_dict is not None
        assert ctx_dict["crop"] == "sugarcane"
        assert ctx_dict["problem"] == "Insect pest infestation"
        assert ctx_dict["farmer_name"] == "Rajesh"
        assert ctx_dict["specialist_mode"] is True
    
    def test_end_crop_discussion(self):
        """Test ending a crop discussion."""
        mgr = CropContextManager()
        
        # Start discussion
        mgr.start_crop_discussion(
            crop="wheat",
            problem_description="Problem",
            farmer_name="Farmer"
        )
        
        # Verify it's active
        assert mgr.get_active_context() is not None
        assert mgr.is_in_specialist_mode() is True
        
        # End discussion
        ended = mgr.end_crop_discussion()
        
        # Should return the context that was ended
        assert ended is not None
        assert ended.crop == "wheat"
        assert ended.is_active is False
        assert ended.specialist_mode is False
        
        # Should be in history
        assert len(mgr.history) == 1
        assert mgr.history[0] == ended
        
        # Current context should be None
        assert mgr.current_context is None
        assert mgr.is_in_specialist_mode() is False
    
    def test_end_crop_discussion_when_none_active(self):
        """Test ending discussion when none is active."""
        mgr = CropContextManager()
        
        # Try to end with no active context
        ended = mgr.end_crop_discussion()
        
        # Should return None
        assert ended is None
    
    def test_multiple_discussions_history(self):
        """Test multiple discussions in sequence."""
        mgr = CropContextManager()
        
        # First discussion
        ctx1 = mgr.start_crop_discussion(
            crop="wheat",
            problem_description="Problem 1",
            farmer_name="Farmer"
        )
        mgr.end_crop_discussion()
        
        # Second discussion
        ctx2 = mgr.start_crop_discussion(
            crop="rice",
            problem_description="Problem 2",
            farmer_name="Farmer"
        )
        mgr.end_crop_discussion()
        
        # History should have both
        assert len(mgr.history) == 2
        assert mgr.history[0].crop == "wheat"
        assert mgr.history[1].crop == "rice"
    
    def test_reset(self):
        """Test resetting the context manager."""
        mgr = CropContextManager()
        
        # Add some data
        mgr.start_crop_discussion(
            crop="wheat",
            problem_description="Problem",
            farmer_name="Farmer"
        )
        mgr.end_crop_discussion()
        
        # Verify data exists
        assert mgr.current_context is None
        assert len(mgr.history) == 1
        
        # Reset
        mgr.reset()
        
        # Should be clean
        assert mgr.current_context is None
        assert len(mgr.history) == 0
    
    def test_global_singleton(self):
        """Test that global get_crop_context_manager returns singleton."""
        # Reset global
        import src.crop_context
        src.crop_context._crop_context_manager = None
        
        # Get first instance
        mgr1 = get_crop_context_manager()
        
        # Start discussion
        mgr1.start_crop_discussion(
            crop="wheat",
            problem_description="Problem",
            farmer_name="Farmer"
        )
        
        # Get second instance - should be same
        mgr2 = get_crop_context_manager()
        
        assert mgr1 is mgr2
        assert mgr2.is_in_specialist_mode() is True


class TestCropContextManagerIntegration:
    """Integration tests for crop context workflow."""
    
    def setup_method(self):
        """Reset global context manager before each test."""
        import src.crop_context
        src.crop_context._crop_context_manager = None
    
    def test_complete_workflow(self):
        """Test a complete handoff and handback workflow."""
        mgr = get_crop_context_manager()
        
        # Farmer comes with wheat problem
        assert not mgr.is_in_specialist_mode()
        
        # Handoff to specialist
        ctx = mgr.start_crop_discussion(
            crop="wheat",
            problem_description="Yellow leaves with brown spots",
            farmer_name="Raj Kumar",
            district="Uttar Pradesh"
        )
        
        # In specialist mode
        assert mgr.is_in_specialist_mode()
        assert mgr.get_active_context().crop == "wheat"
        
        # Specialist works with context
        prompt_ctx = mgr.get_context_for_prompt()
        assert prompt_ctx["crop"] == "wheat"
        assert prompt_ctx["farmer_name"] == "Raj Kumar"
        
        # Problem resolved, hand back
        ended = mgr.end_crop_discussion()
        
        # Back to main mode
        assert not mgr.is_in_specialist_mode()
        assert ended.crop == "wheat"
        assert ended.is_active is False
    
    def test_context_preservation_across_calls(self):
        """Test that context is preserved correctly."""
        mgr = get_crop_context_manager()
        
        farmer_name = "Priya Singh"
        crop = "rice"
        problem = "Blast disease affecting leaves"
        district = "West Bengal"
        
        # Start discussion
        ctx = mgr.start_crop_discussion(
            crop=crop,
            problem_description=problem,
            farmer_name=farmer_name,
            district=district
        )
        
        # Get context multiple times
        ctx1 = mgr.get_context_for_prompt()
        ctx2 = mgr.get_context_for_prompt()
        
        # Should be consistent
        assert ctx1 == ctx2
        assert ctx1["farmer_name"] == farmer_name
        assert ctx1["crop"] == crop
        
        # End and verify history
        ended = mgr.end_crop_discussion()
        assert len(mgr.history) == 1
        assert mgr.history[0].farmer_name == farmer_name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
