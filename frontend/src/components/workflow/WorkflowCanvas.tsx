"use client";

import { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  type Connection,
  addEdge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { cn } from "@/lib/utils";
import { useWorkflowStore, useUiStore } from "@/stores";
import { nodeTypes } from "./nodes";
import { NLInput } from "./NLInput";

// Edge options
const defaultEdgeOptions = {
  animated: true,
  style: {
    strokeWidth: 2,
  },
};

// Fit view options
const fitViewOptions = {
  padding: 0.2,
  minZoom: 0.5,
  maxZoom: 1.5,
};

export function WorkflowCanvas() {
  const {
    nodes: storeNodes,
    edges: storeEdges,
    setEdges: setStoreEdges,
    setSelectedNodeId,
    isGenerating,
  } = useWorkflowStore();

  const {
    minimapVisible,
    gridVisible,
    openPropertiesPanel,
  } = useUiStore();

  // Local ReactFlow state synced with store
  const [nodes, setNodes, onNodesChange] = useNodesState(storeNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(storeEdges);

  // Sync store nodes to local state when they change
  useMemo(() => {
    if (storeNodes.length > 0) {
      setNodes(storeNodes);
    }
  }, [storeNodes, setNodes]);

  useMemo(() => {
    if (storeEdges.length > 0) {
      setEdges(storeEdges);
    }
  }, [storeEdges, setEdges]);

  // Handle new connections
  const onConnect = useCallback(
    (connection: Connection) => {
      const newEdges = addEdge(connection, edges);
      setEdges(newEdges);
      setStoreEdges(newEdges);
    },
    [edges, setEdges, setStoreEdges]
  );

  // Handle node selection
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: { id: string }) => {
      setSelectedNodeId(node.id);
      openPropertiesPanel();
    },
    [setSelectedNodeId, openPropertiesPanel]
  );

  // Handle pane click (deselect)
  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, [setSelectedNodeId]);

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

  const hasNodes = nodes.length > 0;

  return (
    <div className="relative h-full w-full">
      {/* Empty state with NL input */}
      {!hasNodes && !isGenerating && (
        <div className="absolute inset-0 z-10 flex items-center justify-center">
          <div className="w-full max-w-2xl px-6">
            <div className="mb-8 text-center">
              <h1 className="mb-2 text-2xl font-semibold tracking-tight">
                Create a DeFi Workflow
              </h1>
              <p className="text-muted-foreground">
                Describe what you want to automate in plain English. Spica will
                generate the workflow for you.
              </p>
            </div>
            <NLInput />
          </div>
        </div>
      )}

      {/* Loading state */}
      {isGenerating && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/50 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-4">
            <div className="relative h-12 w-12">
              <div className="absolute inset-0 rounded-full border-2 border-spica/20" />
              <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-spica" />
            </div>
            <p className="text-sm text-muted-foreground">
              Generating your workflow...
            </p>
          </div>
        </div>
      )}

      {/* ReactFlow Canvas */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        fitView
        fitViewOptions={fitViewOptions}
        minZoom={0.1}
        maxZoom={2}
        className={cn(
          "bg-canvas",
          hasNodes ? "opacity-100" : "opacity-50"
        )}
        proOptions={{ hideAttribution: true }}
      >
        {/* Background */}
        {gridVisible && (
          <Background
            variant={BackgroundVariant.Dots}
            gap={20}
            size={1}
            color="var(--canvas-grid)"
          />
        )}

        {/* Controls */}
        <Controls
          showInteractive={false}
          className="!border-border !bg-card/95 !rounded-lg !shadow-lg"
        />

        {/* MiniMap - Smaller size */}
        {minimapVisible && (
          <MiniMap
            nodeColor={nodeColor}
            maskColor="rgba(0, 0, 0, 0.6)"
            className="!border-border !bg-card/95 !rounded-lg !shadow-lg !w-[120px] !h-[80px]"
            pannable={false}
            zoomable={false}
          />
        )}
      </ReactFlow>

      {/* Floating NL input when workflow exists */}
      {hasNodes && (
        <div className="absolute left-1/2 top-4 z-10 -translate-x-1/2">
          <NLInput />
        </div>
      )}
    </div>
  );
}
