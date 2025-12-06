import { createStore } from "zustand/vanilla";
import { subscribeWithSelector } from "zustand/middleware";
import {
  applyNodeChanges,
  applyEdgeChanges,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
  type XYPosition,
  type Connection,
} from "@xyflow/react";
import { nanoid } from "nanoid";
import {
  NODE_SIZE,
  nodesConfig,
  type SpicaNode,
  type SpicaNodeType,
  type WorkflowNodeData,
} from "../config";
import { createEdge, type SpicaEdge } from "../edges";

// Connection site for drag-drop detection
export interface PotentialConnection {
  id: string;
  position: XYPosition;
  type?: "source" | "target";
  source?: {
    node: string;
    handle?: string | null;
  };
  target?: {
    node: string;
    handle?: string | null;
  };
}

// Canvas state
export interface CanvasState {
  // Graph data
  nodes: SpicaNode[];
  edges: SpicaEdge[];

  // Layout mode
  layout: "fixed" | "free";

  // Drag tracking
  draggedNodes: Map<string, SpicaNode>;

  // Connection sites for smart drop
  connectionSites: Map<string, PotentialConnection>;
  potentialConnection?: PotentialConnection;
}

// Canvas actions
export interface CanvasActions {
  // Layout
  toggleLayout: () => void;

  // Node operations
  onNodesChange: OnNodesChange<SpicaNode>;
  setNodes: (nodes: SpicaNode[]) => void;
  getNodes: () => SpicaNode[];
  addNode: (node: SpicaNode) => void;
  removeNode: (nodeId: string) => void;
  addNodeByType: (type: SpicaNodeType, position: XYPosition) => string | null;
  addNodeInBetween: (options: {
    type: SpicaNodeType;
    source?: string;
    target?: string;
    sourceHandleId?: string | null;
    targetHandleId?: string | null;
    position: XYPosition;
  }) => void;
  updateNodeData: (nodeId: string, data: Partial<WorkflowNodeData>) => void;
  updateNodeStatus: (
    nodeId: string,
    status: WorkflowNodeData["status"]
  ) => void;

  // Edge operations
  onEdgesChange: OnEdgesChange<SpicaEdge>;
  onConnect: OnConnect;
  setEdges: (edges: SpicaEdge[]) => void;
  getEdges: () => SpicaEdge[];
  addEdge: (edge: SpicaEdge) => void;
  removeEdge: (edgeId: string) => void;

  // Drag handling
  onNodeDragStart: (
    event: React.MouseEvent,
    node: SpicaNode,
    nodes: SpicaNode[]
  ) => void;
  onNodeDragStop: () => void;

  // Connection site detection
  checkForPotentialConnection: (
    position: XYPosition,
    options?: {
      type?: "source" | "target";
      exclude?: string[];
    }
  ) => void;
  resetPotentialConnection: () => void;
}

// Combined store type
export type CanvasStore = CanvasState & CanvasActions;

// Create node by type helper
function createNodeByType(
  type: SpicaNodeType,
  position: XYPosition,
  id?: string,
  data?: Partial<WorkflowNodeData>
): SpicaNode {
  const config = nodesConfig[type];

  // Center the node on the given position
  const centeredPosition = {
    x: position.x - NODE_SIZE.width / 2,
    y: position.y - NODE_SIZE.height / 2,
  };

  return {
    id: id || nanoid(),
    type,
    position: centeredPosition,
    data: {
      title: config.title,
      label: "",
      icon: type,
      status: "initial",
      ...data,
    },
  };
}

// Create the store
export function createCanvasStore(
  initialState?: Partial<CanvasState>
) {
  return createStore<CanvasStore>()(
    subscribeWithSelector((set, get) => ({
      // Initial state
      nodes: initialState?.nodes ?? [],
      edges: initialState?.edges ?? [],
      layout: initialState?.layout ?? "free",
      draggedNodes: new Map(),
      connectionSites: new Map(),
      potentialConnection: undefined,

      // Toggle layout mode
      toggleLayout: () =>
        set((state) => ({
          layout: state.layout === "fixed" ? "free" : "fixed",
        })),

      // Node change handler (from ReactFlow)
      onNodesChange: (changes) => {
        set((state) => ({
          nodes: applyNodeChanges(changes, state.nodes),
        }));
      },

      // Set all nodes
      setNodes: (nodes) => set({ nodes }),

      // Get current nodes
      getNodes: () => get().nodes,

      // Add single node
      addNode: (node) => {
        set((state) => ({
          nodes: [...state.nodes, node],
        }));
      },

      // Remove node and connected edges
      removeNode: (nodeId) => {
        const { nodes, edges } = get();
        set({
          nodes: nodes.filter((n) => n.id !== nodeId),
          edges: edges.filter(
            (e) => e.source !== nodeId && e.target !== nodeId
          ),
        });
      },

      // Add node by type at position
      addNodeByType: (type, position) => {
        const newNode = createNodeByType(type, position);
        get().addNode(newNode);
        return newNode.id;
      },

      // Add node between existing nodes (for edge insertion)
      addNodeInBetween: ({
        type,
        source,
        target,
        sourceHandleId,
        targetHandleId,
        position,
      }) => {
        const newNode = createNodeByType(type, position);
        const newNodeId = newNode.id;

        // Get handle IDs from the new node's config
        const newNodeConfig = nodesConfig[type];
        const newNodeTargetHandle = newNodeConfig.handles.find(
          (h) => h.type === "target"
        );
        const newNodeSourceHandle = newNodeConfig.handles.find(
          (h) => h.type === "source"
        );

        // Add the new node
        get().addNode(newNode);

        // If we have source/target info, rewire the edges
        if (source && target) {
          // Remove the original edge
          const edgeId = `${source}-${sourceHandleId || "default"}-${target}-${targetHandleId || "default"}`;
          get().removeEdge(edgeId);

          // Create two new edges
          const edge1 = createEdge(
            source,
            newNodeId,
            sourceHandleId,
            newNodeTargetHandle?.id
          );
          const edge2 = createEdge(
            newNodeId,
            target,
            newNodeSourceHandle?.id,
            targetHandleId
          );

          set((state) => ({
            edges: [...state.edges, edge1, edge2],
          }));
        }
      },

      // Update node data
      updateNodeData: (nodeId, data) => {
        set((state) => ({
          nodes: state.nodes.map((node) =>
            node.id === nodeId
              ? { ...node, data: { ...node.data, ...data } }
              : node
          ),
        }));
      },

      // Update node status
      updateNodeStatus: (nodeId, status) => {
        get().updateNodeData(nodeId, { status });
      },

      // Edge change handler (from ReactFlow)
      onEdgesChange: (changes) => {
        set((state) => ({
          edges: applyEdgeChanges(changes, state.edges),
        }));
      },

      // Connection handler (from ReactFlow)
      onConnect: (connection: Connection) => {
        if (!connection.source || !connection.target) return;

        const newEdge = createEdge(
          connection.source,
          connection.target,
          connection.sourceHandle,
          connection.targetHandle
        );

        get().addEdge(newEdge);
      },

      // Set all edges
      setEdges: (edges) => set({ edges }),

      // Get current edges
      getEdges: () => get().edges,

      // Add single edge
      addEdge: (edge) => {
        set((state) => ({
          edges: [...state.edges, edge],
        }));
      },

      // Remove edge
      removeEdge: (edgeId) => {
        set((state) => ({
          edges: state.edges.filter((e) => e.id !== edgeId),
        }));
      },

      // Track dragged nodes
      onNodeDragStart: (_, __, nodes) => {
        set({
          draggedNodes: new Map(nodes.map((node) => [node.id, node])),
        });
      },

      // Clear drag state
      onNodeDragStop: () => {
        set({
          draggedNodes: new Map(),
          potentialConnection: undefined,
        });
      },

      // Check for nearby connection sites
      checkForPotentialConnection: (position, options) => {
        const { connectionSites } = get();

        let closest: {
          distance: number;
          connection?: PotentialConnection;
        } = { distance: Infinity };

        for (const site of connectionSites.values()) {
          // Skip excluded sites
          if (options?.exclude?.includes(site.id)) continue;

          // Skip wrong type (source can't connect to source, etc.)
          if (options?.type && options.type === site.type) continue;

          // Calculate distance
          const distance = Math.hypot(
            site.position.x - position.x,
            site.position.y - position.y
          );

          if (distance < closest.distance) {
            closest = { distance, connection: site };
          }
        }

        // Only show if within 150px threshold
        set({
          potentialConnection:
            closest.distance < 150 ? closest.connection : undefined,
        });
      },

      // Reset potential connection
      resetPotentialConnection: () => {
        set({ potentialConnection: undefined });
      },
    }))
  );
}
