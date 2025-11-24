"""
Text-to-Speech service using Azure Speech Service (Official Microsoft TTS)
"""

import asyncio
import tempfile
import os
from typing import Optional  # noqa: F401
from google.cloud import storage
import uuid
from datetime import datetime  # noqa: F401
import azure.cognitiveservices.speech as speechsdk


class TTSService:
    def __init__(self):
        # 可用的語音列表 (Azure Neural Voices)
        self.voices = {
            "en-US": {
                "male": "en-US-ChristopherNeural",
                "female": "en-US-JennyNeural",
                "child": "en-US-AnaNeural",
            },
            "en-GB": {"male": "en-GB-RyanNeural", "female": "en-GB-SoniaNeural"},
            "en-AU": {"male": "en-AU-WilliamNeural", "female": "en-AU-NatashaNeural"},
        }

        # Azure Speech 設定
        self.azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.azure_speech_region = os.getenv("AZURE_SPEECH_REGION", "eastasia")

        if not self.azure_speech_key:
            raise ValueError("AZURE_SPEECH_KEY environment variable is not set")

        # 儲存設定：GCS 或本地檔案系統
        self.use_gcs = os.getenv("USE_GCS_STORAGE", "false").lower() == "true"
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "duotopia-audio")
        self.storage_client = None

        # 本地儲存目錄（當不使用 GCS 時）
        self.local_audio_dir = os.path.join(os.path.dirname(__file__), "..", "static", "tts")
        if not self.use_gcs:
            os.makedirs(self.local_audio_dir, exist_ok=True)

    def _get_storage_client(self):
        """延遲初始化 GCS client"""
        if not self.storage_client:
            self.storage_client = storage.Client()
        return self.storage_client

    def _convert_rate_to_prosody(self, rate: str) -> str:
        """
        將 rate 字串轉換為 Azure SSML prosody rate
        '+0%' -> '1.0', '+10%' -> '1.1', '-10%' -> '0.9'
        """
        try:
            percent = int(rate.replace("%", "").replace("+", ""))
            prosody_rate = 1.0 + (percent / 100.0)
            return f"{prosody_rate:.2f}"
        except (ValueError, AttributeError):
            return "1.0"

    async def generate_tts(
        self,
        text: str,
        voice: str = "en-US-JennyNeural",
        rate: str = "+0%",
        volume: str = "+0%",
    ) -> str:
        """
        生成 TTS 音檔並上傳到 GCS (使用 Azure Speech Service)

        Args:
            text: 要轉換的文字
            voice: 語音名稱
            rate: 語速調整 (e.g., '+10%', '-10%')
            volume: 音量調整 (e.g., '+10%', '-10%')

        Returns:
            音檔 GCS URL
        """
        try:
            # 配置 Azure Speech
            speech_config = speechsdk.SpeechConfig(
                subscription=self.azure_speech_key, region=self.azure_speech_region
            )
            speech_config.speech_synthesis_voice_name = voice

            # 生成唯一檔名
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tts_{timestamp}_{file_id}.mp3"

            # 使用臨時檔案
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                # 配置音檔輸出
                audio_config = speechsdk.audio.AudioOutputConfig(filename=tmp_file.name)
                synthesizer = speechsdk.SpeechSynthesizer(
                    speech_config=speech_config, audio_config=audio_config
                )

                # 生成 TTS（同步操作，需在 executor 中執行）
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, synthesizer.speak_text, text)

                # 檢查結果
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    if self.use_gcs:
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
                    else:
                        # 儲存到本地檔案系統
                        local_path = os.path.join(self.local_audio_dir, filename)

                        # 移動檔案到本地目錄
                        import shutil
                        shutil.move(tmp_file.name, local_path)

                        # 返回本地 URL
                        return f"/static/tts/{filename}"
                else:
                    # 清理臨時檔案
                    os.unlink(tmp_file.name)
                    raise Exception(f"Azure TTS failed: {result.reason}")

        except Exception as e:
            raise Exception(f"TTS generation failed: {str(e)}")

    async def batch_generate_tts(
        self,
        texts: list[str],
        voice: str = "en-US-JennyNeural",
        rate: str = "+0%",
        volume: str = "+0%",
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
        tasks = [self.generate_tts(text, voice, rate, volume) for text in texts]

        results = await asyncio.gather(*tasks)
        return results

    async def get_available_voices(self, language: str = "en") -> list[dict]:
        """
        取得可用的語音列表 (Azure Speech)

        Args:
            language: 語言代碼 (e.g., 'en', 'zh')

        Returns:
            語音列表
        """
        # Azure Speech 語音列表（精選常用語音）
        all_voices = [
            {
                "name": "en-US-JennyNeural",
                "display_name": "Jenny (US Female)",
                "gender": "Female",
                "locale": "en-US",
            },
            {
                "name": "en-US-ChristopherNeural",
                "display_name": "Christopher (US Male)",
                "gender": "Male",
                "locale": "en-US",
            },
            {
                "name": "en-US-AnaNeural",
                "display_name": "Ana (US Child)",
                "gender": "Female",
                "locale": "en-US",
            },
            {
                "name": "en-GB-SoniaNeural",
                "display_name": "Sonia (UK Female)",
                "gender": "Female",
                "locale": "en-GB",
            },
            {
                "name": "en-GB-RyanNeural",
                "display_name": "Ryan (UK Male)",
                "gender": "Male",
                "locale": "en-GB",
            },
            {
                "name": "en-AU-NatashaNeural",
                "display_name": "Natasha (AU Female)",
                "gender": "Female",
                "locale": "en-AU",
            },
            {
                "name": "en-AU-WilliamNeural",
                "display_name": "William (AU Male)",
                "gender": "Male",
                "locale": "en-AU",
            },
        ]

        # 過濾指定語言的語音
        filtered_voices = [v for v in all_voices if v["locale"].startswith(language)]

        return filtered_voices


# 單例模式
_tts_service = None


def get_tts_service() -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
