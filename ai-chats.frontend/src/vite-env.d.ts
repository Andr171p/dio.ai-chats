/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AUTH_API_URL?: string;
  readonly VITE_CHATS_API_URL?: string;
  /** Через запятую, например `http://localhost:3000,https://desk.dios.ru` */
  readonly VITE_TRUSTED_ORIGINS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
