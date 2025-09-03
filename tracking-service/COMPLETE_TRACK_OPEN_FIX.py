# COMPLETE FIX for /track/open endpoint in your Replit main.py
# Replace the entire /track/open route with this version

# At the top of your main.py file, add this constant:
SENDER_EMAIL = 'olivia@unsettled.xyz'

@app.route('/track/open')
def track_open():
    """
    Track email open with automatic sender detection
    Detects sender by checking if recipient_email matches sender email
    """
    try:
        # Get tracking parameters
        email_id = request.args.get('id', 'unknown')
        campaign = request.args.get('campaign', 'default')
        username = request.args.get('username', '')
        recipient_email = request.args.get('recipient_email', '').lower().strip()
        
        # FIXED: Two ways to detect if this is a sender open:
        # 1. Explicit sender flag in URL (for previews)
        is_sender_preview = request.args.get('sender', 'false').lower() == 'true'
        
        # 2. NEW: Check if recipient email matches sender email 
        # (This catches when YOU open emails from your Sent folder)
        is_sender_by_email = recipient_email == SENDER_EMAIL.lower()
        
        # Mark as sender if EITHER condition is true
        is_sender = is_sender_preview or is_sender_by_email
        
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
        
        # Log to Supabase with CORRECT sender detection
        if not is_sender:
            # Only log recipient opens (not sender opens) for accurate stats
            try:
                supabase = get_supabase()
                supabase.table('email_opens').insert({
                    'email_id': email_id,
                    'campaign': campaign,
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'opened_at': timestamp,
                    'is_sender': False  # Explicitly mark as recipient
                }).execute()
                print(f"✅ Recipient open tracked: {email_id} for {recipient_email}")
            except Exception as e:
                print(f"Error logging open to Supabase: {e}")
        else:
            # Log sender opens separately (optional - you can skip this to keep stats clean)
            print(f"📧 Sender open detected (not counted): {email_id} by {SENDER_EMAIL}")
            
            # Optionally log sender opens with is_sender=True for debugging
            try:
                supabase = get_supabase()
                supabase.table('email_opens').insert({
                    'email_id': email_id,
                    'campaign': campaign,
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'opened_at': timestamp,
                    'is_sender': True  # Mark as sender
                }).execute()
            except Exception as e:
                print(f"Error logging sender open: {e}")
        
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