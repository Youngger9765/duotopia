# language: zh-TW

功能: 整合後的點數扣除與學習報告
  作為系統
  當學生完成身分整合後
  AI 點數仍扣除到各自的機構/教師
  學習報告以機構/教師為單位獨立呈現

  背景:
    假設 系統中存在機構「A補習班」
    並且 系統中存在學校「A補習班-1分校」隸屬於機構「A補習班」
    並且 系統中存在學校「A補習班-2分校」隸屬於機構「A補習班」
    並且 系統中存在機構「B補習班」
    並且 系統中存在學校「B補習班-1校」隸屬於機構「B補習班」
    並且 系統中存在個人教師「王老師」(ID: 10)

  規則: 點數扣除針對各自的機構/教師

    場景: 同一學生在不同機構使用 AI 功能，點數分別扣除
      假設 系統中存在 StudentIdentity 資料如下
        | id | verified_email   |
        | 1  | ming@example.com |
      並且 StudentIdentity (ID: 1) 關聯學生帳號如下
        | id  | name   | school              |
        | 101 | 王小明 | A補習班-1分校       |
        | 308 | 王小明 | B補習班-1校         |
      並且 「A補習班」擁有 AI 點數 10000 點
      並且 「B補習班」擁有 AI 點數 8000 點
      當 學生 (ID: 101) 使用 AI 語音評分功能，消耗 50 點
      那麼 操作成功
      並且 「A補習班」的剩餘 AI 點數為 9950 點
      並且 「B補習班」的剩餘 AI 點數為 8000 點（不變）
      並且 系統中存在點數使用記錄如下
        | student_id | feature_type        | points_used | teacher_or_org |
        | 101        | speech_assessment   | 50          | A補習班        |

    場景: 同一學生在個人教師處使用 AI 功能
      假設 StudentIdentity (ID: 1) 關聯學生帳號如下
        | id  | name   | teacher    |
        | 412 | 王小明 | 王老師     |
      並且 個人教師「王老師」擁有訂閱配額 5000 點
      當 學生 (ID: 412) 使用 AI 語音評分功能，消耗 30 點
      那麼 操作成功
      並且 個人教師「王老師」的剩餘配額為 4970 點
      並且 系統中存在點數使用記錄如下
        | student_id | teacher_id | feature_type        | points_used |
        | 412        | 10         | speech_assessment   | 30          |

    場景: 驗證點數使用記錄仍指向各自的 Student ID
      假設 StudentIdentity (ID: 1) 關聯學生帳號如下
        | id  | name   | school              |
        | 101 | 王小明 | A補習班-1分校       |
        | 205 | 王小明 | A補習班-2分校       |
      當 學生 (ID: 101) 使用 AI 功能，消耗 50 點
      並且 學生 (ID: 205) 使用 AI 功能，消耗 30 點
      那麼 系統中存在點數使用記錄如下
        | student_id | points_used |
        | 101        | 50          |
        | 205        | 30          |
      並且 不存在使用 StudentIdentity ID 的點數記錄

  規則: 學習報告以機構/教師為單位獨立呈現

    場景: 機構查看學生學習報告，僅看該機構的資料
      假設 StudentIdentity (ID: 1) 關聯學生帳號如下
        | id  | name   | school              |
        | 101 | 王小明 | A補習班-1分校       |
        | 308 | 王小明 | B補習班-1校         |
      並且 學生 (ID: 101) 在「A補習班-1分校」有學習進度如下
        | content_name | score | completed_at |
        | 基礎會話     | 85    | 2026-02-01   |
        | 進階會話     | 90    | 2026-02-05   |
      並且 學生 (ID: 308) 在「B補習班-1校」有學習進度如下
        | content_name | score | completed_at |
        | 商業英文     | 75    | 2026-02-03   |
      當 「A補習班」查詢學生「王小明」的學習報告
      那麼 報告中包含以下學習記錄
        | content_name | score | completed_at |
        | 基礎會話     | 85    | 2026-02-01   |
        | 進階會話     | 90    | 2026-02-05   |
      並且 報告中不包含「商業英文」的記錄

    場景: 機構查看學生列表，僅顯示該機構的學生帳號
      假設 StudentIdentity (ID: 1) 關聯學生帳號如下
        | id  | name   | school              |
        | 101 | 王小明 | A補習班-1分校       |
        | 205 | 王小明 | A補習班-2分校       |
        | 308 | 王小明 | B補習班-1校         |
      當 「A補習班」查詢所有學生列表
      那麼 學生列表包含以下資料
        | student_id | name   | school            |
        | 101        | 王小明 | A補習班-1分校     |
        | 205        | 王小明 | A補習班-2分校     |
      並且 學生列表不包含 student_id 為 308 的記錄

    場景: 個人教師查看學生學習報告
      假設 StudentIdentity (ID: 1) 關聯學生帳號如下
        | id  | name   | teacher    |
        | 412 | 王小明 | 王老師     |
        | 101 | 王小明 | (機構)     |
      並且 學生 (ID: 412) 在「王老師」處有學習進度如下
        | content_name | score | completed_at |
        | 日常對話     | 88    | 2026-02-06   |
      並且 學生 (ID: 101) 在機構有學習進度如下
        | content_name | score | completed_at |
        | 基礎會話     | 85    | 2026-02-01   |
      當 個人教師「王老師」查詢學生「王小明」的學習報告
      那麼 報告中包含以下學習記錄
        | content_name | score | completed_at |
        | 日常對話     | 88    | 2026-02-06   |
      並且 報告中不包含「基礎會話」的記錄

  規則: 學生可查看跨機構的統一學習檔案（可選功能）

    場景: 學生登入後查看個人統一學習檔案
      假設 學生使用 Email "ming@example.com" 登入成功
      並且 登入的 StudentIdentity (ID: 1) 關聯學生帳號如下
        | id  | school              | learning_records_count |
        | 101 | A補習班-1分校       | 5                      |
        | 205 | A補習班-2分校       | 3                      |
        | 308 | B補習班-1校         | 7                      |
      當 學生查詢「我的統一學習檔案」
      那麼 檔案中包含以下帳號資訊
        | student_id | school              | learning_records_count | is_primary |
        | 101        | A補習班-1分校       | 5                      | true       |
        | 205        | A補習班-2分校       | 3                      | false      |
        | 308        | B補習班-1校         | 7                      | false      |
      並且 檔案中顯示 Email 為 "ming@example.com"
      並且 檔案中顯示總學習記錄數為 15（5+3+7）

  規則: 整合不影響既有資料查詢邏輯

    場景: 驗證教師查詢班級學生時，資料正確
      假設 教師「張老師」管理「A補習班-1分校」的「初級班」
      並且 「初級班」包含學生如下
        | student_id | name   |
        | 101        | 王小明 |
        | 102        | 李小華 |
      並且 學生 (ID: 101) 已整合到 StudentIdentity (ID: 1)
      當 教師「張老師」查詢「初級班」的學生列表
      那麼 學生列表包含以下資料
        | student_id | name   |
        | 101        | 王小明 |
        | 102        | 李小華 |
      並且 查詢結果不受 StudentIdentity 整合影響

    場景: 驗證作業指派仍使用 Student ID
      假設 學生 (ID: 101) 已整合到 StudentIdentity (ID: 1)
      並且 教師「張老師」指派作業「基礎會話練習」給學生 (ID: 101)
      那麼 系統中存在作業指派記錄如下
        | student_id | assignment_name  |
        | 101        | 基礎會話練習     |
      並且 作業指派不使用 StudentIdentity ID
