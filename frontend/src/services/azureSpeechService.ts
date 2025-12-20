import * as sdk from "microsoft-cognitiveservices-speech-sdk";
import axios from "axios";
import { useStudentAuthStore } from "@/stores/studentAuthStore";
import { useTeacherAuthStore } from "@/stores/teacherAuthStore";

interface TokenCache {
  token: string;
  region: string;
  expiresAt: Date;
}

export class AzureSpeechService {
  private tokenCache: TokenCache | null = null;

  /**
   * 获取 Azure Speech Token（带缓存，提前1分钟过期）
   * @private
   */
  private async getToken(): Promise<{ token: string; region: string }> {
    // 检查 cache 是否有效（提前1分钟过期）
    if (this.tokenCache && new Date() < this.tokenCache.expiresAt) {
      return {
        token: this.tokenCache.token,
        region: this.tokenCache.region,
      };
    }

    // Cache 过期或不存在，重新获取
    try {
      // 🔑 获取 auth token（优先学生，fallback 老师预览）
      const studentToken = useStudentAuthStore.getState().token;
      const teacherToken = useTeacherAuthStore.getState().token;
      const authToken = studentToken || teacherToken;

      if (!authToken) {
        throw new Error("未登入或 token 已过期");
      }

      const apiUrl = import.meta.env.VITE_API_URL || "";
      const response = await axios.post(
        `${apiUrl}/api/azure-speech/token`,
        null,
        {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        },
      );
      const { token, region, expires_in } = response.data;

      // Cache token（提前1分钟过期 = 9分钟有效）
      this.tokenCache = {
        token,
        region,
        expiresAt: new Date(Date.now() + (expires_in - 60) * 1000),
      };

      return { token, region };
    } catch (error) {
      console.error("Failed to get Azure Speech token:", {
        error: (error as { response?: { status?: number } }).response?.status,
        message: (error as Error).message,
      });
      throw new Error("无法获取语音分析授权，请刷新页面重试");
    }
  }

  /**
   * 直接调用 Azure Speech API 分析发音
   *
   * @param audioBlob 录音 Blob (WAV 格式)
   * @param referenceText 参考文本
   * @param retryCount 内部重试计数（用户无需传入）
   * @returns 分析结果和延迟时间
   */
  async analyzePronunciation(
    audioBlob: Blob,
    referenceText: string,
    retryCount = 0,
  ): Promise<{
    result: sdk.PronunciationAssessmentResult;
    latencyMs: number;
  }> {
    const startTime = Date.now();

    try {
      // 1. 获取短效 token
      const { token, region } = await this.getToken();

      // 2. 配置 Speech SDK
      const speechConfig = sdk.SpeechConfig.fromAuthorizationToken(
        token,
        region,
      );
      speechConfig.speechRecognitionLanguage = "en-US";

      // 3. 配置发音评估参数
      // 🎯 Issue #118: 使用 Word 層級而非 Phoneme，加快分析速度
      // 音素分析保留給未來的單字朗讀功能
      const pronunciationConfig = new sdk.PronunciationAssessmentConfig(
        referenceText,
        sdk.PronunciationAssessmentGradingSystem.HundredMark,
        sdk.PronunciationAssessmentGranularity.Word,
        true, // enableMiscue
      );

      // 4. 从 Blob 创建音频配置（使用 push stream 支持所有格式）
      // 解码音频为 PCM 数据
      const arrayBuffer = await audioBlob.arrayBuffer();
      const audioContext = new AudioContext({ sampleRate: 16000 });
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

      // 转换为 16-bit PCM mono
      const pcmData = audioBuffer.getChannelData(0); // Get mono channel
      const pcm16 = new Int16Array(pcmData.length);
      for (let i = 0; i < pcmData.length; i++) {
        // Convert float32 [-1, 1] to int16 [-32768, 32767]
        pcm16[i] = Math.max(
          -32768,
          Math.min(32767, Math.floor(pcmData[i] * 32768)),
        );
      }

      // 创建 push stream 并推送数据
      const pushStream = sdk.AudioInputStream.createPushStream();
      pushStream.write(pcm16.buffer);
      pushStream.close();

      const audioConfig = sdk.AudioConfig.fromStreamInput(pushStream);

      // 5. 创建语音识别器
      const recognizer = new sdk.SpeechRecognizer(speechConfig, audioConfig);
      pronunciationConfig.applyTo(recognizer);

      // 6. 执行识别（Promise 包装）
      return new Promise((resolve, reject) => {
        recognizer.recognizeOnceAsync(
          (result) => {
            const latencyMs = Date.now() - startTime;

            // 识别成功
            if (result.reason === sdk.ResultReason.RecognizedSpeech) {
              const pronunciationResult =
                sdk.PronunciationAssessmentResult.fromResult(result);

              recognizer.close();
              resolve({ result: pronunciationResult, latencyMs });
            }
            // Token 可能过期 - 自动 retry
            else if (
              (result.reason === sdk.ResultReason.NoMatch ||
                result.errorDetails?.includes("401")) &&
              retryCount === 0
            ) {
              this.tokenCache = null; // 清除旧 token
              recognizer.close();

              // 递归重试（只重试一次）
              resolve(this.analyzePronunciation(audioBlob, referenceText, 1));
            }
            // 其他错误
            else {
              console.error("Azure Speech recognition failed:", {
                reason: result.reason,
                errorDetails: result.errorDetails,
              });

              recognizer.close();
              const errorMsg =
                result.errorDetails || `识别失败: ${result.reason}`;
              reject(new Error(errorMsg));
            }
          },
          (error) => {
            console.error("Azure Speech recognition error:", error);

            recognizer.close();

            // 401 错误 - 自动 retry
            if (error.includes("401") && retryCount === 0) {
              this.tokenCache = null;
              resolve(this.analyzePronunciation(audioBlob, referenceText, 1));
            } else {
              reject(new Error(`分析失败: ${error}`));
            }
          },
        );
      });
    } catch (error) {
      console.error("Azure Speech analysis failed:", error);
      throw new Error("语音分析失败，请重试");
    }
  }

  /**
   * 背景上传音档和分析结果（不阻塞 UI）
   *
   * @param audioBlob 录音 Blob
   * @param analysisResult 分析结果
   * @param latencyMs 客户端到 Azure 的延迟
   */
  async uploadAnalysisInBackground(
    audioBlob: Blob,
    analysisResult: sdk.PronunciationAssessmentResult | Record<string, unknown>,
    latencyMs: number,
  ): Promise<void> {
    try {
      // 获取 auth token（优先学生，fallback 老师预览）
      const studentToken = useStudentAuthStore.getState().token;
      const teacherToken = useTeacherAuthStore.getState().token;

      // 老师预览模式：跳过上传（预览不需要存档）
      if (!studentToken && teacherToken) {
        console.log("Teacher preview mode: skipping background upload");
        return;
      }

      const authToken = studentToken || teacherToken;
      if (!authToken) {
        console.warn("No auth token available, skipping upload");
        return;
      }

      const formData = new FormData();
      formData.append("audio_file", audioBlob, "recording.wav");
      formData.append("analysis_json", JSON.stringify(analysisResult));
      formData.append("latency_ms", latencyMs.toString());

      // 背景上传，不等待结果（catch 捕获错误但不抛出）
      const apiUrl = import.meta.env.VITE_API_URL || "";
      axios
        .post(`${apiUrl}/api/speech/upload-analysis`, formData, {
          headers: {
            "Content-Type": "multipart/form-data",
            Authorization: `Bearer ${authToken}`,
          },
        })
        .catch((error) => {
          console.error("Background upload failed:", error);
          // 可选：存到 localStorage 待后续重试
          // this.saveFailedUpload({ audioBlob, analysisResult, latencyMs });
        });
    } catch (error) {
      console.error("Failed to prepare background upload:", error);
    }
  }
}

// Singleton instance
export const azureSpeechService = new AzureSpeechService();
