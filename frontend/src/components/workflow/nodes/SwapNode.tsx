"use client";

import { memo } from "react";
import { type NodeProps, type Node } from "@xyflow/react";
import { ArrowLeftRight } from "lucide-react";
import BaseNode from "./BaseNode";

interface SwapNodeData extends Record<string, unknown> {
  label: string;
  from_token?: string;
  to_token?: string;
  amount?: number;
  min_output?: number;
}

type SwapNodeType = Node<SwapNodeData, "swap">;

function SwapNode({ data, selected }: NodeProps<SwapNodeType>) {
  // Format display text
  let displayText = data.label;
  if (data.from_token && data.to_token && data.amount !== undefined) {
    displayText = `${data.amount} ${data.from_token} → ${data.to_token}`;
  }

  return (
    <BaseNode
      type="swap"
      label={displayText}
      icon={<ArrowLeftRight className="h-4 w-4" />}
      selected={selected}
      hasInput={true}
      hasOutput={true}
    >
      {data.from_token && data.to_token && (
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center rounded-md border border-cyan-500/20 bg-cyan-500/5 px-2 py-0.5 text-[10px] font-medium text-cyan-500 font-mono">
            {data.from_token}
          </span>
          <ArrowLeftRight className="h-3 w-3 text-muted-foreground" />
          <span className="inline-flex items-center rounded-md border border-cyan-500/20 bg-cyan-500/5 px-2 py-0.5 text-[10px] font-medium text-cyan-500 font-mono">
            {data.to_token}
          </span>
        </div>
      )}

      {data.min_output !== undefined && (
        <div className="text-[10px] text-muted-foreground">
          Min: {data.min_output} {data.to_token}
        </div>
      )}
    </BaseNode>
  );
}

export default memo(SwapNode);
