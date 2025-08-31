# COPY THIS FUNCTION TO REPLACE THE @app.route('/api/dashboard') IN YOUR REPLIT main.py
# This is the simplified version focusing on last 24 hours only

@app.route('/api/dashboard')
def api_dashboard():
    """JSON API for dashboard data - focused on last 24 hours"""
    try:
        supabase = get_supabase()
        
        # Calculate 24 hours ago
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        # Emails sent in last 24 hours (from email_sent table)
        sent_24h = supabase.table('email_sent')\
            .select('id', count='exact')\
            .gte('timestamp', last_24h.isoformat())\
            .execute()
        
        # Opens in last 24 hours (excluding sender opens)
        opens_24h = supabase.table('email_opens')\
            .select('id', count='exact')\
            .eq('is_sender', False)\
            .gte('opened_at', last_24h.isoformat())\
            .execute()
        
        # Get unique opens in last 24h for open rate calculation
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
                'sent_24h': total_sent_24h,
                'opens_24h': total_opens_24h,
                'unique_opens_24h': unique_count,
                'open_rate_24h': open_rate_24h,
            },
            'last_updated': now.isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500