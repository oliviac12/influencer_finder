"""
Email Outreach Module for Creator Review App - Redesigned Layout
Handles bulk email draft generation and sending with expandable views
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
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.email_tracking_integration import EmailTrackingManager
from utils.email_draft_cache import EmailDraftCache
from email_scheduling_ui import render_scheduling_section

load_dotenv()


class EmailOutreachManager:
    def __init__(self):
        self.email_templates = self.load_email_templates()
        self.sent_status = self.load_sent_status()
        self.draft_cache = EmailDraftCache()
        
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
    
    def load_sent_status(self):
        """Load sent email status"""
        sent_file = "cache/sent_email_status.json"
        if os.path.exists(sent_file):
            with open(sent_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_sent_status(self):
        """Save sent email status"""
        sent_file = "cache/sent_email_status.json"
        os.makedirs(os.path.dirname(sent_file), exist_ok=True)
        with open(sent_file, 'w') as f:
            json.dump(self.sent_status, f, indent=2)
    
    def mark_as_sent(self, username, campaign):
        """Mark an email as sent"""
        key = f"{campaign}_{username}"
        self.sent_status[key] = {
            "sent_at": datetime.now().isoformat(),
            "campaign": campaign
        }
        self.save_sent_status()
    
    def is_sent(self, username, campaign):
        """Check if email was sent"""
        key = f"{campaign}_{username}"
        return key in self.sent_status
    
    def generate_personalized_email(self, creator_data, ai_analysis, template_key="generic", campaign_brief="", 
                                   username=None, use_cache=True):
        """Generate a personalized email based on creator data and AI analysis"""
        profile = creator_data.get('profile', {})
        
        # Check cache first if username and campaign provided
        if use_cache and username and campaign_brief:
            cached_draft = self.draft_cache.get_draft(username, campaign_brief, template_key)
            if cached_draft:
                return {
                    'subject': cached_draft['subject'],
                    'body': cached_draft['body'],
                    'to_email': cached_draft.get('email', profile.get('email', '')),
                    'cached': True,
                    'personalization': cached_draft.get('personalization', '')
                }
        
        # Generate new draft if not cached
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
        
        # Save to cache if username and campaign provided
        if username and campaign_brief:
            self.draft_cache.save_draft(
                username=username,
                campaign=campaign_brief,
                template=template_key,
                subject=template['subject'],
                body=email_body,
                email=profile.get('email', ''),
                personalization=personalization['specific_post_mention']
            )
        
        return {
            'subject': template['subject'],
            'body': email_body,
            'to_email': profile.get('email', ''),
            'cached': False,
            'personalization': personalization['specific_post_mention']
        }
    
    def _extract_personalization(self, ai_analysis, posts):
        """Use LLM to extract Wonder-relevant personalization from existing AI analysis"""
        personalization = {
            'specific_post_mention': "Your authentic approach to sharing your journey really resonates with our brand."
        }
        
        # Use Claude to intelligently extract the most relevant content
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
            
            # Mark as sent
            if username and campaign:
                self.mark_as_sent(username, campaign)
            
            return True, "Email sent successfully!"
            
        except Exception as e:
            return False, f"Error sending email: {str(e)}"


def render_email_outreach_section(app, current_campaign=None):
    """Render the redesigned email outreach section in Streamlit"""
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
        return
    
    # Initialize email manager
    email_manager = EmailOutreachManager()
    
    # Campaign settings
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        brand_name = st.text_input("Brand Name", value="Wonder", help="The brand name for this campaign")
        your_name = st.text_input("Your Name", value="Olivia")
    
    with col2:
        template_choice = st.selectbox(
            "Email Template",
            options=list(email_manager.email_templates.keys()),
            format_func=lambda x: x.replace('_', ' ').title()
        )
    
    with col3:
        # Media Kit Upload
        media_kit = st.file_uploader(
            "Media Kit (PDF)", 
            type=['pdf', 'ppt', 'pptx', 'doc', 'docx'],
            help="Attach brand info and collaboration details"
        )
        
        attachment_path = None
        if media_kit:
            # Save uploaded file temporarily
            temp_dir = "temp_attachments"
            os.makedirs(temp_dir, exist_ok=True)
            attachment_path = os.path.join(temp_dir, media_kit.name)
            with open(attachment_path, "wb") as f:
                f.write(media_kit.getbuffer())
    
    # Get creators with emails
    creators_with_emails = []
    creators_without_emails = []
    
    for username in approved_creators:
        creator_data = app.content_db.get_creator_content(username)
        if creator_data and creator_data['profile'].get('email'):
            creators_with_emails.append((username, creator_data))
        else:
            creators_without_emails.append(username)
    
    # Status summary
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.metric("📧 With Emails", len(creators_with_emails))
    with col_stat2:
        st.metric("❌ Without Emails", len(creators_without_emails))
    with col_stat3:
        sent_count = sum(1 for u, _ in creators_with_emails 
                        if email_manager.is_sent(u, current_campaign or "default"))
        st.metric("✅ Sent", sent_count)
    
    if creators_without_emails:
        with st.expander(f"⚠️ {len(creators_without_emails)} creators without emails"):
            st.write(", ".join([f"@{u}" for u in creators_without_emails]))
            if st.button("🔍 Try to Extract Emails"):
                extracted_count = 0
                for username in creators_without_emails:
                    extracted_email = app.extract_and_cache_email(username)
                    if extracted_email:
                        st.success(f"✅ Extracted: @{username} → {extracted_email}")
                        extracted_count += 1
                if extracted_count > 0:
                    st.rerun()
    
    # Main action: Generate all drafts
    st.subheader("📝 Email Drafts")
    
    # Show cache info
    cache_stats = email_manager.draft_cache.get_stats()
    if cache_stats['total_drafts'] > 0:
        campaign_drafts = cache_stats['campaigns'].get(current_campaign or "default", 0)
        if campaign_drafts > 0:
            st.info(f"💾 Using {campaign_drafts} cached drafts for this campaign (saves LLM calls)")
    
    # Check if drafts already exist in session state
    if f"email_drafts_{current_campaign}" not in st.session_state:
        if st.button("🚀 Generate All Email Drafts", type="primary", disabled=not creators_with_emails):
            with st.spinner("Generating personalized emails..."):
                all_drafts = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                cache_hits = 0
                new_drafts = 0
                
                for idx, (username, creator_data) in enumerate(creators_with_emails):
                    creator_data['username'] = username
                    
                    # Check if we have a cached draft first
                    cached = email_manager.draft_cache.has_draft(username, current_campaign or "default", template_choice)
                    
                    if cached:
                        status_text.text(f"Using cached draft for @{username}...")
                        cache_hits += 1
                    else:
                        status_text.text(f"Generating new draft for @{username}...")
                        new_drafts += 1
                    
                    # Get AI analysis from cache
                    ai_analysis = ""
                    if current_campaign and current_campaign != "➕ Create New Campaign":
                        cached_analysis = app.ai_cache.get_cached_analysis(username, current_campaign)
                        if cached_analysis:
                            ai_analysis = cached_analysis.get('analysis', '')
                    
                    # Fallback to legacy reviews
                    if not ai_analysis and hasattr(app, 'reviews') and username in app.reviews:
                        ai_analysis = app.reviews[username].get('analysis', '')
                    
                    # Generate email (will use cache if available)
                    draft = email_manager.generate_personalized_email(
                        creator_data,
                        ai_analysis,
                        template_choice,
                        current_campaign or "default",
                        username=username,
                        use_cache=True
                    )
                    
                    # Apply replacements
                    draft['subject'] = draft['subject'].replace('[BRAND_NAME]', brand_name)
                    draft['body'] = draft['body'].replace('[BRAND_NAME]', brand_name).replace('[YOUR_NAME]', your_name)
                    draft['username'] = username
                    draft['email'] = creator_data['profile'].get('email', '')
                    draft['nickname'] = creator_data['profile'].get('nickname', username)
                    draft['followers'] = creator_data['profile'].get('followers', 0)
                    
                    all_drafts.append(draft)
                    progress_bar.progress((idx + 1) / len(creators_with_emails))
                
                status_text.text("")
                st.session_state[f"email_drafts_{current_campaign}"] = all_drafts
                
                # Show cache statistics
                if cache_hits > 0:
                    st.success(f"✅ Generated {len(all_drafts)} email drafts! ({cache_hits} from cache, {new_drafts} new)")
                else:
                    st.success(f"✅ Generated {len(all_drafts)} email drafts!")
                
                st.rerun()
    
    # Display drafts if they exist
    if f"email_drafts_{current_campaign}" in st.session_state:
        drafts = st.session_state[f"email_drafts_{current_campaign}"]
        
        # Filter and sort options
        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
        with col_filter1:
            show_sent = st.selectbox("Show", ["All", "Unsent Only", "Sent Only"])
        with col_filter2:
            sort_by = st.selectbox("Sort by", ["Username", "Followers", "Sent Status"])
        with col_filter3:
            # Bulk send button
            unsent_drafts = [d for d in drafts 
                           if not email_manager.is_sent(d['username'], current_campaign or "default")]
            if st.button(f"📤 Send All ({len(unsent_drafts)})", 
                        disabled=len(unsent_drafts) == 0,
                        type="primary"):
                st.session_state['bulk_send_confirm'] = True
        with col_filter4:
            if st.button("🔄 Regenerate All"):
                # Clear cache for this campaign
                cleared = email_manager.draft_cache.clear_campaign_drafts(current_campaign or "default")
                del st.session_state[f"email_drafts_{current_campaign}"]
                st.info(f"Cleared {cleared} cached drafts")
                time.sleep(1)
                st.rerun()
        
        # Bulk send confirmation
        if st.session_state.get('bulk_send_confirm', False):
            st.warning(f"⚠️ You are about to send {len(unsent_drafts)} emails. This cannot be undone.")
            col_confirm1, col_confirm2 = st.columns(2)
            with col_confirm1:
                if st.button("✅ Confirm Send All", type="primary"):
                    # Send all unsent emails
                    success_count = 0
                    failed = []
                    progress = st.progress(0)
                    status = st.empty()
                    
                    for idx, draft in enumerate(unsent_drafts):
                        status.text(f"Sending to @{draft['username']}...")
                        success, msg = email_manager.send_email(
                            draft['email'],
                            draft['subject'],
                            draft['body'],
                            attachment_path=attachment_path,
                            username=draft['username'],
                            campaign=current_campaign or "default"
                        )
                        if success:
                            success_count += 1
                        else:
                            failed.append(f"@{draft['username']}: {msg}")
                        
                        progress.progress((idx + 1) / len(unsent_drafts))
                        time.sleep(2)  # Rate limiting
                    
                    status.text("")
                    st.success(f"✅ Sent {success_count} emails successfully!")
                    if failed:
                        st.error(f"Failed to send {len(failed)} emails:")
                        for f in failed:
                            st.write(f"• {f}")
                    
                    del st.session_state['bulk_send_confirm']
                    st.rerun()
            
            with col_confirm2:
                if st.button("❌ Cancel"):
                    del st.session_state['bulk_send_confirm']
                    st.rerun()
        
        # Filter drafts
        filtered_drafts = drafts.copy()
        if show_sent == "Unsent Only":
            filtered_drafts = [d for d in filtered_drafts 
                             if not email_manager.is_sent(d['username'], current_campaign or "default")]
        elif show_sent == "Sent Only":
            filtered_drafts = [d for d in filtered_drafts 
                             if email_manager.is_sent(d['username'], current_campaign or "default")]
        
        # Sort drafts
        if sort_by == "Followers":
            filtered_drafts.sort(key=lambda x: x.get('followers', 0), reverse=True)
        elif sort_by == "Sent Status":
            filtered_drafts.sort(key=lambda x: email_manager.is_sent(x['username'], current_campaign or "default"))
        else:
            filtered_drafts.sort(key=lambda x: x['username'])
        
        st.write(f"**Showing {len(filtered_drafts)} email drafts**")
        
        # Display each draft as an expandable card
        for draft in filtered_drafts:
            is_sent = email_manager.is_sent(draft['username'], current_campaign or "default")
            status_icon = "✅" if is_sent else "📧"
            status_text = "SENT" if is_sent else "DRAFT"
            
            with st.expander(f"{status_icon} @{draft['username']} - {draft['nickname']} ({draft.get('followers', 0):,} followers) - {status_text}"):
                # Email preview
                col_preview, col_actions = st.columns([3, 1])
                
                with col_preview:
                    st.write(f"**To:** {draft['email']}")
                    st.write(f"**Subject:** {draft['subject']}")
                    
                    # Editable body
                    edited_body = st.text_area(
                        "**Body:**",
                        value=draft['body'],
                        height=200,
                        key=f"body_{draft['username']}",
                        disabled=is_sent
                    )
                
                with col_actions:
                    if is_sent:
                        sent_info = email_manager.sent_status.get(f"{current_campaign or 'default'}_{draft['username']}", {})
                        st.success("✅ Sent")
                        if sent_info.get('sent_at'):
                            st.caption(f"Sent: {sent_info['sent_at'][:10]}")
                    else:
                        st.write("**Actions:**")
                        
                        # Send button
                        if st.button(f"📤 Send", key=f"send_{draft['username']}", type="primary"):
                            with st.spinner("Sending..."):
                                success, msg = email_manager.send_email(
                                    draft['email'],
                                    draft['subject'],
                                    edited_body,  # Use edited version
                                    attachment_path=attachment_path,
                                    username=draft['username'],
                                    campaign=current_campaign or "default"
                                )
                                if success:
                                    st.success("✅ Sent!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg}")
                        
                        # Test send
                        test_email = st.text_input("Test email:", key=f"test_{draft['username']}")
                        if st.button(f"🧪 Test", key=f"test_btn_{draft['username']}"):
                            if test_email and '@' in test_email:
                                success, msg = email_manager.send_email(
                                    test_email,
                                    f"[TEST] {draft['subject']}",
                                    f"TEST EMAIL\n\n{edited_body}",
                                    attachment_path=attachment_path
                                )
                                if success:
                                    st.success(f"Test sent to {test_email}")
                                else:
                                    st.error(f"❌ {msg}")
        
        # Export options
        st.subheader("📥 Export")
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            # Export as JSON
            export_data = json.dumps(drafts, indent=2)
            st.download_button(
                label="📄 Download All Drafts (JSON)",
                data=export_data,
                file_name=f"{current_campaign}_email_drafts_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        
        with col_export2:
            # Export as CSV
            import pandas as pd
            df = pd.DataFrame([{
                'username': d['username'],
                'email': d['email'],
                'nickname': d['nickname'],
                'followers': d.get('followers', 0),
                'subject': d['subject'],
                'body': d['body'],
                'sent': email_manager.is_sent(d['username'], current_campaign or "default")
            } for d in drafts])
            
            csv = df.to_csv(index=False)
            st.download_button(
                label="📊 Download All Drafts (CSV)",
                data=csv,
                file_name=f"{current_campaign}_email_drafts_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        # Add scheduling section
        st.divider()
        render_scheduling_section(email_manager, drafts, current_campaign, attachment_path, app, template_choice, brand_name, your_name)
        
        # Note: With Supabase deployment, scheduling is handled by Replit
        # No need to start background scheduler in Streamlit