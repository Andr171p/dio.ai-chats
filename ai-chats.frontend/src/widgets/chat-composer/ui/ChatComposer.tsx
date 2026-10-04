import clsx from 'clsx';
import { ArrowUp, Mic, Plus, Square } from 'lucide-react';
import {
  useLayoutEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type SyntheticEvent,
} from 'react';
import type { Conversation } from '@/entities/conversation';
import { useDefaultMcpServers } from '@/entities/mcp-server';
import { findModel, useDefaultModel, useModels } from '@/entities/model';
import { stopRun, useRun } from '@/entities/run';
import { ModelSelect } from '@/features/select-model';
import { ToolsSelect } from '@/features/select-tools';
import { sendMessage } from '@/features/send-message';
import { describeError } from '@/shared/api';
import { IconButton } from '@/shared/ui/button';
import { Notice } from '@/shared/ui/notice';
import { setDraft, useDraft } from '../model/drafts-store';
import styles from './ChatComposer.module.scss';

export const COMPOSER_INPUT_ID = 'chat-composer-input';

interface ChatComposerProps {
  /** null — новый чат */
  conversationId: string | null;
  conversation?: Conversation;
  /** Показывать дисклеймер под полем ввода */
  disclaimer?: boolean;
}

export function Disclaimer() {
  return (
    <p className={styles.disclaimer}>
      DIOS AI может ошибаться. Проверяйте важную информацию.
    </p>
  );
}

export function ChatComposer({
  conversationId,
  conversation,
  disclaimer = true,
}: ChatComposerProps) {
  const draft = useDraft(conversationId);
  const run = useRun(conversationId);
  const defaultModel = useDefaultModel();
  const defaultMcpServers = useDefaultMcpServers();
  const model =
    useModels(({ items }) =>
      conversation ? findModel(items, conversation.model) : undefined,
    ) ?? defaultModel;
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [error, setError] = useState<string>();

  const generating = run?.status === 'streaming';
  const canSend =
    draft.trim().length > 0 &&
    !generating &&
    (conversationId !== null || defaultModel !== undefined);

  // Поле растёт вместе с текстом до max-height из стилей
  useLayoutEffect(() => {
    const input = inputRef.current;
    if (!input) return;
    input.style.height = 'auto';
    input.style.height = `${input.scrollHeight}px`;
  }, [draft]);

  const submit = (event: SyntheticEvent) => {
    event.preventDefault();
    if (!canSend) return;

    const text = draft.trim();
    setDraft(conversationId, '');
    setError(undefined);

    sendMessage({
      conversationId,
      text,
      model: defaultModel,
      mcpConnectionIds: defaultMcpServers,
    }).catch((reason: unknown) => {
      setDraft(conversationId, text);
      setError(describeError(reason));
    });
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (
      event.key === 'Enter' &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    )
      submit(event);
  };

  const placeholder = generating
    ? 'Ответ формируется…'
    : conversationId
      ? 'Уточните детали или задайте следующий вопрос…'
      : 'Спросите или опишите задачу…';

  return (
    <div className={styles.wrapper}>
      {error && <Notice>{error}</Notice>}

      <form
        className={clsx(styles.composer, generating && styles.busy)}
        onSubmit={submit}
      >
        <textarea
          ref={inputRef}
          id={COMPOSER_INPUT_ID}
          className={styles.input}
          value={draft}
          placeholder={placeholder}
          aria-label="Сообщение"
          rows={2}
          autoFocus
          onChange={(event) => setDraft(conversationId, event.target.value)}
          onKeyDown={onKeyDown}
        />

        <div className={styles.toolbar}>
          <IconButton icon={Plus} label="Прикрепить файл" soon />
          <ToolsSelect conversation={conversation} model={model} />
          <div className={styles.spacer} />
          <ModelSelect conversation={conversation} />
          <IconButton icon={Mic} label="Голосовой ввод" soon />
          {generating && conversationId ? (
            <IconButton
              icon={Square}
              label="Остановить"
              variant="primary"
              onClick={() => stopRun(conversationId)}
            />
          ) : (
            <IconButton
              icon={ArrowUp}
              label="Отправить"
              variant="primary"
              type="submit"
              disabled={!canSend}
            />
          )}
        </div>
      </form>

      {disclaimer && <Disclaimer />}
    </div>
  );
}
