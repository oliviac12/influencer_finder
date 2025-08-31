"""
Email Database Manager
Stores and retrieves sent email records with full content
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import sqlite3
import hashlib

class EmailDatabase:
    def __init__(self, db_path: str = "cache/email_database.db"):
        """Initialize email database"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create emails table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sent_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id TEXT UNIQUE NOT NULL,
                    campaign TEXT NOT NULL,
                    template_version TEXT,
                    recipient_email TEXT NOT NULL,
                    username TEXT,
                    subject TEXT NOT NULL,
                    body_html TEXT NOT NULL,
                    body_preview TEXT,
                    attachment_name TEXT,
                    scheduled_at TIMESTAMP,
                    sent_at TIMESTAMP NOT NULL,
                    zoho_message_id TEXT,
                    tracking_id TEXT,
                    opened BOOLEAN DEFAULT 0,
                    open_count INTEGER DEFAULT 0,
                    first_opened_at TIMESTAMP,
                    last_opened_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_campaign ON sent_emails(campaign)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipient ON sent_emails(recipient_email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sent_at ON sent_emails(sent_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_template ON sent_emails(template_version)")
            
            conn.commit()
    
    def log_email_sent(self, 
                      email_id: str,
                      campaign: str,
                      recipient_email: str,
                      subject: str,
                      body_html: str,
                      username: Optional[str] = None,
                      template_version: Optional[str] = None,
                      attachment_name: Optional[str] = None,
                      scheduled_at: Optional[datetime] = None,
                      sent_at: Optional[datetime] = None,
                      zoho_message_id: Optional[str] = None,
                      tracking_id: Optional[str] = None) -> bool:
        """
        Log a sent email to the database
        
        Args:
            email_id: Unique identifier for the email
            campaign: Campaign name (includes version like 'wonder_20250829_v1_concise')
            recipient_email: Recipient's email address
            subject: Email subject line
            body_html: Full HTML content of the email
            username: Creator's username
            template_version: Template version used (v1_concise, v2_personalized, etc.)
            attachment_name: Name of attached file if any
            scheduled_at: When email was scheduled
            sent_at: When email was actually sent
            zoho_message_id: Message ID from Zoho if available
            tracking_id: Tracking pixel ID
            
        Returns:
            True if successfully logged, False otherwise
        """
        try:
            # Generate preview text (first 200 chars without HTML)
            import re
            body_preview = re.sub('<[^<]+?>', '', body_html)[:200]
            
            # Use current time if sent_at not provided
            if sent_at is None:
                sent_at = datetime.now()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO sent_emails (
                        email_id, campaign, template_version, recipient_email, 
                        username, subject, body_html, body_preview,
                        attachment_name, scheduled_at, sent_at, 
                        zoho_message_id, tracking_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    email_id, campaign, template_version, recipient_email,
                    username, subject, body_html, body_preview,
                    attachment_name, scheduled_at, sent_at,
                    zoho_message_id, tracking_id
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error logging email to database: {e}")
            return False
    
    def update_open_status(self, email_id: str) -> bool:
        """Update email open status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update open count and timestamps
                cursor.execute("""
                    UPDATE sent_emails 
                    SET opened = 1,
                        open_count = open_count + 1,
                        first_opened_at = COALESCE(first_opened_at, CURRENT_TIMESTAMP),
                        last_opened_at = CURRENT_TIMESTAMP
                    WHERE email_id = ?
                """, (email_id,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"Error updating open status: {e}")
            return False
    
    def get_campaign_stats(self, campaign: str) -> Dict:
        """Get statistics for a specific campaign"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get overall stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_sent,
                        SUM(opened) as total_opened,
                        AVG(open_count) as avg_opens_per_email,
                        MIN(sent_at) as first_sent,
                        MAX(sent_at) as last_sent
                    FROM sent_emails
                    WHERE campaign LIKE ?
                """, (f"{campaign}%",))
                
                row = cursor.fetchone()
                
                if row:
                    return {
                        'total_sent': row[0],
                        'total_opened': row[1] or 0,
                        'open_rate': (row[1] or 0) / max(row[0], 1) * 100,
                        'avg_opens_per_email': row[2] or 0,
                        'first_sent': row[3],
                        'last_sent': row[4]
                    }
                
                return {}
                
        except Exception as e:
            print(f"Error getting campaign stats: {e}")
            return {}
    
    def get_template_performance(self, campaign_base: str) -> List[Dict]:
        """Compare performance across template versions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        template_version,
                        COUNT(*) as sent,
                        SUM(opened) as opened,
                        (SUM(opened) * 100.0 / COUNT(*)) as open_rate
                    FROM sent_emails
                    WHERE campaign LIKE ?
                    GROUP BY template_version
                    ORDER BY open_rate DESC
                """, (f"{campaign_base}%",))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'template_version': row[0],
                        'sent': row[1],
                        'opened': row[2] or 0,
                        'open_rate': row[3] or 0
                    })
                
                return results
                
        except Exception as e:
            print(f"Error getting template performance: {e}")
            return []
    
    def get_recent_emails(self, limit: int = 50) -> List[Dict]:
        """Get recently sent emails"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        email_id, campaign, template_version,
                        recipient_email, username, subject,
                        body_preview, attachment_name,
                        sent_at, opened, open_count,
                        first_opened_at
                    FROM sent_emails
                    ORDER BY sent_at DESC
                    LIMIT ?
                """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"Error getting recent emails: {e}")
            return []
    
    def search_emails(self, 
                     campaign: Optional[str] = None,
                     recipient: Optional[str] = None,
                     subject_contains: Optional[str] = None,
                     template_version: Optional[str] = None,
                     opened_only: bool = False) -> List[Dict]:
        """Search emails with filters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM sent_emails WHERE 1=1"
                params = []
                
                if campaign:
                    query += " AND campaign LIKE ?"
                    params.append(f"%{campaign}%")
                
                if recipient:
                    query += " AND recipient_email LIKE ?"
                    params.append(f"%{recipient}%")
                
                if subject_contains:
                    query += " AND subject LIKE ?"
                    params.append(f"%{subject_contains}%")
                
                if template_version:
                    query += " AND template_version = ?"
                    params.append(template_version)
                
                if opened_only:
                    query += " AND opened = 1"
                
                query += " ORDER BY sent_at DESC"
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"Error searching emails: {e}")
            return []
    
    def export_to_csv(self, output_path: str, campaign: Optional[str] = None) -> bool:
        """Export email records to CSV"""
        try:
            import csv
            
            emails = self.search_emails(campaign=campaign) if campaign else self.get_recent_emails(10000)
            
            if not emails:
                print("No emails to export")
                return False
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if emails:
                    writer = csv.DictWriter(f, fieldnames=emails[0].keys())
                    writer.writeheader()
                    writer.writerows(emails)
            
            print(f"Exported {len(emails)} emails to {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False