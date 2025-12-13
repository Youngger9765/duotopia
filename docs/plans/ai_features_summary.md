# Duotopia 現有 AI 自動生成功能總覽

> **建立日期**: 2025-11-10
> **用途**: 整理專案中現有的 AI 功能，作為新增例句功能的參考

---

## 📋 現有 AI 功能清單

### 1️⃣ **翻譯服務** (Translation Service)

**檔案位置**: `backend/services/translation.py`

**使用技術**: OpenAI GPT-3.5-turbo

**功能**:

#### **單一文本翻譯** (`translate_text`)
```python
async def translate_text(self, text: str, target_lang: str = "zh-TW") -> str
```

**支援語言**:
- `zh-TW` - 繁體中文翻譯
- `en` - 英文釋義（English definition）
- 其他語言（通用翻譯）

**Prompt 範例**:
```python
# 中文翻譯
prompt = f"請將以下英文翻譯成繁體中文，只回覆翻譯結果，不要加任何說明：\n{text}"

# 英文釋義
prompt = (
    f"Please provide a simple English definition or explanation for the following word or phrase. "
    f"Keep it concise (1-2 sentences) and suitable for language learners:\n{text}"
)
```

**API 設定**:
- Model: `gpt-3.5-turbo`
- Temperature: `0.3` (低隨機性，翻譯一致)
- Max Tokens: `100`

---

#### **批次翻譯** (`batch_translate`)
```python
async def batch_translate(self, texts: List[str], target_lang: str = "zh-TW") -> List[str]
```

**特點**:
- 使用 JSON 格式輸入/輸出，確保解析穩定
- 自動 fallback 機制（如果批次失敗，自動改用逐句翻譯）
- 支援大量文本翻譯（max_tokens: 1000）

**Prompt 範例**:
```python
texts_json = json.dumps(texts, ensure_ascii=False)

prompt = f"""請將以下 JSON 陣列中的英文翻譯成繁體中文。
直接返回 JSON 陣列格式，每個翻譯對應一個項目。
只返回 JSON 陣列，不要任何其他文字或說明。

輸入: {texts_json}

要求: 返回格式必須是 ["翻譯1", "翻譯2", ...]"""
```

---

#### **前端 API 調用**:
```typescript
// frontend/src/lib/api.ts

// 單一翻譯
async translateText(text: string, targetLang: string = "zh-TW") {
  return this.request("/api/teachers/translate", {
    method: "POST",
    body: JSON.stringify({ text, target_lang: targetLang }),
  });
}

// 批次翻譯
async batchTranslate(texts: string[], targetLang: string = "zh-TW") {
  return this.request("/api/teachers/translate/batch", {
    method: "POST",
    body: JSON.stringify({ texts, target_lang: targetLang }),
  });
}
```

---

#### **後端 API 端點**:
```python
# backend/routers/teachers.py

@router.post("/translate")
async def translate_text(
    request: TranslateRequest,
    current_teacher: Teacher = Depends(get_current_teacher)
):
    """翻譯單一文本"""
    translation = await translation_service.translate_text(
        request.text, request.target_lang
    )
    return {"original": request.text, "translation": translation}

@router.post("/translate/batch")
async def batch_translate(
    request: BatchTranslateRequest,
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """批次翻譯多個文本"""
    translations = await translation_service.batch_translate(
        request.texts, request.target_lang
    )
    return {"originals": request.texts, "translations": translations}
```

---

### 2️⃣ **TTS 服務** (Text-to-Speech)

**檔案位置**: `backend/services/tts.py`

**使用技術**: Microsoft Edge TTS（免費）

**功能**:

#### **生成 TTS 音檔** (`generate_tts`)
```python
async def generate_tts(
    text: str,
    voice: str = "en-US-JennyNeural",
    rate: str = "+0%",
    volume: str = "+0%"
) -> str  # 返回 audio_url
```

**支援選項**:
- **Voice** (語音):
  - `en-US-JennyNeural` (美國女聲)
  - `en-US-ChristopherNeural` (美國男聲)
  - `en-GB-RyanNeural` (英國男聲)
  - `en-GB-SoniaNeural` (英國女聲)
  - `en-AU-WilliamNeural` (澳洲男聲)
  - `en-AU-NatashaNeural` (澳洲女聲)
- **Rate** (語速):
  - `-25%` (慢速)
  - `+0%` (正常)
  - `+50%` (快速)

---

#### **批次生成 TTS** (`batch_generate_tts`)
```python
async def batch_generate_tts(
    texts: List[str],
    voice: str = "en-US-JennyNeural",
    rate: str = "+0%",
    volume: str = "+0%"
) -> List[str]  # 返回 audio_urls
```

---

#### **前端 API 調用**:
```typescript
// frontend/src/lib/api.ts

// 單一 TTS
async generateTTS(
  text: string,
  voice?: string,
  rate?: string,
  volume?: string
): Promise<{ audio_url: string }> {
  return this.request("/api/teachers/tts", {
    method: "POST",
    body: JSON.stringify({ text, voice, rate, volume }),
  });
}

// 批次 TTS
async batchGenerateTTS(
  texts: string[],
  voice?: string,
  rate?: string,
  volume?: string
) {
  return this.request("/api/teachers/tts/batch", {
    method: "POST",
    body: JSON.stringify({ texts, voice, rate, volume }),
  });
}
```

---

### 3️⃣ **AI 發音評估** (Speech Assessment)

**API 端點**: `POST /api/speech/assess`

**功能**:
- 評估學生錄音的發音準確度
- 提供逐字分析（word-level analysis）
- 提供音素級別分析（phoneme-level analysis）

**評分項目**:
- Accuracy Score (準確度)
- Fluency Score (流暢度)
- Pronunciation Score (發音分數)
- Completeness Score (完整度)

**使用場景**:
- 學生完成錄音後，點擊「取得 AI 評估」
- 前端上傳音檔 + 參考文字
- 後端返回 AI 評分結果

---

### 4️⃣ **Cron 任務中的 GPT-4o-mini**

**檔案位置**: `backend/routers/cron.py`

**使用技術**: OpenAI GPT-4o-mini

**用途**:
- 自動化任務（具體功能需進一步查看）
- 可能用於數據分析或自動化報告生成

---

## 🎯 如何應用到「例句」功能

### **Phase 1: 例句翻譯（立即可用）**

#### **方案 1: 直接使用現有翻譯服務** ✅ 推薦

```typescript
// 前端實作 (ReadingAssessmentPanel.tsx)

const handleGenerateExampleSentenceTranslation = async (index: number) => {
  const row = rows[index]

  if (!row.example_sentence) {
    toast.error("請先輸入例句")
    return
  }

  try {
    // 使用現有的翻譯 API
    const chineseTranslation = await apiClient.translateText(
      row.example_sentence,
      "zh-TW"
    )

    const englishDefinition = await apiClient.translateText(
      row.example_sentence,
      "en"
    )

    // 更新 row
    row.example_sentence_translation = chineseTranslation.translation
    row.example_sentence_definition = englishDefinition.translation

    toast.success("例句翻譯生成完成")
  } catch (error) {
    toast.error("翻譯失敗")
  }
}
```

---

#### **方案 2: 批次生成例句翻譯**

```typescript
const handleBatchGenerateExampleSentenceTranslations = async () => {
  // 收集所有有例句但沒有翻譯的項目
  const itemsNeedTranslation = rows.filter(
    row => row.example_sentence && !row.example_sentence_translation
  )

  if (itemsNeedTranslation.length === 0) {
    toast.info("沒有需要翻譯的例句")
    return
  }

  const exampleSentences = itemsNeedTranslation.map(row => row.example_sentence)

  try {
    // 批次翻譯
    const chineseResults = await apiClient.batchTranslate(exampleSentences, "zh-TW")
    const englishResults = await apiClient.batchTranslate(exampleSentences, "en")

    // 更新 rows
    itemsNeedTranslation.forEach((item, idx) => {
      item.example_sentence_translation = chineseResults.translations[idx]
      item.example_sentence_definition = englishResults.translations[idx]
    })

    toast.success(`成功生成 ${itemsNeedTranslation.length} 個例句翻譯`)
  } catch (error) {
    toast.error("批次翻譯失敗")
  }
}
```

---

### **Phase 2: AI 自動生成例句（需要新功能）**

#### **選項 1: 擴展現有翻譯服務** ✅ 推薦

**新增方法**: `backend/services/translation.py`

```python
async def generate_example_sentence(self, word: str, context: str = None) -> str:
    """
    根據單字自動生成例句

    Args:
        word: 單字
        context: 額外的上下文（選填）

    Returns:
        生成的例句
    """
    self._ensure_client()

    try:
        if context:
            prompt = f"""Please create a simple, natural example sentence using the word "{word}" in the context of {context}.
The sentence should be:
1. Suitable for English learners (A1-B1 level)
2. Clear and easy to understand
3. Natural and commonly used
4. Maximum 15 words

Only return the sentence, no explanation."""
        else:
            prompt = f"""Please create a simple, natural example sentence using the word "{word}".
The sentence should be:
1. Suitable for English learners (A1-B1 level)
2. Clear and easy to understand
3. Natural and commonly used
4. Maximum 15 words

Only return the sentence, no explanation."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an English teacher creating example sentences for learners."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # 稍高的隨機性以獲得更自然的句子
            max_tokens=50
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Generate example sentence error: {e}")
        return f"{word.capitalize()} is a word."  # Fallback
```

**批次生成版本**:

```python
async def batch_generate_example_sentences(
    self, words: List[str], context: str = None
) -> List[str]:
    """批次生成例句"""
    import asyncio

    tasks = [self.generate_example_sentence(word, context) for word in words]
    example_sentences = await asyncio.gather(*tasks)
    return example_sentences
```

---

#### **選項 2: 使用更強大的 GPT-4** (成本較高)

```python
# 在 translation.py 中新增
class ExampleSentenceGenerator:
    def __init__(self):
        self.client = None
        self.model = "gpt-4o-mini"  # 或 "gpt-4"

    # ... 實作類似上面的 generate_example_sentence
```

---

## 💡 實作建議

### **Phase 1 實作順序**:

1. ✅ **資料庫變更** (3個新欄位)
   ```sql
   ALTER TABLE content_items
   ADD COLUMN example_sentence TEXT NULL,
   ADD COLUMN example_sentence_translation TEXT NULL,
   ADD COLUMN example_sentence_definition TEXT NULL;
   ```

2. ✅ **後端 API 更新**
   - 更新 Pydantic Schema
   - 確保 CRUD 支援新欄位
   - 不需要新增 API（使用現有翻譯 API）

3. ✅ **前端 UI 更新**
   - 新增三個輸入框：例句、中文翻譯、英文釋義
   - 新增「生成翻譯」按鈕（使用現有 `translateText` API）
   - 新增「批次生成翻譯」按鈕（使用現有 `batchTranslate` API）

4. ✅ **測試**
   - 測試手動輸入例句
   - 測試自動生成翻譯
   - 測試批次操作

---

### **Phase 2 實作順序** (如果需要 AI 自動生成例句):

1. 在 `translation.py` 新增 `generate_example_sentence` 方法
2. 新增後端 API 端點：
   ```python
   @router.post("/generate-example-sentence")
   async def generate_example_sentence(request: GenerateExampleRequest):
       sentence = await translation_service.generate_example_sentence(
           request.word, request.context
       )
       return {"word": request.word, "example_sentence": sentence}
   ```
3. 前端新增「AI 生成例句」按鈕
4. 測試

---

## 📊 成本估算

| 功能 | 使用 API | 估算成本 |
|-----|---------|---------|
| 翻譯單字翻譯 | GPT-3.5-turbo | ~$0.0015/1000 tokens ≈ $0.000002/次 |
| 批次翻譯 (100個) | GPT-3.5-turbo | ~$0.0015/1000 tokens ≈ $0.0002/100次 |
| AI 生成例句 | GPT-3.5-turbo | ~$0.0015/1000 tokens ≈ $0.000003/次 |
| TTS 音檔生成 | Microsoft Edge TTS | 免費 |

**結論**: 使用現有的翻譯服務成本非常低，可以放心使用。

---

## 🔑 環境變數需求

**已設定** (在 `.env` 中):
```bash
OPENAI_API_KEY=sk-xxxxx
```

**不需要額外設定**，可以直接使用現有的翻譯服務！

---

## 📚 參考文件

- [OpenAI API 文件](https://platform.openai.com/docs/api-reference)
- [Microsoft Edge TTS](https://github.com/rany2/edge-tts)
- [GPT-3.5-turbo Pricing](https://openai.com/pricing)

---

**總結**:
- ✅ 專案已有完整的翻譯和 TTS 服務
- ✅ 可以直接使用現有 API，不需要重新實作
- ✅ 成本極低，可以放心使用
- 🔄 如果需要 AI 自動生成例句，可以擴展現有服務
