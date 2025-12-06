"use client";

import { useCallback, useEffect, useMemo } from "react";
import { EdgeLabelRenderer } from "@xyflow/react";
import { Plus } from "lucide-react";
import { useShallow } from "zustand/react/shallow";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCanvasStore, type CanvasStore } from "../../store";
import { nodesConfig, iconMapping, type SpicaNodeType } from "../../config";

interface EdgeButtonProps {
  x: number;
  y: number;
  id: string;
  source: string;
  target: string;
  sourceHandleId?: string | null;
  targetHandleId?: string | null;
}

// Nodes that can be inserted on an edge (have both input and output)
const insertableNodes: SpicaNodeType[] = ["swap", "stake"];

/**
 * EdgeButton - Interactive button rendered on edge midpoint
 *
 * Features:
 * - Shows "+" button for adding nodes mid-connection
 * - Registers as connection site for drag-drop
 * - Red highlight when potential drop target
 * - Dropdown menu for node type selection
 */
export function EdgeButton({
  x,
  y,
  id,
  source,
  target,
  sourceHandleId,
  targetHandleId,
}: EdgeButtonProps) {
  // Store selectors
  const selector = useCallback(
    (state: CanvasStore) => ({
      addNodeInBetween: state.addNodeInBetween,
      connectionSites: state.connectionSites,
      potentialConnection: state.potentialConnection,
    }),
    []
  );

  const { addNodeInBetween, connectionSites, potentialConnection } =
    useCanvasStore(useShallow(selector));

  // Connection ID for this edge
  const connectionId = useMemo(() => `edge-${id}`, [id]);

  // Check if this edge is the potential drop target
  const isPotentialConnection = potentialConnection?.id === connectionId;

  // Register/unregister as connection site
  useEffect(() => {
    connectionSites.set(connectionId, {
      id: connectionId,
      position: { x, y },
      source: { node: source, handle: sourceHandleId || null },
      target: { node: target, handle: targetHandleId || null },
    });

    return () => {
      connectionSites.delete(connectionId);
    };
  }, [connectionSites, connectionId, x, y, source, target, sourceHandleId, targetHandleId]);

  // Handle adding a node on this edge
  const onAddNode = useCallback(
    (nodeType: SpicaNodeType) => {
      addNodeInBetween({
        type: nodeType,
        source,
        target,
        sourceHandleId,
        targetHandleId,
        position: { x, y },
      });
    },
    [addNodeInBetween, source, target, sourceHandleId, targetHandleId, x, y]
  );

  return (
    <EdgeLabelRenderer>
      <div
        style={{
          position: "absolute",
          transform: `translate(-50%, -50%) translate(${x}px, ${y}px)`,
          pointerEvents: "all",
        }}
        className="nodrag nopan"
      >
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              className={cn(
                "h-6 w-6 rounded-xl border-2 bg-card hover:bg-card",
                "hover:border-spica hover:text-spica",
                "transition-all duration-150",
                isPotentialConnection && "border-red-500 ring-2 ring-red-500/30"
              )}
              onClick={(e) => e.stopPropagation()}
            >
              <Plus className="h-3 w-3" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="center" className="w-48">
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              Insert Node
            </DropdownMenuLabel>
            {insertableNodes.map((nodeType) => {
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
      </div>
    </EdgeLabelRenderer>
  );
}
