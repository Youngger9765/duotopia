"""
Vertex AI (Gemini) Service
用於替代 OpenAI GPT 的 AI 服務

支援功能：
- 文字生成（翻譯、例句生成等）
- JSON 格式輸出（詞性分析、干擾選項等）

Model 對應：
- gpt-4o-mini → gemini-2.5-flash（快速、高效能）
- gpt-4 → gemini-2.5-flash（統一使用）
"""

import os
import json
import re
import logging
from typing import Optional, Literal

logger = logging.getLogger(__name__)


class VertexAIService:
    """Vertex AI (Gemini) 服務封裝"""

    def __init__(self):
        self.project_id = os.getenv("VERTEX_AI_PROJECT_ID", "duotopia-472708")
        self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        self._initialized = False
        self._flash_model = None  # gemini-2.5-flash
        self._pro_model = None  # gemini-2.5-flash (統一使用)

    def _ensure_initialized(self):
        """Lazy initialization of Vertex AI"""
        if not self._initialized:
            try:
                import vertexai

                vertexai.init(project=self.project_id, location=self.location)
                self._initialized = True
                logger.info(
                    f"Vertex AI initialized: project={self.project_id}, "
                    f"location={self.location}"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")
                raise

    def get_flash_model(self):
        """取得 Gemini 2.5 Flash (對應 gpt-4o-mini)"""
        self._ensure_initialized()
        if self._flash_model is None:
            from vertexai.generative_models import GenerativeModel

            self._flash_model = GenerativeModel("gemini-2.5-flash")
        return self._flash_model

    def get_pro_model(self):
        """取得 Gemini 2.5 Flash (統一使用，對應 gpt-4)"""
        self._ensure_initialized()
        if self._pro_model is None:
            from vertexai.generative_models import GenerativeModel

            self._pro_model = GenerativeModel("gemini-2.5-flash")
        return self._pro_model

    async def generate_text(
        self,
        prompt: str,
        model_type: Literal["flash", "pro"] = "flash",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        統一的文字生成介面

        Args:
            prompt: 提示詞
            model_type: 模型類型 ("flash" 或 "pro")
            max_tokens: 最大輸出 token 數
            temperature: 溫度參數 (0-1)
            system_instruction: 系統指令（可選）

        Returns:
            生成的文字
        """
        from vertexai.generative_models import GenerationConfig

        model = (
            self.get_flash_model() if model_type == "flash" else self.get_pro_model()
        )

        config = GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )

        # 如果有系統指令，將其加入到 prompt 中
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        try:
            logger.info(f"Vertex AI generate_text: calling model (type={model_type})")
            response = await model.generate_content_async(
                full_prompt,
                generation_config=config,
            )
            logger.info("Vertex AI generate_text: response received")
            return response.text
        except Exception as e:
            logger.error(f"Vertex AI generation failed: {e}", exc_info=True)
            raise

    async def generate_json(
        self,
        prompt: str,
        model_type: Literal["flash", "pro"] = "flash",
        max_tokens: int = 1000,
        temperature: float = 0.3,
        system_instruction: Optional[str] = None,
    ) -> dict:
        """
        生成 JSON 格式的回應

        Args:
            prompt: 提示詞（應該要求 JSON 輸出）
            model_type: 模型類型
            max_tokens: 最大輸出 token 數
            temperature: 溫度參數
            system_instruction: 系統指令

        Returns:
            解析後的 JSON dict
        """
        from vertexai.generative_models import GenerationConfig

        model = (
            self.get_flash_model() if model_type == "flash" else self.get_pro_model()
        )

        config = GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            response_mime_type="application/json",  # 強制 JSON 輸出
        )

        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        try:
            logger.info(f"Vertex AI generate_json: calling model (type={model_type})")
            response = await model.generate_content_async(
                full_prompt,
                generation_config=config,
            )
            logger.info("Vertex AI generate_json: response received")

            content = response.text.strip()

            # 移除可能的前綴文字和 markdown 代碼塊標記
            # 處理 "Here is the JSON requested:\n```json" 等情況
            content = re.sub(r"^.*?```json\s*", "", content, flags=re.DOTALL)
            content = re.sub(r"^.*?```\s*", "", content, flags=re.DOTALL)
            content = re.sub(r"\s*```$", "", content)
            content = content.strip()

            # 如果清理後仍然無法解析，嘗試找到第一個 [ 或 {
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 尋找 JSON 陣列或物件的起始位置
                array_start = content.find("[")
                object_start = content.find("{")

                if array_start >= 0 and (
                    object_start < 0 or array_start < object_start
                ):
                    # JSON 陣列
                    json_content = content[array_start:]
                    # 找到對應的結束括號
                    bracket_count = 0
                    for i, char in enumerate(json_content):
                        if char == "[":
                            bracket_count += 1
                        elif char == "]":
                            bracket_count -= 1
                            if bracket_count == 0:
                                json_content = json_content[: i + 1]
                                break
                    return json.loads(json_content)
                elif object_start >= 0:
                    # JSON 物件
                    json_content = content[object_start:]
                    bracket_count = 0
                    for i, char in enumerate(json_content):
                        if char == "{":
                            bracket_count += 1
                        elif char == "}":
                            bracket_count -= 1
                            if bracket_count == 0:
                                json_content = json_content[: i + 1]
                                break
                    return json.loads(json_content)
                else:
                    raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Vertex AI response: {e}")
            logger.error(f"Raw response: {response.text if response else 'None'}")
            raise
        except Exception as e:
            logger.error(f"Vertex AI JSON generation failed: {e}", exc_info=True)
            raise

    def generate_text_sync(
        self,
        prompt: str,
        model_type: Literal["flash", "pro"] = "flash",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        同步版本的文字生成介面（用於 cron job 等非異步場景）

        Args:
            prompt: 提示詞
            model_type: 模型類型 ("flash" 或 "pro")
            max_tokens: 最大輸出 token 數
            temperature: 溫度參數 (0-1)
            system_instruction: 系統指令（可選）

        Returns:
            生成的文字
        """
        from vertexai.generative_models import GenerationConfig

        model = (
            self.get_flash_model() if model_type == "flash" else self.get_pro_model()
        )

        config = GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )

        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        try:
            response = model.generate_content(
                full_prompt,
                generation_config=config,
            )
            return response.text
        except Exception as e:
            logger.error(f"Vertex AI sync generation failed: {e}")
            raise


# 全局實例（lazy initialization）
_vertex_ai_service: Optional[VertexAIService] = None


def get_vertex_ai_service() -> VertexAIService:
    """取得 Vertex AI 服務實例"""
    global _vertex_ai_service
    if _vertex_ai_service is None:
        _vertex_ai_service = VertexAIService()
    return _vertex_ai_service


# 方便直接導入使用
vertex_ai_service = get_vertex_ai_service()
