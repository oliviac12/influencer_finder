# UPDATED /track/open endpoint to properly detect sender opens

import os

# Define sender email(s) - can be a list if you have multiple sender addresses
SENDER_EMAILS = [
    'olivia@unsettled.xyz',
    'olivia@wonder.world',
    os.getenv('SMTP_EMAIL', '').lower(),
    os.getenv('ZOHO_EMAIL', '').lower()
]

@app.route('/track/open')
def track_open():
    """
    Track email open with proper sender detection
    URL parameters: id, campaign, username, recipient_email, sender (optional)
    """
    try:
        # Get tracking parameters
        email_id = request.args.get('id', 'unknown')
        campaign = request.args.get('campaign', 'default')
        username = request.args.get('username', '')
        recipient_email = request.args.get('recipient_email', '').lower()
        
        # Check if this is a sender open (two ways):
        # 1. Explicit sender flag in URL (for previews)
        is_sender_preview = request.args.get('sender', 'false').lower() == 'true'
        
        # 2. Recipient email matches sender email (for sent emails)
        is_sender_email = recipient_email in SENDER_EMAILS
        
        # Mark as sender if either condition is true
        is_sender = is_sender_preview or is_sender_email
        
        # Get additional tracking info
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        timestamp = datetime.now().isoformat()
        
        # Log to local SQLite database
        from database import log_email_open
        log_email_open(
            email_id=email_id,
            campaign=campaign,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=timestamp
        )
        
        # Log to Supabase with proper sender detection
        try:
            supabase = get_supabase()
            supabase.table('email_opens').insert({
                'email_id': email_id,
                'campaign': campaign,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'opened_at': timestamp,
                'is_sender': is_sender  # Properly detected sender status
            }).execute()
            
            if is_sender:
                print(f"✓ Sender open detected: {email_id} from {recipient_email or 'preview'}")
            else:
                print(f"✓ Recipient open tracked: {email_id} to {recipient_email}")
                
        except Exception as e:
            print(f"Error logging open to Supabase: {e}")
        
        # Return 1x1 transparent pixel
        return send_file(
            io.BytesIO(TRACKING_PIXEL),
            mimetype='image/png',
            as_attachment=False
        )
        
    except Exception as e:
        print(f"Error tracking email open: {e}")
        # Still return pixel even if logging fails
        return send_file(
            io.BytesIO(TRACKING_PIXEL),
            mimetype='image/png',
            as_attachment=False
        )