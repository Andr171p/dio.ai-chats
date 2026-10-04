import type { MessageContent, ToolCallContent } from '@/entities/message';

/** Дописывает фрагмент ответа: продолжает последний текстовый блок или начинает новый после инструмента. */
export function appendText(
  content: MessageContent[],
  delta: string,
): MessageContent[] {
  const last = content.at(-1);
  return last?.type === 'text'
    ? [...content.slice(0, -1), { ...last, text: last.text + delta }]
    : [...content, { type: 'text', text: delta }];
}

/** Добавляет вызов инструмента или обновляет его статус. */
export function upsertToolCall(
  content: MessageContent[],
  call: ToolCallContent,
): MessageContent[] {
  const exists = content.some(
    (part) => part.type === 'tool_call' && part.callId === call.callId,
  );
  return exists
    ? content.map((part) =>
        part.type === 'tool_call' && part.callId === call.callId ? call : part,
      )
    : [...content, call];
}
