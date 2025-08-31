# COPY THIS FUNCTION TO REPLACE THE @app.route('/api/dashboard') IN YOUR REPLIT main.py
# This version uses the existing Supabase tables

@app.route('/api/dashboard')
def api_dashboard():
    """JSON API for dashboard data - focused on last 24 hours"""
    try:
        supabase = get_supabase()
        
        # Calculate 24 hours ago
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        # For sent emails, we'll use the sent_emails table (from old scheduler)
        # OR we can just count unique email_ids from opens as a proxy for "sent"
        # since every email that can be opened must have been sent
        
        # Get all opens in last 24 hours to derive sent count
        all_opens_24h = supabase.table('email_opens')\
            .select('email_id, is_sender')\
            .gte('opened_at', last_24h.isoformat())\
            .execute()
        
        # Separate sender and recipient opens
        recipient_opens = [x for x in (all_opens_24h.data or []) if not x.get('is_sender', False)]
        all_email_ids = set([x['email_id'] for x in (all_opens_24h.data or [])])
        
        # Count metrics
        total_opens_24h = len(recipient_opens)  # Total recipient opens
        unique_opens_24h = len(set([x['email_id'] for x in recipient_opens]))  # Unique emails opened
        
        # For sent count, use unique email IDs (including sender opens)
        # This assumes if we tracked it, it was sent
        total_sent_24h = len(all_email_ids)
        
        # Calculate open rate
        open_rate_24h = (unique_opens_24h / max(total_sent_24h, 1)) * 100 if total_sent_24h > 0 else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'sent_24h': total_sent_24h,
                'opens_24h': total_opens_24h,
                'unique_opens_24h': unique_opens_24h,
                'open_rate_24h': open_rate_24h,
            },
            'last_updated': now.isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500