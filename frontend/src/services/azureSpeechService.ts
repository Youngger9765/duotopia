import * as sdk from "microsoft-cognitiveservices-speech-sdk";
import axios from "axios";

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
    console.log("🔑 [TOKEN] 检查 cache...", {
      hasCachedToken: !!this.tokenCache,
      cacheExpired: this.tokenCache
        ? new Date() >= this.tokenCache.expiresAt
        : "no cache",
    });

    // 检查 cache 是否有效（提前1分钟过期）
    if (this.tokenCache && new Date() < this.tokenCache.expiresAt) {
      console.log("✅ [TOKEN] 使用缓存的 token");
      return {
        token: this.tokenCache.token,
        region: this.tokenCache.region,
      };
    }

    console.log("🔑 [TOKEN] 缓存过期或不存在，请求新 token...");

    // Cache 过期或不存在，重新获取
    try {
      const response = await axios.post("/api/azure-speech/token");
      const { token, region, expires_in } = response.data;

      console.log("✅ [TOKEN] 新 token 获取成功", {
        region,
        expires_in,
        tokenLength: token.length,
      });

      // Cache token（提前1分钟过期 = 9分钟有效）
      this.tokenCache = {
        token,
        region,
        expiresAt: new Date(Date.now() + (expires_in - 60) * 1000),
      };

      return { token, region };
    } catch (error) {
      console.error("❌ [TOKEN] 获取失败", {
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
    console.log("🔵 [AZURE] analyzePronunciation 开始", {
      audioBlobSize: audioBlob.size,
      referenceText: referenceText.substring(0, 50) + "...",
      retryCount,
    });

    const startTime = Date.now();

    try {
      // 1. 获取短效 token
      console.log("🔑 [AZURE] 获取 token...");
      const { token, region } = await this.getToken();
      console.log("🔑 [AZURE] Token 获取成功", {
        region,
        tokenLength: token.length,
      });

      // 2. 配置 Speech SDK
      console.log("⚙️ [AZURE] 配置 Speech SDK...");
      const speechConfig = sdk.SpeechConfig.fromAuthorizationToken(
        token,
        region,
      );
      speechConfig.speechRecognitionLanguage = "en-US";

      // 3. 配置发音评估参数
      const pronunciationConfig = new sdk.PronunciationAssessmentConfig(
        referenceText,
        sdk.PronunciationAssessmentGradingSystem.HundredMark,
        sdk.PronunciationAssessmentGranularity.Phoneme,
        true, // enableMiscue
      );

      // 4. 从 Blob 创建音频配置
      const audioFile = new File([audioBlob], "recording.wav", {
        type: "audio/wav",
      });
      const audioConfig = sdk.AudioConfig.fromWavFileInput(audioFile);

      // 5. 创建语音识别器
      const recognizer = new sdk.SpeechRecognizer(speechConfig, audioConfig);
      pronunciationConfig.applyTo(recognizer);

      console.log("🎙️ [AZURE] 开始识别...");

      // 6. 执行识别（Promise 包装）
      return new Promise((resolve, reject) => {
        recognizer.recognizeOnceAsync(
          (result) => {
            const latencyMs = Date.now() - startTime;

            // 识别成功
            if (result.reason === sdk.ResultReason.RecognizedSpeech) {
              console.log("✅ [AZURE] 识别成功", {
                latencyMs: `${latencyMs}ms`,
                reason: result.reason,
              });

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
              console.warn("⚠️ [AZURE] Token 可能过期，retry...", {
                reason: result.reason,
                errorDetails: result.errorDetails,
              });
              this.tokenCache = null; // 清除旧 token
              recognizer.close();

              // 递归重试（只重试一次）
              resolve(this.analyzePronunciation(audioBlob, referenceText, 1));
            }
            // 其他错误
            else {
              console.error("❌ [AZURE] 识别失败", {
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
            console.error("❌ [AZURE] 识别错误", { error });

            recognizer.close();

            // 401 错误 - 自动 retry
            if (error.includes("401") && retryCount === 0) {
              console.warn("⚠️ [AZURE] 401 错误，retry...");
              this.tokenCache = null;
              resolve(this.analyzePronunciation(audioBlob, referenceText, 1));
            } else {
              reject(new Error(`分析失败: ${error}`));
            }
          },
        );
      });
    } catch (error) {
      console.error("❌ [AZURE] analyzePronunciation 异常", error);
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
      const formData = new FormData();
      formData.append("audio_file", audioBlob, "recording.wav");
      formData.append("analysis_json", JSON.stringify(analysisResult));
      formData.append("latency_ms", latencyMs.toString());

      // 背景上传，不等待结果（catch 捕获错误但不抛出）
      axios
        .post("/api/speech/upload-analysis", formData, {
          headers: { "Content-Type": "multipart/form-data" },
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
