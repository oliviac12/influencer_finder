# Influencer Finder

An agentic workflow to identify TikTok creators that match specific brand vibes, automating the manual process of reviewing creators for brand fit.

## 🎯 Project Overview

This project addresses the challenge of scaling influencer discovery and outreach. Currently, reaching out to 300+ creators monthly to achieve 30 collaborations involves extensive manual content review. This tool automates creator analysis using a hybrid TikAPI + Bright Data MCP approach with LLM-powered content evaluation.

## ✅ Current Status (Updated 2025-01-27)

**Phase 1: Core Infrastructure Complete ✅**
- ✅ **Hybrid API Client Architecture**: Built robust TikAPI + Bright Data MCP fallback system
- ✅ **Automatic Failover**: When Bright Data hits "building snapshot" errors, automatically falls back to TikAPI
- ✅ **Cost Optimization**: Bright Data MCP (free) as primary, TikAPI ($25/month) as backup
- ✅ **Triple Filtering System**: Engagement (5K+ avg views) + Recency (60 days) + Shoppable content detection
- ✅ **Intelligent Caching**: Preserves API credits with comprehensive cache management
- ✅ **Large-Scale Processing**: Successfully processing 351-creator dataset (radar_1k_10K_fashion_affiliate_5%_eng_rate.csv)
- ✅ **Clean Project Organization**: Modular directory structure with proper separation of concerns

**Phase 2: File Organization & Code Quality ✅**
- ✅ **Organized Directory Structure**: 
  - `clients/` - API clients (TikAPI, Bright Data MCP, TikTok MCP)
  - `utils/` - Utility modules (shoppable content filtering)
  - `helpers/` - One-time rebuild scripts
  - `data/` - All CSV files with clear input/output separation
  - `cache/` - Consolidated cache management (screening + subtitle)
  - `logs/` - Centralized logging
- ✅ **Cleaned Up Dead Code**: Removed obsolete files (rapidapi_tiktok_client, brightdata_mcp_client, old logs)
- ✅ **Updated Import Structure**: All imports reflect new modular organization

**Current Phase: UI Development Planning 🚧**
- 🎯 **Streamlit Web Interface**: Build user-friendly frontend for CSV upload and job management
- 🎯 **Background Job Processing**: Long-running creator screening in background
- 🎯 **Email Notifications**: Automatic email alerts when processing completes
- 🎯 **Replit Deployment**: Always-on processing using Replit Paid account

## 🚀 Quick Start

### Prerequisites
```bash
pip install tikapi
```

### Usage
```python
from tikapi import TikAPI

# Initialize API
api = TikAPI("your-api-key")

# Get creator profile and recent posts
profile = api.public.check(username="creator_username")
posts = api.public.posts(secUid=profile_sec_uid)
```

### Test the Implementation
```bash
python test_tikapi_final.py
```

This will fetch recent posts from @27travels as a demonstration.

## 🏗️ Architecture

**Current Project Structure:**
```
influencer_finder/
├── README.md & CLAUDE.md           # Documentation
├── screen_creators.py              # Main screening entry point  
├── analyze_creator.py              # Analysis entry point
├── clients/                        # API clients
│   ├── tikapi_client.py           # TikAPI integration
│   ├── creator_data_client.py     # Hybrid TikAPI + Bright Data client  
│   └── tiktok_mcp_client.py       # TikTok MCP for subtitles
├── utils/                          # Utility modules
│   └── filter_shoppable.py        # Shoppable content detection
├── helpers/                        # One-time scripts
├── data/                           # All CSV files + documentation
├── cache/                          # Intelligent caching system
└── logs/                           # Processing logs
```

**Current Data Flow:**
```
data/radar_1k_10K_fashion_affiliate_5%_eng_rate.csv → 
screen_creators.py (Hybrid API + Triple filtering) → 
data/qualified_creators.csv → 
[Future: Streamlit UI for job management]
```

**Hybrid API Architecture:**
```
Bright Data MCP (Free, Primary) → Success ✅
     ↓ "Building snapshot" error
TikAPI Fallback ($25/month) → Success ✅
```

**Triple Filtering Pipeline:**
1. **Engagement Filter**: 5K+ average views
2. **Recency Filter**: Posted within 60 days  
3. **Shoppable Content Filter**: Has monetizable/commercial content

### Why Search Tool > Pre-computed Database
1. **Flexibility** - Each brand/campaign needs different vibes
2. **Speed to value** - Can start immediately with queries like "Find creators similar to @example"
3. **Learning loop** - Discover what queries work through usage
4. **Efficiency** - Only analyze creators on-demand (can use sophisticated analysis)

## 📋 Roadmap

### Phase 1: Core Infrastructure ✅ COMPLETE
- [x] **Hybrid API Architecture**: TikAPI + Bright Data MCP with automatic failover
- [x] **Triple Filtering System**: Engagement + Recency + Shoppable content detection
- [x] **Large-Scale Processing**: Handle 351-creator datasets efficiently
- [x] **Intelligent Caching**: Comprehensive cache management for API credit conservation
- [x] **Project Organization**: Clean modular structure with proper separation of concerns
- [x] **TikTok MCP Integration**: Subtitle extraction for detailed content analysis

### Phase 3: Web Interface & User Experience 🎯 NEXT
- [ ] **Streamlit Application**: Build web UI for CSV upload and job management
  - [ ] Drag-and-drop CSV upload interface
  - [ ] Configurable filtering thresholds (views, days, etc.)
  - [ ] Real-time progress tracking with job status
  - [ ] Download processed results
- [ ] **Background Job Processing**: Long-running tasks without blocking UI
- [ ] **Email Notifications**: SMTP integration for job completion alerts
  - [ ] Success/failure notifications with summary stats
  - [ ] Download links for completed results
  - [ ] Error details for failed jobs
- [ ] **Replit Deployment**: Always-on processing using Replit Paid account
- [ ] **Job History**: Track previous processing runs and results

### Future Screening Improvements
- [ ] **Database Integration**: Replace CSV-based data storage with SQLite/PostgreSQL database
  - Avoid duplicate API calls by checking existing creator/post data
  - Enable incremental updates (only fetch new creators or recent posts)
  - Create comprehensive data warehouse with tables: `creators`, `posts`, `screening_results`
  - Support historical tracking and time-series analysis
  - Dramatically reduce API costs on subsequent runs
- [ ] **Enhanced Recency Filtering**: Current 60-day threshold may be too strict - need to analyze optimal recency window
- [ ] **Pinned Post Detection**: Better filtering to exclude promotional/pinned content from engagement calculations  
- [ ] **Engagement Rate Thresholds**: Add engagement rate minimums in addition to raw view counts
- [ ] **Content Quality Indicators**: Factor in caption quality, hashtag strategy, and content consistency
- [ ] **Category-Specific Filtering**: Different thresholds for travel vs lifestyle vs food creators
- [ ] **Seasonal Adjustments**: Account for posting patterns during holidays/travel seasons

### Phase 2: Agentic Outreach
- [ ] Automatically draft personalized outreach
- [ ] Integration with email systems
- [ ] Track open/response rates

### Phase 3: Agentic Response & Management
- [ ] Parse creator responses
- [ ] Negotiate terms within parameters
- [ ] Schedule content deliverables
- [ ] Track campaign progress

## 🛠️ Technical Implementation

### Data Sources
- **TikAPI**: Creator profiles, posts, engagement metrics
- **Future**: Modash, CreatorIQ, or HypeAuditor for initial discovery

### Key Features
- Real-time creator content analysis
- Engagement metrics tracking
- Video URL extraction for content analysis
- Scalable architecture for 100K+ creators

## 📊 Success Metrics

- Head of brand approves >70% of top-ranked results
- Significant time savings in creator review process
- Clear signal that LLM analysis correlates with brand fit

## 🔧 Development

### Current Usage
```bash
# Main workflow: Process 351 creators with triple filtering
python screen_creators.py

# Individual creator analysis (for testing)
python analyze_creator.py

# Monitor progress
tail -f logs/screening_progress.log
```

### Key Files (Updated Structure)
- **`screen_creators.py`** - Main entry point for bulk creator screening
- **`clients/creator_data_client.py`** - Hybrid TikAPI + Bright Data MCP client with automatic failover
- **`clients/tikapi_client.py`** - Pure TikAPI implementation (fallback)
- **`clients/tiktok_mcp_client.py`** - TikTok MCP for subtitle extraction
- **`utils/filter_shoppable.py`** - Shoppable content detection
- **`analyze_creator.py`** - Complete workflow for individual creator analysis
- **`data/radar_1k_10K_fashion_affiliate_5%_eng_rate.csv`** - Main 351-creator dataset
- **`data/qualified_creators.csv`** - Screening results output
- **`cache/`** - Intelligent caching for API credit conservation

### Next Development Steps (UI Phase)
1. **Create Streamlit app** on Replit for web interface
2. **Integrate background job processing** with current screening system
3. **Add SMTP email notifications** for job completion alerts
4. **Build progress tracking** and job history features

### Current Results (10 test creators → 3 qualified)
- **adamgordonphoto**: 9,606 avg views (photo tutorials)
- **aisleyherndon**: 16,654 avg views (wedding photography) 
- **aissandali**: 26,260 avg views (travel/lifestyle couple)

### Contributing
1. Use modular components for testing new functionality
2. Expand content analysis capabilities in `analyze_creator.py`
3. Add new filtering criteria in `screen_creators.py`

## 📈 Long-term Vision

- Fully automated pipeline: discovery → outreach → negotiation → management
- Human-in-the-loop for approvals and edge cases
- Learn from successful partnerships to improve all phases
- Scale from 30 collaborations/month to 100+

---

*This project automates influencer discovery to help brands efficiently identify creators that match their specific vibes and values.*