"use client";

import { forwardRef, type ReactNode } from "react";
import { Position, type HandleProps } from "@xyflow/react";
import { cn } from "@/lib/utils";
import { BaseHandle } from "./base-handle";

export interface ButtonHandleProps extends Omit<HandleProps, "position"> {
  position: Position;
  showButton?: boolean;
  children?: ReactNode;
  className?: string;
}

/**
 * ButtonHandle - Handle with optional visible connection button
 * Shows a connector line and button for adding nodes
 */
export const ButtonHandle = forwardRef<HTMLDivElement, ButtonHandleProps>(
  ({ position, showButton = false, children, className, ...props }, ref) => {
    // Position-based wrapper classes
    const wrapperClasses = {
      [Position.Top]: "flex-col-reverse -translate-y-full items-center",
      [Position.Bottom]: "flex-col translate-y-[10px] items-center",
      [Position.Left]: "flex-row-reverse -translate-x-full items-center",
      [Position.Right]: "flex-row translate-x-[10px] items-center",
    };

    // Connector line classes based on position
    const lineClasses = {
      [Position.Top]: "h-[10px] w-px bg-border",
      [Position.Bottom]: "h-[10px] w-px bg-border",
      [Position.Left]: "w-[10px] h-px bg-border",
      [Position.Right]: "w-[10px] h-px bg-border",
    };

    return (
      <BaseHandle ref={ref} position={position} className={className} {...props}>
        {showButton && (
          <div
            className={cn(
              "pointer-events-none absolute flex",
              wrapperClasses[position]
            )}
          >
            {/* Connector line */}
            <div className={lineClasses[position]} />

            {/* Button wrapper - allows pointer events */}
            <div className="pointer-events-auto nodrag nopan">
              {children}
            </div>
          </div>
        )}
      </BaseHandle>
    );
  }
);
ButtonHandle.displayName = "ButtonHandle";
