"use client";

import { memo } from "react";
import { Badge } from "@/components/ui/badge";
import { WorkflowNode } from "./workflow-node";
import { NodeHandle } from "./workflow-node/node-handle";
import { nodesConfig, type WorkflowNodeData } from "../config";

export interface TransferNodeData extends WorkflowNodeData {
  token?: string;
  amount?: string | number;
  recipient?: string;
  memo?: string;
}

// Truncate address for display
function truncateAddress(address: string): string {
  if (address.length <= 12) return address;
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

interface TransferNodeProps {
  id: string;
  data: TransferNodeData;
}

/**
 * TransferNode - Token transfer action
 *
 * Sends tokens to a recipient address
 */
function TransferNodeComponent({ id, data }: TransferNodeProps) {
  const nodeData: WorkflowNodeData = {
    ...data,
    icon: "transfer",
    title: data.title || "Transfer",
  };

  // Get handle config for this node type
  const handles = nodesConfig.transfer.handles;

  return (
    <WorkflowNode id={id} data={nodeData}>
      {/* Token and amount */}
      <div className="flex items-center gap-2">
        {data.amount && data.token && (
          <Badge
            variant="outline"
            className="h-5 border-blue-500/30 bg-blue-500/5 text-blue-500 font-mono"
          >
            {data.amount} {data.token}
          </Badge>
        )}
      </div>

      {/* Recipient */}
      {data.recipient && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>To:</span>
          <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px]">
            {truncateAddress(data.recipient)}
          </code>
        </div>
      )}

      {!data.token && !data.label && (
        <span className="text-xs text-muted-foreground">Configure transfer</span>
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

export const TransferNode = memo(TransferNodeComponent);
