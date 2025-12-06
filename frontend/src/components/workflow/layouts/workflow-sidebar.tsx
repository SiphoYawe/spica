"use client";

import { useState, useCallback } from "react";
import { GripVertical, Plus, Settings, HelpCircle, Command } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useDragAndDrop } from "../hooks";
import { nodesConfig, iconMapping, type SpicaNodeType } from "../config";

// Node types available in sidebar
const availableNodes: SpicaNodeType[] = ["trigger", "swap", "stake", "transfer"];

interface DraggableItemProps {
  nodeType: SpicaNodeType;
  collapsed?: boolean;
}

/**
 * DraggableItem - Draggable node template in sidebar
 */
function DraggableItem({ nodeType, collapsed }: DraggableItemProps) {
  const [isDragging, setIsDragging] = useState(false);
  const { createDragHandler } = useDragAndDrop();

  const config = nodesConfig[nodeType];
  const Icon = iconMapping[nodeType];

  const dragHandlers = createDragHandler(nodeType);

  const handleDragStart = useCallback(
    (e: React.DragEvent) => {
      setIsDragging(true);
      dragHandlers.onDragStart(e);
    },
    [dragHandlers]
  );

  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
    dragHandlers.onDragEnd();
  }, [dragHandlers]);

  const content = (
    <div
      draggable
      onDragStart={handleDragStart}
      onDrag={dragHandlers.onDrag}
      onDragEnd={handleDragEnd}
      className={cn(
        "relative cursor-grab select-none rounded-lg border-2 transition-all",
        "active:cursor-grabbing active:scale-[0.98]",
        isDragging
          ? "border-spica bg-spica/5 shadow-lg shadow-spica/10"
          : "border-border bg-card hover:border-muted-foreground/30",
        collapsed ? "p-2" : "p-3"
      )}
    >
      {/* Drag indicator badge (shows when dragging) */}
      {isDragging && (
        <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full border-2 border-spica bg-card">
          <Plus className="h-3 w-3 text-spica" />
        </span>
      )}

      <div className={cn("flex items-center", collapsed ? "justify-center" : "gap-3")}>
        {/* Icon */}
        <div
          className="flex h-8 w-8 items-center justify-center rounded"
          style={{ backgroundColor: config.color.bg }}
        >
          <Icon className="h-4 w-4" style={{ color: config.color.primary }} />
        </div>

        {/* Text content */}
        {!collapsed && (
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{config.title}</span>
              <GripVertical className="h-4 w-4 text-muted-foreground/50" />
            </div>
            <span className="text-xs text-muted-foreground line-clamp-1">
              {config.description}
            </span>
          </div>
        )}
      </div>
    </div>
  );

  // Wrap in tooltip when collapsed
  if (collapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>{content}</TooltipTrigger>
        <TooltipContent side="right">
          <p className="font-medium">{config.title}</p>
          <p className="text-xs text-muted-foreground">{config.description}</p>
        </TooltipContent>
      </Tooltip>
    );
  }

  return content;
}

interface WorkflowSidebarProps {
  collapsed?: boolean;
}

/**
 * WorkflowSidebar - Draggable node palette
 *
 * Features:
 * - Collapsible (icon-only mode)
 * - Drag-to-canvas node creation
 * - Tooltips in collapsed state
 * - Settings and help actions
 */
export function WorkflowSidebar({ collapsed = false }: WorkflowSidebarProps) {
  return (
    <TooltipProvider delayDuration={0}>
      <div
        className={cn(
          "flex h-full flex-col border-r border-border bg-sidebar transition-all duration-200",
          collapsed ? "w-16" : "w-64"
        )}
      >
        {/* Header */}
        <div className="flex items-center gap-2 border-b border-border px-4 py-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-spica/10">
            <Command className="h-4 w-4 text-spica" />
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <h2 className="text-sm font-semibold">Node Palette</h2>
              <p className="text-xs text-muted-foreground">Drag to canvas</p>
            </div>
          )}
        </div>

        {/* Node list */}
        <div className="flex-1 overflow-y-auto p-3">
          <div className={cn("flex flex-col", collapsed ? "gap-2" : "gap-3")}>
            {availableNodes.map((nodeType) => (
              <DraggableItem
                key={nodeType}
                nodeType={nodeType}
                collapsed={collapsed}
              />
            ))}
          </div>
        </div>

        {/* Footer actions */}
        <div className="mt-auto border-t border-border p-3">
          <div className={cn("flex", collapsed ? "flex-col gap-2" : "gap-2")}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size={collapsed ? "icon" : "sm"}
                  className={cn(!collapsed && "flex-1 justify-start")}
                >
                  <Settings className="h-4 w-4" />
                  {!collapsed && <span className="ml-2">Settings</span>}
                </Button>
              </TooltipTrigger>
              {collapsed && (
                <TooltipContent side="right">Settings</TooltipContent>
              )}
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size={collapsed ? "icon" : "sm"}
                  className={cn(!collapsed && "flex-1 justify-start")}
                >
                  <HelpCircle className="h-4 w-4" />
                  {!collapsed && <span className="ml-2">Help</span>}
                </Button>
              </TooltipTrigger>
              {collapsed && (
                <TooltipContent side="right">Help</TooltipContent>
              )}
            </Tooltip>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}
