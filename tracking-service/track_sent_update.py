# ADD THIS TO YOUR REPLIT main.py - Updates the /track/sent endpoint to log to Supabase

@app.route('/track/sent', methods=['POST'])
def track_sent():
    """
    Track that an email was sent/scheduled
    Expected JSON body: {email_id, campaign, recipient_email, username}
    """
    try:
        data = request.json
        email_id = data.get('email_id', 'unknown')
        campaign = data.get('campaign', 'default')
        recipient_email = data.get('recipient_email', '')
        username = data.get('username', '')
        timestamp = datetime.now().isoformat()
        
        # Log to local SQLite (existing code)
        from database import log_email_sent
        log_email_sent(
            email_id=email_id,
            campaign=campaign,
            recipient_email=recipient_email,
            username=username,
            timestamp=timestamp
        )
        
        # ALSO log to Supabase for dashboard tracking
        try:
            supabase = get_supabase()
            # Create a new table or use existing sent_emails table
            supabase.table('email_scheduled').insert({
                'email_id': email_id,
                'campaign': campaign,
                'recipient_email': recipient_email,
                'username': username,
                'scheduled_at': timestamp,  # When it was scheduled
                'sent_at': timestamp  # Assumes sent immediately (adjust if using delayed send)
            }).execute()
            print(f"✅ Logged scheduled email to Supabase: {email_id}")
        except Exception as e:
            print(f"Warning: Could not log to Supabase: {e}")
            # Don't fail the request if Supabase logging fails
        
        return jsonify({
            'success': True,
            'message': 'Email send tracked',
            'email_id': email_id
        })
        
    except Exception as e:
        print(f"Error tracking email sent: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# AND UPDATE THE /api/dashboard endpoint:

@app.route('/api/dashboard')
def api_dashboard():
    """JSON API for dashboard data - using email_scheduled table"""
    try:
        supabase = get_supabase()
        
        # Calculate 24 hours ago
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        # Emails scheduled/sent in last 24 hours
        sent_24h = supabase.table('email_scheduled')\
            .select('id', count='exact')\
            .gte('sent_at', last_24h.isoformat())\
            .execute()
        
        # Opens in last 24 hours (excluding sender opens)
        opens_24h = supabase.table('email_opens')\
            .select('id', count='exact')\
            .eq('is_sender', False)\
            .gte('opened_at', last_24h.isoformat())\
            .execute()
        
        # Get unique opens in last 24h
        unique_opens_24h = supabase.table('email_opens')\
            .select('email_id')\
            .eq('is_sender', False)\
            .gte('opened_at', last_24h.isoformat())\
            .execute()
        
        # Count unique email IDs
        unique_count = len(set([x['email_id'] for x in (unique_opens_24h.data or [])]))
        
        # Calculate metrics
        total_sent_24h = sent_24h.count or 0
        total_opens_24h = opens_24h.count or 0
        open_rate_24h = (unique_count / max(total_sent_24h, 1)) * 100 if total_sent_24h > 0 else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'sent_24h': total_sent_24h,  # From email_scheduled table
                'opens_24h': total_opens_24h,
                'unique_opens_24h': unique_count,
                'open_rate_24h': open_rate_24h,
            },
            'last_updated': now.isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500