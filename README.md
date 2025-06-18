# Influencer Finder

An agentic workflow to identify TikTok creators that match specific brand vibes, automating the manual process of reviewing creators for brand fit.

## 🎯 Project Overview

This project addresses the challenge of scaling influencer discovery and outreach. Currently, reaching out to 300+ creators monthly to achieve 30 collaborations involves extensive manual content review. This tool automates creator analysis using TikAPI and LLM-powered content evaluation.

## ✅ Current Status

**Phase 1: TikAPI Integration & Creator Screening Complete**
- ✅ Successfully integrated TikAPI for creator data fetching
- ✅ Can retrieve creator profiles, follower counts, and recent posts  
- ✅ Extract video URLs, engagement metrics, and content descriptions
- ✅ Built modular TikAPI client (`tikapi_client.py`)
- ✅ Implemented TikTok MCP integration for subtitle extraction (`tiktok_mcp_client.py`)
- ✅ Created bulk creator screening system (`screen_creators.py`)
- ✅ Added dual filtering: engagement thresholds (5K+ avg views) + recency (60 days max)
- ✅ Intelligent caching system to preserve API credits
- ✅ CSV-based creator database processing (`data.csv` → `qualified_creators.csv`)

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

```
User query → Find relevant creators (filters) → 
Enrich top 100 → LLM scores JUST these 100 → 
Rank and return top 20
```

### Why Search Tool > Pre-computed Database
1. **Flexibility** - Each brand/campaign needs different vibes
2. **Speed to value** - Can start immediately with queries like "Find creators similar to @example"
3. **Learning loop** - Discover what queries work through usage
4. **Efficiency** - Only analyze creators on-demand (can use sophisticated analysis)

## 📋 Roadmap

### Phase 1: Discovery & Analysis ✅
- [x] TikAPI integration for content fetching
- [x] Creator profile and post retrieval
- [x] Bulk creator screening with engagement + recency filters
- [x] Intelligent caching system for API credit conservation
- [x] TikTok MCP integration for subtitle extraction
- [ ] LLM-powered content analysis
- [ ] Basic search functionality

### Next Steps: Screening Improvements
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

### Core Files
- `tikapi_client.py` - Modular TikAPI client for creator analysis
- `tiktok_mcp_client.py` - TikTok MCP integration with intelligent caching  
- `screen_creators.py` - **Main Entry Point** - Bulk creator screening system
- `analyze_creator.py` - Complete workflow orchestrating TikAPI + MCP + LLM analysis
- `data.csv` - Creator database (10 sample creators)
- `qualified_creators.csv` - Screening output with qualified creators and metrics
- `subtitle_cache/` - Intelligent caching directory for API credit conservation

### Usage
1. **Main Entry Point**: Run `python screen_creators.py` to screen all creators
2. **Individual Analysis**: Use `analyze_creator.py` for detailed single creator analysis
3. **Modular Components**: Import `tikapi_client` or `tiktok_mcp_client` for custom workflows

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