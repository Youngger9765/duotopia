/**
 * 跨平台音訊錄音策略
 * 根據不同平台選擇最佳錄音配置
 */

import { detectDevice } from "./deviceDetector";

export interface RecordingStrategy {
  // MIME type 配置
  preferredMimeType: string;
  fallbackMimeTypes: string[];

  // 錄音參數
  useTimeslice: boolean;
  timesliceMs?: number;
  useRequestData: boolean;

  // 限制
  maxDuration: number; // seconds
  minDuration: number; // seconds

  // 驗證策略
  durationValidation: "metadata-first" | "filesize-first" | "lenient";
  minFileSize: number; // bytes

  // 平台資訊
  platformName: string;
  notes: string;
}

/**
 * 根據平台取得錄音策略
 */
export function getRecordingStrategy(
  userAgent: string = navigator.userAgent,
): RecordingStrategy {
  const device = detectDevice(userAgent);

  // 🍎 iOS 全系列 - 所有 iOS 瀏覽器都用 WebKit
  if (device.platform === "iOS") {
    return {
      preferredMimeType: "audio/webm;codecs=opus", // iOS Safari 實際支援 WebM
      fallbackMimeTypes: ["audio/webm", "audio/mp4", "video/mp4"],
      useTimeslice: false, // ❌ timeslice 會導致 ondataavailable 不觸發
      useRequestData: true, // ✅ 必須主動要資料
      maxDuration: 45,
      minDuration: 1,
      durationValidation: "lenient", // WebM metadata 不可靠，使用寬鬆模式（只檢查檔案大小）
      minFileSize: 10000, // 10KB
      platformName: `iOS ${device.browser}`,
      notes:
        "iOS Safari 支援 WebM 錄音但 metadata 不準確，使用檔案大小判斷有效性",
    };
  }

  // 🍎 macOS Safari - 與 iOS 相同問題：MP4 產生 0 byte，改用 WebM
  if (device.platform === "macOS" && device.browser === "Safari") {
    return {
      preferredMimeType: "audio/webm;codecs=opus", // macOS Safari 實際支援 WebM
      fallbackMimeTypes: ["audio/webm", "audio/mp4", "video/mp4"],
      useTimeslice: false,
      useRequestData: true,
      maxDuration: 45,
      minDuration: 1,
      durationValidation: "lenient", // WebM metadata 不可靠，使用寬鬆模式（只檢查檔案大小）
      minFileSize: 10000, // 10KB
      platformName: "macOS Safari",
      notes:
        "macOS Safari 支援 WebM 錄音但 metadata 不準確，使用檔案大小判斷有效性",
    };
  }

  // 🌐 Chrome/Edge (Desktop & Android)
  if (device.browser === "Chrome" || device.browser === "Edge") {
    return {
      preferredMimeType: "audio/webm;codecs=opus",
      fallbackMimeTypes: ["audio/webm", "audio/mp4"],
      useTimeslice: false, // 不用也沒關係，更簡單
      useRequestData: true, // 保險起見都用
      maxDuration: 45,
      minDuration: 1,
      durationValidation: "metadata-first", // metadata 可靠
      minFileSize: 1000, // 1KB
      platformName: device.browser + (device.isMobile ? " Mobile" : " Desktop"),
      notes: "WebM 支援良好，metadata 可靠",
    };
  }

  // 🦊 Firefox
  if (device.browser === "Firefox") {
    return {
      preferredMimeType: "audio/webm;codecs=opus",
      fallbackMimeTypes: ["audio/ogg;codecs=opus", "audio/webm"],
      useTimeslice: false,
      useRequestData: true,
      maxDuration: 45,
      minDuration: 1,
      durationValidation: "metadata-first",
      minFileSize: 1000,
      platformName: "Firefox",
      notes: "WebM/OGG 支援良好",
    };
  }

  // ❓ 未知瀏覽器 - 保守策略
  return {
    preferredMimeType: "audio/mp4", // 最安全的選擇
    fallbackMimeTypes: ["audio/webm", "audio/ogg"],
    useTimeslice: false,
    useRequestData: true,
    maxDuration: 45,
    minDuration: 1,
    durationValidation: "lenient", // 寬鬆驗證
    minFileSize: 5000, // 5KB
    platformName: "Unknown Browser",
    notes: "未知瀏覽器，使用保守策略",
  };
}

/**
 * 選擇支援的 MIME type
 *
 * Safari (iOS & macOS) 特殊處理：
 * - isTypeSupported() 不可靠，直接返回策略中的 MIME types
 * - 優先 audio/mp4，fallback 到 video/mp4
 * - 讓 AudioRecorder 用 try/catch 確保創建成功
 */
export function selectSupportedMimeType(strategy: RecordingStrategy): string {
  const device = detectDevice(navigator.userAgent);

  // 🍎 Safari (iOS & macOS) 特殊處理：不依賴 isTypeSupported
  if (
    device.platform === "iOS" ||
    (device.platform === "macOS" && device.browser === "Safari")
  ) {
    console.log(
      `🍎 Safari detected, using ${strategy.preferredMimeType} (will try fallbacks if needed)`,
    );
    return strategy.preferredMimeType;
  }

  // 檢查 MediaRecorder.isTypeSupported 是否存在
  if (!MediaRecorder.isTypeSupported) {
    console.warn(
      "⚠️ MediaRecorder.isTypeSupported not available, using preferred MIME type",
    );
    return strategy.preferredMimeType;
  }

  // 🖥️ 非 iOS 平台：使用 isTypeSupported 檢查
  if (MediaRecorder.isTypeSupported(strategy.preferredMimeType)) {
    console.log(`✅ Using preferred MIME type: ${strategy.preferredMimeType}`);
    return strategy.preferredMimeType;
  }

  // 試 fallback
  for (const mimeType of strategy.fallbackMimeTypes) {
    if (MediaRecorder.isTypeSupported(mimeType)) {
      console.log(`✅ Using fallback MIME type: ${mimeType}`);
      return mimeType;
    }
  }

  // 都不支援，返回首選（讓 AudioRecorder 用 try/catch 處理）
  console.warn(
    "⚠️ No MIME type reported as supported, will try preferred anyway",
  );
  return strategy.preferredMimeType;
}

/**
 * 驗證錄音 duration
 */
export async function validateDuration(
  blob: Blob,
  url: string,
  strategy: RecordingStrategy,
): Promise<{ valid: boolean; duration: number; method: string }> {
  // 🎯 Lenient mode: 只要檔案大小合理就接受
  if (strategy.durationValidation === "lenient") {
    if (blob.size >= strategy.minFileSize) {
      const estimatedDuration = blob.size / (16 * 1024); // 假設 128kbps
      return {
        valid: true,
        duration: estimatedDuration,
        method: "lenient-filesize",
      };
    }
    return { valid: false, duration: 0, method: "lenient-rejected" };
  }

  // 🎯 FileSize-First mode: 先試檔案大小估算
  if (strategy.durationValidation === "filesize-first") {
    if (blob.size >= strategy.minFileSize) {
      const estimatedDuration = blob.size / (16 * 1024);

      // 檔案大小驗證通過，再試 metadata（當作 bonus）
      try {
        const metadataDuration = await tryGetMetadataDuration(url);
        if (metadataDuration > 0 && isFinite(metadataDuration)) {
          return {
            valid: true,
            duration: metadataDuration,
            method: "filesize-first-with-metadata",
          };
        }
      } catch {
        // metadata 失敗沒關係，用估算的
      }

      return {
        valid: true,
        duration: estimatedDuration,
        method: "filesize-estimated",
      };
    }

    return { valid: false, duration: 0, method: "filesize-too-small" };
  }

  // 🎯 Metadata-First mode: 先試 metadata，失敗才用檔案大小
  try {
    const metadataDuration = await tryGetMetadataDuration(url);

    if (metadataDuration > 0 && isFinite(metadataDuration)) {
      return {
        valid: true,
        duration: metadataDuration,
        method: "metadata",
      };
    }
  } catch {
    console.warn("⚠️ Metadata extraction failed, falling back to file size");
  }

  // Fallback: 用檔案大小
  if (blob.size >= strategy.minFileSize) {
    const estimatedDuration = blob.size / (16 * 1024);
    return {
      valid: true,
      duration: estimatedDuration,
      method: "metadata-failed-filesize-fallback",
    };
  }

  return { valid: false, duration: 0, method: "all-methods-failed" };
}

/**
 * 嘗試從 metadata 取得 duration
 */
async function tryGetMetadataDuration(url: string): Promise<number> {
  return new Promise((resolve, reject) => {
    const audio = new Audio(url);
    const timeout = setTimeout(() => {
      reject(new Error("Metadata load timeout"));
    }, 3000);

    audio.addEventListener("loadedmetadata", () => {
      clearTimeout(timeout);
      resolve(audio.duration);
    });

    audio.addEventListener("error", () => {
      clearTimeout(timeout);
      reject(new Error("Audio load error"));
    });

    audio.load();
  });
}
