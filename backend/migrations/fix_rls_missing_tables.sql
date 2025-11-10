-- Fix RLS for missing tables
-- Date: 2025-11-10
-- Issue: point_usage_logs and subscription_periods missing RLS

-- Enable RLS for point_usage_logs
ALTER TABLE point_usage_logs ENABLE ROW LEVEL SECURITY;

-- Enable RLS for subscription_periods
ALTER TABLE subscription_periods ENABLE ROW LEVEL SECURITY;

-- Create policies for point_usage_logs
-- Allow teachers to view their own usage logs
CREATE POLICY "Teachers can view their own usage logs"
ON point_usage_logs FOR SELECT
USING (auth.uid()::text = teacher_id::text);

-- Allow teachers to insert their own usage logs
CREATE POLICY "Teachers can insert their own usage logs"
ON point_usage_logs FOR INSERT
WITH CHECK (auth.uid()::text = teacher_id::text);

-- Create policies for subscription_periods
-- Allow teachers to view their own subscription periods
CREATE POLICY "Teachers can view their own subscription periods"
ON subscription_periods FOR SELECT
USING (auth.uid()::text = teacher_id::text);

-- Allow teachers to insert their own subscription periods
CREATE POLICY "Teachers can insert their own subscription periods"
ON subscription_periods FOR INSERT
WITH CHECK (auth.uid()::text = teacher_id::text);
