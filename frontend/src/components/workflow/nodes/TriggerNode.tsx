"use client";

import { memo } from "react";
import { type NodeProps, type Node } from "@xyflow/react";
import { Clock, DollarSign } from "lucide-react";
import BaseNode from "./BaseNode";

interface TriggerNodeData extends Record<string, unknown> {
  label: string;
  type?: string;
  token?: string;
  operator?: string;
  value?: number;
  interval?: string;
  time?: string;
}

type TriggerNodeType = Node<TriggerNodeData, "trigger">;

function TriggerNode({ data, selected }: NodeProps<TriggerNodeType>) {
  const isPriceCondition = data.type === "price" || data.token;
  const Icon = isPriceCondition ? DollarSign : Clock;

  return (
    <BaseNode
      type="trigger"
      label={data.label}
      icon={<Icon className="h-4 w-4" />}
      selected={selected}
      hasInput={false}
      hasOutput={true}
    >
      <div className="flex flex-col gap-1.5">
        {/* Trigger type badge */}
        {data.type && (
          <div className="flex items-center">
            <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-400">
              <DollarSign className="h-3 w-3" />
              {data.type === "price" ? "Price" : data.type === "time" ? "Schedule" : data.type}
            </span>
          </div>
        )}

        {/* Price condition display */}
        {data.token && data.operator && data.value !== undefined && (
          <div className="text-sm font-semibold text-foreground font-mono">
            {data.token} {data.operator} ${data.value}
          </div>
        )}

        {/* Time trigger display */}
        {(data.interval || data.time) && (
          <div className="text-sm font-semibold text-foreground">
            {data.interval ? `Every ${data.interval}` : data.time}
          </div>
        )}
      </div>
    </BaseNode>
  );
}

export default memo(TriggerNode);
