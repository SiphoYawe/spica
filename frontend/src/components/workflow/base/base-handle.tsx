"use client";

import { forwardRef, type ReactNode } from "react";
import { Handle, type HandleProps } from "@xyflow/react";
import { cn } from "@/lib/utils";

export interface BaseHandleProps extends HandleProps {
  children?: ReactNode;
  className?: string;
}

/**
 * BaseHandle - Styled handle for node connections
 * Matches Pro template sizing with Spica color accents
 */
export const BaseHandle = forwardRef<HTMLDivElement, BaseHandleProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <Handle
        ref={ref}
        className={cn(
          // Size: 11px circles like Pro template
          "!h-[11px] !w-[11px] !rounded-full",
          // Border and background
          "!border-2 !border-border !bg-card",
          // Dark mode adjustments
          "dark:!border-secondary dark:!bg-secondary",
          // Hover state with Spica green
          "hover:!border-spica hover:!shadow-[0_0_8px_rgba(0,255,72,0.4)]",
          // Connecting state
          "[&.connecting]:!border-spica [&.connecting]:!bg-spica",
          "[&.valid]:!border-spica [&.valid]:!bg-spica",
          // Transition
          "!transition-all !duration-150",
          className
        )}
        {...props}
      >
        {children}
      </Handle>
    );
  }
);
BaseHandle.displayName = "BaseHandle";
