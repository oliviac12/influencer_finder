#!/usr/bin/env python3
"""
Run screening for radar_5k_quitmyjob dataset
"""
import sys
import os
import traceback

def main():
    try:
        print("🚀 Starting radar_5k_quitmyjob screening process...")
        print("📍 Current working directory:", os.getcwd())
        
        # Import after printing initial messages
        from screen_creators import CreatorScreener
        
        print("✅ Imported CreatorScreener successfully")
        
        # Initialize screener with API keys
        print("🔧 Initializing screener with API keys...")
        screener = CreatorScreener(
            tikapi_key="iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx",
            brightdata_token="36c74962-d03a-41c1-b261-7ea4109ec8bd"
        )
        
        print("✅ Screener initialized successfully")
        
        # Check if input file exists
        input_file = "data/inputs/radar_5k_quitmyjob.csv"
        print(f"📂 Checking input file: {input_file}")
        
        if not os.path.exists(input_file):
            print(f"❌ Input file not found: {input_file}")
            return
            
        print("✅ Input file found")
        
        # Run screening with correct input file
        print("🎯 Starting screening process...")
        screener.screen_all_creators(csv_file=input_file)
        
        print("🎉 Screening process completed!")
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        print("📋 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    main()