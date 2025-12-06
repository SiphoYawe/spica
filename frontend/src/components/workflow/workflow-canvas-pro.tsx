"use client";

import { useCallback } from "react";
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  type ColorMode,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useShallow } from "zustand/react/shallow";
import { cn } from "@/lib/utils";
import { useCanvasStore, type CanvasStore } from "./store";
import { nodeTypes } from "./nodes";
import { edgeTypes, defaultEdgeOptions } from "./edges";
import { useDragAndDrop } from "./hooks";
import {
  WorkflowControls,
  FlowRunButton,
  FlowContextMenu,
} from "./components";
import { NLInput } from "./NLInput";

// Fit view options
const fitViewOptions = {
  padding: 0.2,
  minZoom: 0.5,
  maxZoom: 1.5,
};

// Dark mode only - no theme switching
const colorMode: ColorMode = "dark";

/**
 * WorkflowCanvasPro - Main workflow canvas with Pro template design
 *
 * Features:
 * - Drag-and-drop node creation
 * - Right-click context menu
 * - Pro-style edges with insertion buttons
 * - Custom zoom controls
 * - Auto-layout capability
 * - Node status indicators
 */
export function WorkflowCanvasPro() {

  // Store selectors
  const selector = useCallback(
    (state: CanvasStore) => ({
      nodes: state.nodes,
      edges: state.edges,
      onNodesChange: state.onNodesChange,
      onEdgesChange: state.onEdgesChange,
      onConnect: state.onConnect,
      onNodeDragStart: state.onNodeDragStart,
      onNodeDragStop: state.onNodeDragStop,
    }),
    []
  );

  const store = useCanvasStore(useShallow(selector));
  const { onDragOver, onDrop } = useDragAndDrop();

  const hasNodes = store.nodes.length > 0;

  return (
    <div className="relative h-full w-full">
      {/* Empty state with NL input */}
      {!hasNodes && (
        <div className="absolute inset-0 z-10 flex items-center justify-center">
          <div className="w-full max-w-2xl px-6">
            <div className="mb-8 text-center">
              <h1 className="mb-2 text-2xl font-semibold tracking-tight">
                Create a DeFi Workflow
              </h1>
              <p className="text-muted-foreground">
                Describe what you want to automate in plain English, or drag
                nodes from the sidebar to build your workflow.
              </p>
            </div>
            <NLInput />
          </div>
        </div>
      )}

      {/* ReactFlow Canvas */}
      <ReactFlow
        nodes={store.nodes}
        edges={store.edges}
        onNodesChange={store.onNodesChange}
        onEdgesChange={store.onEdgesChange}
        onConnect={store.onConnect}
        onNodeDragStart={store.onNodeDragStart}
        onNodeDragStop={store.onNodeDragStop}
        onDragOver={onDragOver}
        onDrop={onDrop}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        fitView
        fitViewOptions={fitViewOptions}
        minZoom={0.1}
        maxZoom={2}
        colorMode={colorMode}
        className={cn("bg-canvas", hasNodes ? "opacity-100" : "opacity-50")}
        proOptions={{ hideAttribution: true }}
      >
        {/* Background */}
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="var(--canvas-grid)"
        />

        {/* Controls */}
        <WorkflowControls />

        {/* Run button */}
        <FlowRunButton />

        {/* Right-click menu */}
        <FlowContextMenu />
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
