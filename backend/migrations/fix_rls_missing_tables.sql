-- Fix RLS for missing tables
-- Date: 2025-11-10
-- Issue: point_usage_logs and subscription_periods missing RLS

-- Enable RLS for point_usage_logs (only if table exists)
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'point_usage_logs') THEN
    ALTER TABLE point_usage_logs ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled for point_usage_logs';
  ELSE
    RAISE NOTICE 'Table point_usage_logs does not exist, skipping';
  END IF;
END $$;

-- Enable RLS for subscription_periods (only if table exists)
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'subscription_periods') THEN
    ALTER TABLE subscription_periods ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled for subscription_periods';
  ELSE
    RAISE NOTICE 'Table subscription_periods does not exist, skipping';
  END IF;
END $$;

-- Create policies for point_usage_logs (only if table exists)
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'point_usage_logs') THEN
    DROP POLICY IF EXISTS "Teachers can view their own usage logs" ON point_usage_logs;
    CREATE POLICY "Teachers can view their own usage logs"
    ON point_usage_logs FOR SELECT
    USING (auth.uid()::text = teacher_id::text);

    DROP POLICY IF EXISTS "Teachers can insert their own usage logs" ON point_usage_logs;
    CREATE POLICY "Teachers can insert their own usage logs"
    ON point_usage_logs FOR INSERT
    WITH CHECK (auth.uid()::text = teacher_id::text);

    RAISE NOTICE 'Policies created for point_usage_logs';
  END IF;
END $$;

-- Create policies for subscription_periods (only if table exists)
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'subscription_periods') THEN
    DROP POLICY IF EXISTS "Teachers can view their own subscription periods" ON subscription_periods;
    CREATE POLICY "Teachers can view their own subscription periods"
    ON subscription_periods FOR SELECT
    USING (auth.uid()::text = teacher_id::text);

    DROP POLICY IF EXISTS "Teachers can insert their own subscription periods" ON subscription_periods;
    CREATE POLICY "Teachers can insert their own subscription periods"
    ON subscription_periods FOR INSERT
    WITH CHECK (auth.uid()::text = teacher_id::text);

    RAISE NOTICE 'Policies created for subscription_periods';
  END IF;
END $$;
