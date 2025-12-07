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
      <div className="flex flex-col gap-1.5">
        {data.token && (
          <div className="flex items-center gap-1.5">
            <span className="inline-flex items-center rounded-md border border-blue-500/30 bg-blue-500/10 px-2 py-0.5 text-xs font-medium text-blue-400 font-mono">
              {data.token}
            </span>
            {recipient && (
              <>
                <Send className="h-3 w-3 text-muted-foreground/60" />
                <span className="text-xs text-muted-foreground font-mono bg-muted/30 px-1.5 py-0.5 rounded">
                  {formatAddress(recipient)}
                </span>
              </>
            )}
          </div>
        )}

        {data.amount !== undefined && (
          <div className="text-sm font-semibold text-foreground font-mono">
            {data.amount} {data.token}
          </div>
        )}
      </div>
    </BaseNode>
  );
}

export default memo(TransferNode);
