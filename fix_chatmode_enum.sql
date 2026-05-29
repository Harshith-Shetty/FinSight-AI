-- Fix ChatMode enum to use lowercase values
-- This matches the Python enum definition

-- Step 1: Drop the constraint
ALTER TABLE chats ALTER COLUMN mode TYPE VARCHAR(20);

-- Step 2: Drop the old enum
DROP TYPE IF EXISTS chatmode;

-- Step 3: Create new enum with lowercase values
CREATE TYPE chatmode AS ENUM ('HYBRID', 'private');

-- Step 4: Convert column back to enum
ALTER TABLE chats ALTER COLUMN mode TYPE chatmode USING mode::chatmode;
