import { LoginForm } from '@/features/login';
import { LogoMark } from '@/shared/ui/logo';
import styles from './LoginPage.module.scss';

export function LoginPage() {
  return (
    <main className={styles.page}>
      <div className={styles.card}>
        <LogoMark size={36} />
        <div className={styles.heading}>
          <h1 className={styles.title}>Вход в DIOS AI</h1>
          <p className={styles.subtitle}>Используйте учётную запись DIO desk</p>
        </div>
        <LoginForm />
      </div>
    </main>
  );
}
