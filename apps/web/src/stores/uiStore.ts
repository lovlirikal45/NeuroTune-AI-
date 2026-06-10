import { create } from 'zustand';

interface Panel {
  id: string;
  title: string;
  visible: boolean;
  position: { x: number; y: number };
  size: { width: number; height: number };
}

interface UIStore {
  sidebarOpen: boolean;
  theme: 'dark' | 'cyberpunk';
  panels: Panel[];
  toggleSidebar: () => void;
  setTheme: (theme: 'dark' | 'cyberpunk') => void;
  togglePanel: (id: string) => void;
  updatePanelPosition: (id: string, position: { x: number; y: number }) => void;
  updatePanelSize: (id: string, size: { width: number; height: number }) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarOpen: true,
  theme: 'cyberpunk',
  panels: [],
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
  togglePanel: (id) =>
    set((state) => ({
      panels: state.panels.map((p) =>
        p.id === id ? { ...p, visible: !p.visible } : p
      )
    })),
  updatePanelPosition: (id, position) =>
    set((state) => ({
      panels: state.panels.map((p) =>
        p.id === id ? { ...p, position } : p
      )
    })),
  updatePanelSize: (id, size) =>
    set((state) => ({
      panels: state.panels.map((p) =>
        p.id === id ? { ...p, size } : p
      )
    }))
}));