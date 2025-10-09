/**
 * 裝置偵測工具 - 從 User Agent 解析裝置資訊
 * 用於 BigQuery 錯誤日誌記錄
 */

export interface DeviceInfo {
  platform: string;
  browser: string;
  browserVersion: string;
  deviceModel?: string;
  isMobile: boolean;
}

/**
 * 從 User Agent 解析裝置資訊
 */
export function detectDevice(userAgent: string): DeviceInfo {
  const ua = userAgent;

  // 偵測平台
  let platform = "Unknown";
  if (/iPad|iPhone|iPod/.test(ua)) {
    platform = "iOS";
  } else if (/Android/.test(ua)) {
    platform = "Android";
  } else if (/Windows/.test(ua)) {
    platform = "Windows";
  } else if (/Mac/.test(ua)) {
    platform = "macOS";
  } else if (/Linux/.test(ua)) {
    platform = "Linux";
  }

  // 偵測瀏覽器
  let browser = "Unknown";
  let browserVersion = "";

  if (/Firefox\/(\d+)/.test(ua)) {
    browser = "Firefox";
    browserVersion = RegExp.$1;
  } else if (/Edg\/(\d+)/.test(ua)) {
    browser = "Edge";
    browserVersion = RegExp.$1;
  } else if (/Chrome\/(\d+)/.test(ua) && !/Edg/.test(ua)) {
    browser = "Chrome";
    browserVersion = RegExp.$1;
  } else if (/Safari\/(\d+)/.test(ua) && !/Chrome/.test(ua)) {
    browser = "Safari";
    // Safari 版本需要從 Version/ 取得
    if (/Version\/(\d+)/.test(ua)) {
      browserVersion = RegExp.$1;
    } else {
      browserVersion = RegExp.$1;
    }
  }

  // 偵測裝置型號（iOS）
  let deviceModel: string | undefined;
  if (/iPhone/.test(ua)) {
    deviceModel = "iPhone";
  } else if (/iPad/.test(ua)) {
    deviceModel = "iPad";
  } else if (/Android/.test(ua)) {
    // Android 裝置型號解析（較複雜）
    const androidMatch = ua.match(/Android.*;\s([^)]+)\)/);
    if (androidMatch && androidMatch[1]) {
      deviceModel = androidMatch[1].trim();
    } else {
      deviceModel = "Android Device";
    }
  }

  // 偵測是否為手機
  const isMobile = /Mobile|Android|iPhone|iPad/.test(ua);

  return {
    platform,
    browser,
    browserVersion,
    deviceModel,
    isMobile,
  };
}

/**
 * 檢測瀏覽器音訊格式支援
 */
export function checkAudioSupport() {
  const audio = document.createElement("audio");
  return {
    webm: audio.canPlayType('audio/webm; codecs="opus"'),
    mp4: audio.canPlayType('audio/mp4; codecs="mp4a.40.2"'),
  };
}

/**
 * 取得網路連線資訊（如果支援）
 */
export function getConnectionInfo() {
  const connection = (navigator as any).connection;
  if (connection) {
    return {
      effectiveType: connection.effectiveType, // '4g', '3g', etc.
      downlink: connection.downlink, // Mbps
    };
  }
  return null;
}
