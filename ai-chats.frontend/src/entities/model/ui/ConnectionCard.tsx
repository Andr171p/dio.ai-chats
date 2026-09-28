import { Plug } from 'lucide-react';
import type { ReactNode } from 'react';
import { Badge } from '@/shared/ui/badge';
import { formatTokens, PROTOCOL_LABELS } from '../lib/model';
import type { ModelConnection } from '../model/types';
import styles from './ConnectionCard.module.scss';

interface ConnectionCardProps {
  connection: ModelConnection;
  actions?: ReactNode;
}

export function ConnectionCard({ connection, actions }: ConnectionCardProps) {
  const { route } = connection;

  return (
    <article
      className={styles.card}
      data-disabled={!connection.enabled || undefined}
    >
      <div className={styles.icon}>
        <Plug size={18} aria-hidden />
      </div>

      <div className={styles.body}>
        <header className={styles.header}>
          <h3 className={styles.name}>{connection.name}</h3>
          {!connection.enabled && <Badge>Отключено</Badge>}
          {route.type === 'system' && route.hasApiKey && (
            <Badge tone="success">Ключ сохранён</Badge>
          )}
        </header>
        <p className={styles.meta}>
          {PROTOCOL_LABELS[connection.protocol]}
          {route.type === 'system' && ` · ${route.baseUrl}`}
        </p>
        <ul className={styles.models} aria-label="Модели">
          {connection.models.map((model) => (
            <li key={model.id} className={styles.model}>
              {model.id}
              <span className={styles.context}>
                {formatTokens(model.contextWindow)}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {actions && <div className={styles.actions}>{actions}</div>}
    </article>
  );
}
