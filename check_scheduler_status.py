#!/usr/bin/env python3
"""
Quick scheduler status checker
"""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# Load scheduled emails
with open('cache/scheduled_emails.json', 'r') as f:
    emails = json.load(f)

pacific_tz = ZoneInfo("US/Pacific")
now = datetime.now(pacific_tz)

print(f"Current time: {now.strftime('%I:%M:%S %p PT')}")
print("\nScheduled emails:")

for email_id, data in emails.items():
    scheduled_time = datetime.fromisoformat(data['scheduled_time'])
    if scheduled_time.tzinfo is None:
        scheduled_time = scheduled_time.replace(tzinfo=pacific_tz)
    
    status = data['status']
    to_email = data['to_email']
    
    if status == 'pending':
        time_diff = scheduled_time - now
        if time_diff.total_seconds() > 0:
            minutes = int(time_diff.total_seconds() / 60)
            seconds = int(time_diff.total_seconds() % 60)
            print(f"  📬 PENDING: {to_email} - sends in {minutes}m {seconds}s")
        else:
            overdue_minutes = int(abs(time_diff.total_seconds()) / 60)
            print(f"  ⚠️  OVERDUE: {to_email} - was due {overdue_minutes} minutes ago!")
    elif status == 'sent':
        print(f"  ✅ SENT: {to_email} - sent at {data.get('sent_at', 'unknown time')}")
    else:
        print(f"  ❌ {status.upper()}: {to_email}")