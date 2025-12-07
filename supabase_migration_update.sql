-- Migration script to UPDATE existing providers table in Supabase
-- Run this in your Supabase SQL Editor if you already have a providers table
-- This will modify the existing table to match the new schema

-- Add new columns (if they don't exist)
DO $$ 
BEGIN
    -- Add house_address column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'providers' AND column_name = 'house_address') THEN
        ALTER TABLE providers ADD COLUMN house_address TEXT;
    END IF;
    
    -- Add minimum_quote column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'providers' AND column_name = 'minimum_quote') THEN
        ALTER TABLE providers ADD COLUMN minimum_quote NUMERIC(10, 2);
    END IF;
END $$;

-- Remove estimated_price column if it exists
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'providers' AND column_name = 'estimated_price') THEN
        ALTER TABLE providers DROP COLUMN estimated_price;
    END IF;
END $$;

-- Create new indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_providers_house_address ON providers(house_address);

-- Note: The other indexes should already exist from the original migration

