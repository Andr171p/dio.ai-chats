import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { chatsApi, describeError } from '@/shared/api';
import { registerStoreReset } from '@/shared/lib/store-reset';
import { findModel } from '../lib/model';
import type { AvailableModel, ModelSelection } from './types';

interface ModelsState {
  items: AvailableModel[];
  status: 'idle' | 'loading' | 'ready' | 'error';
  error: string | null;
  /** Последняя выбранная модель — для новых чатов */
  preferred: ModelSelection | null;
}

const initialState: ModelsState = {
  items: [],
  status: 'idle',
  error: null,
  preferred: null,
};

export const useModels = create<ModelsState>()(
  persist(() => initialState, {
    name: 'dios.models',
    partialize: ({ preferred }) => ({ preferred }),
  }),
);

registerStoreReset(() => useModels.setState(useModels.getInitialState(), true));

export async function loadModels({ force = false } = {}) {
  const { status } = useModels.getState();
  if (status === 'loading' || (status === 'ready' && !force)) return;

  useModels.setState({ status: 'loading', error: null });
  try {
    const items = await chatsApi.get<AvailableModel[]>('/api/v1/models');
    useModels.setState({ items, status: 'ready' });
  } catch (error) {
    useModels.setState({ status: 'error', error: describeError(error) });
  }
}

export function setPreferredModel({ connectionId, modelId }: ModelSelection) {
  useModels.setState({ preferred: { connectionId, modelId } });
}

/** Модель для нового чата: последняя выбранная, если она ещё доступна, иначе первая. */
export function useDefaultModel(): AvailableModel | undefined {
  return useModels(
    ({ items, preferred }) => findModel(items, preferred) ?? items[0],
  );
}
