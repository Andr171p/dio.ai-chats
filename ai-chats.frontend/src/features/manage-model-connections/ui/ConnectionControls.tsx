import { Ellipsis, Pencil, Plus, Trash2 } from 'lucide-react';
import { useState } from 'react';
import {
  deleteModelConnection,
  updateModelConnection,
  type ModelConnection,
} from '@/entities/model';
import { describeError } from '@/shared/api';
import { Button, IconButton } from '@/shared/ui/button';
import { Dialog, DialogActions } from '@/shared/ui/dialog';
import { Menu, MenuItem } from '@/shared/ui/menu';
import { Notice } from '@/shared/ui/notice';
import { usePopover } from '@/shared/ui/popover';
import { Switch } from '@/shared/ui/switch';
import { ConnectionForm } from './ConnectionForm';

export function AddConnectionButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button variant="primary" icon={Plus} onClick={() => setOpen(true)}>
        Подключить
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Новое подключение"
        size="md"
        description="Подключение станет доступно всем пользователям DIOS."
      >
        <ConnectionForm onDone={() => setOpen(false)} />
      </Dialog>
    </>
  );
}

/** Включение, изменение и удаление подключения. */
export function ConnectionControls({
  connection,
}: {
  connection: ModelConnection;
}) {
  const menu = usePopover();
  const [dialog, setDialog] = useState<'edit' | 'delete' | null>(null);
  const [toggling, setToggling] = useState(false);
  const close = () => setDialog(null);

  const toggle = async (enabled: boolean) => {
    setToggling(true);
    await updateModelConnection(connection.id, { enabled }).catch(
      () => undefined,
    );
    setToggling(false);
  };

  return (
    <>
      <Switch
        checked={connection.enabled}
        disabled={toggling}
        aria-label={connection.enabled ? 'Отключить' : 'Включить'}
        onChange={toggle}
      />
      <IconButton
        icon={Ellipsis}
        label="Действия с подключением"
        tooltip={false}
        {...menu.triggerProps}
      />
      <Menu {...menu.popoverProps} placement="bottom-end">
        <MenuItem icon={Pencil} onSelect={() => setDialog('edit')}>
          Изменить
        </MenuItem>
        <MenuItem
          icon={Trash2}
          tone="danger"
          onSelect={() => setDialog('delete')}
        >
          Удалить
        </MenuItem>
      </Menu>

      <Dialog
        open={dialog === 'edit'}
        onClose={close}
        title="Изменить подключение"
        size="md"
      >
        <ConnectionForm connection={connection} onDone={close} />
      </Dialog>
      <Dialog
        open={dialog === 'delete'}
        onClose={close}
        title="Удалить подключение?"
        description={`Модели «${connection.name}» станут недоступны во всех чатах.`}
      >
        <DeleteConfirmation connection={connection} onDone={close} />
      </Dialog>
    </>
  );
}

function DeleteConfirmation({
  connection,
  onDone,
}: {
  connection: ModelConnection;
  onDone: () => void;
}) {
  const [error, setError] = useState<string>();
  const [deleting, setDeleting] = useState(false);

  const confirm = async () => {
    setDeleting(true);
    try {
      await deleteModelConnection(connection.id);
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
