import { env } from '../config/env';
import { BackendCaller } from './backend-caller';

/** Сервис авторизации DIO desk */
export const authApi = new BackendCaller(env.authApiUrl);

/** Сервис ИИ-чатов */
export const chatsApi = new BackendCaller(env.chatsApiUrl);

export { ApiError, describeError, isAbortError } from './api-error';
export { authTokens, type TokenPair } from './auth-tokens';

/** Страница списка в формате API чатов. */
export interface Page<T> {
  items: T[];
  meta: {
    page: number;
    size: number;
    total: number;
    has_next: boolean;
  };
}
