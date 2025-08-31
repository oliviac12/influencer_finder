-- Add is_sender column to email_opens table in Supabase
-- Run this in the Supabase SQL Editor

-- Add the column with a default value of false
ALTER TABLE email_opens 
ADD COLUMN IF NOT EXISTS is_sender BOOLEAN DEFAULT false;

-- Update any existing records to false (they're all recipient opens from before)
UPDATE email_opens 
SET is_sender = false 
WHERE is_sender IS NULL;

-- Create an index for better query performance
CREATE INDEX IF NOT EXISTS idx_email_opens_is_sender 
ON email_opens(is_sender);

-- Verify the column was added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'email_opens'
AND column_name = 'is_sender';