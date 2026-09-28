import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { registerStoreReset } from './store-reset';

/**
 * Приложение не управляет адресной строкой, чтобы без доработок встраиваться виджетом в DIO desk.
 * Текущий экран живёт в сторе и переживает перезагрузку вкладки.
 */
export type Route =
  { page: 'chat'; conversationId: string | null } | { page: 'models' };

interface NavigationState {
  route: Route;
}

export const useNavigation = create<NavigationState>()(
  persist<NavigationState>(
    () => ({ route: { page: 'chat', conversationId: null } }),
    {
      name: 'dios.navigation',
      storage: createJSONStorage(() => sessionStorage),
    },
  ),
);

registerStoreReset(() =>
  useNavigation.setState(useNavigation.getInitialState(), true),
);

export function navigate(route: Route) {
  useNavigation.setState({ route });
}

export function openChat(conversationId: string | null = null) {
  navigate({ page: 'chat', conversationId });
}

/** Идентификатор открытого чата или null для нового. */
export function useOpenedConversationId(): string | null {
  return useNavigation(({ route }) =>
    route.page === 'chat' ? route.conversationId : null,
  );
}
