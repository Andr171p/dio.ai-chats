import clsx from 'clsx';
import { useId, type ComponentProps, type ReactNode } from 'react';
import styles from './Field.module.scss';

interface FieldProps {
  label: string;
  hint?: ReactNode;
  error?: string;
  className?: string;
  children: (control: {
    id: string;
    'aria-invalid'?: boolean;
    'aria-describedby'?: string;
  }) => ReactNode;
}

function Field({ label, hint, error, className, children }: FieldProps) {
  const id = useId();
  const messageId = `${id}-message`;
  const message = error ?? hint;

  return (
    <div className={clsx(styles.field, className)}>
      <label htmlFor={id} className={styles.label}>
        {label}
      </label>
      {children({
        id,
        'aria-invalid': error ? true : undefined,
        'aria-describedby': message ? messageId : undefined,
      })}
      {message && (
        <span id={messageId} className={error ? styles.error : styles.hint}>
          {message}
        </span>
      )}
    </div>
  );
}

type FieldOwnProps = Pick<FieldProps, 'label' | 'hint' | 'error'>;

export function TextField({
  label,
  hint,
  error,
  className,
  ...props
}: FieldOwnProps & ComponentProps<'input'>) {
  return (
    <Field label={label} hint={hint} error={error} className={className}>
      {(control) => (
        <input className={styles.control} {...control} {...props} />
      )}
    </Field>
  );
}

export function SelectField({
  label,
  hint,
  error,
  className,
  ...props
}: FieldOwnProps & ComponentProps<'select'>) {
  return (
    <Field label={label} hint={hint} error={error} className={className}>
      {(control) => (
        <select
          className={clsx(styles.control, styles.select)}
          {...control}
          {...props}
        />
      )}
    </Field>
  );
}
