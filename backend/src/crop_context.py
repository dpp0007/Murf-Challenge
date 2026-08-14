"""
Crop Context Manager

Manages conversation context for crop problem handoff within a single agent session.
Since LiveKit doesn't support runtime agent switching, we use context-aware prompt
engineering to simulate specialist behavior while maintaining one AgentSession.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger("crop_context")


@dataclass
class CropProblemContext:
    """Context for an active crop problem discussion."""
    crop: str
    problem_description: str
    farmer_name: Optional[str] = None
    district: Optional[str] = None
    is_active: bool = False
    specialist_mode: bool = False  # Indicates if we're in specialist mode
    started_at: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for passing to prompts."""
        return {
            "crop": self.crop,
            "problem": self.problem_description,
            "farmer_name": self.farmer_name,
            "district": self.district,
            "specialist_mode": self.specialist_mode,
        }


class CropContextManager:
    """
    Manages crop problem context across a conversation.
    
    Usage pattern:
    1. Main agent detects crop problem
    2. Calls start_crop_discussion()
    3. Agent switches to specialist mode via modified system prompt
    4. Agent handles crop-specific Q&A
    5. Calls end_crop_discussion() when issue is resolved
    6. Agent returns to main mode
    """
    
    def __init__(self):
        self.current_context: Optional[CropProblemContext] = None
        self.history: list[CropProblemContext] = []
    
    def start_crop_discussion(
        self,
        crop: str,
        problem_description: str,
        farmer_name: Optional[str] = None,
        district: Optional[str] = None,
    ) -> CropProblemContext:
        """
        Start a crop problem discussion context.
        
        Args:
            crop: Crop name
            problem_description: Description of the problem
            farmer_name: Optional farmer name
            district: Optional district
            
        Returns:
            CropProblemContext for this discussion
        """
        import time
        
        self.current_context = CropProblemContext(
            crop=crop,
            problem_description=problem_description,
            farmer_name=farmer_name,
            district=district,
            is_active=True,
            specialist_mode=True,
            started_at=time.time(),
        )
        
        logger.info(
            f"[CropContext] Started crop discussion: crop={crop}, "
            f"farmer={farmer_name}, district={district}"
        )
        
        return self.current_context
    
    def end_crop_discussion(self) -> Optional[CropProblemContext]:
        """
        End the current crop problem discussion.
        
        Returns:
            The context that was ended
        """
        if not self.current_context:
            logger.warning("[CropContext] No active crop discussion to end")
            return None
        
        self.current_context.is_active = False
        self.current_context.specialist_mode = False
        
        # Store in history for reference
        self.history.append(self.current_context)
        
        crop = self.current_context.crop
        farmer = self.current_context.farmer_name
        logger.info(f"[CropContext] Ended crop discussion: crop={crop}, farmer={farmer}")
        
        old_context = self.current_context
        self.current_context = None
        
        return old_context
    
    def get_active_context(self) -> Optional[CropProblemContext]:
        """Get the currently active crop context, if any."""
        return self.current_context if self.current_context and self.current_context.is_active else None
    
    def is_in_specialist_mode(self) -> bool:
        """Check if we're currently in crop specialist mode."""
        return self.current_context is not None and self.current_context.specialist_mode
    
    def get_context_for_prompt(self) -> Optional[Dict[str, Any]]:
        """Get context information to inject into the system prompt."""
        if not self.current_context or not self.current_context.is_active:
            return None
        
        return self.current_context.to_dict()
    
    def reset(self) -> None:
        """Reset all context (for session cleanup)."""
        self.current_context = None
        self.history.clear()
        logger.info("[CropContext] Context reset")


# Global instance
_crop_context_manager: Optional[CropContextManager] = None


def get_crop_context_manager() -> CropContextManager:
    """Get or create the global crop context manager."""
    global _crop_context_manager
    if _crop_context_manager is None:
        _crop_context_manager = CropContextManager()
    return _crop_context_manager
