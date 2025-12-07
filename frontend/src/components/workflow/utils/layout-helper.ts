import ELK from "elkjs/lib/elk.bundled.js";
import type { Node, Edge } from "@xyflow/react";
import { NODE_SIZE } from "../config";

// ELK instance
const elk = new ELK();

// ELK layout options with generous spacing for variable-height nodes
const layoutOptions = {
  "elk.algorithm": "layered",
  "elk.direction": "DOWN",
  "elk.layered.spacing.edgeNodeBetweenLayers": "50", // Vertical space between layers (edges)
  "elk.spacing.nodeNode": "80", // Horizontal space between nodes in same layer
  "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
  "elk.separateConnectedComponents": "true",
  "elk.spacing.componentComponent": "100",
  "elk.layered.spacing.nodeNodeBetweenLayers": "50", // Vertical space between node layers
  "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
};

/**
 * Estimate node height based on its data content
 * This accounts for dynamic content like multiple parameters, badges, etc.
 */
function estimateNodeHeight(node: Node): number {
  const data = node.data as Record<string, unknown> | undefined;

  // Base height: header (52px) + label area (40px) + padding (24px)
  let height = 116;

  if (!data) return height;

  // Add height for token/amount badges
  if (data.token || data.from_token || data.to_token) {
    height += 36; // Badge row
  }

  // Add height for amount display
  if (data.amount !== undefined) {
    height += 32; // Amount text
  }

  // Add height for recipient/pool info
  if (data.recipient || data.pool) {
    height += 24; // Additional info row
  }

  // Add height for trigger conditions
  if (data.operator && data.value !== undefined) {
    height += 32; // Condition display
  }

  // Add height for schedule/time info
  if (data.interval || data.time || data.schedule) {
    height += 28; // Schedule text
  }

  // Add height for duration
  if (data.duration) {
    height += 24;
  }

  // Clamp to min/max bounds
  return Math.max(NODE_SIZE.minHeight, Math.min(height, NODE_SIZE.maxHeight));
}

/**
 * layoutGraph - Apply ELK hierarchical layout to nodes
 *
 * @param nodes - Current nodes
 * @param edges - Current edges
 * @returns Nodes with updated positions
 */
export async function layoutGraph<N extends Node, E extends Edge>(
  nodes: N[],
  edges: E[]
): Promise<N[]> {
  // Convert to ELK format with dynamic height estimation
  const elkGraph = {
    id: "root",
    layoutOptions,
    children: nodes.map((node) => ({
      id: node.id,
      width: NODE_SIZE.width,
      height: estimateNodeHeight(node),
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  // Apply layout
  const layoutedGraph = await elk.layout(elkGraph);

  // Map positions back to nodes
  const positionMap = new Map<string, { x: number; y: number }>();

  layoutedGraph.children?.forEach((child) => {
    positionMap.set(child.id, {
      x: child.x ?? 0,
      y: child.y ?? 0,
    });
  });

  // Update node positions
  return nodes.map((node) => {
    const position = positionMap.get(node.id);
    if (position) {
      return {
        ...node,
        position,
      };
    }
    return node;
  });
}
