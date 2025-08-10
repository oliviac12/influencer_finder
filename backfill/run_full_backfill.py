"""
Run Full Content Data Backfill
Processes ALL creators from CSV files - no limits
"""
import logging
import sys
from datetime import datetime
from backfill_content_data import ContentBackfiller

# Setup logging
log_filename = f"logs/content_backfill_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# API keys
TIKAPI_KEY = "iLLGx2LbZskKRHGcZF7lcilNoL6BPNGeJM1p0CFgoVaD2Nnx"
BRIGHTDATA_TOKEN = "36c74962-d03a-41c1-b261-7ea4109ec8bd"

if __name__ == "__main__":
    logger.info("🚀 Starting FULL content data backfill for ALL creators...")
    logger.info("📊 Estimated: ~970 creators across 3 CSV files")
    logger.info("⏱️  Estimated time: ~2-3 hours (2 second delay between requests)")
    logger.info("💡 You can stop and resume anytime - already processed creators will be skipped")
    logger.info(f"📋 Log file: {log_filename}")
    logger.info("="*60)

    try:
        # Initialize backfiller
        backfiller = ContentBackfiller(TIKAPI_KEY, BRIGHTDATA_TOKEN)
        
        # Run full backfill - NO max_creators limit
        backfiller.run_backfill()
        
        logger.info("🎉 Full backfill complete!")
        
    except KeyboardInterrupt:
        logger.info("⏹️  Backfill stopped by user")
    except Exception as e:
        logger.error(f"❌ Backfill failed with error: {e}")
        raise