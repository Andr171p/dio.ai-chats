import { Ban, Check, Hourglass, X, type LucideIcon } from 'lucide-react';
import { Spinner } from '@/shared/ui/spinner';
import type { ToolCallContent, ToolCallStatus } from '../model/types';
import styles from './ToolCall.module.scss';

const STATUS: Record<
  Exclude<ToolCallStatus, 'running'>,
  { icon: LucideIcon; label: string }
> = {
  waiting_approval: { icon: Hourglass, label: 'ожидает подтверждения' },
  completed: { icon: Check, label: 'выполнено' },
  failed: { icon: X, label: 'ошибка' },
  cancelled: { icon: Ban, label: 'отменено' },
};

/** Вызов инструмента в ответе: что модель сделала и чем это закончилось. */
export function ToolCall({ call }: { call: ToolCallContent }) {
  const name = call.title ?? call.name;
  const status = call.status === 'running' ? null : STATUS[call.status];

  return (
    <div className={styles.call} data-status={call.status} title={call.name}>
      {status ? (
        <status.icon size={14} className={styles.icon} aria-hidden />
      ) : (
        <Spinner size={14} />
      )}
      <span className={styles.name}>{name}</span>
      <span className={styles.status}>
        {status ? `· ${status.label}` : '· выполняется…'}
      </span>
    </div>
  );
}
