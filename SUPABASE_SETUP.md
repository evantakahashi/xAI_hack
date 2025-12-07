# Supabase Setup Guide

This project has been migrated from SQLite to Supabase for database storage.

## Prerequisites

1. A Supabase account and project
2. Your Supabase project URL and API key (already configured in `config.py`)

## Setup Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the `supabase` package along with other dependencies.

### 2. Create the Database Table

Run the SQL migration script in your Supabase SQL Editor:

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Go to the SQL Editor
4. Copy and paste the contents of `supabase_migration.sql`
5. Run the migration

Alternatively, you can create the table manually with these columns:

- `id` (BIGSERIAL PRIMARY KEY)
- `service_provider` (TEXT NOT NULL)
- `phone_number` (TEXT)
- `context_answers` (TEXT) - Contains the answers to the 5 context questions as a paragraph
- `house_address` (TEXT) - Full house address collected at the beginning
- `zip_code` (TEXT)
- `max_price` (NUMERIC(10, 2)) - Budget/maximum price collected at the beginning
- `job_id` (TEXT NOT NULL)
- `minimum_quote` (NUMERIC(10, 2)) - Minimum quote (collected later by other parts of the project)
- `raw_result` (JSONB)
- `created_at` (TIMESTAMP WITH TIME ZONE)

### 3. Configure Environment Variables (Optional)

If you want to use environment variables instead of hardcoded values, create a `.env` file:

```env
XAI_API_KEY=your_xai_api_key_here
SUPABASE_URL=https://podtjfttutrybvotsduh.supabase.co
SUPABASE_KEY=your_supabase_api_key_here
```

The Supabase credentials are already configured in `config.py` with the provided values.

### 4. Test the Setup

Run the CLI to test:

```bash
python cli.py --demo
```

Or start the FastAPI server:

```bash
uvicorn main:app --reload
```

## Database Schema

The `providers` table stores:

- **service_provider**: Name of the service provider
- **phone_number**: Contact phone number
- **context_answers**: A paragraph containing the answers to the 5 context questions
- **house_address**: Full house address (collected at the beginning with zip_code, budget, and date)
- **zip_code**: ZIP code for the job location (collected at the beginning)
- **max_price**: Maximum price/budget for the job (collected at the beginning)
- **job_id**: Associated job ID
- **minimum_quote**: Minimum quote (nullable, will be collected later by other parts of the project)
- **raw_result**: Raw JSON data from the search

## Notes

- The `context_answers` field combines all 5 question-answer pairs into a single paragraph
- Row Level Security (RLS) is enabled by default - adjust policies in Supabase dashboard as needed
- The migration script includes indexes for better query performance

