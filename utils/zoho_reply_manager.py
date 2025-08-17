"""
Zoho Reply Manager
Fetches and manages email replies from Zoho inbox
Generates AI-powered responses using Claude
"""
import os
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import json
import re
import anthropic
from typing import List, Dict, Optional
import smtplib
from dotenv import load_dotenv

load_dotenv()


class ZohoReplyManager:
    def __init__(self):
        self.email_address = os.getenv('SMTP_EMAIL')
        self.password = os.getenv('SMTP_PASSWORD')
        self.imap_host = 'imappro.zoho.com'  # Updated to correct server
        self.imap_port = 993
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.zoho.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.replies_cache = "cache/email_replies.json"
        self.ensure_cache_exists()
    
    def ensure_cache_exists(self):
        """Create cache directory and file if they don't exist"""
        os.makedirs(os.path.dirname(self.replies_cache), exist_ok=True)
        if not os.path.exists(self.replies_cache):
            with open(self.replies_cache, 'w') as f:
                json.dump({}, f)
    
    def connect_imap(self):
        """Connect to Zoho IMAP server"""
        try:
            # Connect to Zoho IMAP
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            mail.login(self.email_address, self.password)
            return mail
        except Exception as e:
            print(f"Error connecting to Zoho IMAP: {e}")
            return None
    
    def fetch_recent_replies(self, days_back=7, campaign_keyword="Wonder", show_all=False):
        """
        Fetch recent replies from Zoho inbox
        Filters for replies to our campaign emails
        """
        replies = []
        
        try:
            mail = self.connect_imap()
            if not mail:
                return []
            
            # Select inbox
            mail.select('INBOX')
            
            # Calculate date for search
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            
            # Search for recent emails
            # Get ALL recent emails, we'll filter later
            search_criteria = f'(SINCE "{since_date}")'
            
            typ, data = mail.search(None, search_criteria)
            
            if typ != 'OK':
                return []
            
            email_ids = data[0].split()
            
            # Process most recent emails first
            email_ids = email_ids[-100:]  # Last 100 emails max
            email_ids.reverse()  # Most recent first
            
            print(f"📧 Checking {len(email_ids)} recent emails...")
            
            # Fetch each email
            for email_id in email_ids:
                try:
                    typ, msg_data = mail.fetch(email_id, '(RFC822)')
                    
                    if typ != 'OK':
                        continue
                    
                    # Parse email
                    email_body = msg_data[0][1]
                    message = email.message_from_bytes(email_body)
                    
                    # Extract email details
                    subject = message.get('Subject', '')
                    from_addr = message.get('From', '')
                    to_addr = message.get('To', '')
                    date = message.get('Date', '')
                    in_reply_to = message.get('In-Reply-To', '')
                    references = message.get('References', '')
                    
                    # Skip emails FROM us (sent emails)
                    if self.email_address and self.email_address.lower() in from_addr.lower():
                        continue
                    
                    # More flexible reply detection
                    is_reply = any([
                        'RE:' in subject.upper(),
                        'Re:' in subject,
                        in_reply_to is not None and in_reply_to != '',
                        references is not None and references != ''
                    ])
                    
                    # More flexible campaign detection
                    is_campaign_related = any([
                        campaign_keyword.lower() in subject.lower(),
                        campaign_keyword.lower() in str(message).lower()[:1000],  # Check first 1000 chars
                        'collaboration' in subject.lower(),
                        'partnership' in subject.lower(),
                        'wonder_fall2025' in str(message).lower()
                    ])
                    
                    # Include email if it's either a reply OR campaign-related OR show_all is True
                    if show_all or is_reply or is_campaign_related:
                        # Extract email body
                        body = self.extract_email_body(message)
                        
                        # Extract sender details
                        sender_email = self.extract_email_address(from_addr)
                        sender_name = self.extract_sender_name(from_addr)
                        
                        # Try to match to a creator username
                        username = self.match_to_creator(sender_email, sender_name)
                        
                        replies.append({
                            'id': str(email_id),
                            'subject': subject,
                            'from': from_addr,
                            'from_email': sender_email,
                            'from_name': sender_name,
                            'to': to_addr,
                            'date': date,
                            'body': body,
                            'is_reply': is_reply,
                            'in_reply_to': in_reply_to,
                            'references': references,
                            'username': username,
                            'campaign_related': is_campaign_related
                        })
                
                except Exception as e:
                    print(f"Error processing email {email_id}: {e}")
                    continue
            
            # Close connection
            mail.logout()
            
            # Cache the replies
            self.cache_replies(replies)
            
            return replies
            
        except Exception as e:
            print(f"Error fetching replies: {e}")
            return []
    
    def extract_email_body(self, message):
        """Extract plain text body from email message"""
        body = ""
        
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                body = message.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(message.get_payload())
        
        return body.strip()
    
    def extract_email_address(self, from_field):
        """Extract email address from From field"""
        email_match = re.search(r'<(.+?)>', from_field)
        if email_match:
            return email_match.group(1)
        elif '@' in from_field:
            return from_field.strip()
        return ""
    
    def extract_sender_name(self, from_field):
        """Extract sender name from From field"""
        name_match = re.match(r'^(.+?)<', from_field)
        if name_match:
            return name_match.group(1).strip().strip('"')
        return from_field.split('@')[0] if '@' in from_field else from_field
    
    def match_to_creator(self, sender_email, sender_name):
        """Try to match email to a creator username"""
        # This would ideally check against your creator database
        # For now, extract from email or name
        if sender_email:
            username = sender_email.split('@')[0]
            # Remove common email prefixes
            for prefix in ['hello', 'info', 'contact', 'business', 'collab']:
                if username.startswith(prefix):
                    username = username[len(prefix):]
            return username
        return sender_name.lower().replace(' ', '')
    
    def cache_replies(self, replies):
        """Cache replies to avoid re-fetching"""
        with open(self.replies_cache, 'w') as f:
            json.dump(replies, f, indent=2, default=str)
    
    def get_cached_replies(self):
        """Get cached replies"""
        try:
            with open(self.replies_cache, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def generate_ai_response(self, original_email, reply_content, creator_username, campaign_context):
        """
        Use Claude to generate an appropriate response
        """
        try:
            claude_api_key = os.getenv('ANTHROPIC_API_KEY')
            if not claude_api_key:
                return "API key not configured"
            
            prompt = f"""
You are helping respond to an influencer who replied to our Wonder brand collaboration outreach email.

Original outreach subject: {original_email.get('subject', 'Collaboration with Wonder')}
Creator username: @{creator_username}
Their reply: {reply_content}

Campaign context: {campaign_context}

Based on their reply, generate an appropriate response that:
1. Acknowledges their message professionally
2. Answers any questions they have
3. Moves the conversation forward toward collaboration
4. Maintains Wonder's brand voice (authentic, permission-free living)
5. Keeps it concise (under 150 words)

If they're interested: Provide next steps (media kit, commission structure, product samples)
If they have questions: Answer clearly and offer to schedule a call
If they're not interested: Thank them graciously and leave door open

Generate ONLY the email body text, no subject line or signature.
"""
            
            client = anthropic.Anthropic(api_key=claude_api_key)
            
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text.strip()
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def send_reply(self, to_email, subject, body, in_reply_to=None, references=None):
        """
        Send a reply using existing SMTP configuration
        """
        try:
            # Create message
            message = MIMEMultipart()
            message['From'] = self.email_address
            message['To'] = to_email
            message['Subject'] = subject if subject.startswith('Re:') else f"Re: {subject}"
            
            # Add threading headers for proper email threading
            if in_reply_to:
                message['In-Reply-To'] = in_reply_to
            if references:
                message['References'] = references
            
            # Add body
            message.attach(MIMEText(body, 'plain'))
            
            # Send via SMTP
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.email_address, self.password)
            
            text = message.as_string()
            server.sendmail(self.email_address, to_email, text)
            server.quit()
            
            return True, "Reply sent successfully"
            
        except Exception as e:
            return False, f"Error sending reply: {str(e)}"
    
    def mark_reply_as_handled(self, reply_id):
        """Mark a reply as handled in our cache"""
        replies = self.get_cached_replies()
        for reply in replies:
            if reply.get('id') == reply_id:
                reply['handled'] = True
                reply['handled_at'] = datetime.now().isoformat()
        self.cache_replies(replies)


# Test the reply manager
if __name__ == "__main__":
    manager = ZohoReplyManager()
    
    # Test fetching replies
    print("🔍 Fetching recent replies...")
    replies = manager.fetch_recent_replies(days_back=7)
    
    print(f"📧 Found {len(replies)} potential replies")
    for reply in replies[:3]:
        print(f"  From: {reply['from_name']} <{reply['from_email']}>")
        print(f"  Subject: {reply['subject']}")
        print(f"  Date: {reply['date']}")
        print(f"  Preview: {reply['body'][:100]}...")
        print()