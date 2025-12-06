import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

// Panel configuration
export type PanelId = 'sidebar' | 'properties' | 'minimap';

interface UiState {
  // Backend status
  backendStatus: 'checking' | 'connected' | 'disconnected';
  backendVersion: string;

  // Panel visibility
  sidebarOpen: boolean;
  propertiesPanelOpen: boolean;
  minimapVisible: boolean;

  // Canvas settings
  canvasZoom: number;
  canvasPosition: { x: number; y: number };
  snapToGrid: boolean;
  gridVisible: boolean;

  // Actions
  setBackendStatus: (status: 'checking' | 'connected' | 'disconnected') => void;
  setBackendVersion: (version: string) => void;

  // Panel actions
  toggleSidebar: () => void;
  togglePropertiesPanel: () => void;
  toggleMinimap: () => void;
  openPropertiesPanel: () => void;
  closePropertiesPanel: () => void;

  // Canvas actions
  setCanvasZoom: (zoom: number) => void;
  setCanvasPosition: (position: { x: number; y: number }) => void;
  toggleSnapToGrid: () => void;
  toggleGridVisible: () => void;

  // Helpers
  isHealthy: () => boolean;
}

export const useUiStore = create<UiState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        backendStatus: 'checking',
        backendVersion: '',
        sidebarOpen: true,
        propertiesPanelOpen: false,
        minimapVisible: true,
        canvasZoom: 1,
        canvasPosition: { x: 0, y: 0 },
        snapToGrid: true,
        gridVisible: true,

        // Backend actions
        setBackendStatus: (status) => set({ backendStatus: status }, false, 'setBackendStatus'),
        setBackendVersion: (version) => set({ backendVersion: version }, false, 'setBackendVersion'),

        // Panel actions
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen }), false, 'toggleSidebar'),
        togglePropertiesPanel: () => set((state) => ({ propertiesPanelOpen: !state.propertiesPanelOpen }), false, 'togglePropertiesPanel'),
        toggleMinimap: () => set((state) => ({ minimapVisible: !state.minimapVisible }), false, 'toggleMinimap'),
        openPropertiesPanel: () => set({ propertiesPanelOpen: true }, false, 'openPropertiesPanel'),
        closePropertiesPanel: () => set({ propertiesPanelOpen: false }, false, 'closePropertiesPanel'),

        // Canvas actions
        setCanvasZoom: (zoom) => set({ canvasZoom: zoom }, false, 'setCanvasZoom'),
        setCanvasPosition: (position) => set({ canvasPosition: position }, false, 'setCanvasPosition'),
        toggleSnapToGrid: () => set((state) => ({ snapToGrid: !state.snapToGrid }), false, 'toggleSnapToGrid'),
        toggleGridVisible: () => set((state) => ({ gridVisible: !state.gridVisible }), false, 'toggleGridVisible'),

        // Helpers
        isHealthy: () => get().backendStatus === 'connected',
      }),
      {
        name: 'spica-ui-store',
        partialize: (state) => ({
          sidebarOpen: state.sidebarOpen,
          minimapVisible: state.minimapVisible,
          snapToGrid: state.snapToGrid,
          gridVisible: state.gridVisible,
        }),
      }
    ),
    { name: 'ui-store' }
  )
);
