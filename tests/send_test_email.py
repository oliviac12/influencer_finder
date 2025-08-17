#!/usr/bin/env python3
"""
Send a test email FROM your Zoho account TO a test recipient
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_test_outreach_email(recipient_email):
    """
    Send a test email FROM olivia@unsettled.xyz TO a specified recipient
    This simulates what will happen when you email creators
    """
    
    # Your Zoho credentials (SENDER)
    sender_email = os.getenv('SMTP_EMAIL')  # olivia@unsettled.xyz
    sender_password = os.getenv('SMTP_PASSWORD')
    smtp_host = os.getenv('SMTP_HOST', 'smtp.zoho.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    print("=" * 50)
    print("SENDING TEST OUTREACH EMAIL")
    print("=" * 50)
    print(f"\n📤 FROM: {sender_email} (your Zoho email)")
    print(f"📬 TO: {recipient_email}")
    
    # Create the email content (like what you'd send to a creator)
    subject = "Collaboration Opportunity with Wonder"
    
    body = """Hi there!

I've been following your content on TikTok and I'm genuinely impressed by your authentic storytelling and creative style.

I'm reaching out from Wonder because we think your content perfectly aligns with our brand values of choosing your own path and living permission-free.

We'd love to discuss a paid partnership opportunity for our upcoming Fall 2025 campaign. Are you open to brand collaborations?

Looking forward to hearing from you!

Best,
Olivia
Wonder Team

---
This is a test email from the Influencer Finder system.
"""
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email  # FROM: olivia@unsettled.xyz
    msg['To'] = recipient_email  # TO: the test recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    # Send the email
    try:
        print(f"\n🔌 Connecting to Zoho SMTP server...")
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        
        print(f"📨 Sending email...")
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        
        print(f"\n✅ SUCCESS! Email sent:")
        print(f"   FROM: {sender_email}")
        print(f"   TO: {recipient_email}")
        print(f"   Subject: {subject}")
        print(f"\n   The recipient should receive the email shortly!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to send email: {str(e)}")
        return False

def main():
    print("\n🚀 INFLUENCER FINDER - EMAIL SENDER TEST\n")
    
    # Ask for recipient email
    print("This will send a test email FROM olivia@unsettled.xyz")
    print("Enter the recipient email address (who should receive the test):")
    print("(You can use your personal email or a test email)")
    
    recipient = input("Recipient email: ").strip()
    
    if not recipient or '@' not in recipient:
        print("❌ Invalid email address")
        return
    
    print(f"\nConfirm: Send test email FROM olivia@unsettled.xyz TO {recipient}?")
    print("Type 'yes' to confirm: ")
    
    if input().strip().lower() == 'yes':
        send_test_outreach_email(recipient)
    else:
        print("Cancelled")

if __name__ == "__main__":
    # You can also call this directly with a recipient:
    # send_test_outreach_email("test@example.com")
    
    # For now, let's send to a test address you specify
    print("Sending test email FROM olivia@unsettled.xyz")
    print("Please specify a test recipient email:")
    recipient = input("Send test TO: ").strip()
    
    if recipient:
        send_test_outreach_email(recipient)
    else:
        print("No recipient specified")