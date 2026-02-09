# language: zh-TW

功能: Email 認證時自動整合學生身分
  作為系統
  當學生完成 Email 驗證時
  系統自動檢查並整合同一 Email 的多個學生帳號

  背景:
    假設 系統中存在機構「A補習班」
    並且 系統中存在學校「A補習班-1分校」隸屬於機構「A補習班」
    並且 系統中存在學校「A補習班-2分校」隸屬於機構「A補習班」
    並且 系統中存在機構「B補習班」
    並且 系統中存在學校「B補習班-1校」隸屬於機構「B補習班」
    並且 系統中存在個人教師「王老師」

  規則: 首次 Email 認證時創建新 StudentIdentity

    場景: 學生首次完成 Email 認證
      假設 學校「A補習班-1分校」中存在學生資料如下
        | id  | name   | email              | birthdate  | email_verified |
        | 101 | 王小明 | ming@example.com   | 2010-05-15 | false          |
      當 學生「王小明」(ID: 101) 完成 Email 驗證，驗證 token 為有效
      那麼 操作成功
      並且 系統中存在 StudentIdentity 資料如下
        | verified_email   | primary_student_id | password_changed |
        | ming@example.com | 101                | false            |
      並且 學生「王小明」(ID: 101) 的資料如下
        | email_verified | identity_id | is_primary_account | password_migrated_to_identity |
        | true           | (新建的)    | true               | true                          |

    場景: 首次認證時學生已修改過密碼
      假設 學校「A補習班-1分校」中存在學生資料如下
        | id  | name   | email              | birthdate  | email_verified | password_changed |
        | 102 | 李小華 | hua@example.com    | 2011-03-20 | false          | true             |
      當 學生「李小華」(ID: 102) 完成 Email 認證，驗證 token 為有效
      那麼 操作成功
      並且 系統中存在 StudentIdentity 資料如下
        | verified_email  | primary_student_id | password_changed |
        | hua@example.com | 102                | true             |

  規則: 相同 Email 認證時整合到既有 StudentIdentity

    場景: 第二個帳號完成 Email 認證，整合到既有身分
      假設 學校「A補習班-1分校」中存在學生資料如下
        | id  | name   | email              | birthdate  | email_verified | identity_id |
        | 101 | 王小明 | ming@example.com   | 2010-05-15 | true           | 1           |
      並且 系統中存在 StudentIdentity 資料如下
        | id | verified_email   | primary_student_id | password_changed |
        | 1  | ming@example.com | 101                | false            |
      並且 學校「A補習班-2分校」中存在學生資料如下
        | id  | name   | email              | birthdate  | email_verified |
        | 205 | 王小明 | ming@example.com   | 2010-05-15 | false          |
      當 學生「王小明」(ID: 205) 完成 Email 認證，驗證 token 為有效
      那麼 操作成功
      並且 學生「王小明」(ID: 205) 的資料如下
        | email_verified | identity_id | is_primary_account | password_migrated_to_identity |
        | true           | 1           | false              | true                          |
      並且 StudentIdentity (ID: 1) 關聯的學生帳號數為 2
      並且 StudentIdentity (ID: 1) 的 primary_student_id 為 101

    場景: 多個帳號整合，其中一個已修改密碼
      假設 學校「A補習班-1分校」中存在學生資料如下
        | id  | name   | email              | password_changed | email_verified | identity_id |
        | 101 | 王小明 | ming@example.com   | false            | true           | 1           |
      並且 系統中存在 StudentIdentity 資料如下
        | id | verified_email   | primary_student_id | password_changed |
        | 1  | ming@example.com | 101                | false            |
      並且 學校「B補習班-1校」中存在學生資料如下
        | id  | name   | email              | password_changed | email_verified |
        | 308 | 王小明 | ming@example.com   | true             | false          |
      當 學生「王小明」(ID: 308) 完成 Email 認證，驗證 token 為有效
      那麼 操作成功
      並且 StudentIdentity (ID: 1) 的 password_changed 為 true
      並且 學生「王小明」(ID: 308) 的 identity_id 為 1

  規則: 智能密碼選擇策略

    場景: 都是預設密碼時，保持 Identity 的密碼
      假設 系統中存在 StudentIdentity 資料如下
        | id | verified_email   | password_hash      | password_changed |
        | 1  | ming@example.com | hash_of_20100515   | false            |
      並且 StudentIdentity (ID: 1) 關聯學生 (ID: 101)
      並且 學生 (ID: 205) 的資料如下
        | email            | password_hash      | password_changed | email_verified |
        | ming@example.com | hash_of_20100515   | false            | false          |
      當 學生 (ID: 205) 完成 Email 認證，驗證 token 為有效
      那麼 操作成功
      並且 StudentIdentity (ID: 1) 的 password_hash 為 "hash_of_20100515"
      並且 StudentIdentity (ID: 1) 的 password_changed 為 false

    場景: Identity 是預設密碼，新學生有自定義密碼，採用新學生的密碼
      假設 系統中存在 StudentIdentity 資料如下
        | id | verified_email   | password_hash      | password_changed |
        | 1  | ming@example.com | hash_of_20100515   | false            |
      並且 StudentIdentity (ID: 1) 關聯學生 (ID: 101)
      並且 學生 (ID: 308) 的資料如下
        | email            | password_hash      | password_changed | email_verified |
        | ming@example.com | hash_custom_308    | true             | false          |
      當 學生 (ID: 308) 完成 Email 認證，驗證 token 為有效
      那麼 操作成功
      並且 StudentIdentity (ID: 1) 的 password_hash 為 "hash_custom_308"
      並且 StudentIdentity (ID: 1) 的 password_changed 為 true

    場景: Identity 有自定義密碼，新學生是預設密碼，保持 Identity 的密碼
      假設 系統中存在 StudentIdentity 資料如下
        | id | verified_email   | password_hash      | password_changed |
        | 1  | ming@example.com | hash_custom_101    | true             |
      並且 StudentIdentity (ID: 1) 關聯學生 (ID: 101)
      並且 學生 (ID: 205) 的資料如下
        | email            | password_hash      | password_changed | email_verified |
        | ming@example.com | hash_of_20100515   | false            | false          |
      當 學生 (ID: 205) 完成 Email 認證，驗證 token 為有效
      那麼 操作成功
      並且 StudentIdentity (ID: 1) 的 password_hash 為 "hash_custom_101"
      並且 StudentIdentity (ID: 1) 的 password_changed 為 true

  規則: 整合後資料保留驗證

    場景: 整合後各帳號的學習資料獨立保留
      假設 學生 (ID: 101) 在「A補習班-1分校」有 5 筆學習進度記錄
      並且 學生 (ID: 205) 在「A補習班-2分校」有 3 筆學習進度記錄
      並且 學生 (ID: 101) 已整合到 StudentIdentity (ID: 1)
      當 學生 (ID: 205) 完成 Email 認證並整合到 StudentIdentity (ID: 1)
      那麼 操作成功
      並且 學生 (ID: 101) 的學習進度記錄數仍為 5
      並且 學生 (ID: 205) 的學習進度記錄數仍為 3

    場景: 整合後各帳號的機構關係獨立保留
      假設 學生 (ID: 101) 關聯到「A補習班-1分校」
      並且 學生 (ID: 205) 關聯到「A補習班-2分校」
      並且 學生 (ID: 308) 關聯到「B補習班-1校」
      並且 學生 (ID: 101, 205, 308) 都整合到 StudentIdentity (ID: 1)
      那麼 學生 (ID: 101) 的關聯學校為「A補習班-1分校」
      並且 學生 (ID: 205) 的關聯學校為「A補習班-2分校」
      並且 學生 (ID: 308) 的關聯學校為「B補習班-1校」

  規則: Email 驗證失敗時不整合

    場景: 驗證 token 無效
      假設 學生 (ID: 101) 的資料如下
        | email              | email_verified |
        | ming@example.com   | false          |
      當 學生 (ID: 101) 嘗試 Email 認證，驗證 token 為「invalid_token」
      那麼 操作失敗
      並且 學生 (ID: 101) 的 email_verified 為 false
      並且 學生 (ID: 101) 的 identity_id 為 null

    場景: Email 已被其他學生驗證
      假設 學生 (ID: 101) 的 email 為 "ming@example.com" 且已完成驗證
      並且 學生 (ID: 101) 關聯到 StudentIdentity (ID: 1, verified_email: "ming@example.com")
      並且 學生 (ID: 999) 的資料如下
        | email              | email_verified |
        | ming@example.com   | false          |
      當 學生 (ID: 999) 完成 Email 認證，驗證 token 為有效
      那麼 操作成功
      並且 學生 (ID: 999) 關聯到 StudentIdentity (ID: 1)
