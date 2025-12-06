"use client";

import { memo, type ReactNode } from "react";
import { Handle, Position } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface BaseNodeProps {
  type: "trigger" | "swap" | "stake" | "transfer";
  label: string;
  icon: ReactNode;
  selected?: boolean;
  hasInput?: boolean;
  hasOutput?: boolean;
  children?: ReactNode;
  metadata?: ReactNode;
}

const nodeStyles = {
  trigger: {
    border: "border-amber-500/30",
    borderSelected: "border-amber-500",
    indicator: "bg-amber-500",
    iconBg: "bg-amber-500/10",
    iconText: "text-amber-500",
    handle: "border-amber-500",
    glow: "shadow-[0_0_20px_rgba(245,158,11,0.15)]",
  },
  swap: {
    border: "border-cyan-500/30",
    borderSelected: "border-cyan-500",
    indicator: "bg-cyan-500",
    iconBg: "bg-cyan-500/10",
    iconText: "text-cyan-500",
    handle: "border-cyan-500",
    glow: "shadow-[0_0_20px_rgba(6,182,212,0.15)]",
  },
  stake: {
    border: "border-emerald-500/30",
    borderSelected: "border-emerald-500",
    indicator: "bg-emerald-500",
    iconBg: "bg-emerald-500/10",
    iconText: "text-emerald-500",
    handle: "border-emerald-500",
    glow: "shadow-[0_0_20px_rgba(16,185,129,0.15)]",
  },
  transfer: {
    border: "border-blue-500/30",
    borderSelected: "border-blue-500",
    indicator: "bg-blue-500",
    iconBg: "bg-blue-500/10",
    iconText: "text-blue-500",
    handle: "border-blue-500",
    glow: "shadow-[0_0_20px_rgba(59,130,246,0.15)]",
  },
};

function BaseNode({
  type,
  label,
  icon,
  selected,
  hasInput = true,
  hasOutput = true,
  children,
  metadata,
}: BaseNodeProps) {
  const styles = nodeStyles[type];

  return (
    <div
      className={cn(
        "relative min-w-[220px] max-w-[280px] rounded-lg border bg-card transition-all duration-150",
        selected ? styles.borderSelected : styles.border,
        selected && styles.glow
      )}
    >
      {/* Type indicator bar */}
      <div className={cn("absolute left-0 right-0 top-0 h-0.5 rounded-t-lg", styles.indicator)} />

      {/* Input handle */}
      {hasInput && (
        <Handle
          type="target"
          position={Position.Top}
          className={cn(
            "!h-3 !w-3 !rounded-full !border-2 !bg-card transition-all",
            styles.handle
          )}
        />
      )}

      {/* Header */}
      <div className="flex items-center gap-2.5 border-b border-border/50 px-3 py-2.5">
        <div
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-md",
            styles.iconBg
          )}
        >
          <span className={styles.iconText}>{icon}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            {type}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-3 space-y-2">
        <div className="text-sm font-medium text-foreground truncate">
          {label}
        </div>

        {children}

        {metadata && (
          <div className="pt-1 text-xs text-muted-foreground font-mono">
            {metadata}
          </div>
        )}
      </div>

      {/* Output handle */}
      {hasOutput && (
        <Handle
          type="source"
          position={Position.Bottom}
          className={cn(
            "!h-3 !w-3 !rounded-full !border-2 !bg-card transition-all",
            styles.handle
          )}
        />
      )}
    </div>
  );
}

export default memo(BaseNode);
