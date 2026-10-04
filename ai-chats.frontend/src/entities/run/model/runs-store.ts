import { create } from 'zustand';
import type { MessageContent, ToolCallContent } from '@/entities/message';
import { registerStoreReset } from '@/shared/lib/store-reset';
import { appendText, upsertToolCall } from '../lib/content';

/** Генерация ответа модели в конкретном чате. */
export interface Run {
  runId: string | null;
  /** Уже полученная часть ответа: текст и вызовы инструментов */
  content: MessageContent[];
  status: 'streaming' | 'failed';
  error: string | null;
  /** Текст, который можно отправить повторно, если сервер его не принял */
  retryText: string | null;
  controller: AbortController;
}

interface RunsState {
  /** Активные и упавшие запуски по идентификатору чата */
  runs: Record<string, Run>;
}

export const useRuns = create<RunsState>()(() => ({ runs: {} }));

registerStoreReset(() => {
  Object.values(useRuns.getState().runs).forEach((run) =>
    run.controller.abort(),
  );
  useRuns.setState(useRuns.getInitialState(), true);
});

function patchRun(conversationId: string, update: (run: Run) => Partial<Run>) {
  useRuns.setState(({ runs }) => {
    const run = runs[conversationId];
    return run
      ? { runs: { ...runs, [conversationId]: { ...run, ...update(run) } } }
      : {};
  });
}

export function useRun(conversationId: string | null): Run | undefined {
  return useRuns(({ runs }) =>
    conversationId ? runs[conversationId] : undefined,
  );
}

export function getRun(conversationId: string): Run | undefined {
  return useRuns.getState().runs[conversationId];
}

export function startRun(conversationId: string): AbortSignal {
  const controller = new AbortController();
  useRuns.setState(({ runs }) => ({
    runs: {
      ...runs,
      [conversationId]: {
        runId: null,
        content: [],
        status: 'streaming',
        error: null,
        retryText: null,
        controller,
      },
    },
  }));
  return controller.signal;
}

export function setRunId(conversationId: string, runId: string) {
  patchRun(conversationId, () => ({ runId }));
}

export function appendRunText(conversationId: string, delta: string) {
  patchRun(conversationId, ({ content }) => ({
    content: appendText(content, delta),
  }));
}

export function setRunToolCall(conversationId: string, call: ToolCallContent) {
  patchRun(conversationId, ({ content }) => ({
    content: upsertToolCall(content, call),
  }));
}

export function failRun(
  conversationId: string,
  error: string,
  retryText: string | null = null,
) {
  patchRun(conversationId, () => ({ status: 'failed', error, retryText }));
}

export function finishRun(conversationId: string) {
  useRuns.setState(({ runs }) => {
    const { [conversationId]: _, ...rest } = runs;
    return { runs: rest };
  });
}

/** Останавливает генерацию. Сервер сохранит уже полученную часть ответа. */
export function stopRun(conversationId: string) {
  useRuns.getState().runs[conversationId]?.controller.abort();
}
