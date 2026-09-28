import { useCallback, useEffect, useEffectEvent, useState } from 'react';

/**
 * Глобальное сочетание клавиш. `code` — физическая клавиша (KeyK),
 * поэтому сочетание работает при любой раскладке.
 */
export function useHotkey(
  code: string,
  handler: (event: KeyboardEvent) => void,
  { withModifier = false } = {},
) {
  const onHotkey = useEffectEvent(handler);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.code !== code) return;
      if (withModifier && !(event.ctrlKey || event.metaKey)) return;

      event.preventDefault();
      onHotkey(event);
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [code, withModifier]);
}

export function useCopyToClipboard(resetAfterMs = 1500) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), resetAfterMs);
    return () => clearTimeout(timer);
  }, [copied, resetAfterMs]);

  const copy = useCallback(async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
  }, []);

  return { copied, copy };
}
