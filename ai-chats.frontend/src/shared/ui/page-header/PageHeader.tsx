import type { ReactNode } from 'react';
import styles from './PageHeader.module.scss';

interface PageHeaderProps {
  /** Хлебные крошки, последняя — текущая страница */
  breadcrumbs: string[];
  actions?: ReactNode;
}

export function PageHeader({ breadcrumbs, actions }: PageHeaderProps) {
  return (
    <header className={styles.header}>
      <nav aria-label="Вы здесь" className={styles.breadcrumbs}>
        <ol>
          {breadcrumbs.map((crumb, index) => (
            <li
              key={index}
              aria-current={
                index === breadcrumbs.length - 1 ? 'page' : undefined
              }
            >
              {crumb}
            </li>
          ))}
        </ol>
      </nav>
      {actions && <div className={styles.actions}>{actions}</div>}
    </header>
  );
}
