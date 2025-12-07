"use client";

import { useCallback, useEffect, useRef } from "react";
import {
  ReactFlow,
  Background,
  MiniMap,
  Panel,
  useNodesState,
  useEdgesState,
  useStore,
  useViewport,
  BackgroundVariant,
  useReactFlow,
  type Connection,
  type ColorMode,
  type XYPosition,
  type NodeChange,
  type EdgeChange,
  addEdge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { nanoid } from "nanoid";

import { useWorkflowStore, useUiStore, type GraphNode } from "@/stores";
import { nodeTypes } from "./nodes";
import { NLInput } from "./NLInput";
import { NODE_SIZE, nodesConfig, type SpicaNodeType } from "./config";
import { layoutGraph } from "./utils/layout-helper";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Minus, Plus, Maximize, Route } from "lucide-react";

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

// Dark mode only - no theme switching
const colorMode: ColorMode = "dark";

// Helper to create a node from a type
function createNodeFromType(
  type: SpicaNodeType,
  position: XYPosition
) {
  const config = nodesConfig[type];

  // Center the node on the drop position
  const centeredPosition = {
    x: position.x - NODE_SIZE.width / 2,
    y: position.y - NODE_SIZE.height / 2,
  };

  return {
    id: nanoid(),
    type,
    position: centeredPosition,
    data: {
      label: config.title,
      icon: type,
      status: "initial",
    },
  } as const;
}

/**
 * ZoomSlider - Zoom control with slider and buttons
 */
function ZoomSlider() {
  const { zoomIn, zoomOut, fitView, setViewport } = useReactFlow();
  const { zoom } = useViewport();

  // Get zoom limits from store
  const minZoom = useStore((state) => state.minZoom);
  const maxZoom = useStore((state) => state.maxZoom);

  // Handle slider change
  const onZoomChange = useCallback(
    (value: number[]) => {
      setViewport({ x: 0, y: 0, zoom: value[0] }, { duration: 300 });
    },
    [setViewport]
  );

  // Zoom percentage display
  const zoomPercent = Math.round(zoom * 100);

  return (
    <TooltipProvider delayDuration={0}>
      <Panel
        position="bottom-left"
        className="!m-4 flex items-center gap-1 rounded-lg border border-border bg-card/95 p-1 backdrop-blur-sm shadow-lg"
      >
        {/* Zoom out */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => zoomOut({ duration: 300 })}
            >
              <Minus className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">Zoom out</TooltipContent>
        </Tooltip>

        {/* Slider */}
        <div className="w-[100px] px-2">
          <Slider
            value={[zoom]}
            min={minZoom}
            max={maxZoom}
            step={0.01}
            onValueChange={onZoomChange}
            className="cursor-pointer"
          />
        </div>

        {/* Zoom in */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => zoomIn({ duration: 300 })}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">Zoom in</TooltipContent>
        </Tooltip>

        {/* Separator */}
        <div className="mx-1 h-5 w-px bg-border" />

        {/* Zoom percentage */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-12 text-xs font-mono"
              onClick={() => setViewport({ x: 0, y: 0, zoom: 1 }, { duration: 300 })}
            >
              {zoomPercent}%
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">Reset zoom to 100%</TooltipContent>
        </Tooltip>

        {/* Fit view */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => fitView({ duration: 300, padding: 0.2 })}
            >
              <Maximize className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">Fit to view</TooltipContent>
        </Tooltip>
      </Panel>
    </TooltipProvider>
  );
}

/**
 * LayoutButton - Auto-layout trigger using ELK algorithm
 */
function LayoutButton({
  onLayout,
}: {
  onLayout: () => void;
}) {
  return (
    <TooltipProvider delayDuration={0}>
      <Panel
        position="bottom-right"
        className="!m-4 rounded-lg border border-border bg-card/95 p-1 backdrop-blur-sm shadow-lg"
      >
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={onLayout}
            >
              <Route className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="left">Auto-layout nodes</TooltipContent>
        </Tooltip>
      </Panel>
    </TooltipProvider>
  );
}

export function WorkflowCanvas() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition, fitView } = useReactFlow();

  const {
    nodes: storeNodes,
    edges: storeEdges,
    setEdges: setStoreEdges,
    setNodes: setStoreNodes,
    addNode,
    removeNode,
    addEdge: addStoreEdge,
    setSelectedNodeId,
    isGenerating,
  } = useWorkflowStore();

  const {
    minimapVisible,
    gridVisible,
    openPropertiesPanel,
    closePropertiesPanel,
  } = useUiStore();

  // Local ReactFlow state synced with store
  const [nodes, setNodes, onNodesChangeBase] = useNodesState(storeNodes);
  const [edges, setEdges, onEdgesChangeBase] = useEdgesState(storeEdges);

  // Sync store nodes to local state when they change
  useEffect(() => {
    setNodes(storeNodes);
  }, [storeNodes, setNodes]);

  useEffect(() => {
    setEdges(storeEdges);
  }, [storeEdges, setEdges]);

  // Wrap onNodesChange to sync removals to the workflow store
  const onNodesChange = useCallback(
    (changes: NodeChange<GraphNode>[]) => {
      // Apply changes to local state
      onNodesChangeBase(changes);

      // Sync removals to the workflow store
      changes.forEach((change) => {
        if (change.type === "remove") {
          removeNode(change.id);
        }
      });
    },
    [onNodesChangeBase, removeNode]
  );

  // Wrap onEdgesChange to sync removals to the workflow store
  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      // Apply changes to local state
      onEdgesChangeBase(changes);

      // When edges are removed, sync to store
      const removeChanges = changes.filter((c) => c.type === "remove");
      if (removeChanges.length > 0) {
        // Get current edges after applying changes and sync to store
        setEdges((currentEdges) => {
          const remainingEdgeIds = new Set(
            removeChanges.map((c) => c.id)
          );
          const filteredEdges = currentEdges.filter(
            (e) => !remainingEdgeIds.has(e.id)
          );
          setStoreEdges(filteredEdges);
          return currentEdges; // Let ReactFlow handle the actual removal
        });
      }
    },
    [onEdgesChangeBase, setEdges, setStoreEdges]
  );

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

  // Handle pane click (deselect and close panel)
  const onPaneClick = useCallback(() => {
    setSelectedNodeId(null);
    closePropertiesPanel();
  }, [setSelectedNodeId, closePropertiesPanel]);

  // Handle drag over (allow drop)
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  // Handle drop - create node at drop position
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      // Get node type from drag data
      const nodeType = event.dataTransfer.getData(
        "application/reactflow"
      ) as SpicaNodeType;

      // Validate node type
      if (!nodeType || !nodesConfig[nodeType]) {
        return;
      }

      // Convert screen position to flow position
      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      // Create the new node
      const newNode = createNodeFromType(nodeType, position);

      // Add to local state immediately for instant feedback
      setNodes((nds) => [...nds, newNode]);

      // Also add to store for persistence
      addNode(newNode);

      // Check if we should auto-connect to nearby nodes
      const nearbyNode = nodes.find((node) => {
        const dx = Math.abs(node.position.x + NODE_SIZE.width / 2 - position.x);
        const dy = Math.abs(node.position.y + NODE_SIZE.height / 2 - position.y);
        return dx < 200 && dy < 150;
      });

      if (nearbyNode) {
        // Determine connection direction based on node types
        const nearbyConfig = nodesConfig[nearbyNode.type as SpicaNodeType];
        const newConfig = nodesConfig[nodeType];

        // Check if nearby node has a source handle and new node has target
        const nearbyHasSource = nearbyConfig?.handles.some(
          (h) => h.type === "source"
        );
        const newHasTarget = newConfig?.handles.some((h) => h.type === "target");

        // Check if nearby node has a target handle and new node has source
        const nearbyHasTarget = nearbyConfig?.handles.some(
          (h) => h.type === "target"
        );
        const newHasSource = newConfig?.handles.some((h) => h.type === "source");

        // Determine if new node is above or below nearby node
        const isNewNodeBelow = position.y > nearbyNode.position.y;

        if (isNewNodeBelow && nearbyHasSource && newHasTarget) {
          // Connect nearby (source) -> new node (target)
          const newEdge = {
            id: `${nearbyNode.id}-${newNode.id}`,
            source: nearbyNode.id,
            target: newNode.id,
            animated: true,
          };
          setEdges((eds) => [...eds, newEdge]);
          setStoreEdges([...edges, newEdge]);
        } else if (!isNewNodeBelow && nearbyHasTarget && newHasSource) {
          // Connect new node (source) -> nearby (target)
          const newEdge = {
            id: `${newNode.id}-${nearbyNode.id}`,
            source: newNode.id,
            target: nearbyNode.id,
            animated: true,
          };
          setEdges((eds) => [...eds, newEdge]);
          setStoreEdges([...edges, newEdge]);
        }
      }
    },
    [screenToFlowPosition, setNodes, addNode, nodes, edges, setEdges, setStoreEdges]
  );

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

  // Auto-layout using ELK algorithm
  const handleAutoLayout = useCallback(async () => {
    if (nodes.length === 0) return;

    try {
      const layoutedNodes = await layoutGraph(nodes, edges);
      setNodes(layoutedNodes);
      setStoreNodes(layoutedNodes);
      // Fit view after layout to show all nodes
      setTimeout(() => fitView({ duration: 300, padding: 0.2 }), 50);
    } catch (error) {
      console.error("Layout error:", error);
    }
  }, [nodes, edges, setNodes, setStoreNodes, fitView]);

  const hasNodes = nodes.length > 0;

  return (
    <div className="relative h-full w-full">
      {/* Empty state with NL input */}
      {!hasNodes && !isGenerating && (
        <div className="absolute inset-0 z-10 flex items-center justify-center pointer-events-none">
          <div className="w-full max-w-2xl px-6 pointer-events-auto">
            <div className="mb-8 text-center">
              <h1 className="mb-2 text-2xl font-semibold tracking-tight">
                Create a DeFi Workflow
              </h1>
              <p className="text-muted-foreground">
                Describe what you want to automate in plain English, or drag
                nodes from the sidebar to build your workflow manually.
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
        onDragOver={onDragOver}
        onDrop={onDrop}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        fitView
        fitViewOptions={fitViewOptions}
        minZoom={0.1}
        maxZoom={2}
        colorMode={colorMode}
        className="bg-canvas"
        proOptions={{ hideAttribution: true }}
      >
        {/* Background - Subtle white dots pattern */}
        {gridVisible && (
          <Background
            variant={BackgroundVariant.Dots}
            gap={24}
            size={1.5}
            color="rgba(255, 255, 255, 0.15)"
          />
        )}

        {/* Zoom Controls */}
        <ZoomSlider />

        {/* Auto-layout Button */}
        <LayoutButton onLayout={handleAutoLayout} />

        {/* MiniMap - Positioned above the layout button */}
        {minimapVisible && (
          <MiniMap
            nodeColor={nodeColor}
            maskColor="rgba(0, 0, 0, 0.6)"
            className="!border-border !bg-card/95 !rounded-lg !shadow-lg !w-[120px] !h-[80px] !bottom-16 !right-4"
            pannable={false}
            zoomable={false}
          />
        )}
      </ReactFlow>

{/* NL input is hidden once nodes exist - users can drag more nodes from sidebar */}
    </div>
  );
}
