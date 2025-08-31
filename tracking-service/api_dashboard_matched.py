# BETTER VERSION - Only counts opens for emails that were actually scheduled

@app.route('/api/dashboard')
def api_dashboard():
    """JSON API for dashboard data - matched opens to scheduled emails"""
    print("DEBUG: api_dashboard called - matching opens to scheduled emails")
    try:
        supabase = get_supabase()
        
        # Calculate 24 hours ago
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        # Get scheduled emails in last 24 hours
        scheduled_24h = supabase.table('email_scheduled')\
            .select('email_id')\
            .gte('sent_at', last_24h.isoformat())\
            .execute()
        
        # Get the email IDs that were scheduled
        scheduled_email_ids = [x['email_id'] for x in (scheduled_24h.data or [])]
        total_sent_24h = len(scheduled_email_ids)
        
        # Get opens in last 24 hours (excluding sender opens)
        opens_24h = supabase.table('email_opens')\
            .select('email_id')\
            .eq('is_sender', False)\
            .gte('opened_at', last_24h.isoformat())\
            .execute()
        
        # Only count opens for emails that were actually scheduled
        opens_for_scheduled = [x for x in (opens_24h.data or []) 
                               if x['email_id'] in scheduled_email_ids]
        
        total_opens_24h = len(opens_for_scheduled)
        unique_opens_24h = len(set([x['email_id'] for x in opens_for_scheduled]))
        
        # Calculate accurate open rate
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