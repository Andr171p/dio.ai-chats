import { Plus, Trash2 } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import {
  createModelConnection,
  PROTOCOL_LABELS,
  updateModelConnection,
  type ModelConnection,
  type ModelProtocol,
  type ModelSpec,
} from '@/entities/model';
import { describeError } from '@/shared/api';
import { Button, IconButton } from '@/shared/ui/button';
import { DialogActions } from '@/shared/ui/dialog';
import { SelectField, TextField } from '@/shared/ui/field';
import { Notice } from '@/shared/ui/notice';
import styles from './ConnectionForm.module.scss';

interface ModelRow {
  key: string;
  spec: ModelSpec;
}

const newRow = (spec?: ModelSpec): ModelRow => ({
  key: crypto.randomUUID(),
  spec: spec ?? {
    id: '',
    provider: '',
    inputModalities: ['text'],
    outputModalities: ['text'],
    contextWindow: 128_000,
    capabilities: [],
  },
});

interface ConnectionFormProps {
  /** Без подключения — форма создания */
  connection?: ModelConnection;
  onDone: () => void;
}

export function ConnectionForm({ connection, onDone }: ConnectionFormProps) {
  const route =
    connection?.route.type === 'system' ? connection.route : undefined;

  const [name, setName] = useState(connection?.name ?? '');
  const [protocol, setProtocol] = useState<ModelProtocol>(
    connection?.protocol ?? 'openai_chat_completions',
  );
  const [baseUrl, setBaseUrl] = useState(route?.baseUrl ?? '');
  const [apiKey, setApiKey] = useState('');
  const [rows, setRows] = useState<ModelRow[]>(() =>
    connection ? connection.models.map((spec) => newRow(spec)) : [newRow()],
  );
  const [error, setError] = useState<string>();
  const [saving, setSaving] = useState(false);

  const updateRow = (key: string, patch: Partial<ModelSpec>) =>
    setRows((current) =>
      current.map((row) =>
        row.key === key ? { ...row, spec: { ...row.spec, ...patch } } : row,
      ),
    );

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(undefined);

    const models = rows.map(({ spec }) => ({
      ...spec,
      id: spec.id.trim(),
      provider: spec.provider.trim(),
    }));
    try {
      if (connection) {
        await updateModelConnection(connection.id, {
          name: name.trim(),
          baseUrl,
          apiKey,
          models,
        });
      } else {
        await createModelConnection({
          name: name.trim(),
          protocol,
          baseUrl,
          apiKey,
          models,
        });
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

      <div className={styles.grid}>
        <TextField
          label="Название"
          value={name}
          maxLength={100}
          required
          autoFocus
          placeholder="Например, OpenAI"
          onChange={(event) => setName(event.target.value)}
        />
        <SelectField
          label="Протокол"
          value={protocol}
          disabled={Boolean(connection)}
          hint={connection ? 'Протокол нельзя изменить' : undefined}
          onChange={(event) => setProtocol(event.target.value as ModelProtocol)}
        >
          {Object.entries(PROTOCOL_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </SelectField>
      </div>

      <TextField
        label="Базовый URL"
        type="url"
        value={baseUrl}
        required
        placeholder="https://api.openai.com/v1"
        onChange={(event) => setBaseUrl(event.target.value)}
      />
      <TextField
        label="API-ключ"
        type="password"
        value={apiKey}
        autoComplete="off"
        placeholder={
          route?.hasApiKey ? '••••••••' : 'Не требуется для локальных моделей'
        }
        hint={
          route?.hasApiKey
            ? 'Ключ сохранён на сервере. Оставьте поле пустым, чтобы не менять его.'
            : undefined
        }
        onChange={(event) => setApiKey(event.target.value)}
      />

      <fieldset className={styles.models}>
        <legend className={styles.legend}>Модели</legend>
        {rows.map(({ key, spec }) => (
          <div key={key} className={styles.modelRow}>
            <TextField
              label="ID модели"
              value={spec.id}
              required
              placeholder="gpt-4.1"
              onChange={(event) => updateRow(key, { id: event.target.value })}
            />
            <TextField
              label="Провайдер"
              value={spec.provider}
              required
              placeholder="openai"
              onChange={(event) =>
                updateRow(key, { provider: event.target.value })
              }
            />
            <TextField
              label="Контекст, токенов"
              type="number"
              min={1}
              value={spec.contextWindow}
              required
              onChange={(event) =>
                updateRow(key, { contextWindow: Number(event.target.value) })
              }
            />
            <IconButton
              icon={Trash2}
              label="Убрать модель"
              className={styles.removeModel}
              disabled={rows.length === 1}
              onClick={() =>
                setRows((current) => current.filter((row) => row.key !== key))
              }
            />
          </div>
        ))}
        <Button
          size="sm"
          variant="ghost"
          icon={Plus}
          onClick={() => setRows((current) => [...current, newRow()])}
        >
          Добавить модель
        </Button>
      </fieldset>

      <DialogActions>
        <Button onClick={onDone}>Отмена</Button>
        <Button type="submit" variant="primary" loading={saving}>
          {connection ? 'Сохранить' : 'Подключить'}
        </Button>
      </DialogActions>
    </form>
  );
}
