export interface ServerSentEvent {
  event: string;
  data: string;
}

const EVENT_SEPARATOR = /\r?\n\r?\n/;

/** Разбирает поток text/event-stream на события. */
export async function* readServerSentEvents(
  body: ReadableStream<BufferSource>,
): AsyncGenerator<ServerSentEvent> {
  const reader = body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = '';

  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += value;
      const chunks = buffer.split(EVENT_SEPARATOR);
      buffer = chunks.pop() ?? '';

      for (const chunk of chunks) {
        const event = parseEvent(chunk);
        if (event) yield event;
      }
    }

    const tail = parseEvent(buffer);
    if (tail) yield tail;
  } finally {
    // Закрывает соединение, если потребитель вышел из цикла раньше времени
    reader.cancel().catch(() => undefined);
  }
}

function parseEvent(chunk: string): ServerSentEvent | null {
  let event = 'message';
  const data: string[] = [];

  for (const line of chunk.split(/\r?\n/)) {
    if (!line || line.startsWith(':')) continue;

    const separator = line.indexOf(':');
    const field = separator === -1 ? line : line.slice(0, separator);
    const value =
      separator === -1 ? '' : line.slice(separator + 1).replace(/^ /, '');

    if (field === 'event') event = value;
    else if (field === 'data') data.push(value);
  }

  return data.length > 0 ? { event, data: data.join('\n') } : null;
}
