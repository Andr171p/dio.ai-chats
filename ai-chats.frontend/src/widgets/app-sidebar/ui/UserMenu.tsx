import { LogOut, Moon, Settings, Sun } from 'lucide-react';
import { displayName, logout, useSession } from '@/entities/session';
import { toggleTheme, useTheme } from '@/shared/lib/theme';
import { Avatar } from '@/shared/ui/avatar';
import { IconButton } from '@/shared/ui/button';
import { Menu, MenuItem, MenuSeparator } from '@/shared/ui/menu';
import { usePopover } from '@/shared/ui/popover';
import styles from './AppSidebar.module.scss';

export function UserMenu({ collapsed }: { collapsed: boolean }) {
  const user = useSession((state) => state.user);
  const dark = useTheme((state) => state.theme === 'dark');
  const menu = usePopover();

  if (!user) return null;
  const name = displayName(user);

  return (
    <div className={styles.user}>
      {collapsed ? (
        <button
          type="button"
          className={styles.avatarButton}
          aria-label={`Меню пользователя ${name}`}
          {...menu.triggerProps}
        >
          <Avatar name={name} />
        </button>
      ) : (
        <>
          <Avatar name={name} />
          <div className={styles.userText}>
            <span className={styles.userName}>{name}</span>
            <span className={styles.userCaption}>Личное пространство</span>
          </div>
          <IconButton
            icon={Settings}
            label="Настройки"
            tooltip={false}
            {...menu.triggerProps}
          />
        </>
      )}

      <Menu
        {...menu.popoverProps}
        placement={collapsed ? 'right-end' : 'top-end'}
      >
        <div className={styles.menuUser}>{user.email}</div>
        <MenuSeparator />
        <MenuItem icon={dark ? Sun : Moon} onSelect={toggleTheme}>
          {dark ? 'Светлая тема' : 'Тёмная тема'}
        </MenuItem>
        <MenuItem icon={LogOut} tone="danger" onSelect={() => void logout()}>
          Выйти
        </MenuItem>
      </Menu>
    </div>
  );
}
