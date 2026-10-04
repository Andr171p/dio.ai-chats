import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { useShallow } from 'zustand/react/shallow';
import { chatsApi, describeError } from '@/shared/api';
import { registerStoreReset } from '@/shared/lib/store-reset';
import type { AvailableMcpServer, McpTool } from './types';

const BASE = '/api/v1/mcp-servers';

interface ServerTools {
  items: McpTool[];
  status: 'loading' | 'ready' | 'error';
}

interface McpServersState {
  items: AvailableMcpServer[];
  status: 'idle' | 'loading' | 'ready' | 'error';
  error: string | null;
  /** Инструменты по идентификатору подключения: загружаются по требованию */
  tools: Record<string, ServerTools>;
  /** Последний выбор серверов — для новых чатов */
  preferred: string[];
}

const initialState: McpServersState = {
  items: [],
  status: 'idle',
  error: null,
  tools: {},
  preferred: [],
};

export const useMcpServers = create<McpServersState>()(
  persist(() => initialState, {
    name: 'dios.mcp-servers',
    partialize: ({ preferred }) => ({ preferred }),
  }),
);

registerStoreReset(() =>
  useMcpServers.setState(useMcpServers.getInitialState(), true),
);

export async function loadMcpServers({ force = false } = {}) {
  const { status } = useMcpServers.getState();
  if (status === 'loading' || (status === 'ready' && !force)) return;

  useMcpServers.setState({ status: 'loading', error: null });
  try {
    const items = await chatsApi.get<AvailableMcpServer[]>(BASE);
    useMcpServers.setState({ items, status: 'ready' });
  } catch (error) {
    useMcpServers.setState({ status: 'error', error: describeError(error) });
  }
}

/** Инструменты сервера; список зависит от прав пользователя на сервере. */
export async function loadMcpTools(connectionId: string) {
  const current = useMcpServers.getState().tools[connectionId];
  if (current && current.status !== 'error') return;

  const setTools = (tools: ServerTools) =>
    useMcpServers.setState((state) => ({
      tools: { ...state.tools, [connectionId]: tools },
    }));

  setTools({ items: [], status: 'loading' });
  try {
    const items = await chatsApi.get<McpTool[]>(
      `${BASE}/${connectionId}/tools`,
    );
    setTools({ items, status: 'ready' });
  } catch {
    setTools({ items: [], status: 'error' });
  }
}

export function setPreferredMcpServers(connectionIds: string[]) {
  useMcpServers.setState({ preferred: connectionIds });
}

/** Серверы для нового чата: последний выбор без недоступных. */
export function useDefaultMcpServers(): string[] {
  return useMcpServers(
    // Новый массив на каждый вызов: без сравнения по элементам стор зациклит рендер
    useShallow(({ items, preferred }) =>
      preferred.filter((id) =>
        items.some((server) => server.connectionId === id),
      ),
    ),
  );
}
