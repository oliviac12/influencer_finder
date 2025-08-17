# Wonder Email Tracking Service

A simple Flask-based email tracking service for the Wonder influencer campaign. Tracks email opens via 1x1 tracking pixels and provides analytics.

## 🚀 Quick Setup on Replit

### 1. Create New Replit
- Go to [replit.com](https://replit.com)
- Create new Repl → Python (Flask)
- Name it: `wonder-email-tracking`

### 2. Copy Files
Copy these 4 files into your Replit:
- `main.py`
- `database.py` 
- `requirements.txt`
- `README.md` (this file)

### 3. Deploy
- Click **"Run"** in Replit
- Your service will be live at `https://wonder-email-tracking.YOUR-USERNAME.repl.co`

### 4. Connect Your Domain
- In Replit, go to the **"Domains"** tab
- Add your custom domain: `tracking.unsettled.xyz`
- Replit will show you need to add a CNAME record
- Go to your domain registrar and add:
  - Type: CNAME
  - Name: tracking
  - Value: unsettled-oliviac121.replit.app

## 📡 API Endpoints

Once deployed, your service provides:

### Tracking Pixel
```
GET https://tracking.unsettled.xyz/track/open?id=EMAIL_ID&campaign=CAMPAIGN_NAME
```
- Returns 1x1 transparent pixel
- Logs email open event

### Stats API (for Streamlit integration)
```
GET https://tracking.unsettled.xyz/api/stats
```
Returns JSON:
```json
{
  "success": true,
  "overall": {
    "total_opens": 15,
    "unique_opens": 12,
    "open_rate": 85.7,
    "recent_opens_24h": 3
  },
  "campaigns": {
    "wonder_fall2025": {
      "opens": 8,
      "unique": 7,
      "rate": 87.5
    }
  }
}
```

### Campaign-Specific Stats
```
GET https://unsettled.xyz/api/campaign/wonder_fall2025
```

### Web Dashboard
```
GET https://unsettled.xyz/stats
```
- Human-readable stats page
- Campaign breakdowns
- Real-time data

## 🔗 Integration with Streamlit App

Your Streamlit app can fetch tracking data:

```python
import requests

# Get tracking stats
response = requests.get("https://unsettled.xyz/api/stats")
stats = response.json()

print(f"Open rate: {stats['overall']['open_rate']}%")
```

## 📧 Email Integration

Add tracking pixels to your emails by including this HTML:

```html
<img src="https://unsettled.xyz/track/open?id=wonder_USERNAME_TIMESTAMP&campaign=wonder_fall2025" 
     width="1" height="1" style="display:none;">
```

## 🔧 Testing

Test your tracking:
1. Visit: `https://unsettled.xyz/test`
2. Check stats: `https://unsettled.xyz/stats`
3. Should see 1 open logged

## 📊 Features

- **Email open tracking** with timestamps
- **Campaign segmentation** 
- **IP address logging** (for geolocation)
- **User agent detection** (device/email client)
- **SQLite database** (reliable, no external dependencies)
- **JSON API** for integration
- **Web dashboard** for monitoring

## 🛡️ Privacy & Security

- Only logs opens, not email content
- IP addresses stored for analytics only
- No personal data beyond email IDs
- Compliant with standard email tracking practices

## 🚨 Important Notes

1. **Always-On**: Make sure your Replit has "Always On" enabled (Replit Pro)
2. **Domain**: Connect `unsettled.xyz` properly for production use
3. **Backup**: Replit backs up your SQLite database automatically

## 💡 Next Steps

After deployment:
1. Test tracking with a few emails
2. Integrate stats API into your Streamlit app
3. Monitor open rates and campaign performance
4. Consider adding click tracking for links

## 🆘 Troubleshooting

**Tracking not working?**
- Check if domain is properly connected
- Verify emails contain proper tracking pixel HTML
- Test with `/test` endpoint first

**Need help?**
- Check Replit logs for errors
- Verify database is being created (`email_tracking.db`)
- Test API endpoints manually