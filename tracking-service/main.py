"""
Email Tracking Service for Wonder Campaign
Simple Flask app to track email opens via tracking pixels
"""
from flask import Flask, request, jsonify, send_file
from database import init_db, log_email_open, get_tracking_stats, get_campaign_stats
import io
import base64
from datetime import datetime

app = Flask(__name__)

# Initialize database on startup
init_db()

# 1x1 transparent pixel image (base64 encoded)
TRACKING_PIXEL = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
)

@app.route('/')
def home():
    """Simple home page"""
    return """
    <h1>Wonder Email Tracking Service</h1>
    <p>Email tracking service for Wonder campaign emails.</p>
    <p><a href="/stats">View Stats</a></p>
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
        
        # Log the open event
        log_email_open(
            email_id=email_id,
            campaign=campaign,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=timestamp
        )
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)