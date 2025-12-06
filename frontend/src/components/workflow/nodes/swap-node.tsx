"use client";

import { memo } from "react";
import { ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { WorkflowNode } from "./workflow-node";
import { NodeHandle } from "./workflow-node/node-handle";
import { nodesConfig, type WorkflowNodeData } from "../config";

export interface SwapNodeData extends WorkflowNodeData {
  fromToken?: string;
  toToken?: string;
  amount?: string | number;
  minOutput?: string | number;
  slippage?: number;
}

interface SwapNodeProps {
  id: string;
  data: SwapNodeData;
}

/**
 * SwapNode - Token exchange action
 *
 * Swaps one token for another on a DEX
 */
function SwapNodeComponent({ id, data }: SwapNodeProps) {
  const nodeData: WorkflowNodeData = {
    ...data,
    icon: "swap",
    title: data.title || "Swap",
  };

  // Get handle config for this node type
  const handles = nodesConfig.swap.handles;

  return (
    <WorkflowNode id={id} data={nodeData}>
      {/* Token pair display */}
      {data.fromToken && data.toToken ? (
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className="h-5 border-cyan-500/30 bg-cyan-500/5 text-cyan-500 font-mono"
          >
            {data.fromToken}
          </Badge>
          <ArrowRight className="h-3 w-3 text-muted-foreground" />
          <Badge
            variant="outline"
            className="h-5 border-cyan-500/30 bg-cyan-500/5 text-cyan-500 font-mono"
          >
            {data.toToken}
          </Badge>
        </div>
      ) : (
        <span className="text-xs text-muted-foreground">
          {data.label || "Configure swap"}
        </span>
      )}

      {/* Amount and min output */}
      {(data.amount || data.minOutput) && (
        <div className="flex items-center gap-3 text-xs text-muted-foreground font-mono">
          {data.amount && <span>Amount: {data.amount}</span>}
          {data.minOutput && <span>Min: {data.minOutput}</span>}
        </div>
      )}

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

export const SwapNode = memo(SwapNodeComponent);
