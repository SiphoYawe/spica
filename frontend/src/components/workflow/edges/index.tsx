import { type Edge } from "@xyflow/react";
import { WorkflowEdge } from "./workflow-edge";

// Edge data type (empty for now, can be extended)
export type SpicaEdgeData = Record<string, never>;

// Typed edge
export type SpicaEdge = Edge<SpicaEdgeData, "workflow">;

// Edge type registry for ReactFlow
export const edgeTypes = {
  workflow: WorkflowEdge,
} as const;

// Default edge options
export const defaultEdgeOptions = {
  type: "workflow" as const,
  animated: true,
};

// Factory function to create edges
export function createEdge(
  source: string,
  target: string,
  sourceHandleId?: string | null,
  targetHandleId?: string | null
): SpicaEdge {
  return {
    id: `${source}-${sourceHandleId || "default"}-${target}-${targetHandleId || "default"}`,
    source,
    target,
    sourceHandle: sourceHandleId ?? undefined,
    targetHandle: targetHandleId ?? undefined,
    type: "workflow",
    animated: true,
  };
}

// Re-export components
export { WorkflowEdge } from "./workflow-edge";
export { EdgeButton } from "./workflow-edge/edge-button";
