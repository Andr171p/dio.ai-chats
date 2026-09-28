import type { Conversation } from '../model/types';

export interface ConversationGroup {
  label: string;
  items: Conversation[];
}

const DAY_MS = 86_400_000;

const startOfDay = (date: Date) =>
  new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();

function groupLabel(date: Date, today: number): string {
  const daysAgo = Math.round((today - startOfDay(date)) / DAY_MS);

  if (daysAgo <= 0) return 'Сегодня';
  if (daysAgo === 1) return 'Вчера';
  if (daysAgo < 7) return 'Последние 7 дней';
  if (daysAgo < 30) return 'Последние 30 дней';
  return 'Ранее';
}

/** Группирует отсортированные по активности чаты: «Сегодня», «Вчера», … */
export function groupByDate(
  conversations: Conversation[],
  now = new Date(),
): ConversationGroup[] {
  const today = startOfDay(now);
  const groups: ConversationGroup[] = [];

  for (const conversation of conversations) {
    const label = groupLabel(new Date(conversation.updatedAt), today);
    const last = groups.at(-1);

    if (last?.label === label) last.items.push(conversation);
    else groups.push({ label, items: [conversation] });
  }

  return groups;
}
