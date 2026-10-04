import 'katex/dist/katex.min.css';
import 'streamdown/styles.css';
import { useMemo } from 'react';
import { Streamdown, type LinkSafetyConfig } from 'streamdown';
import { env } from '../../config/env';
import { useTheme } from '../../lib/theme';
import {
  controls,
  icons,
  mermaidOptions,
  plugins,
  translations,
} from './config';
import { ExternalLinkDialog } from './ExternalLinkDialog';
import styles from './Markdown.module.scss';
import { normalizeMathDelimiters } from './normalize-math';

const linkSafety: LinkSafetyConfig = {
  enabled: true,
  // Ссылки на сервисы экосистемы (например, задача в DIO desk) открываются сразу
  onLinkCheck: isTrustedUrl,
  renderModal: (props) => <ExternalLinkDialog {...props} />,
};

function isTrustedUrl(url: string): boolean {
  try {
    return env.trustedOrigins.includes(new URL(url).origin);
  } catch {
    return false;
  }
}

interface MarkdownProps {
  children: string;
  /** Текст ещё приходит потоком */
  streaming?: boolean;
}

/**
 * Markdown ответа модели: GFM, подсветка кода, формулы KaTeX, диаграммы Mermaid.
 * Незакрытая при стриминге разметка дорисовывается корректно.
 */
export function Markdown({ children, streaming = false }: MarkdownProps) {
  const theme = useTheme((state) => state.theme);
  const mermaid = useMemo(() => mermaidOptions(theme), [theme]);
  const content = useMemo(() => normalizeMathDelimiters(children), [children]);

  return (
    <Streamdown
      // Mermaid применяет тему только при отрисовке — перерисовываем диаграммы при смене темы
      key={theme}
      className={styles.markdown}
      plugins={plugins}
      controls={controls}
      icons={icons}
      translations={translations}
      linkSafety={linkSafety}
      mermaid={mermaid}
      lineNumbers={false}
      isAnimating={streaming}
      caret="block"
    >
      {content}
    </Streamdown>
  );
}
