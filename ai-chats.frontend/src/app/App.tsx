import { lazy, Suspense } from 'react';
import { restoreSession, useSession } from '@/entities/session';
import { LoginPage } from '@/pages/login';
import { SplashScreen } from './ui/SplashScreen';

// Рабочая часть приложения тяжелее (подсветка кода, формулы, диаграммы) — грузим её после входа
const AppLayout = lazy(() => import('./ui/AppLayout'));

export function App() {
  const status = useSession((state) => state.status);
  const restoreError = useSession((state) => state.restoreError);

  if (status === 'anonymous') return <LoginPage />;
  if (status === 'restoring')
    return <SplashScreen error={restoreError} onRetry={restoreSession} />;

  return (
    <Suspense fallback={<SplashScreen />}>
      <AppLayout />
    </Suspense>
  );
}
