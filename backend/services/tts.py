"""
Text-to-Speech service using edge-tts (free Microsoft Edge TTS)
"""
import edge_tts
import asyncio
import tempfile
import os
from typing import Optional
from google.cloud import storage
import uuid
from datetime import datetime

class TTSService:
    def __init__(self):
        # 可用的語音列表
        self.voices = {
            'en-US': {
                'male': 'en-US-ChristopherNeural',
                'female': 'en-US-JennyNeural',
                'child': 'en-US-AnaNeural'
            },
            'en-GB': {
                'male': 'en-GB-RyanNeural',
                'female': 'en-GB-SoniaNeural'
            },
            'en-AU': {
                'male': 'en-AU-WilliamNeural',
                'female': 'en-AU-NatashaNeural'
            }
        }
        
        # GCS 設定
        self.bucket_name = os.getenv('GCS_BUCKET_NAME', 'duotopia-audio')
        self.storage_client = None
        
    def _get_storage_client(self):
        """延遲初始化 GCS client"""
        if not self.storage_client:
            self.storage_client = storage.Client()
        return self.storage_client
    
    async def generate_tts(
        self, 
        text: str, 
        voice: str = 'en-US-JennyNeural',
        rate: str = '+0%',
        volume: str = '+0%',
        save_to_gcs: bool = True  # 預設為 True，優先使用 GCS
    ) -> str:
        """
        生成 TTS 音檔
        
        Args:
            text: 要轉換的文字
            voice: 語音名稱
            rate: 語速調整 (e.g., '+10%', '-10%')
            volume: 音量調整 (e.g., '+10%', '-10%')
            save_to_gcs: 是否儲存到 GCS
            
        Returns:
            音檔 URL 或本地路徑
        """
        try:
            # 創建 TTS 通訊
            communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
            
            # 生成唯一檔名
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tts_{timestamp}_{file_id}.mp3"
            
            # 使用臨時檔案
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                await communicate.save(tmp_file.name)
                
                if save_to_gcs:
                    try:
                        # 上傳到 GCS
                        client = self._get_storage_client()
                        bucket = client.bucket(self.bucket_name)
                        blob = bucket.blob(f"tts/{filename}")
                        
                        blob.upload_from_filename(tmp_file.name)
                        blob.make_public()
                        
                        # 清理臨時檔案
                        os.unlink(tmp_file.name)
                        
                        # 返回公開 URL
                        return f"https://storage.googleapis.com/{self.bucket_name}/tts/{filename}"
                    except Exception as e:
                        print(f"GCS upload failed: {e}, falling back to local storage")
                        # 如果 GCS 失敗，改用本地儲存
                        save_to_gcs = False
                
                if not save_to_gcs:
                    # 儲存到本地 static 目錄
                    local_dir = "static/audio/tts"
                    os.makedirs(local_dir, exist_ok=True)
                    local_path = os.path.join(local_dir, filename)
                    
                    # 複製檔案到 static 目錄
                    import shutil
                    shutil.copy2(tmp_file.name, local_path)
                    
                    # 清理臨時檔案
                    os.unlink(tmp_file.name)
                    
                    # 返回本地 URL（相對於 API 路徑）
                    return f"/static/audio/tts/{filename}"
                    
        except Exception as e:
            raise Exception(f"TTS generation failed: {str(e)}")
    
    async def batch_generate_tts(
        self,
        texts: list[str],
        voice: str = 'en-US-JennyNeural',
        rate: str = '+0%',
        volume: str = '+0%'
    ) -> list[str]:
        """
        批次生成 TTS
        
        Args:
            texts: 文字列表
            voice: 語音名稱
            rate: 語速調整
            volume: 音量調整
            
        Returns:
            音檔 URL 列表
        """
        tasks = [
            self.generate_tts(text, voice, rate, volume)
            for text in texts
        ]
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def get_available_voices(self, language: str = 'en') -> list[dict]:
        """
        取得可用的語音列表
        
        Args:
            language: 語言代碼 (e.g., 'en', 'zh')
            
        Returns:
            語音列表
        """
        voices = await edge_tts.list_voices()
        
        # 過濾指定語言的語音
        filtered_voices = [
            {
                'name': v['Name'],
                'display_name': v['ShortName'],
                'gender': v['Gender'],
                'locale': v['Locale']
            }
            for v in voices
            if v['Locale'].startswith(language)
        ]
        
        return filtered_voices

# 單例模式
_tts_service = None

def get_tts_service() -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service