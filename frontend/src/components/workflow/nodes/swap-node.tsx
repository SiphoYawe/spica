"use client";

import { memo } from "react";
import { ArrowRight, Percent } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { WorkflowNode } from "./workflow-node";
import { NodeHandle } from "./workflow-node/node-handle";
import { nodesConfig, type WorkflowNodeData } from "../config";

export interface SwapNodeData extends WorkflowNodeData {
  from_token?: string;
  to_token?: string;
  fromToken?: string; // Legacy support
  toToken?: string; // Legacy support
  amount?: string | number;
  amountType?: "fixed" | "percentage";
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

  // Support both naming conventions
  const fromToken = data.from_token || data.fromToken;
  const toToken = data.to_token || data.toToken;

  // Get handle config for this node type
  const handles = nodesConfig.swap.handles;

  // Format amount display
  const formatAmount = () => {
    if (!data.amount) return null;
    if (data.amountType === "percentage") {
      return `${data.amount}%`;
    }
    return `${data.amount} ${fromToken || ""}`;
  };

  const isConfigured = fromToken && toToken;

  return (
    <WorkflowNode id={id} data={nodeData}>
      <div className="space-y-1.5">
        {/* Token pair display */}
        {isConfigured ? (
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className="h-5 border-cyan-500/30 bg-cyan-500/5 text-cyan-500 font-mono"
            >
              {fromToken}
            </Badge>
            <ArrowRight className="h-3 w-3 text-muted-foreground" />
            <Badge
              variant="outline"
              className="h-5 border-cyan-500/30 bg-cyan-500/5 text-cyan-500 font-mono"
            >
              {toToken}
            </Badge>
          </div>
        ) : (
          <span className="text-xs text-muted-foreground">
            {data.label || "Select tokens to swap"}
          </span>
        )}

        {/* Amount display */}
        {data.amount && (
          <div className="flex items-center gap-2 text-sm text-foreground">
            {data.amountType === "percentage" && (
              <Percent className="h-3 w-3 text-muted-foreground" />
            )}
            <span className="font-mono">{formatAmount()}</span>
          </div>
        )}

        {/* Slippage display */}
        {data.slippage && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>Slippage: {data.slippage}%</span>
          </div>
        )}
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

export const SwapNode = memo(SwapNodeComponent);
