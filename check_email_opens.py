"""
Check email opens to see who's opening emails
"""
import requests
import json

# Query Supabase to see recent email opens
print("Checking recent email opens to identify sender vs recipient opens...")

# You'll need to check this in your Supabase dashboard or via SQL query
# For now, let's create a script you can run on Replit to check

tracking_server_check = """
# Add this endpoint to your Replit tracking server to debug

@app.route('/api/debug/opens')
def debug_opens():
    '''Debug endpoint to see who's opening emails'''
    try:
        supabase = get_supabase()
        
        # Get recent opens with more details
        opens = supabase.table('email_opens')\\
            .select('*')\\
            .order('opened_at', desc=True)\\
            .limit(20)\\
            .execute()
        
        # Group by is_sender status
        sender_opens = []
        recipient_opens = []
        
        for open_record in (opens.data or []):
            if open_record.get('is_sender'):
                sender_opens.append({
                    'email_id': open_record.get('email_id'),
                    'campaign': open_record.get('campaign'),
                    'opened_at': open_record.get('opened_at')
                })
            else:
                recipient_opens.append({
                    'email_id': open_record.get('email_id'),
                    'campaign': open_record.get('campaign'),
                    'opened_at': open_record.get('opened_at')
                })
        
        return jsonify({
            'success': True,
            'total_opens': len(opens.data or []),
            'sender_opens': len(sender_opens),
            'recipient_opens': len(recipient_opens),
            'recent_sender_opens': sender_opens[:5],
            'recent_recipient_opens': recipient_opens[:5]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
"""

print("\n📋 TO CHECK WHO'S OPENING EMAILS:")
print("1. Add the debug endpoint above to your Replit tracking server")
print("2. Deploy it")
print("3. Then run: curl https://tracking.unsettled.xyz/api/debug/opens")
print("\n" + "="*50)

print("\n🔧 TO FIX THE SENDER DETECTION:")
print("""
Update your Replit /track/open endpoint to include this check:

# At the top of the file, define sender email
SENDER_EMAIL = 'olivia@unsettled.xyz'

# In the /track/open route, update the is_sender detection:
@app.route('/track/open')
def track_open():
    # ... existing code ...
    
    # Get parameters
    recipient_email = request.args.get('recipient_email', '').lower()
    
    # Check if this is a sender open (two ways):
    # 1. Explicit sender flag in URL (for previews)
    is_sender_preview = request.args.get('sender', 'false').lower() == 'true'
    
    # 2. Recipient email matches sender email (YOU opening your own sent email)
    is_sender_by_email = recipient_email == SENDER_EMAIL.lower()
    
    # Mark as sender if either condition is true
    is_sender = is_sender_preview or is_sender_by_email
    
    # Log with proper is_sender flag
    supabase.table('email_opens').insert({
        'email_id': email_id,
        'campaign': campaign,
        'is_sender': is_sender  # Will be True if you opened your own email
    }).execute()
""")