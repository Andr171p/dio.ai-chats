export const env = {
  /** Сервис авторизации DIO desk */
  authApiUrl: import.meta.env.VITE_AUTH_API_URL ?? '/auth-api',
  /** Сервис ИИ-чатов */
  chatsApiUrl: import.meta.env.VITE_CHATS_API_URL ?? '/chats-api',
  /** Сервисы экосистемы DIOS: ссылки на них из ответов модели открываются без предупреждения */
  trustedOrigins: (import.meta.env.VITE_TRUSTED_ORIGINS ?? '')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean),
} as const;
