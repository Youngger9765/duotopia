import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

// Import translation files
import zhTW from "./locales/zh-TW/translation.json";
import en from "./locales/en/translation.json";
import ja from "./locales/ja/translation.json";
import ko from "./locales/ko/translation.json";

const resources = {
  "zh-TW": {
    translation: zhTW,
  },
  en: {
    translation: en,
  },
  ja: {
    translation: ja,
  },
  ko: {
    translation: ko,
  },
};

i18n
  // 偵測使用者語言
  .use(LanguageDetector)
  // 傳遞 i18n 實例到 react-i18next
  .use(initReactI18next)
  // 初始化 i18next
  .init({
    resources,
    fallbackLng: "zh-TW", // 預設語言
    debug: import.meta.env.DEV, // 開發環境啟用 debug

    interpolation: {
      escapeValue: false, // React 已經保護了
    },

    // 語言偵測選項
    detection: {
      order: ["localStorage", "navigator"],
      caches: ["localStorage"],
    },
  });

export default i18n;
