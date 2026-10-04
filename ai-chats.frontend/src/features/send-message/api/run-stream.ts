import type { Conversation } from '@/entities/conversation';
import type { Message, ToolCallContent } from '@/entities/message';
import { chatsApi } from '@/shared/api';

export type RunEvent =
  | { type: 'run.started'; runId: string; inputMessage: Message }
  | { type: 'message.delta'; runId: string; delta: string }
  | {
      type: 'tool_call.started' | 'tool_call.completed';
      runId: string;
      toolCall: ToolCallContent;
    }
  | {
      type: 'run.completed';
      runId: string;
      outputMessage: Message;
      finishReason: string;
    }
  | {
      type: 'run.failed';
      runId?: string;
      error?: { code?: string; message?: string };
    }
  | { type: 'conversation.updated'; conversation: Conversation };

/**
 * RunStream: отправляет сообщение и отдаёт события запуска модели.
 * Прерывание `signal` останавливает генерацию на сервере.
 */
export async function* streamRun(
  conversationId: string,
  text: string,
  signal: AbortSignal,
): AsyncGenerator<RunEvent> {
  const events = chatsApi.stream(
    `/api/v1/conversations/${conversationId}/messages`,
    {
      body: { content: [{ type: 'text', text }] },
      signal,
    },
  );

  for await (const { data } of events) {
    yield JSON.parse(data) as RunEvent;
  }
}
