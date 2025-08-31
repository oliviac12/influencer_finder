# Testing Email Tracking: Sender vs Recipient Differentiation

## Quick Automated Test

Run this command to automatically test the tracking differentiation:
```bash
python3 test_tracking_differentiation.py
```

This will:
1. Generate two tracking pixels (sender vs recipient)
2. Trigger both pixels
3. Verify sender opens don't count in stats
4. Verify recipient opens do count in stats

## Manual Testing Steps

### Step 1: Check Current Stats
Visit: https://tracking.unsettled.xyz/stats
- Note the current "Total Opens" number
- Note the current "Unique Opens" number

### Step 2: Send Yourself a Test Email
1. Open the Email Scheduler app:
   ```bash
   streamlit run app/email_scheduler_app.py
   ```

2. Upload a CSV with just your email:
   ```csv
   username,email
   test_yourself,olivia@unsettled.xyz
   ```

3. Schedule the email for immediate delivery

4. Check your email and open it

### Step 3: Check Stats Again
1. Go back to: https://tracking.unsettled.xyz/stats
2. The opens count should NOT have increased (because you're the sender)

### Step 4: Send to a Different Email
1. Use a different email address (like a personal Gmail)
2. Create a new CSV:
   ```csv
   username,email
   test_recipient,your.personal@gmail.com
   ```

3. Schedule and send the email
4. Open it from the recipient's inbox

### Step 5: Verify Stats Updated
1. Check https://tracking.unsettled.xyz/stats again
2. NOW the opens count should have increased by 1

## Verifying in Supabase

1. Go to your Supabase dashboard
2. Check the `email_opens` table
3. You should see entries with:
   - `is_sender: true` (your preview opens - not counted)
   - `is_sender: false` (recipient opens - counted in stats)

## Testing in the Streamlit App

In your Email Scheduler app, the tracking section should show:
- Only recipient opens (not your previews)
- Accurate open rates based on actual recipients

## What to Look For

✅ **Working correctly if:**
- Your email previews don't increase open counts
- Recipient opens do increase open counts
- Dashboard shows only recipient activity
- Supabase has both types of opens logged with correct flags

❌ **Not working if:**
- All opens are counted the same
- Stats increase when you preview emails
- No `is_sender` field in Supabase
- Missing `&sender=true` in preview pixel URLs

## Debugging

If tracking isn't differentiating:

1. **Check the pixel URL in your sent email:**
   - View email source
   - Find the `<img>` tag with tracking pixel
   - For your previews, URL should contain `&sender=true`
   - For recipients, URL should NOT have this parameter

2. **Check Replit logs:**
   ```
   Visit your Replit project
   Check the console output
   Should see: "Sender preview opened: [email_id] from campaign [campaign]"
   ```

3. **Check Supabase directly:**
   ```sql
   -- See all opens with sender flag
   SELECT email_id, campaign, is_sender, opened_at 
   FROM email_opens 
   ORDER BY opened_at DESC 
   LIMIT 20;
   ```

## Important Notes

- The SQLite database (on Replit) doesn't track `is_sender` to avoid schema migration
- Only Supabase tracks the `is_sender` flag
- Dashboard stats are pulled from Supabase with `is_sender = false` filter
- This prevents your testing from skewing the metrics