-- Run this in Supabase SQL Editor to create the email_scheduled table

CREATE TABLE IF NOT EXISTS email_scheduled (
    id SERIAL PRIMARY KEY,
    email_id TEXT NOT NULL,
    campaign TEXT NOT NULL,
    recipient_email TEXT,
    username TEXT,
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_email_scheduled_sent_at ON email_scheduled(sent_at);
CREATE INDEX IF NOT EXISTS idx_email_scheduled_campaign ON email_scheduled(campaign);
CREATE INDEX IF NOT EXISTS idx_email_scheduled_email_id ON email_scheduled(email_id);

-- Verify the table was created
SELECT * FROM email_scheduled LIMIT 1;