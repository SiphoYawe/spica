"use client";

import { useCallback, useEffect, useMemo } from "react";
import {
  Position,
  useConnection,
  useNodeId,
  useNodeConnections,
  useInternalNode,
} from "@xyflow/react";
import { Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ButtonHandle } from "../../base";
import { useCanvasStore, type CanvasStore } from "../../store";
import {
  nodesConfig,
  iconMapping,
  getCompatibleNodes,
  type SpicaNodeType,
} from "../../config";
import { useShallow } from "zustand/react/shallow";

interface NodeHandleProps {
  id?: string;
  type: "source" | "target";
  position: Position;
  x: number;
  y: number;
}

// Calculate absolute position for connection site registration
function getIndicatorPosition(
  nodePosition: { x: number; y: number } | undefined,
  handleX: number,
  handleY: number,
  type: "source" | "target"
) {
  if (!nodePosition) return { x: 0, y: 0 };

  // Offset for the add button position
  const yOffset = type === "source" ? 50 : -50;

  return {
    x: nodePosition.x + handleX,
    y: nodePosition.y + handleY + yOffset,
  };
}

/**
 * NodeHandle - Advanced handle with dropdown for adding nodes
 *
 * Features:
 * - Shows "+" button when no connections exist
 * - Dropdown menu for selecting compatible node types
 * - Registers as connection site for drag-drop detection
 * - Red border when potential connection is nearby
 */
export function NodeHandle({ id, type, position, x, y }: NodeHandleProps) {
  const nodeId = useNodeId();
  const internalNode = useInternalNode(nodeId || "");
  const nodePosition = internalNode?.internals.positionAbsolute;

  // Get existing connections for this handle
  const connections = useNodeConnections({
    handleType: type,
    handleId: id || undefined,
  });

  // Check if a connection is in progress
  const isConnectionInProgress = useConnection((c) => c.inProgress);

  // Store selectors
  const selector = useCallback(
    (state: CanvasStore) => ({
      draggedNodes: state.draggedNodes,
      addNodeByType: state.addNodeByType,
      connectionSites: state.connectionSites,
      potentialConnection: state.potentialConnection,
    }),
    []
  );

  const {
    draggedNodes,
    addNodeByType,
    connectionSites,
    potentialConnection,
  } = useCanvasStore(useShallow(selector));

  // Connection ID for tracking
  const connectionId = useMemo(
    () => `handle-${nodeId}-${type}-${id || "default"}`,
    [nodeId, type, id]
  );

  // Check if this handle is the potential connection target
  const isPotentialConnection = potentialConnection?.id === connectionId;

  // Show add button only when:
  // 1. No existing connections
  // 2. No connection being drawn
  // 3. No nodes being dragged
  const displayAddButton =
    connections.length === 0 &&
    !isConnectionInProgress &&
    !draggedNodes.has(nodeId || "");

  // Register/unregister connection site
  useEffect(() => {
    if (!nodeId || !displayAddButton) {
      connectionSites.delete(connectionId);
      return;
    }

    const indicatorPosition = getIndicatorPosition(nodePosition, x, y, type);

    connectionSites.set(connectionId, {
      id: connectionId,
      position: indicatorPosition,
      type,
      [type === "source" ? "source" : "target"]: {
        node: nodeId,
        handle: id || null,
      },
    });

    return () => {
      connectionSites.delete(connectionId);
    };
  }, [
    nodeId,
    displayAddButton,
    connectionId,
    connectionSites,
    nodePosition,
    x,
    y,
    type,
    id,
  ]);

  // Handle adding a node from the dropdown
  const onAddNode = useCallback(
    (nodeType: SpicaNodeType) => {
      if (!nodeId) return;

      const indicatorPosition = getIndicatorPosition(nodePosition, x, y, type);

      // Add node at the calculated position
      addNodeByType(nodeType, indicatorPosition);
    },
    [nodeId, nodePosition, x, y, type, addNodeByType]
  );

  // Get compatible node types for this handle
  const compatibleNodes = getCompatibleNodes(type);

  // Calculate handle position styles
  const handleStyle = useMemo(
    () => ({
      left: x,
      top: y,
      transform: "translate(-50%, -50%)",
    }),
    [x, y]
  );

  return (
    <ButtonHandle
      id={id}
      type={type}
      position={position}
      showButton={displayAddButton}
      style={handleStyle}
      className={cn(
        isPotentialConnection && "!border-red-500 !ring-2 !ring-red-500/30"
      )}
    >
      {/* Add node dropdown */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            size="icon"
            className={cn(
              "h-6 w-6 rounded-xl border-2 bg-card hover:bg-card",
              "hover:border-spica hover:text-spica",
              isPotentialConnection && "border-red-500"
            )}
          >
            <Plus className="h-3 w-3" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="center"
          className="w-48"
          style={{
            transform: "translate(-50%, 0)",
          }}
        >
          <DropdownMenuLabel className="text-xs text-muted-foreground">
            Add Node
          </DropdownMenuLabel>
          {compatibleNodes.map((nodeType) => {
            const config = nodesConfig[nodeType];
            const Icon = iconMapping[nodeType];
            return (
              <DropdownMenuItem
                key={nodeType}
                onClick={() => onAddNode(nodeType)}
                className="flex items-center gap-2"
              >
                <div
                  className="flex h-6 w-6 items-center justify-center rounded"
                  style={{ backgroundColor: config.color.bg }}
                >
                  <Icon
                    className="h-3.5 w-3.5"
                    style={{ color: config.color.primary }}
                  />
                </div>
                <span>{config.title}</span>
              </DropdownMenuItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>
    </ButtonHandle>
  );
}
