# Setup Instructions for Supabase Migration

## Option 1: Fresh Setup (No Existing Table)

If you haven't created the table yet, or want to start fresh:

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Go to **SQL Editor**
4. Copy and paste the contents of `supabase_migration.sql`
5. Click **Run** to execute

This will create the table with the correct schema.

## Option 2: Update Existing Table

If you already have a `providers` table from before:

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Go to **SQL Editor**
4. Copy and paste the contents of `supabase_migration_update.sql`
5. Click **Run** to execute

This will:
- Add `house_address` column
- Add `minimum_quote` column
- Remove `estimated_price` column
- Create the new index

## Verify the Schema

After running either migration, verify the table structure:

1. In Supabase dashboard, go to **Table Editor**
2. Click on the `providers` table
3. Verify the columns match:
   - `id` (bigint)
   - `service_provider` (text)
   - `phone_number` (text)
   - `context_answers` (text)
   - `house_address` (text) ✅ NEW
   - `zip_code` (text)
   - `max_price` (numeric)
   - `job_id` (text)
   - `minimum_quote` (numeric) ✅ NEW
   - `raw_result` (jsonb)
   - `created_at` (timestamptz)

## Test the Setup

Once the migration is complete, test the application:

```bash
# Install dependencies (if not already done)
pip install -r requirements.txt

# Test with CLI
python3 cli.py --demo

# Or start the FastAPI server
uvicorn main:app --reload
```

## Troubleshooting

If you get errors about missing columns:
- Make sure you ran the correct migration script
- Check that the table exists in your Supabase project
- Verify the column names match exactly (case-sensitive)

If you get permission errors:
- Check that Row Level Security (RLS) policies are set correctly
- The migration script includes a permissive policy for development

