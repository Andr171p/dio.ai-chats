import { Check, Copy, GitBranch, RefreshCw, ThumbsUp } from 'lucide-react';
import { useCopyToClipboard } from '@/shared/lib/hooks';
import { IconButton } from '@/shared/ui/button';
import styles from './ConversationThread.module.scss';

export function MessageActions({ text }: { text: string }) {
  const { copied, copy } = useCopyToClipboard();

  return (
    <div className={styles.actions}>
      <IconButton
        icon={copied ? Check : Copy}
        label={copied ? 'Скопировано' : 'Копировать'}
        onClick={() => void copy(text)}
      />
      <IconButton icon={ThumbsUp} label="Хороший ответ" soon />
      <IconButton icon={RefreshCw} label="Сгенерировать заново" soon />
      <IconButton icon={GitBranch} label="Новая ветка" soon />
    </div>
  );
}
