-- Migration script to add call-related fields to providers table
-- Run this in your Supabase SQL Editor

-- Add new columns for call tracking and negotiated prices
DO $$ 
BEGIN
    -- Add negotiated_price column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'providers' AND column_name = 'negotiated_price') THEN
        ALTER TABLE providers ADD COLUMN negotiated_price NUMERIC(10, 2);
    END IF;
    
    -- Add call_status column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'providers' AND column_name = 'call_status') THEN
        ALTER TABLE providers ADD COLUMN call_status TEXT DEFAULT 'pending';
    END IF;
    
    -- Add call_transcript column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'providers' AND column_name = 'call_transcript') THEN
        ALTER TABLE providers ADD COLUMN call_transcript TEXT;
    END IF;
END $$;

-- Create index for call_status for faster queries
CREATE INDEX IF NOT EXISTS idx_providers_call_status ON providers(call_status);

-- Add check constraint for call_status values
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'providers_call_status_check'
    ) THEN
        ALTER TABLE providers ADD CONSTRAINT providers_call_status_check 
        CHECK (call_status IN ('pending', 'in_progress', 'completed', 'failed'));
    END IF;
END $$;

