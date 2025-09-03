"""
Add this duplicate detection to email_scheduler_app.py after loading the CSV
"""

# After line 540 where recipients are loaded, add:

# Remove duplicate email addresses
if recipients:
    import pandas as pd
    
    # Convert to DataFrame for easy duplicate handling
    df_recipients = pd.DataFrame(recipients)
    
    # Check for duplicates
    duplicates = df_recipients[df_recipients.duplicated(subset=['email'], keep=False)]
    
    if not duplicates.empty:
        st.warning(f"⚠️ Found {len(duplicates)} duplicate email addresses in your list")
        
        # Show duplicates
        with st.expander("View Duplicate Emails"):
            for email in duplicates['email'].unique():
                dupes = df_recipients[df_recipients['email'] == email]
                st.write(f"**{email}** appears {len(dupes)} times:")
                for _, row in dupes.iterrows():
                    st.text(f"  - @{row['username']}")
        
        # Remove duplicates (keep first occurrence)
        df_recipients = df_recipients.drop_duplicates(subset=['email'], keep='first')
        recipients = df_recipients.to_dict('records')
        
        st.info(f"✅ Removed duplicates. Will send to {len(recipients)} unique email addresses")

# Also add a check before sending to prevent double-sends:
"""
# Before scheduling each email, check if already sent today
sent_today = set()  # Track what we've sent in this session

for recipient in recipients:
    email_key = f"{recipient['email']}_{campaign_with_version}"
    
    if email_key in sent_today:
        st.warning(f"⚠️ Skipping duplicate: {recipient['email']} already scheduled")
        continue
    
    # Schedule the email...
    result = scheduler.schedule_email(...)
    
    if result['success']:
        sent_today.add(email_key)  # Mark as sent
"""