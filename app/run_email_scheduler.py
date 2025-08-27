"""
Run the Email Scheduler App
"""
import sys
import os
import subprocess

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Run the Streamlit app
if __name__ == "__main__":
    subprocess.run([
        "streamlit", "run", 
        os.path.join(os.path.dirname(__file__), "email_scheduler_app.py"),
        "--server.port", "8503",
        "--server.headless", "true"
    ])