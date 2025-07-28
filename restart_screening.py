#!/usr/bin/env python3
import sys
print("🔄 Restarting radar_5k_quitmyjob screening...")
sys.stdout.flush()

from screen_creators import CreatorScreener

screener = CreatorScreener(
    'iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx', 
    brightdata_token='36c74962-d03a-41c1-b261-7ea4109ec8bd'
)

print("✅ Resuming from where we left off...")
sys.stdout.flush()

screener.screen_all_creators('data/inputs/radar_5k_quitmyjob.csv')