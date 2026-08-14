"""
Tests for Day 9 TTS voice switching via LiveKit's update_options().

Verifies that:
- Main voice (Anisha) is used by default
- Handoff activates specialist voice (Samar) via update_options(tts=...)
- Handback restores main voice (Anisha)
- Specialist mode state is properly tracked
"""

import pytest
import logging
from unittest.mock import Mock, AsyncMock

logger = logging.getLogger("test_voice_switching")
logging.basicConfig(level=logging.DEBUG)


class TestVoiceConfiguration:
    """Test voice configuration."""
    
    def test_specialist_voice_config_exists(self):
        """Specialist voice must be configured."""
        from src import config
        assert hasattr(config, 'CROP_SPECIALIST_TTS_VOICE')
        assert config.CROP_SPECIALIST_TTS_VOICE == "samar"
    
    def test_main_voice_config_exists(self):
        """Main voice must be configured."""
        from src.config import TTS_VOICE
        assert TTS_VOICE == "anisha"
    
    def test_tts_style_configured(self):
        """TTS style and pacing must be configured."""
        from src.config import TTS_STYLE, TTS_TEXT_PACING
        assert TTS_STYLE is not None
        assert TTS_TEXT_PACING is not None


class TestVoiceState:
    """Test voice state management."""
    
    def test_specialist_mode_state_tracking(self):
        """CropContextManager must track specialist mode state."""
        from src.crop_context import get_crop_context_manager
        
        mgr = get_crop_context_manager()
        mgr.reset()
        
        # Initially not in specialist mode
        assert not mgr.is_in_specialist_mode()
        
        # Start crop discussion → specialist mode
        mgr.start_crop_discussion(crop="wheat", problem_description="yellowing", farmer_name="Ram")
        assert mgr.is_in_specialist_mode()
        
        # End crop discussion → back to normal
        mgr.end_crop_discussion()
        assert not mgr.is_in_specialist_mode()
        logger.info("✓ Specialist mode state properly tracked")


class TestHandoffVoiceSwitching:
    """Test that handoff properly switches TTS voice."""
    
    @pytest.mark.asyncio
    async def test_handoff_calls_update_options(self):
        """Handoff must call agent.update_options(tts=...) to switch voice."""
        from src.assistant import KisanMitraAssistant
        
        assistant = KisanMitraAssistant(room_name="test", call_id="call_123")
        assistant.update_options = Mock()
        
        # Mock context
        mock_ctx = AsyncMock()
        mock_ctx.say = AsyncMock()
        
        # Call handoff
        result = await assistant.handoff_to_crop_specialist(
            ctx=mock_ctx,
            crop="wheat",
            problem_description="yellowing leaves",
            farmer_name="Ramesh"
        )
        
        # Verify:
        # 1. Announcement was made
        mock_ctx.say.assert_called()
        
        # 2. update_options was called (this switches the TTS voice)
        assert assistant.update_options.called
        assert 'tts' in assistant.update_options.call_args.kwargs
        
        # 3. Handoff succeeded
        assert "handoff_success" in result
        logger.info("✓ Handoff calls update_options to switch voice")
    
    @pytest.mark.asyncio
    async def test_handoff_failure_graceful(self):
        """If TTS switch fails, agent should continue with fallback."""
        from src.assistant import KisanMitraAssistant
        
        assistant = KisanMitraAssistant(room_name="test", call_id="call_123")
        
        # Mock update_options to fail
        assistant.update_options = Mock(side_effect=Exception("TTS switch failed"))
        
        mock_ctx = AsyncMock()
        mock_ctx.say = AsyncMock()
        
        # Handoff should still succeed (logs error, continues)
        result = await assistant.handoff_to_crop_specialist(
            ctx=mock_ctx,
            crop="wheat",
            problem_description="yellowing",
            farmer_name="Ramesh"
        )
        
        assert "handoff_success" in result
        logger.info("✓ Handoff continues if TTS switch fails")


class TestHandbackVoiceSwitching:
    """Test that handback restores main voice."""
    
    @pytest.mark.asyncio
    async def test_handback_restores_main_voice(self):
        """Handback must restore main voice via update_options."""
        from src.assistant import KisanMitraAssistant
        from src.crop_context import get_crop_context_manager
        
        assistant = KisanMitraAssistant(room_name="test", call_id="call_123")
        assistant.update_options = Mock()
        
        mgr = get_crop_context_manager()
        mgr.reset()
        mgr.start_crop_discussion(crop="wheat", problem_description="test", farmer_name="Ram")
        
        mock_ctx = AsyncMock()
        mock_ctx.say = AsyncMock()
        
        # Call handback
        result = await assistant.handback_to_kisan_mitra(ctx=mock_ctx)
        
        # Verify:
        # 1. Announcement was made
        mock_ctx.say.assert_called()
        
        # 2. update_options was called (restores main voice)
        assert assistant.update_options.called
        assert 'tts' in assistant.update_options.call_args.kwargs
        
        # 3. Handback succeeded
        assert "handback_success" in result
        logger.info("✓ Handback calls update_options to restore main voice")
    
    @pytest.mark.asyncio
    async def test_handback_session_preserved(self):
        """Handback must preserve same session/call_id."""
        from src.assistant import KisanMitraAssistant
        
        assistant = KisanMitraAssistant(room_name="test_room", call_id="call_456")
        assistant.update_options = Mock()
        
        mock_ctx = AsyncMock()
        mock_ctx.say = AsyncMock()
        
        await assistant.handback_to_kisan_mitra(ctx=mock_ctx)
        
        # Same call_id should be maintained
        assert assistant.call_id == "call_456"
        logger.info("✓ Handback preserves same call_id and session")


class TestVoiceSwitchingSequence:
    """Test full handoff/handback sequences."""
    
    @pytest.mark.asyncio
    async def test_full_handoff_handback_cycle(self):
        """Test complete cycle: main → specialist → main."""
        from src.assistant import KisanMitraAssistant
        from src.crop_context import get_crop_context_manager
        
        assistant = KisanMitraAssistant(room_name="test", call_id="call_789")
        assistant.update_options = Mock()
        
        mgr = get_crop_context_manager()
        mgr.reset()
        
        mock_ctx = AsyncMock()
        mock_ctx.say = AsyncMock()
        
        # Step 1: Handoff to specialist
        result1 = await assistant.handoff_to_crop_specialist(
            ctx=mock_ctx,
            crop="rice",
            problem_description="brown spots",
            farmer_name="Priya"
        )
        assert "handoff_success" in result1
        assert mgr.is_in_specialist_mode()
        assert assistant.update_options.call_count == 1
        
        # Step 2: Handback to main
        result2 = await assistant.handback_to_kisan_mitra(ctx=mock_ctx)
        assert "handback_success" in result2
        assert not mgr.is_in_specialist_mode()
        assert assistant.update_options.call_count == 2  # Called again for handback
        
        logger.info("✓ Full handoff/handback cycle works correctly")


class TestVoiceContextIntegration:
    """Test that voice switching works with specialist context."""
    
    @pytest.mark.asyncio
    async def test_voice_switch_with_context(self):
        """Voice switch must happen WITH specialist context available."""
        from src.assistant import KisanMitraAssistant
        from src.crop_context import get_crop_context_manager
        
        assistant = KisanMitraAssistant(room_name="test", call_id="call_999")
        assistant.update_options = Mock()
        
        mgr = get_crop_context_manager()
        mgr.reset()
        
        mock_ctx = AsyncMock()
        mock_ctx.say = AsyncMock()
        
        # Handoff with full context
        await assistant.handoff_to_crop_specialist(
            ctx=mock_ctx,
            crop="cotton",
            problem_description="pest infestation",
            farmer_name="Priya",
            district="Vidarbha"
        )
        
        # Verify:
        # 1. Voice switched
        assert assistant.update_options.called
        
        # 2. Context is available
        context = mgr.get_context_for_prompt()
        assert context is not None
        assert context['crop'] == "cotton"
        assert context['farmer_name'] == "Priya"
        
        logger.info("✓ Voice switch happens WITH specialist context preserved")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
