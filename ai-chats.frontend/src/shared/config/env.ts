export const env = {
  /** Сервис авторизации DIO desk */
  authApiUrl: import.meta.env.VITE_AUTH_API_URL ?? '/auth-api',
  /** Сервис ИИ-чатов */
  chatsApiUrl: import.meta.env.VITE_CHATS_API_URL ?? '/chats-api',
} as const;
