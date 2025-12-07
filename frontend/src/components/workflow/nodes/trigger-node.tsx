"use client";

import { memo } from "react";
import { Clock, DollarSign, Calendar, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { WorkflowNode } from "./workflow-node";
import { NodeHandle } from "./workflow-node/node-handle";
import { nodesConfig, type WorkflowNodeData } from "../config";

export interface TriggerNodeData extends WorkflowNodeData {
  type?: "price" | "time" | "event";
  triggerType?: "price" | "time" | "event"; // Legacy support
  token?: string;
  operator?: ">" | "<" | ">=" | "<=" | "==";
  value?: string | number;
  // Time trigger fields
  interval?: string;
  time?: string;
  dayOfWeek?: string;
  dayOfMonth?: number;
  schedule?: string;
  // Event trigger fields
  contractAddress?: string;
  eventName?: string;
}

interface TriggerNodeProps {
  id: string;
  data: TriggerNodeData;
}

// Format time for display
function formatTime(time: string): string {
  if (!time) return "";
  const [hours, minutes] = time.split(":");
  const hour = parseInt(hours);
  const ampm = hour >= 12 ? "PM" : "AM";
  const displayHour = hour % 12 || 12;
  return `${displayHour}:${minutes} ${ampm}`;
}

// Capitalize first letter
function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * TriggerNode - Workflow entry point
 *
 * Triggered by:
 * - Price conditions (e.g., "When NEO > $15")
 * - Time schedules (e.g., "Every day at 9:00 AM")
 * - On-chain events
 */
function TriggerNodeComponent({ id, data }: TriggerNodeProps) {
  const nodeData: WorkflowNodeData = {
    ...data,
    icon: "trigger",
    title: data.title || "Trigger",
  };

  // Determine trigger type (support both 'type' and legacy 'triggerType')
  const triggerType = data.type || data.triggerType || "price";

  // Format the trigger condition for display
  const formatPriceCondition = () => {
    if (data.token && data.operator && data.value) {
      return `${data.token} ${data.operator} $${data.value}`;
    }
    return null;
  };

  // Format time schedule for display
  const formatTimeSchedule = () => {
    const parts: string[] = [];

    if (data.interval) {
      if (data.interval === "weekly" && data.dayOfWeek) {
        parts.push(`Every ${capitalize(data.dayOfWeek)}`);
      } else if (data.interval === "monthly" && data.dayOfMonth) {
        const suffix = data.dayOfMonth === 1 ? "st" : data.dayOfMonth === 2 ? "nd" : data.dayOfMonth === 3 ? "rd" : "th";
        parts.push(`${data.dayOfMonth}${suffix} of month`);
      } else {
        parts.push(capitalize(data.interval));
      }
    }

    if (data.time) {
      parts.push(`at ${formatTime(data.time)}`);
    }

    if (parts.length > 0) return parts.join(" ");
    if (data.schedule) return data.schedule;
    return null;
  };

  // Get handle config for this node type
  const handles = nodesConfig.trigger.handles;

  // Get badge icon based on trigger type
  const getBadgeIcon = () => {
    switch (triggerType) {
      case "price": return <DollarSign className="h-3 w-3" />;
      case "time": return <Clock className="h-3 w-3" />;
      case "event": return <Zap className="h-3 w-3" />;
      default: return null;
    }
  };

  // Check if trigger is configured
  const isConfigured = triggerType === "price"
    ? !!(data.token && data.operator && data.value)
    : triggerType === "time"
    ? !!(data.interval || data.schedule)
    : !!(data.contractAddress && data.eventName);

  return (
    <WorkflowNode id={id} data={nodeData}>
      <div className="space-y-1.5">
        {/* Trigger type badge */}
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className="h-5 gap-1 border-amber-500/30 bg-amber-500/5 text-amber-500"
          >
            {getBadgeIcon()}
            {triggerType === "price" ? "Price" : triggerType === "time" ? "Schedule" : "Event"}
          </Badge>
        </div>

        {/* Price trigger display */}
        {triggerType === "price" && (
          <div className="space-y-1">
            {formatPriceCondition() ? (
              <div className="font-mono text-sm text-foreground">
                {formatPriceCondition()}
              </div>
            ) : (
              <span className="text-xs text-muted-foreground">Set price condition</span>
            )}
          </div>
        )}

        {/* Time trigger display */}
        {triggerType === "time" && (
          <div className="space-y-1">
            {formatTimeSchedule() ? (
              <div className="flex items-center gap-1.5 text-sm text-foreground">
                <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                <span>{formatTimeSchedule()}</span>
              </div>
            ) : (
              <span className="text-xs text-muted-foreground">Set schedule</span>
            )}
          </div>
        )}

        {/* Event trigger display */}
        {triggerType === "event" && (
          <div className="space-y-1">
            {data.eventName ? (
              <>
                <div className="text-sm text-foreground">{data.eventName}</div>
                {data.contractAddress && (
                  <code className="text-[10px] text-muted-foreground font-mono truncate block">
                    {data.contractAddress.slice(0, 10)}...{data.contractAddress.slice(-6)}
                  </code>
                )}
              </>
            ) : (
              <span className="text-xs text-muted-foreground">Set event trigger</span>
            )}
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

export const TriggerNode = memo(TriggerNodeComponent);
