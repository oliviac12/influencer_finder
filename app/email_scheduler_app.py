"""
Standalone Email Scheduler App
Schedule emails via Zoho with rate limit management
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import csv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import sys
from io import StringIO

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.zoho_native_scheduler import ZohoNativeScheduler
from utils.email_tracking_integration import EmailTrackingManager
from utils.email_database import EmailDatabase

# Page config
st.set_page_config(
    page_title="Email Scheduler - Zoho",
    page_icon="📧",
    layout="wide"
)

st.title("📧 Zoho Email Scheduler")
st.markdown("Schedule bulk emails with automatic rate limit management (50 emails/hour)")

# Initialize session state
if 'scheduled_count' not in st.session_state:
    st.session_state.scheduled_count = 0
if 'scheduling_results' not in st.session_state:
    st.session_state.scheduling_results = []

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Timezone selection
    timezone_options = {
        "US/Pacific": "Pacific Time (PST/PDT)",
        "US/Eastern": "Eastern Time (EST/EDT)",
        "US/Central": "Central Time (CST/CDT)",
        "US/Mountain": "Mountain Time (MST/MDT)",
        "UTC": "UTC",
        "Asia/Shanghai": "China Standard Time"
    }
    
    selected_tz = st.selectbox(
        "Timezone",
        options=list(timezone_options.keys()),
        format_func=lambda x: timezone_options[x],
        index=0
    )
    
    st.markdown("---")
    
    # Rate limit settings
    st.subheader("📊 Rate Limits")
    emails_per_batch = st.number_input(
        "Emails per batch",
        min_value=1,
        max_value=30,
        value=30,
        help="Max 30 to stay under Zoho's 50/hour limit"
    )
    
    batch_gap_minutes = st.number_input(
        "Gap between batches (minutes)",
        min_value=30,
        max_value=120,
        value=40,
        help="Wait time between batches to reset rate limit"
    )
    
    interval_minutes = st.number_input(
        "Interval between emails (minutes)",
        min_value=1,
        max_value=10,
        value=3,
        help="Time between individual emails in a batch"
    )
    
    st.markdown("---")
    st.info(f"""
    **Current Settings:**
    - {emails_per_batch} emails per batch
    - {interval_minutes} min between emails
    - {batch_gap_minutes} min between batches
    - Max rate: ~{int(60/interval_minutes)} emails/hour
    """)

# Main content area
col1, col2 = st.columns([3, 2])

with col1:
    st.header("📝 Email Data")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload CSV with recipients",
        type=['csv'],
        help="CSV must have 'username' and 'email' columns",
        key="csv_upload"
    )
    
    # Or manual input
    st.markdown("**OR** enter recipients manually:")
    manual_input = st.text_area(
        "Enter recipients (username,email format)",
        placeholder="lisa.mariee1,serranolisa98@gmail.com\nlauren.clutter,hello@laurenclutter.com",
        height=100
    )
    
    # Email template
    st.markdown("---")
    st.subheader("📄 Email Template")
    
    # Campaign name for tracking (will be updated with template version)
    base_campaign_name = st.text_input(
        "Campaign Name",
        value=f"wonder_{datetime.now().strftime('%Y%m%d')}",
        help="Will be appended with template version for A/B testing"
    )
    
    st.info("✨ All email templates will be automatically wrapped in professional HTML format with Wonder branding, header image, and styled layout.")
    
    email_subject = st.text_input(
        "Subject Line",
        value="Wonder Partnership Opportunity - TikTok Shop Campaign",
        help="Use {username} to personalize"
    )
    
    # Email template versions
    template_v1 = """<p>Hi {username},</p>

<p>I'm Olivia from Unsettled.xyz, a brand partnership agency. I've been following your TikTok content and believe your authentic storytelling style would be perfect for our client Wonder's upcoming campaign.</p>

<p><a href="https://www.instagram.com/wondertravelgear/" style="color: #007bff; text-decoration: none;">Wonder</a> is a premium luggage brand (by Travelhouse - established on <a href="https://www.amazon.com/stores/Travelhouse/page/FF7AED26-A513-49EF-99F1-4F60D6622FD4" style="color: #007bff; text-decoration: none;">Amazon</a>/<a href="https://www.walmart.com/c/brand/travelhouse" style="color: #007bff; text-decoration: none;">Walmart</a>) launching their first direct-to-consumer line this fall. They're specifically seeking creators who embody independent thinking and authentic lifestyle content.</p>

<p>We're offering:<br>
• Complimentary Wonder carry-on for review<br>
• Competitive affiliate commission structure<br>
• Performance-based bonuses for holiday season<br>
• Full creative freedom within brand guidelines</p>

<p>I've attached our partnership deck with campaign details and compensation structure. Would you be open to a brief discussion about this opportunity?</p>

<p>Best regards,<br>
Olivia Chen<br>
Partnership Director<br>
Unsettled.xyz</p>"""

    template_v2 = """<p>Dear {username},</p>

<p>I'm reaching out because your recent travel and lifestyle content on TikTok caught my attention - particularly your authentic approach to storytelling and the genuine connection you have with your audience. This aligns perfectly with a campaign I'm managing.</p>

<p>I represent <a href="https://www.instagram.com/wondertravelgear/" style="color: #007bff; text-decoration: none;">Wonder</a>, a new premium luggage line from Travelhouse (an established manufacturer with strong <a href="https://www.amazon.com/stores/Travelhouse/page/FF7AED26-A513-49EF-99F1-4F60D6622FD4" style="color: #007bff; text-decoration: none;">Amazon</a>/<a href="https://www.walmart.com/c/brand/travelhouse" style="color: #007bff; text-decoration: none;">Walmart</a> presence). Wonder is positioning itself differently - focusing on creators and travelers who value both design and functionality.</p>

<p>For this TikTok Shop campaign launching in Q4 2024, we're selecting a limited number of creators for paid partnerships. The collaboration includes product gifting, competitive commissions, and performance incentives during the holiday shopping season.</p>

<p>I've attached a detailed partnership proposal. Given your audience demographic and engagement rates, I believe this could be mutually beneficial. Are you currently accepting brand partnerships for Q4?</p>

<p>Sincerely,<br>
Olivia Chen<br>
Unsettled.xyz | Brand Partnerships</p>"""

    template_v3 = """<p>Hi {username},</p>

<p>Your TikTok content consistently demonstrates the authentic storytelling that resonates with modern audiences - exactly what our client Wonder is seeking for their upcoming launch.</p>

<p>Quick context: <a href="https://www.instagram.com/wondertravelgear/" style="color: #007bff; text-decoration: none;">Wonder</a> is a premium luggage brand entering the direct-to-consumer market this fall. Their parent company, Travelhouse, has proven success on <a href="https://www.amazon.com/stores/Travelhouse/page/FF7AED26-A513-49EF-99F1-4F60D6622FD4" style="color: #007bff; text-decoration: none;">major</a> <a href="https://www.walmart.com/c/brand/travelhouse" style="color: #007bff; text-decoration: none;">retail</a> platforms, and they're now investing significantly in creator partnerships for this new venture.</p>

<p>Why I'm reaching out to you specifically:<br>
- Your audience aligns with Wonder's target demographic<br>
- Your content style matches their brand values<br>
- Your engagement rates exceed our campaign requirements</p>

<p>The partnership includes product sampling, tiered commission structure, and additional performance bonuses for the Q4 holiday period. Full campaign details and compensation terms are in the attached document.</p>

<p>If brand partnerships are something you're exploring, I'd appreciate the opportunity to discuss how this could fit into your content calendar.</p>

<p>Best,<br>
Olivia Chen<br>
Director of Influencer Relations<br>
Unsettled.xyz</p>"""
    
    # Professional HTML template wrapper for all email versions
    def wrap_in_professional_html(body_content):
        """Wrap any email content in the professional HTML template"""
        return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
    <meta name="format-detection" content="telephone=no"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Brand Collaboration Opportunity</title>
    <style type="text/css" emogrify="no">#outlook a {{ padding:0; }} .ExternalClass {{ width:100%; }} .ExternalClass, .ExternalClass p, .ExternalClass span, .ExternalClass font, .ExternalClass td, .ExternalClass div {{ line-height: 100%; }} table td {{ border-collapse: collapse; mso-line-height-rule: exactly; }} .editable.image {{ font-size: 0 !important; line-height: 0 !important; }} .nl2go_preheader {{ display: none !important; mso-hide:all !important; mso-line-height-rule: exactly; visibility: hidden !important; line-height: 0px !important; font-size: 0px !important; }} body {{ width:100% !important; -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; margin:0; padding:0; color: #333333; }} img {{ outline:none; text-decoration:none; -ms-interpolation-mode: bicubic; }} a img {{ border:none; }} table {{ border-collapse:collapse; mso-table-lspace:0pt; mso-table-rspace:0pt; }} th {{ font-weight: normal; text-align: left; }} *[class="gmail-fix"] {{ display: none !important; }} </style>
    <style type="text/css" emogrify="no"> @media (max-width: 600px) {{ .gmx-killpill {{ content: ' \\03D1';}} }} </style>
    <style type="text/css" emogrify="no">@media (max-width: 600px) {{ .gmx-killpill {{ content: ' \\03D1';}} .r0-o {{ border-style: solid !important; margin: 0 auto 0 auto !important; width: 100% !important }} .r1-c {{ box-sizing: border-box !important; text-align: center !important; valign: top !important; width: 320px !important }} .r2-o {{ border-style: solid !important; margin: 0 auto 0 auto !important; width: 320px !important }} .r3-i {{ padding-bottom: 0px !important; padding-left: 15px !important; padding-right: 15px !important; padding-top: 0px !important }} .r4-c {{ box-sizing: border-box !important; display: block !important; valign: top !important; width: 100% !important }} .r5-o {{ border-style: solid !important; width: 100% !important }} .r10-i {{ background-color: #ffffff !important }} .r11-c {{ box-sizing: border-box !important; text-align: center !important; valign: middle !important; width: 100% !important }} .r12-c {{ box-sizing: border-box !important; display: block !important; valign: middle !important; width: 100% !important }} .r13-o {{ border-bottom-width: 0px !important; border-left-width: 0px !important; border-right-width: 0px !important; border-style: solid !important; border-top-width: 0px !important; margin: 0 auto 0 0 !important; margin-top: 0px !important; width: 100% !important }} .r14-i {{ padding-bottom: 0px !important; padding-right: 0px !important; padding-top: 0px !important }} .r15-c {{ box-sizing: border-box !important; text-align: center !important; valign: top !important; width: 100% !important }} .r16-i {{ padding-bottom: 20px !important; padding-left: 15px !important; padding-right: 15px !important; padding-top: 20px !important }} .r17-i {{ padding-left: 0px !important; padding-right: 0px !important }} .r18-c {{ box-sizing: border-box !important; padding-bottom: 15px !important; padding-top: 0px !important; text-align: left !important; valign: top !important; width: 100% !important }} .r19-i {{ background-color: #181717 !important; padding-bottom: 20px !important; padding-left: 15px !important; padding-right: 15px !important; padding-top: 20px !important }} .r20-o {{ border-style: solid !important; margin: 0 auto 0 auto !important; margin-bottom: 15px !important; margin-top: 15px !important; width: 100% !important }} .r21-i {{ text-align: center !important }} .r22-r {{ background-color: #0a0b0b !important; border-color: #f1ebeb !important; border-radius: 24px !important; border-width: 2px !important; box-sizing: border-box; height: initial !important; padding-bottom: 12px !important; padding-top: 12px !important; text-align: center !important; width: 100% !important }} body {{ -webkit-text-size-adjust: none }} .nl2go-responsive-hide {{ display: none }} .nl2go-body-table {{ min-width: unset !important }} .mobshow {{ height: auto !important; overflow: visible !important; max-height: unset !important; visibility: visible !important; border: none !important }} .resp-table {{ display: inline-table !important }} .magic-resp {{ display: table-cell !important }} }} </style>
    <!--[if !mso]><!-->
    <style type="text/css" emogrify="no">@import url("https://fonts.googleapis.com/css2?family=Inter"); </style>
    <!--<![endif]-->
    <style type="text/css">p, h1, h2, h3, h4, ol, ul, li {{ margin: 0; }} a, a:link {{ color: #0092ff; text-decoration: underline }} .nl2go-default-textstyle {{ color: #333333; font-family: Inter, arial; font-size: 16px; line-height: 1.5; word-break: break-word }} .default-button {{ color: #ffffff; font-family: Inter, arial; font-size: 16px; font-style: normal; font-weight: normal; line-height: 1.15; text-decoration: none; word-break: break-word }} .default-heading3 {{ color: #333333; font-family: Inter, arial; font-size: 24px; word-break: break-word }} .default-heading4 {{ color: #333333; font-family: Inter, arial; font-size: 18px; word-break: break-word }} .default-heading1 {{ color: #333333; font-family: Inter, arial; font-size: 36px; word-break: break-word }} .default-heading2 {{ color: #333333; font-family: Inter, arial; font-size: 32px; word-break: break-word }} a[x-apple-data-detectors] {{ color: inherit !important; text-decoration: inherit !important; font-size: inherit !important; font-family: inherit !important; font-weight: inherit !important; line-height: inherit !important; }} .no-show-for-you {{ border: none; display: none; float: none; font-size: 0; height: 0; line-height: 0; max-height: 0; mso-hide: all; overflow: hidden; table-layout: fixed; visibility: hidden; width: 0; }} </style>
    <!--[if mso]>
    <xml>
      <o:OfficeDocumentSettings>
        <o:AllowPNG/>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
    <![endif]-->
    <style type="text/css">a:link{{color: #0092ff; text-decoration: underline;}}</style>
</head>
<body bgcolor="#ffffff" text="#3b3f44" link="#0092ff" yahoo="fix" style="background-color: #ffffff; padding-bottom: 0px; padding-top: 0px;">
    <table cellspacing="0" cellpadding="0" border="0" role="presentation" class="nl2go-body-table" width="100%" style="background-color: #ffffff; width: 100%;">
      <tbody><tr>
        <td>
          <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="600" align="center" class="r2-o" style="table-layout: fixed; width: 600px;">
            <tbody><tr>
              <td valign="top" class="r10-i" style="background-color: #ffffff;">
                <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" align="center" class="r0-o" style="table-layout: fixed; width: 100%;">
                  <tbody><tr>
                    <td class="r3-i">
                      <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation">
                        <tbody><tr>
                          <th width="100%" valign="middle" class="r12-c" style="font-weight: normal;">
                            <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="600" align="left" class="r13-o" style="border-bottom-width: 0px; border-collapse: separate; border-left-width: 0px; border-radius: 0px; border-right-width: 0px; border-top-width: 0px; margin-top: 0px; table-layout: fixed; width: 600px;">
                              <tbody><tr>
                                <td class="r14-i" style="border-radius: 0px; font-size: 0px; line-height: 0px;">
                                  <img src="https://i.imgur.com/jORPlBG.jpeg" width="600" border="0" style="display: block; width: 100%; border-radius: 0px;" alt="Wonder Luggage Collection"/>
                                </td>
                              </tr>
                            </tbody></table>
                          </th>
                        </tr>
                      </tbody></table>
                    </td>
                  </tr>
                </tbody></table>
                <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" align="center" class="r0-o" style="table-layout: fixed; width: 100%;">
                  <tbody><tr>
                    <td class="r16-i" style="padding-bottom: 20px; padding-top: 20px;">
                      <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation">
                        <tbody><tr>
                          <th width="100%" valign="top" class="r4-c" style="font-weight: normal;">
                            <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" class="r5-o" style="table-layout: fixed; width: 100%;">
                              <tbody><tr>
                                <td valign="top" class="r17-i" style="padding-left: 15px; padding-right: 15px;">
                                  <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation">
                                    <tbody><tr>
                                      <td class="r18-c nl2go-default-textstyle" align="left" style="color: #3b3f44; font-family: Inter,arial; font-size: 16px; line-height: 1.5; word-break: break-word; padding-bottom: 15px; padding-top: 15px; text-align: left; valign: top; word-wrap: break-word;">
                                        <div>
                                          {body_content}
                                        </div>
                                      </td>
                                    </tr>
                                  </tbody></table>
                                </td>
                              </tr>
                            </tbody></table>
                          </th>
                        </tr>
                      </tbody></table>
                    </td>
                  </tr>
                </tbody></table>
                <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" align="center" class="r0-o" style="table-layout: fixed; width: 100%;">
                  <tbody><tr>
                    <td class="r19-i" style="background-color: #181717; padding-bottom: 20px; padding-top: 20px;">
                      <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation">
                        <tbody><tr>
                          <th width="100%" valign="top" class="r4-c" style="font-weight: normal;">
                            <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="100%" class="r5-o" style="table-layout: fixed; width: 100%;">
                              <tbody><tr>
                                <td valign="top" class="r17-i" style="padding-left: 15px; padding-right: 15px;">
                                  <table width="100%" cellspacing="0" cellpadding="0" border="0" role="presentation">
                                    <tbody><tr>
                                      <td class="r15-c" align="center">
                                        <table cellspacing="0" cellpadding="0" border="0" role="presentation" width="171" class="r20-o" style="table-layout: fixed; width: 171px;">
                                          <tbody><tr class="nl2go-responsive-hide">
                                            <td height="15" style="font-size: 15px; line-height: 15px;">­</td>
                                          </tr>
                                          <tr>
                                            <td height="18" align="center" valign="top" class="r21-i nl2go-default-textstyle" style="color: #3b3f44; font-family: Inter,arial; font-size: 16px; line-height: 1.5; word-break: break-word;">
                                              <a href="#" class="r22-r default-button" target="_blank" title="Brand Kit" data-btn="1" style="font-style: normal; font-weight: normal; line-height: 1.15; text-decoration: none; word-break: break-word; border-style: solid; word-wrap: break-word; display: block; -webkit-text-size-adjust: none; background-color: #0a0b0b; border-color: #f1ebeb; border-radius: 24px; border-width: 2px; color: #ffffff; font-family: Inter, arial; font-size: 16px; height: 18px; mso-hide: all; padding-bottom: 12px; padding-top: 12px; width: 167px;"> <span>View PDF</span></a>
                                            </td>
                                          </tr>
                                          <tr class="nl2go-responsive-hide">
                                            <td height="15" style="font-size: 15px; line-height: 15px;">­</td>
                                          </tr>
                                        </tbody></table>
                                      </td>
                                    </tr>
                                  </tbody></table>
                                </td>
                              </tr>
                            </tbody></table>
                          </th>
                        </tr>
                      </tbody></table>
                    </td>
                  </tr>
                </tbody></table>
              </td>
            </tr>
          </tbody></table>
        </td>
      </tr>
    </tbody></table>
</body>
</html>"""

    # Template selector
    template_option = st.selectbox(
        "Choose Email Template Version",
        ["Version 1: Concise & Direct", "Version 2: Personalized & Specific", "Version 3: Value-First Approach", "Custom HTML Template"],
        help="All templates will be wrapped in professional HTML format with Wonder branding"
    )
    
    # Set template based on selection
    if template_option == "Version 1: Concise & Direct":
        selected_template = template_v1
        template_version = "v1_concise"
    elif template_option == "Version 2: Personalized & Specific":
        selected_template = template_v2
        template_version = "v2_personalized"
    elif template_option == "Version 3: Value-First Approach":
        selected_template = template_v3
        template_version = "v3_value_first"
    else:
        selected_template = ""
        template_version = "custom_html"
    
    # HTML Template input with preview
    if template_option == "Custom HTML Template":
        st.info("📝 Paste your complete HTML template below. You can include images, styles, and use {username} for personalization.")
        
        # Tips for HTML emails
        with st.expander("💡 HTML Email Tips"):
            st.markdown("""
            **Best Practices:**
            - Use inline CSS styles (not external stylesheets)
            - Host images on public URLs (e.g., imgur, cloudinary)
            - Keep width under 600px for mobile compatibility
            - Use table-based layouts for better email client support
            - Test with different email clients
            
            **Supported:**
            - `<img src="https://...">` - Images from public URLs
            - Inline styles: `<p style="color: blue;">`
            - Basic HTML tags: `<h1>`, `<p>`, `<a>`, `<table>`, etc.
            - `{username}` placeholder for personalization
            
            **Example:**
            ```html
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <img src="https://your-image-url.com/header.png" style="width: 100%;">
                    <h1 style="color: #333;">Hi {username}!</h1>
                    <p>Your content here...</p>
                </div>
            </body>
            </html>
            ```
            """)
        
        email_template = st.text_area(
            "HTML Email Template",
            value=selected_template,
            height=400,
            help="Paste your complete HTML including <html>, <body>, images, etc. Use {username} for personalization"
        )
        
        # HTML Preview
        if email_template:
            with st.expander("🔍 Preview HTML Email", expanded=True):
                # Show preview with a sample username
                preview_html = email_template.replace('{username}', '@samplecreator')
                components.html(preview_html, height=600, scrolling=True)
                
            # Also show raw HTML for debugging
            with st.expander("📄 View Raw HTML"):
                st.code(email_template[:1000] + "..." if len(email_template) > 1000 else email_template, language='html')
    else:
        email_template = st.text_area(
            "Email Body (HTML supported)",
            value=selected_template,
            height=400,
            help="Use {username} to insert the creator's username"
        )
        
        # Show preview of how it will look in professional format
        if template_option != "Custom HTML Template":
            with st.expander("🔍 Preview Email in Professional Format", expanded=False):
                preview_content = email_template.replace('{username}', '@samplecreator')
                preview_html = wrap_in_professional_html(preview_content)
                components.html(preview_html, height=800, scrolling=True)
    
    # Attachment upload
    st.markdown("---")
    st.subheader("📎 Attachment")
    attachment_file = st.file_uploader(
        "Upload attachment (optional)",
        type=['pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg'],
        help="File will be attached to all emails"
    )
    
    # Save uploaded file temporarily if provided
    attachment_path = None
    if attachment_file:
        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(os.path.dirname(__file__), 'temp_attachments')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the uploaded file
        attachment_path = os.path.join(temp_dir, attachment_file.name)
        with open(attachment_path, 'wb') as f:
            f.write(attachment_file.getbuffer())
        
        st.success(f"✅ Attachment loaded: {attachment_file.name} ({attachment_file.size / 1024:.1f} KB)")

with col2:
    st.header("⏰ Schedule Settings")
    
    # Schedule type
    schedule_type = st.radio(
        "When to send",
        ["Schedule for specific time", "Send immediately (with rate limits)"]
    )
    
    if schedule_type == "Schedule for specific time":
        # Date and time selection
        col_date, col_time = st.columns(2)
        
        with col_date:
            schedule_date = st.date_input(
                "Date",
                min_value=datetime.now().date(),
                value=datetime.now().date() + timedelta(days=1)
            )
        
        with col_time:
            schedule_time = st.time_input(
                "Time",
                value=datetime.strptime("09:00", "%H:%M").time()
            )
        
        # Combine date and time
        tz = ZoneInfo(selected_tz)
        scheduled_datetime = datetime.combine(schedule_date, schedule_time).replace(tzinfo=tz)
        
        st.info(f"📅 First email: {scheduled_datetime.strftime('%Y-%m-%d %I:%M %p %Z')}")
    else:
        # Send immediately (well, in 2 minutes)
        tz = ZoneInfo(selected_tz)
        scheduled_datetime = datetime.now(tz) + timedelta(minutes=2)
        st.info(f"📅 First email: {scheduled_datetime.strftime('%Y-%m-%d %I:%M %p %Z')}")
    
    # Preview
    st.markdown("---")
    st.subheader("👁️ Preview")
    
    # Parse recipients
    recipients = []
    if uploaded_file is not None:
        try:
            # Reset file pointer to beginning
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
            
            # Check if CSV has data
            if len(df) > 0:
                # Check for required columns (case-insensitive)
                columns_lower = {col.lower(): col for col in df.columns}
                
                if 'username' in columns_lower and 'email' in columns_lower:
                    username_col = columns_lower['username']
                    email_col = columns_lower['email']
                    recipients = df[[username_col, email_col]].rename(columns={
                        username_col: 'username',
                        email_col: 'email'
                    }).to_dict('records')
                    
                    # Filter out empty rows and validate emails
                    valid_recipients = []
                    invalid_count = 0
                    for r in recipients:
                        if r.get('username') and r.get('email'):
                            # Basic email validation
                            email = str(r.get('email', '')).strip()
                            if '@' in email and '.' in email:
                                r['email'] = email  # Use cleaned email
                                valid_recipients.append(r)
                            else:
                                invalid_count += 1
                    recipients = valid_recipients
                    
                    if invalid_count > 0:
                        st.warning(f"⚠️ Skipped {invalid_count} rows with invalid email addresses")
                else:
                    st.error(f"❌ CSV must have 'username' and 'email' columns. Found: {', '.join(df.columns)}")
            else:
                st.warning("⚠️ CSV file is empty")
        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")
    elif manual_input:
        for line in manual_input.strip().split('\n'):
            if ',' in line:
                parts = line.split(',')
                if len(parts) >= 2:
                    recipients.append({
                        'username': parts[0].strip(),
                        'email': parts[1].strip()
                    })
    
    if recipients:
        st.success(f"✅ {len(recipients)} recipients loaded")
        
        # Calculate timing
        total_batches = (len(recipients) - 1) // emails_per_batch + 1
        if total_batches > 1:
            # Account for batch gaps
            total_duration = 0
            for batch in range(total_batches):
                batch_size = min(emails_per_batch, len(recipients) - batch * emails_per_batch)
                total_duration += (batch_size - 1) * interval_minutes
                if batch < total_batches - 1:
                    total_duration += batch_gap_minutes
        else:
            total_duration = (len(recipients) - 1) * interval_minutes
        
        end_time = scheduled_datetime + timedelta(minutes=total_duration)
        
        # Display timing info
        st.markdown(f"""
        **📊 Scheduling Summary:**
        - Recipients: {len(recipients)}
        - Batches: {total_batches}
        - Duration: {total_duration} minutes
        - Last email: {end_time.strftime('%I:%M %p')}
        """)
        
        # Show first few recipients
        with st.expander("View Recipients"):
            for i, r in enumerate(recipients[:10]):
                st.text(f"{i+1}. @{r['username']} → {r['email']}")
            if len(recipients) > 10:
                st.text(f"... and {len(recipients)-10} more")
    else:
        st.warning("⚠️ No recipients loaded")

# Schedule/Send buttons
st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    if st.button("📤 Send Now", type="secondary", use_container_width=True, disabled=not recipients):
        if recipients:
            with st.spinner(f"Sending {len(recipients)} emails immediately..."):
                try:
                    # Initialize scheduler, tracking, and database
                    scheduler = ZohoNativeScheduler()
                    tracker = EmailTrackingManager()
                    email_db = EmailDatabase()
                    
                    # Use immediate time (2 minutes from now to allow processing)
                    tz = ZoneInfo(selected_tz)
                    immediate_time = datetime.now(tz) + timedelta(minutes=2)
                    
                    # Prepare emails with tracking
                    emails_to_schedule = []
                    for recipient in recipients:
                        # Replace placeholders in template
                        body_content = email_template.replace('{username}', recipient['username'])
                        subject = email_subject.replace('{username}', recipient['username'])
                        
                        # Wrap in professional HTML format (except for Custom HTML which is already complete)
                        if template_option != "Custom HTML Template":
                            body = wrap_in_professional_html(body_content)
                        else:
                            body = body_content
                        
                        # Add tracking pixel with template version in campaign name
                        campaign_with_version = f"{base_campaign_name}_{template_version}"
                        pixel_html, tracking_id = tracker.get_tracking_pixel_html(
                            username=recipient['username'],
                            campaign=campaign_with_version,
                            recipient_email=recipient['email']
                        )
                        
                        # Add tracking pixel to the email body
                        tracked_body = f"{body}\n{pixel_html}"
                        
                        emails_to_schedule.append({
                            'username': recipient['username'],
                            'email': recipient['email'],
                            'subject': subject,
                            'body': tracked_body,
                            'attachment_path': attachment_path,
                            'tracking_id': tracking_id
                        })
                    
                    # Send immediately with minimal delays
                    progress = st.progress(0)
                    status = st.empty()
                    
                    scheduled_ids = []
                    current_time = immediate_time  # Use immediate time instead of scheduled
                    
                    for i, email_data in enumerate(emails_to_schedule):
                        # Check if we need a batch gap
                        if i > 0 and i % emails_per_batch == 0:
                            batch_num = i // emails_per_batch + 1
                            current_time += timedelta(minutes=batch_gap_minutes - interval_minutes)
                            status.text(f"⏸️ Batch {batch_num} starting...")
                        
                        # Schedule this email
                        result = scheduler.schedule_email(
                            to_email=email_data['email'],
                            subject=email_data['subject'],
                            body=email_data['body'],
                            scheduled_time=current_time,
                            attachment_path=email_data.get('attachment_path'),
                            username=email_data.get('username'),
                            campaign=campaign_with_version
                        )
                        
                        if result['success']:
                            scheduled_ids.append(result['email_id'])
                            status.text(f"✅ [{i+1}/{len(recipients)}] Sent @{email_data['username']}")
                            
                            # Log to database
                            email_db.log_email_sent(
                                email_id=result['email_id'],
                                campaign=campaign_with_version,
                                recipient_email=email_data['email'],
                                subject=email_data['subject'],
                                body_html=email_data['body'],
                                username=email_data.get('username'),
                                template_version=template_version,
                                attachment_name=attachment_file.name if attachment_file else None,
                                scheduled_at=current_time,
                                sent_at=datetime.now(),
                                tracking_id=email_data.get('tracking_id')
                            )
                        else:
                            error_msg = result.get('error', 'Unknown error')[:100]  # Truncate long errors
                            status.text(f"❌ [{i+1}/{len(recipients)}] Failed: @{email_data['username']}")
                            
                            # Log failed emails for review
                            if 'failed_emails' not in st.session_state:
                                st.session_state.failed_emails = []
                            st.session_state.failed_emails.append({
                                'username': email_data['username'],
                                'email': email_data['email'],
                                'error': error_msg
                            })
                        
                        # Update progress
                        progress.progress((i + 1) / len(recipients))
                        
                        # For immediate send, use minimal delay (30 seconds between emails)
                        current_time += timedelta(seconds=30)
                    
                    # Success message
                    if len(scheduled_ids) > 0:
                        st.balloons()
                    
                    if len(scheduled_ids) == len(recipients):
                        st.success(f"""
                        ✅ **All emails sent successfully!**
                        - Total: {len(scheduled_ids)} emails
                        - Campaign: {campaign_with_version}
                        - Template: {template_option}
                        - Tracking: Enabled (email opens will be tracked)
                        - Emails will be delivered within 2-3 minutes
                        """)
                    else:
                        st.warning(f"""
                        ⚠️ **Sending Complete with some failures**
                        - Sent: {len(scheduled_ids)} emails
                        - Failed: {len(recipients) - len(scheduled_ids)} emails
                        - Campaign: {campaign_with_version}
                        - Check your Zoho Sent folder for successful ones
                        """)
                        
                        # Show failed emails
                        if st.session_state.get('failed_emails'):
                            with st.expander("❌ View Failed Emails"):
                                for fail in st.session_state.failed_emails:
                                    st.text(f"@{fail['username']} ({fail['email']})")
                                    st.caption(f"Error: {fail['error']}")
                                st.info("Common issues: Invalid email format, authentication errors, or rate limits")
                    
                    # Store results
                    st.session_state.scheduled_count += len(scheduled_ids)
                    st.session_state.scheduling_results.append({
                        'timestamp': datetime.now(),
                        'count': len(scheduled_ids),
                        'campaign': 'manual'
                    })
                    
                    # Cleanup temporary attachment file
                    if attachment_path and os.path.exists(attachment_path):
                        try:
                            os.remove(attachment_path)
                        except:
                            pass  # Ignore cleanup errors
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

with col_btn2:
    if st.button("📅 Schedule Emails", type="primary", use_container_width=True, disabled=not recipients):
        if recipients:
            with st.spinner(f"Scheduling {len(recipients)} emails..."):
                try:
                    # Initialize scheduler, tracking, and database
                    scheduler = ZohoNativeScheduler()
                    tracker = EmailTrackingManager()
                    email_db = EmailDatabase()
                    
                    # Prepare emails with tracking
                    emails_to_schedule = []
                    for recipient in recipients:
                        # Replace placeholders in template
                        body_content = email_template.replace('{username}', recipient['username'])
                        subject = email_subject.replace('{username}', recipient['username'])
                        
                        # Wrap in professional HTML format (except for Custom HTML which is already complete)
                        if template_option != "Custom HTML Template":
                            body = wrap_in_professional_html(body_content)
                        else:
                            body = body_content
                        
                        # Add tracking pixel with template version in campaign name
                        campaign_with_version = f"{base_campaign_name}_{template_version}"
                        pixel_html, tracking_id = tracker.get_tracking_pixel_html(
                            username=recipient['username'],
                            campaign=campaign_with_version,
                            recipient_email=recipient['email']
                        )
                        
                        # Add tracking pixel to the email body
                        tracked_body = f"{body}\n{pixel_html}"
                        
                        emails_to_schedule.append({
                            'username': recipient['username'],
                            'email': recipient['email'],
                            'subject': subject,
                            'body': tracked_body,
                            'attachment_path': attachment_path,
                            'tracking_id': tracking_id
                        })
                    
                    # Schedule with rate limits
                    progress = st.progress(0)
                    status = st.empty()
                    
                    scheduled_ids = []
                    current_time = scheduled_datetime
                    
                    for i, email_data in enumerate(emails_to_schedule):
                        # Check if we need a batch gap
                        if i > 0 and i % emails_per_batch == 0:
                            batch_num = i // emails_per_batch + 1
                            current_time += timedelta(minutes=batch_gap_minutes - interval_minutes)
                            status.text(f"⏸️ Batch {batch_num} starting...")
                        
                        # Schedule this email
                        result = scheduler.schedule_email(
                            to_email=email_data['email'],
                            subject=email_data['subject'],
                            body=email_data['body'],
                            scheduled_time=current_time,
                            attachment_path=email_data.get('attachment_path'),
                            username=email_data.get('username'),
                            campaign=campaign_with_version
                        )
                        
                        if result['success']:
                            scheduled_ids.append(result['email_id'])
                            status.text(f"✅ [{i+1}/{len(recipients)}] Scheduled @{email_data['username']} for {current_time.strftime('%I:%M %p')}")
                        else:
                            error_msg = result.get('error', 'Unknown error')[:100]
                            status.text(f"❌ [{i+1}/{len(recipients)}] Failed: @{email_data['username']}")
                            
                            # Log failed emails for review
                            if 'failed_emails' not in st.session_state:
                                st.session_state.failed_emails = []
                            st.session_state.failed_emails.append({
                                'username': email_data['username'],
                                'email': email_data['email'],
                                'error': error_msg
                            })
                        
                        # Update progress
                        progress.progress((i + 1) / len(recipients))
                        
                        # Increment time for next email
                        current_time += timedelta(minutes=interval_minutes)
                    
                    # Success message
                    if len(scheduled_ids) > 0:
                        st.balloons()
                    
                    if len(scheduled_ids) == len(recipients):
                        st.success(f"""
                        ✅ **All emails scheduled successfully!**
                        - Total: {len(scheduled_ids)} emails
                        - Campaign: {campaign_with_version}
                        - Template: {template_option}
                        - First email: {scheduled_datetime.strftime('%I:%M %p %Z')}
                        - Tracking: Enabled
                        """)
                    else:
                        st.warning(f"""
                        ⚠️ **Scheduling Complete with some failures**
                        - Scheduled: {len(scheduled_ids)} emails
                        - Failed: {len(recipients) - len(scheduled_ids)} emails
                        """)
                        
                        # Show failed emails
                        if st.session_state.get('failed_emails'):
                            with st.expander("❌ View Failed Emails"):
                                for fail in st.session_state.failed_emails:
                                    st.text(f"@{fail['username']} ({fail['email']})")
                                    st.caption(f"Error: {fail['error']}")
                    
                    # Store results
                    st.session_state.scheduled_count += len(scheduled_ids)
                    st.session_state.scheduling_results.append({
                        'timestamp': datetime.now(),
                        'count': len(scheduled_ids),
                        'campaign': campaign_name
                    })
                    
                    # Cleanup temporary attachment file
                    if attachment_path and os.path.exists(attachment_path):
                        try:
                            os.remove(attachment_path)
                        except:
                            pass
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# History section
if st.session_state.scheduled_count > 0:
    st.markdown("---")
    st.subheader("📊 Session History")
    st.metric("Total Scheduled This Session", st.session_state.scheduled_count)
    
    if st.session_state.scheduling_results:
        history_df = pd.DataFrame(st.session_state.scheduling_results)
        st.dataframe(history_df, use_container_width=True)

# Tracking section
st.markdown("---")
st.subheader("📈 Email Tracking")

col_track1, col_track2 = st.columns(2)

with col_track1:
    if st.button("🔍 View Tracking Stats"):
        # Fetch from /api/dashboard endpoint which uses Supabase with sender filtering
        try:
            import requests
            response = requests.get("https://tracking.unsettled.xyz/api/dashboard", timeout=5)
            
            if response.status_code == 200:
                dashboard_data = response.json()
                
                if dashboard_data.get('success'):
                    st.success("📊 Last 24 Hours Email Stats")
                    
                    # Get stats from dashboard API
                    stats = dashboard_data.get('stats', {})
                    
                    # Display 24-hour metrics only
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("📤 Sent (24h)", stats.get('sent_24h', 0))
                    with col_b:
                        st.metric("👀 Opens (24h)", stats.get('opens_24h', 0))
                    with col_c:
                        st.metric("📈 Open Rate (24h)", f"{stats.get('open_rate_24h', 0):.1f}%")
                    
                    # Add note about filtering
                    st.info("💡 Tracking last 24 hours only • Sender opens excluded")
                    
                    # Link to full dashboard
                    st.markdown("[📊 View Full Dashboard](https://tracking.unsettled.xyz/dashboard)")
                else:
                    st.error("Failed to fetch dashboard data")
            else:
                # Fallback to old method if dashboard endpoint fails
                tracker = EmailTrackingManager()
                stats = tracker.fetch_tracking_stats()
                
                if stats and stats.get('success'):
                    st.warning("📊 Email Stats (Note: May include sender opens)")
                    overall = stats.get('overall', {})
                    st.metric("Total Opens", overall.get('total_opens', 0))
                    st.metric("Open Rate", f"{overall.get('open_rate', 0):.1f}%")
                else:
                    st.info("No tracking data available yet")
                    
        except Exception as e:
            st.error(f"Error fetching stats: {str(e)}")
            st.info("[Try viewing stats directly](https://tracking.unsettled.xyz/dashboard)")

with col_track2:
    st.info("""
    **How Tracking Works:**
    - Invisible pixel added to emails
    - Tracks when email is opened
    - Records timestamp and IP
    - View stats anytime
    """)

# Help section
with st.expander("ℹ️ Help & Tips"):
    st.markdown("""
    ### CSV Format
    Your CSV should have at least these columns:
    - `username`: Creator's username (without @)
    - `email`: Email address
    
    ### Campaign & Tracking
    - Set a unique campaign name for tracking
    - Each email includes an invisible tracking pixel
    - View open rates with "View Tracking Stats" button
    - Track which creators engaged with your emails
    
    ### Rate Limits
    - Zoho allows max 50 emails per hour
    - We use 30 emails per batch with 40-minute gaps for safety
    - Adjust intervals and batch sizes in the sidebar
    
    ### Template Variables
    - Use `{username}` in subject or body to personalize
    
    ### Attachments
    - Upload files directly (PDF, DOCX, images)
    - Same attachment is sent to all recipients
    - Files are automatically cleaned up after sending
    
    ### Timezone
    - Select your timezone in the sidebar
    - All times are shown in your selected timezone
    """)

# Email Database Section
st.markdown("---")
st.header("📊 Email Database")

# Initialize database
email_db = EmailDatabase()

# Create tabs for different views
db_tab1, db_tab2, db_tab3 = st.tabs(["Recent Emails", "Campaign Analytics", "Search & Export"])

with db_tab1:
    st.subheader("📧 Recently Sent Emails")
    
    # Get recent emails
    recent_emails = email_db.get_recent_emails(limit=100)
    
    if recent_emails:
        # Create DataFrame for display
        import pandas as pd
        df = pd.DataFrame(recent_emails)
        
        # Format timestamps
        if 'sent_at' in df.columns:
            df['sent_at'] = pd.to_datetime(df['sent_at']).dt.strftime('%Y-%m-%d %I:%M %p')
        if 'first_opened_at' in df.columns:
            df['first_opened_at'] = pd.to_datetime(df['first_opened_at']).dt.strftime('%Y-%m-%d %I:%M %p')
        
        # Display key columns
        display_cols = ['sent_at', 'username', 'recipient_email', 'subject', 
                       'campaign', 'template_version', 'opened', 'open_count']
        display_cols = [col for col in display_cols if col in df.columns]
        
        st.dataframe(
            df[display_cols],
            use_container_width=True,
            hide_index=True
        )
        
        # Show total stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Emails", len(df))
        with col2:
            opened_count = df['opened'].sum() if 'opened' in df.columns else 0
            st.metric("Total Opened", opened_count)
        with col3:
            open_rate = (opened_count / len(df) * 100) if len(df) > 0 else 0
            st.metric("Open Rate", f"{open_rate:.1f}%")
    else:
        st.info("No emails sent yet")

with db_tab2:
    st.subheader("📈 Campaign Performance Analytics")
    
    # Get unique campaigns
    all_emails = email_db.get_recent_emails(limit=10000)
    if all_emails:
        campaigns = list(set([e['campaign'] for e in all_emails if e.get('campaign')]))
        campaigns.sort(reverse=True)
        
        if campaigns:
            selected_campaign = st.selectbox(
                "Select Campaign",
                campaigns,
                help="Choose a campaign to view detailed analytics"
            )
            
            if selected_campaign:
                # Get base campaign name (without version suffix)
                base_campaign = selected_campaign.rsplit('_', 2)[0] if '_v' in selected_campaign else selected_campaign
                
                # Get campaign stats
                stats = email_db.get_campaign_stats(base_campaign)
                
                if stats:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Sent", stats.get('total_sent', 0))
                    with col2:
                        st.metric("Opened", stats.get('total_opened', 0))
                    with col3:
                        st.metric("Open Rate", f"{stats.get('open_rate', 0):.1f}%")
                    with col4:
                        st.metric("Avg Opens/Email", f"{stats.get('avg_opens_per_email', 0):.1f}")
                
                # Template version comparison
                st.markdown("#### Template Performance Comparison")
                template_perf = email_db.get_template_performance(base_campaign)
                
                if template_perf:
                    perf_df = pd.DataFrame(template_perf)
                    
                    # Create bar chart
                    st.bar_chart(
                        data=perf_df.set_index('template_version')['open_rate'],
                        use_container_width=True
                    )
                    
                    # Show detailed table
                    st.dataframe(
                        perf_df,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No template comparison data available yet")
        else:
            st.info("No campaigns found")
    else:
        st.info("No email data available")

with db_tab3:
    st.subheader("🔍 Search & Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        search_campaign = st.text_input("Search by Campaign", placeholder="e.g., wonder")
        search_recipient = st.text_input("Search by Recipient", placeholder="email or username")
    
    with col2:
        search_subject = st.text_input("Search by Subject", placeholder="keyword in subject")
        search_opened = st.checkbox("Show only opened emails")
    
    if st.button("🔍 Search", type="primary"):
        results = email_db.search_emails(
            campaign=search_campaign if search_campaign else None,
            recipient=search_recipient if search_recipient else None,
            subject_contains=search_subject if search_subject else None,
            opened_only=search_opened
        )
        
        if results:
            st.success(f"Found {len(results)} emails")
            
            # Display results
            results_df = pd.DataFrame(results)
            
            # Format timestamps
            for col in ['sent_at', 'first_opened_at', 'last_opened_at']:
                if col in results_df.columns:
                    results_df[col] = pd.to_datetime(results_df[col]).dt.strftime('%Y-%m-%d %I:%M %p')
            
            # Show relevant columns
            display_cols = ['sent_at', 'username', 'recipient_email', 'subject', 
                          'campaign', 'template_version', 'opened', 'open_count']
            display_cols = [col for col in display_cols if col in results_df.columns]
            
            st.dataframe(
                results_df[display_cols],
                use_container_width=True,
                hide_index=True
            )
            
            # Export option
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name=f"email_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No emails found matching your search criteria")
    
    # Export all emails
    st.markdown("---")
    st.markdown("#### Export All Emails")
    
    export_campaign = st.text_input(
        "Export specific campaign (optional)",
        placeholder="Leave empty to export all emails"
    )
    
    if st.button("📥 Export to CSV"):
        export_path = f"cache/email_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        if email_db.export_to_csv(export_path, campaign=export_campaign if export_campaign else None):
            with open(export_path, 'r') as f:
                csv_data = f.read()
            
            st.download_button(
                label="📥 Download Export",
                data=csv_data,
                file_name=os.path.basename(export_path),
                mime="text/csv"
            )
            
            # Clean up export file
            if os.path.exists(export_path):
                os.remove(export_path)
        else:
            st.error("Failed to export emails")