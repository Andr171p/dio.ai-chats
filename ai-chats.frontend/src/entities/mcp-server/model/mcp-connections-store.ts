import { create } from 'zustand';
import { chatsApi, describeError, type Page } from '@/shared/api';
import { registerStoreReset } from '@/shared/lib/store-reset';
import { loadMcpServers } from './mcp-servers-store';
import type { McpConnection, McpConnectionInput } from './types';

const BASE = '/api/v1/mcp-connections';

interface McpConnectionsState {
  items: McpConnection[];
  status: 'idle' | 'loading' | 'ready' | 'error';
  error: string | null;
}

export const useMcpConnections = create<McpConnectionsState>()(() => ({
  items: [],
  status: 'idle',
  error: null,
}));

registerStoreReset(() =>
  useMcpConnections.setState(useMcpConnections.getInitialState(), true),
);

/** Каталог для чатов меняется вместе с подключениями. */
const refreshCatalog = () => void loadMcpServers({ force: true });

export async function loadMcpConnections() {
  useMcpConnections.setState({ status: 'loading', error: null });
  try {
    const page = await chatsApi.get<Page<McpConnection>>(BASE, {
      query: { size: 100 },
    });
    useMcpConnections.setState({ items: page.items, status: 'ready' });
  } catch (error) {
    useMcpConnections.setState({
      status: 'error',
      error: describeError(error),
    });
  }
}

export async function createMcpConnection({
  auth,
  ...input
}: McpConnectionInput) {
  const connection = await chatsApi.post<McpConnection>(BASE, {
    body: { ...input, auth: { type: auth } },
  });

  useMcpConnections.setState(({ items }) => ({
    items: [connection, ...items],
  }));
  refreshCatalog();
}

/** Способ авторизации после создания не меняется. */
export async function updateMcpConnection(
  id: string,
  patch: Partial<Omit<McpConnectionInput, 'auth'>>,
) {
  const connection = await chatsApi.patch<McpConnection>(`${BASE}/${id}`, {
    body: patch,
  });

  useMcpConnections.setState(({ items }) => ({
    items: items.map((item) => (item.id === id ? connection : item)),
  }));
  refreshCatalog();
}

export async function deleteMcpConnection(id: string) {
  await chatsApi.delete(`${BASE}/${id}`);

  useMcpConnections.setState(({ items }) => ({
    items: items.filter((item) => item.id !== id),
  }));
  refreshCatalog();
}
