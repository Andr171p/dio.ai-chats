export type MessageRole = 'user' | 'assistant';

export interface TextContent {
  type: 'text';
  text: string;
}

/** Ссылка на приложенный файл */
export interface AttachmentContent {
  type: 'content';
  attachmentId: string;
  contentType: string;
}

export type ToolCallStatus =
  'waiting_approval' | 'running' | 'completed' | 'failed' | 'cancelled';

/** Вызов инструмента MCP-сервера внутри ответа ассистента */
export interface ToolCallContent {
  type: 'tool_call';
  callId: string;
  connectionId: string;
  name: string;
  /** Человекочитаемое название, если сервер его задал */
  title: string | null;
  status: ToolCallStatus;
}

export type MessageContent = TextContent | AttachmentContent | ToolCallContent;

export interface Message {
  id: string;
  conversationId: string;
  threadId: string;
  role: MessageRole;
  content: MessageContent[];
  runId: string | null;
  createdAt: string;
}

export function messageText(message: Message): string {
  return message.content
    .filter((part): part is TextContent => part.type === 'text')
    .map((part) => part.text)
    .join('\n\n');
}

/** Локальная копия сообщения, пока сервер не вернул сохранённую версию. */
export function draftMessage(
  conversationId: string,
  role: MessageRole,
  content: MessageContent[],
): Message {
  return {
    id: `draft-${crypto.randomUUID()}`,
    conversationId,
    threadId: '',
    role,
    content,
    runId: null,
    createdAt: new Date().toISOString(),
  };
}
