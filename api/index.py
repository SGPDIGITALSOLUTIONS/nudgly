"""
Vercel entry point for Nudgly app.
This file is required for Vercel Python deployments.
"""

from app.main import app

# Vercel expects the FastAPI app to be available as 'app'
# This file acts as the entry point for serverless deployment
