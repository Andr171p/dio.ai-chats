import { MessageSquare } from 'lucide-react';
import { useEffect, useMemo, useRef } from 'react';
import {
  conversationTitle,
  groupByDate,
  loadConversations,
  loadMoreConversations,
  useConversations,
} from '@/entities/conversation';
import { useRuns } from '@/entities/run';
import { ConversationActions } from '@/features/manage-conversation';
import { openChat, useOpenedConversationId } from '@/shared/lib/navigation';
import { Button } from '@/shared/ui/button';
import { NavItem } from '@/shared/ui/nav-item';
import { Spinner } from '@/shared/ui/spinner';
import styles from './AppSidebar.module.scss';

export function ConversationList() {
  const { items, status, error, hasMore } = useConversations();
  const openedId = useOpenedConversationId();
  const runs = useRuns((state) => state.runs);
  const groups = useMemo(() => groupByDate(items), [items]);
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void loadConversations();
  }, []);

  // Подгружаем следующую страницу, когда список докручен до конца
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel || !hasMore) return;

    const observer = new IntersectionObserver(([entry]) => {
      if (entry?.isIntersecting) void loadMoreConversations();
    });
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore]);

  if (status === 'error' && items.length === 0) {
    return (
      <div className={styles.listStatus}>
        <span>{error}</span>
        <Button size="sm" onClick={() => void loadConversations()}>
          Повторить
        </Button>
      </div>
    );
  }

  if (status === 'loading' && items.length === 0) {
    return (
      <div className={styles.listStatus}>
        <Spinner label="Загружаем чаты" />
      </div>
    );
  }

  if (status === 'ready' && items.length === 0) {
    return <p className={styles.listStatus}>Здесь появятся ваши чаты</p>;
  }

  return (
    <>
      {groups.map((group) => (
        <section
          key={group.label}
          className={styles.section}
          aria-label={group.label}
        >
          <h2 className={styles.sectionTitle}>{group.label}</h2>
          {group.items.map((conversation) => (
            <NavItem
              key={conversation.id}
              icon={MessageSquare}
              label={conversationTitle(conversation)}
              active={conversation.id === openedId}
              meta={
                runs[conversation.id]?.status === 'streaming' && (
                  <Spinner size={14} label="Отвечает" />
                )
              }
              actions={<ConversationActions conversation={conversation} />}
              onClick={() => openChat(conversation.id)}
            />
          ))}
        </section>
      ))}
      <div ref={sentinelRef} className={styles.sentinel}>
        {status === 'loading' && <Spinner />}
      </div>
    </>
  );
}
