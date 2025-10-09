/**
 * 音檔錯誤記錄工具 - 記錄到後端 BigQuery
 */

import {
  detectDevice,
  checkAudioSupport,
  getConnectionInfo,
} from "./deviceDetector";

export interface AudioErrorData {
  errorType: string;
  errorCode?: number;
  errorMessage?: string;
  audioUrl: string;
  audioSize?: number;
  audioDuration?: number;
  contentType?: string;
  studentId?: number;
  assignmentId?: number;
  loadTimeMs?: number;
}

/**
 * 記錄音檔錯誤到後端 BigQuery
 *
 * @param data 錯誤資料
 * @returns Promise<void>
 */
export async function logAudioError(data: AudioErrorData): Promise<void> {
  try {
    const deviceInfo = detectDevice(navigator.userAgent);
    const audioSupport = checkAudioSupport();
    const connectionInfo = getConnectionInfo();

    const errorLog = {
      timestamp: new Date().toISOString(),

      // 錯誤資訊
      error_type: data.errorType,
      error_code: data.errorCode,
      error_message: data.errorMessage,

      // 音檔資訊
      audio_url: data.audioUrl,
      audio_size: data.audioSize,
      audio_duration: data.audioDuration,
      content_type: data.contentType,

      // 裝置資訊
      user_agent: navigator.userAgent,
      platform: deviceInfo.platform,
      browser: deviceInfo.browser,
      browser_version: deviceInfo.browserVersion,
      device_model: deviceInfo.deviceModel,
      is_mobile: deviceInfo.isMobile,
      screen_resolution: `${window.screen.width}x${window.screen.height}`,
      connection_type: connectionInfo?.effectiveType,

      // 使用者資訊
      student_id: data.studentId,
      assignment_id: data.assignmentId,
      page_url: window.location.href,

      // 診斷資訊
      can_play_webm: audioSupport.webm,
      can_play_mp4: audioSupport.mp4,
      load_time_ms: data.loadTimeMs,
    };

    console.log("📊 Logging audio error to BigQuery:", errorLog);

    // 發送到後端（靜默失敗，不影響使用者體驗）
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8080";
    const response = await fetch(`${apiUrl}/api/logs/audio-error`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(errorLog),
    });

    if (!response.ok) {
      console.warn("⚠️ Failed to log audio error:", response.statusText);
    } else {
      console.log("✅ Audio error logged successfully");
    }
  } catch (error) {
    // 靜默失敗，不影響使用者體驗
    console.warn("⚠️ Error logging failed:", error);
  }
}
