# Human-in-the-Loop Escalation System - Implementation Summary

## Overview

This document summarizes the complete human-in-the-loop escalation system implemented for Kisan Mitra on Day 7. The system allows farmers to escalate serious agricultural problems to human advisers via Discord, with automatic callbacks when the adviser provides a solution.

## Commit Details

**Commit Hash:** `418855f`  
**Branch:** `day-6`  
**Author:** Deepankar Patel  
**Date:** August 12, 2026

**Commit Message:**
```
Day 7: Human-in-the-Loop Escalation System - Framework Implementation
```

## What Was Implemented

### 1. Database Layer

**File:** `backend/src/database/escalation_repository.py` (427 lines)

- Complete CRUD operations for escalation requests
- `Escalation` dataclass with all required fields
- Methods:
  - `create_escalation()` - Create new escalation with unique reference ID
  - `get_escalation_by_reference()` - Fetch escalation by KM-YYYYMMDD-XXXX ID
  - `get_escalations_by_user()` - Get farmer's escalations
  - `get_open_escalations()` - List all open escalations for Discord display
  - `resolve_escalation()` - Mark as resolved with adviser answer
  - `update_callback_status()` - Track callback progress

**Schema:** `escalations` table in SQLite
```sql
CREATE TABLE escalations (
  id INTEGER PRIMARY KEY,
  reference_id TEXT UNIQUE,          -- KM-20260812-0042
  user_id TEXT NOT NULL,             -- Farmer ID
  farmer_name TEXT NOT NULL,
  district TEXT,
  reason TEXT NOT NULL,              -- SERIOUS_CROP_PROBLEM, etc.
  original_question TEXT,
  summary TEXT,
  what_agent_checked TEXT,
  urgency TEXT,                      -- LOW, MEDIUM, HIGH, EMERGENCY
  language TEXT,                     -- hi, en
  status TEXT,                       -- OPEN, IN_PROGRESS, RESOLVED
  human_answer TEXT,                 -- Adviser's response
  resolution_notes TEXT,
  callback_status TEXT,              -- NOT_STARTED, QUEUED, CALLING, COMPLETED, etc.
  callback_attempts INTEGER,
  created_at, updated_at, resolved_at, callback_timestamps...
)
```

**Indexes:** user_id, reference_id, status, callback_status for fast queries

### 2. Service Layer

#### Escalation Service
**File:** `backend/src/services/escalation_service.py` (173 lines)

- Escalation determination logic
- Enum: `EscalationReason` (SERIOUS_CROP_PROBLEM, MARKET_DATA_UNAVAILABLE, UNCERTAIN_DIAGNOSIS, OTHER)
- Methods:
  - `should_escalate_crop_problem()` - Analyze problem description
  - `should_escalate_market_data()` - Check API failures/stale data
  - `create_escalation()` - Create with farmer context

#### Escalation Callback Service
**File:** `backend/src/services/escalation_callback_service.py` (215 lines)

- Orchestrates automatic callbacks when escalation resolved
- Methods:
  - `queue_callback()` - Queue callback for execution
  - `_execute_callback()` - Trigger SIP call via outbound service
  - `handle_callback_completed()` - Update status after call ends
  - `should_retry_callback()` - Determine if retry needed

#### Discord Service
**File:** `backend/src/services/discord_service.py` (186 lines)

- Placeholder for discord.py integration
- Structure for:
  - Sending notifications to escalation channel
  - Displaying open escalations to advisers
  - Modal for adviser to submit answer
  - Authorization checks (role-based)

### 3. Tools Layer

**File:** `backend/src/tools/escalation_tools.py` (127 lines)

- `create_escalation()` function tool for agent
- Exposed to Gemini LLM via `@function_tool` decorator
- Parameters:
  - `reason` - One of the escalation reasons
  - `summary` - Brief issue description
  - `original_question` - Farmer's original question
  - `what_agent_checked` - What agent verified
  - `urgency` - Severity level
  - `preferred_followup` - Callback method (phone/whatsapp)

**Important:** Tool validates farmer permission was obtained before allowing escalation

### 4. API Layer

**File:** `backend/src/api/escalation_routes.py` (179 lines)

HTTP endpoints for adviser/Discord integration:
- `POST /api/escalations/{reference_id}/resolve` - Adviser submits answer
- `GET /api/escalations/open` - List open escalations
- `GET /api/escalations/{reference_id}` - Get escalation details
- `GET /api/escalations/user/{user_id}` - Get farmer's escalations

*Note:* Routes created but not yet integrated into `http_server.py`

### 5. System Prompt Updates

**File:** `backend/src/prompts/kisan_prompt.py` (60 lines added)

- **New Section: ESCALATION** - Detailed escalation flow
  - When to consider escalation (serious crop problems, market data unavailable, etc.)
  - Permission-first approach (ask farmer before escalating)
  - Clear dialogue examples for asking permission
  - Instructions not to pressure farmer
  - Opt-out respect

- **Permission Flow:**
  1. Agent identifies problem needs human help
  2. Explains situation warmly to farmer
  3. Asks: "क्या मैं आपकी समस्या विशेषज्ञ के साथ साझा कर सकता हूँ?"
  4. Waits for explicit YES (हाँ, जी, ठीक है, भेज दो)
  5. Only on YES → calls create_escalation()
  6. If NO → "ठीक है। मैं आपकी जानकारी किसी के साथ साझा नहीं करूंगा।"

### 6. Database Integration

**File:** `backend/src/database/db.py` (45 lines added)

- Created `escalations` table schema in `initialize()` method
- Added 4 indexes for performance
- Integrated with existing user/farmer_profiles foreign keys
- Cascading delete for data consistency

### 7. Assistant Integration

**File:** `backend/src/assistant.py` (5 lines modified)

- Imported and initialized `get_escalation_tools()`
- Made escalation tool available to agent

### 8. Environment Configuration

**File:** `backend/.env.example` (10 lines added)

```
# Discord Integration (for adviser notifications)
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_SERVER_ID=your_server_id
DISCORD_ESCALATION_CHANNEL_ID=your_channel_id
DISCORD_ADVISER_ROLE_ID=your_adviser_role_id

# Callback Configuration
CALLBACK_MAX_RETRIES=2
OUTBOUND_CALL_ENABLED=true
```

### 9. Documentation

**File:** `README.md` (96 lines added)

- Added "Day 7: Human-in-the-Loop Escalation System" section
- Documented all features
- Architecture diagram (text-based)
- Database design explanation
- Implementation status tracking

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      ESCALATION FLOW                             │
└─────────────────────────────────────────────────────────────────┘

1. AGENT IDENTIFIES SERIOUS PROBLEM
   └─ crop disease, widespread pest, market data unavailable, etc.

2. AGENT ASKS PERMISSION (CRITICAL)
   └─ "क्या मैं आपकी समस्या विशेषज्ञ के साथ साझा कर सकता हूँ?"
   
3. FARMER RESPONDS
   ├─ YES (हाँ/जी/ठीक है) → Continue to step 4
   └─ NO (नहीं/मत भेजो) → End escalation, respect choice

4. AGENT CALLS create_escalation()
   └─ create_escalation(reason, summary, original_question, ...)

5. ESCALATION STORED IN SQLite
   ├─ reference_id: KM-20260812-0042
   ├─ status: OPEN
   └─ callback_status: NOT_STARTED

6. DISCORD NOTIFICATION (TODO)
   └─ Notify advisers in #escalations channel

7. ADVISER REVIEWS & SUBMITS ANSWER (TODO)
   ├─ Use Discord modal or web dashboard
   └─ POST /api/escalations/{reference_id}/resolve

8. ESCALATION RESOLVED
   ├─ status: RESOLVED
   ├─ human_answer: [adviser's answer]
   └─ callback_status: QUEUED

9. AUTOMATIC CALLBACK TRIGGERED (TODO - IN PROGRESS)
   ├─ EscalationCallbackService.queue_callback()
   ├─ Check farmer opt-out status
   └─ If enabled → Place SIP call via OutboundWeatherService

10. FARMER RECEIVES CALLBACK
    ├─ Agent repeats original question
    ├─ Agent provides human adviser answer
    └─ Call completes: callback_status: COMPLETED
```

## Key Design Decisions

### 1. Permission-First Approach
- **Why:** Farmer autonomy and trust
- **How:** Agent asks explicit permission before escalating
- **Implementation:** Tool validates permission flow was followed

### 2. Reference ID Format: KM-YYYYMMDD-XXXX
- **Why:** Human-readable, trackable, sortable
- **Format:** KM-20260812-0042 (date + 4-digit sequence)
- **Implementation:** Generated in repository, checked for uniqueness

### 3. Callback Status Tracking
- NOT_STARTED → QUEUED → CALLING → CONNECTED → COMPLETED
- Falls back to NO_ANSWER, FAILED, SKIPPED_OPT_OUT
- **Why:** Full audit trail for debugging and retry logic

### 4. Escalation Reasons Enum
- **Why:** Type safety, prevent invalid reasons
- **Values:**
  - SERIOUS_CROP_PROBLEM (severe damage, disease, pest)
  - MARKET_DATA_UNAVAILABLE (API failure)
  - UNCERTAIN_DIAGNOSIS (agent unsure)
  - OTHER (general)

### 5. Opt-Out Protection
- Callback service checks `farmer.outbound_calls_enabled` before calling
- Status updated to SKIPPED_OPT_OUT if farmer opted out
- **Why:** Respect farmer preferences, legal compliance

## Files Summary

| File | Type | Lines | Purpose |
|------|------|-------|---------|
| escalation_repository.py | New | 427 | Database CRUD operations |
| escalation_service.py | New | 173 | Escalation logic |
| escalation_callback_service.py | New | 215 | Callback orchestration |
| discord_service.py | New | 186 | Discord integration (TODO) |
| escalation_tools.py | New | 127 | Agent function tools |
| escalation_routes.py | New | 179 | HTTP API endpoints |
| db.py | Modified | +45 | Added escalations table |
| assistant.py | Modified | +5 | Tool integration |
| kisan_prompt.py | Modified | +60 | Escalation instructions |
| .env.example | Modified | +10 | Config variables |
| README.md | Modified | +96 | Documentation |

**Total:** 11 files, 1,520 lines added

## What's Complete ✅

- [x] Database schema with full audit trail
- [x] Escalation repository (all CRUD operations)
- [x] Escalation service (determination logic)
- [x] Escalation callback service (callback orchestration)
- [x] Agent function tool (create_escalation with permission validation)
- [x] HTTP API routes (escalation endpoints)
- [x] Discord service structure (placeholder)
- [x] System prompt (escalation & permission flow)
- [x] Environment configuration
- [x] Documentation

## What's Remaining (Blocking) ⏳

### CRITICAL - Required for End-to-End Flow:

1. **Outbound Service Integration**
   - [ ] Add `initiate_escalation_callback()` method to OutboundWeatherAlertService
   - [ ] Pass escalation context (reference_id, original_question, human_answer)
   - [ ] Generate callback message template
   - [ ] Call existing `create_sip_participant()` with escalation context

2. **HTTP Server Integration**
   - [ ] Register escalation routes in FastAPI http_server.py
   - [ ] Mount escalation routes to app

3. **Discord Bot Implementation**
   - [ ] Install discord.py library
   - [ ] Implement bot client initialization
   - [ ] Send notifications to escalation channel
   - [ ] Display open escalations (paginated)
   - [ ] Modal for adviser resolution submission
   - [ ] Authorization check (role-based)

4. **Agent Callback Context Handling**
   - [ ] When escalation callback room joins, agent detects context
   - [ ] Agent knows: this is escalation callback, not weather alert
   - [ ] Agent repeats original question naturally
   - [ ] Agent provides human answer WITHOUT hallucinating

### IMPORTANT - High Priority:

5. [ ] Idempotency protection for callbacks (prevent duplicate calls)
6. [ ] Retry logic with exponential backoff
7. [ ] Comprehensive logging with reference_id context
8. [ ] Permission validation on adviser operations
9. [ ] Input sanitization (farmer names, answers, etc.)

### TESTING - Required for Production:

10. [ ] Unit tests for escalation creation
11. [ ] Unit tests for permission validation
12. [ ] Unit tests for callback status transitions
13. [ ] Integration tests for database operations
14. [ ] End-to-end test: farmer → escalation → Discord → adviser → callback
15. [ ] Opt-out protection tests
16. [ ] Error handling tests (API failures, network issues)

## Testing Strategy

### Manual Testing (Before Unit Tests):
1. Create escalation from agent tool directly
2. Verify reference_id generated correctly
3. Query escalations from database
4. Update escalation with adviser answer
5. Verify callback_status changes

### Unit Tests:
- Escalation repository (CRUD, queries)
- Escalation service (determination logic)
- Callback service (status transitions)
- Tools (permission validation)

### Integration Tests:
- Full escalation creation flow
- Permission validation
- Database atomicity (no orphaned records)
- Callback queueing

### E2E Tests:
- Farmer reports problem
- Agent asks permission
- Farmer says "हाँ"
- Escalation created and stored
- Advisory interface shows escalation
- Adviser resolves with answer
- Callback queued
- Callback placed and connected
- Agent speaks question + answer
- Callback completed
- Database shows COMPLETED status

## Deployment Checklist

Before deploying to production:

- [ ] Implement all CRITICAL blocking items
- [ ] Run comprehensive test suite (>80% coverage)
- [ ] Load test (escalations under high volume)
- [ ] Discord bot tokens configured in environment
- [ ] Database migrations tested on production schema
- [ ] Backup strategy for escalations table
- [ ] Monitoring and alerting for escalation failures
- [ ] Adviser training on Discord interface
- [ ] Farmer communication about escalation process
- [ ] Opt-out mechanism clearly documented

## Notes for Future Development

1. **Escalation Analytics:**
   - Track escalation rate by reason, crop, district
   - Adviser response time SLA tracking
   - Callback success rate

2. **Escalation Dashboard:**
   - Web UI for advisers (alternative to Discord)
   - Real-time escalation status
   - Metrics and analytics

3. **Advanced Callback Features:**
   - Callback scheduling (defer if busy)
   - Multi-lingual callback support
   - Recording and transcription of advisers' answers for AI learning

4. **Escalation SLA:**
   - Target response time: 2 hours
   - Escalation reassignment if no response
   - Callback scheduling based on farmer availability

## Questions & Support

For questions about this implementation:
1. Check commit message: `418855f`
2. Review system prompt section on escalations
3. See escalation_service.py for determination logic
4. Consult escalation_repository.py for schema

---

**Status:** Framework complete, integration and testing in progress  
**Last Updated:** August 12, 2026  
**Next Review:** After HTTP integration and Discord bot implementation
