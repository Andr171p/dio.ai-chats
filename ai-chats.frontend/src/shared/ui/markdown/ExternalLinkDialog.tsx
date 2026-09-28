import type { LinkSafetyModalProps } from 'streamdown';
import { Button } from '../button';
import { Dialog, DialogActions } from '../dialog';
import styles from './Markdown.module.scss';

/** Подтверждение перехода по ссылке из ответа модели. */
export function ExternalLinkDialog({
  isOpen,
  onClose,
  onConfirm,
  url,
}: LinkSafetyModalProps) {
  // Streamdown создаёт модалку для каждой ссылки — держим в DOM только открытую
  if (!isOpen) return null;

  return (
    <Dialog
      open
      onClose={onClose}
      title="Открыть внешнюю ссылку?"
      description="Ссылка ведёт на сторонний сайт. Убедитесь, что доверяете ему."
    >
      <code className={styles.linkPreview}>{url}</code>
      <DialogActions>
        <Button onClick={onClose}>Отмена</Button>
        <Button
          variant="primary"
          onClick={() => {
            onConfirm();
            onClose();
          }}
        >
          Открыть
        </Button>
      </DialogActions>
    </Dialog>
  );
}
