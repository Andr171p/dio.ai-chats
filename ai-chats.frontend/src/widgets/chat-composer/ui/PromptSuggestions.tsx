import { Code, FileText, Globe } from 'lucide-react';
import { setDraft } from '../model/drafts-store';
import styles from './ChatComposer.module.scss';
import { COMPOSER_INPUT_ID } from './ChatComposer';

const SUGGESTIONS = [
  {
    icon: FileText,
    label: 'Написать текст',
    prompt: 'Помоги написать текст: ',
  },
  {
    icon: Code,
    label: 'Разобраться в коде',
    prompt: 'Объясни, как работает этот код:\n\n',
  },
  {
    icon: Globe,
    label: 'Исследовать тему',
    prompt: 'Исследуй тему и собери ключевые факты со ссылками на источники: ',
  },
];

/** Быстрые старты под композером нового чата. */
export function PromptSuggestions() {
  const apply = (prompt: string) => {
    setDraft(null, prompt);
    // Каретка встанет в конец текста, когда React обновит значение поля
    document.getElementById(COMPOSER_INPUT_ID)?.focus();
  };

  return (
    <div className={styles.suggestions}>
      {SUGGESTIONS.map(({ icon: Icon, label, prompt }) => (
        <button
          key={label}
          type="button"
          className={styles.suggestion}
          onClick={() => apply(prompt)}
        >
          <Icon size={16} aria-hidden />
          {label}
        </button>
      ))}
    </div>
  );
}
