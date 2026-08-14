"""
Test suite for Gemini API to detect rate limits, quota issues, and response failures.

This test suite checks:
1. API connectivity and authentication
2. Rate limiting (429 errors)
3. Quota exhaustion (403 errors)
4. Response generation failures (no response)
5. Token limit issues
6. Response quality and structure
"""

import os
import asyncio
import time
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import Mock, patch, AsyncMock
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import Gemini components
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    logger.error("google.generativeai not installed. Run: pip install google-generativeai")
    genai = None

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


class TestGeminiAPIBasics:
    """Test basic Gemini API connectivity and configuration."""

    def test_api_key_configured(self):
        """Check if Google API key is configured."""
        assert GOOGLE_API_KEY is not None, "GOOGLE_API_KEY not set in environment"
        assert len(GOOGLE_API_KEY) > 0, "GOOGLE_API_KEY is empty"
        logger.info(f"✅ API Key configured: {GOOGLE_API_KEY[:20]}...")

    def test_gemini_library_available(self):
        """Check if google.generativeai is installed."""
        assert genai is not None, "google.generativeai library not installed"
        logger.info("✅ google.generativeai library available")

    def test_api_initialization(self):
        """Test Gemini API initialization."""
        if genai is None:
            pytest.skip("google.generativeai not installed")
        
        try:
            genai.configure(api_key=GOOGLE_API_KEY)
            logger.info("✅ Gemini API initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini API: {e}")
            raise


class TestGeminiAPIResponses:
    """Test Gemini API response generation and error handling."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        if genai is None:
            pytest.skip("google.generativeai not installed")
        genai.configure(api_key=GOOGLE_API_KEY)

    def test_simple_text_generation(self):
        """Test simple text generation."""
        logger.info("\n--- TEST: Simple Text Generation ---")
        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content("Say 'Hello' in one word")
            
            assert response is not None, "No response received"
            assert hasattr(response, 'text'), "Response has no text attribute"
            assert len(response.text) > 0, "Response text is empty"
            
            logger.info(f"✅ Simple generation successful: {response.text[:50]}")
            
        except Exception as e:
            logger.error(f"❌ Simple generation failed: {e}")
            raise

    def test_response_with_safety_settings(self):
        """Test response generation with safety settings."""
        logger.info("\n--- TEST: Response with Safety Settings ---")
        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(
                "What is 2+2?",
                safety_settings=[
                    {
                        "category": HarmCategory.HARM_CATEGORY_UNSPECIFIED,
                        "threshold": HarmBlockThreshold.BLOCK_NONE,
                    }
                ]
            )
            
            assert response is not None
            assert response.text
            logger.info(f"✅ Generation with safety settings successful: {response.text}")
            
        except Exception as e:
            logger.error(f"❌ Generation with safety settings failed: {e}")
            raise

    def test_long_prompt_handling(self):
        """Test handling of long prompts (token limit testing)."""
        logger.info("\n--- TEST: Long Prompt Handling ---")
        
        # Create a long prompt
        long_text = "What is farming? " * 500  # ~2000 words
        
        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(long_text)
            
            assert response is not None
            assert response.text
            logger.info(f"✅ Long prompt handled successfully. Response length: {len(response.text)}")
            
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                logger.error(f"❌ Rate limit hit: {e}")
                raise AssertionError("Rate limit detected") from e
            elif "400" in str(e) or "token" in str(e).lower():
                logger.error(f"❌ Token limit exceeded: {e}")
                raise AssertionError("Token limit detected") from e
            else:
                logger.error(f"❌ Long prompt handling failed: {e}")
                raise

    def test_rapid_consecutive_requests(self):
        """Test rapid consecutive requests to detect rate limiting."""
        logger.info("\n--- TEST: Rapid Consecutive Requests ---")
        
        model = genai.GenerativeModel("gemini-pro")
        failures = []
        successes = 0
        rate_limit_hit = False
        
        for i in range(5):
            try:
                logger.info(f"  Request {i+1}/5...")
                response = model.generate_content(f"Count: {i}")
                
                if response and response.text:
                    successes += 1
                    logger.info(f"    ✅ Success: {response.text[:30]}")
                else:
                    failures.append(f"Request {i}: No response")
                    logger.warning(f"    ⚠️ No response for request {i}")
                
                # Add small delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "too many requests" in error_msg.lower():
                    rate_limit_hit = True
                    logger.error(f"    ❌ RATE LIMIT HIT on request {i+1}: {e}")
                    failures.append(f"Request {i}: Rate limit")
                elif "503" in error_msg:
                    logger.error(f"    ❌ SERVICE UNAVAILABLE on request {i+1}: {e}")
                    failures.append(f"Request {i}: Service unavailable")
                else:
                    logger.error(f"    ❌ Error on request {i+1}: {e}")
                    failures.append(f"Request {i}: {str(e)[:50]}")
        
        logger.info(f"\n  Summary: {successes} successes, {len(failures)} failures")
        if failures:
            for failure in failures:
                logger.info(f"    - {failure}")
        
        if rate_limit_hit:
            logger.warning("⚠️ RATE LIMIT DETECTED: API is limiting request frequency")
        
        assert successes >= 3, f"Too many failures: {len(failures)}/5"

    def test_streaming_generation(self):
        """Test streaming response generation."""
        logger.info("\n--- TEST: Streaming Generation ---")
        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(
                "Explain farming in 3 sentences",
                stream=True
            )
            
            chunks = 0
            full_text = ""
            for chunk in response:
                if chunk.text:
                    chunks += 1
                    full_text += chunk.text
            
            assert chunks > 0, "No chunks received in stream"
            assert len(full_text) > 0, "Stream produced no text"
            logger.info(f"✅ Streaming successful: {chunks} chunks, {len(full_text)} chars")
            
        except Exception as e:
            logger.error(f"❌ Streaming generation failed: {e}")
            raise


class TestGeminiAPILimits:
    """Test API limits and quota issues."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        if genai is None:
            pytest.skip("google.generativeai not installed")
        genai.configure(api_key=GOOGLE_API_KEY)

    def test_rate_limit_detection(self):
        """Test detection of rate limiting."""
        logger.info("\n--- TEST: Rate Limit Detection ---")
        
        model = genai.GenerativeModel("gemini-pro")
        
        # Try 10 rapid requests without delay
        rate_limit_responses = []
        
        for i in range(10):
            try:
                logger.info(f"  Rapid request {i+1}/10...")
                response = model.generate_content(f"Quick test {i}")
                
                if response and response.text:
                    logger.info(f"    ✅ Response received")
                    rate_limit_responses.append(("success", None))
                
                # No delay between requests
                
            except Exception as e:
                error_msg = str(e)
                rate_limit_responses.append(("error", error_msg))
                
                if "429" in error_msg:
                    logger.warning(f"    ⚠️ Rate limit detected on request {i+1}")
                elif "RESOURCE_EXHAUSTED" in error_msg:
                    logger.warning(f"    ⚠️ Resource exhausted on request {i+1}")
                else:
                    logger.info(f"    ℹ️ Request {i+1} error: {error_msg[:50]}")
        
        # Count results
        successes = sum(1 for status, _ in rate_limit_responses if status == "success")
        errors = sum(1 for status, _ in rate_limit_responses if status == "error")
        rate_limits = sum(1 for status, msg in rate_limit_responses 
                         if status == "error" and msg and "429" in msg)
        
        logger.info(f"\n  Results:")
        logger.info(f"    Successes: {successes}/10")
        logger.info(f"    Errors: {errors}/10")
        logger.info(f"    Rate limits (429): {rate_limits}/10")
        
        if rate_limits > 0:
            logger.warning("⚠️ RATE LIMITING DETECTED: API returned 429 Too Many Requests")
        else:
            logger.info("✅ No rate limiting detected in rapid requests")

    def test_quota_exhaustion_detection(self):
        """Test detection of quota exhaustion."""
        logger.info("\n--- TEST: Quota Exhaustion Detection ---")
        
        model = genai.GenerativeModel("gemini-pro")
        
        try:
            response = model.generate_content("Test quota")
            
            if response and response.text:
                logger.info("✅ API is responding normally (quota not exhausted)")
            else:
                logger.warning("⚠️ API returned empty response (possible quota issue)")
                
        except Exception as e:
            error_msg = str(e)
            
            if "403" in error_msg or "Forbidden" in error_msg:
                logger.error(f"❌ QUOTA EXHAUSTED: {e}")
                raise AssertionError("Quota exhausted") from e
            elif "429" in error_msg:
                logger.error(f"❌ RATE LIMITED: {e}")
                raise AssertionError("Rate limited") from e
            elif "401" in error_msg or "Unauthorized" in error_msg:
                logger.error(f"❌ AUTHENTICATION FAILED: {e}")
                raise AssertionError("Authentication failed") from e
            else:
                logger.error(f"❌ Unexpected error: {e}")
                raise

    def test_empty_response_detection(self):
        """Test detection of empty responses (no_response generated)."""
        logger.info("\n--- TEST: Empty Response Detection ---")
        
        model = genai.GenerativeModel("gemini-pro")
        
        empty_responses = 0
        for i in range(3):
            try:
                response = model.generate_content("Generate a response")
                
                if response is None:
                    logger.warning(f"  ⚠️ Request {i+1}: None response")
                    empty_responses += 1
                elif not response.text or len(response.text.strip()) == 0:
                    logger.warning(f"  ⚠️ Request {i+1}: Empty text response")
                    empty_responses += 1
                else:
                    logger.info(f"  ✅ Request {i+1}: Valid response ({len(response.text)} chars)")
                
                time.sleep(0.5)
                
            except Exception as e:
                if "no response generated" in str(e).lower():
                    logger.warning(f"  ⚠️ Request {i+1}: 'no response generated' error")
                    empty_responses += 1
                else:
                    logger.error(f"  ❌ Request {i+1}: {e}")
        
        if empty_responses > 0:
            logger.warning(f"⚠️ {empty_responses}/3 requests had empty/no response issues")
        else:
            logger.info("✅ All responses were valid")


class TestGeminiAPIHealthReport:
    """Generate a health report for Gemini API."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        if genai is None:
            pytest.skip("google.generativeai not installed")
        genai.configure(api_key=GOOGLE_API_KEY)

    def test_generate_health_report(self):
        """Generate comprehensive health report."""
        logger.info("\n" + "="*70)
        logger.info("GEMINI API HEALTH REPORT")
        logger.info("="*70)
        
        model = genai.GenerativeModel("gemini-pro")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "api_key_configured": bool(GOOGLE_API_KEY),
            "basic_generation": False,
            "streaming_available": False,
            "rate_limit_status": "Unknown",
            "quota_status": "Unknown",
            "avg_response_time": 0,
            "issues": [],
            "recommendations": []
        }
        
        # Test 1: Basic generation
        logger.info("\n[1/5] Testing basic generation...")
        try:
            start = time.time()
            response = model.generate_content("Test")
            elapsed = time.time() - start
            report["basic_generation"] = bool(response and response.text)
            report["avg_response_time"] = elapsed
            logger.info(f"✅ Response in {elapsed:.2f}s: {response.text[:30]}")
        except Exception as e:
            logger.error(f"❌ {e}")
            report["issues"].append(f"Basic generation failed: {str(e)[:50]}")
        
        # Test 2: Streaming
        logger.info("\n[2/5] Testing streaming...")
        try:
            response = model.generate_content("Test", stream=True)
            chunks = sum(1 for _ in response)
            report["streaming_available"] = chunks > 0
            logger.info(f"✅ Streaming works: {chunks} chunks")
        except Exception as e:
            logger.warning(f"⚠️ Streaming failed: {e}")
            report["issues"].append("Streaming unavailable")
        
        # Test 3: Rate limits
        logger.info("\n[3/5] Testing for rate limits...")
        rate_limit_count = 0
        for i in range(3):
            try:
                model.generate_content(f"Test {i}")
                time.sleep(0.2)
            except Exception as e:
                if "429" in str(e):
                    rate_limit_count += 1
        
        if rate_limit_count == 0:
            report["rate_limit_status"] = "✅ No rate limits detected"
            logger.info("✅ No rate limits detected")
        elif rate_limit_count < 2:
            report["rate_limit_status"] = "⚠️ Occasional rate limiting"
            logger.warning("⚠️ Occasional rate limiting detected")
            report["recommendations"].append("Add request delays (0.5-1s)")
        else:
            report["rate_limit_status"] = "❌ Frequent rate limiting"
            logger.error("❌ Frequent rate limiting detected")
            report["recommendations"].append("API key may have low quota")
        
        # Test 4: Quota
        logger.info("\n[4/5] Testing quota...")
        try:
            model.generate_content("Test quota")
            report["quota_status"] = "✅ Quota available"
            logger.info("✅ Quota appears to be available")
        except Exception as e:
            if "403" in str(e) or "quota" in str(e).lower():
                report["quota_status"] = "❌ Quota exhausted"
                logger.error("❌ Quota exhausted")
                report["issues"].append("Daily quota exhausted")
            else:
                report["quota_status"] = "⚠️ Unknown"
        
        # Test 5: Summary
        logger.info("\n[5/5] Generating summary...")
        
        # Print report
        logger.info("\n" + "-"*70)
        logger.info("REPORT SUMMARY:")
        logger.info("-"*70)
        for key, value in report.items():
            if key not in ["issues", "recommendations"]:
                logger.info(f"  {key}: {value}")
        
        if report["issues"]:
            logger.info("\n⚠️ ISSUES DETECTED:")
            for issue in report["issues"]:
                logger.info(f"  - {issue}")
        
        if report["recommendations"]:
            logger.info("\n💡 RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                logger.info(f"  - {rec}")
        
        logger.info("\n" + "="*70)
        
        # Return report for assertions
        return report


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
