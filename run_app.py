#!/usr/bin/env python3
"""
Main entry point for Replit deployment
Runs both the Streamlit app and email scheduler
"""
import subprocess
import threading
import time
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_scheduler():
    """Run the email scheduler in a separate thread"""
    print("🚀 Starting email scheduler service...")
    try:
        # Import and run the scheduler
        from email_scheduler_service import main as scheduler_main
        scheduler_main()
    except Exception as e:
        print(f"❌ Scheduler error: {e}")
        # Keep trying to restart
        time.sleep(30)
        run_scheduler()

def run_streamlit():
    """Run the Streamlit app"""
    print("🎯 Starting Streamlit app...")
    
    # Configure Streamlit for Replit
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    
    # Run Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "app/creator_review_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ])

if __name__ == "__main__":
    print("="*50)
    print("🎯 Influencer Finder - Starting Services")
    print("="*50)
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ Email scheduler started in background")
    
    # Give scheduler a moment to initialize
    time.sleep(2)
    
    # Run Streamlit in main thread
    run_streamlit()