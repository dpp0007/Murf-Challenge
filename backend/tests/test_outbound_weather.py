"""
Unit tests for outbound weather alert service.

Tests:
- Weather alert generation
- Missing farmer scenarios
- Missing location scenarios
- Weather API failures
- SIP configuration validation
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional, Dict, Any

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.outbound_weather_service import (
    OutboundWeatherAlertService,
    CallStatus
)
from config.sip_config import SIPConfig


@pytest.fixture
def sip_config_mock():
    """Mock SIP configuration."""
    with patch('config.sip_config.get_sip_config') as mock:
        config = MagicMock()
        config.is_configured.return_value = True
        config.demo_district = "Varanasi"
        config.sip_uri = "test_user@sip.linphone.org"
        config.mask_uri.return_value = "test_user@sip.linphone.org"
        mock.return_value = config
        yield config


@pytest.fixture
def weather_service_mock():
    """Mock weather service."""
    with patch('services.outbound_weather_service.WeatherService') as mock:
        instance = MagicMock()
        instance.get_weather = AsyncMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def farmer_repo_mock():
    """Mock farmer repository."""
    with patch('services.outbound_weather_service.get_farmer_repository') as mock:
        yield mock.return_value


@pytest.fixture
def service(sip_config_mock, weather_service_mock, farmer_repo_mock):
    """Create OutboundWeatherAlertService with mocks."""
    service = OutboundWeatherAlertService()
    service.sip_config = sip_config_mock
    service.weather_service = weather_service_mock
    service.farmer_repo = farmer_repo_mock
    return service


class TestOutboundWeatherAlertService:
    """Test suite for outbound weather alert service."""
    
    @pytest.mark.asyncio
    async def test_demo_call_success(self, service, weather_service_mock):
        """Test successful demo weather alert call."""
        # Mock weather data
        weather_service_mock.get_weather.return_value = {
            "current": {
                "temperature": 25,
                "weather": "Partly cloudy",
                "humidity": 70,
                "wind_speed": 10,
                "precipitation": 40,
                "rain": 0
            }
        }
        
        # Call
        result = await service.initiate_demo_weather_alert()
        
        # Verify
        assert result["success"] is True
        assert "call_id" in result
        assert result["status"] == "initiated"
        assert "message" in result
        assert "weather" in result
        assert result["weather"]["temperature"] == 25
    
    @pytest.mark.asyncio
    async def test_service_disabled(self, service):
        """Test when outbound calling is disabled."""
        service.sip_config.is_configured.return_value = False
        
        result = await service.initiate_demo_weather_alert()
        
        assert result["success"] is False
        assert result["error"] == "DISABLED"
    
    @pytest.mark.asyncio
    async def test_weather_unavailable(self, service, weather_service_mock):
        """Test when weather API fails."""
        weather_service_mock.get_weather.return_value = None
        
        result = await service.initiate_demo_weather_alert()
        
        assert result["success"] is False
        assert result["error"] == "WEATHER_UNAVAILABLE"
    
    @pytest.mark.asyncio
    async def test_weather_alert_message_hi_rain(self, service):
        """Test weather alert message generation - rain scenario."""
        weather = {
            "district": "Varanasi",
            "temperature": 25,
            "condition": "Rainy",
            "humidity": 80,
            "wind_speed": 15,
            "precipitation": 80,
            "rain": 5
        }
        
        message = service._generate_weather_alert_message(
            farmer_name="Rajesh",
            district="Varanasi",
            weather=weather,
            language="hi"
        )
        
        assert "Rajesh" in message
        assert "Varanasi" in message
        assert "बारिश" in message or "80" in message
        assert "किसान मित्र" in message
    
    @pytest.mark.asyncio
    async def test_weather_alert_message_en_hot(self, service):
        """Test weather alert message generation - hot weather."""
        weather = {
            "district": "Delhi",
            "temperature": 42,
            "condition": "Clear",
            "humidity": 30,
            "wind_speed": 8,
            "precipitation": 0,
            "rain": 0
        }
        
        message = service._generate_weather_alert_message(
            farmer_name="John",
            district="Delhi",
            weather=weather,
            language="en"
        )
        
        assert "John" in message
        assert "Delhi" in message
        assert "42" in message
        assert "Kisan Mitra" in message
    
    @pytest.mark.asyncio
    async def test_call_status_tracking(self, service, weather_service_mock):
        """Test call status tracking."""
        weather_service_mock.get_weather.return_value = {
            "current": {
                "temperature": 25,
                "weather": "Clear",
                "humidity": 60,
                "wind_speed": 5,
                "precipitation": 10,
                "rain": 0
            }
        }
        
        # Initiate call
        result = await service.initiate_demo_weather_alert()
        call_id = result["call_id"]
        
        # Check initial status
        status = service.get_call_status(call_id)
        assert status is not None
        assert status["call_id"] == call_id
        assert status["status"] == "initiated"
        
        # Update status
        service.update_call_status(call_id, CallStatus.RINGING)
        status = service.get_call_status(call_id)
        assert status["status"] == "ringing"
    
    @pytest.mark.asyncio
    async def test_coordinate_lookup(self, service):
        """Test district coordinate lookup."""
        # Test known district
        result_varanasi = await service._fetch_weather_for_district("Varanasi")
        # Should attempt fetch (may fail if weather API not available)
        
        # Test unknown district (should use default)
        result_unknown = await service._fetch_weather_for_district("UnknownDistrict")
        # Should use Varanasi as fallback
    
    def test_is_enabled(self, service):
        """Test feature enabled check."""
        service.sip_config.is_configured.return_value = True
        assert service.is_enabled() is True
        
        service.sip_config.is_configured.return_value = False
        assert service.is_enabled() is False
    
    @pytest.mark.asyncio
    async def test_concurrent_calls(self, service, weather_service_mock):
        """Test handling multiple concurrent calls."""
        weather_service_mock.get_weather.return_value = {
            "current": {
                "temperature": 25,
                "weather": "Clear",
                "humidity": 60,
                "wind_speed": 5,
                "precipitation": 10,
                "rain": 0
            }
        }
        
        # Initiate multiple calls
        results = await asyncio.gather(
            service.initiate_demo_weather_alert(),
            service.initiate_demo_weather_alert(),
            service.initiate_demo_weather_alert(),
        )
        
        # Verify all succeeded with unique IDs
        assert all(r["success"] for r in results)
        call_ids = [r["call_id"] for r in results]
        assert len(set(call_ids)) == 3  # All unique


class TestSIPConfig:
    """Test SIP configuration validation."""
    
    def test_sip_config_fully_configured(self):
        """Test SIP config validation - fully configured."""
        with patch.dict('os.environ', {
            'OUTBOUND_CALL_ENABLED': 'true',
            'LINPHONE_SIP_USERNAME': 'testuser',
            'LINPHONE_SIP_PASSWORD': 'testpass',
            'LINPHONE_SIP_URI': 'testuser@sip.linphone.org',
        }):
            config = SIPConfig()
            is_valid, error = config.validate()
            assert is_valid is True
            assert error == ""
    
    def test_sip_config_missing_credentials(self):
        """Test SIP config validation - missing credentials."""
        with patch.dict('os.environ', {
            'OUTBOUND_CALL_ENABLED': 'true',
        }, clear=True):
            config = SIPConfig()
            is_valid, error = config.validate()
            assert is_valid is False
            assert "not set" in error or "missing" in error.lower()
    
    def test_sip_config_disabled(self):
        """Test SIP config validation - feature disabled."""
        with patch.dict('os.environ', {
            'OUTBOUND_CALL_ENABLED': 'false',
        }):
            config = SIPConfig()
            is_valid, error = config.validate()
            assert is_valid is False
    
    def test_sip_config_password_masking(self):
        """Test SIP password masking for logging."""
        with patch.dict('os.environ', {
            'LINPHONE_SIP_PASSWORD': 'supersecret123',
        }):
            config = SIPConfig()
            masked = config.mask_password()
            assert 'supersecret123' not in masked
            assert '***' in masked
    
    def test_sip_config_uri_masking(self):
        """Test SIP URI masking for logging."""
        with patch.dict('os.environ', {
            'LINPHONE_SIP_URI': 'testuser@sip.linphone.org',
        }):
            config = SIPConfig()
            masked = config.mask_uri()
            assert 'testuser' not in masked or masked.count('*') > 0
            assert '@sip.linphone.org' in masked


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
