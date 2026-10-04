import { useState, type FormEvent } from 'react';
import {
  createMcpConnection,
  MCP_AUTH_LABELS,
  mcpConnectionUrl,
  updateMcpConnection,
  type McpConnection,
  type McpConnectionInput,
} from '@/entities/mcp-server';
import { describeError } from '@/shared/api';
import { Button } from '@/shared/ui/button';
import { DialogActions } from '@/shared/ui/dialog';
import { SelectField, TextField } from '@/shared/ui/field';
import { Notice } from '@/shared/ui/notice';
import styles from './McpConnectionForm.module.scss';

type Auth = McpConnectionInput['auth'];

const AUTH_HINTS: Record<Auth, string> = {
  dios: 'Модель действует от имени пользователя и в рамках его прав.',
  none: 'Сервер доступен без входа — подходит для публичных данных.',
};

interface McpConnectionFormProps {
  /** Без подключения — форма создания */
  connection?: McpConnection;
  onDone: () => void;
}

export function McpConnectionForm({
  connection,
  onDone,
}: McpConnectionFormProps) {
  const [name, setName] = useState(connection?.name ?? '');
  const [url, setUrl] = useState(
    (connection && mcpConnectionUrl(connection)) ?? '',
  );
  const [auth, setAuth] = useState<Auth>(
    connection?.auth.type === 'none' ? 'none' : 'dios',
  );
  const [error, setError] = useState<string>();
  const [saving, setSaving] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(undefined);

    try {
      if (connection) {
        await updateMcpConnection(connection.id, { name: name.trim(), url });
      } else {
        await createMcpConnection({ name: name.trim(), url, auth });
      }
      onDone();
    } catch (reason) {
      setError(describeError(reason));
      setSaving(false);
    }
  };

  return (
    <form className={styles.form} onSubmit={submit}>
      {error && <Notice>{error}</Notice>}

      <TextField
        label="Название"
        value={name}
        maxLength={100}
        required
        autoFocus
        placeholder="Например, DIO desk"
        onChange={(event) => setName(event.target.value)}
      />
      <TextField
        label="Адрес MCP-сервера"
        type="url"
        value={url}
        required
        placeholder="http://localhost:8001/mcp/"
        hint="Streamable HTTP endpoint"
        onChange={(event) => setUrl(event.target.value)}
      />
      <SelectField
        label="Авторизация"
        value={auth}
        disabled={Boolean(connection)}
        hint={
          connection ? 'Способ авторизации нельзя изменить' : AUTH_HINTS[auth]
        }
        onChange={(event) => setAuth(event.target.value as Auth)}
      >
        {(Object.keys(AUTH_HINTS) as Auth[]).map((value) => (
          <option key={value} value={value}>
            {MCP_AUTH_LABELS[value]}
          </option>
        ))}
      </SelectField>

      <DialogActions>
        <Button onClick={onDone}>Отмена</Button>
        <Button type="submit" variant="primary" loading={saving}>
          {connection ? 'Сохранить' : 'Подключить'}
        </Button>
      </DialogActions>
    </form>
  );
}
