# COMPLETE FIX: Update your Replit main.py /track/open endpoint
# This fix:
# 1. Captures recipient_email from URL
# 2. Stores it in the email_opens table
# 3. Uses it to detect if sender is opening their own email

# Add this constant at the top of your main.py:
SENDER_EMAIL = 'olivia@unsettled.xyz'

@app.route('/track/open')
def track_open():
    """
    Track email open with proper recipient_email recording and sender detection
    """
    try:
        # Get ALL tracking parameters including recipient_email
        email_id = request.args.get('id', 'unknown')
        campaign = request.args.get('campaign', 'default')
        username = request.args.get('username', '')
        
        # IMPORTANT: Get recipient_email from the URL parameters
        recipient_email = request.args.get('recipient_email', '')
        
        # Check if this is a sender open (two methods):
        # 1. Explicit sender flag (for previews)
        is_sender_preview = request.args.get('sender', 'false').lower() == 'true'
        
        # 2. Check if recipient_email matches sender email
        # This catches when you send test emails to yourself
        is_sender_by_email = recipient_email.lower() == SENDER_EMAIL.lower() if recipient_email else False
        
        # Mark as sender if either condition is true
        is_sender = is_sender_preview or is_sender_by_email
        
        # Get client info
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        timestamp = datetime.now().isoformat()
        
        # Log to local SQLite
        log_email_open(
            email_id=email_id,
            campaign=campaign,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=timestamp
        )
        
        # Log to Supabase with recipient_email included
        try:
            supabase = get_supabase()
            supabase.table('email_opens').insert({
                'email_id': email_id,
                'campaign': campaign,
                'recipient_email': recipient_email,  # NOW STORING RECIPIENT EMAIL!
                'username': username,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'opened_at': timestamp,
                'is_sender': is_sender
            }).execute()
            
            if is_sender:
                print(f"📧 Sender open: {email_id} for {recipient_email}")
            else:
                print(f"✅ Recipient open: {email_id} for {recipient_email}")
                
        except Exception as e:
            print(f"Error logging open to Supabase: {e}")
        
        # Return tracking pixel
        return send_file(
            io.BytesIO(TRACKING_PIXEL),
            mimetype='image/png',
            as_attachment=False
        )
        
    except Exception as e:
        print(f"Error tracking email open: {e}")
        return send_file(
            io.BytesIO(TRACKING_PIXEL),
            mimetype='image/png',
            as_attachment=False
        )

# ALSO: Make sure your email_opens table has these columns:
"""
ALTER TABLE email_opens 
ADD COLUMN IF NOT EXISTS recipient_email TEXT;

ALTER TABLE email_opens 
ADD COLUMN IF NOT EXISTS username TEXT;
"""