"""
Hindi speech normalization for natural pronunciation with Murf TTS.

Converts technical text, numbers, and measurements into 
natural spoken Hindi suitable for voice synthesis.
"""

import re
import logging

logger = logging.getLogger("hindi_speech")


# Number word mappings in Hindi
ONES = [
    "", "एक", "दो", "तीन", "चार", "पांच", "छह", "सात", "आठ", "नौ"
]

TENS = [
    "", "", "बीस", "तीस", "चालीस", "पचास", "साठ", "सत्तर", "अस्सी", "नब्बे"
]

TEENS = [
    "दस", "ग्यारह", "बारह", "तेरह", "चौदह", "पंद्रह",
    "सोलह", "सत्रह", "अठारह", "उन्नीस"
]

TWENTY_TO_HUNDRED = {
    21: "इक्कीस", 22: "बाईस", 23: "तेईस", 24: "चौबीस", 25: "पच्चीस",
    26: "छब्बीस", 27: "सत्ताईस", 28: "अट्ठाईस", 29: "उनतीस",
    31: "इकतीस", 32: "बत्तीस", 33: "तैंतीस", 34: "चौंतीस", 35: "पैंतीस",
    36: "छत्तीस", 37: "सैंतीस", 38: "अड़तीस", 39: "उनतालीस",
    41: "इकतालीस", 42: "बयालीस", 43: "तैंतालीस", 44: "चौवालीस", 45: "पैंतालीस",
    46: "छियालीस", 47: "सैंतालीस", 48: "अड़तालीस", 49: "उनचास",
    51: "इक्यावन", 52: "बावन", 53: "तिरपन", 54: "चौवन", 55: "पचपन",
    56: "छप्पन", 57: "सत्तावन", 58: "अट्ठावन", 59: "उनसठ",
    61: "इकसठ", 62: "बासठ", 63: "तिरसठ", 64: "चौंसठ", 65: "पैंसठ",
    66: "छियासठ", 67: "सड़सठ", 68: "अड़सठ", 69: "उनहत्तर",
    71: "इकहत्तर", 72: "बहत्तर", 73: "तिहत्तर", 74: "चौहत्तर", 75: "पचहत्तर",
    76: "छिहत्तर", 77: "सतहत्तर", 78: "अठहत्तर", 79: "उन्यासी",
    81: "इक्यासी", 82: "बयासी", 83: "तिरासी", 84: "चौरासी", 85: "पचासी",
    86: "छियासी", 87: "सत्तासी", 88: "अट्ठासी", 89: "नवासी",
    91: "इक्यानवे", 92: "बानवे", 93: "तिरानवे", 94: "चौरानवे", 95: "पचानवे",
    96: "छियानवे", 97: "सत्तानवे", 98: "अट्ठानवे", 99: "निन्यानवे"
}


def number_to_hindi_words(num: float) -> str:
    """
    Convert a number to Hindi words.
    
    Args:
        num: Number to convert (can be float for decimals)
    
    Returns:
        Hindi word representation
    """
    try:
        # Handle negative
        if num < 0:
            return f"माइनस {number_to_hindi_words(abs(num))}"
        
        # Handle decimal
        if isinstance(num, float) and num != int(num):
            integer_part = int(num)
            decimal_part = int(round((num - integer_part) * 10))
            if decimal_part > 0:
                return f"{number_to_hindi_words(integer_part)} दशमलव {number_to_hindi_words(decimal_part)}"
            return number_to_hindi_words(integer_part)
        
        num = int(num)
        
        # 0
        if num == 0:
            return "शून्य"
        
        # 1-9
        if num < 10:
            return ONES[num]
        
        # 10-19
        if num < 20:
            return TEENS[num - 10]
        
        # 20-99 (use lookup table)
        if num < 100:
            if num in TWENTY_TO_HUNDRED:
                return TWENTY_TO_HUNDRED[num]
            # Fallback for exact tens
            return TENS[num // 10]
        
        # 100-999
        if num < 1000:
            hundreds = num // 100
            remainder = num % 100
            result = f"{ONES[hundreds]} सौ"
            if remainder > 0:
                result += f" {number_to_hindi_words(remainder)}"
            return result
        
        # 1000-99999
        if num < 100000:
            thousands = num // 1000
            remainder = num % 1000
            result = f"{number_to_hindi_words(thousands)} हज़ार"
            if remainder > 0:
                result += f" {number_to_hindi_words(remainder)}"
            return result
        
        # 100000+ (lakh)
        lakhs = num // 100000
        remainder = num % 100000
        result = f"{number_to_hindi_words(lakhs)} लाख"
        if remainder > 0:
            result += f" {number_to_hindi_words(remainder)}"
        return result
        
    except Exception as e:
        logger.warning(f"Could not convert number {num} to Hindi: {e}")
        return str(num)


def normalize_temperature(text: str) -> str:
    """
    Convert temperature values to natural Hindi.
    
    Examples:
        "32°C" → "बत्तीस डिग्री"
        "Temperature: 25°C" → "तापमान पच्चीस डिग्री"
    """
    # Match patterns like "32°C" or "32 °C" or "32°"
    pattern = r'(\d+(?:\.\d+)?)\s*°[CFcf]?'
    
    def replace_temp(match):
        temp = float(match.group(1))
        temp_words = number_to_hindi_words(temp)
        return f"{temp_words} डिग्री"
    
    return re.sub(pattern, replace_temp, text)


def normalize_percentage(text: str) -> str:
    """
    Convert percentages to natural Hindi.
    
    Examples:
        "70%" → "सत्तर प्रतिशत"
        "80 %" → "अस्सी प्रतिशत"
    """
    pattern = r'(\d+(?:\.\d+)?)\s*%'
    
    def replace_percent(match):
        num = float(match.group(1))
        num_words = number_to_hindi_words(num)
        return f"{num_words} प्रतिशत"
    
    return re.sub(pattern, replace_percent, text)


def normalize_numbers(text: str) -> str:
    """
    Convert standalone numbers to Hindi words where appropriate.
    
    Only converts numbers that appear in speech contexts,
    not in technical identifiers or codes.
    """
    # Match numbers that are standalone or followed by common units
    pattern = r'\b(\d+(?:\.\d+)?)\s*(किमी|मीटर|हेक्टेयर|क्विंटल|किलो|ग्राम|लीटर)?\b'
    
    def replace_num(match):
        num = float(match.group(1))
        unit = match.group(2) or ""
        
        # Skip very large numbers (likely IDs/codes)
        if num > 10000:
            return match.group(0)
        
        num_words = number_to_hindi_words(num)
        if unit:
            return f"{num_words} {unit}"
        return num_words
    
    return re.sub(pattern, replace_num, text)


def normalize_weather_conditions(text: str) -> str:
    """
    Ensure weather conditions are in proper Hindi without technical terms.
    
    Common weather API responses use English technical terms.
    Convert them to natural Hindi.
    """
    replacements = {
        # Keep these as-is since they're already in natural Hindi
        # Just ensure no English weather terms slip through
        "clear sky": "साफ़ आसमान",
        "partly cloudy": "कुछ बादल",
        "cloudy": "बादल",
        "overcast": "घने बादल",
        "rain": "बारिश",
        "light rain": "हल्की बारिश",
        "heavy rain": "भारी बारिश",
        "thunderstorm": "आंधी-तूफान",
        "fog": "कोहरा",
        "mist": "धुंध",
    }
    
    result = text
    for eng, hindi in replacements.items():
        # Case insensitive replacement
        result = re.sub(eng, hindi, result, flags=re.IGNORECASE)
    
    return result


def remove_technical_markers(text: str) -> str:
    """
    Remove technical markers, JSON field names, and code artifacts.
    
    Examples:
        "temperature: 32" → "32"
        "[INFO]" → ""
        "district=Varanasi" → "Varanasi"
    """
    # Remove field names with colons
    text = re.sub(r'\b\w+\s*:\s*', '', text)
    
    # Remove log markers
    text = re.sub(r'\[[\w\s]+\]', '', text)
    
    # Remove key=value patterns
    text = re.sub(r'\b\w+=', '', text)
    
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    
    # Remove markdown
    text = re.sub(r'[*_`#]', '', text)
    
    return text


def optimize_for_murf_tts(text: str) -> str:
    """
    Main function to optimize Hindi text for natural Murf TTS pronunciation.
    
    Applies all normalization steps in proper order:
    1. Remove technical artifacts
    2. Normalize temperatures
    3. Normalize percentages  
    4. Normalize weather conditions
    5. Normalize remaining numbers (carefully)
    6. Clean up extra spaces
    
    Args:
        text: Raw Hindi text with numbers, symbols, technical terms
    
    Returns:
        Optimized text suitable for natural speech synthesis
    """
    if not text:
        return text
    
    original = text
    
    # Step 1: Remove technical markers
    text = remove_technical_markers(text)
    
    # Step 2: Normalize temperature (must come before general numbers)
    text = normalize_temperature(text)
    
    # Step 3: Normalize percentages
    text = normalize_percentage(text)
    
    # Step 4: Normalize weather conditions to Hindi
    text = normalize_weather_conditions(text)
    
    # Step 5: Normalize remaining numbers (careful with this)
    # Only do this for numbers in clear speech contexts
    # Skip for now to avoid over-normalization - can enable if needed
    # text = normalize_numbers(text)
    
    # Step 6: Clean up spaces
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Log if significant changes
    if original != text:
        logger.debug(f"Speech normalization: {len(original)} → {len(text)} chars")
    
    return text


def is_hindi_text(text: str) -> bool:
    """
    Check if text contains Hindi/Devanagari characters.
    
    Returns:
        True if text has Devanagari script
    """
    return bool(re.search(r'[\u0900-\u097F]', text))


def normalize_for_speech(text: str, language: str = "hi") -> str:
    """
    Normalize text for speech based on language.
    
    Args:
        text: Input text
        language: Language code (hi/en)
    
    Returns:
        Speech-optimized text
    """
    if language == "hi" or is_hindi_text(text):
        return optimize_for_murf_tts(text)
    
    # For English, just basic cleanup
    return remove_technical_markers(text)
