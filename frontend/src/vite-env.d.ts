/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_RESOURCE_ACCOUNT_EMAIL?: string;
  // 更多環境變數...
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
