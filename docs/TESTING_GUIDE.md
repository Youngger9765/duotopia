# 📚 Duotopia 測試指南

## 🌐 測試環境
- **前端**: https://duotopia-staging-frontend-qchnzlfpda-de.a.run.app
- **後端 API**: https://duotopia-staging-backend-qchnzlfpda-de.a.run.app
- **API 文件**: https://duotopia-staging-backend-qchnzlfpda-de.a.run.app/docs

## 👨‍🏫 教師端測試

### 1. 教師登入
1. 前往: https://duotopia-staging-frontend-qchnzlfpda-de.a.run.app/teacher/login
2. 輸入帳號:
   - Email: `demo@duotopia.com`
   - 密碼: `demo123`
3. 登入成功後會跳轉到 Dashboard

### 2. 班級管理測試

#### 檢視班級列表
1. 登入後前往 Dashboard
2. 應該看到 2 個班級:
   - **五年級A班** (ID: 1)
   - **六年級B班** (ID: 2)

#### 進入班級詳情 (以五年級A班為例)
1. 點擊「五年級A班」或前往: `/teacher/classroom/1`
2. 頁面應顯示:
   - 班級名稱和描述
   - 學生列表
   - 課程列表

### 3. 學生管理測試

#### 班級 1 (五年級A班) 的學生
| 學生姓名 | 登入密碼 | 測試重點 |
|---------|---------|----------|
| 王小明 | mynewpassword123 | 已更改密碼的學生 |
| 李小美 | 20120101 | 使用預設密碼 |
| 陳大雄 | student456 | 已更改密碼的學生 |

#### 班級 2 (六年級B班) 的學生
| 學生姓名 | 登入密碼 | 測試重點 |
|---------|---------|----------|
| 張志豪 | 20120101 | 使用預設密碼 |
| 林靜香 | password789 | 已更改密碼的學生 |

#### 測試項目
- [ ] 檢視學生列表
- [ ] 新增學生
- [ ] 編輯學生資料
- [ ] 刪除學生
- [ ] 批量匯入學生 (CSV/Excel)

### 4. 課程管理測試

#### 班級 1 的課程
1. **基礎英語發音** (3個單元)
   - Unit 1: Vowels
   - Unit 2: Consonants
   - Unit 3: Blends
2. **日常會話** (3個單元)
   - Unit 1: Greetings
   - Unit 2: Shopping
   - Unit 3: Restaurant

#### 班級 2 的課程
1. **進階文法** (3個單元)
   - Unit 1: Tenses
   - Unit 2: Conditionals
   - Unit 3: Passive Voice
2. **英語寫作** (3個單元)
   - Unit 1: Paragraphs
   - Unit 2: Essays
   - Unit 3: Reports

#### 測試項目
- [ ] 檢視課程列表
- [ ] 建立新課程
- [ ] 編輯課程內容
- [ ] 新增課程單元
- [ ] 拖拽排序課程和單元
- [ ] 派發作業

### 5. 作業管理測試
1. 選擇課程單元
2. 設定作業參數:
   - 截止日期
   - 重複次數
   - 是否允許重做
3. 派發給全班或特定學生
4. 檢視作業完成狀態
5. 批改作業並給予回饋

## 👨‍🎓 學生端測試

### 1. 學生登入流程
1. 前往: https://duotopia-staging-frontend-qchnzlfpda-de.a.run.app/student/login
2. **步驟 1**: 選擇教師
   - 選擇「Demo 老師」或輸入 `demo@duotopia.com`
3. **步驟 2**: 選擇班級
   - 五年級A班 或 六年級B班
4. **步驟 3**: 選擇學生
   - 從下拉選單選擇學生姓名
5. **步驟 4**: 輸入密碼
   - 使用上表中對應的密碼

### 2. 學生功能測試

#### 作業列表
- 檢視待完成作業
- 檢視已完成作業
- 檢視作業詳情

#### 活動類型測試
1. **朗讀評測** (reading_assessment)
   - 錄音朗讀文章
   - AI 評分反饋
   
2. **口說練習** (speaking_practice)
   - 自由口說練習
   - 即時反饋
   
3. **情境對話** (speaking_scenario)
   - 角色扮演對話
   - 互動式練習
   
4. **聽力填空** (listening_cloze)
   - 聽音頻填空
   - 自動評分
   
5. **造句練習** (sentence_making)
   - 使用關鍵字造句
   - 文法檢查
   
6. **口說測驗** (speaking_quiz)
   - 限時口說測驗
   - 綜合評分

### 3. 學習進度測試
- 查看個人學習統計
- 查看作業完成率
- 查看成績趨勢圖

## 🔧 API 測試

### 使用 cURL 測試

#### 1. 教師登入
```bash
curl -X POST https://duotopia-staging-backend-qchnzlfpda-de.a.run.app/api/auth/teacher/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@duotopia.com","password":"demo123"}'
```

#### 2. 取得班級列表
```bash
TOKEN="YOUR_JWT_TOKEN"
curl https://duotopia-staging-backend-qchnzlfpda-de.a.run.app/api/teachers/classrooms \
  -H "Authorization: Bearer $TOKEN"
```

#### 3. 取得班級詳情
```bash
curl https://duotopia-staging-backend-qchnzlfpda-de.a.run.app/api/teachers/classrooms/1 \
  -H "Authorization: Bearer $TOKEN"
```

### 使用 Python 測試腳本

```python
import requests

# 1. 登入
login_response = requests.post(
    "https://duotopia-staging-backend-qchnzlfpda-de.a.run.app/api/auth/teacher/login",
    json={"email": "demo@duotopia.com", "password": "demo123"}
)
token = login_response.json()["access_token"]

# 2. 取得班級資訊
headers = {"Authorization": f"Bearer {token}"}
classrooms = requests.get(
    "https://duotopia-staging-backend-qchnzlfpda-de.a.run.app/api/teachers/classrooms",
    headers=headers
)
print(classrooms.json())
```

## 📝 測試檢查清單

### 基本功能
- [ ] 教師登入/登出
- [ ] 學生多步驟登入
- [ ] Dashboard 載入
- [ ] 班級列表顯示
- [ ] 學生列表顯示
- [ ] 課程列表顯示

### 進階功能
- [ ] 拖拽排序（課程/單元）
- [ ] 批量操作（學生/作業）
- [ ] 檔案上傳（CSV/Excel）
- [ ] 即時更新（WebSocket）
- [ ] 多語言切換

### 效能測試
- [ ] 頁面載入時間 < 3秒
- [ ] API 回應時間 < 1秒
- [ ] 大量資料顯示（100+ 學生）
- [ ] 並發使用者測試

### 錯誤處理
- [ ] 網路斷線處理
- [ ] Token 過期處理
- [ ] 404 頁面
- [ ] 錯誤訊息顯示

## 🐛 常見問題

### 1. 401 Unauthorized 錯誤
- **原因**: Token 過期或未登入
- **解決**: 重新登入

### 2. 拖拽功能不工作
- **原因**: 瀏覽器不支援或 JavaScript 錯誤
- **解決**: 使用現代瀏覽器（Chrome/Firefox/Safari）

### 3. 學生無法登入
- **原因**: 密碼錯誤或帳號不存在
- **解決**: 確認使用正確的密碼（見上表）

### 4. 資料未更新
- **原因**: 快取問題
- **解決**: 強制重新整理（Ctrl+F5）

## 📊 測試資料總覽

| 項目 | 數量 | 說明 |
|-----|------|------|
| 教師 | 1 | demo@duotopia.com |
| 班級 | 2 | 五年級A班、六年級B班 |
| 學生 | 5 | 分布在 2 個班級 |
| 課程 | 4 | 每班 2 個課程 |
| 單元 | 12 | 每課程 3 個單元 |
| 作業 | 5 | 已派發給學生 |

## 🚀 自動化測試

### E2E 測試腳本位置
```bash
tests/e2e/
├── teacher_login.spec.js
├── student_login.spec.js
├── classroom_management.spec.js
└── assignment_workflow.spec.js
```

### 執行測試
```bash
# 安裝 Playwright
npm install -D @playwright/test

# 執行所有測試
npx playwright test

# 執行特定測試
npx playwright test teacher_login.spec.js

# 顯示測試報告
npx playwright show-report
```

---
最後更新：2025-08-29