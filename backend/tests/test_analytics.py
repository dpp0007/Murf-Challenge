"""
Tests for call analytics system.

Tests:
- Call record creation
- Call record finalization
- Duration calculation
- Success/failure outcomes
- Task type tracking
- Tool usage tracking
- Escalation tracking
- API endpoints
- Summary calculations
- Recent calls queries
"""

import pytest
import asyncio
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.db import get_database
from database.analytics_repository import get_analytics_repository
from services.analytics_service import get_analytics_service
from analytics.call_tracker import get_or_create_tracker

logger = logging.getLogger("test_analytics")


# Fixtures
@pytest.fixture(autouse=True)
def clear_database():
    """Clear all data from the analytics table before each test."""
    import database.db as db_module
    import database.analytics_repository as repo_module
    
    # Reset global instances
    db_module._database_instance = None
    repo_module._analytics_repository_instance = None
    
    # Get a fresh repository (which will create a new DB instance with fresh schema)
    repo = get_analytics_repository()
    
    try:
        # Clear all data from call_analytics table
        db = repo.db
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Drop and recreate the table for a clean slate
        cursor.execute("DROP TABLE IF EXISTS call_analytics")
        cursor.execute("""
            CREATE TABLE call_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT UNIQUE NOT NULL,
                user_id TEXT,
                channel TEXT NOT NULL,
                language TEXT DEFAULT 'hi',
                started_at TEXT NOT NULL,
                connected_at TEXT,
                ended_at TEXT,
                duration_seconds INTEGER,
                outcome TEXT DEFAULT 'IN_PROGRESS',
                outcome_reason TEXT,
                task_type TEXT DEFAULT 'unknown',
                tool_used TEXT,
                escalated INTEGER DEFAULT 0,
                latency_ms INTEGER,
                failure_type TEXT,
                created_at TEXT NOT NULL,
                metadata_json TEXT
            )
        """)
        
        # Recreate indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_analytics_call_id ON call_analytics(call_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_analytics_user_id ON call_analytics(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_analytics_started_at ON call_analytics(started_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_analytics_outcome ON call_analytics(outcome)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_analytics_channel ON call_analytics(channel)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_analytics_task_type ON call_analytics(task_type)")
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.debug(f"Error clearing database: {e}")
    
    yield
    
    # Cleanup after test
    repo_module._analytics_repository_instance = None
    db_module._database_instance = None


@pytest.fixture
def analytics_repo():
    """Get analytics repository for testing."""
    return get_analytics_repository()


@pytest.fixture
def analytics_service():
    """Get analytics service for testing."""
    return get_analytics_service()


# Tests
class TestCallRecordCreation:
    """Test creating call analytics records."""
    
    def test_create_call_record(self, analytics_repo):
        """Test creating a new call record."""
        result = analytics_repo.create_call_record(
            call_id="test-call-1",
            channel="browser",
            user_id="test-user-1",
            language="hi"
        )
        assert result is True
        
        # Verify record exists
        record = analytics_repo.get_call_record("test-call-1")
        assert record is not None
        assert record.call_id == "test-call-1"
        assert record.channel == "browser"
        assert record.user_id == "test-user-1"
        assert record.outcome == "IN_PROGRESS"
    
    def test_duplicate_call_prevention(self, analytics_repo):
        """Test that duplicate call records are prevented."""
        analytics_repo.create_call_record("test-call-2", "sip")
        
        # Try to create duplicate
        result = analytics_repo.create_call_record("test-call-2", "sip")
        assert result is False
    
    def test_create_with_metadata(self, analytics_repo):
        """Test creating call record with metadata."""
        metadata = {"farmer_name": "Ram", "district": "NOIDA"}
        analytics_repo.create_call_record(
            call_id="test-call-3",
            channel="browser",
            metadata=metadata
        )
        
        record = analytics_repo.get_call_record("test-call-3")
        assert record.metadata["farmer_name"] == "Ram"


class TestCallFinalization:
    """Test call finalization (success/failure)."""
    
    def test_finalize_success(self, analytics_repo):
        """Test marking call as successful."""
        analytics_repo.create_call_record("test-success-1", "browser")
        
        result = analytics_repo.finalize_call_success(
            "test-success-1",
            duration_seconds=42,
            outcome_reason="Weather information delivered"
        )
        assert result is True
        
        record = analytics_repo.get_call_record("test-success-1")
        assert record.outcome == "SUCCESS"
        assert record.duration_seconds == 42
        assert record.outcome_reason == "Weather information delivered"
        assert record.ended_at is not None
    
    def test_finalize_failure(self, analytics_repo):
        """Test marking call as failed."""
        analytics_repo.create_call_record("test-failed-1", "sip")
        
        result = analytics_repo.finalize_call_failed(
            "test-failed-1",
            duration_seconds=15,
            failure_type="USER_HANGUP",
            outcome_reason="User ended call before task completion"
        )
        assert result is True
        
        record = analytics_repo.get_call_record("test-failed-1")
        assert record.outcome == "FAILED"
        assert record.failure_type == "USER_HANGUP"
        assert record.duration_seconds == 15
    
    def test_prevent_double_finalization(self, analytics_repo):
        """Test that call cannot be finalized twice."""
        analytics_repo.create_call_record("test-dbl-fin", "browser")
        
        # First finalization
        analytics_repo.finalize_call_success("test-dbl-fin", 30)
        
        # Try second finalization - should not update
        result = analytics_repo.finalize_call_failed(
            "test-dbl-fin", 30, "USER_HANGUP", "Should not update"
        )
        assert result is True  # Returns True but doesn't update
        
        record = analytics_repo.get_call_record("test-dbl-fin")
        assert record.outcome == "SUCCESS"
        assert record.failure_type is None


class TestTaskAndToolTracking:
    """Test recording task types and tool usage."""
    
    def test_record_task_type(self, analytics_repo):
        """Test recording task type."""
        analytics_repo.create_call_record("test-task-1", "browser")
        
        analytics_repo.record_task_type("test-task-1", "weather")
        
        record = analytics_repo.get_call_record("test-task-1")
        assert record.task_type == "weather"
    
    def test_record_tool_used(self, analytics_repo):
        """Test recording tool usage."""
        analytics_repo.create_call_record("test-tool-1", "browser")
        
        analytics_repo.record_tool_used("test-tool-1", "weather_api")
        
        record = analytics_repo.get_call_record("test-tool-1")
        assert record.tool_used == "weather_api"
    
    def test_record_escalation(self, analytics_repo):
        """Test recording escalation."""
        analytics_repo.create_call_record("test-esc-1", "browser")
        
        analytics_repo.record_escalation("test-esc-1", "KM-20260812-0001-ABCD")
        
        record = analytics_repo.get_call_record("test-esc-1")
        assert record.escalated == 1
        assert record.metadata["escalation_reference_id"] == "KM-20260812-0001-ABCD"
    
    def test_record_latency(self, analytics_repo):
        """Test recording latency."""
        analytics_repo.create_call_record("test-lat-1", "browser")
        
        analytics_repo.record_latency("test-lat-1", 1250)
        
        record = analytics_repo.get_call_record("test-lat-1")
        assert record.latency_ms == 1250


class TestSummaryMetrics:
    """Test summary metrics calculation."""
    
    def test_empty_summary(self, analytics_repo):
        """Test summary with no calls."""
        summary = analytics_repo.get_summary()
        assert summary["total_calls"] == 0
        assert summary["successful_calls"] == 0
        assert summary["failed_calls"] == 0
        assert summary["success_rate"] == 0
    
    def test_summary_with_calls(self, analytics_repo):
        """Test summary calculation with mixed calls."""
        # Create 3 successful calls
        for i in range(3):
            analytics_repo.create_call_record(f"success-{i}", "browser")
            analytics_repo.finalize_call_success(f"success-{i}", 30)
        
        # Create 2 failed calls
        for i in range(2):
            analytics_repo.create_call_record(f"failed-{i}", "browser")
            analytics_repo.finalize_call_failed(f"failed-{i}", 15, "USER_HANGUP", "User ended call")
        
        summary = analytics_repo.get_summary()
        assert summary["total_calls"] == 5
        assert summary["successful_calls"] == 3
        assert summary["failed_calls"] == 2
        assert summary["success_rate"] == 60.0  # 3/5 * 100
    
    def test_summary_excludes_in_progress(self, analytics_repo):
        """Test that IN_PROGRESS calls are not counted in summary."""
        analytics_repo.create_call_record("in-progress-1", "browser")
        analytics_repo.finalize_call_success("success-1", 30)
        
        summary = analytics_repo.get_summary()
        assert summary["total_calls"] == 1  # Only the SUCCESS call
        assert summary["successful_calls"] == 1


class TestRecentCalls:
    """Test retrieving recent calls."""
    
    def test_recent_calls_empty(self, analytics_repo):
        """Test getting recent calls with no data."""
        recent = analytics_repo.get_recent_calls(limit=10)
        assert len(recent) == 0
    
    def test_recent_calls_ordered(self, analytics_repo):
        """Test that recent calls are ordered newest first."""
        # Create calls with small delays to ensure ordering
        for i in range(3):
            analytics_repo.create_call_record(f"call-{i}", "browser")
            analytics_repo.finalize_call_success(f"call-{i}", 30)
            time.sleep(0.01)
        
        recent = analytics_repo.get_recent_calls(limit=10)
        assert len(recent) == 3
        # Most recent should be call-2
        assert recent[0].call_id == "call-2"
        assert recent[1].call_id == "call-1"
        assert recent[2].call_id == "call-0"
    
    def test_recent_calls_limit(self, analytics_repo):
        """Test limit parameter."""
        for i in range(5):
            analytics_repo.create_call_record(f"call-limit-{i}", "browser")
            analytics_repo.finalize_call_success(f"call-limit-{i}", 30)
        
        recent = analytics_repo.get_recent_calls(limit=3)
        assert len(recent) == 3


class TestAnalyticsService:
    """Test analytics service."""
    
    def test_service_start_call(self, analytics_service):
        """Test starting a call through service."""
        result = analytics_service.start_call(
            "svc-call-1",
            "browser",
            user_id="user-1",
            language="hi"
        )
        assert result is True
    
    def test_service_invalid_channel(self, analytics_service):
        """Test service rejects invalid channel."""
        result = analytics_service.start_call(
            "bad-channel",
            "invalid_channel"
        )
        assert result is False
    
    def test_service_record_task(self, analytics_service):
        """Test recording task through service."""
        analytics_service.start_call("svc-task-1", "browser")
        analytics_service.record_task("svc-task-1", "weather")
        
        repo = get_analytics_repository()
        record = repo.get_call_record("svc-task-1")
        assert record.task_type == "weather"
    
    def test_service_finalize_success(self, analytics_service):
        """Test successful finalization through service."""
        analytics_service.start_call("svc-success-1", "browser")
        result = analytics_service.finalize_success("svc-success-1", 42)
        assert result is True
        
        repo = get_analytics_repository()
        record = repo.get_call_record("svc-success-1")
        assert record.outcome == "SUCCESS"


class TestCallTracker:
    """Test CallTracker convenience class."""
    
    def test_tracker_creation(self):
        """Test creating a call tracker."""
        from analytics.call_tracker import get_tracker, remove_tracker
        
        tracker = get_or_create_tracker("tracker-1", "browser", "hi")
        assert tracker is not None
        assert tracker.call_id == "tracker-1"
        assert tracker.finalized is False
        
        remove_tracker("tracker-1")
    
    def test_tracker_success_finalization(self):
        """Test finalizing call as success."""
        from analytics.call_tracker import remove_tracker
        
        tracker = get_or_create_tracker("tracker-success", "browser")
        tracker.record_task("weather")
        
        duration = 30
        result = tracker.finalize_success("Weather delivered successfully")
        assert result is True
        assert tracker.finalized is True
        
        # Verify in database
        repo = get_analytics_repository()
        record = repo.get_call_record("tracker-success")
        assert record.outcome == "SUCCESS"
        assert record.task_type == "weather"
        
        remove_tracker("tracker-success")
    
    def test_tracker_prevents_double_finalize(self):
        """Test tracker prevents double finalization."""
        from analytics.call_tracker import remove_tracker
        
        tracker = get_or_create_tracker("tracker-double", "browser")
        tracker.finalize_success("First finalization")
        
        # Try to finalize again
        result = tracker.finalize_success("Second finalization")
        assert result is False
        
        remove_tracker("tracker-double")
    
    def test_tracker_safe_finalize_if_not_done(self):
        """Test safe finalization fallback."""
        from analytics.call_tracker import remove_tracker
        
        tracker = get_or_create_tracker("tracker-safe", "browser")
        # Don't explicitly finalize, let safe_finalize_if_not_done handle it
        tracker.safe_finalize_if_not_done()
        
        assert tracker.finalized is True
        
        # Verify it's marked as unknown failure
        repo = get_analytics_repository()
        record = repo.get_call_record("tracker-safe")
        assert record.outcome == "FAILED"
        assert record.failure_type == "UNKNOWN"
        
        remove_tracker("tracker-safe")


# Performance test
class TestPerformance:
    """Test performance characteristics."""
    
    def test_bulk_create_calls(self, analytics_repo):
        """Test creating many calls."""
        start = time.time()
        
        for i in range(100):
            analytics_repo.create_call_record(f"perf-{i}", "browser")
        
        elapsed = time.time() - start
        print(f"\nCreated 100 calls in {elapsed:.3f}s")
        assert elapsed < 5.0  # Should complete quickly
    
    def test_bulk_finalize_calls(self, analytics_repo):
        """Test finalizing many calls."""
        # Create calls
        for i in range(100):
            analytics_repo.create_call_record(f"fin-{i}", "browser")
        
        start = time.time()
        
        # Finalize them
        for i in range(100):
            analytics_repo.finalize_call_success(f"fin-{i}", 30)
        
        elapsed = time.time() - start
        print(f"\nFinalized 100 calls in {elapsed:.3f}s")
        assert elapsed < 5.0
    
    def test_summary_query_speed(self, analytics_repo):
        """Test summary query speed with many records."""
        # Create 500 records
        for i in range(500):
            analytics_repo.create_call_record(f"summary-{i}", "browser")
            if i % 3 == 0:
                analytics_repo.finalize_call_success(f"summary-{i}", 30)
            else:
                analytics_repo.finalize_call_failed(f"summary-{i}", 15, "USER_HANGUP", "Ended")
        
        start = time.time()
        summary = analytics_repo.get_summary()
        elapsed = time.time() - start
        
        print(f"\nSummary query with 500 records: {elapsed*1000:.1f}ms")
        assert elapsed < 1.0  # Should be very fast with indexes
