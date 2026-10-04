import type { McpAuthType, McpConnection } from '../model/types';

export const MCP_AUTH_LABELS: Record<McpAuthType, string> = {
  dios: 'Учётная запись DIOS',
  none: 'Без авторизации',
  api_key: 'API-ключ',
  oauth: 'OAuth',
};

/** Адрес сервера, если его вызывает сервис чатов. */
export function mcpConnectionUrl({ route }: McpConnection): string | null {
  switch (route.type) {
    case 'managed':
      return route.target;
    case 'remote':
      return route.url;
    default:
      return null;
  }
}
