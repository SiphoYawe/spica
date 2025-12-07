"use client";

import { memo } from "react";
import { Send, Percent } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { WorkflowNode } from "./workflow-node";
import { NodeHandle } from "./workflow-node/node-handle";
import { nodesConfig, type WorkflowNodeData } from "../config";

export interface TransferNodeData extends WorkflowNodeData {
  token?: string;
  amount?: string | number;
  amountType?: "fixed" | "percentage";
  to_address?: string;
  recipient?: string; // Legacy support
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

  // Support both naming conventions
  const recipientAddress = data.to_address || data.recipient;

  // Get handle config for this node type
  const handles = nodesConfig.transfer.handles;

  // Format amount display
  const formatAmount = () => {
    if (!data.amount) return null;
    if (data.amountType === "percentage") {
      return `${data.amount}%`;
    }
    return `${data.amount} ${data.token || ""}`;
  };

  const isConfigured = data.token && recipientAddress;

  return (
    <WorkflowNode id={id} data={nodeData}>
      <div className="space-y-1.5">
        {/* Token badge */}
        {data.token ? (
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className="h-5 border-blue-500/30 bg-blue-500/5 text-blue-500 font-mono"
            >
              {data.token}
            </Badge>
            {recipientAddress && (
              <>
                <Send className="h-3 w-3 text-muted-foreground" />
                <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-foreground">
                  {truncateAddress(recipientAddress)}
                </code>
              </>
            )}
          </div>
        ) : (
          <span className="text-xs text-muted-foreground">
            {data.label || "Select token and recipient"}
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

export const TransferNode = memo(TransferNodeComponent);
