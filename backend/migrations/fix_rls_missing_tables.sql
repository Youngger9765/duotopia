-- Fix RLS Configuration for JWT-based Backend
-- =============================================
-- DISABLE RLS for all business tables because:
-- - Backend uses JWT auth (not Supabase Auth)
-- - auth.uid() is always NULL with direct database connections
-- - All authorization handled in backend code (78 verification points)
--
-- Security Architecture:
-- HTTPS → JWT → Backend Code → Database
-- (No direct frontend-to-database access)

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

-- Content Management
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

-- Assignment Management
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

-- Progress Tracking
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

-- Subscription & Billing (with policy cleanup)
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'subscription_periods') THEN
    -- Drop existing policies first
    DROP POLICY IF EXISTS "Teachers can view their own subscription periods" ON subscription_periods;
    DROP POLICY IF EXISTS "Teachers can insert their own subscription periods" ON subscription_periods;
    DROP POLICY IF EXISTS "Teachers can update their own subscription periods" ON subscription_periods;

    -- Disable RLS
    ALTER TABLE subscription_periods DISABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS disabled for subscription_periods (policies dropped)';
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'point_usage_logs') THEN
    ALTER TABLE point_usage_logs DISABLE ROW LEVEL SECURITY;
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
  RAISE NOTICE 'All 17 business tables have RLS DISABLED';
  RAISE NOTICE 'Authorization is handled by backend JWT + code logic';
  RAISE NOTICE '=================================================================';
END $$;
