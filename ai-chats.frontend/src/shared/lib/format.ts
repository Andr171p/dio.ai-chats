const time = new Intl.DateTimeFormat('ru-RU', {
  hour: '2-digit',
  minute: '2-digit',
});
const day = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'short',
});
const dayWithYear = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
});

/** «14:05» для сегодняшних дат, «27 сент.» для этого года, иначе с годом. */
export function formatShortDate(
  value: string | Date,
  now = new Date(),
): string {
  const date = new Date(value);

  if (date.toDateString() === now.toDateString()) return time.format(date);
  if (date.getFullYear() === now.getFullYear()) return day.format(date);
  return dayWithYear.format(date);
}
