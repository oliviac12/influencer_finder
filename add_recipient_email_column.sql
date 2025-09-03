-- Run this in Supabase SQL Editor to add missing columns to email_opens table

-- Add recipient_email column if it doesn't exist
ALTER TABLE email_opens 
ADD COLUMN IF NOT EXISTS recipient_email TEXT;

-- Add username column if it doesn't exist  
ALTER TABLE email_opens 
ADD COLUMN IF NOT EXISTS username TEXT;

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_email_opens_recipient ON email_opens(recipient_email);

-- Verify the columns were added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'email_opens'
ORDER BY ordinal_position;