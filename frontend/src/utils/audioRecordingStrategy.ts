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

  // 🍎 iOS Safari - 最問題多的平台
  if (device.platform === "iOS" && device.browser === "Safari") {
    return {
      preferredMimeType: "audio/mp4",
      fallbackMimeTypes: [],
      useTimeslice: false, // ❌ timeslice 會導致 ondataavailable 不觸發
      useRequestData: true, // ✅ 必須主動要資料
      maxDuration: 45,
      minDuration: 1,
      durationValidation: "filesize-first", // metadata 不可靠，優先用檔案大小
      minFileSize: 10000, // 10KB
      platformName: "iOS Safari",
      notes:
        "isTypeSupported 不可信，強制使用 MP4，duration metadata 可能是 Infinity",
    };
  }

  // 🍎 macOS Safari - 類似 iOS 問題
  if (device.platform === "macOS" && device.browser === "Safari") {
    return {
      preferredMimeType: "audio/mp4",
      fallbackMimeTypes: [],
      useTimeslice: false,
      useRequestData: true,
      maxDuration: 45,
      minDuration: 1,
      durationValidation: "filesize-first",
      minFileSize: 10000,
      platformName: "macOS Safari",
      notes: "同 iOS Safari，MP4 最穩定",
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
 */
export function selectSupportedMimeType(strategy: RecordingStrategy): string {
  // 先試首選
  if (MediaRecorder.isTypeSupported(strategy.preferredMimeType)) {
    // 🍎 Safari 例外：即使回傳 true 也要檢查
    const device = detectDevice(navigator.userAgent);
    if (
      device.browser === "Safari" &&
      strategy.preferredMimeType !== "audio/mp4"
    ) {
      console.warn("⚠️ Safari detected but not using MP4, forcing MP4");
      return "audio/mp4";
    }

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

  // 都不支援，讓瀏覽器自己選
  console.warn("⚠️ No supported MIME type found, using browser default");
  return "";
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
