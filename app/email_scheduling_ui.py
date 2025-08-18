"""
Email Scheduling UI Component
Provides interface for scheduling emails in Streamlit
"""
import streamlit as st
from datetime import datetime, timedelta, time
import sys
import os
from zoneinfo import ZoneInfo

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from utils.supabase_scheduler import SupabaseEmailScheduler as EmailScheduler
except ImportError:
    from utils.email_scheduler import EmailScheduler


def render_scheduling_section(email_manager, drafts, current_campaign, attachment_path=None):
    """Render email scheduling interface"""
    
    st.subheader("📅 Schedule Email Sending")
    st.caption("🕐 All times shown in Pacific Time (PT)")
    
    # Initialize scheduler with Pacific timezone
    try:
        scheduler = EmailScheduler(timezone="US/Pacific")
    except TypeError:
        # Fallback if timezone parameter not recognized (cached module issue)
        scheduler = EmailScheduler()
        scheduler.timezone = ZoneInfo("US/Pacific")
    pacific_tz = ZoneInfo("US/Pacific")
    
    # Scheduler status at the top
    status_col1, status_col2, status_col3 = st.columns([1, 2, 1])
    
    with status_col1:
        # Check if scheduler is running
        if 'email_scheduler' in st.session_state:
            st.success("✅ Scheduler Active")
        else:
            st.warning("⚠️ Scheduler Not Started")
            st.caption("Emails won't send automatically")
    
    with status_col2:
        # Get schedule stats
        stats = scheduler.get_schedule_stats()
        if stats['pending'] > 0:
            st.info(f"📬 {stats['pending']} emails waiting to send | ✅ {stats['sent']} sent today")
            if stats['next_scheduled']:
                next_time = datetime.fromisoformat(stats['next_scheduled'])
                st.caption(f"Next send: {next_time.strftime('%I:%M %p PT')}")
        else:
            st.info("📭 No emails scheduled")
    
    with status_col3:
        # Quick stats
        if stats['failed'] > 0:
            st.error(f"❌ {stats['failed']} failed")
        else:
            st.metric("Success Rate", "100%" if stats['sent'] > 0 else "—")
    
    # Get unsent drafts
    unsent_drafts = [d for d in drafts 
                     if not email_manager.is_sent(d['username'], current_campaign or "default")]
    
    if not unsent_drafts:
        st.info("No unsent emails to schedule")
        return
    
    # Scheduling options
    tab1, tab2, tab3 = st.tabs(["⏰ Schedule Bulk Send", "📊 View Schedule", "🎯 Quick Schedule"])
    
    with tab1:
        st.write(f"**Schedule {len(unsent_drafts)} unsent emails**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Get current time in Pacific
            now_pacific = datetime.now(pacific_tz)
            
            # Date selection
            schedule_date = st.date_input(
                "Select date (PT)",
                min_value=now_pacific.date(),
                value=now_pacific.date()
            )
            
            # Time selection
            schedule_time = st.time_input(
                "Start time (PT)",
                value=time(10, 0),  # Default to 10 AM PT
                help="First email will be sent at this time (Pacific Time)"
            )
        
        with col2:
            # Option to add interval or send all at once
            send_mode = st.radio(
                "Send mode:",
                ["All at once", "With intervals"],
                index=0,
                help="Send all emails at the same time or space them out"
            )
            
            if send_mode == "With intervals":
                interval = st.slider(
                    "Minutes between emails",
                    min_value=1,
                    max_value=30,
                    value=5,
                    help="Space out emails to avoid spam filters"
                )
                # Calculate end time
                total_minutes = len(unsent_drafts) * interval
                end_time = datetime.combine(schedule_date, schedule_time) + timedelta(minutes=total_minutes)
                st.info(f"Last email at: {end_time.strftime('%I:%M %p')}")
            else:
                interval = 0
                st.info(f"All {len(unsent_drafts)} emails will send at once")
        
        # Preview schedule
        with st.expander("📋 Preview Schedule"):
            start_datetime = datetime.combine(schedule_date, schedule_time)
            
            if interval == 0:  # All at once
                st.write(f"**{start_datetime.strftime('%I:%M %p')}** - Send all {len(unsent_drafts)} emails:")
                for draft in unsent_drafts[:10]:  # Show first 10
                    st.write(f"  • @{draft['username']} ({draft['email']})")
                if len(unsent_drafts) > 10:
                    st.write(f"  • ... and {len(unsent_drafts) - 10} more")
            else:  # With intervals
                current_time = start_datetime
                for idx, draft in enumerate(unsent_drafts[:5]):  # Show first 5
                    st.write(f"{current_time.strftime('%I:%M %p')} - @{draft['username']} ({draft['email']})")
                    current_time += timedelta(minutes=interval)
                if len(unsent_drafts) > 5:
                    st.write(f"... and {len(unsent_drafts) - 5} more")
        
        # Schedule button
        if st.button("📅 Schedule All Emails", type="primary"):
            # Create datetime with Pacific timezone
            start_datetime = datetime.combine(schedule_date, schedule_time)
            start_datetime = start_datetime.replace(tzinfo=pacific_tz)
            
            # Prepare email data
            emails_to_schedule = []
            for draft in unsent_drafts:
                emails_to_schedule.append({
                    'username': draft['username'],
                    'email': draft['email'],
                    'subject': draft['subject'],
                    'body': draft['body'],
                    'attachment_path': attachment_path
                })
            
            # Schedule the emails
            schedule_ids = scheduler.schedule_bulk_emails(
                emails=emails_to_schedule,
                campaign=current_campaign or "default",
                start_time=start_datetime,
                interval_minutes=interval
            )
            
            st.success(f"✅ Scheduled {len(schedule_ids)} emails starting at {start_datetime.strftime('%B %d at %I:%M %p')}")
            st.balloons()
            
            # Show next steps
            st.info("""
            **Important Notes:**
            - Emails will send automatically at scheduled times
            - Keep the app running locally, or deploy to ensure 24/7 sending
            - You can view and manage scheduled emails in the 'View Schedule' tab
            """)
    
    with tab2:
        st.write("**📅 Scheduled Emails**")
        
        # Get schedule stats
        stats = scheduler.get_schedule_stats()
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Pending", stats['pending'])
        with col2:
            st.metric("Sent", stats['sent'])
        with col3:
            st.metric("Failed", stats['failed'])
        with col4:
            st.metric("Total", stats['total'])
        
        # Next scheduled
        if stats['next_scheduled']:
            next_time = datetime.fromisoformat(stats['next_scheduled'])
            st.info(f"⏰ Next email scheduled for: {next_time.strftime('%B %d at %I:%M %p')}")
        
        # Get pending emails for this campaign
        campaign_schedule = scheduler.get_campaign_schedule(current_campaign or "default")
        pending_schedule = [e for e in campaign_schedule if e['status'] == 'pending']
        
        if pending_schedule:
            st.write(f"**Upcoming sends ({len(pending_schedule)})**")
            
            # Show scheduled emails
            for email in pending_schedule[:10]:  # Show first 10
                scheduled_time = email['scheduled_datetime']
                # Ensure we compare timezone-aware datetimes
                if scheduled_time.tzinfo is None:
                    scheduled_time = scheduled_time.replace(tzinfo=pacific_tz)
                time_until = scheduled_time - datetime.now(pacific_tz)
                
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.write(f"@{email['username']}")
                
                with col2:
                    st.write(scheduled_time.strftime('%b %d, %I:%M %p'))
                
                with col3:
                    if time_until.total_seconds() > 0:
                        hours = int(time_until.total_seconds() // 3600)
                        minutes = int((time_until.total_seconds() % 3600) // 60)
                        if hours > 0:
                            st.write(f"In {hours}h {minutes}m")
                        else:
                            st.write(f"In {minutes}m")
                    else:
                        st.write("Ready to send")
                
                with col4:
                    if st.button("❌", key=f"cancel_{email['schedule_id']}", help="Cancel"):
                        scheduler.cancel_scheduled_email(email['schedule_id'])
                        st.rerun()
            
            if len(pending_schedule) > 10:
                st.write(f"... and {len(pending_schedule) - 10} more")
        else:
            st.info("No scheduled emails for this campaign")
        
        # Sent/Failed history
        with st.expander("📜 History"):
            sent_emails = [e for e in campaign_schedule if e['status'] == 'sent']
            failed_emails = [e for e in campaign_schedule if e['status'] == 'failed']
            
            if sent_emails:
                st.write("**✅ Sent**")
                for email in sent_emails[-5:]:  # Last 5
                    if 'sent_at' in email:
                        sent_time = datetime.fromisoformat(email['sent_at'])
                        st.write(f"@{email['username']} - {sent_time.strftime('%b %d at %I:%M %p')}")
            
            if failed_emails:
                st.write("**❌ Failed**")
                for email in failed_emails[-5:]:  # Last 5
                    st.write(f"@{email['username']} - {email.get('last_error', 'Unknown error')}")
    
    with tab3:
        st.write("**🎯 Quick Schedule Options**")
        
        # Add test scheduling section
        with st.expander("🧪 Test Scheduling (Send to yourself)"):
            st.write("Test the scheduling system by sending a test email to yourself")
            
            test_col1, test_col2, test_col3 = st.columns(3)
            
            with test_col1:
                test_email = st.text_input("Your email address:", placeholder="your.email@gmail.com", key="test_email_input")
            
            with test_col2:
                # Time zone selection - just PT and China
                timezone_options = {
                    "Pacific Time (PT)": "US/Pacific",
                    "China Time (CST)": "Asia/Shanghai"
                }
                selected_tz_name = st.selectbox("Time Zone:", list(timezone_options.keys()), key="test_tz_select")
                selected_tz = ZoneInfo(timezone_options[selected_tz_name])
                
            with test_col3:
                # Get current time in selected timezone
                now_in_tz = datetime.now(selected_tz)
                st.caption(f"Current time in {selected_tz_name}:")
                st.caption(f"{now_in_tz.strftime('%I:%M:%S %p')}")
            
            test_col4, test_col5, test_col6 = st.columns(3)
            
            with test_col4:
                # Date selection
                test_date = st.date_input(
                    "Schedule date:",
                    min_value=now_in_tz.date(),
                    value=now_in_tz.date(),
                    key="test_date_input"
                )
            
            with test_col5:
                # Time selection
                default_time = (now_in_tz + timedelta(minutes=5)).time()
                test_time = st.time_input(
                    f"Schedule time ({selected_tz_name}):",
                    value=default_time,
                    key="test_time_input",
                    help=f"Enter time in {selected_tz_name}"
                )
            
            with test_col6:
                # Show when it will send
                scheduled_datetime = datetime.combine(test_date, test_time)
                scheduled_datetime = scheduled_datetime.replace(tzinfo=selected_tz)
                
                # Convert to Pacific for backend
                scheduled_pacific = scheduled_datetime.astimezone(pacific_tz)
                
                # Calculate time until send
                now = datetime.now(selected_tz)
                time_diff = scheduled_datetime - now
                
                if time_diff.total_seconds() > 0:
                    hours = int(time_diff.total_seconds() // 3600)
                    minutes = int((time_diff.total_seconds() % 3600) // 60)
                    if hours > 0:
                        st.info(f"Sends in: {hours}h {minutes}m")
                    else:
                        st.info(f"Sends in: {minutes}m")
                else:
                    st.warning("Time is in the past!")
            
            if st.button("📧 Send Test Scheduled Email", type="primary", disabled=not test_email, key="send_test_btn"):
                # Get current time in selected timezone
                now_in_tz = datetime.now(selected_tz)
                
                # Create scheduled datetime in selected timezone
                scheduled_datetime = datetime.combine(test_date, test_time)
                scheduled_datetime = scheduled_datetime.replace(tzinfo=selected_tz)
                
                # Convert to Pacific for storage (backend uses Pacific)
                scheduled_pacific = scheduled_datetime.astimezone(pacific_tz)
                
                # Create a test email with timezone info
                test_subject = f"[TEST] Scheduled Email - {selected_tz_name}"
                test_body = f"""This is a test of the email scheduling system with timezone support.

SCHEDULING DETAILS:
-------------------
Scheduled at: {now_in_tz.strftime('%B %d, %Y at %I:%M:%S %p')} {selected_tz_name}
Scheduled for: {scheduled_datetime.strftime('%B %d, %Y at %I:%M:%S %p')} {selected_tz_name}

TIMEZONE CONVERSIONS:
--------------------
Your selected time ({selected_tz_name}): {scheduled_datetime.strftime('%I:%M %p on %b %d')}
Pacific Time (system timezone): {scheduled_pacific.strftime('%I:%M %p PT on %b %d')}
Current time in {selected_tz_name}: {now_in_tz.strftime('%I:%M:%S %p')}

If you receive this email at the scheduled time, the timezone handling is working correctly!

Campaign: {current_campaign or 'Test Campaign'}
System Timezone: Pacific Time (PT)
Test Timezone: {selected_tz_name}
                """
                
                # Schedule the test email (convert to Pacific for backend)
                schedule_id = scheduler.schedule_email(
                    email_id=f"test_{now_in_tz.timestamp()}",
                    username="test_user",
                    campaign=current_campaign or "test",
                    to_email=test_email,
                    subject=test_subject,
                    body=test_body,
                    scheduled_time=scheduled_pacific  # Store in Pacific time
                )
                
                # Show success with both times
                st.success(f"✅ Test email scheduled!")
                st.info(f"Will send at: **{scheduled_datetime.strftime('%I:%M %p')} {selected_tz_name}**")
                if selected_tz_name != "Pacific Time (PT)":
                    st.caption(f"({scheduled_pacific.strftime('%I:%M %p PT')} in system time)")
                st.caption(f"Schedule ID: {schedule_id}")
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📤 Send Now", help="Start sending immediately with 5min intervals"):
                start_time = datetime.now() + timedelta(minutes=1)
                emails_to_schedule = []
                for draft in unsent_drafts:
                    emails_to_schedule.append({
                        'username': draft['username'],
                        'email': draft['email'],
                        'subject': draft['subject'],
                        'body': draft['body'],
                        'attachment_path': attachment_path
                    })
                
                schedule_ids = scheduler.schedule_bulk_emails(
                    emails=emails_to_schedule,
                    campaign=current_campaign or "default",
                    start_time=start_time,
                    interval_minutes=5
                )
                st.success(f"✅ Scheduled {len(schedule_ids)} emails to start in 1 minute")
                st.rerun()
        
        with col2:
            if st.button("🌅 Tomorrow 9 AM PT", help="Schedule for tomorrow at 9 AM Pacific"):
                now_pacific = datetime.now(pacific_tz)
                tomorrow_9am = datetime.combine(
                    now_pacific.date() + timedelta(days=1),
                    time(9, 0)
                )
                tomorrow_9am = tomorrow_9am.replace(tzinfo=pacific_tz)
                emails_to_schedule = []
                for draft in unsent_drafts:
                    emails_to_schedule.append({
                        'username': draft['username'],
                        'email': draft['email'],
                        'subject': draft['subject'],
                        'body': draft['body'],
                        'attachment_path': attachment_path
                    })
                
                schedule_ids = scheduler.schedule_bulk_emails(
                    emails=emails_to_schedule,
                    campaign=current_campaign or "default",
                    start_time=tomorrow_9am,
                    interval_minutes=5
                )
                st.success(f"✅ Scheduled {len(schedule_ids)} emails for tomorrow at 9 AM")
                st.rerun()
        
        with col3:
            if st.button("🌙 Tonight 6 PM PT", help="Schedule for today at 6 PM Pacific"):
                now_pacific = datetime.now(pacific_tz)
                today_6pm = datetime.combine(
                    now_pacific.date(),
                    time(18, 0)
                )
                today_6pm = today_6pm.replace(tzinfo=pacific_tz)
                if now_pacific > today_6pm:
                    today_6pm += timedelta(days=1)  # Tomorrow if past 6 PM
                
                emails_to_schedule = []
                for draft in unsent_drafts:
                    emails_to_schedule.append({
                        'username': draft['username'],
                        'email': draft['email'],
                        'subject': draft['subject'],
                        'body': draft['body'],
                        'attachment_path': attachment_path
                    })
                
                schedule_ids = scheduler.schedule_bulk_emails(
                    emails=emails_to_schedule,
                    campaign=current_campaign or "default",
                    start_time=today_6pm,
                    interval_minutes=5
                )
                st.success(f"✅ Scheduled {len(schedule_ids)} emails for 6 PM")
                st.rerun()
    
    # Remove sidebar scheduler status - we'll integrate it into the main section


# Function to start the scheduler (call from main app)
def start_email_scheduler(email_manager):
    """Start the background email scheduler"""
    scheduler = EmailScheduler()
    
    def send_email_callback(to_email, subject, body, username=None, campaign=None, attachment_path=None):
        """Callback function for scheduler to send emails"""
        return email_manager.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            attachment_path=attachment_path,
            username=username,
            campaign=campaign
        )
    
    scheduler.start_background_scheduler(send_email_callback)
    return scheduler