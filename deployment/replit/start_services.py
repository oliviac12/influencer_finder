#!/usr/bin/env python
"""
Start both Streamlit and Email Scheduler for Replit Deployment
This ensures both services run when deployed
"""
import subprocess
import threading
import time
import os
import sys

def run_scheduler():
    """Run the email scheduler in background"""
    print("🚀 Starting Email Scheduler Service...")
    while True:
        try:
            # Run the scheduler
            subprocess.run([sys.executable, "email_scheduler_service.py"])
        except Exception as e:
            print(f"Scheduler crashed, restarting in 30s: {e}")
            time.sleep(30)

def run_streamlit():
    """Run the Streamlit app"""
    print("🎯 Starting Streamlit App...")
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "app/creator_review_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])

if __name__ == "__main__":
    print("="*50)
    print("🎯 Starting Influencer Finder Services")
    print("📧 Email Scheduler + Streamlit App")
    print("="*50)
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ Email scheduler started in background")
    
    # Wait a moment for scheduler to initialize
    time.sleep(3)
    
    # Run Streamlit in main thread
    run_streamlit()