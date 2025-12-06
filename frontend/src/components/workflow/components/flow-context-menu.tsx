"use client";

import { useState, useCallback, useEffect } from "react";
import { useReactFlow } from "@xyflow/react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useCanvasStore } from "../store";
import { nodesConfig, iconMapping, type SpicaNodeType } from "../config";

// All available node types for context menu
const availableNodes: SpicaNodeType[] = ["trigger", "swap", "stake", "transfer"];

interface ContextMenuPosition {
  x: number;
  y: number;
  flowX: number;
  flowY: number;
}

/**
 * FlowContextMenu - Right-click menu for adding nodes
 *
 * Features:
 * - Shows at cursor position on right-click
 * - Creates node at click position
 * - Lists all available node types with icons
 */
export function FlowContextMenu() {
  const [position, setPosition] = useState<ContextMenuPosition | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const { screenToFlowPosition } = useReactFlow();
  const addNodeByType = useCanvasStore((s) => s.addNodeByType);

  // Handle right-click on canvas pane
  useEffect(() => {
    const handleContextMenu = (event: MouseEvent) => {
      // Check if right-click is on the canvas pane
      const target = event.target as HTMLElement;
      const isPane = target.classList.contains("react-flow__pane");

      if (isPane) {
        event.preventDefault();

        const flowPosition = screenToFlowPosition({
          x: event.clientX,
          y: event.clientY,
        });

        setPosition({
          x: event.clientX,
          y: event.clientY,
          flowX: flowPosition.x,
          flowY: flowPosition.y,
        });
        setIsOpen(true);
      }
    };

    document.addEventListener("contextmenu", handleContextMenu);
    return () => document.removeEventListener("contextmenu", handleContextMenu);
  }, [screenToFlowPosition]);

  // Handle adding a node
  const onAddNode = useCallback(
    (nodeType: SpicaNodeType) => {
      if (!position) return;

      addNodeByType(nodeType, { x: position.flowX, y: position.flowY });
      setIsOpen(false);
      setPosition(null);
    },
    [position, addNodeByType]
  );


  if (!position) return null;

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <div
          className="fixed"
          style={{
            left: position.x,
            top: position.y,
            width: 1,
            height: 1,
          }}
        />
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-52" align="start">
        <DropdownMenuLabel className="text-xs text-muted-foreground">
          Add Node
        </DropdownMenuLabel>
        {availableNodes.map((nodeType) => {
          const config = nodesConfig[nodeType];
          const Icon = iconMapping[nodeType];
          return (
            <DropdownMenuItem
              key={nodeType}
              onClick={() => onAddNode(nodeType)}
              className="flex items-center gap-3"
            >
              <div
                className="flex h-7 w-7 items-center justify-center rounded"
                style={{ backgroundColor: config.color.bg }}
              >
                <Icon
                  className="h-4 w-4"
                  style={{ color: config.color.primary }}
                />
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium">{config.title}</div>
                <div className="text-xs text-muted-foreground line-clamp-1">
                  {config.description}
                </div>
              </div>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
