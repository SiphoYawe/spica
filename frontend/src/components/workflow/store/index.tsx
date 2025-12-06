"use client";

import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";
import { useStore, type StoreApi } from "zustand";
import { createCanvasStore, type CanvasStore } from "./canvas-store";
import type { SpicaNode } from "../config";
import type { SpicaEdge } from "../edges";

// Context for the store
const CanvasStoreContext = createContext<StoreApi<CanvasStore> | null>(null);

// Initial state interface
interface CanvasStoreProviderProps {
  children: ReactNode;
  initialState?: {
    nodes?: SpicaNode[];
    edges?: SpicaEdge[];
  };
}

/**
 * CanvasStoreProvider - Provides Zustand store via React Context
 *
 * This pattern allows:
 * 1. Server-side initial state injection
 * 2. Multiple independent canvas instances if needed
 * 3. Proper store isolation in Next.js
 */
export function CanvasStoreProvider({
  children,
  initialState,
}: CanvasStoreProviderProps) {
  // Use useState with lazy initializer to create store once
  const [store] = useState(() => createCanvasStore(initialState));

  return (
    <CanvasStoreContext.Provider value={store}>
      {children}
    </CanvasStoreContext.Provider>
  );
}

/**
 * useCanvasStore - Hook to access the canvas store
 *
 * @param selector - Optional selector function for partial state
 * @returns Selected state or full store
 */
export function useCanvasStore<T = CanvasStore>(
  selector?: (store: CanvasStore) => T
): T {
  const storeContext = useContext(CanvasStoreContext);

  if (!storeContext) {
    throw new Error("useCanvasStore must be used within CanvasStoreProvider");
  }

  return useStore(storeContext, selector ?? ((state) => state as T));
}

/**
 * useCanvasContext - Check if CanvasStoreProvider is present
 *
 * @returns true if within a CanvasStoreProvider, false otherwise
 */
export function useCanvasContext(): boolean {
  const storeContext = useContext(CanvasStoreContext);
  return storeContext !== null;
}

// Re-export types
export type { CanvasStore, CanvasState, CanvasActions } from "./canvas-store";
