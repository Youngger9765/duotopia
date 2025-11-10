-- Fix RLS Configuration for JWT-based Backend
-- Date: 2025-11-10
-- Issue: Backend uses JWT auth (not Supabase Auth), so auth.uid() is always NULL
-- Solution: DISABLE RLS for all business tables, let backend handle authorization

-- =============================================================================
-- Background:
-- - Our backend uses JWT tokens for authentication
-- - Supabase RLS policies rely on auth.uid() which is only set by Supabase Auth
-- - When backend connects directly, auth.uid() = NULL, causing all RLS checks to fail
-- - Therefore, we DISABLE RLS and handle all authorization in backend code
-- =============================================================================

-- Core User Tables
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'teachers') THEN
    ALTER TABLE teachers DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for teachers';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'students') THEN
    ALTER TABLE students DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for students';
  END IF;
END $$;

-- Classroom Management
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'classrooms') THEN
    ALTER TABLE classrooms DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for classrooms';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'classroom_students') THEN
    ALTER TABLE classroom_students DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for classroom_students';
  END IF;
END $$;

-- Program & Content
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'programs') THEN
    ALTER TABLE programs DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for programs';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'lessons') THEN
    ALTER TABLE lessons DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for lessons';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'content') THEN
    ALTER TABLE content DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for content';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'content_item') THEN
    ALTER TABLE content_item DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for content_item';
  END IF;
END $$;

-- Assignments
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'assignments') THEN
    ALTER TABLE assignments DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for assignments';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'assignment_content') THEN
    ALTER TABLE assignment_content DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for assignment_content';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'student_assignments') THEN
    ALTER TABLE student_assignments DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for student_assignments';
  END IF;
END $$;

-- Student Progress
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'student_content_progress') THEN
    ALTER TABLE student_content_progress DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for student_content_progress';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'student_item_progress') THEN
    ALTER TABLE student_item_progress DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for student_item_progress';
  END IF;
END $$;

-- Subscription & Billing
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'subscription_periods') THEN
    ALTER TABLE subscription_periods DISABLE ROW LEVEL SECURITY;
    -- Drop any existing policies
    DROP POLICY IF EXISTS "Teachers can view their own subscription periods" ON subscription_periods;
    DROP POLICY IF EXISTS "Teachers can insert their own subscription periods" ON subscription_periods;
    RAISE NOTICE 'RLS disabled for subscription_periods';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'point_usage_logs') THEN
    ALTER TABLE point_usage_logs DISABLE ROW LEVEL SECURITY;
    -- Drop any existing policies
    DROP POLICY IF EXISTS "Teachers can view their own usage logs" ON point_usage_logs;
    DROP POLICY IF EXISTS "Teachers can insert their own usage logs" ON point_usage_logs;
    RAISE NOTICE 'RLS disabled for point_usage_logs';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'teacher_subscription_transaction') THEN
    ALTER TABLE teacher_subscription_transaction DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for teacher_subscription_transaction';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'invoice_status_history') THEN
    ALTER TABLE invoice_status_history DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for invoice_status_history';
  END IF;
END $$;

-- Summary
DO $$
BEGIN
  RAISE NOTICE '=================================================================';
  RAISE NOTICE 'RLS Configuration Complete';
  RAISE NOTICE 'All business tables have RLS DISABLED';
  RAISE NOTICE 'Authorization is handled by backend JWT + code logic';
  RAISE NOTICE '=================================================================';
END $$;
