"use client";

import { memo } from "react";
import { type NodeProps, type Node } from "@xyflow/react";
import { Send } from "lucide-react";
import BaseNode from "./BaseNode";

interface TransferNodeData extends Record<string, unknown> {
  label: string;
  token?: string;
  amount?: number;
  to_address?: string;
  recipient?: string;
}

type TransferNodeType = Node<TransferNodeData, "transfer">;

function TransferNode({ data, selected }: NodeProps<TransferNodeType>) {
  // Format display text
  let displayText = data.label;
  if (data.token && data.amount !== undefined) {
    displayText = `Send ${data.amount} ${data.token}`;
  }

  // Truncate address for display
  const formatAddress = (address: string) => {
    if (address.length > 12) {
      return `${address.slice(0, 6)}...${address.slice(-4)}`;
    }
    return address;
  };

  const recipient = data.to_address || data.recipient;

  return (
    <BaseNode
      type="transfer"
      label={displayText}
      icon={<Send className="h-4 w-4" />}
      selected={selected}
      hasInput={true}
      hasOutput={true}
    >
      {data.token && data.amount !== undefined && (
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center rounded-md border border-blue-500/20 bg-blue-500/5 px-2 py-0.5 text-[10px] font-medium text-blue-500 font-mono">
            {data.amount} {data.token}
          </span>
        </div>
      )}

      {recipient && (
        <div className="text-[10px] text-muted-foreground">
          To: <span className="font-mono">{formatAddress(recipient)}</span>
        </div>
      )}
    </BaseNode>
  );
}

export default memo(TransferNode);
