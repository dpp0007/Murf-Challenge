"""Configuration modules - re-export from parent config.py for backward compatibility."""

# Import directly from the sibling config.py module
import importlib.util
from pathlib import Path

# Load config.py as a module directly to avoid naming conflicts
config_file = Path(__file__).parent.parent / "config.py"
spec = importlib.util.spec_from_file_location("_config_module", config_file)
_config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_config_module)

# Re-export all configuration from config.py
AGENT_NAME = _config_module.AGENT_NAME
ASSISTANT_NAME = _config_module.ASSISTANT_NAME
GREETING_MESSAGE = _config_module.GREETING_MESSAGE
SILENCE_TIMEOUT = _config_module.SILENCE_TIMEOUT
MAX_SILENCE_RETRIES = _config_module.MAX_SILENCE_RETRIES
SILENCE_REPROMPT_1 = _config_module.SILENCE_REPROMPT_1
SILENCE_REPROMPT_2 = _config_module.SILENCE_REPROMPT_2
TTS_VOICE = _config_module.TTS_VOICE
TTS_STYLE = _config_module.TTS_STYLE
TTS_TEXT_PACING = _config_module.TTS_TEXT_PACING
# Day 9 Specialist Voice Configuration
CROP_SPECIALIST_TTS_VOICE = _config_module.CROP_SPECIALIST_TTS_VOICE
CROP_SPECIALIST_TTS_STYLE = _config_module.CROP_SPECIALIST_TTS_STYLE
CROP_SPECIALIST_TTS_PACING = _config_module.CROP_SPECIALIST_TTS_PACING
MURF_API_KEY = _config_module.MURF_API_KEY
STT_MODEL = _config_module.STT_MODEL
STT_LANGUAGE = _config_module.STT_LANGUAGE
LLM_MODEL = _config_module.LLM_MODEL
DEFAULT_LANGUAGE = _config_module.DEFAULT_LANGUAGE
SUPPORTED_LANGUAGES = _config_module.SUPPORTED_LANGUAGES
MAX_RESPONSE_WORDS = _config_module.MAX_RESPONSE_WORDS
MIN_SENTENCE_LENGTH = _config_module.MIN_SENTENCE_LENGTH
EMERGENCY_CONTACTS = _config_module.EMERGENCY_CONTACTS
ENABLE_LATENCY_LOGGING = _config_module.ENABLE_LATENCY_LOGGING
PROMPT_MODULE = _config_module.PROMPT_MODULE
OUTBOUND_CALL_ENABLED = _config_module.OUTBOUND_CALL_ENABLED
WEATHER_ALERT_CALL_TIMEOUT = _config_module.WEATHER_ALERT_CALL_TIMEOUT
WEATHER_ALERT_DEMO_DISTRICT = _config_module.WEATHER_ALERT_DEMO_DISTRICT

# Import SIP configuration module
from .sip_config import SIPConfig, get_sip_config

__all__ = [
    "AGENT_NAME",
    "ASSISTANT_NAME",
    "GREETING_MESSAGE",
    "SILENCE_TIMEOUT",
    "MAX_SILENCE_RETRIES",
    "SILENCE_REPROMPT_1",
    "SILENCE_REPROMPT_2",
    "TTS_VOICE",
    "TTS_STYLE",
    "TTS_TEXT_PACING",
    "CROP_SPECIALIST_TTS_VOICE",
    "CROP_SPECIALIST_TTS_STYLE",
    "CROP_SPECIALIST_TTS_PACING",
    "MURF_API_KEY",
    "STT_MODEL",
    "STT_LANGUAGE",
    "LLM_MODEL",
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "MAX_RESPONSE_WORDS",
    "MIN_SENTENCE_LENGTH",
    "EMERGENCY_CONTACTS",
    "ENABLE_LATENCY_LOGGING",
    "PROMPT_MODULE",
    "OUTBOUND_CALL_ENABLED",
    "WEATHER_ALERT_CALL_TIMEOUT",
    "WEATHER_ALERT_DEMO_DISTRICT",
    "SIPConfig",
    "get_sip_config",
]
