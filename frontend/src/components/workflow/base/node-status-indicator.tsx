"use client";

import { type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { LoaderCircle } from "lucide-react";

export type NodeStatus = "initial" | "loading" | "success" | "error";

interface NodeStatusIndicatorProps {
  status?: NodeStatus;
  variant?: "border" | "overlay";
  children: ReactNode;
  className?: string;
}

/**
 * SpinnerLoadingIndicator - Overlay with animated spinner
 */
function SpinnerLoadingIndicator() {
  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center rounded-lg bg-background/50 backdrop-blur-[2px]">
      {/* Ping effect */}
      <div className="absolute h-8 w-8 animate-ping rounded-full bg-spica/20" />
      {/* Spinner */}
      <LoaderCircle className="h-6 w-6 animate-spin text-spica" />
    </div>
  );
}

/**
 * BorderLoadingIndicator - Animated conic gradient border
 */
function BorderLoadingIndicator() {
  return (
    <div
      className="pointer-events-none absolute -inset-[3px] overflow-hidden rounded-xl"
      style={{
        // Overflow clip for the rotating gradient
        clipPath: "inset(0 round 12px)",
      }}
    >
      <div
        className="absolute left-1/2 top-1/2 h-[140%] w-[140%]"
        style={{
          background:
            "conic-gradient(from 0deg at 50% 50%, rgb(0,255,72) 0deg, rgba(0,255,72,0) 360deg)",
          animation: "spin 2s linear infinite",
          transform: "translate(-50%, -50%)",
        }}
      />
      {/* Inner mask to show only the border */}
      <div className="absolute inset-[2px] rounded-[10px] bg-card" />
    </div>
  );
}

/**
 * NodeStatusIndicator - Wraps nodes with status feedback
 *
 * - initial: No indicator
 * - loading: Spinner overlay or animated border
 * - success: Green border
 * - error: Red border
 */
export function NodeStatusIndicator({
  status = "initial",
  variant = "overlay",
  children,
  className,
}: NodeStatusIndicatorProps) {
  // Status-based border classes
  const statusBorderClasses = {
    initial: "",
    loading: "",
    success: "ring-2 ring-emerald-500/60 rounded-lg",
    error: "ring-2 ring-red-400/60 rounded-lg",
  };

  return (
    <div className={cn("relative", statusBorderClasses[status], className)}>
      {/* Loading indicator based on variant */}
      {status === "loading" && variant === "overlay" && <SpinnerLoadingIndicator />}
      {status === "loading" && variant === "border" && <BorderLoadingIndicator />}

      {children}

      {/* Keyframes for border spinner */}
      <style jsx>{`
        @keyframes spin {
          from {
            transform: translate(-50%, -50%) rotate(0deg);
          }
          to {
            transform: translate(-50%, -50%) rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}
