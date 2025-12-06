"use client";

import { memo } from "react";
import {
  BaseEdge,
  getBezierPath,
  type EdgeProps,
} from "@xyflow/react";
import { EdgeButton } from "./edge-button";
import type { SpicaEdge } from "../index";

/**
 * WorkflowEdge - Custom edge with animated path and edge button
 *
 * Features:
 * - Bezier path for smooth curves
 * - Animated dash pattern (via CSS)
 * - Interactive button at midpoint for node insertion
 * - Spica green accent when selected
 */
function WorkflowEdgeComponent({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  source,
  sourceHandleId,
  target,
  targetHandleId,
  style = {},
  markerEnd,
  selected,
}: EdgeProps<SpicaEdge>) {
  // Calculate bezier path and label position
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      {/* Main edge path */}
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          strokeWidth: 2,
          stroke: selected ? "var(--spica)" : "var(--muted-foreground)",
          pointerEvents: "auto",
        }}
      />

      {/* Edge button at midpoint */}
      <EdgeButton
        x={labelX}
        y={labelY}
        id={id}
        source={source}
        target={target}
        sourceHandleId={sourceHandleId}
        targetHandleId={targetHandleId}
      />
    </>
  );
}

export const WorkflowEdge = memo(WorkflowEdgeComponent);
