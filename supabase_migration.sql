-- Migration script for creating the providers table in Supabase
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS providers (
    id BIGSERIAL PRIMARY KEY,
    service_provider TEXT NOT NULL,
    phone_number TEXT,
    context_answers TEXT,
    house_address TEXT,
    zip_code TEXT,
    max_price NUMERIC(10, 2),
    job_id TEXT NOT NULL,
    minimum_quote NUMERIC(10, 2),
    raw_result JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_providers_job_id ON providers(job_id);
CREATE INDEX IF NOT EXISTS idx_providers_zip_code ON providers(zip_code);
CREATE INDEX IF NOT EXISTS idx_providers_service_provider ON providers(service_provider);
CREATE INDEX IF NOT EXISTS idx_providers_house_address ON providers(house_address);

-- Enable Row Level Security (RLS) - adjust policies as needed
ALTER TABLE providers ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows all operations (adjust based on your security needs)
-- For development, you might want to allow all operations
CREATE POLICY "Allow all operations for anon users" ON providers
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Alternatively, for production, you might want more restrictive policies:
-- CREATE POLICY "Allow read access for anon users" ON providers
--     FOR SELECT
--     USING (true);
-- 
-- CREATE POLICY "Allow insert for anon users" ON providers
--     FOR INSERT
--     WITH CHECK (true);

