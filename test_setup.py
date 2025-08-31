#!/usr/bin/env python3
"""
Test script to verify Nudgly setup and components.

Run this to test individual components before full deployment.
"""

import sys
import os
from datetime import datetime, timedelta
import pytz

# Add app to path
sys.path.insert(0, '.')

def test_settings():
    """Test settings loading."""
    print("🔧 Testing settings...")
    try:
        from app.settings import (
            TZ, DAILY_DIGEST_HOUR, TWILIO_ACCOUNT_SID,
            OPENAI_API_KEY, ALLOWED_SENDERS
        )
        print(f"  ✅ Timezone: {TZ}")
        print(f"  ✅ Daily digest hour: {DAILY_DIGEST_HOUR}")
        print(f"  ✅ Twilio SID: {TWILIO_ACCOUNT_SID[:10]}..." if TWILIO_ACCOUNT_SID else "  ❌ Twilio SID not set")
        print(f"  ✅ OpenAI key: {'Set' if OPENAI_API_KEY else 'Not set'}")
        print(f"  ✅ Allowed senders: {len(ALLOWED_SENDERS)} numbers")
        return True
    except Exception as e:
        print(f"  ❌ Settings error: {e}")
        return False

def test_database():
    """Test database connection and models."""
    print("\n💾 Testing database...")
    try:
        from app.db import init_db
        from app.models import Reminder, ReminderStatus, ReminderSource
        
        init_db()
        print("  ✅ Database initialized")
        print("  ✅ Models loaded")
        return True
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def test_parser():
    """Test text parsing functionality."""
    print("\n🧠 Testing parser...")
    try:
        from app.parsers import parse_text
        
        # Test various inputs
        test_cases = [
            "Remind me to take meds at 9am",
            "Call GP tomorrow at 11",
            "LIST",
            "DONE 123"
        ]
        
        for test in test_cases:
            result = parse_text(test)
            print(f"  ✅ '{test}' → {result.command_type}")
        
        return True
    except Exception as e:
        print(f"  ❌ Parser error: {e}")
        return False

def test_scheduler():
    """Test scheduler functionality."""
    print("\n⏰ Testing scheduler...")
    try:
        from app.scheduler import NudglyScheduler
        
        scheduler = NudglyScheduler()
        print("  ✅ Scheduler created")
        
        # Don't actually start it in test
        print("  ✅ Scheduler configuration OK")
        return True
    except Exception as e:
        print(f"  ❌ Scheduler error: {e}")
        return False

def test_whisper():
    """Test Whisper configuration."""
    print("\n🎤 Testing Whisper...")
    try:
        from app.whisper_utils import VoiceTranscriber
        
        transcriber = VoiceTranscriber()
        if transcriber.openai_client:
            print("  ✅ OpenAI client initialized")
        else:
            print("  ⚠️  OpenAI client not available (API key missing)")
        
        print("  ✅ Whisper module loaded")
        return True
    except Exception as e:
        print(f"  ❌ Whisper error: {e}")
        return False

def test_timezone():
    """Test timezone handling."""
    print("\n🌍 Testing timezone...")
    try:
        from app.settings import TZ
        
        tz = pytz.timezone(TZ)
        now = datetime.now(tz)
        utc_now = datetime.utcnow()
        
        print(f"  ✅ Timezone: {TZ}")
        print(f"  ✅ Local time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"  ✅ UTC time: {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    except Exception as e:
        print(f"  ❌ Timezone error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Nudgly Component Tests\n")
    
    tests = [
        test_settings,
        test_database,
        test_parser,
        test_scheduler,
        test_whisper,
        test_timezone,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
            results.append(False)
    
    print("\n" + "="*50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All {total} tests passed! Nudgly is ready to go.")
    else:
        print(f"⚠️  {passed}/{total} tests passed. Check errors above.")
        
    print("\n📝 Next steps:")
    print("1. Fix any failing tests")
    print("2. Set up ngrok: ngrok http 8000")
    print("3. Configure Twilio webhook")
    print("4. Run: python run.py")

if __name__ == "__main__":
    main()


