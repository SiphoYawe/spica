"use client";

import { memo } from "react";
import { Clock, Percent, Vault } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { WorkflowNode } from "./workflow-node";
import { NodeHandle } from "./workflow-node/node-handle";
import { nodesConfig, type WorkflowNodeData } from "../config";

export interface StakeNodeData extends WorkflowNodeData {
  token?: string;
  amount?: string | number;
  amountType?: "fixed" | "percentage";
  pool?: string;
  duration?: string;
  apy?: string | number;
}

interface StakeNodeProps {
  id: string;
  data: StakeNodeData;
}

// Pool display names
const POOL_NAMES: Record<string, string> = {
  flamingo: "Flamingo Finance",
  neoburger: "NeoBurger",
  grandneo: "GrandNeo",
};

// Duration display names
const DURATION_NAMES: Record<string, string> = {
  flexible: "Flexible",
  "7d": "7 Days",
  "30d": "30 Days",
  "90d": "90 Days",
  "180d": "180 Days",
  "365d": "1 Year",
};

/**
 * StakeNode - Token staking action
 *
 * Stakes tokens in a pool for yield
 */
function StakeNodeComponent({ id, data }: StakeNodeProps) {
  const nodeData: WorkflowNodeData = {
    ...data,
    icon: "stake",
    title: data.title || "Stake",
  };

  // Get handle config for this node type
  const handles = nodesConfig.stake.handles;

  // Format amount display
  const formatAmount = () => {
    if (!data.amount) return null;
    if (data.amountType === "percentage") {
      return `${data.amount}%`;
    }
    return `${data.amount} ${data.token || ""}`;
  };

  const isConfigured = data.token && data.pool;

  return (
    <WorkflowNode id={id} data={nodeData}>
      <div className="space-y-1.5">
        {/* Token and pool display */}
        {isConfigured ? (
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className="h-5 border-emerald-500/30 bg-emerald-500/5 text-emerald-500 font-mono"
            >
              {data.token}
            </Badge>
            <span className="text-xs text-muted-foreground">→</span>
            <div className="flex items-center gap-1 text-xs text-foreground">
              <Vault className="h-3 w-3 text-emerald-500" />
              <span>{(data.pool && POOL_NAMES[data.pool]) || data.pool}</span>
            </div>
          </div>
        ) : (
          <span className="text-xs text-muted-foreground">
            {data.label || "Select token and pool"}
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

        {/* Duration and APY row */}
        {(data.duration || data.apy) && (
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            {data.duration && (
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                <span>{DURATION_NAMES[data.duration] || data.duration}</span>
              </div>
            )}
            {data.apy && (
              <Badge
                variant="outline"
                className="h-4 border-emerald-500/20 bg-emerald-500/5 text-emerald-400 text-[10px]"
              >
                {data.apy}% APY
              </Badge>
            )}
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

export const StakeNode = memo(StakeNodeComponent);
