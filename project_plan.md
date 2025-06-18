# Influencer Finder Project Plan

## Project Overview
Build an agentic workflow to identify TikTok creators that match specific brand vibes, automating the manual process of reviewing creators for brand fit.

## Current Challenge
- Need to reach out to 300+ creators monthly to achieve 30 collaborations
- Manual process involves:
  - Starting with large database
  - Filtering by hard requirements (TikTok Shop, email available, US-based, category)
  - Manual content review for brand fit (time-consuming)

## Proposed Solution: Search Tool Architecture

### Why Search Tool > Pre-computed Database
1. **Flexibility** - Each brand/campaign needs different vibes
2. **Speed to value** - Can start immediately with queries like "Find creators similar to @example"
3. **Learning loop** - Discover what queries work through usage
4. **Efficiency** - Only analyze creators on-demand (can use sophisticated analysis)

### Architecture
```
User query → Find relevant creators (filters) → 
Enrich top 100 → LLM scores JUST these 100 → 
Rank and return top 20
```

## Data Scale & Approach
- ~109,000 US TikTok creators with 50K+ followers
- Manageable database size (~100MB)
- Can do monthly full refreshes from commercial APIs

## 2-Week Semi-Automated Search Tool MVP

### Week 1: Data + Basic Search
- Export 500 creators from Modash (mix of typical categories)
- Build simple database: handle, followers, category, bio
- Create basic search: "sustainable fashion creators 50K-200K followers"
- Use TikTok MCP to pull last 3 videos + subtitles for search results
- Simple LLM prompt: "Does this creator match [brand vibe description]?"

### Week 2: Refinement + Validation
- Add similarity search: "Find creators like @specificcreator"
- Improve LLM analysis:
  - Comment sentiment analysis
  - Posting consistency
  - Content themes
- Build simple UI showing:
  - Creator stats
  - Why they match (LLM explanation)
  - Recent content summary
  - Confidence score
- Validation with head of brand:
  - Run 10 searches
  - Track precision: Of top 10 results, how many pass the bar?
  - Track coverage: Did we miss obvious good fits?
  - Track efficiency: Can they review 50 creators in 30 mins vs 2 hours?

### Success Metrics
- Head of brand approves >70% of top-ranked results
- Significant time savings in creator review process
- Clear signal that LLM analysis correlates with brand fit

## Available Tools
- **TikTok MCP**: Pull video subtitles and comments
- **Bright Data**: Web scraping if needed
- **Commercial APIs**: Modash for initial creator discovery

## Immediate Next Steps

### 1. Simple POC (1-2 days)
- Get sample of 30 creators (manual selection or small API pull)
- Use TikTok MCP to analyze their content
- Have LLM score brand fit
- Validate with human review
- **Goal**: Confirm LLM can accurately detect brand fit

### 2. API Vendor Decision
After POC validation, evaluate:
- Modash
- CreatorIQ
- HypeAuditor
- Other options based on cost, data quality, and API capabilities

### 3. Build Search Tool (First Phase)
- This is just the foundation
- Enables efficient discovery and filtering
- Reduces manual review time

## 2-Week Semi-Automated Search Tool MVP

### Week 1: Data + Basic Search
- Export 500 creators from Modash (mix of typical categories)
- Build simple database: handle, followers, category, bio
- Create basic search: "sustainable fashion creators 50K-200K followers"
- Use TikTok MCP to pull last 3 videos + subtitles for search results
- Simple LLM prompt: "Does this creator match [brand vibe description]?"

### Week 2: Refinement + Validation
- Add similarity search: "Find creators like @specificcreator"
- Improve LLM analysis:
  - Comment sentiment analysis
  - Posting consistency
  - Content themes
- Build simple UI showing:
  - Creator stats
  - Why they match (LLM explanation)
  - Recent content summary
  - Confidence score
- Validation with head of brand:
  - Run 10 searches
  - Track precision: Of top 10 results, how many pass the bar?
  - Track coverage: Did we miss obvious good fits?
  - Track efficiency: Can they review 50 creators in 30 mins vs 2 hours?

### Success Metrics
- Head of brand approves >70% of top-ranked results
- Significant time savings in creator review process
- Clear signal that LLM analysis correlates with brand fit

## Full Product Vision

### Phase 1: Discovery & Analysis (Search Tool)
- Find creators matching brand vibe
- LLM-powered content analysis
- Ranked results with explanations

### Phase 2: Agentic Outreach
- Automatically draft personalized outreach based on:
  - Media brief requirements
  - Creator's content style
  - Past successful collaborations
- Send initial outreach emails
- Track open/response rates

### Phase 3: Agentic Response & Management
- Parse creator responses
- Negotiate terms within parameters
- Answer common questions
- Schedule content deliverables
- Track campaign progress
- Flag issues for human review

## Long-term Vision
- Fully automated pipeline: discovery → outreach → negotiation → management
- Human-in-the-loop for approvals and edge cases
- Learn from successful partnerships to improve all phases
- Scale from 30 collaborations/month to 100+