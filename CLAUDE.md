# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an agentic workflow to identify TikTok creators that match specific brand vibes, automating the manual process of reviewing creators for brand fit. The project combines TikAPI for creator data fetching, TikTok MCP for subtitle extraction, and LLM-powered content analysis.
This is my side project, so it's important to keep the code clean and easy to understand, also keep the progress updates in the README.md file. always update the README.md file when the code is updated, and give me a recap of the progress when a new session starts. 

## Development Commands

**Prerequisites:**
```bash
pip install tikapi pandas
```

**Main Entry Points:**
- `python screen_creators.py` - Bulk creator screening system (main workflow)
- `python analyze_creator.py` - Individual creator analysis with full workflow
- `python tikapi_client.py` - Test TikAPI client functionality
- `python tiktok_mcp_client.py` - Test TikTok MCP integration

**No package.json, requirements.txt, or testing framework** is present - this is a Python script-based project with manual dependency installation.

## Architecture

The project follows a modular architecture with distinct components:

### Core Workflow
```
User query → Find relevant creators (filters) → 
Enrich top 100 → LLM scores JUST these 100 → 
Rank and return top 20
```

### Key Components

**1. Creator Screening Pipeline (`screen_creators.py`)**
- Main entry point for bulk creator processing
- Reads from `data.csv` (creator database), outputs to `qualified_creators.csv`
- Dual filtering criteria: 5K+ avg views AND posted within 60 days
- Filters out photo carousel posts, focuses on video content only
- Requires 3+ recent video posts for analysis
- Intelligent caching system to preserve API credits

**2. TikAPI Client (`tikapi_client.py`)**
- Modular client for TikTok creator data fetching
- Handles profile retrieval, recent posts, engagement metrics
- Photo vs video detection and filtering
- Error handling for API failures

**3. TikTok MCP Integration (`tiktok_mcp_client.py`)**
- Interfaces with TikTok MCP server for subtitle extraction
- Intelligent caching system (`subtitle_cache/` directory)
- Two implementations: full MCP client and simplified direct calls
- API key management and credit conservation

**4. Complete Analysis Workflow (`analyze_creator.py`)**
- Orchestrates TikAPI + MCP + LLM analysis
- Content pattern analysis (hashtags, themes, engagement)
- Creator classification and summary generation
- Configurable thresholds for subtitle extraction

### Data Flow
1. **Input**: CSV file with creator usernames and metadata
2. **TikAPI**: Fetch creator profiles and recent posts
3. **Filtering**: Remove photo posts, apply engagement/recency thresholds
4. **MCP**: Extract subtitles from qualifying videos (credit-conscious)
5. **Analysis**: Generate content patterns, themes, and creator classifications
6. **Output**: Qualified creators with detailed metrics

## Configuration

**API Keys** (hardcoded in files - should be externalized):
- TikAPI key in `tikapi_client.py:172`
- TikNeuron MCP API key in `tiktok_mcp_client.py:186`

**Filtering Thresholds**:
- Minimum average views: 5,000 (configurable in `CreatorScreener`)
- Maximum days since last post: 60 days
- Minimum video posts required: 3

**MCP Server Path**: `/Users/oliviachen/tiktok-mcp/build/index.js`

## File Structure

```
├── screen_creators.py          # Main bulk screening entry point
├── analyze_creator.py          # Individual creator analysis
├── tikapi_client.py           # TikAPI interface
├── tiktok_mcp_client.py       # MCP subtitle extraction
├── data.csv                   # Creator database (10 sample creators)
├── qualified_creators.csv     # Screening output
└── subtitle_cache/            # Cached subtitle files
```

## Development Notes

- **No testing framework** - manual testing through main entry points
- **Python script-based** - no build system or package management
- **Caching strategy** - Subtitle cache uses MD5 hashing for filename generation
- **Error handling** - Graceful degradation when APIs fail or credits insufficient
- **Rate limiting** - 2-second delays between API calls to avoid throttling

## Common Workflows

**Screen all creators:**
```bash
python screen_creators.py
# Processes data.csv → qualified_creators.csv
```

**Analyze single creator:**
```bash
python analyze_creator.py
# Modify username in file for different creators
```

**Test individual components:**
```bash
python tikapi_client.py        # Test TikAPI functionality
python tiktok_mcp_client.py    # Test MCP integration
```