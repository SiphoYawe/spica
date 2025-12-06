"use client";

import { forwardRef, type ComponentProps } from "react";
import { cn } from "@/lib/utils";

/**
 * BaseNode - Foundation wrapper for all workflow nodes
 * Styled to match Pro template with Spica's scientific aesthetic
 */
export const BaseNode = forwardRef<HTMLDivElement, ComponentProps<"div">>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "bg-card text-card-foreground relative rounded-lg border transition-all duration-150",
          // Selection styling via React Flow parent class
          "[.react-flow__node.selected_&]:border-spica/60",
          "[.react-flow__node.selected_&]:shadow-[0_0_24px_rgba(0,255,72,0.2)]",
          // Hover state
          "hover:ring-1 hover:ring-spica/20",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
BaseNode.displayName = "BaseNode";

/**
 * BaseNodeHeader - Top section with icon and title
 */
export const BaseNodeHeader = forwardRef<HTMLDivElement, ComponentProps<"div">>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "flex items-center justify-between gap-2 px-3 py-2 border-b border-border/50",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
BaseNodeHeader.displayName = "BaseNodeHeader";

/**
 * BaseNodeHeaderTitle - Non-selectable title text
 */
export const BaseNodeHeaderTitle = forwardRef<
  HTMLSpanElement,
  ComponentProps<"span">
>(({ className, children, ...props }, ref) => {
  return (
    <span
      ref={ref}
      className={cn(
        "text-[10px] font-semibold uppercase tracking-widest text-muted-foreground select-none",
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
});
BaseNodeHeaderTitle.displayName = "BaseNodeHeaderTitle";

/**
 * BaseNodeContent - Main content area
 */
export const BaseNodeContent = forwardRef<HTMLDivElement, ComponentProps<"div">>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("flex flex-col gap-y-2 p-3", className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);
BaseNodeContent.displayName = "BaseNodeContent";

/**
 * BaseNodeFooter - Bottom section
 */
export const BaseNodeFooter = forwardRef<HTMLDivElement, ComponentProps<"div">>(
  ({ className, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn("border-t border-border/50 px-3 py-2", className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);
BaseNodeFooter.displayName = "BaseNodeFooter";
