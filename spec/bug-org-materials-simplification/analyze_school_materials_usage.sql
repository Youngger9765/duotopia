-- ========================================
-- 學校教材使用情況分析 SQL 腳本
-- ========================================
-- 用途: 評估移除學校教材層級的影響範圍
-- 執行環境: PostgreSQL
-- 建議: 先在測試環境執行，確認無誤後再於生產環境執行
-- ========================================

-- 1. 總覽統計
-- ========================================
SELECT 
    '總覽統計' AS category,
    'Total Programs' AS metric,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM programs WHERE is_active = true), 0), 2) AS percentage
FROM programs 
WHERE is_active = true

UNION ALL

SELECT 
    '總覽統計',
    'School Materials',
    COUNT(*),
    ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM programs WHERE is_active = true), 0), 2)
FROM programs 
WHERE school_id IS NOT NULL AND is_active = true

UNION ALL

SELECT 
    '總覽統計',
    'Organization Materials',
    COUNT(*),
    ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM programs WHERE is_active = true), 0), 2)
FROM programs 
WHERE organization_id IS NOT NULL AND school_id IS NULL AND is_active = true

UNION ALL

SELECT 
    '總覽統計',
    'Teacher Materials',
    COUNT(*),
    ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM programs WHERE is_active = true), 0), 2)
FROM programs 
WHERE teacher_id IS NOT NULL AND organization_id IS NULL AND school_id IS NULL AND is_active = true

ORDER BY category, metric;


-- 2. 學校教材詳細統計
-- ========================================
SELECT 
    '學校教材分析' AS analysis_type,
    COUNT(DISTINCT p.school_id) AS affected_schools,
    COUNT(DISTINCT p.teacher_id) AS affected_teachers,
    COUNT(DISTINCT p.id) AS total_school_programs,
    COUNT(DISTINCT l.id) AS total_lessons,
    COUNT(DISTINCT c.id) AS total_contents
FROM programs p
LEFT JOIN lessons l ON l.program_id = p.id AND l.is_active = true
LEFT JOIN contents c ON c.lesson_id = l.id AND c.is_active = true
WHERE p.school_id IS NOT NULL AND p.is_active = true;


-- 3. 按學校分組的教材統計
-- ========================================
SELECT 
    s.id AS school_id,
    s.name AS school_name,
    o.name AS organization_name,
    COUNT(DISTINCT p.id) AS program_count,
    COUNT(DISTINCT l.id) AS lesson_count,
    COUNT(DISTINCT c.id) AS content_count,
    COUNT(DISTINCT p.teacher_id) AS creator_count,
    MIN(p.created_at) AS oldest_created,
    MAX(p.created_at) AS newest_created
FROM schools s
LEFT JOIN programs p ON p.school_id = s.id AND p.is_active = true
LEFT JOIN lessons l ON l.program_id = p.id AND l.is_active = true
LEFT JOIN contents c ON c.lesson_id = l.id AND c.is_active = true
LEFT JOIN organizations o ON o.id = s.organization_id
WHERE s.is_active = true
GROUP BY s.id, s.name, o.name
HAVING COUNT(DISTINCT p.id) > 0
ORDER BY program_count DESC;


-- 4. 學校教材的複製追蹤
-- ========================================
-- 檢查有多少班級課程是從學校教材複製的
SELECT 
    '複製追蹤' AS category,
    COUNT(DISTINCT p.id) AS copied_programs_count,
    COUNT(DISTINCT p.classroom_id) AS affected_classrooms
FROM programs p
WHERE p.is_active = true
  AND p.source_metadata IS NOT NULL
  AND p.source_metadata::text LIKE '%school_id%'
  AND p.classroom_id IS NOT NULL;


-- 5. 學校教材的最近活動
-- ========================================
SELECT 
    p.id,
    p.name,
    s.name AS school_name,
    t.name AS creator_name,
    p.created_at,
    p.updated_at,
    (SELECT COUNT(*) FROM lessons WHERE program_id = p.id AND is_active = true) AS lesson_count,
    CASE 
        WHEN p.updated_at > NOW() - INTERVAL '7 days' THEN 'Active (< 7 days)'
        WHEN p.updated_at > NOW() - INTERVAL '30 days' THEN 'Recent (< 30 days)'
        WHEN p.updated_at > NOW() - INTERVAL '90 days' THEN 'Moderate (< 90 days)'
        ELSE 'Inactive (> 90 days)'
    END AS activity_status
FROM programs p
JOIN schools s ON s.id = p.school_id
JOIN teachers t ON t.id = p.teacher_id
WHERE p.school_id IS NOT NULL AND p.is_active = true
ORDER BY p.updated_at DESC
LIMIT 50;


-- 6. 檢查外鍵約束和依賴關係
-- ========================================
SELECT 
    '依賴檢查' AS check_type,
    'Programs with school_id' AS description,
    COUNT(*) AS count
FROM programs 
WHERE school_id IS NOT NULL AND is_active = true

UNION ALL

SELECT 
    '依賴檢查',
    'Lessons under school programs',
    COUNT(DISTINCT l.id)
FROM programs p
JOIN lessons l ON l.program_id = p.id AND l.is_active = true
WHERE p.school_id IS NOT NULL AND p.is_active = true

UNION ALL

SELECT 
    '依賴檢查',
    'Contents under school programs',
    COUNT(DISTINCT c.id)
FROM programs p
JOIN lessons l ON l.program_id = p.id AND l.is_active = true
JOIN contents c ON c.lesson_id = l.id AND c.is_active = true
WHERE p.school_id IS NOT NULL AND p.is_active = true

UNION ALL

SELECT 
    '依賴檢查',
    'Content items under school programs',
    COUNT(DISTINCT ci.id)
FROM programs p
JOIN lessons l ON l.program_id = p.id AND l.is_active = true
JOIN contents c ON c.lesson_id = l.id AND c.is_active = true
JOIN content_items ci ON ci.content_id = c.id
WHERE p.school_id IS NOT NULL AND p.is_active = true;


-- 7. 建議的遷移策略分析
-- ========================================
-- 計算如果提升為機構教材會影響多少資料
SELECT 
    '遷移策略' AS strategy,
    'Option A: Promote to Org Materials' AS description,
    COUNT(DISTINCT p.id) AS programs_affected,
    COUNT(DISTINCT p.organization_id) AS organizations_affected,
    COUNT(DISTINCT p.school_id) AS schools_will_lose_exclusivity
FROM programs p
WHERE p.school_id IS NOT NULL 
  AND p.organization_id IS NOT NULL 
  AND p.is_active = true

UNION ALL

-- 計算如果降級為老師教材會影響多少資料
SELECT 
    '遷移策略',
    'Option B: Demote to Teacher Materials',
    COUNT(DISTINCT p.id),
    COUNT(DISTINCT p.organization_id),
    COUNT(DISTINCT p.school_id)
FROM programs p
WHERE p.school_id IS NOT NULL 
  AND p.teacher_id IS NOT NULL 
  AND p.is_active = true

UNION ALL

-- 計算如果軟刪除會影響多少資料
SELECT 
    '遷移策略',
    'Option C: Soft Delete (NOT RECOMMENDED)',
    COUNT(DISTINCT p.id),
    COUNT(DISTINCT p.organization_id),
    COUNT(DISTINCT p.school_id)
FROM programs p
WHERE p.school_id IS NOT NULL 
  AND p.is_active = true;


-- 8. 資料品質檢查
-- ========================================
-- 檢查異常資料（school_id 有值但 organization_id 為 NULL）
SELECT 
    '資料品質' AS check_category,
    'Invalid: school_id without organization_id' AS issue,
    COUNT(*) AS problematic_records
FROM programs 
WHERE school_id IS NOT NULL 
  AND organization_id IS NULL
  AND is_active = true

UNION ALL

-- 檢查孤立的學校教材（學校已被刪除）
SELECT 
    '資料品質',
    'Orphaned: school_id references deleted school',
    COUNT(DISTINCT p.id)
FROM programs p
LEFT JOIN schools s ON s.id = p.school_id
WHERE p.school_id IS NOT NULL 
  AND p.is_active = true
  AND (s.id IS NULL OR s.is_active = false);


-- 9. 使用者影響分析
-- ========================================
-- 統計會受影響的使用者角色
WITH school_material_teachers AS (
    SELECT DISTINCT ts.teacher_id, ts.school_id, ts.roles
    FROM programs p
    JOIN teacher_schools ts ON ts.school_id = p.school_id
    WHERE p.school_id IS NOT NULL AND p.is_active = true
)
SELECT 
    '使用者影響' AS category,
    CASE 
        WHEN 'school_admin' = ANY(roles) THEN 'School Admins (High Impact)'
        WHEN 'teacher' = ANY(roles) THEN 'Teachers (Medium Impact)'
        ELSE 'Other Roles'
    END AS user_role,
    COUNT(DISTINCT teacher_id) AS affected_user_count,
    COUNT(DISTINCT school_id) AS affected_school_count
FROM school_material_teachers
GROUP BY 
    CASE 
        WHEN 'school_admin' = ANY(roles) THEN 'School Admins (High Impact)'
        WHEN 'teacher' = ANY(roles) THEN 'Teachers (Medium Impact)'
        ELSE 'Other Roles'
    END
ORDER BY affected_user_count DESC;


-- 10. 摘要建議
-- ========================================
SELECT 
    '====== 決策建議 ======' AS summary,
    CASE 
        WHEN (SELECT COUNT(*) FROM programs WHERE school_id IS NOT NULL AND is_active = true) = 0 
            THEN '✅ 安全移除: 無學校教材資料'
        WHEN (SELECT COUNT(*) FROM programs WHERE school_id IS NOT NULL AND is_active = true) < 10 
            THEN '⚠️ 可考慮移除: 學校教材數量少 (< 10), 建議手動遷移'
        WHEN (SELECT ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM programs WHERE is_active = true), 0), 2) 
              FROM programs WHERE school_id IS NOT NULL AND is_active = true) < 10
            THEN '⚠️ 慎重評估: 學校教材使用率 < 10%, 建議使用 Deprecated 方案'
        ELSE '🔴 高風險: 學校教材使用率高, 強烈建議使用標籤系統方案'
    END AS recommendation,
    (SELECT COUNT(*) FROM programs WHERE school_id IS NOT NULL AND is_active = true) AS school_materials_count,
    (SELECT ROUND(COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM programs WHERE is_active = true), 0), 2) 
     FROM programs WHERE school_id IS NOT NULL AND is_active = true) AS usage_percentage;


-- ========================================
-- 執行完畢
-- ========================================
-- 請檢閱以上統計結果，並參考 REMOVE_SCHOOL_MATERIALS_IMPACT_ASSESSMENT.md
-- 進行決策
-- ========================================
