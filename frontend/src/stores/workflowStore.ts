import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Node, Edge } from '@xyflow/react';

// Workflow specification from backend
export interface WorkflowSpec {
  intent?: string;
  trigger?: Record<string, unknown>;
  actions?: Array<Record<string, unknown>>;
  [key: string]: unknown;
}

// Graph node with our custom data
export interface GraphNode extends Node {
  data: {
    label: string;
    icon?: string;
    status?: string;
    [key: string]: unknown;
  };
}

// Graph edge
export type GraphEdge = Edge;

interface WorkflowState {
  // Workflow specification
  workflowSpec: WorkflowSpec | null;

  // Graph data
  nodes: GraphNode[];
  edges: GraphEdge[];

  // Workflow metadata
  workflowId: string | null;
  workflowName: string;
  workflowDescription: string;

  // Selection
  selectedNodeId: string | null;

  // Loading states
  isGenerating: boolean;
  isParsing: boolean;

  // Error states
  error: string | null;
  parseError: unknown | null;

  // Actions
  setWorkflowSpec: (spec: WorkflowSpec | null) => void;
  setNodes: (nodes: GraphNode[]) => void;
  setEdges: (edges: GraphEdge[]) => void;
  setWorkflowId: (id: string | null) => void;
  setWorkflowName: (name: string) => void;
  setWorkflowDescription: (description: string) => void;
  setSelectedNodeId: (nodeId: string | null) => void;
  setIsGenerating: (loading: boolean) => void;
  setIsParsing: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setParseError: (error: unknown | null) => void;

  // Complex actions
  addNode: (node: GraphNode) => void;
  addEdge: (edge: GraphEdge) => void;
  removeNode: (nodeId: string) => void;
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void;
  getSelectedNode: () => GraphNode | null;
  resetWorkflow: () => void;
  clearErrors: () => void;
}

export const useWorkflowStore = create<WorkflowState>()(
  devtools(
    (set, get) => ({
      // Initial state
      workflowSpec: null,
      nodes: [],
      edges: [],
      workflowId: null,
      workflowName: '',
      workflowDescription: '',
      selectedNodeId: null,
      isGenerating: false,
      isParsing: false,
      error: null,
      parseError: null,

      // Setters
      setWorkflowSpec: (spec) => set({ workflowSpec: spec }, false, 'setWorkflowSpec'),
      setNodes: (nodes) => set({ nodes }, false, 'setNodes'),
      setEdges: (edges) => set({ edges }, false, 'setEdges'),
      setWorkflowId: (id) => set({ workflowId: id }, false, 'setWorkflowId'),
      setWorkflowName: (name) => set({ workflowName: name }, false, 'setWorkflowName'),
      setWorkflowDescription: (description) => set({ workflowDescription: description }, false, 'setWorkflowDescription'),
      setSelectedNodeId: (nodeId) => set({ selectedNodeId: nodeId }, false, 'setSelectedNodeId'),
      setIsGenerating: (loading) => set({ isGenerating: loading }, false, 'setIsGenerating'),
      setIsParsing: (loading) => set({ isParsing: loading }, false, 'setIsParsing'),
      setError: (error) => set({ error }, false, 'setError'),
      setParseError: (error) => set({ parseError: error }, false, 'setParseError'),

      // Add node
      addNode: (node) =>
        set(
          (state) => ({
            nodes: [...state.nodes, node],
          }),
          false,
          'addNode'
        ),

      // Add edge
      addEdge: (edge) =>
        set(
          (state) => ({
            edges: [...state.edges, edge],
          }),
          false,
          'addEdge'
        ),

      // Remove node and its connected edges
      removeNode: (nodeId) =>
        set(
          (state) => ({
            nodes: state.nodes.filter((n) => n.id !== nodeId),
            edges: state.edges.filter(
              (e) => e.source !== nodeId && e.target !== nodeId
            ),
            selectedNodeId:
              state.selectedNodeId === nodeId ? null : state.selectedNodeId,
          }),
          false,
          'removeNode'
        ),

      // Update node data
      updateNodeData: (nodeId, data) =>
        set(
          (state) => ({
            nodes: state.nodes.map((node) =>
              node.id === nodeId
                ? { ...node, data: { ...node.data, ...data } }
                : node
            ),
          }),
          false,
          'updateNodeData'
        ),

      // Get selected node
      getSelectedNode: () => {
        const state = get();
        if (!state.selectedNodeId) return null;
        return state.nodes.find((n) => n.id === state.selectedNodeId) || null;
      },

      // Reset workflow
      resetWorkflow: () =>
        set(
          {
            workflowSpec: null,
            nodes: [],
            edges: [],
            workflowId: null,
            workflowName: '',
            workflowDescription: '',
            selectedNodeId: null,
            error: null,
            parseError: null,
          },
          false,
          'resetWorkflow'
        ),

      // Clear errors
      clearErrors: () =>
        set({ error: null, parseError: null }, false, 'clearErrors'),
    }),
    { name: 'workflow-store' }
  )
);
