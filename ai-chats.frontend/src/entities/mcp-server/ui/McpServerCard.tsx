import { Blocks } from 'lucide-react';
import { useEffect, type ReactNode } from 'react';
import { Badge } from '@/shared/ui/badge';
import { Spinner } from '@/shared/ui/spinner';
import { loadMcpTools, useMcpServers } from '../model/mcp-servers-store';
import styles from './McpServerCard.module.scss';

/** Сколько инструментов показывать до «ещё N» */
const VISIBLE_TOOLS = 12;

interface McpServerCardProps {
  connectionId: string;
  name: string;
  /** Строка под названием: адрес, способ входа */
  meta?: ReactNode;
  enabled?: boolean;
  actions?: ReactNode;
}

export function McpServerCard({
  connectionId,
  name,
  meta,
  enabled = true,
  actions,
}: McpServerCardProps) {
  return (
    <article className={styles.card} data-disabled={!enabled || undefined}>
      <div className={styles.icon}>
        <Blocks size={18} aria-hidden />
      </div>

      <div className={styles.body}>
        <header className={styles.header}>
          <h3 className={styles.name}>{name}</h3>
          {!enabled && <Badge>Отключено</Badge>}
        </header>
        {meta && <p className={styles.meta}>{meta}</p>}
        {enabled && <ToolList connectionId={connectionId} />}
      </div>

      {actions && <div className={styles.actions}>{actions}</div>}
    </article>
  );
}

function ToolList({ connectionId }: { connectionId: string }) {
  const tools = useMcpServers((state) => state.tools[connectionId]);

  useEffect(() => {
    void loadMcpTools(connectionId);
  }, [connectionId]);

  if (!tools || tools.status === 'loading') {
    return (
      <p className={styles.status}>
        <Spinner size={14} /> Загружаем инструменты…
      </p>
    );
  }

  if (tools.status === 'error') {
    return <p className={styles.status}>Сервер не отвечает</p>;
  }

  const hidden = tools.items.length - VISIBLE_TOOLS;

  return (
    <ul className={styles.tools} aria-label="Инструменты">
      {tools.items.slice(0, VISIBLE_TOOLS).map((tool) => (
        <li
          key={tool.name}
          className={styles.tool}
          title={tool.description ?? undefined}
        >
          {tool.name}
        </li>
      ))}
      {hidden > 0 && <li className={styles.more}>и ещё {hidden}</li>}
    </ul>
  );
}
