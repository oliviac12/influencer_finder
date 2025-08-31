"""
Schedule batch emails using Zoho Native Scheduler
Tomorrow at 6am PT with 3-minute intervals
"""
import csv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from utils.zoho_native_scheduler import ZohoNativeScheduler

# Read the CSV file
creators_to_email = []
with open('schedule_batch_emails.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        creators_to_email.append({
            'username': row['creator_username'],
            'email': row['email']
        })

print(f"📧 Preparing to schedule {len(creators_to_email)} emails")
print("="*60)

# Email template - personalized with username
def create_email_body(username):
    return f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<p>Hi {username}!</p>

<p>I've been following your content on TikTok, and your content really aligns with Wonder's values of choosing your own path and living permission-free. Your authentic approach to sharing your journey really resonates with our brand.</p>

<p>I'm reaching out on behalf of Wonder, a design-focused luggage brand. At the moment, you may not NEED another carry-on, but this brand is quite unique - they position themselves as a travel companion for people who choose their own path, and are on their journey to become the person they want to be. That's why you popped into my head and thought you might be a good fit.</p>

<p>I don't want this email to sound like we just talk budget - the most important thing is that we love who you are and who you are becoming. This is a commission-based campaign with gifted carry-on and very attractive performance bonuses on top. We're preparing for the launch in fall and upcoming holiday season and looking for the right creators to partner with during this exciting time.</p>

<p>I've attached more information about Wonder and our collaboration opportunities for you to review.</p>

<p>Let me know what you think!</p>
</body>
</html>
"""

# Initialize scheduler
scheduler = ZohoNativeScheduler()

# Set start time: Tomorrow at 6am PT
pacific_tz = ZoneInfo("US/Pacific")
tomorrow = datetime.now(pacific_tz).replace(hour=6, minute=0, second=0, microsecond=0) + timedelta(days=1)

print(f"📅 Scheduling emails starting at: {tomorrow.strftime('%Y-%m-%d %I:%M %p %Z')}")
print(f"⏰ Interval: 3 minutes between emails")
print("="*60)

# Prepare emails for scheduling
emails_to_schedule = []
for creator in creators_to_email:
    emails_to_schedule.append({
        'username': creator['username'],
        'email': creator['email'],
        'subject': "TikTok Shop Collab with Wonder ✨",
        'body': create_email_body(creator['username']),
        'attachment_path': '/Users/oliviachen/influencer_finder/shared_attachments/Wonder_InfluenceKit_fall2025.pdf'
    })

# Schedule the emails
print("\nScheduling emails...")
scheduled_ids = scheduler.schedule_bulk_emails(
    emails=emails_to_schedule,
    campaign="manual_outreach_batch1",
    start_time=tomorrow,
    interval_minutes=3  # 3 minutes between each email
)

# Summary
print("\n" + "="*60)
print("✅ SCHEDULING COMPLETE!")
print("="*60)
print(f"📧 Total scheduled: {len(scheduled_ids)} emails")
print(f"📅 First email: {tomorrow.strftime('%I:%M %p %Z')}")
end_time = tomorrow + timedelta(minutes=3 * (len(creators_to_email) - 1))
print(f"📅 Last email: {end_time.strftime('%I:%M %p %Z')}")
print(f"⏱️ Total duration: {3 * (len(creators_to_email) - 1)} minutes")
print("\n📋 Creators being emailed:")
for i, creator in enumerate(creators_to_email, 1):
    send_time = tomorrow + timedelta(minutes=3 * (i - 1))
    print(f"  {i}. @{creator['username']} at {send_time.strftime('%I:%M %p')}")
print("="*60)