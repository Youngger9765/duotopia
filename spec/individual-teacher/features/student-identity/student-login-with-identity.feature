# language: zh-TW

功能: 學生使用統一身分登入
  作為學生
  當我完成 Email 認證並整合身分後
  我可以使用兩種方式登入：
  1. 新流程：直接使用 Email 和統一密碼登入
  2. 舊流程：透過老師Email→班級→學生名稱→密碼（兼容未綁定Email的學生）

  背景:
    假設 系統中存在機構「A補習班」
    並且 系統中存在學校「A補習班-1分校」隸屬於機構「A補習班」
    並且 系統中存在學校「A補習班-2分校」隸屬於機構「A補習班」
    並且 系統中存在個人教師「王老師」(email: wang@example.com)

  規則: 使用 Email 登入到主帳號

    場景: 成功使用 Email 和統一密碼登入
      假設 系統中存在 StudentIdentity 資料如下
        | id | verified_email   | primary_student_id | password_hash  |
        | 1  | ming@example.com | 101                | hash_password1 |
      並且 StudentIdentity (ID: 1) 關聯學生帳號如下
        | id  | name   | school              | is_primary_account |
        | 101 | 王小明 | A補習班-1分校       | true               |
        | 205 | 王小明 | A補習班-2分校       | false              |
      當 學生使用以下資料登入
        | email            | password  |
        | ming@example.com | password1 |
      那麼 操作成功
      並且 登入的學生 ID 為 101
      並且 登入的學生姓名為「王小明」
      並且 登入 token 關聯到 StudentIdentity (ID: 1)

    場景: Email 正確但密碼錯誤
      假設 系統中存在 StudentIdentity 資料如下
        | id | verified_email   | password_hash  |
        | 1  | ming@example.com | hash_password1 |
      當 學生使用以下資料登入
        | email            | password      |
        | ming@example.com | wrong_password |
      那麼 操作失敗，錯誤訊息為「帳號或密碼錯誤」

    場景: Email 不存在
      當 學生使用以下資料登入
        | email                | password  |
        | notexist@example.com | password1 |
      那麼 操作失敗，錯誤訊息為「帳號或密碼錯誤」

  規則: 舊流程登入（老師Email→班級→學生→密碼）- 完全兼容

    場景: 未綁定Email的學生使用舊流程登入
      假設 個人教師「王老師」有班級「初級班」(ID: 50)
      並且 班級「初級班」包含學生如下
        | id  | name   | password_hash  | identity_id | password_migrated_to_identity |
        | 999 | 張小三 | hash_old_pw    | null        | false                         |
      當 學生透過舊流程登入，步驟如下
        | step | action                          | value               |
        | 1    | 輸入老師Email                   | wang@example.com    |
        | 2    | 選擇班級                        | 初級班              |
        | 3    | 選擇學生                        | 張小三 (ID: 999)    |
        | 4    | 輸入密碼                        | old_pw              |
      那麼 操作成功
      並且 登入的學生 ID 為 999
      並且 使用的密碼來源為 Student (ID: 999) 自己的 password_hash

    場景: 已整合身分的學生使用舊流程登入，必須使用統一密碼
      假設 系統中存在 StudentIdentity 資料如下
        | id | verified_email   | password_hash     |
        | 1  | ming@example.com | hash_unified_pw   |
      並且 個人教師「王老師」有班級「初級班」(ID: 50)
      並且 班級「初級班」包含學生如下
        | id  | name   | identity_id | password_migrated_to_identity | old_password_hash |
        | 101 | 王小明 | 1           | true                          | hash_old_pw_101   |
      當 學生透過舊流程登入，步驟如下
        | step | action                          | value               |
        | 1    | 輸入老師Email                   | wang@example.com    |
        | 2    | 選擇班級                        | 初級班              |
        | 3    | 選擇學生                        | 王小明 (ID: 101)    |
        | 4    | 輸入密碼                        | unified_pw          |
      那麼 操作成功
      並且 登入的學生 ID 為 101
      並且 使用的密碼來源為 StudentIdentity (ID: 1)

    場景: 已整合身分的學生使用舊流程登入，輸入舊密碼應失敗
      假設 系統中存在 StudentIdentity 資料如下
        | id | verified_email   | password_hash     |
        | 1  | ming@example.com | hash_unified_pw   |
      並且 個人教師「王老師」有班級「初級班」(ID: 50)
      並且 班級「初級班」包含學生如下
        | id  | name   | identity_id | password_migrated_to_identity | old_password_hash |
        | 101 | 王小明 | 1           | true                          | hash_old_pw_101   |
      當 學生透過舊流程登入，步驟如下
        | step | action                          | value               |
        | 1    | 輸入老師Email                   | wang@example.com    |
        | 2    | 選擇班級                        | 初級班              |
        | 3    | 選擇學生                        | 王小明 (ID: 101)    |
        | 4    | 輸入密碼                        | old_pw_101          |
      那麼 操作失敗，錯誤訊息為「帳號或密碼錯誤」
      並且 系統使用 StudentIdentity (ID: 1) 的密碼驗證（不使用舊密碼）

  規則: 直接使用 Student ID 登入（API 層面，向後兼容）

    場景: 已整合身分的學生使用 Student ID + 統一密碼登入
      假設 系統中存在 StudentIdentity 資料如下
        | id | verified_email   | password_hash  |
        | 1  | ming@example.com | hash_password1 |
      並且 學生資料如下
        | id  | name   | identity_id | password_migrated_to_identity |
        | 101 | 王小明 | 1           | true                          |
      當 學生使用以下資料登入（API: /api/auth/student/login）
        | student_id | password  |
        | 101        | password1 |
      那麼 操作成功
      並且 登入的學生 ID 為 101
      並且 使用的密碼來源為 StudentIdentity (ID: 1)

    場景: 已整合身分的學生使用 Student ID + 舊密碼登入應失敗
      假設 系統中存在 StudentIdentity 資料如下
        | id | verified_email   | password_hash     |
        | 1  | ming@example.com | hash_unified_pw   |
      並且 學生資料如下
        | id  | name   | identity_id | password_migrated_to_identity | old_password_hash |
        | 101 | 王小明 | 1           | true                          | hash_old_pw       |
      當 學生使用以下資料登入（API: /api/auth/student/login）
        | student_id | password |
        | 101        | old_pw   |
      那麼 操作失敗，錯誤訊息為「帳號或密碼錯誤」

  規則: 主帳號異常時的容錯處理

    場景: 主帳號被刪除，自動選擇第一個連結帳號
      假設 系統中存在 StudentIdentity 資料如下
        | id | verified_email   | primary_student_id | password_hash  |
        | 1  | ming@example.com | null               | hash_password1 |
      並且 StudentIdentity (ID: 1) 關聯學生帳號如下
        | id  | name   | is_primary_account |
        | 205 | 王小明 | false              |
        | 308 | 王小明 | false              |
      當 學生使用以下資料登入
        | email            | password  |
        | ming@example.com | password1 |
      那麼 操作成功
      並且 登入的學生 ID 為 205 或 308（第一個可用的連結帳號）
      並且 StudentIdentity (ID: 1) 的 primary_student_id 被更新為登入的學生 ID

    場景: StudentIdentity 已停用
      假設 系統中存在 StudentIdentity 資料如下
        | id | verified_email   | is_active | password_hash  |
        | 1  | ming@example.com | false     | hash_password1 |
      當 學生使用以下資料登入
        | email            | password  |
        | ming@example.com | password1 |
      那麼 操作失敗，錯誤訊息為「帳號已停用」
