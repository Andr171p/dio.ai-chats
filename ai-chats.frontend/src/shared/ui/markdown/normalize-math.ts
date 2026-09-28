/** Блоки и строки кода, внутри которых разметку трогать нельзя. Незакрытый блок — при стриминге. */
const CODE = /(```[\s\S]*?(?:```|$)|`[^`\n]*`)/;

/**
 * Модели часто пишут формулы в LaTeX-разделителях \( … \) и \[ … \],
 * а remark-math понимает только $$ … $$. Приводим к нему всё, что вне кода.
 */
export function normalizeMathDelimiters(markdown: string): string {
  if (!markdown.includes('\\(') && !markdown.includes('\\[')) return markdown;

  return markdown
    .split(CODE)
    .map((part, index) =>
      index % 2 === 1
        ? part
        : part
            .replace(
              /\\\[([\s\S]+?)\\\]/g,
              (_, formula: string) => `\n$$\n${formula.trim()}\n$$\n`,
            )
            .replace(
              /\\\(([\s\S]+?)\\\)/g,
              (_, formula: string) => `$$${formula.trim()}$$`,
            ),
    )
    .join('');
}
