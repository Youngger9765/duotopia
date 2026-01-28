-- Reset Staging Database Alembic Version
--
-- Purpose: Fix broken migration chain after consolidating 7 migrations
--
-- Context:
-- - Staging DB's alembic_version points to deleted migration '6334a41a9f41'
-- - New consolidated migration expects DB at 'b2c3d4e5f6a7'
-- - This script resets alembic_version to the correct revision
--
-- Safety: This is safe because:
-- 1. Staging can be reset (confirmed by user)
-- 2. b2c3d4e5f6a7 is main's last migration (confirmed above)
-- 3. New migration uses IF NOT EXISTS for all operations
--
-- Usage:
-- psql $DATABASE_URL < reset_staging_alembic_version.sql

BEGIN;

-- Show current state
SELECT 'Current alembic_version:' AS info;
SELECT * FROM alembic_version;

-- Reset to b2c3d4e5f6a7 (main's last migration)
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('b2c3d4e5f6a7');

-- Confirm new state
SELECT 'New alembic_version:' AS info;
SELECT * FROM alembic_version;

COMMIT;

-- Expected output:
-- Current alembic_version: 6334a41a9f41 (broken - file deleted)
-- New alembic_version: b2c3d4e5f6a7 (main's last migration)
--
-- Next deployment will run: add_org_features migration
