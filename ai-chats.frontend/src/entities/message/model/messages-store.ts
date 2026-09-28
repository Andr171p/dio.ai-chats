import { create } from 'zustand';
import { chatsApi, describeError } from '@/shared/api';
import { registerStoreReset } from '@/shared/lib/store-reset';
import type { Message } from './types';

export interface Thread {
  items: Message[];
  status: 'loading' | 'ready' | 'error';
  error: string | null;
}

interface MessagesState {
  /** История текущей ветки по идентификатору чата */
  threads: Record<string, Thread>;
}

export const useMessages = create<MessagesState>()(() => ({ threads: {} }));

registerStoreReset(() =>
  useMessages.setState(useMessages.getInitialState(), true),
);

function patchThread(
  conversationId: string,
  update: (thread: Thread) => Partial<Thread>,
) {
  useMessages.setState(({ threads }) => {
    const thread = threads[conversationId] ?? {
      items: [],
      status: 'ready',
      error: null,
    };
    return {
      threads: {
        ...threads,
        [conversationId]: { ...thread, ...update(thread) },
      },
    };
  });
}

export function useThread(conversationId: string | null): Thread | undefined {
  return useMessages(({ threads }) =>
    conversationId ? threads[conversationId] : undefined,
  );
}

export async function loadMessages(
  conversationId: string,
  { force = false } = {},
) {
  const thread = useMessages.getState().threads[conversationId];
  if (thread && !force && thread.status !== 'error') return;

  patchThread(conversationId, () => ({
    status: thread?.items.length ? 'ready' : 'loading',
    error: null,
  }));
  try {
    const items = await chatsApi.get<Message[]>(
      `/api/v1/conversations/${conversationId}/messages`,
    );
    patchThread(conversationId, () => ({ items, status: 'ready' }));
  } catch (error) {
    patchThread(conversationId, () => ({
      status: 'error',
      error: describeError(error),
    }));
  }
}

export function addMessage(conversationId: string, message: Message) {
  patchThread(conversationId, ({ items }) => ({ items: [...items, message] }));
}

export function replaceMessage(
  conversationId: string,
  id: string,
  message: Message,
) {
  patchThread(conversationId, ({ items }) => ({
    items: items.map((item) => (item.id === id ? message : item)),
  }));
}

export function removeMessage(conversationId: string, id: string) {
  patchThread(conversationId, ({ items }) => ({
    items: items.filter((item) => item.id !== id),
  }));
}
