"use client";

import { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { cn } from "@/lib/utils";
import { nodeTypes } from "./nodes";

// Edge options for read-only mode
const defaultEdgeOptions = {
  animated: true,
  style: {
    strokeWidth: 2,
  },
};

// Fit view options
const fitViewOptions = {
  padding: 0.3,
  minZoom: 0.5,
  maxZoom: 1.5,
};

interface ReadOnlyGraphProps {
  nodes: Node[];
  edges: Edge[];
  className?: string;
}

export function ReadOnlyGraph({ nodes, edges, className }: ReadOnlyGraphProps) {
  // Convert nodes to proper format with positions
  const processedNodes = useMemo(() => {
    return nodes.map((node) => ({
      ...node,
      draggable: false,
      selectable: false,
      connectable: false,
    }));
  }, [nodes]);

  // Node color for minimap
  const nodeColor = useCallback((node: { type?: string }) => {
    switch (node.type) {
      case "trigger":
        return "#F59E0B";
      case "swap":
        return "#06B6D4";
      case "stake":
        return "#10B981";
      case "transfer":
        return "#3B82F6";
      default:
        return "#6B7280";
    }
  }, []);

  return (
    <div
      className={cn("h-full w-full", className)}
      role="img"
      aria-label="Read-only workflow visualization graph"
    >
      <ReactFlow
        nodes={processedNodes}
        edges={edges}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        fitView
        fitViewOptions={fitViewOptions}
        minZoom={0.1}
        maxZoom={2}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag
        zoomOnScroll
        className="bg-canvas"
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="var(--canvas-grid)"
        />
        <Controls
          showInteractive={false}
          className="!border-border !bg-card/95 !rounded-lg !shadow-lg"
        />
        <MiniMap
          nodeColor={nodeColor}
          maskColor="rgba(0, 0, 0, 0.6)"
          className="!border-border !bg-card/95 !rounded-lg !shadow-lg !w-[100px] !h-[70px]"
          pannable={false}
          zoomable={false}
        />
      </ReactFlow>
    </div>
  );
}
