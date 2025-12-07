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
  return (
    <BaseNode
      type="swap"
      label={data.label}
      icon={<ArrowLeftRight className="h-4 w-4" />}
      selected={selected}
      hasInput={true}
      hasOutput={true}
    >
      <div className="flex flex-col gap-1.5">
        {/* Token pair badges */}
        {data.from_token && data.to_token && (
          <div className="flex items-center gap-1.5">
            <span className="inline-flex items-center rounded-md border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 text-xs font-medium text-cyan-400 font-mono">
              {data.from_token}
            </span>
            <ArrowLeftRight className="h-3 w-3 text-muted-foreground/60" />
            <span className="inline-flex items-center rounded-md border border-cyan-500/30 bg-cyan-500/10 px-2 py-0.5 text-xs font-medium text-cyan-400 font-mono">
              {data.to_token}
            </span>
          </div>
        )}

        {/* Amount display */}
        {data.amount !== undefined && (
          <div className="text-sm font-semibold text-foreground font-mono">
            {data.amount} {data.from_token}
          </div>
        )}

        {/* Min output */}
        {data.min_output !== undefined && (
          <div className="text-xs text-muted-foreground">
            Min output: <span className="font-mono">{data.min_output} {data.to_token}</span>
          </div>
        )}
      </div>
    </BaseNode>
  );
}

export default memo(SwapNode);
