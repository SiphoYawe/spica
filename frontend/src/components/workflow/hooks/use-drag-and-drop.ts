"use client";

import { useCallback, useMemo } from "react";
import { useReactFlow } from "@xyflow/react";
import { useShallow } from "zustand/react/shallow";
import { useCanvasStore, type CanvasStore } from "../store";
import { type SpicaNodeType } from "../config";

/**
 * useDragAndDrop - Hook for handling node drag-and-drop from sidebar
 *
 * Features:
 * - Converts screen coordinates to flow coordinates
 * - Detects potential connection sites during drag
 * - Creates nodes on drop (standalone or in-between)
 */
export function useDragAndDrop() {
  const { screenToFlowPosition } = useReactFlow();

  const selector = useCallback(
    (state: CanvasStore) => ({
      addNodeByType: state.addNodeByType,
      addNodeInBetween: state.addNodeInBetween,
      potentialConnection: state.potentialConnection,
      checkForPotentialConnection: state.checkForPotentialConnection,
      resetPotentialConnection: state.resetPotentialConnection,
    }),
    []
  );

  const {
    addNodeByType,
    addNodeInBetween,
    potentialConnection,
    checkForPotentialConnection,
    resetPotentialConnection,
  } = useCanvasStore(useShallow(selector));

  // Handle drop on canvas
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      // Get node type from drag data
      const nodeType = event.dataTransfer.getData(
        "application/reactflow"
      ) as SpicaNodeType;

      if (!nodeType) return;

      // Check if dropping on a potential connection
      if (potentialConnection) {
        // Insert node between existing connection
        addNodeInBetween({
          type: nodeType,
          source: potentialConnection.source?.node,
          target: potentialConnection.target?.node,
          sourceHandleId: potentialConnection.source?.handle,
          targetHandleId: potentialConnection.target?.handle,
          position: potentialConnection.position,
        });
      } else {
        // Create standalone node at drop position
        const position = screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        });
        addNodeByType(nodeType, position);
      }

      // Reset potential connection
      resetPotentialConnection();
    },
    [
      addNodeByType,
      addNodeInBetween,
      potentialConnection,
      resetPotentialConnection,
      screenToFlowPosition,
    ]
  );

  // Handle drag over canvas (allow drop)
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  // Create drag handler for sidebar items
  const createDragHandler = useCallback(
    (nodeType: SpicaNodeType) => {
      return {
        onDragStart: (event: React.DragEvent) => {
          event.dataTransfer.setData("application/reactflow", nodeType);
          event.dataTransfer.effectAllowed = "move";
        },
        onDrag: (event: React.DragEvent) => {
          // Skip if no position (drag end)
          if (event.clientX === 0 && event.clientY === 0) return;

          const flowPosition = screenToFlowPosition({
            x: event.clientX,
            y: event.clientY,
          });

          // Check for nearby connection sites
          checkForPotentialConnection(flowPosition);
        },
        onDragEnd: () => {
          resetPotentialConnection();
        },
      };
    },
    [screenToFlowPosition, checkForPotentialConnection, resetPotentialConnection]
  );

  return useMemo(
    () => ({
      onDrop,
      onDragOver,
      createDragHandler,
    }),
    [onDrop, onDragOver, createDragHandler]
  );
}
