import clsx from 'clsx';
import { Folder, PanelLeft, Plug, Plus } from 'lucide-react';
import { SearchConversations } from '@/features/search-conversations';
import { navigate, openChat, useNavigation } from '@/shared/lib/navigation';
import { Button, IconButton } from '@/shared/ui/button';
import { Logo, LogoMark } from '@/shared/ui/logo';
import { NavItem } from '@/shared/ui/nav-item';
import { Tooltip } from '@/shared/ui/tooltip';
import { toggleSidebar, useSidebar } from '../model/sidebar-store';
import styles from './AppSidebar.module.scss';
import { ConversationList } from './ConversationList';
import { UserMenu } from './UserMenu';

export function AppSidebar() {
  const collapsed = useSidebar((state) => state.collapsed);
  const onModelsPage = useNavigation(({ route }) => route.page === 'models');

  return (
    <aside
      className={clsx(styles.sidebar, collapsed && styles.collapsed)}
      aria-label="Навигация"
    >
      <div className={styles.top}>
        {collapsed ? (
          <Tooltip label="Развернуть панель" placement="right-start">
            <button
              type="button"
              className={styles.logoButton}
              aria-label="Развернуть панель"
              onClick={toggleSidebar}
            >
              <LogoMark size={22} />
            </button>
          </Tooltip>
        ) : (
          <>
            <Logo />
            <IconButton
              icon={PanelLeft}
              label="Свернуть панель"
              onClick={toggleSidebar}
            />
          </>
        )}
      </div>

      <div className={styles.actions}>
        {collapsed ? (
          <IconButton
            icon={Plus}
            label="Новый чат"
            variant="primary"
            size="md"
            tooltipPlacement="right-start"
            onClick={() => openChat(null)}
          />
        ) : (
          <Button
            variant="primary"
            icon={Plus}
            block
            onClick={() => openChat(null)}
          >
            Новый чат
          </Button>
        )}
        <SearchConversations collapsed={collapsed} />
      </div>

      <nav className={styles.scroll} aria-label="Чаты">
        {collapsed ? (
          <NavItem icon={Folder} label="Проекты" collapsed soon />
        ) : (
          <>
            <section className={styles.section} aria-label="Проекты">
              <div className={styles.sectionHeader}>
                <h2 className={styles.sectionTitle}>Проекты</h2>
                <IconButton icon={Plus} label="Новый проект" soon />
              </div>
              <NavItem icon={Folder} label="Проекты" soon />
            </section>
            <ConversationList />
          </>
        )}
      </nav>

      <div className={styles.bottom}>
        <NavItem
          icon={Plug}
          label="Модели и подключения"
          collapsed={collapsed}
          active={onModelsPage}
          onClick={() => navigate({ page: 'models' })}
        />
        <UserMenu collapsed={collapsed} />
      </div>
    </aside>
  );
}
