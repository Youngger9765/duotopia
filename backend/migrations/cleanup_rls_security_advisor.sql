-- =====================================================
-- Duotopia RLS Security Advisor Cleanup Script
-- =====================================================
-- 目的: 消除 Supabase Security Advisor 警告
-- 日期: 2025-12-31
--
-- 背景說明:
-- - Duotopia 使用後端 JWT 認證，不是 Supabase Auth
-- - auth.uid() 在直接 DB 連接時永遠是 NULL
-- - 所有授權在後端代碼中處理
-- - 後端使用 service_role key（會 bypass RLS）
--
-- 策略:
-- 1. 刪除所有未使用的 RLS 政策（消除 "Policy Exists RLS Disabled" 警告）
-- 2. 啟用 RLS 但不創建政策（阻擋 anon key 直接訪問）
-- 3. service_role key 不受影響
-- =====================================================

BEGIN;

-- =====================================================
-- STEP 1: 刪除 teachers 表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "teachers_select_own" ON public.teachers;
DROP POLICY IF EXISTS "teachers_update_own" ON public.teachers;
DROP POLICY IF EXISTS "Teachers can only see their own data" ON public.teachers;
DROP POLICY IF EXISTS "Teachers can update their own data" ON public.teachers;

-- =====================================================
-- STEP 2: 刪除 students 表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "students_select_own" ON public.students;
DROP POLICY IF EXISTS "students_update_own" ON public.students;
DROP POLICY IF EXISTS "teachers_select_classroom_students" ON public.students;
DROP POLICY IF EXISTS "Teachers can see their students" ON public.students;
DROP POLICY IF EXISTS "Students can see their own data" ON public.students;
DROP POLICY IF EXISTS "Students can view their classroom" ON public.students;

-- =====================================================
-- STEP 3: 刪除 classrooms 表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "classrooms_select_own" ON public.classrooms;
DROP POLICY IF EXISTS "classrooms_insert_own" ON public.classrooms;
DROP POLICY IF EXISTS "classrooms_update_own" ON public.classrooms;
DROP POLICY IF EXISTS "classrooms_delete_own" ON public.classrooms;
DROP POLICY IF EXISTS "Teachers can manage their classrooms" ON public.classrooms;

-- =====================================================
-- STEP 4: 刪除 classroom_students 表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "classroom_students_select_teacher" ON public.classroom_students;
DROP POLICY IF EXISTS "classroom_students_select_student" ON public.classroom_students;
DROP POLICY IF EXISTS "classroom_students_insert_teacher" ON public.classroom_students;
DROP POLICY IF EXISTS "classroom_students_delete_teacher" ON public.classroom_students;

-- =====================================================
-- STEP 5: 刪除 programs 表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "programs_select_all" ON public.programs;
DROP POLICY IF EXISTS "programs_insert_own" ON public.programs;
DROP POLICY IF EXISTS "programs_update_own" ON public.programs;
DROP POLICY IF EXISTS "programs_delete_own" ON public.programs;
DROP POLICY IF EXISTS "Teachers can manage their programs" ON public.programs;
DROP POLICY IF EXISTS "Public programs are viewable by all" ON public.programs;

-- =====================================================
-- STEP 6: 刪除 lessons 表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "lessons_select_all" ON public.lessons;
DROP POLICY IF EXISTS "lessons_insert_teacher" ON public.lessons;
DROP POLICY IF EXISTS "lessons_update_teacher" ON public.lessons;
DROP POLICY IF EXISTS "lessons_delete_teacher" ON public.lessons;

-- =====================================================
-- STEP 7: 刪除 contents 表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "contents_select_all" ON public.contents;
DROP POLICY IF EXISTS "contents_insert_teacher" ON public.contents;
DROP POLICY IF EXISTS "contents_update_teacher" ON public.contents;
DROP POLICY IF EXISTS "contents_delete_teacher" ON public.contents;

-- =====================================================
-- STEP 8: 刪除 assignments 表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "assignments_select_teacher" ON public.assignments;
DROP POLICY IF EXISTS "assignments_select_student" ON public.assignments;
DROP POLICY IF EXISTS "assignments_insert_teacher" ON public.assignments;
DROP POLICY IF EXISTS "assignments_update_teacher" ON public.assignments;
DROP POLICY IF EXISTS "assignments_delete_teacher" ON public.assignments;

-- =====================================================
-- STEP 9: 刪除 assignment_contents 表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "assignment_contents_select_teacher" ON public.assignment_contents;
DROP POLICY IF EXISTS "assignment_contents_select_student" ON public.assignment_contents;
DROP POLICY IF EXISTS "assignment_contents_insert_teacher" ON public.assignment_contents;
DROP POLICY IF EXISTS "assignment_contents_delete_teacher" ON public.assignment_contents;

-- =====================================================
-- STEP 10: 刪除 student_assignments 表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "student_assignments_select_teacher" ON public.student_assignments;
DROP POLICY IF EXISTS "student_assignments_select_student" ON public.student_assignments;
DROP POLICY IF EXISTS "student_assignments_update_student" ON public.student_assignments;
DROP POLICY IF EXISTS "Teachers can see all assignments for their students" ON public.student_assignments;
DROP POLICY IF EXISTS "Students can see their own assignments" ON public.student_assignments;

-- =====================================================
-- STEP 11: 刪除 student_content_progress 表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "student_content_progress_select_teacher" ON public.student_content_progress;
DROP POLICY IF EXISTS "student_content_progress_select_student" ON public.student_content_progress;
DROP POLICY IF EXISTS "student_content_progress_insert_student" ON public.student_content_progress;
DROP POLICY IF EXISTS "student_content_progress_update_student" ON public.student_content_progress;

-- =====================================================
-- STEP 12: 刪除 content_items 表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "content_items_select_all" ON public.content_items;
DROP POLICY IF EXISTS "content_items_insert_teacher" ON public.content_items;
DROP POLICY IF EXISTS "content_items_update_teacher" ON public.content_items;
DROP POLICY IF EXISTS "content_items_delete_teacher" ON public.content_items;

-- =====================================================
-- STEP 13: 刪除 student_item_progress 表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "student_item_progress_select_teacher" ON public.student_item_progress;
DROP POLICY IF EXISTS "student_item_progress_select_student" ON public.student_item_progress;
DROP POLICY IF EXISTS "student_item_progress_insert_student" ON public.student_item_progress;
DROP POLICY IF EXISTS "student_item_progress_update_student" ON public.student_item_progress;

-- =====================================================
-- STEP 14: 刪除 subscription 相關表的未使用政策
-- =====================================================
DROP POLICY IF EXISTS "subscriptions_select_own" ON public.teacher_subscription_transactions;
DROP POLICY IF EXISTS "subscriptions_insert_own" ON public.teacher_subscription_transactions;
DROP POLICY IF EXISTS "invoice_history_select_own" ON public.invoice_status_history;
DROP POLICY IF EXISTS "invoice_history_insert_own" ON public.invoice_status_history;

-- =====================================================
-- STEP 15: 為新表啟用 RLS（無政策 = 阻擋 anon key）
-- =====================================================
-- 這些表之前沒有 RLS，啟用後 anon key 無法訪問
-- service_role key 不受影響（會 bypass RLS）

-- user_word_progress
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'user_word_progress') THEN
    ALTER TABLE public.user_word_progress ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled for user_word_progress (no policies = blocked for anon)';
  END IF;
END $$;

-- practice_sessions
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'practice_sessions') THEN
    ALTER TABLE public.practice_sessions ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled for practice_sessions (no policies = blocked for anon)';
  END IF;
END $$;

-- practice_answers
DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'practice_answers') THEN
    ALTER TABLE public.practice_answers ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled for practice_answers (no policies = blocked for anon)';
  END IF;
END $$;

-- =====================================================
-- STEP 16: 特殊處理 alembic_version
-- =====================================================
-- alembic_version 是 Alembic migration 系統表
-- 選項 A: 啟用 RLS（推薦）
-- 選項 B: 從 PostgREST 中排除（需要改 Supabase 設定）

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'alembic_version') THEN
    ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY;
    RAISE NOTICE 'RLS enabled for alembic_version (no policies = blocked for anon)';
  END IF;
END $$;

-- =====================================================
-- STEP 17: 確保所有業務表都啟用 RLS
-- =====================================================
-- 這些表可能已經啟用或禁用，統一啟用

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'teachers') THEN
    ALTER TABLE public.teachers ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'students') THEN
    ALTER TABLE public.students ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'classrooms') THEN
    ALTER TABLE public.classrooms ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'classroom_students') THEN
    ALTER TABLE public.classroom_students ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'programs') THEN
    ALTER TABLE public.programs ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'lessons') THEN
    ALTER TABLE public.lessons ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'contents') THEN
    ALTER TABLE public.contents ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'content_items') THEN
    ALTER TABLE public.content_items ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'assignments') THEN
    ALTER TABLE public.assignments ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'assignment_contents') THEN
    ALTER TABLE public.assignment_contents ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'student_assignments') THEN
    ALTER TABLE public.student_assignments ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'student_content_progress') THEN
    ALTER TABLE public.student_content_progress ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'student_item_progress') THEN
    ALTER TABLE public.student_item_progress ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'teacher_subscription_transactions') THEN
    ALTER TABLE public.teacher_subscription_transactions ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'invoice_status_history') THEN
    ALTER TABLE public.invoice_status_history ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'subscription_periods') THEN
    ALTER TABLE public.subscription_periods ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'point_usage_logs') THEN
    ALTER TABLE public.point_usage_logs ENABLE ROW LEVEL SECURITY;
  END IF;
END $$;

COMMIT;

-- =====================================================
-- 驗證查詢（執行完畢後運行）
-- =====================================================
-- 檢查哪些表有 RLS 政策但 RLS 未啟用
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- 檢查剩餘的 RLS 政策
SELECT
    schemaname,
    tablename,
    policyname
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- =====================================================
-- 完成！
-- =====================================================
-- 執行後，Supabase Security Advisor 應該不再顯示：
-- 1. "Policy Exists RLS Disabled" 警告
-- 2. "RLS Disabled in public" 警告
--
-- 安全性說明：
-- - 所有表都啟用了 RLS
-- - 沒有任何政策 = anon key 無法訪問任何數據
-- - 後端使用 service_role key 會 bypass RLS，正常運作
-- =====================================================
