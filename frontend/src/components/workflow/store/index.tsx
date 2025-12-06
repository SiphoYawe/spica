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

// Fallback store for read-only mode - created once as module singleton
let fallbackStore: StoreApi<CanvasStore> | null = null;
function getFallbackStore(): StoreApi<CanvasStore> {
  if (!fallbackStore) {
    fallbackStore = createCanvasStore();
  }
  return fallbackStore;
}

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

/**
 * useCanvasStoreSafe - Hook that works with or without CanvasStoreProvider
 *
 * Uses a fallback empty store when no provider is present.
 * This allows components to work in both editable and read-only contexts.
 * Actions on the fallback store are no-ops that don't affect anything.
 *
 * @param selector - Selector function for partial state
 * @returns Object with selected value and isEditable flag
 */
export function useCanvasStoreSafe<T>(
  selector: (store: CanvasStore) => T
): { value: T; isEditable: boolean } {
  const storeContext = useContext(CanvasStoreContext);
  const isEditable = storeContext !== null;

  // Always call useStore (consistent hook pattern) but use fallback if no context
  const value = useStore(storeContext ?? getFallbackStore(), selector);

  return { value, isEditable };
}

// Re-export types
export type { CanvasStore, CanvasState, CanvasActions } from "./canvas-store";
