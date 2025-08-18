"""
Email Tracking Service for Wonder Campaign
Enhanced with Supabase email monitoring dashboard
"""
from flask import Flask, request, jsonify, send_file, render_template_string
from database import init_db, log_email_open, get_tracking_stats, get_campaign_stats
import io
import base64
import os
from datetime import datetime, timedelta
from supabase import create_client, Client

app = Flask(__name__)

# Initialize database on startup
init_db()

# Initialize Supabase client
def get_supabase():
    """Get Supabase client"""
    url = os.getenv('SUPABASE_URL', 'https://jvyachugejlsvrwzscoi.supabase.co')
    key = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp2eWFjaHVnZWpsc3Zyd3pzY29pIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU0Nzc0ODgsImV4cCI6MjA3MTA1MzQ4OH0.irmZDdtwmd1pe5Ws_EIU1TNzCZP1no3WGxBEtZh552k')
    return create_client(url, key)

# 1x1 transparent pixel image (base64 encoded)
TRACKING_PIXEL = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
)

@app.route('/')
def home():
    """Enhanced home page with dashboard links"""
    return """
    <h1>Wonder Email Tracking Service</h1>
    <p>Email tracking service for Wonder campaign emails.</p>
    <div style="margin: 20px 0;">
        <h3>📊 Dashboards:</h3>
        <p><a href="/dashboard">🚀 Live Email Dashboard (Supabase)</a></p>
        <p><a href="/stats">📈 Tracking Pixel Stats</a></p>
        <p><a href="/morning-report">☀️ Morning Status Report</a></p>
    </div>
    """

@app.route('/track/open')
def track_open():
    """
    Track email open via 1x1 pixel
    Expected parameters: id (email_id), campaign (optional)
    """
    try:
        # Get tracking parameters
        email_id = request.args.get('id', 'unknown')
        campaign = request.args.get('campaign', 'default')
        
        # Get client info
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        timestamp = datetime.now().isoformat()
        
        # Log the open event to local SQLite
        log_email_open(
            email_id=email_id,
            campaign=campaign,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=timestamp
        )
        
        # Also log to Supabase for dashboard analytics
        try:
            supabase = get_supabase()
            supabase.table('email_opens').insert({
                'email_id': email_id,
                'campaign': campaign,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'opened_at': timestamp
            }).execute()
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

@app.route('/track/sent', methods=['POST'])
def track_sent():
    """
    Track that an email was sent
    Expected JSON body: {email_id, campaign, recipient_email, username}
    """
    try:
        data = request.json
        email_id = data.get('email_id', 'unknown')
        campaign = data.get('campaign', 'default')
        recipient_email = data.get('recipient_email', '')
        username = data.get('username', '')
        timestamp = datetime.now().isoformat()
        
        # Import the new function from database
        from database import log_email_sent
        
        # Log the sent event
        log_email_sent(
            email_id=email_id,
            campaign=campaign,
            recipient_email=recipient_email,
            username=username,
            timestamp=timestamp
        )
        
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

@app.route('/stats')
def stats_page():
    """HTML stats page"""
    try:
        stats = get_tracking_stats()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Wonder Email Tracking Stats</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .stat {{ background: #f5f5f5; padding: 20px; margin: 10px 0; border-radius: 5px; }}
                .campaign {{ background: #e8f4f8; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>📧 Wonder Email Tracking Dashboard</h1>
            
            <div class="stat">
                <h2>📊 Overall Stats</h2>
                <p><strong>Total Emails Sent:</strong> {stats.get('total_sent', 0)}</p>
                <p><strong>Total Opens:</strong> {stats['total_opens']}</p>
                <p><strong>Unique Opens:</strong> {stats['unique_opens']}</p>
                <p><strong>Open Rate:</strong> {stats['open_rate']:.1f}%</p>
                <p><strong>Recent Sent (24h):</strong> {stats.get('recent_sent_24h', 0)}</p>
                <p><strong>Recent Opens (24h):</strong> {stats.get('recent_opens_24h', 0)}</p>
                <p><strong>Last Updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="stat">
                <h2>📈 Campaign Breakdown</h2>
        """
        
        # Add campaign stats
        campaign_stats = get_campaign_stats()
        for campaign, data in campaign_stats.items():
            html += f"""
                <div class="campaign">
                    <h3>{campaign}</h3>
                    <p>Sent: {data.get('sent', 0)} | Opens: {data.get('opens', 0)} | Unique Opens: {data.get('unique_opens', 0)} | Rate: {data.get('open_rate', 0):.1f}%</p>
                </div>
            """
        
        html += """
            </div>
            
            <div class="stat">
                <h2>🔗 API Endpoints</h2>
                <p><code>GET /api/stats</code> - JSON stats for your Streamlit app</p>
                <p><code>GET /track/open?id=EMAIL_ID&campaign=CAMPAIGN</code> - Tracking pixel</p>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"<h1>Error loading stats: {e}</h1>"

@app.route('/api/stats')
def api_stats():
    """JSON API for Streamlit app to fetch stats"""
    try:
        stats = get_tracking_stats()
        campaign_stats = get_campaign_stats()
        
        return jsonify({
            'success': True,
            'overall': stats,
            'campaigns': campaign_stats,
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/campaign/<campaign_name>')
def api_campaign_stats(campaign_name):
    """Get stats for a specific campaign"""
    try:
        campaign_stats = get_campaign_stats()
        
        if campaign_name in campaign_stats:
            return jsonify({
                'success': True,
                'campaign': campaign_name,
                'stats': campaign_stats[campaign_name]
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Campaign {campaign_name} not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test')
def test_tracking():
    """Test endpoint to verify tracking works"""
    return """
    <h1>Test Email Tracking</h1>
    <p>This page contains a tracking pixel. Check the stats to see if it was logged.</p>
    <img src="/track/open?id=test_email_123&campaign=test_campaign" width="1" height="1" style="display:none;">
    <p><a href="/stats">View Stats</a></p>
    """

@app.route('/dashboard')
def supabase_dashboard():
    """Live email dashboard pulling from Supabase"""
    try:
        supabase = get_supabase()
        
        # Get counts from all tables
        scheduled = supabase.table('scheduled_emails').select('id', count='exact').execute()
        sent = supabase.table('sent_emails').select('id', count='exact').execute()
        opens = supabase.table('email_opens').select('id', count='exact').execute()
        
        # Get pending emails
        pending = supabase.table('scheduled_emails')\
            .select('id', count='exact')\
            .eq('status', 'pending')\
            .execute()
        
        # Get failed emails
        failed = supabase.table('scheduled_emails')\
            .select('id', count='exact')\
            .eq('status', 'failed')\
            .execute()
        
        # Get today's stats
        today = datetime.now().date()
        today_sent = supabase.table('sent_emails')\
            .select('id', count='exact')\
            .gte('sent_at', f"{today}T00:00:00")\
            .lte('sent_at', f"{today}T23:59:59")\
            .execute()
        
        today_opens = supabase.table('email_opens')\
            .select('id', count='exact')\
            .gte('opened_at', f"{today}T00:00:00")\
            .lte('opened_at', f"{today}T23:59:59")\
            .execute()
        
        # Get unique opens (distinct email_ids)
        unique_opens = supabase.table('email_opens')\
            .select('email_id', count='exact')\
            .execute()
        
        # Get next 5 scheduled emails
        next_emails = supabase.table('scheduled_emails')\
            .select('username, to_email, scheduled_time, campaign')\
            .eq('status', 'pending')\
            .order('scheduled_time')\
            .limit(5)\
            .execute()
        
        # Get recent sent emails
        recent_sent = supabase.table('sent_emails')\
            .select('username, to_email, sent_at, campaign')\
            .order('sent_at', desc=True)\
            .limit(10)\
            .execute()
        
        # Get recent opens
        recent_opens = supabase.table('email_opens')\
            .select('email_id, campaign, opened_at, ip_address')\
            .order('opened_at', desc=True)\
            .limit(10)\
            .execute()
        
        # Calculate stats
        total_scheduled = scheduled.count or 0
        total_sent = sent.count or 0
        total_opens = opens.count or 0
        total_pending = pending.count or 0
        total_failed = failed.count or 0
        sent_today = today_sent.count or 0
        opens_today = today_opens.count or 0
        
        success_rate = (total_sent / max(total_scheduled, 1)) * 100
        open_rate = (total_opens / max(total_sent, 1)) * 100
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Wonder Email Dashboard</title>
            <meta http-equiv="refresh" content="30">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f7fa; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
                .stat-number {{ font-size: 2em; font-weight: bold; margin-bottom: 5px; }}
                .stat-label {{ color: #666; font-size: 0.9em; }}
                .pending {{ color: #f39c12; }}
                .sent {{ color: #27ae60; }}
                .failed {{ color: #e74c3c; }}
                .scheduled {{ color: #3498db; }}
                .section {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
                .email-list {{ max-height: 300px; overflow-y: auto; }}
                .email-item {{ padding: 10px; border-bottom: 1px solid #eee; }}
                .email-item:last-child {{ border-bottom: none; }}
                .timestamp {{ color: #666; font-size: 0.9em; }}
                .refresh-note {{ text-align: center; color: #666; font-size: 0.9em; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Wonder Email Dashboard</h1>
                    <p>Real-time email campaign monitoring • Auto-refresh every 30 seconds</p>
                    <p><strong>Last Updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S PT')}</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number scheduled">{total_scheduled}</div>
                        <div class="stat-label">Total Scheduled</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number sent">{total_sent}</div>
                        <div class="stat-label">Total Sent</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color: #8e44ad;">{total_opens}</div>
                        <div class="stat-label">Total Opens</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number pending">{total_pending}</div>
                        <div class="stat-label">Pending</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number failed">{total_failed}</div>
                        <div class="stat-label">Failed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number sent">{sent_today}</div>
                        <div class="stat-label">Sent Today</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color: #8e44ad;">{opens_today}</div>
                        <div class="stat-label">Opens Today</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{success_rate:.1f}%</div>
                        <div class="stat-label">Send Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color: #8e44ad;">{open_rate:.1f}%</div>
                        <div class="stat-label">Open Rate</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>⏰ Next 5 Scheduled Emails</h2>
                    <div class="email-list">
        """
        
        if next_emails.data:
            for email in next_emails.data:
                scheduled_time = datetime.fromisoformat(email['scheduled_time'].replace('Z', '+00:00'))
                time_str = scheduled_time.strftime('%b %d, %I:%M %p')
                html += f"""
                        <div class="email-item">
                            <strong>@{email['username']}</strong> → {email['to_email']}
                            <div class="timestamp">📅 {time_str} • Campaign: {email['campaign']}</div>
                        </div>
                """
        else:
            html += '<div class="email-item">No pending emails</div>'
        
        html += """
                    </div>
                </div>
                
                <div class="section">
                    <h2>✅ Recently Sent Emails</h2>
                    <div class="email-list">
        """
        
        if recent_sent.data:
            for email in recent_sent.data:
                sent_time = datetime.fromisoformat(email['sent_at'].replace('Z', '+00:00'))
                time_str = sent_time.strftime('%b %d, %I:%M %p')
                html += f"""
                        <div class="email-item">
                            <strong>@{email['username']}</strong> → {email['to_email']}
                            <div class="timestamp">✅ {time_str} • Campaign: {email['campaign']}</div>
                        </div>
                """
        else:
            html += '<div class="email-item">No emails sent yet</div>'
        
        html += """
                    </div>
                </div>
                
                <div class="section">
                    <h2>👀 Recent Email Opens</h2>
                    <div class="email-list">
        """
        
        if recent_opens.data:
            for open_event in recent_opens.data:
                opened_time = datetime.fromisoformat(open_event['opened_at'].replace('Z', '+00:00'))
                time_str = opened_time.strftime('%b %d, %I:%M %p')
                # Extract location from IP (simplified)
                location = open_event['ip_address'][:7] + "..." if open_event['ip_address'] else "Unknown"
                html += f"""
                        <div class="email-item">
                            <strong>📧 {open_event['email_id']}</strong> 
                            <div class="timestamp">👀 {time_str} • Campaign: {open_event['campaign']} • IP: {location}</div>
                        </div>
                """
        else:
            html += '<div class="email-item">No email opens yet</div>'
        
        html += f"""
                    </div>
                </div>
                
                <div class="refresh-note">
                    🔄 Page auto-refreshes every 30 seconds • 
                    <a href="/morning-report">☀️ Morning Report</a> • 
                    <a href="/api/dashboard">📊 JSON API</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"<h1>Dashboard Error: {e}</h1><p><a href='/'>← Back to Home</a></p>"

@app.route('/morning-report')
def morning_report():
    """Simple morning status report"""
    try:
        supabase = get_supabase()
        
        # Get today's stats
        today = datetime.now().date()
        today_sent = supabase.table('sent_emails')\
            .select('*')\
            .gte('sent_at', f"{today}T00:00:00")\
            .lte('sent_at', f"{today}T23:59:59")\
            .execute()
        
        today_opens = supabase.table('email_opens')\
            .select('*')\
            .gte('opened_at', f"{today}T00:00:00")\
            .lte('opened_at', f"{today}T23:59:59")\
            .execute()
        
        # Get pending emails
        pending = supabase.table('scheduled_emails')\
            .select('*')\
            .eq('status', 'pending')\
            .execute()
        
        # Get failed emails
        failed = supabase.table('scheduled_emails')\
            .select('*')\
            .eq('status', 'failed')\
            .execute()
        
        # Group by campaign
        campaigns = {}
        for email in today_sent.data or []:
            campaign = email.get('campaign', 'Unknown')
            campaigns[campaign] = campaigns.get(campaign, 0) + 1
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Morning Email Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
                .report {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .stat {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
                .success {{ border-left-color: #28a745; }}
                .warning {{ border-left-color: #ffc107; }}
                .danger {{ border-left-color: #dc3545; }}
                .campaign {{ background: #e9ecef; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="report">
                <div class="header">
                    <h1>☀️ Good Morning!</h1>
                    <h2>Email Campaign Status Report</h2>
                    <p>{datetime.now().strftime('%A, %B %d, %Y')}</p>
                </div>
                
                <div class="stat success">
                    <h3>✅ Emails Sent Today</h3>
                    <p><strong>{len(today_sent.data or [])}</strong> emails successfully delivered</p>
                </div>
                
                <div class="stat" style="border-left-color: #8e44ad;">
                    <h3>👀 Emails Opened Today</h3>
                    <p><strong>{len(today_opens.data or [])}</strong> emails opened</p>
                    <p><em>Open Rate: {(len(today_opens.data or []) / max(len(today_sent.data or []), 1)) * 100:.1f}%</em></p>
                </div>
                
                <div class="stat warning">
                    <h3>⏰ Pending Emails</h3>
                    <p><strong>{len(pending.data or [])}</strong> emails waiting to send</p>
                </div>
                
                <div class="stat danger">
                    <h3>❌ Failed Emails</h3>
                    <p><strong>{len(failed.data or [])}</strong> emails failed</p>
                </div>
                
                <div class="stat">
                    <h3>📊 Campaign Breakdown</h3>
        """
        
        if campaigns:
            for campaign, count in campaigns.items():
                html += f'<div class="campaign">{campaign}: {count} sent</div>'
        else:
            html += '<div class="campaign">No campaigns sent today</div>'
        
        html += f"""
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <p><a href="/dashboard">📊 View Full Dashboard</a></p>
                    <p><small>Report generated at {datetime.now().strftime('%H:%M:%S PT')}</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"<h1>Report Error: {e}</h1>"

@app.route('/api/dashboard')
def api_dashboard():
    """JSON API for dashboard data"""
    try:
        supabase = get_supabase()
        
        # Get all stats
        scheduled = supabase.table('scheduled_emails').select('id', count='exact').execute()
        sent = supabase.table('sent_emails').select('id', count='exact').execute()
        pending = supabase.table('scheduled_emails').select('id', count='exact').eq('status', 'pending').execute()
        failed = supabase.table('scheduled_emails').select('id', count='exact').eq('status', 'failed').execute()
        
        today = datetime.now().date()
        today_sent = supabase.table('sent_emails')\
            .select('id', count='exact')\
            .gte('sent_at', f"{today}T00:00:00")\
            .lte('sent_at', f"{today}T23:59:59")\
            .execute()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_scheduled': scheduled.count or 0,
                'total_sent': sent.count or 0,
                'pending': pending.count or 0,
                'failed': failed.count or 0,
                'sent_today': today_sent.count or 0,
                'success_rate': ((sent.count or 0) / max(scheduled.count or 1, 1)) * 100
            },
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)