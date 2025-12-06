import ELK from "elkjs/lib/elk.bundled.js";
import type { Node, Edge } from "@xyflow/react";
import { NODE_SIZE } from "../config";

// ELK instance
const elk = new ELK();

// ELK layout options
const layoutOptions = {
  "elk.algorithm": "layered",
  "elk.direction": "DOWN",
  "elk.layered.spacing.edgeNodeBetweenLayers": "80",
  "elk.spacing.nodeNode": "100",
  "elk.layered.nodePlacement.strategy": "SIMPLE",
  "elk.separateConnectedComponents": "true",
  "elk.spacing.componentComponent": "100",
  "elk.layered.spacing.nodeNodeBetweenLayers": "80",
};

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
  // Convert to ELK format
  const elkGraph = {
    id: "root",
    layoutOptions,
    children: nodes.map((node) => ({
      id: node.id,
      width: NODE_SIZE.width,
      height: NODE_SIZE.height,
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
