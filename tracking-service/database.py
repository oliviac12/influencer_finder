"""
Database functions for email tracking
Uses SQLite for simplicity and reliability
"""
import sqlite3
import os
from datetime import datetime
from collections import defaultdict

DB_PATH = 'email_tracking.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = get_db_connection()
    
    # Create email_opens table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS email_opens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT NOT NULL,
            campaign TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create email_sent table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS email_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT NOT NULL UNIQUE,
            campaign TEXT NOT NULL,
            recipient_email TEXT,
            username TEXT,
            timestamp TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for faster queries
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_email_id ON email_opens(email_id)
    ''')
    
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_campaign ON email_opens(campaign)
    ''')
    
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_sent_email_id ON email_sent(email_id)
    ''')
    
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_sent_campaign ON email_sent(campaign)
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"📁 Database initialized at: {os.path.abspath(DB_PATH)}")

def log_email_sent(email_id, campaign, recipient_email, username, timestamp):
    """Log that an email was sent"""
    conn = get_db_connection()
    
    try:
        conn.execute('''
            INSERT OR REPLACE INTO email_sent (email_id, campaign, recipient_email, username, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (email_id, campaign, recipient_email, username, timestamp))
        
        conn.commit()
        print(f"📤 Tracked email sent: {email_id} to {username} (campaign: {campaign})")
        
    except Exception as e:
        print(f"❌ Error logging email sent: {e}")
    finally:
        conn.close()

def log_email_open(email_id, campaign, ip_address, user_agent, timestamp):
    """Log an email open event"""
    conn = get_db_connection()
    
    try:
        conn.execute('''
            INSERT INTO email_opens (email_id, campaign, ip_address, user_agent, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (email_id, campaign, ip_address, user_agent, timestamp))
        
        conn.commit()
        print(f"📧 Tracked email open: {email_id} (campaign: {campaign})")
        
    except Exception as e:
        print(f"❌ Error logging email open: {e}")
    finally:
        conn.close()

def get_tracking_stats():
    """Get overall tracking statistics"""
    conn = get_db_connection()
    
    try:
        # Total emails sent
        total_sent = conn.execute('SELECT COUNT(*) FROM email_sent').fetchone()[0]
        
        # Total opens
        total_opens = conn.execute('SELECT COUNT(*) FROM email_opens').fetchone()[0]
        
        # Unique opens (distinct email_ids that were opened)
        unique_opens = conn.execute('SELECT COUNT(DISTINCT email_id) FROM email_opens').fetchone()[0]
        
        # Calculate actual open rate based on sent emails
        open_rate = (unique_opens / max(total_sent, 1)) * 100 if total_sent > 0 else 0
        
        # Recent opens (last 24 hours)
        recent_opens = conn.execute('''
            SELECT COUNT(*) FROM email_opens 
            WHERE datetime(timestamp) > datetime('now', '-1 day')
        ''').fetchone()[0]
        
        # Recent sends (last 24 hours)
        recent_sent = conn.execute('''
            SELECT COUNT(*) FROM email_sent 
            WHERE datetime(timestamp) > datetime('now', '-1 day')
        ''').fetchone()[0]
        
        return {
            'total_sent': total_sent,
            'total_opens': total_opens,
            'unique_opens': unique_opens,
            'open_rate': open_rate,
            'recent_opens_24h': recent_opens,
            'recent_sent_24h': recent_sent
        }
        
    except Exception as e:
        print(f"❌ Error getting tracking stats: {e}")
        return {
            'total_opens': 0,
            'unique_opens': 0,
            'open_rate': 0,
            'recent_opens_24h': 0
        }
    finally:
        conn.close()

def get_campaign_stats():
    """Get statistics broken down by campaign"""
    conn = get_db_connection()
    
    try:
        # Get sent emails by campaign
        sent_rows = conn.execute('''
            SELECT campaign, COUNT(*) as sent_count
            FROM email_sent 
            GROUP BY campaign
        ''').fetchall()
        
        # Get opens by campaign
        open_rows = conn.execute('''
            SELECT campaign, email_id, COUNT(*) as open_count
            FROM email_opens 
            GROUP BY campaign, email_id
        ''').fetchall()
        
        # Process sent data
        campaign_sent = {}
        for row in sent_rows:
            campaign_sent[row['campaign']] = row['sent_count']
        
        # Process opens data
        campaign_data = defaultdict(lambda: {'opens': 0, 'unique_opens': 0, 'emails_opened': set()})
        
        for row in open_rows:
            campaign = row['campaign']
            campaign_data[campaign]['opens'] += row['open_count']
            campaign_data[campaign]['emails_opened'].add(row['email_id'])
        
        # Combine sent and opens data
        result = {}
        all_campaigns = set(campaign_sent.keys()) | set(campaign_data.keys())
        
        for campaign in all_campaigns:
            sent = campaign_sent.get(campaign, 0)
            opens_data = campaign_data.get(campaign, {'opens': 0, 'emails_opened': set()})
            unique_opens = len(opens_data['emails_opened'])
            
            result[campaign] = {
                'sent': sent,
                'opens': opens_data['opens'],
                'unique_opens': unique_opens,
                'open_rate': (unique_opens / max(sent, 1)) * 100 if sent > 0 else 0
            }
        
        return result
        
    except Exception as e:
        print(f"❌ Error getting campaign stats: {e}")
        return {}
    finally:
        conn.close()

def get_opens_for_email(email_id):
    """Get all opens for a specific email ID"""
    conn = get_db_connection()
    
    try:
        rows = conn.execute('''
            SELECT * FROM email_opens 
            WHERE email_id = ? 
            ORDER BY timestamp DESC
        ''', (email_id,)).fetchall()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        print(f"❌ Error getting opens for email {email_id}: {e}")
        return []
    finally:
        conn.close()

def cleanup_old_data(days_to_keep=90):
    """Clean up tracking data older than specified days"""
    conn = get_db_connection()
    
    try:
        deleted = conn.execute('''
            DELETE FROM email_opens 
            WHERE datetime(timestamp) < datetime('now', '-{} days')
        '''.format(days_to_keep))
        
        conn.commit()
        print(f"🧹 Cleaned up {deleted.rowcount} old tracking records")
        
    except Exception as e:
        print(f"❌ Error cleaning up old data: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    # Test the database functions
    print("🧪 Testing database functions...")
    
    # Initialize
    init_db()
    
    # Test logging an open
    log_email_open(
        email_id='test_user_123',
        campaign='test_campaign',
        ip_address='127.0.0.1',
        user_agent='Test Browser',
        timestamp=datetime.now().isoformat()
    )
    
    # Test getting stats
    stats = get_tracking_stats()
    print(f"📊 Stats: {stats}")
    
    campaign_stats = get_campaign_stats()
    print(f"📈 Campaign stats: {campaign_stats}")
    
    print("✅ Database tests completed!")