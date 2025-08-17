"""
Email Tracking Dashboard for Streamlit App
Shows email open rates, engagement metrics, and reply management
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.email_tracking_integration import EmailTrackingManager
import plotly.express as px
import plotly.graph_objects as go

def render_email_tracking_dashboard(campaign_name=None):
    """Render the email tracking dashboard in Streamlit"""
    st.header("📊 Email Tracking Dashboard")
    
    # Initialize tracking manager
    tracker = EmailTrackingManager("https://tracking.unsettled.xyz")
    
    # Fetch latest stats from tracking service
    with st.spinner("Fetching tracking data..."):
        stats = tracker.fetch_tracking_stats()
    
    if not stats or not stats.get("success"):
        st.warning("⚠️ Tracking service not connected. Deploy the tracking service to Replit first.")
        st.info("Once deployed, your tracking data will appear here automatically.")
        return
    
    # Overall Stats Section
    st.subheader("📈 Overall Email Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    overall = stats.get("overall", {})
    with col1:
        st.metric("Total Opens", overall.get("total_opens", 0))
    with col2:
        st.metric("Unique Opens", overall.get("unique_opens", 0))
    with col3:
        st.metric("Open Rate", f"{overall.get('open_rate', 0):.1f}%")
    with col4:
        st.metric("Last 24h Opens", overall.get("recent_opens_24h", 0))
    
    # Campaign-specific stats
    if campaign_name:
        st.subheader(f"🎯 Campaign: {campaign_name}")
        
        campaign_report = tracker.get_campaign_email_report(campaign_name)
        
        if campaign_report["tracking_stats"].get("success"):
            campaign_data = campaign_report["tracking_stats"]["stats"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Campaign Opens", campaign_data.get("opens", 0))
            with col2:
                st.metric("Unique Recipients", campaign_data.get("unique", 0))
            with col3:
                st.metric("Campaign Open Rate", f"{campaign_data.get('rate', 0):.1f}%")
        
        # Creator-level tracking
        st.subheader("👥 Creator Engagement")
        
        creators_data = campaign_report.get("creators", {})
        if creators_data:
            # Build dataframe for display
            rows = []
            for username, emails in creators_data.items():
                for email in emails:
                    rows.append({
                        "Creator": f"@{username}",
                        "Sent At": email["sent_at"][:16],
                        "Status": "✅ Opened" if email["opened"] else "⏳ Not Opened",
                        "Open Count": email["open_count"],
                        "First Opened": email["first_opened_at"][:16] if email["first_opened_at"] else "-",
                        "Last Opened": email["last_opened_at"][:16] if email["last_opened_at"] else "-"
                    })
            
            if rows:
                df = pd.DataFrame(rows)
                
                # Add filters
                col1, col2 = st.columns(2)
                with col1:
                    status_filter = st.selectbox(
                        "Filter by Status",
                        ["All", "Opened", "Not Opened"]
                    )
                with col2:
                    sort_by = st.selectbox(
                        "Sort by",
                        ["Sent At", "Open Count", "Creator"]
                    )
                
                # Apply filters
                if status_filter == "Opened":
                    df = df[df["Status"] == "✅ Opened"]
                elif status_filter == "Not Opened":
                    df = df[df["Status"] == "⏳ Not Opened"]
                
                # Sort
                df = df.sort_values(by=sort_by, ascending=False if sort_by == "Open Count" else True)
                
                # Display
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Engagement chart
                if st.checkbox("Show Engagement Timeline"):
                    # This would show a timeline of when emails were opened
                    st.info("📅 Timeline visualization coming soon!")
            else:
                st.info("No email data yet for this campaign.")
    
    # All campaigns overview
    st.subheader("📊 All Campaigns")
    
    campaigns = stats.get("campaigns", {})
    if campaigns:
        # Create comparison chart
        campaign_names = list(campaigns.keys())
        opens = [campaigns[c]["opens"] for c in campaign_names]
        unique_opens = [campaigns[c]["unique"] for c in campaign_names]
        
        fig = go.Figure(data=[
            go.Bar(name='Total Opens', x=campaign_names, y=opens),
            go.Bar(name='Unique Opens', x=campaign_names, y=unique_opens)
        ])
        fig.update_layout(
            title="Campaign Performance Comparison",
            barmode='group',
            xaxis_title="Campaign",
            yaxis_title="Count"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Future Features Preview
    with st.expander("🚀 Coming Soon: Reply Management"):
        st.markdown("""
        ### Email Reply Features (In Development)
        
        **Automatic Reply Detection**
        - Connect Gmail/email provider API
        - Auto-detect replies to your outreach emails
        - Flag high-priority responses
        
        **AI-Powered Response Generation**
        - Claude generates contextual responses
        - Maintains conversation history
        - Suggests follow-up timing
        
        **Workflow Automation**
        - Auto-follow-up for opened but not replied
        - Schedule response sequences
        - Track full conversation threads
        """)
    
    # Refresh button
    if st.button("🔄 Refresh Tracking Data"):
        st.rerun()
    
    # Export tracking data
    if st.button("📥 Export Tracking Report"):
        report = tracker.get_campaign_email_report(campaign_name) if campaign_name else stats
        
        # Convert to CSV
        if campaign_name and "creators" in report:
            rows = []
            for username, emails in report["creators"].items():
                for email in emails:
                    rows.append({
                        "Username": username,
                        "Campaign": campaign_name,
                        "Sent": email["sent_at"],
                        "Opened": email["opened"],
                        "Open Count": email["open_count"]
                    })
            
            if rows:
                df = pd.DataFrame(rows)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download Tracking Report",
                    data=csv,
                    file_name=f"tracking_report_{campaign_name}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )


def render_mini_tracking_widget(username, campaign):
    """Mini tracking widget to show in email outreach section"""
    tracker = EmailTrackingManager("https://tracking.unsettled.xyz")
    
    # Get status for this creator
    email_status = tracker.get_creator_email_status(username, campaign)
    
    if email_status:
        latest = email_status[-1]  # Get most recent email
        
        if latest["opened"]:
            st.success(f"✅ Email opened {latest['open_count']} time(s)")
            if latest["first_opened_at"]:
                st.caption(f"First opened: {latest['first_opened_at'][:16]}")
        else:
            st.info("⏳ Email sent, not yet opened")
            st.caption(f"Sent: {latest['sent_at'][:16]}")
    else:
        st.caption("No tracking data yet")


# Test the dashboard
if __name__ == "__main__":
    # This would be called from your main Streamlit app
    st.set_page_config(page_title="Email Tracking Dashboard", layout="wide")
    
    st.title("📧 Wonder Campaign Email Tracking")
    
    # Render dashboard
    render_email_tracking_dashboard("wonder_fall2025")