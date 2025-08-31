# BEST VERSION - Match opens by campaign for accurate stats

@app.route('/api/dashboard')
def api_dashboard():
    """JSON API for dashboard data - matched by campaign"""
    print("DEBUG: api_dashboard called - matching by campaign")
    try:
        supabase = get_supabase()
        
        # Calculate 24 hours ago
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        # Get scheduled emails in last 24 hours
        scheduled_24h = supabase.table('email_scheduled')\
            .select('email_id, campaign')\
            .gte('sent_at', last_24h.isoformat())\
            .execute()
        
        # Count sent by campaign
        total_sent_24h = len(scheduled_24h.data or [])
        
        # Get list of campaigns from scheduled emails
        active_campaigns = set([x['campaign'] for x in (scheduled_24h.data or [])])
        
        # Get opens in last 24 hours for these campaigns only
        all_opens_24h = []
        for campaign in active_campaigns:
            opens = supabase.table('email_opens')\
                .select('email_id, campaign')\
                .eq('is_sender', False)\
                .eq('campaign', campaign)\
                .gte('opened_at', last_24h.isoformat())\
                .execute()
            all_opens_24h.extend(opens.data or [])
        
        # Count opens
        total_opens_24h = len(all_opens_24h)
        unique_opens_24h = len(set([x['email_id'] for x in all_opens_24h]))
        
        # Calculate accurate open rate
        open_rate_24h = (unique_opens_24h / max(total_sent_24h, 1)) * 100 if total_sent_24h > 0 else 0
        
        # Get breakdown by campaign (optional but useful)
        campaign_stats = {}
        for campaign in active_campaigns:
            sent_in_campaign = len([x for x in (scheduled_24h.data or []) if x['campaign'] == campaign])
            opens_in_campaign = len([x for x in all_opens_24h if x['campaign'] == campaign])
            unique_in_campaign = len(set([x['email_id'] for x in all_opens_24h if x['campaign'] == campaign]))
            
            campaign_stats[campaign] = {
                'sent': sent_in_campaign,
                'opens': opens_in_campaign,
                'unique_opens': unique_in_campaign,
                'open_rate': (unique_in_campaign / max(sent_in_campaign, 1)) * 100
            }
        
        return jsonify({
            'success': True,
            'stats': {
                'sent_24h': total_sent_24h,
                'opens_24h': total_opens_24h,
                'unique_opens_24h': unique_opens_24h,
                'open_rate_24h': open_rate_24h,
            },
            'campaigns': campaign_stats,  # Breakdown by campaign
            'last_updated': now.isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500