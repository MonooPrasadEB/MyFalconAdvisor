-- Migration Script: Update Transaction Status to 5-Status Model
-- Date: 2025-11-16
-- Purpose: Remove 'approved' status, add 'rejected' status
--
-- New status model: pending, executed, rejected, failed, cancelled
-- Old status model: pending, approved, executed, cancelled, failed

BEGIN;

-- Step 1: Update any existing 'approved' transactions
-- These are transactions that were approved but not yet executed
-- Set them to 'pending' since approval is no longer a separate state
UPDATE transactions 
SET status = 'pending',
    notes = CONCAT(COALESCE(notes, ''), E'\n[Migration] Status changed from approved to pending'),
    updated_at = CURRENT_TIMESTAMP
WHERE status = 'approved';

-- Step 2: Drop old constraint
ALTER TABLE transactions 
DROP CONSTRAINT IF EXISTS transactions_status_check;

-- Step 3: Add new constraint with 5-status model
ALTER TABLE transactions 
ADD CONSTRAINT transactions_status_check 
CHECK (status::text = ANY (ARRAY[
    'pending'::character varying,
    'executed'::character varying,
    'rejected'::character varying,
    'failed'::character varying,
    'cancelled'::character varying
]::text[]));

-- Step 4: Verify migration
-- Show count of transactions by status
SELECT 
    status,
    COUNT(*) as count,
    MIN(created_at) as oldest,
    MAX(created_at) as newest
FROM transactions
GROUP BY status
ORDER BY count DESC;

COMMIT;

-- Rollback script (if needed):
-- BEGIN;
-- ALTER TABLE transactions DROP CONSTRAINT transactions_status_check;
-- ALTER TABLE transactions ADD CONSTRAINT transactions_status_check 
-- CHECK (status::text = ANY (ARRAY['pending', 'approved', 'executed', 'cancelled', 'failed']::text[]));
-- COMMIT;

