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

  // Format display text
  let displayText = data.label;
  if (data.token && data.operator && data.value !== undefined) {
    displayText = `${data.token} ${data.operator} $${data.value.toFixed(2)}`;
  } else if (data.interval || data.time) {
    displayText = data.interval ? `Every ${data.interval}` : data.time || data.label;
  }

  const Icon = isPriceCondition ? DollarSign : Clock;

  return (
    <BaseNode
      type="trigger"
      label={displayText}
      icon={<Icon className="h-4 w-4" />}
      selected={selected}
      hasInput={false}
      hasOutput={true}
    >
      {data.type && (
        <div className="flex items-center gap-1.5">
          <span className="inline-flex items-center rounded-md border border-amber-500/20 bg-amber-500/5 px-2 py-0.5 text-[10px] font-medium text-amber-500">
            {data.type === "price" ? "Price Condition" : data.type === "time" ? "Scheduled" : data.type}
          </span>
        </div>
      )}
    </BaseNode>
  );
}

export default memo(TriggerNode);
