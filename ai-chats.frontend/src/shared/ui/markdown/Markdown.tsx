import 'katex/dist/katex.min.css';
import 'streamdown/styles.css';
import { useMemo } from 'react';
import { Streamdown, type LinkSafetyConfig } from 'streamdown';
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
  renderModal: (props) => <ExternalLinkDialog {...props} />,
};

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
