import type { ReactNode } from 'react';
import { LogoMark } from '@/shared/ui/logo';
import { Markdown } from '@/shared/ui/markdown';
import type { MessageContent } from '../model/types';
import styles from './ChatMessage.module.scss';
import { ToolCall } from './ToolCall';

export function UserMessage({ text }: { text: string }) {
  return (
    <article className={styles.message}>
      <span className={styles.author}>Вы</span>
      <p className={styles.userText}>{text}</p>
    </article>
  );
}

interface AssistantMessageProps {
  /** Текст и вызовы инструментов в порядке появления */
  content: MessageContent[];
  streaming?: boolean;
  /** Модель, которая отвечает */
  model?: string;
  /** Действия и статусы под ответом */
  children?: ReactNode;
}

export function AssistantMessage({
  content,
  streaming = false,
  model,
  children,
}: AssistantMessageProps) {
  const lastIndex = content.length - 1;

  return (
    <article className={styles.message} aria-busy={streaming}>
      <header className={styles.assistantHeader}>
        <LogoMark size={20} />
        <span className={styles.assistantName}>DIOS</span>
        {model && <span className={styles.model}>· {model}</span>}
      </header>

      {content.map((part, index) => {
        switch (part.type) {
          case 'text':
            return (
              <Markdown
                key={index}
                streaming={streaming && index === lastIndex}
              >
                {part.text}
              </Markdown>
            );
          case 'tool_call':
            return <ToolCall key={part.callId} call={part} />;
          default:
            return null;
        }
      })}

      {streaming && isWaitingForText(content) && (
        <span
          className={styles.typing}
          role="status"
          aria-label="Ответ формируется"
        >
          <span />
          <span />
          <span />
        </span>
      )}

      {children}
    </article>
  );
}

/** Модель ещё не начала отвечать или думает над результатом инструмента. */
function isWaitingForText(content: MessageContent[]): boolean {
  const last = content.at(-1);
  return !last || (last.type === 'tool_call' && last.status !== 'running');
}
