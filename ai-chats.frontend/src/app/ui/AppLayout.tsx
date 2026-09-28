import { ChatPage } from '@/pages/chat';
import { ModelsPage } from '@/pages/models';
import { AppSidebar } from '@/widgets/app-sidebar';
import { useNavigation } from '@/shared/lib/navigation';
import styles from './AppLayout.module.scss';

export default function AppLayout() {
  const page = useNavigation(({ route }) => route.page);

  return (
    <div className={styles.layout}>
      <AppSidebar />
      <main className={styles.main}>
        {page === 'models' ? <ModelsPage /> : <ChatPage />}
      </main>
    </div>
  );
}
