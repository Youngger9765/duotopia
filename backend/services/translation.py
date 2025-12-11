"""
Translation service using OpenAI API
"""

import os
import logging
from typing import List, Dict, Optional  # noqa: F401
from functools import lru_cache
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class TranslationService:
    def __init__(self):
        self.client = None
        self.model = "gpt-3.5-turbo"
        # Cache statistics
        self._cache_hits = 0
        self._cache_misses = 0

    def _ensure_client(self):
        """Lazy initialization of OpenAI client"""
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self.client = OpenAI(api_key=api_key)

    @lru_cache(maxsize=10000)
    def _translate_cached(self, text: str, target_lang: str = "zh-TW") -> str:
        """
        Cached synchronous translation helper

        Args:
            text: Text to translate
            target_lang: Target language

        Returns:
            Translated text
        """
        self._ensure_client()

        try:
            # Build prompt based on target language
            if target_lang == "zh-TW":
                prompt = f"請將以下英文翻譯成繁體中文，只回覆翻譯結果，不要加任何說明：\n{text}"
            elif target_lang == "en":
                # English definition
                prompt = (
                    f"Please provide a simple English definition or explanation "
                    f"for the following word or phrase. "
                    f"Keep it concise (1-2 sentences) and suitable for language "
                    f"learners:\n{text}"
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
                temperature=0.3,  # Lower randomness for consistent translations
                max_tokens=100,
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Translation error: {e}")
            # Return original text if translation fails
            return text

    async def translate_text(self, text: str, target_lang: str = "zh-TW") -> str:
        """
        翻譯單一文本（使用 LRU 缓存减少 API 调用）

        Args:
            text: 要翻譯的文本
            target_lang: 目標語言（預設為繁體中文）

        Returns:
            翻譯後的文本
        """
        # Check cache before calling API
        cache_info = self._translate_cached.cache_info()
        prev_hits = cache_info.hits

        # Call cached translation
        result = self._translate_cached(text, target_lang)

        # Track cache statistics
        new_cache_info = self._translate_cached.cache_info()
        if new_cache_info.hits > prev_hits:
            self._cache_hits += 1
            logger.debug(
                f"Translation cache HIT for '{text[:30]}...' ({target_lang}). "
                f"Total hits: {self._cache_hits}, misses: {self._cache_misses}"
            )
        else:
            self._cache_misses += 1
            logger.info(
                f"Translation cache MISS for '{text[:30]}...' ({target_lang}). "
                f"Total hits: {self._cache_hits}, misses: {self._cache_misses}"
            )

        return result

    def get_cache_stats(self) -> Dict[str, any]:
        """
        Get cache statistics for monitoring

        Returns:
            Dictionary with cache hit/miss rates and other metrics
        """
        cache_info = self._translate_cached.cache_info()
        total_calls = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_calls * 100) if total_calls > 0 else 0

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_calls": total_calls,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": cache_info.currsize,
            "cache_maxsize": cache_info.maxsize,
        }

    def clear_cache(self):
        """Clear the translation cache"""
        self._translate_cached.cache_clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("Translation cache cleared")

    async def batch_translate(
        self, texts: List[str], target_lang: str = "zh-TW"
    ) -> List[str]:
        """
        批次翻譯多個文本（使用缓存优化，重复文本不会重复翻译）

        Args:
            texts: 要翻譯的文本列表
            target_lang: 目標語言（預設為繁體中文）

        Returns:
            翻譯後的文本列表
        """
        # Strategy: Check for cached items first
        # If many items are cached, use individual lookups
        # Otherwise, use batch API call
        import asyncio

        cached_count = 0
        for text in texts:
            cache_key = (text, target_lang)
            # Check if in cache without calling the function
            if cache_key in {
                (text, lang)
                for text, lang in [
                    (t, l)
                    for t, l in zip(
                        [text],
                        [target_lang],
                    )
                ]
            }:
                cached_count += 1

        # If batch is small or has many potential cache hits, use individual calls
        # This maximizes cache utilization
        if len(texts) <= 10 or len(set(texts)) < len(texts):
            logger.info(
                f"Using individual translation for {len(texts)} items "
                f"(unique: {len(set(texts))}) to maximize cache hits"
            )
            tasks = [self.translate_text(text, target_lang) for text in texts]
            return await asyncio.gather(*tasks)

        # For large unique batches, use batch API
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
                prompt = f"""Please provide simple English definitions for the \
following JSON array of words/phrases.
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
