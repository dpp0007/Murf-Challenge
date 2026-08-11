"""
Response post-processing utilities for voice optimization.
Ensures all LLM responses are clean and suitable for TTS output.
Includes Hindi speech normalization for natural pronunciation.
"""

import re
import logging

logger = logging.getLogger("response_processor")

# Import Hindi speech normalization
try:
    from .hindi_speech import optimize_for_murf_tts, is_hindi_text
except ImportError:
    from hindi_speech import optimize_for_murf_tts, is_hindi_text


def clean_response_for_voice(text: str) -> str:
    """
    Clean LLM response to make it voice-friendly.
    
    Removes:
    - Markdown formatting (* ** # etc.)
    - Bullet points (• - *)
    - Numbered lists (1. 2. 3.)
    - Emojis
    - Special brackets and formatting
    - Code blocks
    - JSON structures
    
    For Hindi text, also applies speech normalization for natural pronunciation.
    
    Args:
        text: Raw response from LLM
    
    Returns:
        Cleaned text suitable for voice synthesis
    """
    if not text:
        return text
    
    original_text = text
    
    # Remove markdown headers (# ## ###)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Remove markdown bold/italic (* ** _)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
    
    # Remove bullet points at start of lines
    text = re.sub(r'^\s*[•\-\*]\s+', '', text, flags=re.MULTILINE)
    
    # Remove numbered lists (1. 2. 3.)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Remove emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    
    # Remove code blocks (```...```)
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove special brackets used in structured responses
    text = re.sub(r'\[([^\]]+)\]', r'\1', text)  # [text] -> text
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove multiple newlines (keep at most one)
    text = re.sub(r'\n\s*\n+', '\n', text)
    
    # Clean up whitespace
    text = text.strip()
    
    # Apply Hindi speech normalization for natural pronunciation
    if is_hindi_text(text):
        text = optimize_for_murf_tts(text)
        logger.debug("Applied Hindi speech normalization")
    
    # Log if significant cleaning occurred
    if len(original_text) - len(text) > 20:
        logger.debug(f"Cleaned response: removed {len(original_text) - len(text)} characters")
    
    return text


def split_into_sentences(text: str, max_length: int = 100) -> list[str]:
    """
    Split text into shorter sentences for better voice pacing.
    
    Args:
        text: Input text
        max_length: Maximum character length per chunk
    
    Returns:
        List of sentence chunks
    """
    # Split on natural boundaries
    sentences = re.split(r'[।.!?]\s+', text)
    
    result = []
    for sentence in sentences:
        if sentence.strip():
            # If sentence is too long, split on commas
            if len(sentence) > max_length:
                parts = sentence.split(',')
                result.extend([p.strip() + ',' for p in parts if p.strip()])
            else:
                result.append(sentence.strip())
    
    return result


def detect_language_style(text: str) -> str:
    """
    Detect the language style of user input.
    
    Returns:
        'hi' for Hindi/Devanagari
        'en' for English
        'mixed' for Hinglish (mixed)
    """
    # Check for Devanagari characters
    has_devanagari = bool(re.search(r'[\u0900-\u097F]', text))
    
    # Check for English letters
    has_english = bool(re.search(r'[a-zA-Z]', text))
    
    if has_devanagari and has_english:
        return 'mixed'
    elif has_devanagari:
        return 'hi'
    elif has_english:
        return 'en'
    else:
        return 'mixed'


def count_words(text: str) -> int:
    """
    Count words in text (works for both English and Hindi).
    
    Args:
        text: Input text
    
    Returns:
        Approximate word count
    """
    # Split on whitespace
    words = text.split()
    return len(words)


def truncate_response(text: str, max_words: int = 80) -> str:
    """
    Truncate response to maximum word count while keeping sentences intact.
    
    Args:
        text: Input text
        max_words: Maximum number of words
    
    Returns:
        Truncated text
    """
    words = text.split()
    
    if len(words) <= max_words:
        return text
    
    # Find last sentence boundary within limit
    truncated = ' '.join(words[:max_words])
    
    # Try to end at a sentence boundary
    last_period = max(
        truncated.rfind('.'),
        truncated.rfind('।'),
        truncated.rfind('?'),
        truncated.rfind('!')
    )
    
    if last_period > len(truncated) * 0.7:  # If we're at least 70% through
        return truncated[:last_period + 1]
    
    return truncated + '...'
