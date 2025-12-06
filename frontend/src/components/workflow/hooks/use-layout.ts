"use client";

import { useCallback } from "react";
import { useShallow } from "zustand/react/shallow";
import { useCanvasStore } from "../store";
import { layoutGraph } from "../utils/layout-helper";

/**
 * useLayout - Hook for auto-layout functionality
 *
 * Uses ELK algorithm for hierarchical graph layout
 */
export function useLayout() {
  const { getNodes, getEdges, setNodes } = useCanvasStore(
    useShallow((state) => ({
      getNodes: state.getNodes,
      getEdges: state.getEdges,
      setNodes: state.setNodes,
    }))
  );

  // Apply layout to current graph
  const applyLayout = useCallback(async () => {
    const nodes = getNodes();
    const edges = getEdges();

    if (nodes.length === 0) return;

    try {
      const layoutedNodes = await layoutGraph(nodes, edges);
      setNodes(layoutedNodes);
    } catch (error) {
      console.error("Layout error:", error);
    }
  }, [getNodes, getEdges, setNodes]);

  return applyLayout;
}
