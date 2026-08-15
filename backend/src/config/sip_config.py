"""
SIP Configuration for outbound calls via Linphone SIP trunk and LiveKit.

Handles:
- SIP credentials from environment
- Configuration validation
- Secure masking for logging
"""

import os
import logging
from typing import Tuple

logger = logging.getLogger("sip_config")


class SIPConfig:
    """
    SIP Configuration for outbound calling via LiveKit SIP Trunk.
    
    Environment variables required:
    - OUTBOUND_CALL_ENABLED: "true" to enable
    - LIVEKIT_URL: LiveKit server URL
    - LIVEKIT_API_KEY: LiveKit API key
    - LIVEKIT_API_SECRET: LiveKit API secret
    - LIVEKIT_SIP_TRUNK_ID: SIP trunk ID in LiveKit
    - LINPHONE_SIP_URI: Linphone SIP URI (e.g., testuser@sip.linphone.org)
    - LINPHONE_SIP_PASSWORD: Linphone SIP password
    """
    
    def __init__(self):
        """Initialize SIP configuration from environment variables."""
        self.outbound_call_enabled = os.getenv("OUTBOUND_CALL_ENABLED", "false").lower() == "true"
        self.livekit_url = os.getenv("LIVEKIT_URL", "")
        self.livekit_api_key = os.getenv("LIVEKIT_API_KEY", "")
        self.livekit_api_secret = os.getenv("LIVEKIT_API_SECRET", "")
        self.livekit_sip_trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID", "")
        self.linphone_sip_uri = os.getenv("LINPHONE_SIP_URI", "")
        self.linphone_sip_password = os.getenv("LINPHONE_SIP_PASSWORD", "")
        self.demo_district = os.getenv("WEATHER_ALERT_DEMO_DISTRICT", "Varanasi")
        self.call_timeout = int(os.getenv("WEATHER_ALERT_CALL_TIMEOUT", "60"))
    
    def is_configured(self) -> bool:
        """
        Check if all required SIP configuration is available.
        
        Returns:
            True if all credentials are set, False otherwise
        """
        if not self.outbound_call_enabled:
            return False
        
        required_fields = [
            self.livekit_url,
            self.livekit_api_key,
            self.livekit_api_secret,
            self.livekit_sip_trunk_id,
            self.linphone_sip_uri,
            self.linphone_sip_password,
        ]
        
        return all(required_fields)
    
    def validate(self) -> Tuple[bool, str]:
        """
        Validate SIP configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.outbound_call_enabled:
            return False, "OUTBOUND_CALL_ENABLED is not set to true"
        
        missing_fields = []
        
        # Core fields needed for outbound calling
        if not self.linphone_sip_uri:
            missing_fields.append("LINPHONE_SIP_URI")
        if not self.linphone_sip_password:
            missing_fields.append("LINPHONE_SIP_PASSWORD")
        
        if missing_fields:
            error_msg = f"Missing SIP configuration: {', '.join(missing_fields)} not set"
            return False, error_msg
        
        return True, ""
    
    def mask_password(self) -> str:
        """
        Return masked SIP password for safe logging.
        
        Returns:
            Masked password string (e.g., "sup***123")
        """
        if not self.linphone_sip_password:
            return "***"
        
        password = self.linphone_sip_password
        if len(password) <= 4:
            return "***"
        
        # Show first 3 and last 3 characters
        return f"{password[:3]}***{password[-3:]}"
    
    def mask_uri(self) -> str:
        """
        Return masked SIP URI for safe logging.
        
        Returns:
            Masked URI string (e.g., "***@sip.linphone.org")
        """
        if not self.linphone_sip_uri:
            return "***@sip.linphone.org"
        
        # Mask the user part, keep the domain
        parts = self.linphone_sip_uri.split("@", 1)
        if len(parts) == 2:
            return f"***@{parts[1]}"
        
        return "***@sip.linphone.org"


# Global SIP config instance
_sip_config_instance = None


def get_sip_config() -> SIPConfig:
    """
    Get or create the global SIP configuration instance.
    
    Returns:
        SIPConfig instance
    """
    global _sip_config_instance
    if _sip_config_instance is None:
        _sip_config_instance = SIPConfig()
    return _sip_config_instance


def reset_sip_config():
    """Reset the global SIP config instance (for testing)."""
    global _sip_config_instance
    _sip_config_instance = None
