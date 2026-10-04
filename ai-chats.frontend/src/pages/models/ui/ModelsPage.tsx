import { KeyRound, Monitor, Server, type LucideIcon } from 'lucide-react';
import { useEffect, type ReactNode } from 'react';
import {
  loadMcpConnections,
  loadMcpServers,
  MCP_AUTH_LABELS,
  mcpConnectionUrl,
  McpServerCard,
  useMcpConnections,
  useMcpServers,
} from '@/entities/mcp-server';
import {
  ConnectionCard,
  loadModelConnections,
  useModelConnections,
} from '@/entities/model';
import { isAdmin, useSession } from '@/entities/session';
import {
  AddMcpServerButton,
  McpConnectionControls,
} from '@/features/manage-mcp-connections';
import {
  AddConnectionButton,
  ConnectionControls,
} from '@/features/manage-model-connections';
import { ThemeToggle } from '@/features/toggle-theme';
import { Badge } from '@/shared/ui/badge';
import { Button, SOON_LABEL } from '@/shared/ui/button';
import { Notice } from '@/shared/ui/notice';
import { PageHeader } from '@/shared/ui/page-header';
import { Spinner } from '@/shared/ui/spinner';
import styles from './ModelsPage.module.scss';

export function ModelsPage() {
  const { items, status, error } = useModelConnections();
  const admin = useSession((state) => isAdmin(state.user));

  useEffect(() => {
    void loadModelConnections();
  }, []);

  return (
    <div className={styles.page}>
      <PageHeader
        breadcrumbs={['Настройки', 'Модели и подключения']}
        actions={<ThemeToggle />}
      />

      <div className={styles.scroll}>
        <div className={styles.content}>
          <header className={styles.intro}>
            <div>
              <h1 className={styles.title}>Модели и подключения</h1>
              <p className={styles.subtitle}>
                Откуда DIOS берёт модели и инструменты для ваших чатов.
              </p>
            </div>
            {admin && <AddConnectionButton />}
          </header>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Подключения DIOS</h2>
            {status === 'loading' && items.length === 0 && (
              <Spinner label="Загружаем подключения" />
            )}
            {status === 'error' && (
              <Notice
                action={
                  <Button size="sm" onClick={() => void loadModelConnections()}>
                    Повторить
                  </Button>
                }
              >
                {error}
              </Notice>
            )}
            {status === 'ready' && items.length === 0 && (
              <p className={styles.empty}>
                {admin
                  ? 'Подключите первый источник моделей.'
                  : 'Администратор ещё не подключил модели.'}
              </p>
            )}
            {items.map((connection) => (
              <ConnectionCard
                key={connection.id}
                connection={connection}
                actions={
                  admin && <ConnectionControls connection={connection} />
                }
              />
            ))}
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Ваши модели</h2>
            <SoonCard
              icon={KeyRound}
              title="Личный аккаунт или API-ключ"
              text="Подписка ChatGPT, Claude или свой ключ. Запросы идут напрямую из браузера, ключи хранятся только у вас."
            />
            <SoonCard
              icon={Monitor}
              title="Локальные модели"
              text="Модели на вашем компьютере или во внутренней сети, в том числе доступные только через VPN."
            />
          </section>

          <section className={styles.section}>
            <header className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>MCP-серверы</h2>
              {admin && <AddMcpServerButton />}
            </header>
            {admin ? <AdminMcpServers /> : <AvailableMcpServers />}
            <SoonCard
              icon={Server}
              title="Свои MCP-серверы"
              text="Инструменты и данные вашей команды."
            />
          </section>
        </div>
      </div>
    </div>
  );
}

/** Все подключения MCP-серверов с управлением. */
function AdminMcpServers() {
  const { items, status, error } = useMcpConnections();

  useEffect(() => {
    void loadMcpConnections();
  }, []);

  return (
    <ListState
      status={status}
      error={error}
      empty={items.length === 0}
      emptyText="Подключите DIO desk или другой MCP-сервер."
      onRetry={loadMcpConnections}
    >
      {items.map((connection) => (
        <McpServerCard
          key={connection.id}
          connectionId={connection.id}
          name={connection.name}
          enabled={connection.enabled}
          meta={[
            mcpConnectionUrl(connection),
            MCP_AUTH_LABELS[connection.auth.type],
          ]
            .filter(Boolean)
            .join(' · ')}
          actions={<McpConnectionControls connection={connection} />}
        />
      ))}
    </ListState>
  );
}

/** MCP-серверы, которые пользователь может подключить к чату. */
function AvailableMcpServers() {
  const { items, status, error } = useMcpServers();

  useEffect(() => {
    void loadMcpServers();
  }, []);

  return (
    <ListState
      status={status}
      error={error}
      empty={items.length === 0}
      emptyText="Администратор ещё не подключил MCP-серверы."
      onRetry={() => loadMcpServers({ force: true })}
    >
      {items.map((server) => (
        <McpServerCard
          key={server.connectionId}
          connectionId={server.connectionId}
          name={server.name}
          meta="Подключается к чату кнопкой «Инструменты» под полем ввода"
        />
      ))}
    </ListState>
  );
}

function ListState({
  status,
  error,
  empty,
  emptyText,
  onRetry,
  children,
}: {
  status: 'idle' | 'loading' | 'ready' | 'error';
  error: string | null;
  empty: boolean;
  emptyText: string;
  onRetry: () => Promise<void>;
  children: ReactNode;
}) {
  return (
    <>
      {status === 'loading' && empty && <Spinner label="Загружаем" />}
      {status === 'error' && (
        <Notice
          action={
            <Button size="sm" onClick={() => void onRetry()}>
              Повторить
            </Button>
          }
        >
          {error}
        </Notice>
      )}
      {status === 'ready' && empty && (
        <p className={styles.empty}>{emptyText}</p>
      )}
      {children}
    </>
  );
}

function SoonCard({
  icon: Icon,
  title,
  text,
}: {
  icon: LucideIcon;
  title: string;
  text: string;
}) {
  return (
    <article className={styles.soonCard} aria-disabled>
      <div className={styles.soonIcon}>
        <Icon size={18} aria-hidden />
      </div>
      <div className={styles.soonBody}>
        <h3 className={styles.soonTitle}>{title}</h3>
        <p className={styles.soonText}>{text}</p>
      </div>
      <Badge>{SOON_LABEL}</Badge>
    </article>
  );
}
