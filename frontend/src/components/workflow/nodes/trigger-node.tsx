"use client";

import { memo } from "react";
import { Badge } from "@/components/ui/badge";
import { WorkflowNode } from "./workflow-node";
import { NodeHandle } from "./workflow-node/node-handle";
import { nodesConfig, type WorkflowNodeData } from "../config";

export interface TriggerNodeData extends WorkflowNodeData {
  triggerType?: "price" | "time";
  token?: string;
  operator?: ">" | "<" | ">=" | "<=" | "==";
  value?: string | number;
  schedule?: string;
}

interface TriggerNodeProps {
  id: string;
  data: TriggerNodeData;
}

/**
 * TriggerNode - Workflow entry point
 *
 * Triggered by:
 * - Price conditions (e.g., "When NEO > $15")
 * - Time schedules (e.g., "Every day at 9:00 AM")
 */
function TriggerNodeComponent({ id, data }: TriggerNodeProps) {
  const nodeData: WorkflowNodeData = {
    ...data,
    icon: "trigger",
    title: data.title || "Trigger",
  };

  // Format the trigger condition for display
  const formatCondition = () => {
    if (data.triggerType === "price" && data.token && data.operator && data.value) {
      return `${data.token} ${data.operator} $${data.value}`;
    }
    if (data.triggerType === "time" && data.schedule) {
      return data.schedule;
    }
    return data.label || "Configure trigger";
  };

  // Get handle config for this node type
  const handles = nodesConfig.trigger.handles;

  return (
    <WorkflowNode id={id} data={nodeData}>
      {/* Condition display */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {data.triggerType && (
          <Badge
            variant="outline"
            className="h-5 border-amber-500/30 bg-amber-500/5 text-amber-500"
          >
            {data.triggerType === "price" ? "Price" : "Time"}
          </Badge>
        )}
        <span className="font-mono truncate">{formatCondition()}</span>
      </div>

      {/* Render handles from config */}
      {handles.map((handle) => (
        <NodeHandle
          key={`${handle.type}-${handle.id || "default"}`}
          id={handle.id}
          type={handle.type}
          position={handle.position}
          x={handle.x}
          y={handle.y}
        />
      ))}
    </WorkflowNode>
  );
}

export const TriggerNode = memo(TriggerNodeComponent);
