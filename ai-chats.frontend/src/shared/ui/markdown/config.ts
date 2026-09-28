import { createCodePlugin } from '@streamdown/code';
import { createMathPlugin } from '@streamdown/math';
import { mermaid } from '@streamdown/mermaid';
import {
  Check,
  Copy,
  Download,
  ExternalLink,
  Loader2,
  Maximize2,
  RotateCcw,
  X,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';
import type {
  ControlsConfig,
  IconMap,
  MermaidOptions,
  PluginConfig,
  StreamdownTranslations,
} from 'streamdown';
import type { Theme } from '../../lib/theme';

export const plugins: PluginConfig = {
  code: createCodePlugin({ themes: ['github-light', 'github-dark'] }),
  math: createMathPlugin({ errorColor: 'var(--color-text-tertiary)' }),
  mermaid,
};

export const controls: ControlsConfig = {
  code: { copy: true, download: true },
  table: { copy: true, download: true, fullscreen: false },
  mermaid: { copy: true, download: true, fullscreen: false, panZoom: false },
  image: { download: true },
};

export const icons: IconMap = {
  CheckIcon: Check,
  CopyIcon: Copy,
  DownloadIcon: Download,
  ExternalLinkIcon: ExternalLink,
  Loader2Icon: Loader2,
  Maximize2Icon: Maximize2,
  RotateCcwIcon: RotateCcw,
  XIcon: X,
  ZoomInIcon: ZoomIn,
  ZoomOutIcon: ZoomOut,
};

const MERMAID_PALETTE: Record<Theme, Record<string, string>> = {
  dark: {
    background: '#272727',
    primaryColor: '#2e2e2e',
    primaryTextColor: '#fafaf7',
    primaryBorderColor: '#454545',
    secondaryColor: '#392326',
    tertiaryColor: '#1c1c1c',
    lineColor: '#8e8e8a',
    textColor: '#fafaf7',
  },
  light: {
    background: '#ffffff',
    primaryColor: '#f1f1ed',
    primaryTextColor: '#1c1c1c',
    primaryBorderColor: '#cfcfc9',
    secondaryColor: '#f8e8e9',
    tertiaryColor: '#ffffff',
    lineColor: '#7a7a75',
    textColor: '#1c1c1c',
  },
};

export const mermaidOptions = (theme: Theme): MermaidOptions => ({
  config: {
    theme: 'base',
    securityLevel: 'strict',
    fontFamily: 'Inter Variable, Inter, system-ui, sans-serif',
    themeVariables: { darkMode: theme === 'dark', ...MERMAID_PALETTE[theme] },
  },
});

export const translations: StreamdownTranslations = {
  close: 'Закрыть',
  copied: 'Скопировано',
  copyCode: 'Копировать код',
  copyLink: 'Копировать ссылку',
  copyTable: 'Копировать таблицу',
  copyTableAsCsv: 'Копировать как CSV',
  copyTableAsMarkdown: 'Копировать как Markdown',
  copyTableAsTsv: 'Копировать как TSV',
  downloadDiagram: 'Скачать диаграмму',
  downloadDiagramAsMmd: 'Скачать как MMD',
  downloadDiagramAsPng: 'Скачать как PNG',
  downloadDiagramAsSvg: 'Скачать как SVG',
  downloadFile: 'Скачать файл',
  downloadImage: 'Скачать изображение',
  downloadTable: 'Скачать таблицу',
  downloadTableAsCsv: 'Скачать как CSV',
  downloadTableAsMarkdown: 'Скачать как Markdown',
  exitFullscreen: 'Выйти из полноэкранного режима',
  externalLinkWarning: 'Ссылка ведёт на внешний сайт',
  imageNotAvailable: 'Изображение недоступно',
  mermaidFormatMmd: 'MMD',
  mermaidFormatPng: 'PNG',
  mermaidFormatSvg: 'SVG',
  openExternalLink: 'Открыть внешнюю ссылку?',
  openLink: 'Открыть ссылку',
  resetView: 'Сбросить вид',
  tableFormatCsv: 'CSV',
  tableFormatMarkdown: 'Markdown',
  tableFormatTsv: 'TSV',
  viewFullscreen: 'На весь экран',
  zoomIn: 'Увеличить',
  zoomOut: 'Уменьшить',
};
