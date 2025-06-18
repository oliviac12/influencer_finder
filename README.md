# Influencer Finder

An agentic workflow to identify TikTok creators that match specific brand vibes, automating the manual process of reviewing creators for brand fit.

## 🎯 Project Overview

This project addresses the challenge of scaling influencer discovery and outreach. Currently, reaching out to 300+ creators monthly to achieve 30 collaborations involves extensive manual content review. This tool automates creator analysis using TikAPI and LLM-powered content evaluation.

## ✅ Current Status

**Phase 1: TikAPI Integration Complete**
- ✅ Successfully integrated TikAPI for creator data fetching
- ✅ Can retrieve creator profiles, follower counts, and recent posts
- ✅ Extract video URLs, engagement metrics, and content descriptions
- ✅ Working implementation in `test_tikapi_final.py`

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
- [ ] LLM-powered content analysis
- [ ] Basic search functionality

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

### Current Files
- `test_tikapi_final.py` - Working TikAPI implementation
- `sample_creators.md` - Sample creator data
- `data.xlsx` - Creator database

### Contributing
1. Test new creator usernames in `test_tikapi_final.py`
2. Expand content analysis capabilities
3. Add new data sources and APIs

## 📈 Long-term Vision

- Fully automated pipeline: discovery → outreach → negotiation → management
- Human-in-the-loop for approvals and edge cases
- Learn from successful partnerships to improve all phases
- Scale from 30 collaborations/month to 100+

---

*This project automates influencer discovery to help brands efficiently identify creators that match their specific vibes and values.*