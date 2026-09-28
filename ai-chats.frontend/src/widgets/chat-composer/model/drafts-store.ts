import { create } from 'zustand';
import { registerStoreReset } from '@/shared/lib/store-reset';

const NEW_CHAT = 'new';

interface DraftsState {
  /** Недописанные сообщения по чатам: переключение между чатами их не теряет */
  drafts: Record<string, string>;
}

export const useDrafts = create<DraftsState>()(() => ({ drafts: {} }));

registerStoreReset(() => useDrafts.setState(useDrafts.getInitialState(), true));

export function useDraft(conversationId: string | null): string {
  return useDrafts(({ drafts }) => drafts[conversationId ?? NEW_CHAT] ?? '');
}

export function setDraft(conversationId: string | null, text: string) {
  useDrafts.setState(({ drafts }) => ({
    drafts: { ...drafts, [conversationId ?? NEW_CHAT]: text },
  }));
}
