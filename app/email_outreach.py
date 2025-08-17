"""
Email Outreach Module for Creator Review App
Handles email template generation and sending
"""
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import sys
from datetime import datetime
import json
import time
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.email_tracking_integration import EmailTrackingManager

load_dotenv()


class EmailOutreachManager:
    def __init__(self):
        self.email_templates = self.load_email_templates()
        
    def load_email_templates(self):
        """Load email templates or create defaults"""
        templates_file = "email_templates.json"
        if os.path.exists(templates_file):
            with open(templates_file, 'r') as f:
                return json.load(f)
        else:
            # Default templates
            default_templates = {
                "brand_collaboration": {
                    "subject": "Collaboration Opportunity with [BRAND_NAME]",
                    "body": """Hi {nickname}!

I've been following your content on TikTok, and your content really aligns with [BRAND_NAME]'s values of choosing your own path and living permission-free. {specific_post_mention}

I'm reaching out on behalf of [BRAND_NAME], a design-focused luggage brand. At the moment, you may not NEED another carry-on, but this brand is quite unique - they position themselves as a travel companion for people who choose their own path, and are on their journey to become the person they want to be. That's why you popped into my head and thought you might be a good fit.

I've attached more information about [BRAND_NAME] and our collaboration opportunities for you to review.

Let me know what you think! 

Best,
[YOUR_NAME]"""
                },
                "generic": {
                    "subject": "Partnership Opportunity - [BRAND_NAME]",
                    "body": """Hi {nickname}!

I've been following your content on TikTok, and your content really aligns with [BRAND_NAME]'s values of choosing your own path and living permission-free. {specific_post_mention}

I'm reaching out on behalf of [BRAND_NAME], a design-focused luggage brand. At the moment, you may not NEED another carry-on, but this brand is quite unique - they position themselves as a travel companion for people who choose their own path, and are on their journey to become the person they want to be. That's why you popped into my head and thought you might be a good fit.

With a bit more detail, I can see you're really a perfect fit for the brand. I've attached more information about [BRAND_NAME] and our collaboration opportunities for you to review.

Are you interested in learning more?

Best,
[YOUR_NAME]"""
                }
            }
            return default_templates
    
    def generate_personalized_email(self, creator_data, ai_analysis, template_key="generic", campaign_brief=""):
        """Generate a personalized email based on creator data and AI analysis"""
        profile = creator_data.get('profile', {})
        posts = creator_data.get('posts', [])
        
        # Extract personalization elements from AI analysis
        personalization = self._extract_personalization(ai_analysis, posts)
        
        # Get template
        template = self.email_templates.get(template_key, self.email_templates['generic'])
        
        # Fill in the template
        email_body = template['body'].format(
            nickname=profile.get('nickname', 'there'),
            specific_post_mention=personalization['specific_post_mention'],
            campaign_type=campaign_brief
        )
        
        return {
            'subject': template['subject'],
            'body': email_body,
            'to_email': profile.get('email', '')
        }
    
    def _extract_personalization(self, ai_analysis, posts):
        """Use LLM to extract Wonder-relevant personalization from existing AI analysis"""
        personalization = {
            'specific_post_mention': "Your authentic approach to sharing your journey really resonates with our brand."
        }
        
        # Use Claude to intelligently extract the most Wonder-relevant content
        try:
            import os
            import anthropic
            
            claude_api_key = os.getenv('ANTHROPIC_API_KEY')
            if not claude_api_key or not ai_analysis:
                return personalization
            
            # Prompt Claude to extract the most relevant content for Wonder
            prompt = f"""
You are analyzing a creator's content to find what would be most relevant for Wonder, a luggage brand that positions itself as a travel companion for people who choose their own path instead of staying on conventional paths.

Here is the AI analysis of this creator:
{ai_analysis}

Extract the SINGLE most relevant piece of content that aligns with Wonder's "choose your own path" values. Focus ONLY on:
- Specific quotes about independence, freedom, or unconventional choices
- Themes about personal growth, authenticity, or breaking from norms  
- Messages about self-empowerment or living authentically
- Content about choosing your own path vs following conventional expectations

DO NOT focus on general travel content (like destination weddings, vacation spots, or typical travel experiences) unless the creator's entire brand is about solo/unconventional travel that aligns with choosing your own path.

Return ONLY a single sentence for an email that varies the phrasing naturally. Use patterns like:
- "I love how you talk about [specific theme]"
- "Your content about [specific theme] really resonates with me"
- "I particularly enjoyed your post about [specific content]"
- "Your approach to [specific theme] really speaks to me"
- "I love your perspective on [specific theme]"
- "The way you discuss [specific theme] is so inspiring"

Do NOT use quotation marks around any extracted quotes or themes. Keep it under 15 words and make it personal and specific. If nothing strongly aligns with Wonder's values, return: "Your authentic approach to content creation really resonates with our brand."

Do not include any other text or explanation - just the single sentence.
"""
            
            client = anthropic.Anthropic(api_key=claude_api_key)
            
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=50,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            extracted_mention = message.content[0].text.strip()
            
            # Validate the response
            if (extracted_mention and 
                len(extracted_mention) < 150 and 
                any(start in extracted_mention.lower() for start in ['i love', 'your content', 'i particularly', 'your authentic']) and
                not any(avoid in extracted_mention.lower() for avoid in ['sorry', 'cannot', 'unable', 'error'])):
                personalization['specific_post_mention'] = extracted_mention
            
        except Exception as e:
            # If LLM extraction fails, fall back to default
            pass
        
        return personalization
    
    def send_email(self, to_email, subject, body, from_email=None, from_password=None, attachment_path=None, username=None, campaign=None):
        """Send email using SMTP with optional attachment and tracking"""
        if not from_email:
            from_email = os.getenv('SMTP_EMAIL')
        if not from_password:
            from_password = os.getenv('SMTP_PASSWORD')
            
        if not from_email or not from_password:
            return False, "Email credentials not configured"
        
        # Get SMTP settings from env or use Zoho defaults
        smtp_host = os.getenv('SMTP_HOST', 'smtp.zoho.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # Add tracking pixel if username and campaign provided
        tracking_id = None
        if username and campaign:
            tracker = EmailTrackingManager()
            pixel_html, tracking_id = tracker.get_tracking_pixel_html(username, campaign, recipient_email=to_email)
            # Convert body to HTML and add tracking pixel
            html_body = f"""
            <html>
            <body>
            {body.replace(chr(10), '<br>')}
            <br>
            {pixel_html}
            </body>
            </html>
            """
        else:
            html_body = None
        
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = from_email
            message['To'] = to_email
            message['Subject'] = subject
            
            # Add both plain text and HTML versions
            message.attach(MIMEText(body, 'plain'))
            if html_body:
                message.attach(MIMEText(html_body, 'html'))
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    
                    filename = os.path.basename(attachment_path)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}',
                    )
                    message.attach(part)
            
            # SMTP setup (works for Zoho, Gmail, etc.)
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(from_email, from_password)
            
            # Send email
            text = message.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            return True, "Email sent successfully!"
            
        except Exception as e:
            return False, f"Error sending email: {str(e)}"
    
    def get_sent_emails_count(self):
        """Get count of sent emails from tracking service"""
        # This could query the tracking service API in the future
        # For now, return 0 or implement tracking service integration
        return 0


def render_email_outreach_section(app, current_campaign=None):
    """Render the email outreach section in Streamlit"""
    st.header("📧 Email Outreach")
    
    # Get approved creators from the current campaign
    approved_creators = []
    if current_campaign and current_campaign != "➕ Create New Campaign":
        # Get from campaign-specific human review cache
        campaign_reviews = app.human_cache.get_campaign_reviews(current_campaign)
        approved_creators = [
            r['username'] for r in campaign_reviews
            if r['decision'] in ['approved', 'maybe']  # Include both approved and maybe
        ]
        st.info(f"Campaign: **{current_campaign}** - {len(approved_creators)} creators ready for outreach")
    else:
        # Fallback to legacy system if no campaign selected
        approved_creators = [
            username for username, review in app.reviews.items()
            if review.get('status') in ['Approved', 'Maybe']
        ]
        if not current_campaign:
            st.warning("⚠️ No campaign selected. Please select a campaign in the Creator Analysis tab.")
    
    if not approved_creators:
        st.info("No approved/maybe creators yet for this campaign. Review some creators first!")
        return
    
    # Email configuration check
    if not os.getenv('SMTP_EMAIL') or not os.getenv('SMTP_PASSWORD'):
        st.warning("⚠️ Email credentials not configured. Add SMTP_EMAIL and SMTP_PASSWORD to your .env file")
        with st.expander("📋 Email Setup Instructions"):
            st.markdown("""
            1. Create a `.env` file in your project root
            2. Add your email credentials:
            ```
            SMTP_EMAIL=your-email@zoho.com
            SMTP_PASSWORD=your-zoho-password
            SMTP_HOST=smtp.zoho.com  # Optional, defaults to Zoho
            SMTP_PORT=587           # Optional, defaults to 587
            ```
            
            **For Zoho Mail:**
            - Use your regular Zoho password (or app-specific password if 2FA enabled)
            - SMTP Server: smtp.zoho.com
            - Port: 587 (TLS) or 465 (SSL)
            
            **For other providers:**
            - Gmail: smtp.gmail.com (requires app password)
            - Outlook: smtp-mail.outlook.com
            - Yahoo: smtp.mail.yahoo.com
            """)
    
    # Initialize email manager
    email_manager = EmailOutreachManager()
    
    # Campaign settings
    col1, col2 = st.columns([2, 1])
    with col1:
        campaign_name = st.text_input("Campaign Name", value="Fall 2025 Campaign")
        brand_name = st.text_input("Brand Name", value="Wonder", help="The brand name for this campaign")
        your_name = st.text_input("Your Name", value="Olivia")
    
    with col2:
        template_choice = st.selectbox(
            "Email Template",
            options=list(email_manager.email_templates.keys()),
            format_func=lambda x: "TikTok Shop Focus" if x == "tiktok_shop" else "General Partnership" if x == "generic" else x.replace('_', ' ').title()
        )
        st.metric("Emails Sent", email_manager.get_sent_emails_count())
    
    # Creator selection
    st.subheader("Select Creators to Email")
    
    # Filter creators with emails
    creators_with_emails = []
    creators_without_emails = []
    
    for username in approved_creators:
        creator_data = app.content_db.get_creator_content(username)
        if creator_data and creator_data['profile'].get('email'):
            creators_with_emails.append((username, creator_data))
        else:
            creators_without_emails.append(username)
    
    if creators_with_emails:
        st.success(f"✅ {len(creators_with_emails)} creators with emails ready for outreach")
    
    if creators_without_emails:
        st.warning(f"⚠️ {len(creators_without_emails)} creators without emails: {', '.join(creators_without_emails)}")
        
        # Add button to extract emails for existing approved creators
        if st.button("🔍 Extract Emails for Missing Creators", help="Try to extract emails from bios of approved creators"):
            extracted_count = 0
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, username in enumerate(creators_without_emails):
                status_text.text(f"Extracting email for @{username}...")
                
                # Import the app from parent scope to access extraction method
                extracted_email = app.extract_and_cache_email(username)
                if extracted_email:
                    st.success(f"✅ Extracted: @{username} → {extracted_email}")
                    extracted_count += 1
                else:
                    st.info(f"ℹ️ No email found in @{username}'s bio")
                
                progress_bar.progress((i + 1) / len(creators_without_emails))
            
            status_text.text(f"✅ Extraction complete: {extracted_count} emails found")
            if extracted_count > 0:
                st.info("🔄 Refresh the page to see updated creator list")
                time.sleep(2)
                st.rerun()
    
    # Email preview and sending
    if creators_with_emails:
        selected_creator = st.selectbox(
            "Select creator to email",
            options=[c[0] for c in creators_with_emails],
            format_func=lambda x: f"@{x} - {next(c[1]['profile'].get('nickname', x) for c in creators_with_emails if c[0] == x)}"
        )
        
        if selected_creator:
            # Get creator data
            creator_data = next(c[1] for c in creators_with_emails if c[0] == selected_creator)
            creator_data['username'] = selected_creator
            
            # Get AI analysis
            ai_analysis = app.reviews[selected_creator].get('analysis', '')
            
            # Generate email
            email_draft = email_manager.generate_personalized_email(
                creator_data,
                ai_analysis,
                template_choice,
                campaign_name
            )
            
            # Email preview
            st.subheader("📝 Email Preview")
            
            # Make email editable
            email_to = st.text_input("To:", value=creator_data['profile'].get('email', ''))
            email_subject = st.text_input("Subject:", value=email_draft['subject'].replace('[BRAND_NAME]', brand_name))
            email_body = st.text_area(
                "Body:",
                value=email_draft['body'].replace('[BRAND_NAME]', brand_name).replace('[YOUR_NAME]', your_name),
                height=300
            )
            
            # Media Kit Upload Section
            st.subheader("📎 Attachment")
            st.info("💡 Your email mentions an attachment with collaboration details - make sure to upload your media kit!")
            media_kit = st.file_uploader(
                "Upload Media Kit with TikTok Shop Details (PDF recommended)", 
                type=['pdf', 'ppt', 'pptx', 'doc', 'docx'],
                help="This should include Wonder brand info, TikTok Shop commission structure, and performance bonus details"
            )
            
            attachment_path = None
            if media_kit:
                # Save uploaded file temporarily
                temp_dir = "temp_attachments"
                os.makedirs(temp_dir, exist_ok=True)
                attachment_path = os.path.join(temp_dir, media_kit.name)
                with open(attachment_path, "wb") as f:
                    f.write(media_kit.getbuffer())
                st.success(f"✅ Media kit ready: {media_kit.name}")
            
            # Creator info sidebar
            with st.expander("👤 Creator Info"):
                profile = creator_data['profile']
                st.write(f"**Username:** @{selected_creator}")
                st.write(f"**Nickname:** {profile.get('nickname', 'N/A')}")
                st.write(f"**Followers:** {profile.get('followers', 0):,}")
                st.write(f"**Email:** {profile.get('email', 'N/A')}")
            
            # Full AI Analysis in separate expander
            with st.expander("🤖 View Full AI Analysis", expanded=False):
                if ai_analysis:
                    st.markdown("**Complete AI Analysis:**")
                    st.text_area("", value=ai_analysis, height=300, disabled=True, key=f"ai_analysis_{selected_creator}")
                else:
                    st.info("No AI analysis available for this creator.")
            
            # Send buttons section
            st.subheader("📤 Send Options")
            
            # Test email section
            test_recipient = st.text_input(
                "Test Email Recipient", 
                placeholder="your.personal@gmail.com",
                help="Enter a different email address to test sending (e.g., your personal Gmail)"
            )
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                # Test email button
                if st.button("🧪 Send Test", help="Send test email to the address above"):
                    if test_recipient and '@' in test_recipient:
                        sender_email = os.getenv('SMTP_EMAIL')
                        st.info(f"Sending FROM: {sender_email}")
                        st.info(f"Sending TO: {test_recipient}")
                        success, message = email_manager.send_email(
                            test_recipient,
                            f"[TEST] {email_subject}",
                            f"THIS IS A TEST EMAIL\n\n{email_body}\n\n---\nSent from: {sender_email}",
                            attachment_path=attachment_path,
                            username=f"test_{selected_creator}",
                            campaign=campaign_name if campaign_name else "test"
                        )
                        if success:
                            st.success(f"✅ Test email sent!")
                            st.info(f"Check inbox at: {test_recipient}")
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("Please enter a valid test email address")
            
            with col2:
                # Real send button
                if st.button("📤 Send to Creator", type="primary"):
                    if email_to and email_subject and email_body:
                        success, message = email_manager.send_email(
                            email_to,
                            email_subject,
                            email_body,
                            attachment_path=attachment_path,
                            username=selected_creator,
                            campaign=campaign_name if campaign_name else "default"
                        )
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("Please fill in all email fields")
            
            with col2:
                if st.button("📋 Copy to Clipboard"):
                    clipboard_text = f"To: {email_to}\nSubject: {email_subject}\n\n{email_body}"
                    st.code(clipboard_text, language=None)
                    st.info("Email copied! You can paste it into your email client.")
            
    # Bulk actions
    st.subheader("🚀 Bulk Actions")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 Export Email List"):
            if creators_with_emails:
                export_data = []
                for username, creator_data in creators_with_emails:
                    export_data.append({
                        'username': username,
                        'email': creator_data['profile'].get('email', ''),
                        'nickname': creator_data['profile'].get('nickname', ''),
                        'followers': creator_data['profile'].get('followers', 0)
                    })
                
                import pandas as pd
                df = pd.DataFrame(export_data)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download Email List CSV",
                    data=csv,
                    file_name=f"creator_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    with col2:
        if st.button("📝 Generate All Drafts"):
            if creators_with_emails:
                all_drafts = []
                for username, creator_data in creators_with_emails:
                    creator_data['username'] = username
                    ai_analysis = app.reviews[username].get('analysis', '')
                    draft = email_manager.generate_personalized_email(
                        creator_data,
                        ai_analysis,
                        template_choice,
                        campaign_name
                    )
                    all_drafts.append({
                        'username': username,
                        'email': creator_data['profile'].get('email', ''),
                        'subject': draft['subject'].replace('[BRAND_NAME]', brand_name),
                        'body': draft['body'].replace('[BRAND_NAME]', brand_name).replace('[YOUR_NAME]', your_name)
                    })
                
                # Save drafts
                drafts_file = f"email_drafts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(drafts_file, 'w') as f:
                    json.dump(all_drafts, f, indent=2)
                
                st.success(f"✅ Generated {len(all_drafts)} email drafts!")
                st.download_button(
                    label="📥 Download All Drafts",
                    data=json.dumps(all_drafts, indent=2),
                    file_name=drafts_file,
                    mime="application/json"
                )
    
    with col3:
        if st.button("📤 Send Bulk Emails"):
            if not (os.getenv('SMTP_EMAIL') and os.getenv('SMTP_PASSWORD')):
                st.error("❌ Email credentials not configured. Please set SMTP_EMAIL and SMTP_PASSWORD in your .env file.")
            elif creators_with_emails:
                # Show preview and confirmation
                st.warning(f"⚠️ You are about to send {len(creators_with_emails)} emails. This action cannot be undone.")
                
                # Preview section
                with st.expander("📋 Preview First Email", expanded=True):
                    if creators_with_emails:
                        preview_username, preview_data = creators_with_emails[0]
                        preview_data['username'] = preview_username
                        preview_analysis = app.reviews[preview_username].get('analysis', '')
                        preview_draft = email_manager.generate_personalized_email(
                            preview_data,
                            preview_analysis,
                            template_choice,
                            campaign_name
                        )
                        st.write(f"**To:** {preview_data['profile'].get('email', '')}")
                        st.write(f"**Subject:** {preview_draft['subject'].replace('[BRAND_NAME]', brand_name)}")
                        st.text_area("**Body:**", 
                                   value=preview_draft['body'].replace('[BRAND_NAME]', brand_name).replace('[YOUR_NAME]', your_name),
                                   height=200, disabled=True)
                
                # Confirmation and send
                confirm_send = st.checkbox("✅ I confirm sending emails to all selected creators")
                
                if confirm_send and st.button("🚀 SEND ALL EMAILS", type="primary"):
                    success_count = 0
                    failed_emails = []
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, (username, creator_data) in enumerate(creators_with_emails):
                        status_text.text(f"Sending email to @{username}...")
                        
                        try:
                            creator_data['username'] = username
                            ai_analysis = app.reviews[username].get('analysis', '')
                            
                            # Generate personalized email
                            email_draft = email_manager.generate_personalized_email(
                                creator_data,
                                ai_analysis,
                                template_choice,
                                campaign_name
                            )
                            
                            # Send email with tracking
                            success, message = email_manager.send_email(
                                creator_data['profile'].get('email', ''),
                                email_draft['subject'].replace('[BRAND_NAME]', brand_name),
                                email_draft['body'].replace('[BRAND_NAME]', brand_name).replace('[YOUR_NAME]', your_name),
                                attachment_path=attachment_path,
                                username=username,
                                campaign=campaign_name if campaign_name else "bulk_send"
                            )
                            
                            if success:
                                success_count += 1
                            else:
                                failed_emails.append(f"@{username}: {message}")
                            
                            # Small delay to avoid overwhelming the SMTP server
                            time.sleep(2)
                            
                        except Exception as e:
                            failed_emails.append(f"@{username}: {str(e)}")
                        
                        # Update progress
                        progress_bar.progress((idx + 1) / len(creators_with_emails))
                    
                    # Show results
                    status_text.text("✅ Bulk email sending complete!")
                    
                    if success_count > 0:
                        st.success(f"✅ Successfully sent {success_count} emails!")
                        
                    if failed_emails:
                        st.error(f"❌ Failed to send {len(failed_emails)} emails:")
                        for error in failed_emails:
                            st.write(f"• {error}")
                    
                    if success_count > 0:
                        st.balloons()
            else:
                st.warning("No creators with emails available for bulk sending.")