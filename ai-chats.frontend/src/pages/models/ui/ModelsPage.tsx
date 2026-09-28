import {
  Blocks,
  KeyRound,
  Monitor,
  Server,
  type LucideIcon,
} from 'lucide-react';
import { useEffect } from 'react';
import {
  ConnectionCard,
  loadModelConnections,
  useModelConnections,
} from '@/entities/model';
import { isAdmin, useSession } from '@/entities/session';
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
            <h2 className={styles.sectionTitle}>MCP-серверы</h2>
            <SoonCard
              icon={Blocks}
              title="DIO desk"
              text="Задачи и заявки прямо в чате — подключение в пару кликов."
            />
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
