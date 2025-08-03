#!/usr/bin/env python3
"""
Launch Creator Review Streamlit App
Quick launcher for the creator review interface
"""
import subprocess
import sys
import os

def main():
    print("🚀 Launching Creator Review App...")
    print("📋 Make sure you have streamlit installed: pip install streamlit anthropic")
    print("🌐 App will open in your browser automatically")
    print("=" * 60)
    
    try:
        # Launch streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "creator_review_app.py",
            "--server.port=8501",
            "--server.headless=false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Streamlit app stopped")
    except Exception as e:
        print(f"❌ Error launching app: {e}")
        print("\n💡 Try running manually:")
        print("   streamlit run creator_review_app.py")

if __name__ == "__main__":
    main()