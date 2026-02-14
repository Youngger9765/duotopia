# 批次匯入執行指南

## 概述

本文件說明如何在正式環境執行批次匯入腳本，將 CSV 資料匯入到 Duotopia 系統。

## 執行方式

### 方式一：在 VM 上執行（推薦）

由於正式環境的 nginx 有 CORS 限制，只允許來自 `duotopia.co` 域名的請求，**建議直接在 VM 上執行腳本**。

#### 步驟：

1. **將檔案上傳到 VM**

```bash
# 在本地機器上，將腳本和 CSV 上傳到 VM
scp scripts/import_vocabulary_from_csv.py user@duotopia.co:/tmp/
scp examples/114-2_翰林佳音_第八冊_Unit1_What_Do_You_Do_in_Your_Free_Time.csv user@duotopia.co:/tmp/
```

2. **SSH 連線到 VM**

```bash
ssh user@duotopia.co
```

3. **確認執行模式設定為 "vm"**

```bash
cd /tmp
nano import_vocabulary_from_csv.py

# 確認這行：
# EXECUTION_MODE = "vm"  # 在 VM 上執行
```

4. **執行腳本**

```bash
python import_vocabulary_from_csv.py "114-2_翰林佳音_第八冊_Unit1_What_Do_You_Do_in_Your_Free_Time.csv"
```

5. **輸入密碼**
   腳本會提示輸入 `contact@duotopia.co` 的密碼

6. **等待執行完成**
   腳本會顯示進度並在完成後顯示統計資訊。

---

### 方式二：從外部執行（不建議）

如果必須從本地機器執行，需要先修改 nginx 配置允許外部訪問。

#### 修改 nginx 配置：

1. 修改 `deployment/vm/nginx.conf` 中的 CORS 設定：

```nginx
# 原本（只允許 duotopia.co）
set $cors_origin "";
if ($http_origin ~* "^https://(www\.)?duotopia\.co$") {
    set $cors_origin $http_origin;
}

# 改為（允許所有來源 - 僅測試用）
set $cors_origin "*";
```

2. 重新載入 nginx：

```bash
docker exec duotopia-nginx-1 nginx -s reload
```

3. 修改腳本執行模式：

```python
EXECUTION_MODE = "external"  # 從外部執行
```

4. 執行腳本：

```bash
python scripts\import_vocabulary_from_csv.py "examples\114-2_翰林佳音_第八冊_Unit1_What_Do_You_Do_in_Your_Free_Time.csv"
```

5. **完成後立即還原 nginx 配置並重新載入**

⚠️ **警告**：方式二會暫時開放 API 給外部訪問，有安全風險，僅供測試使用。

---

## 腳本運作邏輯

### 1. 登入驗證

- 使用教師帳號登入取得 access token
- 支援兩種執行模式：
  - **vm 模式**：連接 `http://localhost:8080/api`（內部）
  - **external 模式**：連接 `https://duotopia.co/api`（外部）

### 2. 課程與單元處理

- **課程（Program）**：依 CSV 的 `course_name` 查找
  - 找到：使用既有課程
  - 找不到：創建新課程
- **單元（Lesson）**：依 CSV 的 `unit_name` 查找
  - 找到：使用既有單元（不創建新的）
  - 找不到：創建新單元

### 3. 內容集創建

- **單字集（Content）**：依 CSV 的 `content_title` 創建
  - 即使名稱相同，也會創建新的內容集
  - 這樣可以避免意外覆蓋既有資料

### 4. 單字項目（ContentItem）

- 每一筆 CSV 記錄轉換為一個單字項目
- 包含：text, translation, part_of_speech, example_sentence, example_sentence_translation
- 自動設定 level 和 tags

## CSV 檔案格式

必要欄位：

- `course_name`: 課程名稱（如：114-2 翰林佳音 第八冊）
- `unit_name`: 單元名稱（如：Unit 1 What Do You Do in Your Free Time?）
- `content_title`: 內容集標題（如：Warm up Words）
- `text`: 單字本文（如：play basketball）
- `translation`: 中文翻譯（如：打籃球）
- `part_of_speech`: 詞性（verb/noun/adjective/adverb/phrase/other）
- `level`: 程度（A1/A2/B1/B2/C1/C2）
- `tags`: 標籤（以逗號分隔，如：free time, hobbies）

選填欄位：

- `example_sentence`: 例句
- `example_sentence_translation`: 例句翻譯

## 執行結果

成功執行後會顯示：

```
✅ 匯入完成
📊 統計資訊:
  - 共創建 1 個課程
  - 共創建 1 個單元
  - 共創建 5 個單字集
  - 共創建 52 個單字項目
```

## 注意事項

1. **密碼安全**：腳本使用 `getpass` 模組安全地輸入密碼，不會在終端顯示或儲存在程式碼中
2. **CORS 限制**：正式環境有 CORS 保護，建議在 VM 上執行
3. **重複名稱**：即使課程/單元/內容集名稱相同，也會創建新的（避免覆蓋）
4. **錯誤處理**：如果執行失敗，檢查：
   - API 連線是否正常
   - 密碼是否正確
   - CSV 格式是否正確
   - 執行模式設定是否正確

## 故障排除

### 405 Not Allowed

- **原因**：外部執行時被 nginx CORS 限制阻擋
- **解決**：切換到 VM 執行模式

### 401 Unauthorized

- **原因**：密碼錯誤或 token 過期
- **解決**：確認密碼正確

### CSV 編碼問題

- **原因**：CSV 檔案未使用 UTF-8 BOM 編碼
- **解決**：使用 Excel 另存為 "CSV UTF-8 (逗號分隔) (\*.csv)"

### 找不到課程/單元

- **檢查**：CSV 中的 `course_name` 和 `unit_name` 是否與系統中完全一致
- **解決**：腳本會自動創建不存在的課程/單元
