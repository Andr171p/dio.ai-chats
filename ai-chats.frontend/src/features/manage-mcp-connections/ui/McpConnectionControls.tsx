import { Ellipsis, Pencil, Plus, Trash2 } from 'lucide-react';
import { useState } from 'react';
import {
  deleteMcpConnection,
  updateMcpConnection,
  type McpConnection,
} from '@/entities/mcp-server';
import { describeError } from '@/shared/api';
import { Button, IconButton } from '@/shared/ui/button';
import { Dialog, DialogActions } from '@/shared/ui/dialog';
import { Menu, MenuItem } from '@/shared/ui/menu';
import { Notice } from '@/shared/ui/notice';
import { usePopover } from '@/shared/ui/popover';
import { Switch } from '@/shared/ui/switch';
import { McpConnectionForm } from './McpConnectionForm';

export function AddMcpServerButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button icon={Plus} onClick={() => setOpen(true)}>
        Подключить MCP
      </Button>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Новый MCP-сервер"
        size="md"
        description="Пользователи смогут подключать его инструменты к своим чатам."
      >
        <McpConnectionForm onDone={() => setOpen(false)} />
      </Dialog>
    </>
  );
}

/** Включение, изменение и удаление MCP-сервера. */
export function McpConnectionControls({
  connection,
}: {
  connection: McpConnection;
}) {
  const menu = usePopover();
  const [dialog, setDialog] = useState<'edit' | 'delete' | null>(null);
  const [toggling, setToggling] = useState(false);
  const close = () => setDialog(null);

  const toggle = async (enabled: boolean) => {
    setToggling(true);
    await updateMcpConnection(connection.id, { enabled }).catch(
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
        label="Действия с MCP-сервером"
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
        title="Изменить MCP-сервер"
        size="md"
      >
        <McpConnectionForm connection={connection} onDone={close} />
      </Dialog>
      <Dialog
        open={dialog === 'delete'}
        onClose={close}
        title="Удалить MCP-сервер?"
        description={`Инструменты «${connection.name}» пропадут из всех чатов.`}
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
  connection: McpConnection;
  onDone: () => void;
}) {
  const [error, setError] = useState<string>();
  const [deleting, setDeleting] = useState(false);

  const confirm = async () => {
    setDeleting(true);
    try {
      await deleteMcpConnection(connection.id);
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
