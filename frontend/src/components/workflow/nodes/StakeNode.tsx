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
  return (
    <BaseNode
      type="stake"
      label={data.label}
      icon={<Lock className="h-4 w-4" />}
      selected={selected}
      hasInput={true}
      hasOutput={true}
    >
      <div className="flex flex-col gap-1.5">
        {/* Token badge */}
        {data.token && (
          <div className="flex items-center gap-1.5">
            <span className="inline-flex items-center rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-400 font-mono">
              {data.token}
            </span>
            {data.pool && (
              <span className="text-xs text-muted-foreground">
                → {data.pool}
              </span>
            )}
          </div>
        )}

        {/* Amount display */}
        {data.amount !== undefined && (
          <div className="text-sm font-semibold text-foreground font-mono">
            {data.amount} {data.token}
          </div>
        )}

        {/* Duration */}
        {data.duration && (
          <div className="text-xs text-muted-foreground">
            Duration: <span className="font-mono">{data.duration}</span>
          </div>
        )}
      </div>
    </BaseNode>
  );
}

export default memo(StakeNode);
