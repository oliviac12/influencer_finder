"""
Reply Management Interface for Streamlit
Displays email replies and allows AI-powered response generation
"""
import streamlit as st
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.zoho_reply_manager import ZohoReplyManager
from dotenv import load_dotenv

load_dotenv()


def render_reply_management_section(app, current_campaign=None):
    """Render the reply management section in Streamlit"""
    st.header("💬 Reply Management")
    
    # Initialize reply manager
    reply_manager = ZohoReplyManager()
    
    # Check if email credentials are configured
    if not os.getenv('SMTP_EMAIL') or not os.getenv('SMTP_PASSWORD'):
        st.warning("⚠️ Email credentials not configured. Add SMTP_EMAIL and SMTP_PASSWORD to your .env file")
        return
    
    # Fetch replies section
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        days_back = st.number_input("Fetch emails from last N days", min_value=1, max_value=30, value=7)
    
    with col2:
        campaign_filter = st.text_input("Campaign keyword", value="Wonder" if not current_campaign else current_campaign)
    
    with col3:
        show_all = st.checkbox("Show ALL emails", value=False, help="Show all inbox emails, not just replies")
    
    with col4:
        if st.button("🔄 Fetch Replies", type="primary"):
            with st.spinner("Fetching replies from Zoho..."):
                replies = reply_manager.fetch_recent_replies(
                    days_back=days_back, 
                    campaign_keyword=campaign_filter,
                    show_all=show_all
                )
                st.session_state['fetched_replies'] = replies
                if replies:
                    st.success(f"✅ Found {len(replies)} emails")
                else:
                    st.info("No emails found. Check your IMAP settings or try 'Show ALL emails'")
    
    # Display replies
    if 'fetched_replies' in st.session_state and st.session_state['fetched_replies']:
        replies = st.session_state['fetched_replies']
        
        # Filter options
        st.subheader("📥 Email Replies")
        
        col_a, col_b = st.columns(2)
        with col_a:
            show_only_unhandled = st.checkbox("Show only unhandled", value=True)
        with col_b:
            sort_order = st.selectbox("Sort by", ["Newest First", "Oldest First"])
        
        # Apply filters
        filtered_replies = replies
        if show_only_unhandled:
            filtered_replies = [r for r in replies if not r.get('handled', False)]
        
        # Sort
        reverse = (sort_order == "Newest First")
        filtered_replies.sort(key=lambda x: x.get('date', ''), reverse=reverse)
        
        st.write(f"**Showing {len(filtered_replies)} replies**")
        
        # Display each reply
        for idx, reply in enumerate(filtered_replies):
            # Create unique key for this reply
            reply_key = f"reply_{reply.get('id', idx)}"
            
            # Status indicator
            status = "✅ Handled" if reply.get('handled', False) else "🆕 New"
            
            with st.expander(f"{status} | From: {reply['from_name']} | Subject: {reply['subject'][:50]}..."):
                # Reply details
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.write("**From:**", reply['from'])
                    st.write("**Date:**", reply['date'])
                    st.write("**Subject:**", reply['subject'])
                    
                    # Show if this is matched to a creator
                    if reply.get('username'):
                        st.write("**Matched Creator:**", f"@{reply['username']}")
                    
                    # Debug info
                    with st.expander("🔍 Debug Info"):
                        st.write("**Is Reply:**", reply.get('is_reply', False))
                        st.write("**Campaign Related:**", reply.get('campaign_related', False))
                        st.write("**In-Reply-To:**", reply.get('in_reply_to', 'None'))
                        st.write("**References:**", reply.get('references', 'None')[:100] if reply.get('references') else 'None')
                    
                    # Email body
                    st.text_area("**Message:**", value=reply['body'], height=200, disabled=True, key=f"body_{reply_key}")
                
                with col_right:
                    # Action buttons
                    st.write("**Actions:**")
                    
                    # Generate AI response
                    if st.button("🤖 Generate Response", key=f"gen_{reply_key}"):
                        with st.spinner("Generating AI response..."):
                            # Get campaign context
                            campaign_context = "Wonder luggage brand collaboration focusing on authentic creators who embody choosing their own path"
                            
                            # Generate response
                            ai_response = reply_manager.generate_ai_response(
                                original_email={'subject': reply['subject']},
                                reply_content=reply['body'],
                                creator_username=reply.get('username', 'creator'),
                                campaign_context=campaign_context
                            )
                            
                            # Store in session state
                            st.session_state[f"ai_response_{reply_key}"] = ai_response
                            st.success("✅ Response generated!")
                    
                    # Mark as handled
                    if not reply.get('handled', False):
                        if st.button("✔️ Mark Handled", key=f"handled_{reply_key}"):
                            reply_manager.mark_reply_as_handled(reply['id'])
                            st.success("Marked as handled")
                            st.rerun()
                
                # AI Response section
                if f"ai_response_{reply_key}" in st.session_state:
                    st.subheader("🤖 AI-Generated Response")
                    
                    # Editable response
                    response_text = st.text_area(
                        "Edit response before sending:",
                        value=st.session_state[f"ai_response_{reply_key}"],
                        height=150,
                        key=f"response_edit_{reply_key}"
                    )
                    
                    # Add signature
                    signature = f"\n\nBest,\n{os.getenv('YOUR_NAME', 'Olivia')}\nWonder Team"
                    full_response = response_text + signature
                    
                    # Send options
                    col_send1, col_send2, col_send3 = st.columns(3)
                    
                    with col_send1:
                        if st.button("📤 Send Reply", key=f"send_{reply_key}", type="primary"):
                            with st.spinner("Sending reply..."):
                                success, message = reply_manager.send_reply(
                                    to_email=reply['from_email'],
                                    subject=reply['subject'],
                                    body=full_response,
                                    in_reply_to=reply.get('in_reply_to'),
                                    references=reply.get('references')
                                )
                                
                                if success:
                                    st.success("✅ Reply sent successfully!")
                                    # Mark as handled
                                    reply_manager.mark_reply_as_handled(reply['id'])
                                    # Clear the response from session
                                    del st.session_state[f"ai_response_{reply_key}"]
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                    
                    with col_send2:
                        if st.button("📋 Copy", key=f"copy_{reply_key}"):
                            st.code(full_response, language=None)
                            st.info("Response copied to view")
                    
                    with col_send3:
                        if st.button("🗑️ Discard", key=f"discard_{reply_key}"):
                            del st.session_state[f"ai_response_{reply_key}"]
                            st.rerun()
    
    else:
        # No replies fetched yet
        st.info("👆 Click 'Fetch Replies' to check for new responses to your outreach emails")
    
    # Stats section
    with st.expander("📊 Reply Statistics"):
        if 'fetched_replies' in st.session_state and st.session_state['fetched_replies']:
            replies = st.session_state['fetched_replies']
            
            total_replies = len(replies)
            handled_replies = sum(1 for r in replies if r.get('handled', False))
            unhandled_replies = total_replies - handled_replies
            campaign_replies = sum(1 for r in replies if r.get('campaign_related', False))
            
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("Total Replies", total_replies)
            with col_stat2:
                st.metric("Unhandled", unhandled_replies)
            with col_stat3:
                st.metric("Handled", handled_replies)
            with col_stat4:
                st.metric("Campaign Related", campaign_replies)
        else:
            st.info("No reply data available yet")
    
    # Help section
    with st.expander("ℹ️ How Reply Management Works"):
        st.markdown("""
        ### Reply Detection
        - Connects to your Zoho inbox via IMAP
        - Looks for replies to your outreach emails
        - Matches replies to creators when possible
        
        ### AI Response Generation
        - Claude analyzes the reply sentiment
        - Generates contextual responses based on:
          - Whether they're interested
          - Questions they asked
          - Campaign context
        
        ### Sending Replies
        - Review and edit AI-generated responses
        - Send directly from the app via Zoho SMTP
        - Maintains email threading for conversations
        
        ### Tips
        - Fetch replies regularly (daily recommended)
        - Always review AI responses before sending
        - Mark handled to keep inbox organized
        """)


# Test the interface
if __name__ == "__main__":
    st.set_page_config(page_title="Reply Management", layout="wide")
    st.title("💬 Wonder Campaign Reply Management")
    
    # Mock app object for testing
    class MockApp:
        pass
    
    app = MockApp()
    render_reply_management_section(app, "wonder_fall2025")