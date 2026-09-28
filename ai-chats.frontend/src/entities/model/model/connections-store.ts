import { create } from 'zustand';
import { chatsApi, describeError, type Page } from '@/shared/api';
import { registerStoreReset } from '@/shared/lib/store-reset';
import { loadModels } from './models-store';
import type { ModelConnection, ModelConnectionInput } from './types';

const BASE = '/api/v1/model-connections';

interface ConnectionsState {
  items: ModelConnection[];
  status: 'idle' | 'loading' | 'ready' | 'error';
  error: string | null;
}

export const useModelConnections = create<ConnectionsState>()(() => ({
  items: [],
  status: 'idle',
  error: null,
}));

registerStoreReset(() =>
  useModelConnections.setState(useModelConnections.getInitialState(), true),
);

const replace = (connection: ModelConnection) =>
  useModelConnections.setState(({ items }) => ({
    items: items.map((item) => (item.id === connection.id ? connection : item)),
  }));

export async function loadModelConnections() {
  useModelConnections.setState({ status: 'loading', error: null });
  try {
    const page = await chatsApi.get<Page<ModelConnection>>(BASE, {
      query: { size: 100 },
    });
    useModelConnections.setState({ items: page.items, status: 'ready' });
  } catch (error) {
    useModelConnections.setState({
      status: 'error',
      error: describeError(error),
    });
  }
}

export async function createModelConnection({
  baseUrl,
  apiKey,
  ...input
}: ModelConnectionInput) {
  const connection = await chatsApi.post<ModelConnection>(BASE, {
    body: {
      ...input,
      route: { type: 'system', baseUrl, apiKey: apiKey || null },
    },
  });

  useModelConnections.setState(({ items }) => ({
    items: [...items, connection],
  }));
  void loadModels({ force: true });
}

/** Протокол после создания не меняется; пустой ключ оставляет текущий. */
export async function updateModelConnection(
  id: string,
  { apiKey, ...patch }: Partial<Omit<ModelConnectionInput, 'protocol'>>,
) {
  const connection = await chatsApi.patch<ModelConnection>(`${BASE}/${id}`, {
    body: { ...patch, ...(apiKey && { apiKey }) },
  });

  replace(connection);
  void loadModels({ force: true });
}

export async function deleteModelConnection(id: string) {
  await chatsApi.delete(`${BASE}/${id}`);

  useModelConnections.setState(({ items }) => ({
    items: items.filter((item) => item.id !== id),
  }));
  void loadModels({ force: true });
}
