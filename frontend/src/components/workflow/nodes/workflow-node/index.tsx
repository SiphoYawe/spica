"use client";

import { useCallback, type ReactNode } from "react";
import { Play, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  BaseNode,
  BaseNodeHeader,
  BaseNodeHeaderTitle,
  NodeStatusIndicator,
  type NodeStatus,
} from "../../base";
import { NODE_SIZE, nodesConfig, iconMapping, type SpicaNodeType, type WorkflowNodeData } from "../../config";
import { useCanvasStoreSafe } from "../../store";

export interface WorkflowNodeProps {
  id: string;
  data: WorkflowNodeData;
  children?: ReactNode;
}

/**
 * WorkflowNode - Main node wrapper used by all Spica node types
 *
 * Features:
 * - Status indicator (loading spinner, success/error borders)
 * - Dynamic icon based on node type
 * - Play button to run workflow from this node
 * - Delete button to remove node
 * - Fixed dimensions matching Pro template (260×80)
 *
 * Note: Works in both editable mode (with CanvasStoreProvider) and
 * read-only mode (without provider). In read-only mode, action buttons are hidden.
 */
export function WorkflowNode({ id, data, children }: WorkflowNodeProps) {
  // Use safe hook that works with or without CanvasStoreProvider
  const { value: removeNode, isEditable } = useCanvasStoreSafe(
    (s) => s.removeNode
  );

  // Get node type from data or infer from icon
  const nodeType = data.icon as SpicaNodeType | undefined;
  const config = nodeType ? nodesConfig[nodeType] : null;

  // Get the icon component
  const IconComponent = nodeType ? iconMapping[nodeType] : null;

  // Get status for indicator
  const status = (data.status || "initial") as NodeStatus;

  // Get colors from config
  const colors = config?.color || {
    primary: "#6B7280",
    bg: "rgba(107, 114, 128, 0.08)",
    border: "rgba(107, 114, 128, 0.3)",
    glow: "rgba(107, 114, 128, 0.15)",
  };

  // Handle play button click
  const onPlay = useCallback(() => {
    // TODO: Integrate with workflow runner
    console.log("Run workflow from node:", id);
  }, [id]);

  // Handle delete button click
  const onRemove = useCallback(() => {
    removeNode(id);
  }, [id, removeNode]);

  return (
    <NodeStatusIndicator status={status} variant="overlay">
      <BaseNode
        style={{
          width: NODE_SIZE.width,
          minHeight: NODE_SIZE.height,
          borderColor: colors.border,
        }}
        className="overflow-visible"
      >
        {/* Type indicator bar at top */}
        <div
          className="absolute left-0 right-0 top-0 h-0.5 rounded-t-lg"
          style={{ backgroundColor: colors.primary }}
        />

        {/* Header */}
        <BaseNodeHeader>
          <div className="flex items-center gap-2.5">
            {/* Icon */}
            {IconComponent && (
              <div
                className="flex h-7 w-7 items-center justify-center rounded"
                style={{ backgroundColor: colors.bg }}
              >
                <IconComponent
                  className="h-4 w-4"
                  style={{ color: colors.primary }}
                  aria-label={config?.title}
                />
              </div>
            )}
            {/* Title */}
            <BaseNodeHeaderTitle>
              {data.title || config?.title || "Node"}
            </BaseNodeHeaderTitle>
          </div>

          {/* Action buttons - only shown in editable mode */}
          {isEditable && (
            <div className="flex items-center gap-1">
              {/* Play button */}
              <Button
                variant="ghost"
                size="icon"
                className={cn(
                  "nodrag h-6 w-6 rounded",
                  "hover:bg-spica/10 hover:text-spica"
                )}
                onClick={onPlay}
                title="Run from this node"
              >
                <Play className="h-3.5 w-3.5" />
              </Button>

              {/* Delete button */}
              <Button
                variant="ghost"
                size="icon"
                className={cn(
                  "nodrag h-6 w-6 rounded",
                  "hover:bg-destructive/10 hover:text-destructive"
                )}
                onClick={onRemove}
                title="Delete node"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          )}
        </BaseNodeHeader>

        {/* Content - renders node-specific children */}
        <div className="px-3 py-2">
          {data.label && (
            <div className="text-sm font-medium text-foreground truncate">
              {data.label}
            </div>
          )}
          {children}
        </div>
      </BaseNode>
    </NodeStatusIndicator>
  );
}
