import type { ModelSelection } from '@/entities/model';

export interface ConversationTitle {
  label: string;
  /** auto — сгенерирован по теме диалога, manual — задан пользователем */
  source: 'auto' | 'manual';
}

export interface Conversation {
  id: string;
  title: ConversationTitle | null;
  model: ModelSelection;
  currentThreadId: string;
  createdAt: string;
  updatedAt: string;
}

export interface ConversationPatch {
  title?: string;
  model?: ModelSelection;
}

export const NEW_CHAT_TITLE = 'Новый чат';

export function conversationTitle(
  conversation: Conversation | undefined,
): string {
  return conversation?.title?.label ?? NEW_CHAT_TITLE;
}
