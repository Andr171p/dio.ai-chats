/** MCP-сервер, который можно подключить к чату. */
export interface AvailableMcpServer {
  connectionId: string;
  name: string;
}

/** Инструмент MCP-сервера в том виде, в котором его видит модель пользователя. */
export interface McpTool {
  name: string;
  title: string | null;
  description: string | null;
}

/**
 * dios — запросы от имени пользователя с его учётной записью DIOS;
 * none — сервер без авторизации.
 */
export type McpAuthType = 'dios' | 'none' | 'api_key' | 'oauth';

type McpRoute =
  | { type: 'managed'; target: string }
  | { type: 'remote'; url: string }
  | { type: 'edge'; endpointId: string; localConnectionId: string };

/** Подключение MCP-сервера (для администратора). */
export interface McpConnection {
  id: string;
  name: string;
  route: McpRoute;
  auth: { type: McpAuthType };
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface McpConnectionInput {
  name: string;
  url: string;
  auth: Extract<McpAuthType, 'dios' | 'none'>;
  enabled?: boolean;
}
