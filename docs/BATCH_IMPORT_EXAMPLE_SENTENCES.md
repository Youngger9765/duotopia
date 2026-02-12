# 例句集批次匯入說明文件

## 📋 CSV 欄位說明

| 欄位名稱                       | 必填 | 說明                     | 範例                   |
| ------------------------------ | ---- | ------------------------ | ---------------------- |
| `course_name`                  | ✅   | 課程名稱                 | 我的英文課程           |
| `unit_name`                    | ✅   | 單元名稱                 | Unit 1: Greetings      |
| `content_title`                | ✅   | 例句集標題               | 打招呼例句集           |
| `level`                        | ✅   | 等級                     | A1, A2, B1, B2, C1, C2 |
| `tags`                         | ❌   | 標籤（逗號分隔）         | greeting,daily         |
| `text`                         | ✅   | 例句（英文）             | Hello! How are you?    |
| `translation`                  | ✅   | 例句翻譯（中文）         | 你好！你好嗎？         |
| `example_sentence`             | ❌   | 範例使用情境（英文）     | I said hello to friend |
| `example_sentence_translation` | ❌   | 範例使用情境翻譯（中文） | 我跟朋友打招呼         |

## ⚠️ 重要規則

### 句子長度限制

- **最少**: 2 個英文單字
- **最多**: 25 個英文單字
- 不符合長度規則的例句將無法匯入

### 匯入邏輯

- 相同的 `course_name` + `unit_name` + `content_title` 組合會被視為同一個例句集
- 每一行代表一個例句項目
- 系統會自動計算單字數量和允許的錯誤次數

## 📝 範例資料

```csv
course_name,unit_name,content_title,level,tags,text,translation,example_sentence,example_sentence_translation
我的英文課程,Unit 1: Greetings,打招呼例句集,A1,"greeting,daily",Hello! How are you?,你好！你好嗎？,I said hello to my friend.,我跟我的朋友打招呼。
我的英文課程,Unit 1: Greetings,打招呼例句集,A1,"greeting,daily",Good morning!,早安！,Every morning I say good morning to my teacher.,每天早上我都會跟老師說早安。
```

## 🔧 使用流程

1. **下載範本**: 使用 `example_sentences_batch_import_template.csv` 作為起點
2. **填寫資料**: 使用 Excel 或 Google Sheets 編輯
3. **儲存 UTF-8**: 確保檔案以 UTF-8 編碼儲存（避免中文亂碼）
4. **上傳匯入**: 透過系統介面上傳 CSV 檔案

## 💡 提示

- **Excel 用戶**: 儲存時選擇「CSV UTF-8 (逗號分隔) (\*.csv)」
- **Google Sheets 用戶**: 下載時選擇「逗號分隔值 (.csv)」
- 標籤可以不填，但如果填寫請用英文逗號分隔，不要有空格

## ❌ 常見錯誤

1. **句子太短**: "Hi." → 只有 1 個字，需要至少 2 個字
2. **句子太長**: 超過 25 個英文單字
3. **編碼錯誤**: 中文顯示亂碼 → 使用 UTF-8 編碼儲存
4. **格式錯誤**: 欄位中包含未轉義的逗號或換行符號
