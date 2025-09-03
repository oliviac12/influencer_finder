-- Run this in Supabase to find duplicate sends

-- Find recipients who received multiple emails in the same campaign
SELECT 
    recipient_email,
    campaign,
    COUNT(*) as times_sent,
    STRING_AGG(email_id, ', ') as email_ids,
    STRING_AGG(sent_at::text, ', ') as sent_times
FROM email_scheduled
WHERE campaign LIKE 'wonder_20250902%'
GROUP BY recipient_email, campaign
HAVING COUNT(*) > 1
ORDER BY times_sent DESC;

-- See all emails sent to this specific recipient
SELECT 
    email_id,
    campaign,
    recipient_email,
    username,
    scheduled_at,
    sent_at,
    created_at
FROM email_scheduled
WHERE recipient_email = 'alexalaosm@gmail.com'
ORDER BY sent_at DESC;