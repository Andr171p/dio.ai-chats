import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SidebarState {
  collapsed: boolean;
}

export const useSidebar = create<SidebarState>()(
  persist<SidebarState>(() => ({ collapsed: false }), { name: 'dios.sidebar' }),
);

export function toggleSidebar() {
  useSidebar.setState(({ collapsed }) => ({ collapsed: !collapsed }));
}
