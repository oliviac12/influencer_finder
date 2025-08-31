"""
Cancel old scheduled emails and reschedule with correct template
"""
from utils.zoho_native_scheduler import ZohoNativeScheduler
import time

# Initialize scheduler
scheduler = ZohoNativeScheduler()

print("🗑️ Cancelling previously scheduled emails...")
print("="*60)

# Unfortunately we don't have the email IDs from the previous run
# Let's check if we can get scheduled emails
scheduled_emails = scheduler.get_scheduled_emails()

if scheduled_emails:
    print(f"Found {len(scheduled_emails)} scheduled emails")
    for email in scheduled_emails:
        email_id = email.get('messageId') or email.get('id')
        if email_id:
            if scheduler.cancel_scheduled_email(email_id):
                print(f"  ✅ Cancelled email {email_id}")
            else:
                print(f"  ❌ Failed to cancel {email_id}")
            time.sleep(0.5)
else:
    print("⚠️ Could not retrieve scheduled emails via API")
    print("Note: Zoho API may not support listing scheduled emails")
    print("You may need to manually cancel them from Zoho Mail's Outbox")

print("\n" + "="*60)
print("Now rescheduling with correct template and attachment...")
print("="*60)

# Now run the updated scheduling script
exec(open('schedule_zoho_batch.py').read())