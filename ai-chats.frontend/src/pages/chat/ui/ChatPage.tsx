import { useEffect } from 'react';
import {
  conversationTitle,
  fetchConversation,
  useConversation,
} from '@/entities/conversation';
import { ConversationActions } from '@/features/manage-conversation';
import { ThemeToggle } from '@/features/toggle-theme';
import {
  ChatComposer,
  Disclaimer,
  PromptSuggestions,
} from '@/widgets/chat-composer';
import { ConversationThread } from '@/widgets/conversation-thread';
import { openChat, useOpenedConversationId } from '@/shared/lib/navigation';
import { LogoMark } from '@/shared/ui/logo';
import { PageHeader } from '@/shared/ui/page-header';
import styles from './ChatPage.module.scss';

export function ChatPage() {
  const conversationId = useOpenedConversationId();
  const conversation = useConversation(conversationId);

  // Чат открыт после перезагрузки и ещё не попал в загруженный список
  useEffect(() => {
    if (conversationId && !conversation) {
      fetchConversation(conversationId).catch(() => openChat(null));
    }
  }, [conversationId, conversation]);

  return (
    <div className={styles.page}>
      <PageHeader
        breadcrumbs={['Чаты', conversationTitle(conversation)]}
        actions={
          <>
            <ThemeToggle />
            {conversation && (
              <ConversationActions conversation={conversation} />
            )}
          </>
        }
      />

      {conversationId ? (
        <>
          <ConversationThread
            key={conversationId}
            conversationId={conversationId}
          />
          <div className={styles.dock}>
            <ChatComposer
              key={conversationId}
              conversationId={conversationId}
              conversation={conversation}
            />
          </div>
        </>
      ) : (
        <>
          <div className={styles.welcome}>
            <div className={styles.hero}>
              <LogoMark size={32} />
              <h1 className={styles.title}>Над чем поработаем?</h1>
              <p className={styles.subtitle}>
                От первого вопроса до готового результата.
              </p>
            </div>
            <ChatComposer conversationId={null} disclaimer={false} />
            <PromptSuggestions />
          </div>
          <div className={styles.footer}>
            <Disclaimer />
          </div>
        </>
      )}
    </div>
  );
}
