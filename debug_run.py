#!/usr/bin/env python3
import sys
import os

print("🚀 Starting debug run...")
print("📍 Current working directory:", os.getcwd())

print("📦 Importing modules...")
from screen_creators import CreatorScreener
print("✅ Import successful")

print("🔧 Initializing screener...")
sys.stdout.flush()  # Force output to appear immediately

screener = CreatorScreener(
    tikapi_key="iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx",
    brightdata_token="36c74962-d03a-41c1-b261-7ea4109ec8bd"
)

print("✅ Screener initialized!")
print("🎯 About to start screening...")
sys.stdout.flush()