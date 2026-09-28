import clsx from 'clsx';
import type { LucideIcon } from 'lucide-react';
import type { ComponentProps, ReactNode } from 'react';
import { Badge } from '../badge';
import { SOON_LABEL } from '../button';
import { Tooltip } from '../tooltip';
import styles from './NavItem.module.scss';

interface NavItemProps extends Omit<ComponentProps<'button'>, 'children'> {
  icon: LucideIcon;
  label: string;
  active?: boolean;
  /** Только иконка — для свёрнутого сайдбара */
  collapsed?: boolean;
  soon?: boolean;
  /** Подсказка справа, например сочетание клавиш */
  meta?: ReactNode;
  /** Действия, которые появляются при наведении */
  actions?: ReactNode;
}

/** Строка навигации сайдбара. */
export function NavItem({
  icon: Icon,
  label,
  active = false,
  collapsed = false,
  soon = false,
  meta,
  actions,
  className,
  onClick,
  ...props
}: NavItemProps) {
  const button = (
    <button
      type="button"
      className={styles.main}
      aria-current={active ? 'page' : undefined}
      aria-disabled={soon || undefined}
      aria-label={collapsed ? label : undefined}
      onClick={soon ? undefined : onClick}
      {...props}
    >
      <Icon size={16} className={styles.icon} aria-hidden />
      {!collapsed && <span className={styles.label}>{label}</span>}
      {!collapsed && (soon ? <Badge>{SOON_LABEL}</Badge> : meta)}
    </button>
  );

  return (
    <div
      className={clsx(
        styles.item,
        active && styles.active,
        collapsed && styles.collapsed,
        className,
      )}
    >
      {collapsed ? (
        <Tooltip
          label={soon ? `${label} · ${SOON_LABEL.toLowerCase()}` : label}
          placement="right-start"
        >
          {button}
        </Tooltip>
      ) : (
        button
      )}
      {!collapsed && actions && <div className={styles.actions}>{actions}</div>}
    </div>
  );
}
