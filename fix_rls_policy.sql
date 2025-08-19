-- Fix RLS policy for email_draft_cache migration
-- Run this in your Supabase SQL Editor

-- Drop the restrictive policy
DROP POLICY IF EXISTS "Allow all operations for authenticated users" ON email_draft_cache;

-- Create a permissive policy that allows all operations
CREATE POLICY "Allow all operations" ON email_draft_cache
    FOR ALL USING (true);

-- Alternative: Temporarily disable RLS completely
-- ALTER TABLE email_draft_cache DISABLE ROW LEVEL SECURITY;