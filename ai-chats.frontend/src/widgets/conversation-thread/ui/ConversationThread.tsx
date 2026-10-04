import { ArrowDown, RotateCcw } from 'lucide-react';
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from 'react';
import {
  AssistantMessage,
  loadMessages,
  messageText,
  UserMessage,
  useThread,
  type Thread,
} from '@/entities/message';
import { useRun } from '@/entities/run';
import { sendMessage } from '@/features/send-message';
import { Button, IconButton } from '@/shared/ui/button';
import { Notice } from '@/shared/ui/notice';
import { Spinner } from '@/shared/ui/spinner';
import styles from './ConversationThread.module.scss';
import { MessageActions } from './MessageActions';

/** Расстояние до низа, в пределах которого лента следует за новым контентом */
const STICK_THRESHOLD_PX = 80;

export function ConversationThread({
  conversationId,
}: {
  conversationId: string;
}) {
  const thread = useThread(conversationId);

  useEffect(() => {
    void loadMessages(conversationId);
  }, [conversationId]);

  if (!thread || (thread.status === 'loading' && thread.items.length === 0)) {
    return (
      <div className={styles.center}>
        <Spinner size={20} label="Загружаем историю" />
      </div>
    );
  }

  return <MessageList conversationId={conversationId} thread={thread} />;
}

function MessageList({
  conversationId,
  thread,
}: {
  conversationId: string;
  thread: Thread;
}) {
  const run = useRun(conversationId);
  const scrollRef = useRef<HTMLDivElement>(null);
  const columnRef = useRef<HTMLDivElement>(null);
  const stickToBottom = useRef(true);
  const lastScrollTop = useRef(0);
  const [atBottom, setAtBottom] = useState(true);
  const lastMessage = thread.items.at(-1);

  const scrollToEnd = useCallback((behavior: ScrollBehavior = 'instant') => {
    const element = scrollRef.current;
    element?.scrollTo({ top: element.scrollHeight, behavior });
  }, []);

  // Контент растёт (стрим, подсветка кода, диаграммы) — остаёмся внизу, если пользователь был там
  useEffect(() => {
    const column = columnRef.current;
    if (!column) return;

    const observer = new ResizeObserver(() => {
      if (stickToBottom.current) scrollToEnd();
    });
    observer.observe(column);
    return () => observer.disconnect();
  }, [scrollToEnd]);

  // Только что отправленное сообщение показываем всегда
  useLayoutEffect(() => {
    if (lastMessage?.role !== 'user') return;
    stickToBottom.current = true;
    scrollToEnd();
  }, [lastMessage, scrollToEnd]);

  const onScroll = () => {
    const element = scrollRef.current;
    if (!element) return;

    // Отлипаем только когда пользователь прокрутил вверх: контент при стриме
    // растёт быстрее, чем приходит событие scroll от нашей же прокрутки
    const distance =
      element.scrollHeight - element.scrollTop - element.clientHeight;
    if (element.scrollTop < lastScrollTop.current)
      stickToBottom.current = false;
    if (distance < STICK_THRESHOLD_PX) stickToBottom.current = true;

    lastScrollTop.current = element.scrollTop;
    setAtBottom(stickToBottom.current);
  };

  const retry = (text: string) => void sendMessage({ conversationId, text });

  return (
    <div className={styles.viewport}>
      <div ref={scrollRef} className={styles.scroll} onScroll={onScroll}>
        <div ref={columnRef} className={styles.column}>
          {thread.status === 'error' && (
            <Notice
              action={
                <Button
                  size="sm"
                  onClick={() => void loadMessages(conversationId)}
                >
                  Повторить
                </Button>
              }
            >
              {thread.error}
            </Notice>
          )}

          {thread.items.map((message) => {
            const text = messageText(message);
            return message.role === 'user' ? (
              <UserMessage key={message.id} text={text} />
            ) : (
              <AssistantMessage key={message.id} content={message.content}>
                <MessageActions text={text} />
              </AssistantMessage>
            );
          })}

          {run?.status === 'streaming' && (
            <AssistantMessage content={run.content} streaming />
          )}

          {run?.status === 'failed' && (
            <Notice
              action={
                run.retryText !== null && (
                  <Button
                    size="sm"
                    icon={RotateCcw}
                    onClick={() => retry(run.retryText ?? '')}
                  >
                    Повторить
                  </Button>
                )
              }
            >
              {run.error}
            </Notice>
          )}
        </div>
      </div>

      {!atBottom && (
        <IconButton
          icon={ArrowDown}
          label="К последнему сообщению"
          variant="secondary"
          size="md"
          tooltip={false}
          className={styles.toBottom}
          onClick={() => {
            stickToBottom.current = true;
            scrollToEnd('smooth');
          }}
        />
      )}
    </div>
  );
}
