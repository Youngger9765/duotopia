/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  // 更多環境變數可以在這裡定義
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}