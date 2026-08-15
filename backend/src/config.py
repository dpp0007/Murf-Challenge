"""
Configuration module for Kisan Mitra voice assistant.
All configurable parameters are centralized here.
"""

import os
# Load environment variables from .env.local FIRST
try:
    from dotenv import load_dotenv
    load_dotenv('.env.local')
except ImportError:
    pass

# ========================= ASSISTANT CONFIGURATION =========================
ASSISTANT_NAME = "Kisan Mitra"
AGENT_NAME = "my-agent"

# ========================= GREETING =========================
GREETING_MESSAGE = (
    "नमस्ते! मैं किसान मित्र हूँ। "
    "मैं खेती, फसल, मौसम, खाद और कृषि से जुड़े सवालों में आपकी मदद कर सकती हूँ। "
    "आज मैं आपकी किस प्रकार सहायता कर सकती हूँ?"
)

# ========================= SILENCE HANDLING =========================
# Time in seconds to wait before considering user silence
SILENCE_TIMEOUT = 5.0

# Maximum number of silence reprompts before ending conversation
MAX_SILENCE_RETRIES = 2

# Reprompt messages for silence detection
SILENCE_REPROMPT_1 = (
    "क्या आप मेरी आवाज़ सुन पा रहे हैं? "
    "मैं आपकी मदद के लिए यहाँ हूँ।"
)

SILENCE_REPROMPT_2 = (
    "लगता है अभी आप व्यस्त हैं। "
    "जब चाहें दोबारा बात करिए। "
    "धन्यवाद।"
)

# ========================= VOICE CONFIGURATION =========================
# Main Kisan Mitra - Female voice
TTS_VOICE = "anisha"  # Hindi (India) female voice - Anisha (more natural, supports multiple Indian languages)
TTS_STYLE = "Conversation"  # Natural conversation style with emotion
TTS_TEXT_PACING = True

# Crop Specialist - Male voice (Day 9 feature)
CROP_SPECIALIST_TTS_VOICE = "samar"  # Indian English male voice - Samar
CROP_SPECIALIST_TTS_STYLE = "Conversation"  # Same conversation style
CROP_SPECIALIST_TTS_PACING = True

# Validate MURF API key for voice switching
# If specialist voice switching is needed but MURF_API_KEY is missing, fail early
MURF_API_KEY = os.getenv("MURF_API_KEY", "")
if not MURF_API_KEY:
    import warnings
    warnings.warn(
        "⚠️  WARNING: MURF_API_KEY not set. "
        "Specialist voice switching (Day 9 feature) will be disabled. "
        "Agent will continue in main voice. "
        "To enable specialist voice: Set MURF_API_KEY in .env.local",
        UserWarning
    )

# STT (Speech-to-Text) settings
STT_MODEL = "nova-3"
STT_LANGUAGE = "hi"  # Hindi language support

# LLM settings
LLM_MODEL = "gemini-3.5-flash-lite"

# ========================= LANGUAGE SETTINGS =========================
DEFAULT_LANGUAGE = "hi"  # Hindi
SUPPORTED_LANGUAGES = ["hi", "en"]  # Hindi and English

# ========================= RESPONSE SETTINGS =========================
# Maximum response length in words for voice optimization
MAX_RESPONSE_WORDS = 80

# Minimum sentence length for tokenization
MIN_SENTENCE_LENGTH = 2

# ========================= ESCALATION CONTACTS =========================
EMERGENCY_CONTACTS = {
    "krishi_vigyan_kendra": "Krishi Vigyan Kendra",
    "agriculture_officer": "Agriculture Officer",
    "government_helpline": "Government Helpline"
}

# ========================= LOGGING =========================
# Enable detailed latency logging
ENABLE_LATENCY_LOGGING = True

# ========================= PROMPT CONFIGURATION =========================
# Path to system prompt module
PROMPT_MODULE = "prompts.kisan_prompt"

# ========================= OUTBOUND CALLING (via LiveKit SIP) =========================
# Feature toggle
OUTBOUND_CALL_ENABLED = True

# Call configuration
WEATHER_ALERT_CALL_TIMEOUT = 60  # seconds
WEATHER_ALERT_DEMO_DISTRICT = "Varanasi"

# ========================= SIP CONFIGURATION =========================
# Import SIP configuration module for outbound calling
try:
    from .config.sip_config import SIPConfig, get_sip_config
    sip_config = get_sip_config  # Function reference for compatibility
except ImportError:
    try:
        from src.config.sip_config import SIPConfig, get_sip_config
        sip_config = get_sip_config
    except ImportError:
        # Will be imported by __init__.py instead
        pass
