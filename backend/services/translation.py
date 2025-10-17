"""
Translation service using OpenAI API
"""

import os
from typing import List, Dict, Optional  # noqa: F401
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


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
                            "translation without any explanation."
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
                            "Return ONLY the JSON array, no markdown, no explanation."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1000,  # 增加 tokens 以支援更多翻譯
            )

            # 解析 JSON 回應
            import re

            content = response.choices[0].message.content.strip()

            # 移除可能的 markdown 代碼塊標記
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            content = content.strip()

            translations = json.loads(content)

            # 確保返回的翻譯數量與輸入相同
            if len(translations) != len(texts):
                print(
                    f"Warning: Expected {len(texts)} translations, got {len(translations)}. "
                    f"Falling back to individual translation."
                )
                # Fallback: 逐句翻譯
                import asyncio

                tasks = [self.translate_text(text, target_lang) for text in texts]
                translations = await asyncio.gather(*tasks)

            return translations
        except Exception as e:
            print(
                f"Batch translation error: {e}. Falling back to individual translation."
            )
            # Fallback: 逐句翻譯
            import asyncio

            tasks = [self.translate_text(text, target_lang) for text in texts]
            translations = await asyncio.gather(*tasks)
            return translations


# 創建全局實例
translation_service = TranslationService()
