"use client";

import { memo } from "react";
import { type NodeProps, type Node } from "@xyflow/react";
import { Lock } from "lucide-react";
import BaseNode from "./BaseNode";

interface StakeNodeData extends Record<string, unknown> {
  label: string;
  token?: string;
  amount?: number;
  pool?: string;
  duration?: string;
}

type StakeNodeType = Node<StakeNodeData, "stake">;

function StakeNode({ data, selected }: NodeProps<StakeNodeType>) {
  // Format display text
  let displayText = data.label;
  if (data.token && data.amount !== undefined) {
    displayText = `Stake ${data.amount} ${data.token}`;
    if (data.pool) {
      displayText += ` in ${data.pool}`;
    }
  }

  return (
    <BaseNode
      type="stake"
      label={displayText}
      icon={<Lock className="h-4 w-4" />}
      selected={selected}
      hasInput={true}
      hasOutput={true}
    >
      {data.token && data.amount !== undefined && (
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center rounded-md border border-emerald-500/20 bg-emerald-500/5 px-2 py-0.5 text-[10px] font-medium text-emerald-500 font-mono">
            {data.amount} {data.token}
          </span>
        </div>
      )}

      {(data.pool || data.duration) && (
        <div className="flex flex-col gap-0.5 text-[10px] text-muted-foreground">
          {data.pool && <span>Pool: {data.pool}</span>}
          {data.duration && <span>Duration: {data.duration}</span>}
        </div>
      )}
    </BaseNode>
  );
}

export default memo(StakeNode);
