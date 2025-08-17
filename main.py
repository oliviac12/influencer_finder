#!/usr/bin/env python
"""
Simple entry point for Replit - alternative to run_app.py
"""
import os
import sys
import subprocess

# Set up environment
os.environ['STREAMLIT_SERVER_PORT'] = '8501'
os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

# Run streamlit directly
subprocess.run([
    sys.executable, "-m", "streamlit", "run",
    "app/creator_review_app.py",
    "--server.port", "8501",
    "--server.address", "0.0.0.0",
    "--server.headless", "true",
    "--browser.gatherUsageStats", "false"
])