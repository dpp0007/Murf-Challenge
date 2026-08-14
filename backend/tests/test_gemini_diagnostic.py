"""
Quick diagnostic for Gemini API - check rate limits and quota status.
"""

import os
import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env.local")

# Now import after env is loaded
import google.generativeai as genai

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def print_section(text):
    print(f"\n{text}")
    print("-" * 70)

def test_api_status():
    """Test Gemini API status and detect limits."""
    
    print_header("GEMINI API DIAGNOSTIC TEST")
    
    # Check API key
    print_section("[1/6] Checking API Key")
    if not GOOGLE_API_KEY:
        print("❌ GOOGLE_API_KEY not configured")
        return False
    print(f"✅ API Key found: {GOOGLE_API_KEY[:20]}...")
    
    # Configure API
    print_section("[2/6] Configuring API")
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        print("✅ API configured successfully")
    except Exception as e:
        print(f"❌ Failed to configure: {e}")
        return False
    
    # Test basic generation
    print_section("[3/6] Testing Basic Generation")
    try:
        # Try newer models first
        model = genai.GenerativeModel("gemini-3.5-flash-lite")
        start = time.time()
        response = model.generate_content("Say 'OK' in one word")
        elapsed = time.time() - start
        
        if response and response.text:
            print(f"✅ Response received in {elapsed:.2f}s")
            print(f"   Response: {response.text}")
        else:
            print("⚠️ Response received but empty text")
            print(f"   Response object: {response}")
            return False
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False
    
    # Test rapid requests (detect rate limiting)
    print_section("[4/6] Testing for Rate Limiting (5 rapid requests)")
    model = genai.GenerativeModel("gemini-3.5-flash-lite")
    rate_limit_count = 0
    success_count = 0
    
    for i in range(5):
        try:
            print(f"  Request {i+1}/5... ", end="", flush=True)
            response = model.generate_content(f"Response {i}")
            if response and response.text:
                print("✅")
                success_count += 1
            else:
                print("⚠️ (no response text)")
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "too many requests" in error_str.lower():
                print(f"❌ RATE LIMIT (429)")
                rate_limit_count += 1
            elif "503" in error_str:
                print(f"❌ SERVICE UNAVAILABLE (503)")
            else:
                print(f"❌ {error_str[:40]}")
    
    print(f"\n  Results: {success_count}/5 successful, {rate_limit_count} rate limits")
    
    if rate_limit_count > 0:
        print(f"  ⚠️ WARNING: Rate limiting detected ({rate_limit_count}/5 requests)")
    else:
        print(f"  ✅ No rate limiting detected")
    
    # Test quota
    print_section("[5/6] Testing Quota Status")
    try:
        response = model.generate_content("Test quota")
        print("✅ Quota appears to be available")
    except Exception as e:
        error_str = str(e)
        if "403" in error_str or "quota" in error_str.lower():
            print(f"❌ QUOTA EXHAUSTED: {e}")
        elif "429" in error_str:
            print(f"❌ RATE LIMITED: {e}")
        else:
            print(f"⚠️ {e}")
    
    # Summary
    print_section("[6/6] Summary")
    print(f"✅ API is accessible")
    print(f"✅ Basic generation works")
    
    if rate_limit_count == 0:
        print(f"✅ No rate limiting detected in rapid requests")
    elif rate_limit_count < 2:
        print(f"⚠️ Occasional rate limiting (add 0.5-1s delays between requests)")
    else:
        print(f"❌ Frequent rate limiting detected - quota may be low")
    
    print_header("DIAGNOSTIC COMPLETE")
    return True

if __name__ == "__main__":
    success = test_api_status()
    sys.exit(0 if success else 1)
