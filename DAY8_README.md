# Day 8: Call Analytics & Real-time Dashboard

## Overview

Day 8 implements a **production-ready call analytics system** that tracks all aspects of farmer assistance calls, from initiation through resolution. The system records call outcomes, tool usage, task completion, and escalations—providing real-time visibility into system performance and farmer support quality.

## Key Features Implemented

### 1. Real-time Call Analytics Tracking
- **Call Lifecycle Tracking**: Records every call from initialization through disconnect
- **Task Recording**: Captures what task the farmer performed (weather query, mandi prices, escalation, etc.)
- **Tool Usage Logging**: Records which APIs/tools were successfully invoked
- **Duration Tracking**: Measures call duration and pipeline latency
- **Call Outcomes**: Determines success/failure with specific failure categories

### 2. Outcome Determination Logic
Calls are classified with context-aware logic:
- **SUCCESS**: Tool was successfully recorded (weather/mandi data retrieved, escalation created)
- **FAILED - TASK_INCOMPLETE**: Task started but not completed or API failed
- **FAILED - USER_HANGUP**: User disconnected without initiating any task
- **FAILED - SIP_ERROR**: SIP call failed (for telephony calls)

### 3. Analytics Dashboard (React)
- **Real-time Metrics**: Auto-refreshes every 15 seconds
- **Summary Statistics**: 
  - Total calls
  - Success rate (%)
  - Average call duration
  - Breakdown by channel (browser/SIP)
- **Recent Calls**: Live feed showing latest 20 calls with outcomes
- **Responsive Design**: Works on desktop and mobile

### 4. Analytics API Endpoints
```
GET /api/analytics/summary
- Returns: success_count, failed_count, total_calls, success_rate, avg_duration, channels

GET /api/analytics/recent
- Returns: Array of recent calls with call_id, duration, outcome, user_id, timestamp
```

## Architecture

### Core Components

#### 1. **CallTracker** (`backend/src/analytics/call_tracker.py`)
In-memory tracker for individual call sessions:
- Stores call state during session lifetime
- Records task, tool, and escalation events
- Determines outcomes on disconnect
- Auto-finalizes to ensure clean state

```python
tracker = get_or_create_tracker(
    call_id="room__timestamp_uuid",
    channel="browser|sip",
    language="hi|en",
    user_id="farmer_id"
)
tracker.record_task("weather")
tracker.record_tool("weather_api")
tracker.finalize_success()
```

#### 2. **AnalyticsService** (`backend/src/services/analytics_service.py`)
Business logic layer:
- Evaluates call outcomes with context-aware heuristics
- Routes finalization to repository
- Handles different call types (inbound, outbound weather alerts, escalation callbacks)

#### 3. **AnalyticsRepository** (`backend/src/database/analytics_repository.py`)
Database persistence layer:
- SQLite table: `call_analytics` (18 columns, 7 indexes)
- Stores call metadata, outcomes, metrics
- Efficiently queries calls by date range, outcome, channel

#### 4. **Analytics Routes** (`backend/src/api/analytics_routes.py`)
HTTP API endpoints:
- Summary stats aggregated from database
- Recent calls with pagination support
- Filters by outcome, channel, date range

### Data Flow

```
Call Initiated
    ↓
agent.py creates CallTracker with unique call_id
    ↓
Assistant tools use tracker to record task/tool usage
    ↓
on_participant_disconnect event triggered
    ↓
AnalyticsService evaluates outcome based on:
    - tool_recorded flag
    - task_recorded flag
    - disconnection reason
    ↓
AnalyticsRepository persists to SQLite
    ↓
Dashboard fetches via /api/analytics/summary & /api/analytics/recent
    ↓
Real-time UI updates every 15 seconds
```

## Files Added/Modified

### New Files
```
backend/src/analytics/
  ├── __init__.py
  └── call_tracker.py              # In-memory call state management

backend/src/services/
  └── analytics_service.py         # Outcome determination & business logic

backend/src/database/
  └── analytics_repository.py      # SQLite persistence layer

backend/src/api/
  └── analytics_routes.py          # HTTP endpoints

backend/tests/
  └── test_analytics.py            # Integration tests

frontend/app/analytics/
  └── page.tsx                     # Dashboard React component

frontend/app/api/analytics/
  ├── route.ts                     # Summary endpoint
  ├── recent/route.ts              # Recent calls endpoint
  └── summary/route.ts             # Aggregated stats endpoint
```

### Modified Files

#### `backend/src/agent.py`
- Lines 170-192: **CallTracker initialization**
  - Generates unique `call_id` combining room name + timestamp + UUID
  - Creates tracker with channel detection (browser/SIP)
  - Marks tracker as connected

- Lines 441-500: **Disconnect event handler**
  - Evaluates call outcome using AnalyticsService
  - Finalizes tracker (success or failure)
  - Removes tracker from memory

#### `backend/src/assistant.py`
- Lines 43-65: **Constructor enhanced**
  - Added `call_id` parameter for analytics
  - Stores `self.call_id` for tool methods to access

- Lines 128-185: **get_weather() method**
  - Retrieves tracker using `call_id`
  - Records "weather" task before API call
  - Records "weather_api" tool on success
  - Graceful error handling without call termination

- Lines 220-295: **get_mandi_prices() method**
  - Same analytics pattern as get_weather
  - Records "mandi" task
  - Records "mandi_api" tool on success

- Lines 435-565: **create_escalation() method**
  - Records escalation task and reference ID
  - Handles finalization for invalid/failed escalations
  - Maintains call session on escalation error

#### `backend/src/api/http_server.py`
- Added `/api/analytics/*` route registration

#### `backend/src/database/db.py`
- Added database initialization for `call_analytics` table

## Bug Fixes Applied

### Critical Bug #1: Tracker Lookup Failure
**Problem**: Tools searched for trackers by `room_name` but trackers were stored by unique `call_id`
**Result**: Tracker always returned None, tools couldn't record themselves
**Fix**: 
- Pass `call_id` to assistant constructor
- Update tool methods to use `get_tracker(self.call_id)`
- Ensure tracker lookup succeeds

### Critical Bug #2: Incorrect Outcome Determination
**Problem**: All calls marked FAILED because disconnect handler only checked `tool_recorded` flag (always False due to Bug #1)
**Result**: Even successful weather queries showed as FAILED in analytics
**Fix**:
- Implement context-aware outcome logic
- Check `task_recorded` separately (incomplete tasks)
- Distinguish user hangup from API failures
- Record actual success when tools are recorded

### Minor Improvements
- Silent log suppression for noisy LiveKit debug messages
- Better error messages for analytics recording failures
- Graceful handling of tracker not found scenarios

## Testing

### Unit Tests
```bash
cd backend
python -m pytest tests/test_analytics.py -v
```

### Manual Integration Testing
1. Make a browser call requesting weather
2. Check database: `SELECT * FROM call_analytics ORDER BY created_at DESC LIMIT 1`
3. Verify: `outcome="SUCCESS"`, `tool_recorded=1`, `task_type="weather"`
4. Visit dashboard: http://localhost:3000/analytics
5. See updated metrics in real-time

## Database Schema

```sql
CREATE TABLE call_analytics (
  call_id TEXT PRIMARY KEY,
  user_id TEXT,
  channel TEXT,          -- "browser" or "sip"
  language TEXT,         -- "hi" or "en"
  task_type TEXT,        -- "weather", "mandi", "escalation", etc.
  tool_name TEXT,        -- "weather_api", "mandi_api", etc.
  escalation_ref_id TEXT,-- Reference ID if escalation created
  start_time REAL,       -- Unix timestamp when call started
  connected_time REAL,   -- Unix timestamp when participant connected
  end_time REAL,         -- Unix timestamp when call ended
  duration_seconds INT,  -- Total call duration
  outcome TEXT,          -- "SUCCESS" or "FAILED"
  failure_type TEXT,     -- "TASK_INCOMPLETE", "USER_HANGUP", "SIP_ERROR", etc.
  failure_reason TEXT,   -- Human-readable reason
  latency_ms INT,        -- Pipeline latency if recorded
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX idx_outcome ON call_analytics(outcome);
CREATE INDEX idx_channel ON call_analytics(channel);
CREATE INDEX idx_user_id ON call_analytics(user_id);
CREATE INDEX idx_task_type ON call_analytics(task_type);
CREATE INDEX idx_created_at ON call_analytics(created_at);
CREATE INDEX idx_date ON call_analytics(DATE(created_at));
CREATE INDEX idx_escalation_ref ON call_analytics(escalation_ref_id);
```

## Configuration

No additional configuration needed. The system auto-initializes on first call:
- Creates SQLite table if missing
- Creates indexes for performance
- Starts tracking automatically

## Known Limitations

1. **In-Memory Tracker Storage**: Trackers stored in Python dict, lost on process restart
   - Mitigation: Quick finalization on disconnect ensures data persists to database

2. **Single-Process Analytics**: Each call has one session
   - Works for current architecture, may need refactoring for multi-process deployments

3. **Real-time Dashboard**: 15-second refresh interval (not true WebSocket streaming)
   - Sufficient for current use case, can be enhanced with Socket.io if needed

## Production Readiness Checklist

- ✅ Database schema defined and tested
- ✅ API endpoints implemented and documented
- ✅ Dashboard UI functional and responsive
- ✅ Error handling for tracker not found
- ✅ Call lifecycle properly managed
- ✅ Outcome determination context-aware
- ✅ No data loss on call failure
- ✅ Performance optimized with indexes
- ⏳ Integration testing pending (run real calls to verify)

## Next Steps

1. Deploy day-8 branch to staging/production
2. Make test calls (browser and SIP)
3. Verify dashboard shows correct metrics
4. Monitor logs for any analytics errors
5. Celebrate! 🎉

## Support

For issues or questions about analytics:
1. Check logs: `[Analytics]` log lines show detailed tracking info
2. Verify database: Query `call_analytics` table directly
3. Test tracker: Make calls with known parameters and verify records
