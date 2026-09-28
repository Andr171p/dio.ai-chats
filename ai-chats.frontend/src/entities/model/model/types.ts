/** Ссылка на выбранную модель. */
export interface ModelSelection {
  connectionId: string;
  modelId: string;
}

export type Modality = 'text' | 'image' | 'audio' | 'video';

export type ModelCapability =
  'tools' | 'structured_output' | 'reasoning' | 'file_input';

/** Модель, которую пользователь может выбрать в чате. */
export interface AvailableModel extends ModelSelection {
  connectionName: string;
  provider: string;
  inputModalities: Modality[];
  outputModalities: Modality[];
  capabilities: ModelCapability[];
  contextWindow: number;
  maxOutputTokens: number | null;
}

export type ModelProtocol =
  | 'openai_responses'
  | 'openai_chat_completions'
  | 'anthropic_messages'
  | 'gemini';

/** Описание модели внутри подключения. */
export interface ModelSpec {
  id: string;
  provider: string;
  inputModalities: Modality[];
  outputModalities: Modality[];
  contextWindow: number;
  maxOutputTokens?: number | null;
  capabilities?: ModelCapability[];
}

type ConnectionOwner =
  | { scope: 'system' }
  | { scope: 'organization'; organizationId: string }
  | { scope: 'user'; organizationId: string; userId: string };

type ConnectionRoute =
  | { type: 'system'; baseUrl: string; hasApiKey: boolean }
  | { type: 'edge'; endpointId: string; localConnectionId: string };

/** Источник моделей: OpenAI-совместимый сервер, Anthropic, Gemini и т. п. */
export interface ModelConnection {
  id: string;
  owner: ConnectionOwner;
  name: string;
  protocol: ModelProtocol;
  route: ConnectionRoute;
  models: ModelSpec[];
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ModelConnectionInput {
  name: string;
  protocol: ModelProtocol;
  baseUrl: string;
  /** Пустое значение при изменении оставляет текущий ключ */
  apiKey?: string;
  models: ModelSpec[];
  enabled?: boolean;
}
