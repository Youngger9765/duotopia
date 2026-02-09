# language: zh-TW
功能: 1Campus SSO 整合與帳號合併
  作為一位使用 1Campus 的學生
  我希望能用教育部單一登入系統登入 DuoTopia
  並且系統能自動識別我在不同縣市或補習班的帳號
  以便我能統一管理學習記錄

  業務規則：
  - 1Campus 為學校學生的主要登入方式
  - 系統透過 one_campus_student_id 或 national_id_hash 識別同一學生
  - 偵測到疑似重複帳號時，在學生端顯示提示並由學生確認合併
  - 補習班學生仍使用傳統 Email 註冊/登入

  場景: 首次使用 1Campus SSO 登入
    假設 學生小明從未在 DuoTopia 註冊過
    當 小明點擊「學校帳號登入」
    並且 完成 1Campus OAuth 授權（taipei.s123@1campus.net）
    並且 系統收到 OAuth 回傳資料:
      | studentAcc              | studentID   | schoolDsns |
      | taipei.s123@1campus.net | A123456789  | tp001      |
    那麼 系統應該創建新的 Student 記錄
    並且 系統應該創建新的 StudentIdentity 記錄，包含:
      | verified_email          | one_campus_student_id | primary_student_id |
      | taipei.s123@1campus.net | A123456789            | (新建的 Student ID) |
    並且 學生可以成功登入

  場景: 使用已註冊的 1Campus 帳號登入
    假設 學生小明已使用 taipei.s123@1campus.net 註冊過
    並且 StudentIdentity 記錄:
      | verified_email          | one_campus_student_id |
      | taipei.s123@1campus.net | A123456789            |
    當 小明使用 1Campus SSO 登入
    並且 系統收到相同的 studentAcc 和 studentID
    那麼 系統應該找到既有的 StudentIdentity
    並且 學生應該直接登入到主帳號
    並且 不應該創建新的 Student 或 StudentIdentity

  場景: 系統偵測到疑似重複帳號（相同 one_campus_student_id）
    假設 學生小明先在補習班用 Gmail 註冊
    並且 StudentIdentity #1 記錄:
      | verified_email   | one_campus_student_id | primary_student_id |
      | john@gmail.com   | null                  | Student #101       |
    當 小明首次使用 1Campus SSO 登入
    並且 系統收到 OAuth 回傳資料:
      | studentAcc              | studentID   |
      | taipei.s123@1campus.net | A123456789  |
    並且 小明填寫身分證字號「A123456789」（與 studentID 相同或不同欄位）
    並且 系統檢查發現沒有其他相同 one_campus_student_id 的 StudentIdentity
    那麼 系統應該創建新的 Student #102
    並且 系統應該創建新的 StudentIdentity #2:
      | verified_email          | one_campus_student_id | primary_student_id |
      | taipei.s123@1campus.net | A123456789            | Student #102       |
    並且 小明成功登入後，系統應該顯示合併提示視窗
    並且 提示訊息應該包含:
      """
      偵測到您可能已有其他學習帳號
      
      我們發現以下帳號可能屬於同一位學生：
      • taipei.s123@1campus.net (台北市○○國中)
      • john@gmail.com (補習班)
      
      合併後的效果：
      ✅ 統一密碼管理
      ✅ 可用任一帳號登入
      ✅ 學習記錄保持獨立（分校/機構分開）
      """

  場景: 學生確認合併帳號（相同 one_campus_student_id）
    假設 系統偵測到疑似重複帳號
    並且 StudentIdentity #1: john@gmail.com（補習班）
    並且 StudentIdentity #2: taipei.s123@1campus.net（學校）
    並且 兩者的 one_campus_student_id 都是 "A123456789"
    當 學生在提示視窗點擊「確認合併」
    那麼 系統應該將 StudentIdentity #2 合併到 StudentIdentity #1
    並且 Student #102 的 identity_id 應該改為 StudentIdentity #1 的 ID
    並且 StudentIdentity #1 應該更新:
      | one_campus_student_id | merge_source     |
      | A123456789            | one_campus_sso   |
    並且 StudentIdentity #2 應該被刪除或標記為已合併
    並且 學生之後可以用 taipei.s123@1campus.net 或 john@gmail.com 登入
    並且 登入後都會看到兩個帳號的學習記錄（分開顯示）

  場景: 學生拒絕合併帳號
    假設 系統偵測到疑似重複帳號
    並且 顯示合併提示視窗
    當 學生點擊「暫時不要」
    那麼 系統應該略過合併
    並且 兩個 StudentIdentity 保持獨立
    並且 下次學生登入時，仍會顯示相同的合併提示

  場景: 跨縣市轉學 - 系統自動識別
    假設 學生小明在基隆就讀時，已使用 1Campus 登入過
    並且 StudentIdentity 記錄:
      | verified_email           | one_campus_student_id | primary_student_id |
      | keelung.s123@1campus.net | A123456789            | Student #201       |
    當 小明轉學到台北市
    並且 小明使用新的 1Campus 帳號登入
    並且 系統收到 OAuth 回傳資料:
      | studentAcc              | studentID   | schoolDsns |
      | taipei.s456@1campus.net | A123456789  | tp001      |
    並且 系統檢查發現 one_campus_student_id "A123456789" 已存在
    那麼 系統應該創建新的 Student #202
    並且 系統應該創建暫時的 StudentIdentity #2
    並且 登入後顯示合併提示:
      """
      偵測到您可能已有其他學習帳號
      
      我們發現以下帳號可能屬於同一位學生：
      • taipei.s456@1campus.net (台北市○○國中)
      • keelung.s123@1campus.net (基隆市○○國中)
      """
    當 學生確認合併
    那麼 基隆和台北的學習記錄都應該保留
    並且 學生可以用任一 1Campus 帳號登入（若舊帳號仍可用）

  場景: 使用 national_id_hash 識別（當 1Campus 未提供 studentID）
    假設 1Campus API 未提供可用的 studentID
    並且 學生小明在首次登入後，系統要求填寫身分證字號（選填）
    並且 小明填寫身分證字號「A123456789」
    並且 系統計算 national_id_hash = SHA256("A123456789")
    並且 StudentIdentity #1 記錄:
      | verified_email   | national_id_hash         |
      | john@gmail.com   | SHA256("A123456789")      |
    當 小明用另一個 Email 註冊並填寫相同身分證字號
    並且 系統計算出相同的 national_id_hash
    那麼 系統應該偵測到疑似重複帳號
    並且 顯示合併提示（流程同上）

  場景: 同時使用 1Campus 和個人 Email 登入
    假設 學生小明已有 StudentIdentity（透過 1Campus）:
      | verified_email          | one_campus_student_id |
      | taipei.s123@1campus.net | A123456789            |
    當 小明想綁定個人 Email "john@gmail.com"
    並且 小明完成 Email 驗證
    並且 系統檢查該 Email 尚未被其他 StudentIdentity 使用
    那麼 系統應該將 john@gmail.com 加入為次要登入方式
    # 注意：這可能需要額外的業務規則設計，目前規格未定義「次要 Email」概念
    # 暫時的處理方式：視為新的 StudentIdentity，並透過 one_campus_student_id 提示合併

  場景: 外籍學生使用居留證號
    假設 學生 John 是外籍學生
    當 John 填寫居留證號「AB12345678」（2碼英文+8碼數字）
    並且 系統計算 national_id_hash = SHA256("AB12345678")
    那麼 系統應該正確處理居留證號格式
    並且 識別邏輯與身分證字號相同

  場景: 缺少身分識別資訊時的處理
    假設 學生小明使用 1Campus 登入
    並且 1Campus 未提供 studentID
    並且 小明未填寫身分證字號
    當 小明後續用個人 Email 註冊
    那麼 系統無法透過身分識別資訊比對
    並且 系統應該退回使用 verified_email 機制
    並且 兩個帳號保持獨立（除非 Email 相同）

  場景大綱: 系統偵測條件測試
    假設 StudentIdentity #1 記錄:
      | verified_email   | one_campus_student_id | national_id_hash |
      | john@gmail.com   | <id1>                 | <hash1>          |
    並且 新登入嘗試創建 StudentIdentity #2:
      | verified_email   | one_campus_student_id | national_id_hash |
      | mary@gmail.com   | <id2>                 | <hash2>          |
    那麼 系統應該<結果>

    範例:
      | id1        | hash1      | id2        | hash2      | 結果               |
      | A123456789 | null       | A123456789 | null       | 偵測到重複並提示   |
      | null       | hash_abc   | null       | hash_abc   | 偵測到重複並提示   |
      | A123456789 | hash_abc   | B987654321 | hash_xyz   | 不提示（不同人）   |
      | null       | null       | null       | null       | 不提示（無識別資訊）|
      | A123456789 | hash_abc   | A123456789 | hash_abc   | 偵測到重複並提示   |
