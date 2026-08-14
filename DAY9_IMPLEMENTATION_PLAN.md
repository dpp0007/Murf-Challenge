# Day 9: Agent Handoff Implementation Plan

## Status: IN PROGRESS - Phase 1 Complete

This document outlines the Day 9 agent handoff feature implementation strategy.

---

## What's Complete (Phase 1)

1. ✅ Crop Specialist Prompt (`src/prompts/crop_specialist_prompt.py`)
   - Focused instructions for crop-specific problems
   - Clear scope boundaries  
   - Proper voice and language configuration

2. ✅ Crop Specialist Agent Class (`src/crop_specialist.py`)
   - Separate CropSpecialist agent
   - Shares same call_id for analytics
   - Independent system instructions

3. ✅ Configuration Updates (`src/config.py`)
   - Added CROP_SPECIALIST_TTS_VOICE = "samar"
   - Separate voice config for specialist

4. ✅ Handoff Tool in Kisan Mitra (`src/assistant.py`)
   - `handoff_to_crop_specialist()` method
   - Announces handoff to farmer before switching
   - Prepares context for specialist

---

## What's Needed (Phase 2+)

### Phase 2: Core Handoff Mechanism (TODO)

The critical piece is implementing agent switching within the same LiveKit session.

Current challenge:
- LiveKit AgentSession is attached to a specific Agent instance
- We need to switch agents without closing the session
- Must preserve conversation context
- Must keep the same audio stream

Solution approach:
- Investigate LiveKit Agents SDK capabilities
- Implement agent switching mechanism
- Handle TTS voice switching (anisha → samar)

### Phase 3: Conversation History Preservation (TODO)

The specialist must continue without farmer repeating the problem.

### Phase 4: Handback Mechanism (TODO)

Specialist must be able to hand back to Kisan Mitra with same conversation continuing.

### Phase 5: Testing & Validation (TODO)

All 7 test scenarios must pass.

---

## Key Design Decisions

**Single AgentSession with agent switching** (not creating new session)

This approach:
- Keeps single analytics call record
- Maintains continuous conversation
- Same room/participants
- Seamless voice switch
- No new LiveKit session/token needed

---

## Next Steps

1. Investigate `AgentSession.update()` or similar mechanism in LiveKit SDK
2. Implement handoff_manager.py for agent switching logic
3. Update agent.py to support agent switching
4. Test single agent switch with voice change
5. Implement handback mechanism
6. Run full integration tests
7. Real end-to-end voice test

---

## Branch Strategy

- **day-8**: Day 8 analytics (COMPLETE & STABLE)
- **day-9**: Day 9 handoff feature (IN PROGRESS)

Day 9 changes are ONLY on day-9 branch.
