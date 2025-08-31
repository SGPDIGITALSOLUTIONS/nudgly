#!/usr/bin/env python3
"""
Quick start script for Nudgly.

This script provides an easy way to run the Nudgly application
with proper error handling and setup validation.
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.11 or higher."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_env_file():
    """Check if .env file exists."""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("📝 Copy env.example to .env and fill in your configuration:")
        print("   cp env.example .env")
        return False
    print("✅ .env file found")
    return True

def check_ffmpeg():
    """Check if FFmpeg is available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0:
            print("✅ FFmpeg is available")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("⚠️  FFmpeg not found - voice note transcription may not work")
    print("📖 Install FFmpeg: https://ffmpeg.org/download.html")
    return True  # Don't block startup, just warn

def check_dependencies():
    """Check if required packages are installed."""
    try:
        import fastapi
        import uvicorn
        import twilio
        import openai
        import sqlalchemy
        import apscheduler
        print("✅ Dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Install dependencies: pip install -r requirements.txt")
        return False

def main():
    """Main startup function."""
    print("🚀 Starting Nudgly setup check...\n")
    
    checks = [
        check_python_version(),
        check_dependencies(),
        check_env_file(),
        check_ffmpeg(),
    ]
    
    if not all(checks[:3]):  # First 3 are critical
        print("\n❌ Setup incomplete. Please fix the issues above.")
        sys.exit(1)
    
    print("\n🎉 Setup looks good! Starting Nudgly...")
    print("📱 Make sure to configure your Twilio WhatsApp webhook to:")
    print("   https://your-ngrok-url.ngrok.io/twilio/whatsapp")
    print("\n" + "="*50)
    
    # Start the application
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Nudgly stopped. See you later!")
    except Exception as e:
        print(f"\n❌ Error starting Nudgly: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


