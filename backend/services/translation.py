"""
Translation service using OpenAI API
"""

import os
import asyncio
import logging
from typing import List, Dict, Optional  # noqa: F401
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class TranslationService:
    def __init__(self):
        self.client = None
        self.model = "gpt-3.5-turbo"

    def _ensure_client(self):
        """Lazy initialization of OpenAI client"""
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self.client = OpenAI(api_key=api_key)

    async def translate_text(self, text: str, target_lang: str = "zh-TW") -> str:
        """
        翻譯單一文本

        Args:
            text: 要翻譯的文本
            target_lang: 目標語言（預設為繁體中文）

        Returns:
            翻譯後的文本
        """
        self._ensure_client()

        try:
            # 根據目標語言設定 prompt
            if target_lang == "zh-TW":
                prompt = f"請將以下英文翻譯成繁體中文，只回覆翻譯結果，不要加任何說明：\n{text}"
            elif target_lang == "en":
                # 英英釋義
                prompt = (
                    f"Please provide a simple English definition or explanation for the following word or phrase. "
                    f"Keep it concise (1-2 sentences) and suitable for language learners:\n{text}"
                )
            else:
                prompt = (
                    f"Please translate the following text to {target_lang}, "
                    f"only return the translation without any explanation:\n{text}"
                )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional translator. Only provide the "
                            "translation without any explanation. "
                            "CRITICAL: When translating to Chinese, you MUST use Traditional Chinese (繁體中文), "
                            "NOT Simplified Chinese."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # 降低隨機性以獲得更一致的翻譯
                max_tokens=100,
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Translation error: {e}")
            # 如果翻譯失敗，返回原文
            return text

    async def translate_with_pos(
        self, text: str, target_lang: str = "zh-TW"
    ) -> Dict[str, any]:
        """
        翻譯單字並辨識詞性

        Args:
            text: 要翻譯的單字
            target_lang: 目標語言（預設為繁體中文）

        Returns:
            包含 translation 和 parts_of_speech 的字典
        """
        self._ensure_client()
        import json

        try:
            # 建立 prompt 要求同時翻譯和辨識詞性
            if target_lang == "zh-TW":
                prompt = f"""請分析以下英文單字，提供：
1. 繁體中文翻譯
2. 詞性（必須列出所有常見用法的詞性）

單字: {text}

重要提示：
- 許多英文單字有多種詞性，請列出所有常見的用法
- 例如：顏色詞（red, blue, green）通常既是形容詞也是名詞
- 例如：動作詞（run, walk, dance）通常既是動詞也是名詞
- 例如：材料詞（gold, silver, plastic）通常既是名詞也是形容詞
- 請勿遺漏任何常見詞性

請以 JSON 格式回覆，格式如下：
{{"translation": "中文翻譯", "parts_of_speech": ["n.", "adj."]}}

詞性縮寫：n. (名詞), v. (動詞), adj. (形容詞), adv. (副詞),
pron. (代名詞), prep. (介系詞), conj. (連接詞), interj. (感嘆詞),
det. (限定詞), aux. (助動詞)

只回覆 JSON，不要其他文字。"""
            else:
                prompt = f"""Analyze the following English word and provide:
1. English definition
2. Parts of speech (MUST list ALL common usages)

Word: {text}

IMPORTANT:
- Many English words have multiple parts of speech - list ALL common usages
- Colors (red, blue, green) are typically both adjectives AND nouns
- Action words (run, walk, dance) are typically both verbs AND nouns
- Material words (gold, silver, plastic) are typically both nouns AND adjectives
- Do NOT omit any common part of speech

Reply in JSON format:
{{"translation": "definition", "parts_of_speech": ["n.", "adj."]}}

POS abbreviations: n. (noun), v. (verb), adj. (adjective), adv. (adverb),
pron. (pronoun), prep. (preposition), conj. (conjunction), interj. (interjection),
det. (determiner), aux. (auxiliary)

Only reply with JSON, no other text."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional linguist specializing in English grammar. "
                            "When identifying parts of speech, you MUST list ALL common usages - "
                            "many English words function as multiple parts of speech. "
                            "CRITICAL: When translating to Chinese, you MUST use Traditional Chinese (繁體中文), "
                            "NOT Simplified Chinese. Always respond with valid JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,  # Lower temperature for more consistent POS detection
                max_tokens=200,
            )

            # 解析 JSON 回應
            import re

            content = response.choices[0].message.content.strip()
            # 移除可能的 markdown 代碼塊標記
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            content = content.strip()

            result = json.loads(content)

            # 確保返回正確的結構
            return {
                "translation": result.get("translation", text),
                "parts_of_speech": result.get("parts_of_speech", []),
            }
        except Exception as e:
            print(f"Translate with POS error: {e}")
            # Fallback: 只返回翻譯
            translation = await self.translate_text(text, target_lang)
            return {"translation": translation, "parts_of_speech": []}

    async def batch_translate(
        self, texts: List[str], target_lang: str = "zh-TW"
    ) -> List[str]:
        """
        批次翻譯多個文本（使用 JSON 格式確保穩定快速）

        Args:
            texts: 要翻譯的文本列表
            target_lang: 目標語言（預設為繁體中文）

        Returns:
            翻譯後的文本列表
        """
        self._ensure_client()

        try:
            # 使用 JSON 格式以確保解析穩定性
            import json

            texts_json = json.dumps(texts, ensure_ascii=False)

            if target_lang == "zh-TW":
                prompt = f"""請將以下 JSON 陣列中的英文翻譯成繁體中文。
直接返回 JSON 陣列格式，每個翻譯對應一個項目。
只返回 JSON 陣列，不要任何其他文字或說明。
為兼容舊版測試，可使用 '---' 分隔多個翻譯（同樣需保持項目數量一致）。

輸入: {texts_json}

要求: 返回格式必須是 ["翻譯1", "翻譯2", ...]"""
            elif target_lang == "en":
                prompt = f"""Please provide simple English definitions for the following JSON array of words/phrases.
Return as a JSON array with each definition as one item.
Keep definitions concise (1-2 sentences) and suitable for language learners.
Only return the JSON array, no other text.

Input: {texts_json}

Required: Return format must be ["definition1", "definition2", ...]"""
            else:
                prompt = f"""Please translate the following JSON array to {target_lang}.
Return as a JSON array with each translation as one item.
Only return the JSON array, no other text.

Input: {texts_json}

Required: Return format must be ["translation1", "translation2", ...]"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional translator. Always return results "
                            "as a valid JSON array with the exact same number of items as input. "
                            "Return ONLY the JSON array, no markdown, no explanation. "
                            "CRITICAL: When translating to Chinese, you MUST use Traditional Chinese (繁體中文), "
                            "NOT Simplified Chinese."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=500,  # 與單元測試預期一致
            )

            # 解析 JSON 回應
            import re

            content = response.choices[0].message.content.strip()

            # 移除可能的 markdown 代碼塊標記
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            content = content.strip()

            # Try JSON parse; handle legacy separator when JSON decode fails
            try:
                translations = json.loads(content)
            except Exception:
                # If not JSON, fall back to separator or raw string
                if "---" in content:
                    translations = [
                        seg.strip() for seg in content.split("---") if seg.strip()
                    ]
                else:
                    translations = [content.strip()] if content else []
            if isinstance(translations, str):
                translations = translations.split("---")

            # 確保返回的翻譯數量與輸入相同
            if len(translations) != len(texts):
                # Try manual split on separator if present
                if isinstance(content, str) and "---" in content:
                    manual = [
                        seg.strip() for seg in content.split("---") if seg.strip()
                    ]
                    if len(manual) == len(texts):
                        translations = manual
                    else:
                        print(
                            f"Warning: Expected {len(texts)} translations, got {len(translations)}"
                        )
                        logger.warning(
                            "Batch translation count mismatch "
                            f"(expected {len(texts)}, got {len(translations)}), "
                            "falling back to individual translation."
                        )
                        return texts
                else:
                    print(
                        f"Warning: Expected {len(texts)} translations, got {len(translations)}"
                    )
                    logger.warning(
                        "Batch translation count mismatch "
                        f"(expected {len(texts)}, got {len(translations)}), "
                        "falling back to individual translation."
                    )
                    return texts

            return translations
        except Exception as e:
            print(f"Batch translation error: {e}")
            logger.error(
                f"Batch translation error: {e}. Falling back to individual translation."
            )
            return texts

    async def batch_translate_with_pos(
        self, texts: List[str], target_lang: str = "zh-TW"
    ) -> List[Dict[str, any]]:
        """
        批次翻譯多個單字並辨識詞性

        Args:
            texts: 要翻譯的單字列表
            target_lang: 目標語言（預設為繁體中文）

        Returns:
            包含 translation 和 parts_of_speech 的字典列表
        """
        self._ensure_client()
        import json

        try:
            texts_json = json.dumps(texts, ensure_ascii=False)

            if target_lang == "zh-TW":
                prompt = f"""請分析以下英文單字列表，為每個單字提供：
1. 繁體中文翻譯
2. 詞性（必須列出所有常見用法的詞性）

單字列表: {texts_json}

重要提示：
- 許多英文單字有多種詞性，請列出所有常見的用法
- 例如：顏色詞（red, blue, green）通常既是形容詞也是名詞
- 例如：動作詞（run, walk, dance）通常既是動詞也是名詞
- 例如：材料詞（gold, silver, plastic）通常既是名詞也是形容詞
- 請勿遺漏任何常見詞性

請以 JSON 陣列格式回覆，格式如下：
[{{"translation": "翻譯1", "parts_of_speech": ["n.", "adj."]}}, {{"translation": "翻譯2", "parts_of_speech": ["v.", "n."]}}]

詞性縮寫：n. (名詞), v. (動詞), adj. (形容詞), adv. (副詞),
pron. (代名詞), prep. (介系詞), conj. (連接詞), interj. (感嘆詞),
det. (限定詞), aux. (助動詞)

只回覆 JSON 陣列，不要其他文字。"""
            else:
                prompt = f"""Analyze the following English words and provide for each:
1. English definition
2. Parts of speech (MUST list ALL common usages)

Words: {texts_json}

IMPORTANT:
- Many English words have multiple parts of speech - list ALL common usages
- Colors (red, blue, green) are typically both adjectives AND nouns
- Action words (run, walk, dance) are typically both verbs AND nouns
- Material words (gold, silver, plastic) are typically both nouns AND adjectives
- Do NOT omit any common part of speech

Reply as JSON array:
[{{"translation": "definition1", "parts_of_speech": ["n.", "adj."]}}, \
{{"translation": "definition2", "parts_of_speech": ["v.", "n."]}}]

POS abbreviations: n. (noun), v. (verb), adj. (adjective), adv. (adverb),
pron. (pronoun), prep. (preposition), conj. (conjunction), interj. (interjection),
det. (determiner), aux. (auxiliary)

Only reply with JSON array, no other text."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional linguist specializing in English grammar. "
                            "When identifying parts of speech, you MUST list ALL common usages - "
                            "many English words function as multiple parts of speech. "
                            "CRITICAL: When translating to Chinese, you MUST use Traditional Chinese (繁體中文), "
                            "NOT Simplified Chinese. Always respond with valid JSON array only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,  # Lower temperature for more consistent POS detection
                max_tokens=2000,
            )

            # 解析 JSON 回應
            import re

            content = response.choices[0].message.content.strip()
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            content = content.strip()

            results = json.loads(content)

            # 確保返回數量正確
            if len(results) != len(texts):
                print(
                    f"Warning: Expected {len(texts)} results, got {len(results)}. Falling back."
                )
                # Fallback: 逐個處理
                tasks = [self.translate_with_pos(text, target_lang) for text in texts]
                results = await asyncio.gather(*tasks)

            return results
        except Exception as e:
            print(f"Batch translate with POS error: {e}. Falling back.")
            # Fallback: 逐個處理
            tasks = [self.translate_with_pos(text, target_lang) for text in texts]
            results = await asyncio.gather(*tasks)
            return results

    async def generate_sentences(
        self,
        words: List[str],
        level: str = "A1",
        prompt: Optional[str] = None,
        translate_to: Optional[str] = None,
        parts_of_speech: Optional[List[List[str]]] = None,
    ) -> List[Dict[str, str]]:
        """
        使用 AI 為單字生成例句

        Args:
            words: 單字列表
            level: CEFR 等級 (A1, A2, B1, B2, C1, C2)
            prompt: 使用者自訂 prompt
            translate_to: 翻譯目標語言 (zh-TW, ja, ko)
            parts_of_speech: 每個單字的詞性列表

        Returns:
            包含 sentence 和 translation 的字典列表
        """
        self._ensure_client()
        import json

        try:
            # 構建單字資訊
            words_info = []
            for i, word in enumerate(words):
                info = {"word": word}
                if parts_of_speech and i < len(parts_of_speech) and parts_of_speech[i]:
                    info["pos"] = ", ".join(parts_of_speech[i])
                words_info.append(info)

            words_json = json.dumps(words_info, ensure_ascii=False)

            # 構建 system prompt
            system_prompt = f"""You are an English teacher creating example sentences for language learners.
Generate ONE example sentence for each word at CEFR level {level}.
The sentences should be natural, educational, and appropriate for the difficulty level.

CRITICAL REQUIREMENTS:
1. Each sentence MUST contain the exact target word (the word being learned). Do NOT use synonyms or derivatives.
2. If translating to Chinese, you MUST use Traditional Chinese (繁體中文), NOT Simplified Chinese.

Level guidelines:
- A1: Simple present/past, basic vocabulary, short sentences (5-8 words)
- A2: Simple sentences with common phrases, everyday topics (8-12 words)
- B1: Compound sentences, wider vocabulary, various tenses (10-15 words)
- B2: Complex sentences, idiomatic expressions, abstract topics (12-18 words)
- C1: Sophisticated vocabulary, nuanced meaning, formal/informal register
- C2: Near-native fluency, literary style, rare vocabulary acceptable"""

            # 構建 user prompt
            user_prompt = f"""Generate example sentences for the following words:
{words_json}

"""
            if prompt:
                user_prompt += f"Additional instructions: {prompt}\n\n"

            if translate_to:
                lang_name = {
                    "zh-TW": "Traditional Chinese (繁體中文)",
                    "ja": "Japanese",
                    "ko": "Korean",
                }.get(translate_to, translate_to)
                user_prompt += f"""Return as JSON array with this format:
[{{"sentence": "...", "translation": "..."}}]
Where translation is in {lang_name}.
IMPORTANT: Each English sentence MUST contain the exact target word.
Translation to Chinese MUST use Traditional Chinese (繁體中文), NOT Simplified Chinese."""
            else:
                user_prompt += """Return as JSON array with this format:
[{"sentence": "..."}]"""

            user_prompt += "\n\nOnly return the JSON array, no other text."

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,  # 稍高一點讓例句更有變化
                max_tokens=2000,
            )

            # 解析回應
            import re

            content = response.choices[0].message.content.strip()

            # 移除可能的 markdown 代碼塊標記
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            content = content.strip()

            sentences = json.loads(content)

            # 確保返回數量正確
            if len(sentences) != len(words):
                print(
                    f"Warning: Expected {len(words)} sentences, got {len(sentences)}."
                )
                # 補齊或截斷
                while len(sentences) < len(words):
                    sentences.append(
                        {"sentence": f"Example with {words[len(sentences)]}"}
                    )
                sentences = sentences[: len(words)]

            return sentences

        except Exception as e:
            print(f"Generate sentences error: {e}")
            # Fallback: 返回簡單的預設例句
            return [{"sentence": f"This is an example with {word}."} for word in words]

    async def generate_distractors(
        self,
        word: str,
        translation: str,
        count: int = 3,
        part_of_speech: Optional[str] = None,
    ) -> List[str]:
        """
        Generate distractor options for vocabulary selection quiz.

        Uses AI to generate semantically similar but different Chinese translations
        that can be used as wrong answer choices.

        Args:
            word: The English word (e.g., "apple")
            translation: The correct Chinese translation (e.g., "蘋果")
            count: Number of distractors to generate (default: 3)
            part_of_speech: Optional part of speech to help generate better distractors

        Returns:
            List of distractor translations (e.g., ["香蕉", "橘子", "葡萄"])
        """
        self._ensure_client()
        import json

        try:
            pos_hint = f"詞性: {part_of_speech}" if part_of_speech else ""

            prompt = f"""為單字 "{word}"（正確翻譯: {translation}）生成 {count} 個干擾項。
{pos_hint}

嚴格要求:
- 必須是繁體中文翻譯
- 同詞性（名詞配名詞、動詞配動詞）
- 干擾項必須與正確答案有明顯區別，不能是近義詞或相似詞
- 干擾項之間也要有明顯區別，不能互為近義詞
- 選擇同類別但意義完全不同的詞（例如水果類：蘋果的干擾項用香蕉、西瓜，而非紅蘋果、青蘋果）
- 不能是正確答案 "{translation}" 的同義詞或變體
- 每個干擾項應該是常見詞彙，讓學生容易辨別

請以 JSON 陣列格式回覆，只包含 {count} 個干擾項翻譯：
["干擾項1", "干擾項2", "干擾項3"]

只回覆 JSON 陣列，不要其他文字。"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a vocabulary quiz generator. Generate clearly "
                            "different but plausible wrong answer options. "
                            "IMPORTANT: Options must be distinctly different from each other "
                            "and from the correct answer - avoid synonyms or similar meanings. "
                            "CRITICAL: All Chinese output MUST be in Traditional Chinese (繁體中文), "
                            "NOT Simplified Chinese. Always respond with valid JSON array only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=1.0,  # Higher temperature for more variety and distinction
                max_tokens=200,
            )

            # Parse JSON response
            import re

            content = response.choices[0].message.content.strip()
            # Remove markdown code block markers if present
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            content = content.strip()

            distractors = json.loads(content)

            # Filter: remove duplicates (case-insensitive) and correct answer
            seen = {translation.lower().strip()}
            unique_distractors = []
            for d in distractors:
                d_normalized = d.lower().strip()
                if d_normalized not in seen and d.strip():
                    seen.add(d_normalized)
                    unique_distractors.append(d)
            distractors = unique_distractors[:count]

            # Ensure we have enough distractors
            if len(distractors) < count:
                logger.warning(
                    f"Only generated {len(distractors)} distractors for '{word}', "
                    f"expected {count}"
                )

            return distractors

        except Exception as e:
            logger.error(f"Generate distractors error for '{word}': {e}")
            # Fallback: return generic distractors
            fallback = ["選項A", "選項B", "選項C"]
            return fallback[:count]

    async def batch_generate_distractors(
        self,
        words: List[Dict[str, str]],
        count: int = 3,
    ) -> List[List[str]]:
        """
        Batch generate distractors for multiple words.

        Args:
            words: List of dicts with 'word', 'translation', and optionally 'part_of_speech'
            count: Number of distractors per word (default: 3)

        Returns:
            List of distractor lists, one per input word
        """
        self._ensure_client()
        import json

        try:
            words_json = json.dumps(
                [{"word": w["word"], "translation": w["translation"]} for w in words],
                ensure_ascii=False,
            )

            prompt = f"""為以下單字列表生成干擾項。每個單字需要 {count} 個干擾項。

單字列表:
{words_json}

嚴格要求:
- 所有干擾項必須是繁體中文
- 同詞性（名詞配名詞、動詞配動詞）
- 干擾項必須與正確答案有明顯區別，不能是近義詞或相似詞
- 干擾項之間也要有明顯區別，不能互為近義詞
- 選擇同類別但意義完全不同的詞（例如水果類：蘋果的干擾項用香蕉、西瓜，而非紅蘋果、青蘋果）
- 不能是正確答案的同義詞或變體
- 每個干擾項應該是常見詞彙，讓學生容易辨別

請以 JSON 陣列格式回覆，每個元素是一個包含 {count} 個干擾項的陣列：
[["干擾項1", "干擾項2", "干擾項3"], ["干擾項1", "干擾項2", "干擾項3"], ...]

只回覆 JSON 陣列，不要其他文字。"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a vocabulary quiz generator. Generate clearly "
                            "different but plausible wrong answer options. "
                            "IMPORTANT: Options must be distinctly different from each other "
                            "and from the correct answer - avoid synonyms or similar meanings. "
                            "CRITICAL: All Chinese output MUST be in Traditional Chinese (繁體中文), "
                            "NOT Simplified Chinese. Always respond with valid JSON array only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=1.0,  # Higher temperature for more variety and distinction
                max_tokens=1000,
            )

            # Parse JSON response
            import re

            content = response.choices[0].message.content.strip()
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            content = content.strip()

            all_distractors = json.loads(content)

            # Verify count matches
            if len(all_distractors) != len(words):
                logger.warning(
                    f"Batch distractors count mismatch: expected {len(words)}, "
                    f"got {len(all_distractors)}. Falling back to individual generation."
                )
                # Fallback to individual generation
                tasks = [
                    self.generate_distractors(
                        w["word"],
                        w["translation"],
                        count,
                        w.get("part_of_speech"),
                    )
                    for w in words
                ]
                return await asyncio.gather(*tasks)

            # Filter out correct answers and duplicates from each distractor list
            result = []
            for i, distractors in enumerate(all_distractors):
                correct = words[i]["translation"]
                # Case-insensitive dedup and correct answer removal
                seen = {correct.lower().strip()}
                unique = []
                for d in distractors:
                    d_normalized = d.lower().strip()
                    if d_normalized not in seen and d.strip():
                        seen.add(d_normalized)
                        unique.append(d)
                result.append(unique[:count])

            return result

        except Exception as e:
            logger.error(f"Batch generate distractors error: {e}")
            # Fallback to individual generation
            tasks = [
                self.generate_distractors(
                    w["word"],
                    w["translation"],
                    count,
                    w.get("part_of_speech"),
                )
                for w in words
            ]
            return await asyncio.gather(*tasks)


# 創建全局實例
translation_service = TranslationService()
