import {
  createConversation,
  upsertConversation,
} from '@/entities/conversation';
import {
  addMessage,
  draftMessage,
  loadMessages,
  removeMessage,
  replaceMessage,
} from '@/entities/message';
import type { ModelSelection } from '@/entities/model';
import {
  appendRunText,
  failRun,
  finishRun,
  getRun,
  setRunId,
  setRunToolCall,
  startRun,
} from '@/entities/run';
import { describeError, isAbortError } from '@/shared/api';
import { openChat } from '@/shared/lib/navigation';
import { streamRun } from '../api/run-stream';

interface SendMessageParams {
  /** null — новый чат, он будет создан с моделью `model` и MCP-серверами `mcpConnectionIds` */
  conversationId: string | null;
  text: string;
  model?: ModelSelection;
  mcpConnectionIds?: string[];
}

export async function sendMessage({
  conversationId,
  text,
  model,
  mcpConnectionIds,
}: SendMessageParams) {
  const id =
    conversationId ?? (await createConversationWith(model, mcpConnectionIds));
  if (getRun(id)?.status === 'streaming') return;

  const draft = draftMessage(id, 'user', [{ type: 'text', text }]);
  addMessage(id, draft);
  const signal = startRun(id);
  if (!conversationId) openChat(id);

  const deltas = frameBuffer((chunk) => appendRunText(id, chunk));
  let started = false;
  let completed = false;

  try {
    for await (const event of streamRun(id, text, signal)) {
      switch (event.type) {
        case 'run.started':
          started = true;
          replaceMessage(id, draft.id, event.inputMessage);
          setRunId(id, event.runId);
          break;
        case 'message.delta':
          deltas.push(event.delta);
          break;
        case 'tool_call.started':
        case 'tool_call.completed':
          // Текст до вызова инструмента должен оказаться выше него
          deltas.flush();
          setRunToolCall(id, event.toolCall);
          break;
        case 'run.completed':
          completed = true;
          deltas.cancel();
          addMessage(id, event.outputMessage);
          finishRun(id);
          break;
        case 'run.failed':
          deltas.flush();
          failRun(id, event.error?.message ?? 'Модель не смогла ответить');
          break;
        case 'conversation.updated':
          upsertConversation(event.conversation);
          break;
      }
    }
  } catch (error) {
    deltas.flush();
    if (!started) removeMessage(id, draft.id);
    // Повторить можно, только если сервер не принял сообщение
    if (!isAbortError(error))
      failRun(id, describeError(error), started ? null : text);
  }

  if (completed) return;

  // Остановка или обрыв: сервер сохранил полученную часть ответа
  const run = getRun(id);
  if (run?.status === 'streaming') {
    if (run.content.length > 0)
      addMessage(id, draftMessage(id, 'assistant', run.content));
    finishRun(id);
  }
  void loadMessages(id, { force: true });
}

async function createConversationWith(
  model: ModelSelection | undefined,
  mcpConnectionIds: string[] = [],
): Promise<string> {
  if (!model) throw new Error('Не выбрана модель для нового чата');
  const conversation = await createConversation(model, mcpConnectionIds);
  return conversation.id;
}

/** Копит дельты и отдаёт их пачкой раз в кадр — меньше перерисовок при быстром стриме. */
function frameBuffer(onFlush: (chunk: string) => void) {
  let pending = '';
  let frame = 0;

  const flush = () => {
    cancelAnimationFrame(frame);
    frame = 0;
    if (pending) onFlush(pending);
    pending = '';
  };

  return {
    push(chunk: string) {
      pending += chunk;
      frame ||= requestAnimationFrame(flush);
    },
    flush,
    cancel() {
      cancelAnimationFrame(frame);
      pending = '';
    },
  };
}
