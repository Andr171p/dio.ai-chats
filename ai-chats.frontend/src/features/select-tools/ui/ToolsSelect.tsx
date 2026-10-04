import { Blocks, Check, Plug } from 'lucide-react';
import { useEffect } from 'react';
import { updateConversation, type Conversation } from '@/entities/conversation';
import {
  loadMcpServers,
  setPreferredMcpServers,
  useDefaultMcpServers,
  useMcpServers,
  type AvailableMcpServer,
} from '@/entities/mcp-server';
import type { AvailableModel } from '@/entities/model';
import { navigate } from '@/shared/lib/navigation';
import { Menu, MenuItem, MenuSeparator } from '@/shared/ui/menu';
import { usePopover } from '@/shared/ui/popover';
import { Tooltip } from '@/shared/ui/tooltip';
import styles from './ToolsSelect.module.scss';

interface ToolsSelectProps {
  /** Нет чата — выбор запоминается для нового */
  conversation?: Conversation;
  /** Модель, которая будет отвечать: не каждая умеет вызывать инструменты */
  model?: AvailableModel;
}

/** MCP-серверы, инструменты которых модель может использовать в чате. */
export function ToolsSelect({ conversation, model }: ToolsSelectProps) {
  const servers = useMcpServers((state) => state.items);
  const defaultSelection = useDefaultMcpServers();
  const selected = conversation?.mcpConnectionIds ?? defaultSelection;
  const menu = usePopover();

  useEffect(() => {
    void loadMcpServers();
  }, []);

  if (servers.length === 0) return null;

  const active = servers.filter((server) =>
    selected.includes(server.connectionId),
  );
  const supported = !model || model.capabilities.includes('tools');
  const label = supported && active.length > 0 ? triggerLabel(active) : null;

  const toggle = ({ connectionId }: AvailableMcpServer) => {
    const next = selected.includes(connectionId)
      ? selected.filter((id) => id !== connectionId)
      : [...selected, connectionId];
    setPreferredMcpServers(next);

    if (conversation) {
      // Ошибку откатит стор — переключатель вернётся в прежнее положение
      updateConversation(conversation.id, { mcpConnectionIds: next }).catch(
        () => undefined,
      );
    }
  };

  const trigger = (
    <button
      type="button"
      className={styles.trigger}
      data-active={label !== null || undefined}
      disabled={!supported}
      aria-label={label ? `Инструменты: ${label}` : 'Инструменты'}
      {...menu.triggerProps}
    >
      <Blocks size={16} aria-hidden />
      {label && <span className={styles.label}>{label}</span>}
    </button>
  );

  return (
    <>
      {supported ? (
        trigger
      ) : (
        <Tooltip label="Эта модель не умеет вызывать инструменты">
          {trigger}
        </Tooltip>
      )}

      <Menu
        {...menu.popoverProps}
        placement="top-start"
        className={styles.menu}
        aria-label="Инструменты"
      >
        <div className={styles.heading}>
          <span className={styles.title}>Инструменты</span>
          <span className={styles.subtitle}>
            Модель работает с сервисами от вашего имени и в рамках ваших прав.
          </span>
        </div>
        <MenuSeparator />

        {servers.map((server) => {
          const checked = selected.includes(server.connectionId);
          return (
            <MenuItem
              key={server.connectionId}
              role="menuitemcheckbox"
              aria-checked={checked}
              icon={Blocks}
              selected={checked}
              closeOnSelect={false}
              trailing={
                checked && (
                  <Check size={16} className={styles.check} aria-hidden />
                )
              }
              onSelect={() => toggle(server)}
            >
              {server.name}
            </MenuItem>
          );
        })}

        <MenuSeparator />
        <MenuItem icon={Plug} onSelect={() => navigate({ page: 'models' })}>
          Управлять подключениями
        </MenuItem>
      </Menu>
    </>
  );
}

function triggerLabel(active: AvailableMcpServer[]): string {
  return active.length === 1 ? active[0].name : `Подключено: ${active.length}`;
}
