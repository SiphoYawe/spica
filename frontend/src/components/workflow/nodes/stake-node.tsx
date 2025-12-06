"use client";

import { memo } from "react";
import { Badge } from "@/components/ui/badge";
import { WorkflowNode } from "./workflow-node";
import { NodeHandle } from "./workflow-node/node-handle";
import { nodesConfig, type WorkflowNodeData } from "../config";

export interface StakeNodeData extends WorkflowNodeData {
  token?: string;
  amount?: string | number;
  pool?: string;
  duration?: string;
  apy?: string | number;
}

interface StakeNodeProps {
  id: string;
  data: StakeNodeData;
}

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

  return (
    <WorkflowNode id={id} data={nodeData}>
      {/* Token and pool display */}
      <div className="flex flex-wrap items-center gap-2">
        {data.token && (
          <Badge
            variant="outline"
            className="h-5 border-emerald-500/30 bg-emerald-500/5 text-emerald-500 font-mono"
          >
            {data.token}
          </Badge>
        )}
        {data.pool && (
          <span className="text-xs text-muted-foreground truncate">
            → {data.pool}
          </span>
        )}
      </div>

      {/* Amount and details */}
      {(data.amount || data.duration || data.apy) && (
        <div className="flex items-center gap-3 text-xs text-muted-foreground font-mono">
          {data.amount && <span>{data.amount}</span>}
          {data.duration && <span>{data.duration}</span>}
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

      {!data.token && !data.label && (
        <span className="text-xs text-muted-foreground">Configure stake</span>
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

export const StakeNode = memo(StakeNodeComponent);
