# 📧 Email Scheduler App

A standalone Streamlit app for scheduling bulk emails via Zoho with automatic rate limit management.

## Features

- **📤 Bulk Email Scheduling**: Schedule emails to multiple recipients
- **⏱️ Rate Limit Management**: Automatically handles Zoho's 50 emails/hour limit
- **📎 Attachment Support**: Include PDFs or other files
- **🌍 Timezone Support**: Schedule in any timezone
- **📝 Template Personalization**: Use `{username}` to personalize emails
- **📊 Progress Tracking**: Real-time scheduling progress
- **📈 Session History**: Track all scheduled emails in current session

## Quick Start

```bash
# Run the app
python3 app/run_email_scheduler.py

# Or directly with Streamlit
streamlit run app/email_scheduler_app.py
```

## How to Use

### 1. Prepare Your Recipients

**Option A: CSV Upload**
Create a CSV file with columns:
- `username`: Creator username (without @)
- `email`: Email address

Example:
```csv
username,email
lisa.mariee1,serranolisa98@gmail.com
lauren.clutter,hello@laurenclutter.com
```

**Option B: Manual Input**
Enter directly in the app:
```
lisa.mariee1,serranolisa98@gmail.com
lauren.clutter,hello@laurenclutter.com
```

### 2. Configure Email Template

- **Subject**: Can include `{username}` for personalization
- **Body**: HTML supported, use `{username}` to insert creator name
- **Attachment**: Optional, provide full path to file

### 3. Set Schedule

- Choose specific date/time or send immediately
- Select timezone
- App automatically calculates batching for rate limits

### 4. Review & Send

- Preview recipient count and timing
- Click "Schedule Emails" to begin
- Monitor progress in real-time

## Rate Limit Configuration

Default settings (safe for Zoho):
- **30 emails per batch**: Stays well under 50/hour limit
- **3 minutes between emails**: Smooth delivery
- **40 minutes between batches**: Rate limit reset time

You can adjust these in the sidebar based on your needs.

## Example Timing

For 100 recipients with default settings:
- Batch 1: Recipients 1-30 (0-87 minutes)
- 40 minute gap
- Batch 2: Recipients 31-60 (127-214 minutes) 
- 40 minute gap
- Batch 3: Recipients 61-90 (254-341 minutes)
- 40 minute gap
- Batch 4: Recipients 91-100 (381-408 minutes)

Total time: ~6.8 hours

## Files

- `app/email_scheduler_app.py` - Main Streamlit app
- `app/run_email_scheduler.py` - Runner script
- `data/email_scheduler_template.csv` - Sample CSV template
- `utils/zoho_native_scheduler.py` - Zoho scheduling backend

## Requirements

- Python 3.8+
- Streamlit
- Pandas
- Zoho OAuth credentials configured in `.env`

## Troubleshooting

**"Attachment not found"**
- Ensure you're using the full absolute path
- Check file exists: `/Users/oliviachen/influencer_finder/shared_attachments/Wonder_InfluenceKit_fall2025.pdf`

**"Rate limit exceeded"**
- Reduce emails per batch in sidebar
- Increase gap between batches

**"Authentication failed"**
- Check Zoho credentials in `.env` file
- Ensure refresh token is valid

## Notes

- All scheduled emails appear in your Zoho Outbox
- You can cancel scheduled emails directly in Zoho Mail
- The app tracks session history (resets when app restarts)
- Attachments are uploaded once per email (may take time for large files)