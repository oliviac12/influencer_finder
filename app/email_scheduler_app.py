"""
Standalone Email Scheduler App
Schedule emails via Zoho with rate limit management
"""
import streamlit as st
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
    
    email_subject = st.text_input(
        "Subject Line",
        value="TikTok Shop Collab with Wonder ✨",
        help="Use {username} to personalize"
    )
    
    email_template = st.text_area(
        "Email Body (HTML supported)",
        value="""<p>Hi {username}!</p>

<p>I've been following your content on TikTok, and your content really aligns with Wonder's values of choosing your own path and living permission-free. Your authentic approach to sharing your journey really resonates with our brand.</p>

<p>I'm reaching out on behalf of Wonder, a design-focused luggage brand. At the moment, you may not NEED another carry-on, but this brand is quite unique - they position themselves as a travel companion for people who choose their own path, and are on their journey to become the person they want to be. That's why you popped into my head and thought you might be a good fit.</p>

<p>I don't want this email to sound like we just talk budget - the most important thing is that we love who you are and who you are becoming. This is a commission-based campaign with gifted carry-on and very attractive performance bonuses on top. We're preparing for the launch in fall and upcoming holiday season and looking for the right creators to partner with during this exciting time.</p>

<p>I've attached more information about Wonder and our collaboration opportunities for you to review.</p>

<p>Let me know what you think!</p>""",
        height=300,
        help="Use {username} to insert the creator's username"
    )
    
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
            
            # Debug: Show what columns were found
            if len(df) > 0:
                st.info(f"📊 CSV loaded: {len(df)} rows, columns: {', '.join(df.columns)}")
                
                # Check for required columns (case-insensitive)
                columns_lower = {col.lower(): col for col in df.columns}
                
                if 'username' in columns_lower and 'email' in columns_lower:
                    username_col = columns_lower['username']
                    email_col = columns_lower['email']
                    recipients = df[[username_col, email_col]].rename(columns={
                        username_col: 'username',
                        email_col: 'email'
                    }).to_dict('records')
                    
                    # Filter out empty rows
                    recipients = [r for r in recipients if r.get('username') and r.get('email')]
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

# Schedule button
st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

with col_btn2:
    if st.button("🚀 Schedule Emails", type="primary", use_container_width=True, disabled=not recipients):
        if recipients:
            with st.spinner(f"Scheduling {len(recipients)} emails..."):
                try:
                    # Initialize scheduler
                    scheduler = ZohoNativeScheduler()
                    
                    # Prepare emails
                    emails_to_schedule = []
                    for recipient in recipients:
                        # Replace placeholders in template
                        body = email_template.replace('{username}', recipient['username'])
                        subject = email_subject.replace('{username}', recipient['username'])
                        
                        emails_to_schedule.append({
                            'username': recipient['username'],
                            'email': recipient['email'],
                            'subject': subject,
                            'body': body,
                            'attachment_path': attachment_path
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
                            campaign="manual_scheduler"
                        )
                        
                        if result['success']:
                            scheduled_ids.append(result['email_id'])
                            status.text(f"✅ [{i+1}/{len(recipients)}] Scheduled @{email_data['username']} for {current_time.strftime('%I:%M %p')}")
                        else:
                            status.text(f"❌ [{i+1}/{len(recipients)}] Failed: @{email_data['username']}")
                        
                        # Update progress
                        progress.progress((i + 1) / len(recipients))
                        
                        # Increment time for next email
                        current_time += timedelta(minutes=interval_minutes)
                    
                    # Success message
                    st.balloons()
                    st.success(f"""
                    ✅ **Scheduling Complete!**
                    - Scheduled: {len(scheduled_ids)} emails
                    - Failed: {len(recipients) - len(scheduled_ids)}
                    - Check your Zoho Outbox to verify
                    """)
                    
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

# History section
if st.session_state.scheduled_count > 0:
    st.markdown("---")
    st.subheader("📊 Session History")
    st.metric("Total Scheduled This Session", st.session_state.scheduled_count)
    
    if st.session_state.scheduling_results:
        history_df = pd.DataFrame(st.session_state.scheduling_results)
        st.dataframe(history_df, use_container_width=True)

# Help section
with st.expander("ℹ️ Help & Tips"):
    st.markdown("""
    ### CSV Format
    Your CSV should have at least these columns:
    - `username`: Creator's username (without @)
    - `email`: Email address
    
    ### Rate Limits
    - Zoho allows max 50 emails per hour
    - We use 30 emails per batch with 40-minute gaps for safety
    - Adjust intervals and batch sizes in the sidebar
    
    ### Template Variables
    - Use `{username}` in subject or body to personalize
    
    ### Attachments
    - Provide full path to attachment file
    - File must exist on the system
    - Same attachment is sent to all recipients
    
    ### Timezone
    - Select your timezone in the sidebar
    - All times are shown in your selected timezone
    """)