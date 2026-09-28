import type { ModelProtocol, ModelSelection } from '../model/types';

export function isSameModel(
  a: ModelSelection | null | undefined,
  b: ModelSelection | null | undefined,
) {
  return Boolean(
    a && b && a.connectionId === b.connectionId && a.modelId === b.modelId,
  );
}

export function findModel<T extends ModelSelection>(
  models: T[],
  selection: ModelSelection | null | undefined,
) {
  return models.find((model) => isSameModel(model, selection));
}

/** 1047576 → «1M», 128000 → «128K» */
export function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) return `${Math.round(tokens / 100_000) / 10}M`;
  if (tokens >= 1_000) return `${Math.round(tokens / 1_000)}K`;
  return String(tokens);
}

export const PROTOCOL_LABELS: Record<ModelProtocol, string> = {
  openai_responses: 'OpenAI Responses',
  openai_chat_completions: 'OpenAI Chat Completions',
  anthropic_messages: 'Anthropic Messages',
  gemini: 'Google Gemini',
};
