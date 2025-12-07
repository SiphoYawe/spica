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
    border: "border-amber-500/50",
    borderSelected: "border-amber-500",
    indicator: "bg-amber-500",
    iconBg: "bg-amber-500/20",
    iconText: "text-amber-400",
    handle: "border-amber-400",
    glow: "shadow-[0_0_24px_rgba(245,158,11,0.25)]",
    typeLabel: "text-amber-400/90",
  },
  swap: {
    border: "border-cyan-500/50",
    borderSelected: "border-cyan-500",
    indicator: "bg-cyan-500",
    iconBg: "bg-cyan-500/20",
    iconText: "text-cyan-400",
    handle: "border-cyan-400",
    glow: "shadow-[0_0_24px_rgba(6,182,212,0.25)]",
    typeLabel: "text-cyan-400/90",
  },
  stake: {
    border: "border-emerald-500/50",
    borderSelected: "border-emerald-500",
    indicator: "bg-emerald-500",
    iconBg: "bg-emerald-500/20",
    iconText: "text-emerald-400",
    handle: "border-emerald-400",
    glow: "shadow-[0_0_24px_rgba(16,185,129,0.25)]",
    typeLabel: "text-emerald-400/90",
  },
  transfer: {
    border: "border-blue-500/50",
    borderSelected: "border-blue-500",
    indicator: "bg-blue-500",
    iconBg: "bg-blue-500/20",
    iconText: "text-blue-400",
    handle: "border-blue-400",
    glow: "shadow-[0_0_24px_rgba(59,130,246,0.25)]",
    typeLabel: "text-blue-400/90",
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
        "relative min-w-[220px] max-w-[280px] rounded-lg border-2 bg-card/95 backdrop-blur-sm transition-all duration-150",
        selected ? styles.borderSelected : styles.border,
        selected && styles.glow,
        "hover:border-opacity-80"
      )}
    >
      {/* Type indicator bar - thicker for visibility */}
      <div className={cn("absolute left-0 right-0 top-0 h-1 rounded-t-lg", styles.indicator)} />

      {/* Input handle */}
      {hasInput && (
        <Handle
          type="target"
          position={Position.Top}
          className={cn(
            "!h-3.5 !w-3.5 !rounded-full !border-2 !bg-card transition-all hover:!scale-125",
            styles.handle
          )}
        />
      )}

      {/* Header */}
      <div className="flex items-center gap-2.5 border-b border-border/60 px-3 py-2.5 mt-0.5">
        <div
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-md",
            styles.iconBg
          )}
        >
          <span className={styles.iconText}>{icon}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className={cn("text-[11px] font-semibold uppercase tracking-wider", styles.typeLabel)}>
            {type}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-3 py-2">
        <div className="text-sm font-semibold text-foreground truncate">
          {label}
        </div>

        {children && (
          <div className="mt-1.5 space-y-1.5">
            {children}
          </div>
        )}

        {metadata && (
          <div className="mt-1.5 text-xs text-muted-foreground/80 font-mono">
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
            "!h-3.5 !w-3.5 !rounded-full !border-2 !bg-card transition-all hover:!scale-125",
            styles.handle
          )}
        />
      )}
    </div>
  );
}

export default memo(BaseNode);
