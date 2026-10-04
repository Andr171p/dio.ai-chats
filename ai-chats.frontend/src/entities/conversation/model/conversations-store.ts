import { create } from 'zustand';
import type { ModelSelection } from '@/entities/model';
import { chatsApi, describeError, type Page } from '@/shared/api';
import { registerStoreReset } from '@/shared/lib/store-reset';
import type { Conversation, ConversationPatch } from './types';

const BASE = '/api/v1/conversations';
const PAGE_SIZE = 50;

interface ConversationsState {
  /** Последние активные — первыми */
  items: Conversation[];
  status: 'idle' | 'loading' | 'ready' | 'error';
  error: string | null;
  page: number;
  hasMore: boolean;
}

export const useConversations = create<ConversationsState>()(() => ({
  items: [],
  status: 'idle',
  error: null,
  page: 0,
  hasMore: false,
}));

registerStoreReset(() =>
  useConversations.setState(useConversations.getInitialState(), true),
);

const byRecentActivity = (a: Conversation, b: Conversation) =>
  b.updatedAt.localeCompare(a.updatedAt);

export function useConversation(id: string | null): Conversation | undefined {
  return useConversations(({ items }) => items.find((item) => item.id === id));
}

export function upsertConversation(conversation: Conversation) {
  useConversations.setState(({ items }) => ({
    items: [
      conversation,
      ...items.filter((item) => item.id !== conversation.id),
    ].sort(byRecentActivity),
  }));
}

async function loadPage(page: number) {
  useConversations.setState({ status: 'loading', error: null });
  try {
    const result = await chatsApi.get<Page<Conversation>>(BASE, {
      query: { page, size: PAGE_SIZE },
    });

    useConversations.setState(({ items }) => {
      // Новые чаты сдвигают offset — убираем дубли
      const known = new Set(result.items.map((item) => item.id));
      const merged =
        page === 1
          ? result.items
          : [...items.filter((item) => !known.has(item.id)), ...result.items];

      return {
        items: merged.sort(byRecentActivity),
        page,
        hasMore: result.meta.has_next,
        status: 'ready',
      };
    });
  } catch (error) {
    useConversations.setState({ status: 'error', error: describeError(error) });
  }
}

export async function loadConversations() {
  if (useConversations.getState().status === 'loading') return;
  await loadPage(1);
}

export async function loadMoreConversations() {
  const { status, hasMore, page } = useConversations.getState();
  if (status === 'loading' || !hasMore) return;
  await loadPage(page + 1);
}

/** Чат, которого ещё нет в загруженном списке (например, открыт после перезагрузки). */
export async function fetchConversation(id: string) {
  upsertConversation(await chatsApi.get<Conversation>(`${BASE}/${id}`));
}

export async function createConversation(
  model: ModelSelection,
  mcpConnectionIds: string[] = [],
): Promise<Conversation> {
  const conversation = await chatsApi.post<Conversation>(BASE, {
    body: { model, mcpConnectionIds },
  });
  upsertConversation(conversation);
  return conversation;
}

export async function updateConversation(id: string, patch: ConversationPatch) {
  const previous = useConversations
    .getState()
    .items.find((item) => item.id === id);

  // Оптимистично: изменения видны сразу, при ошибке откатываются
  if (previous) {
    upsertConversation({
      ...previous,
      ...(patch.title && { title: { label: patch.title, source: 'manual' } }),
      ...(patch.model && { model: patch.model }),
      ...(patch.mcpConnectionIds && {
        mcpConnectionIds: patch.mcpConnectionIds,
      }),
    });
  }

  try {
    upsertConversation(
      await chatsApi.patch<Conversation>(`${BASE}/${id}`, { body: patch }),
    );
  } catch (error) {
    if (previous) upsertConversation(previous);
    throw error;
  }
}

export async function deleteConversation(id: string) {
  await chatsApi.delete(`${BASE}/${id}`);
  useConversations.setState(({ items }) => ({
    items: items.filter((item) => item.id !== id),
  }));
}
