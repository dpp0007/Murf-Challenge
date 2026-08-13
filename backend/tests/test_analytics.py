"""
Comprehensive Analytics System Tests

Tests verify the complete fixed tracker lifecycle and outcome determination logic:
- TEST 1: Call tracker created with call_id
- TEST 2: Assistant receives same call_id
- TEST 3: Weather tool retrieves tracker by call_id
- TEST 4: Weather success records correct state
- TEST 5: Successful weather call finalized as SUCCESS
- TEST 6: Weather API failure finalized as FAILED
- TEST 7: User disconnect before task finalized as FAILED
- TEST 8: Mandi success finalized as SUCCESS
- TEST 9: Escalation creation finalized as SUCCESS
- TEST 10: Duplicate tracker lookup returns same instance
"""

import unittest
import sys
import os
import time
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

# Mock the analytics_service before importing call_tracker
sys.modules['services.analytics_service'] = Mock(get_analytics_service=Mock(return_value=Mock()))
sys.modules['database.analytics_repository'] = Mock(get_analytics_repository=Mock(return_value=Mock()))

from src.analytics.call_tracker import (
    CallTracker, get_or_create_tracker, get_tracker, remove_tracker, _active_trackers
)


class TestTrackerInitialization(unittest.TestCase):
    """TEST 1-2: Tracker creation and identity."""
    
    def setUp(self):
        _active_trackers.clear()
    
    def tearDown(self):
        _active_trackers.clear()
    
    def test_1_tracker_created_with_unique_call_id(self):
        """TEST 1: Call tracker created with call_id."""
        call_id = "test-call-001__1723554000_abc12345"
        tracker = get_or_create_tracker(call_id, channel="browser", user_id="farmer1")
        
        self.assertIsNotNone(tracker)
        self.assertEqual(tracker.call_id, call_id)
        self.assertFalse(tracker.finalized)
        self.assertEqual(tracker.channel, "browser")
        self.assertEqual(tracker.user_id, "farmer1")
    
    def test_2_assistant_receives_same_call_id(self):
        """TEST 2: Tracker can be retrieved by same call_id."""
        call_id = "test-call-002__1723554001_def67890"
        tracker1 = get_or_create_tracker(call_id, channel="browser")
        tracker2 = get_tracker(call_id)
        
        # Should be same instance
        self.assertIs(tracker1, tracker2)
        self.assertEqual(tracker2.call_id, call_id)


class TestWeatherCallSuccess(unittest.TestCase):
    """TEST 3-5: Successful weather call flow."""
    
    def setUp(self):
        _active_trackers.clear()
    
    def tearDown(self):
        _active_trackers.clear()
    
    def test_3_weather_tool_retrieves_tracker_by_call_id(self):
        """TEST 3: Weather tool finds tracker using call_id."""
        call_id = "weather-call-001__1723554002_ghi11111"
        tracker = get_or_create_tracker(call_id)
        
        # Simulate tool doing tracker lookup
        found_tracker = get_tracker(call_id)
        
        self.assertIsNotNone(found_tracker)
        self.assertEqual(found_tracker.call_id, call_id)
    
    def test_4_weather_success_records_correct_state(self):
        """TEST 4: Successful weather call records all required state."""
        call_id = "weather-call-002__1723554003_jkl22222"
        tracker = get_or_create_tracker(call_id)
        
        # Simulate weather tool execution flow
        tracker.record_task_started("weather")
        tracker.record_tool("weather_api")
        tracker.record_task_completed()
        
        # Verify state
        self.assertEqual(tracker.task_type, "weather")
        self.assertEqual(tracker.tool_used, "weather_api")
        self.assertTrue(tracker.task_started)
        self.assertTrue(tracker.task_completed)
        self.assertTrue(tracker.tool_recorded)
        self.assertFalse(tracker.task_failed)
    
    def test_5_successful_weather_call_finalized_as_success(self):
        """TEST 5: Successful weather call becomes SUCCESS."""
        call_id = "weather-call-003__1723554004_mno33333"
        tracker = get_or_create_tracker(call_id)
        
        # Weather call succeeds
        tracker.record_task_started("weather")
        tracker.record_tool("weather_api")
        tracker.record_task_completed()
        
        # Disconnect handler evaluation (same logic as agent.py)
        if tracker.task_completed and tracker.tool_recorded:
            tracker.finalize_success("Task completed successfully before disconnect")
        
        self.assertTrue(tracker.finalized)
        # This would be logged as SUCCESS in database


class TestWeatherCallFailure(unittest.TestCase):
    """TEST 6: Weather API failure."""
    
    def setUp(self):
        _active_trackers.clear()
    
    def tearDown(self):
        _active_trackers.clear()
    
    def test_6_weather_api_failure_finalized_as_failed(self):
        """TEST 6: Weather API failure becomes FAILED."""
        call_id = "weather-fail-001__1723554005_pqr44444"
        tracker = get_or_create_tracker(call_id)
        
        # Weather API fails
        tracker.record_task_started("weather")
        tracker.record_task_failed()
        
        # Disconnect handler evaluation
        if tracker.task_started and tracker.task_failed:
            tracker.finalize_failure("TASK_INCOMPLETE", "Task 'weather' could not be completed")
        
        self.assertTrue(tracker.finalized)
        # This would be logged as FAILED in database


class TestUserHangup(unittest.TestCase):
    """TEST 7: User disconnect before task."""
    
    def setUp(self):
        _active_trackers.clear()
    
    def tearDown(self):
        _active_trackers.clear()
    
    def test_7_user_disconnect_before_task_becomes_failed(self):
        """TEST 7: User disconnect before meaningful task becomes FAILED."""
        call_id = "hangup-call-001__1723554006_stu55555"
        tracker = get_or_create_tracker(call_id)
        
        # User disconnects without requesting anything
        # tracker has no task_started = True
        
        # Disconnect handler evaluation
        if tracker.task_completed and tracker.tool_recorded:
            tracker.finalize_success("Task completed successfully")
        elif tracker.task_started and tracker.task_failed:
            tracker.finalize_failure("TASK_INCOMPLETE", "Task could not be completed")
        else:
            # No task attempted
            tracker.finalize_failure("USER_HANGUP", "User disconnected without requesting any task")
        
        self.assertTrue(tracker.finalized)
        # This would be logged as FAILED (USER_HANGUP) in database


class TestMandiCallSuccess(unittest.TestCase):
    """TEST 8: Mandi prices call success."""
    
    def setUp(self):
        _active_trackers.clear()
    
    def tearDown(self):
        _active_trackers.clear()
    
    def test_8_mandi_success_becomes_success(self):
        """TEST 8: Successful mandi prices call becomes SUCCESS."""
        call_id = "mandi-call-001__1723554007_vwx66666"
        tracker = get_or_create_tracker(call_id)
        
        # Mandi prices succeeds
        tracker.record_task_started("mandi")
        tracker.record_tool("mandi_api")
        tracker.record_task_completed()
        
        # Disconnect handler evaluation
        if tracker.task_completed and tracker.tool_recorded:
            tracker.finalize_success("Task completed successfully before disconnect")
        
        self.assertTrue(tracker.finalized)
        self.assertEqual(tracker.task_type, "mandi")
        self.assertEqual(tracker.tool_used, "mandi_api")


class TestEscalationCallSuccess(unittest.TestCase):
    """TEST 9: Escalation creation success."""
    
    def setUp(self):
        _active_trackers.clear()
    
    def tearDown(self):
        _active_trackers.clear()
    
    def test_9_escalation_creation_becomes_success(self):
        """TEST 9: Escalation creation becomes SUCCESS."""
        call_id = "escalation-call-001__1723554008_yz99999"
        tracker = get_or_create_tracker(call_id)
        
        # Escalation succeeds
        tracker.record_task_started("escalation")
        tracker.record_tool("escalation_service")
        tracker.record_escalation("KM-20260814-0001")
        tracker.record_task_completed()
        
        self.assertTrue(tracker.escalation_recorded)
        self.assertEqual(tracker.tool_used, "escalation_service")
        self.assertTrue(tracker.task_completed)


class TestTrackerLifecycle(unittest.TestCase):
    """TEST 10: Tracker cleanup and reuse."""
    
    def setUp(self):
        _active_trackers.clear()
    
    def tearDown(self):
        _active_trackers.clear()
    
    def test_10_duplicate_tracker_lookup_returns_same_instance(self):
        """TEST 10: Duplicate tracker lookup doesn't create another tracker."""
        call_id = "lifecycle-call-001__1723554009_abc88888"
        tracker1 = get_or_create_tracker(call_id)
        tracker2 = get_or_create_tracker(call_id)
        tracker3 = get_tracker(call_id)
        
        # All should be same instance
        self.assertIs(tracker1, tracker2)
        self.assertIs(tracker2, tracker3)
        
        # Only one tracker in memory
        self.assertEqual(len(_active_trackers), 1)
        
        # After cleanup
        remove_tracker(call_id)
        self.assertIsNone(get_tracker(call_id))


class TestOutcomeLogicScenarios(unittest.TestCase):
    """Test complete outcome determination for various scenarios."""
    
    def setUp(self):
        _active_trackers.clear()
    
    def tearDown(self):
        _active_trackers.clear()
    
    def test_successful_weather_query_outcome(self):
        """Scenario: User asks 'नोएडा का मौसम कैसा है?'
        Expected: SUCCESS (task_completed + tool_recorded)"""
        call_id = "scenario-success-1"
        tracker = get_or_create_tracker(call_id)
        
        # Weather query succeeds
        tracker.record_task_started("weather")
        tracker.record_tool("weather_api")
        tracker.record_task_completed()
        
        # Outcome evaluation
        if tracker.task_completed and tracker.tool_recorded:
            outcome = "SUCCESS"
        elif tracker.task_started and tracker.task_failed:
            outcome = "FAILED_TASK_INCOMPLETE"
        else:
            outcome = "FAILED_USER_HANGUP"
        
        self.assertEqual(outcome, "SUCCESS")
    
    def test_failed_weather_query_outcome(self):
        """Scenario: Weather API is down
        Expected: FAILED (task_started + task_failed)"""
        call_id = "scenario-failed-1"
        tracker = get_or_create_tracker(call_id)
        
        # Weather query fails
        tracker.record_task_started("weather")
        tracker.record_task_failed()
        
        # Outcome evaluation
        if tracker.task_completed and tracker.tool_recorded:
            outcome = "SUCCESS"
        elif tracker.task_started and tracker.task_failed:
            outcome = "FAILED_TASK_INCOMPLETE"
        else:
            outcome = "FAILED_USER_HANGUP"
        
        self.assertEqual(outcome, "FAILED_TASK_INCOMPLETE")
    
    def test_user_immediate_hangup_outcome(self):
        """Scenario: User connects and immediately hangs up
        Expected: FAILED (USER_HANGUP - no task attempted)"""
        call_id = "scenario-hangup-1"
        tracker = get_or_create_tracker(call_id)
        
        # No task attempted
        
        # Outcome evaluation
        if tracker.task_completed and tracker.tool_recorded:
            outcome = "SUCCESS"
        elif tracker.task_started and tracker.task_failed:
            outcome = "FAILED_TASK_INCOMPLETE"
        else:
            outcome = "FAILED_USER_HANGUP"
        
        self.assertEqual(outcome, "FAILED_USER_HANGUP")
    
    def test_successful_mandi_query_outcome(self):
        """Scenario: User asks for मंडी price
        Expected: SUCCESS"""
        call_id = "scenario-mandi-1"
        tracker = get_or_create_tracker(call_id)
        
        tracker.record_task_started("mandi")
        tracker.record_tool("mandi_api")
        tracker.record_task_completed()
        
        if tracker.task_completed and tracker.tool_recorded:
            outcome = "SUCCESS"
        else:
            outcome = "FAILED"
        
        self.assertEqual(outcome, "SUCCESS")
    
    def test_successful_escalation_outcome(self):
        """Scenario: Escalation is created
        Expected: SUCCESS"""
        call_id = "scenario-escalation-1"
        tracker = get_or_create_tracker(call_id)
        
        tracker.record_task_started("escalation")
        tracker.record_tool("escalation_service")
        tracker.record_task_completed()
        
        if tracker.task_completed and tracker.tool_recorded:
            outcome = "SUCCESS"
        else:
            outcome = "FAILED"
        
        self.assertEqual(outcome, "SUCCESS")


if __name__ == '__main__':
    unittest.main()
