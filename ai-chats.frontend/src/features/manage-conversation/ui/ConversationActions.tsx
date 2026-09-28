import { Ellipsis, Pencil, Trash2 } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import {
  conversationTitle,
  deleteConversation,
  updateConversation,
  type Conversation,
} from '@/entities/conversation';
import { describeError } from '@/shared/api';
import { openChat, useOpenedConversationId } from '@/shared/lib/navigation';
import { Button, IconButton } from '@/shared/ui/button';
import { Dialog, DialogActions } from '@/shared/ui/dialog';
import { TextField } from '@/shared/ui/field';
import { Menu, MenuItem } from '@/shared/ui/menu';
import { Notice } from '@/shared/ui/notice';
import { usePopover } from '@/shared/ui/popover';

type DialogKind = 'rename' | 'delete' | null;

/** Меню «⋯» чата: переименовать и удалить. */
export function ConversationActions({
  conversation,
}: {
  conversation: Conversation;
}) {
  const menu = usePopover();
  const [dialog, setDialog] = useState<DialogKind>(null);
  const close = () => setDialog(null);

  return (
    <>
      <IconButton
        icon={Ellipsis}
        label="Действия с чатом"
        tooltip={false}
        {...menu.triggerProps}
      />
      <Menu {...menu.popoverProps} placement="bottom-end">
        <MenuItem icon={Pencil} onSelect={() => setDialog('rename')}>
          Переименовать
        </MenuItem>
        <MenuItem
          icon={Trash2}
          tone="danger"
          onSelect={() => setDialog('delete')}
        >
          Удалить
        </MenuItem>
      </Menu>

      <RenameDialog
        conversation={conversation}
        open={dialog === 'rename'}
        onClose={close}
      />
      <DeleteDialog
        conversation={conversation}
        open={dialog === 'delete'}
        onClose={close}
      />
    </>
  );
}

interface DialogProps {
  conversation: Conversation;
  open: boolean;
  onClose: () => void;
}

function RenameDialog({ conversation, open, onClose }: DialogProps) {
  return (
    <Dialog open={open} onClose={onClose} title="Переименовать чат">
      <RenameForm conversation={conversation} onDone={onClose} />
    </Dialog>
  );
}

function RenameForm({
  conversation,
  onDone,
}: {
  conversation: Conversation;
  onDone: () => void;
}) {
  const [title, setTitle] = useState(conversationTitle(conversation));
  const [error, setError] = useState<string>();
  const [saving, setSaving] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const value = title.trim();
    if (!value) {
      setError('Введите название');
      return;
    }

    setSaving(true);
    try {
      await updateConversation(conversation.id, { title: value });
      onDone();
    } catch (reason) {
      setError(describeError(reason));
      setSaving(false);
    }
  };

  return (
    <form onSubmit={submit}>
      <TextField
        label="Название"
        value={title}
        maxLength={200}
        error={error}
        autoFocus
        onChange={(event) => setTitle(event.target.value)}
      />
      <DialogActions>
        <Button onClick={onDone}>Отмена</Button>
        <Button type="submit" variant="primary" loading={saving}>
          Сохранить
        </Button>
      </DialogActions>
    </form>
  );
}

function DeleteDialog({ conversation, open, onClose }: DialogProps) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Удалить чат?"
      description={`«${conversationTitle(conversation)}» и вся переписка будут удалены без возможности восстановления.`}
    >
      <DeleteConfirmation conversation={conversation} onDone={onClose} />
    </Dialog>
  );
}

function DeleteConfirmation({
  conversation,
  onDone,
}: {
  conversation: Conversation;
  onDone: () => void;
}) {
  const openedId = useOpenedConversationId();
  const [error, setError] = useState<string>();
  const [deleting, setDeleting] = useState(false);

  const confirm = async () => {
    setDeleting(true);
    try {
      await deleteConversation(conversation.id);
      if (openedId === conversation.id) openChat(null);
      onDone();
    } catch (reason) {
      setError(describeError(reason));
      setDeleting(false);
    }
  };

  return (
    <>
      {error && <Notice>{error}</Notice>}
      <DialogActions>
        <Button onClick={onDone}>Отмена</Button>
        <Button
          variant="primary"
          icon={Trash2}
          loading={deleting}
          onClick={confirm}
        >
          Удалить
        </Button>
      </DialogActions>
    </>
  );
}
