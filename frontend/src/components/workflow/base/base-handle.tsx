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
          // Size: 12px circles for better visibility
          "!h-3 !w-3 !rounded-full",
          // High contrast colors - light/bright for visibility on dark backgrounds
          "!border-2 !border-zinc-400 !bg-zinc-200",
          // Dark mode - use bright colors for contrast
          "dark:!border-zinc-300 dark:!bg-zinc-100",
          // Hover state with Spica green
          "hover:!border-spica hover:!bg-spica/20 hover:!shadow-[0_0_8px_rgba(0,255,72,0.5)]",
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
