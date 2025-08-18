# Supabase Email Draft Cache Setup

## Overview

This guide helps you set up persistent email draft caching using Supabase to solve the container restart issue on Streamlit Cloud.

## Files Created

1. **`supabase_migrations/001_email_draft_cache.sql`** - Database schema
2. **`utils/supabase_email_draft_cache.py`** - Python client implementation
3. **`migrate_email_cache_to_supabase.py`** - Migration script

## Setup Steps

### 1. Create Supabase Table

Go to your Supabase dashboard and run the SQL migration:

```bash
# In Supabase SQL Editor, run:
supabase_migrations/001_email_draft_cache.sql
```

This creates the `email_draft_cache` table with proper indexes and RLS policies.

### 2. Set Environment Variables

Add to your `.env` file and Streamlit Cloud secrets:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Install Dependencies

Add to requirements.txt:
```
supabase>=2.0.0
```

### 4. Migrate Existing Cache

Run the migration script to transfer your 26 cached drafts:

```bash
python3 migrate_email_cache_to_supabase.py
```

### 5. Update Email Outreach Code

The `utils/supabase_email_draft_cache.py` has the same interface as the file-based cache, so integration should be seamless.

## Key Benefits

- ✅ **Persistent**: Survives container restarts
- ✅ **Shared**: Same cache across Streamlit Cloud and Replit
- ✅ **Fast**: Database indexes for quick lookups
- ✅ **Reliable**: ACID transactions and backups
- ✅ **Scalable**: No file system limitations

## Database Schema

```sql
email_draft_cache (
    id UUID PRIMARY KEY,
    username TEXT NOT NULL,
    campaign TEXT NOT NULL,
    subject TEXT,
    body TEXT,
    email TEXT,
    personalization TEXT,
    generated_at TIMESTAMP WITH TIME ZONE,
    edited_at TIMESTAMP WITH TIME ZONE,
    version INTEGER DEFAULT 1,
    
    UNIQUE (username, campaign)
)
```

## Migration Status

Current local cache contains:
- **26 drafts** for `wonder_fall2025` campaign
- Each draft has personalized content from LLM analysis
- Format: `{campaign}_{username}` cache keys

After migration, these will be accessible from both:
- Streamlit Cloud (persistent across restarts)
- Replit (shared cache)
- Local development (same data everywhere)

## Testing

Test the implementation:

```bash
# Test Supabase connection and basic operations
python3 utils/supabase_email_draft_cache.py
```

## Next Steps

1. Run the SQL migration in Supabase dashboard
2. Set environment variables in Streamlit Cloud
3. Run migration script locally
4. Update email outreach to use Supabase cache
5. Test persistence by restarting containers

This solves the core problem: "draft is disappearing when I refresh or restart" ✅