# 修復計劃：學生作業提交失敗問題 (OOM)

> **Issue**: 25 位學生同時做例句重組作業，5 位學生完成所有題目後作業沒有儲存，停留在最後一題。
> **建立日期**: 2026-01-09
> **狀態**: 規劃中

---

## 問題摘要

25 位學生同時做例句重組作業，5 位學生完成所有題目後作業沒有儲存，停留在最後一題。

### 根本原因

Cloud Run 容器因記憶體不足 (OOM) 被終止：

```
503 Error: "container instance was found to be using too much memory and was terminated"
```

- **觸發 API**: `/api/teachers/translate-with-pos/batch`（批次翻譯，13.8 秒延遲）
- 當容器被殺掉時，該容器上所有進行中的請求（包括 5 位學生的提交）都收到 503 錯誤。

---

## 修復計劃

### P0：架構改進（即時分數更新）

#### 0.1 每答一題即時更新總分

**現況問題**：
- 目前例句重組作業是在**全部完成後最後才把分數送出**到後端 update
- 如果學生停在最後一題，進度和分數都會丟失

**改進方案**：
- 學生每答一題就去更新總分
- 每題作答結果即時保存到後端

**分數計算範例**（10 題，總分 100）：
| 題號 | 單題得分 | 計算方式 | 累計總分 |
|------|----------|----------|----------|
| 1 | 100 | 100 ÷ 10 = 10 | 10 |
| 2 | 80 | 80 ÷ 10 = 8 | 18 |
| 3 | 90 | 90 ÷ 10 = 9 | 27 |
| ... | ... | ... | ... |

**好處**：
1. 學生重新進入作業頁面時可恢復已作答的題目和分數
2. 即使發生 OOM，已完成的題目分數不會丟失
3. 減少最後一次性提交的壓力

**需要修改的檔案**：
| 檔案路徑 | 修改說明 |
|----------|----------|
| `frontend/src/components/activities/RearrangementActivity.tsx` | 每題完成時呼叫更新分數 API |
| `frontend/src/pages/student/StudentActivityPage.tsx` | 處理即時分數更新邏輯 |
| `backend/routers/assignments.py` | 新增/修改即時更新分數的 API endpoint |
| `backend/models/assignment.py` | 確保支援部分進度儲存 |

---

### P1：緊急修復（防止數據丟失）

#### 1.1 前端提交增加重試機制

**檔案**: `frontend/src/pages/student/StudentActivityPage.tsx`

**修改內容**:
- 引入 `retryWithBackoff` 工具
- `handleSubmit` 失敗時自動重試 3 次（指數退避）
- 重試期間顯示 toast 提示
- 最終失敗時顯示錯誤訊息，不導航離開頁面

#### 1.2 正確等待 onSubmit 回調

**檔案**: `frontend/src/pages/student/StudentActivityPageContent.tsx`

**修改位置**: 第 1807-1808 行

```tsx
// 修改前
if (onSubmit) {
  onSubmit({ answers: [] });
}

// 修改後
if (onSubmit) {
  try {
    await onSubmit({ answers: [] });
  } catch (error) {
    console.error("Submission failed:", error);
    toast.error(t("submission.failed"));
  }
}
```

#### 1.3 單題完成 API 失敗時提示用戶

**檔案**: `frontend/src/components/activities/RearrangementActivity.tsx`

**修改位置**: 第 453-467 行

**修改內容**:
- 靜默失敗改為顯示警告 toast
- 記錄失敗的題目，完成時提示用戶「部分進度可能未儲存」

---

### P2：後端記憶體優化

#### 2.1 批次翻譯改為分塊處理

**檔案**: `backend/services/translation.py`

**修改內容**:
- `batch_translate_with_pos()` 分塊處理（每次 10 個詞）
- 分塊間加入短暫延遲允許記憶體釋放
- 避免大批次導致 OOM

#### 2.2 增加 Cloud Run 記憶體

**檔案**: `.github/workflows/deploy-backend.yml`

**修改內容**:
- staging/develop 環境記憶體從 256Mi 增加到 512Mi

#### 2.3 限制批次大小

**檔案**: `backend/routers/teachers.py`

**修改內容**:
- `/translate-with-pos/batch` API 增加批次大小上限（50 個詞）
- 超過限制返回 400 錯誤

---

### P3：長期改進（可選）

#### 3.1 本地狀態持久化

- 將答題進度存入 localStorage
- 頁面刷新或崩潰後可恢復

#### 3.2 背景同步機制

- 失敗的 API 呼叫排隊
- 網路恢復時自動重試

---

## 關鍵檔案清單

| 優先級 | 檔案路徑 | 修改說明 |
|--------|----------|----------|
| P0 | `frontend/src/components/activities/RearrangementActivity.tsx` | 每題完成即時更新分數 |
| P0 | `frontend/src/pages/student/StudentActivityPage.tsx` | 即時分數更新邏輯 |
| P0 | `backend/routers/assignments.py` | 即時更新分數 API |
| P1 | `frontend/src/pages/student/StudentActivityPage.tsx` | 增加重試邏輯 |
| P1 | `frontend/src/pages/student/StudentActivityPageContent.tsx` | await onSubmit |
| P1 | `frontend/src/components/activities/RearrangementActivity.tsx` | 錯誤提示 |
| P2 | `backend/services/translation.py` | 分塊批次處理 |
| P2 | `.github/workflows/deploy-backend.yml` | 增加記憶體 |
| P2 | `backend/routers/teachers.py` | 限制批次大小 |

---

## 實施順序

```
Phase 1 - 立即（防止未來數據丟失 + 即時更新）
├── P0.1 每答一題即時更新總分（架構改進）
├── P1.1 前端重試機制
└── P1.2 await onSubmit 修復

Phase 2 - 短期（減少 OOM 機率）
└── P2.2 增加 Cloud Run 記憶體到 512Mi

Phase 3 - 中期（根本解決記憶體問題）
├── P2.1 批次翻譯分塊處理
└── P2.3 限制批次大小

Phase 4 - 長期（增加系統韌性）
├── P3.1 本地狀態持久化
└── P3.2 背景同步機制
```

---

## 測試驗收標準

### P0 驗收
- [ ] 學生答完第 1 題後，後端 score 欄位已更新
- [ ] 學生中途離開作業頁面，重新進入後能看到已作答的題目和累計分數
- [ ] 模擬 OOM 場景（殺掉容器），確認已完成題目的分數不丟失

### P1 驗收
- [ ] 模擬網路中斷，確認自動重試 3 次
- [ ] 重試成功時顯示成功 toast
- [ ] 最終失敗時停留在當前頁面並顯示錯誤提示

### P2 驗收
- [ ] 大批次翻譯（100+ 詞）不會觸發 OOM
- [ ] 超過 50 個詞的批次請求返回 400 錯誤
- [ ] Cloud Run 記憶體監控顯示穩定在 512Mi 以下

---

## 相關文件

- [LOAD_TESTING_ANALYSIS.md](../LOAD_TESTING_ANALYSIS.md) - 負載測試分析
- [DEPLOYMENT.md](../DEPLOYMENT.md) - 部署說明
