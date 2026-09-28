import type { ReactNode } from 'react';
import { LogoMark } from '@/shared/ui/logo';
import { Markdown } from '@/shared/ui/markdown';
import styles from './ChatMessage.module.scss';

export function UserMessage({ text }: { text: string }) {
  return (
    <article className={styles.message}>
      <span className={styles.author}>Вы</span>
      <p className={styles.userText}>{text}</p>
    </article>
  );
}

interface AssistantMessageProps {
  text: string;
  streaming?: boolean;
  /** Модель, которая отвечает */
  model?: string;
  /** Действия и статусы под ответом */
  children?: ReactNode;
}

export function AssistantMessage({
  text,
  streaming = false,
  model,
  children,
}: AssistantMessageProps) {
  return (
    <article className={styles.message} aria-busy={streaming}>
      <header className={styles.assistantHeader}>
        <LogoMark size={20} />
        <span className={styles.assistantName}>DIOS</span>
        {model && <span className={styles.model}>· {model}</span>}
      </header>

      {text ? (
        <Markdown streaming={streaming}>{text}</Markdown>
      ) : (
        streaming && (
          <span
            className={styles.typing}
            role="status"
            aria-label="Ответ формируется"
          >
            <span />
            <span />
            <span />
          </span>
        )
      )}

      {children}
    </article>
  );
}
