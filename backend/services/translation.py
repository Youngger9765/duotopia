"""
Translation service using OpenAI API
"""

import os
import asyncio
import logging
import threading
import time
from collections import OrderedDict
from typing import List, Dict, Optional  # noqa: F401
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Cache controls: fixed size and TTL to avoid unbounded memory in Cloud Run
TRANSLATION_CACHE_MAXSIZE = 5000
TRANSLATION_CACHE_TTL_SECONDS = 3600  # 1 hour


class _LRUTTLCache:
    """Simple thread-safe LRU cache with TTL, to avoid extra dependencies."""

    def __init__(self, maxsize: int, ttl_seconds: int):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._store: OrderedDict = OrderedDict()
        self._lock = threading.Lock()

    def _evict_expired(self):
        now = time.time()
        expired_keys = [
            key for key, (_, ts) in self._store.items() if now - ts > self.ttl_seconds
        ]
        for key in expired_keys:
            self._store.pop(key, None)

    def get(self, key):
        with self._lock:
            self._evict_expired()
            if key in self._store:
                value, ts = self._store.pop(key)
                # reinsert to mark as recently used
                self._store[key] = (value, ts)
                return value
            return None

    def set(self, key, value):
        with self._lock:
            self._evict_expired()
            if key in self._store:
                self._store.pop(key)
            self._store[key] = (value, time.time())
            if len(self._store) > self.maxsize:
                self._store.popitem(last=False)

    def clear(self):
        with self._lock:
            self._store.clear()

    def size(self) -> int:
        with self._lock:
            self._evict_expired()
            return len(self._store)


class TranslationService:
    def __init__(
        self,
        cache_maxsize: int = TRANSLATION_CACHE_MAXSIZE,
        cache_ttl_seconds: int = TRANSLATION_CACHE_TTL_SECONDS,
    ):
        self.client = None
        self.model = "gpt-3.5-turbo"
        # Cache statistics
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache = _LRUTTLCache(cache_maxsize, cache_ttl_seconds)
        self._cache_ttl_seconds = cache_ttl_seconds
        self._cache_maxsize = cache_maxsize

    def _ensure_client(self):
        """Lazy initialization of OpenAI client"""
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            self.client = OpenAI(api_key=api_key)

    def _translate_sync(self, text: str, target_lang: str = "zh-TW") -> str:
        """
        Synchronous translation helper (runs in thread when called from async).
        """
        self._ensure_client()

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

    async def translate_text(self, text: str, target_lang: str = "zh-TW") -> str:
        """
        翻譯單一文本（使用 LRU 缓存减少 API 调用）

        Args:
            text: 要翻譯的文本
            target_lang: 目標語言（預設為繁體中文）

        Returns:
            翻譯後的文本
        """
        cache_key = (text, target_lang, self.model, 0.3)

        cached = self._cache.get(cache_key)
        if cached is not None:
            self._cache_hits += 1
            logger.debug(
                f"Translation cache HIT for '{text[:30]}...' ({target_lang}). "
                f"Total hits: {self._cache_hits}, misses: {self._cache_misses}"
            )
            return cached

        self._cache_misses += 1
        logger.info(
            f"Translation cache MISS for '{text[:30]}...' ({target_lang}). "
            f"Total hits: {self._cache_hits}, misses: {self._cache_misses}"
        )

        try:
            # Run synchronous API call in a thread to avoid blocking event loop
            result = await asyncio.to_thread(self._translate_sync, text, target_lang)
        except Exception as e:
            logger.error(f"Translation error: {e}")
            result = text

        self._cache.set(cache_key, result)
        return result

    def get_cache_stats(self) -> Dict[str, any]:
        """
        Get cache statistics for monitoring

        Returns:
            Dictionary with cache hit/miss rates and other metrics
        """
        total_calls = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_calls * 100) if total_calls > 0 else 0

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_calls": total_calls,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": self._cache.size(),
            "cache_maxsize": self._cache_maxsize,
            "cache_ttl_seconds": self._cache_ttl_seconds,
        }

    def clear_cache(self):
        """Clear the translation cache"""
        self._cache.clear()
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
        # If batch is small or has duplicates, prefer individual calls to reuse cache
        if len(texts) <= 10 or len(set(texts)) < len(texts):
            logger.info(
                f"Using individual translation for {len(texts)} items "
                f"(unique: {len(set(texts))}) to maximize cache hits"
            )
            results: List[str] = []
            for text in texts:
                results.append(await self.translate_text(text, target_lang))
            return results

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
                logger.warning(
                    "Batch translation count mismatch "
                    f"(expected {len(texts)}, got {len(translations)}), "
                    "falling back to individual translation."
                )
                # Fallback: 逐句翻譯
                tasks = [self.translate_text(text, target_lang) for text in texts]
                translations = await asyncio.gather(*tasks)
                return translations

            # Populate cache for future calls
            for text, translation in zip(texts, translations):
                cache_key = (text, target_lang, self.model, 0.3)
                self._cache.set(cache_key, translation)

            return translations
        except Exception as e:
            logger.error(
                f"Batch translation error: {e}. Falling back to individual translation."
            )
            # Fallback: 逐句翻譯
            tasks = [self.translate_text(text, target_lang) for text in texts]
            translations = await asyncio.gather(*tasks)
            return translations


# 創建全局實例
translation_service = TranslationService()
