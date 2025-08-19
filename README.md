# Influencer Finder

An agentic workflow to identify TikTok creators that match specific brand vibes, automating the manual process of reviewing creators for brand fit.

## 🎯 Project Overview

This project addresses the challenge of scaling influencer discovery and outreach. Currently, reaching out to 300+ creators monthly to achieve 30 collaborations involves extensive manual content review. This tool automates creator analysis using a hybrid TikAPI + Bright Data MCP approach with LLM-powered content evaluation.

## ✅ Current Status (Updated 2025-08-16)

**🆕 Phase 6: Complete Email Workflow System ✅**
- ✅ **Email Tracking Service**: Deployed pixel tracking at tracking.unsettled.xyz on Replit
- ✅ **Open Rate Analytics**: Real-time tracking of email opens with campaign-level stats
- ✅ **Reply Management**: Full IMAP integration with Zoho for fetching email replies
- ✅ **AI Response Generation**: Claude-powered contextual responses to creator replies
- ✅ **Email Threading**: Maintains proper email threads with In-Reply-To headers
- ✅ **Unified Interface**: Complete email workflow in Streamlit (send → track → reply)
- ✅ **Campaign Integration**: All email features integrated with campaign management

**🆕 New Feature: Content Database System**
- **Content Extraction**: Automatically extracts captions, hashtags, and metadata from Bright Data's `top_posts_data`
- **Searchable Database**: Builds `creators_content_database.json` with ~37 posts per creator for flexible querying
- **Campaign Flexibility**: Find creators by keywords, hashtags, or themes on-demand instead of pre-computed categories
- **Background Processing**: Full backfill system to extract content from all existing creator lists

**Phase 1: Core Infrastructure Complete ✅**
- ✅ **Hybrid API Client Architecture**: Built robust TikAPI + Bright Data MCP fallback system  
- ✅ **Universal Automatic Failover**: When Bright Data fails for ANY reason, automatically falls back to TikAPI
- ✅ **Cost Optimization**: Bright Data MCP (free) as primary, TikAPI ($25/month) as backup
- ✅ **Triple Filtering System**: Engagement (5K+ avg views) + Recency (60 days) + Shoppable content detection
- ✅ **Intelligent Caching**: Preserves API credits with comprehensive cache management
- ✅ **Large-Scale Processing**: Successfully processing 970+ creator dataset across 3 CSV files
- ✅ **Clean Project Organization**: Modular directory structure with proper separation of concerns

**Phase 2: Content Database System ✅**
- ✅ **Content Data Extraction**: Extract 40+ fields from Bright Data including captions and hashtags
- ✅ **Searchable Content Database**: JSON database with full creator content for flexible campaign matching
- ✅ **Automatic Content Saving**: All future screening runs automatically save content data
- ✅ **Background Backfill System**: Extract content from all existing creator lists (~970 creators)
- ✅ **Two-Stage Workflow**: Content analysis (cheap) → Video analysis (expensive) for qualified creators only

**Phase 3: File Organization & Code Quality ✅**
- ✅ **Organized Directory Structure**: 
  - `clients/` - API clients (TikAPI, Bright Data MCP, TikTok MCP)
  - `utils/` - Utility modules (content database, shoppable filtering)
  - `helpers/` - One-time rebuild scripts
  - `data/` - All CSV files with clear input/output separation
  - `cache/` - Consolidated cache management (screening + subtitle + content)
  - `logs/` - Centralized logging
- ✅ **Cleaned Up Dead Code**: Removed experimental client versions and test files
- ✅ **Updated Import Structure**: All imports reflect new modular organization

**Phase 4: AI-Powered Creator Review & Outreach ✅**
- ✅ **Streamlit Creator Review App**: Visual interface for AI-powered creator analysis and approval
- ✅ **Claude API Integration**: Automated creator analysis with customizable campaign briefs  
- ✅ **Campaign Management System**: Flexible campaign briefs with persistent AI analysis cache
- ✅ **Human Review Cache**: Track approval decisions per campaign for better organization
- ✅ **Parallel Processing**: Analyze multiple creators simultaneously (3x faster)
- ✅ **Email Extraction**: Automatically extracts creator emails from bios (85.2% success rate)
- ✅ **Approval Workflow**: One-click approve/reject/maybe with decision tracking
- ✅ **Export Functionality**: Download approved creator lists as CSV
- ✅ **Email Outreach System**: Integrated email client with personalized drafts and Zoho SMTP support
- ✅ **Media Kit Attachments**: Attach PDF/PPT media kits to outreach emails
- ✅ **Agency Clarification**: Email templates clarify agency relationship with brand clients

**Phase 5: Database Completion ✅**
- ✅ **Missing Creator Retry System**: Optimized script processes failed creators 40% faster
- ✅ **97% Database Coverage**: Successfully processed 937 out of 964 creators
- ✅ **Invalid Creator Tracking**: 28 permanently failed creators tracked to avoid redundant API calls
- ✅ **34,216 Total Posts**: Comprehensive content database for flexible searching

## 🚀 Quick Start

### Prerequisites
```bash
pip install tikapi pandas streamlit anthropic python-dotenv smtplib
```

### Main Workflows

**Creator Screening + Content Extraction:**
```bash
# Screen creators and automatically save content data
python screen_creators.py
```

**Content Database Backfill:**
```bash
# Extract content from all existing CSV files
python run_full_backfill.py
```

**Content Database Search:**
```python
from utils.content_database import ContentDatabase

db = ContentDatabase()

# Find creators by hashtag
fashion_creators = db.search_creators_by_hashtag("fashion")

# Find creators by keyword
travel_creators = db.search_creators_by_keyword("travel")

# Get specific creator content
creator_data = db.get_creator_content("username")
```

**Creator Review & Email Outreach Interface:**
```bash
# Set up environment variables
cp .env.example .env
# Edit .env with your Zoho email credentials and Anthropic API key

# Launch creator review app with email outreach
python app/run_review_app.py
# OR manually: streamlit run app/creator_review_app.py
```

**Retry Missing Creators (Optimized):**
```bash
# Process creators that failed initial extraction
python backfill/backfill_retry_missing.py
# Monitor progress: cat retry_progress_*.txt
```

**Monitor Background Jobs:**
```bash
# Check backfill progress
tail -f logs/content_backfill_*.log

# Check database stats
python -c "from utils.content_database import ContentDatabase; print(ContentDatabase().get_stats())"
```

## 🏗️ Architecture

**Current Project Structure:**
```
influencer_finder/
├── README.md & CLAUDE.md           # Documentation
├── screen_creators.py              # Main screening entry point  
├── app/                            # Streamlit web interface
│   ├── creator_review_app.py      # AI-powered review interface with tabs
│   ├── email_outreach.py          # Email outreach system
│   └── run_review_app.py          # Launch script
├── backfill/                       # Content extraction & retry scripts
│   ├── backfill_content_data.py   # Main extraction engine
│   ├── backfill_retry_missing.py  # Optimized retry for failed creators
│   └── run_full_backfill.py       # Batch extraction runner
├── clients/                        # API clients
│   ├── tikapi_client.py           # TikAPI integration
│   ├── creator_data_client.py     # Hybrid TikAPI + Bright Data client  
│   └── tiktok_mcp_client.py       # TikTok MCP for subtitles
├── utils/                          # Utility modules
│   ├── content_database.py        # Content database manager
│   ├── filter_shoppable.py        # Shoppable content detection
│   ├── ai_analysis_cache.py       # AI analysis caching (7-day expiry)
│   ├── human_review_cache.py      # Human review decisions per campaign
│   ├── email_cache.py             # Persistent email cache per campaign
│   └── campaign_manager.py        # Campaign management with flexible briefs
├── tools/                          # Utility scripts
│   └── check_creator_emails.py    # Email extraction statistics
├── helpers/                        # One-time rebuild scripts
├── data/                           # All CSV files + documentation
├── cache/                          # Intelligent caching system
│   ├── creators_content_database.json # 937 creators, 34k+ posts
│   ├── ai_analysis_cache.json     # Cached AI analyses
│   ├── screening/                  # Creator screening cache
│   │   └── invalid_usernames.json  # 28 failed creators
│   └── subtitle/                   # Subtitle extraction cache
└── logs/                           # Processing logs
```

**Current Data Flow:**
```
Input: data/inputs/*.csv (970+ creators)
    ↓
screen_creators.py (Hybrid API + Triple filtering + Content extraction)
    ↓                                    ↓
data/outputs/qualified_creators.csv   cache/creators_content_database.json
    ↓                                    ↓
Video Analysis (28 posts)            Content Search (by campaign)
    ↓                                    ↓
Final Creator Rankings               Campaign-Specific Creator Lists
```

**Content Database Workflow:**
```
backfill_content_data.py → Extract 37 posts per creator → 
Content Database (captions + hashtags) → 
On-demand search: "Find fashion creators" → 
Qualified creators for video analysis
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

### Phase 3: Web Interface & User Experience ✅ COMPLETE
- [x] **Streamlit Application**: AI-powered creator review interface
  - [x] Batch AI analysis with Claude Sonnet 4
  - [x] Two modes: analyze custom list vs entire database
  - [x] Concise Q&A format with embedded TikTok links
  - [x] AI analysis caching (7-day expiry) to save costs
- [x] **Email Extraction**: Auto-extract from bios (85.2% success)
- [x] **Export Functionality**: Download approved creators as CSV

### Phase 4: Email Outreach System ✅ COMPLETE
- [x] **Email Outreach Interface**: Integrated into Streamlit app
  - [x] Display creators with emails vs those needing manual entry
  - [x] Draft personalized outreach messages using AI analysis
  - [x] Direct email sending via Zoho SMTP
  - [x] Email templates with personalization
  - [x] Bulk draft generation and export
- [x] **Retry Missing Creators**: Optimized script completed
  - [x] Processed 76 missing creators with 55 successes
  - [x] 40% faster with reduced wait times
  - [x] Invalid creators tracked to avoid redundant attempts

### Phase 5: Enhanced Search & Analytics 🎯 NEXT
- [ ] **Advanced Search Interface**: Query the content database
  - [ ] Search by hashtags, keywords, themes
  - [ ] Filter by engagement, follower count, post frequency
  - [ ] Export search results for campaigns
- [ ] **Analytics Dashboard**: Track campaign performance
  - [ ] Email open/response rates
  - [ ] Creator conversion funnel
  - [ ] ROI tracking

## 🐛 Known Issues

### Replit Scheduler Attachment Bug
- **Issue**: Scheduled emails are sent without attachments despite `attachment_path` being set
- **Impact**: Manual emails work fine, but scheduled emails via Replit don't include PDF attachments
- **Status**: Confirmed bug - attachment logic works locally but fails in Replit environment
- **Workaround**: Use manual email sending for emails that require attachments
- **Priority**: Medium (affects attachment functionality but not core email sending)

### Streamlit Cloud Supabase Connection
- **Issue**: EmailOutreachManager component can't access Supabase credentials on Streamlit Cloud
- **Impact**: Shows "File Cache (No Credentials)" instead of using persistent Supabase cache
- **Status**: Other Supabase features work fine, only affects EmailOutreachManager
- **Workaround**: Cache still works locally and on other components
- **Priority**: Low (functionality works, just less optimal caching)

## 🚀 Future Improvements

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

### Phase 6: Agentic Response & Management
- [ ] Parse creator responses from email
- [ ] Negotiate terms within parameters
- [ ] Schedule content deliverables
- [ ] Track campaign progress
- [ ] Integration with project management tools

## 📧 Email Outreach System

The integrated email outreach system allows you to:

**Features:**
- **Personalized Email Generation**: Uses AI analysis to create customized outreach emails
- **Agency Relationship Clarity**: Templates specify you're representing brands as an agency
- **Campaign-Based Caching**: Persistent email cache per campaign to avoid regenerating
- **Media Kit Attachments**: Upload and attach PDF/PPT media kits to outreach emails
- **Test Email Functionality**: Send test emails to different addresses before creator outreach
- **Direct Sending**: Send emails directly from the app via Zoho SMTP
- **Email Templates**: Pre-built templates with agency/brand relationship clarity
- **Bulk Operations**: Generate drafts for all approved creators at once
- **Email Tracking**: Logs all sent emails with timestamps

**Setup:**
1. Add your Zoho credentials to `.env`:
   ```
   SMTP_EMAIL=your-email@zoho.com
   SMTP_PASSWORD=your-zoho-password
   SMTP_HOST=smtp.zoho.com
   SMTP_PORT=587
   ```
2. Navigate to the "Email Outreach" tab in the app
3. Configure your agency name and client brand
4. Upload optional media kit attachment
5. Test with personal email before sending to creators

## 🛠️ Technical Implementation

### Data Sources
- **Bright Data MCP**: Primary source for creator profiles and content (free tier)
- **TikAPI**: Fallback for failed requests ($25/month)
- **TikTok MCP**: Subtitle extraction for detailed content analysis

### Key Features
- **97% Database Coverage**: 937 creators with 34,216 posts indexed
- **AI Analysis Caching**: 7-day cache reduces API costs by ~80%
- **Email Extraction**: 85.2% success rate from creator bios
- **Optimized Retry System**: 40% faster processing for failed creators
- **Modular Architecture**: Clean separation of concerns for maintainability

## 📊 Success Metrics

- Head of brand approves >70% of top-ranked results
- Significant time savings in creator review process
- Clear signal that LLM analysis correlates with brand fit

## 🔧 Development

### Current Usage
```bash
# Main workflow: Process 351 creators with triple filtering
python screen_creators.py

# Individual creator analysis
python tools/check_creator_emails.py

# Monitor progress
tail -f logs/screening_progress.log
```

### Key Files
- **`screen_creators.py`** - Main entry point for bulk creator screening
- **`app/creator_review_app.py`** - Streamlit interface with AI analysis and email outreach
- **`app/email_outreach.py`** - Email personalization and sending system
- **`backfill/backfill_retry_missing.py`** - Optimized retry for failed creators
- **`utils/content_database.py`** - Manages searchable creator content
- **`utils/ai_analysis_cache.py`** - 7-day caching for AI analyses
- **`cache/creators_content_database.json`** - 937 creators with 34k+ posts
- **`cache/screening/invalid_usernames.json`** - 28 permanently failed creators

### Next Development Steps
1. **Build Advanced Search Interface** for content database queries
2. **Add Analytics Dashboard** to track outreach performance
3. **Implement Response Parsing** for automated follow-ups
4. **Create Campaign Templates** for different verticals

### Current Results (10 test creators → 3 qualified)
- **adamgordonphoto**: 9,606 avg views (photo tutorials)
- **aisleyherndon**: 16,654 avg views (wedding photography) 
- **aissandali**: 26,260 avg views (travel/lifestyle couple)

### Contributing
1. Use modular components for testing new functionality
2. Expand content analysis capabilities in the Streamlit app
3. Add new filtering criteria in `screen_creators.py`

## 📈 Long-term Vision

- Fully automated pipeline: discovery → outreach → negotiation → management
- Human-in-the-loop for approvals and edge cases
- Learn from successful partnerships to improve all phases
- Scale from 30 collaborations/month to 100+

---

*This project automates influencer discovery to help brands efficiently identify creators that match their specific vibes and values.*