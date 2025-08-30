"""
Translation service using OpenAI API
"""
import os
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class TranslationService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        # 使用最便宜的模型
        self.model = "gpt-3.5-turbo"
    
    async def translate_text(self, text: str, target_lang: str = "zh-TW") -> str:
        """
        翻譯單一文本
        
        Args:
            text: 要翻譯的文本
            target_lang: 目標語言（預設為繁體中文）
        
        Returns:
            翻譯後的文本
        """
        try:
            # 根據目標語言設定 prompt
            if target_lang == "zh-TW":
                prompt = f"請將以下英文翻譯成繁體中文，只回覆翻譯結果，不要加任何說明：\n{text}"
            else:
                prompt = f"Please translate the following text to English, only return the translation without any explanation:\n{text}"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional translator. Only provide the translation without any explanation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 降低隨機性以獲得更一致的翻譯
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Translation error: {e}")
            # 如果翻譯失敗，返回原文
            return text
    
    async def batch_translate(self, texts: List[str], target_lang: str = "zh-TW") -> List[str]:
        """
        批次翻譯多個文本
        
        Args:
            texts: 要翻譯的文本列表
            target_lang: 目標語言（預設為繁體中文）
        
        Returns:
            翻譯後的文本列表
        """
        try:
            # 將所有文本組合成一個請求以節省 API 呼叫
            combined_text = "\n---\n".join(texts)
            
            if target_lang == "zh-TW":
                prompt = f"""請將以下英文句子翻譯成繁體中文。
每個句子之間用 --- 分隔。
請保持相同的格式，每個翻譯也用 --- 分隔。
只回覆翻譯結果，不要加任何說明或編號。

{combined_text}"""
            else:
                prompt = f"""Please translate the following sentences to English.
Each sentence is separated by ---.
Keep the same format, separate each translation with ---.
Only return the translations without any explanation or numbering.

{combined_text}"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional translator. Maintain the exact format with --- separators."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500  # 批次翻譯需要更多 tokens
            )
            
            # 分割翻譯結果
            translations = response.choices[0].message.content.strip().split("---")
            translations = [t.strip() for t in translations if t.strip()]
            
            # 確保返回的翻譯數量與輸入相同
            if len(translations) != len(texts):
                print(f"Warning: Expected {len(texts)} translations, got {len(translations)}")
                # 如果數量不匹配，返回原文
                return texts
            
            return translations
        except Exception as e:
            print(f"Batch translation error: {e}")
            # 如果翻譯失敗，返回原文列表
            return texts

# 創建全局實例
translation_service = TranslationService()