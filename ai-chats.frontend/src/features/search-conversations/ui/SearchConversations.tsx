import { MessageSquare, Search } from 'lucide-react';
import {
  useDeferredValue,
  useId,
  useMemo,
  useState,
  type KeyboardEvent,
} from 'react';
import {
  conversationTitle,
  useConversations,
  type Conversation,
} from '@/entities/conversation';
import { formatShortDate } from '@/shared/lib/format';
import { useHotkey } from '@/shared/lib/hooks';
import { openChat } from '@/shared/lib/navigation';
import { Dialog } from '@/shared/ui/dialog';
import { NavItem } from '@/shared/ui/nav-item';
import styles from './SearchConversations.module.scss';

const RESULTS_LIMIT = 50;

/** Пункт «Поиск чатов» в сайдбаре и диалог поиска по Ctrl+K. */
export function SearchConversations({
  collapsed = false,
}: {
  collapsed?: boolean;
}) {
  const [open, setOpen] = useState(false);
  useHotkey('KeyK', () => setOpen(true), { withModifier: true });

  return (
    <>
      <NavItem
        icon={Search}
        label="Поиск чатов"
        collapsed={collapsed}
        meta={<kbd className={styles.shortcut}>Ctrl K</kbd>}
        aria-keyshortcuts="Control+K"
        onClick={() => setOpen(true)}
      />
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title="Поиск чатов"
        size="md"
      >
        <SearchPanel onPick={() => setOpen(false)} />
      </Dialog>
    </>
  );
}

function SearchPanel({ onPick }: { onPick: () => void }) {
  const conversations = useConversations((state) => state.items);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const deferredQuery = useDeferredValue(query);
  const listId = useId();

  const results = useMemo(() => {
    const needle = deferredQuery.trim().toLocaleLowerCase('ru');
    const matches = needle
      ? conversations.filter((item) =>
          conversationTitle(item).toLocaleLowerCase('ru').includes(needle),
        )
      : conversations;
    return matches.slice(0, RESULTS_LIMIT);
  }, [conversations, deferredQuery]);

  const pick = (conversation: Conversation) => {
    openChat(conversation.id);
    onPick();
  };

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      const step = event.key === 'ArrowDown' ? 1 : -1;
      setActiveIndex(
        (index) =>
          (index + step + results.length) % Math.max(results.length, 1),
      );
    } else if (event.key === 'Enter' && results[activeIndex]) {
      event.preventDefault();
      pick(results[activeIndex]);
    }
  };

  return (
    <div className={styles.panel}>
      <div className={styles.inputRow}>
        <Search size={16} aria-hidden />
        <input
          className={styles.input}
          placeholder="Название чата"
          value={query}
          autoFocus
          role="combobox"
          aria-label="Название чата"
          aria-expanded
          aria-controls={listId}
          aria-activedescendant={
            results[activeIndex] ? `${listId}-${activeIndex}` : undefined
          }
          onChange={(event) => {
            setQuery(event.target.value);
            setActiveIndex(0);
          }}
          onKeyDown={onKeyDown}
        />
      </div>

      {results.length > 0 ? (
        <ul id={listId} role="listbox" className={styles.results}>
          {results.map((conversation, index) => (
            <li
              key={conversation.id}
              id={`${listId}-${index}`}
              role="option"
              aria-selected={index === activeIndex}
              className={styles.result}
              onClick={() => pick(conversation)}
              onPointerMove={() => setActiveIndex(index)}
            >
              <MessageSquare size={16} aria-hidden />
              <span className={styles.title}>
                {conversationTitle(conversation)}
              </span>
              <span className={styles.date}>
                {formatShortDate(conversation.updatedAt)}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className={styles.empty}>
          {query ? 'Ничего не нашлось' : 'Чатов пока нет'}
        </p>
      )}
    </div>
  );
}
