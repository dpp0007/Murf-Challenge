"""
Configuration module for Kisan Mitra voice assistant.
All configurable parameters are centralized here.
"""

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
# Murf TTS voice settings
TTS_VOICE = "anisha"  # Hindi (India) female voice - Anisha (more natural, supports multiple Indian languages)
TTS_STYLE = "Conversation"  # Natural conversation style with emotion
TTS_TEXT_PACING = True

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
