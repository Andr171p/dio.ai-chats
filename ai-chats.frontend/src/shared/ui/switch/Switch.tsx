import type { ComponentProps } from 'react';
import styles from './Switch.module.scss';

interface SwitchProps extends Omit<ComponentProps<'button'>, 'onChange'> {
  checked: boolean;
  onChange: (checked: boolean) => void;
}

export function Switch({ checked, onChange, ...props }: SwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      className={styles.switch}
      onClick={() => onChange(!checked)}
      {...props}
    >
      <span className={styles.thumb} />
    </button>
  );
}
