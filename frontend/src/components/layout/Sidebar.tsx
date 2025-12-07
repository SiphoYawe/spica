"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/stores";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Zap,
  ArrowLeftRight,
  Lock,
  Send,
  Workflow,
  GripVertical,
} from "lucide-react";
import Image from "next/image";

// Node type definitions for the palette
const nodeTypes = [
  {
    type: "trigger",
    label: "Trigger",
    description: "Start your workflow with a condition",
    icon: Zap,
    color: "text-amber-500",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/50",
    hoverBorder: "hover:border-amber-500",
    dragBorder: "border-amber-500",
  },
  {
    type: "swap",
    label: "Swap",
    description: "Exchange one token for another",
    icon: ArrowLeftRight,
    color: "text-cyan-500",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/50",
    hoverBorder: "hover:border-cyan-500",
    dragBorder: "border-cyan-500",
  },
  {
    type: "stake",
    label: "Stake",
    description: "Lock tokens to earn rewards",
    icon: Lock,
    color: "text-emerald-500",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/50",
    hoverBorder: "hover:border-emerald-500",
    dragBorder: "border-emerald-500",
  },
  {
    type: "transfer",
    label: "Transfer",
    description: "Send tokens to an address",
    icon: Send,
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/50",
    hoverBorder: "hover:border-blue-500",
    dragBorder: "border-blue-500",
  },
];

export function Sidebar() {
  const { sidebarOpen } = useUiStore();
  const [draggingType, setDraggingType] = useState<string | null>(null);

  const handleDragStart = (e: React.DragEvent, type: string) => {
    e.dataTransfer.setData("application/reactflow", type);
    e.dataTransfer.effectAllowed = "move";
    setDraggingType(type);

    // Create a drag image
    const dragImage = e.currentTarget.cloneNode(true) as HTMLElement;
    dragImage.style.opacity = "0.8";
    dragImage.style.position = "absolute";
    dragImage.style.top = "-1000px";
    document.body.appendChild(dragImage);
    e.dataTransfer.setDragImage(dragImage, 50, 25);
    setTimeout(() => document.body.removeChild(dragImage), 0);
  };

  const handleDragEnd = () => {
    setDraggingType(null);
  };

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex h-28 items-center justify-center border-b border-border px-4">
          <div className={cn("relative", sidebarOpen ? "h-24 w-24" : "h-10 w-10")}>
            <Image
              src={sidebarOpen ? "/spica-logo.svg" : "/symbol-spica.svg"}
              alt="Spica"
              fill
              className="object-contain"
              priority
            />
          </div>
        </div>

        {/* Node Palette */}
        <ScrollArea className="flex-1">
          <div className="p-3">
            {sidebarOpen && (
              <div className="mb-3 flex items-center gap-2 px-1">
                <Workflow className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Drag to Canvas
                </span>
              </div>
            )}

            <div className={cn("space-y-2", !sidebarOpen && "space-y-3")}>
              {nodeTypes.map((node) => {
                const Icon = node.icon;
                const isDragging = draggingType === node.type;

                if (!sidebarOpen) {
                  return (
                    <Tooltip key={node.type}>
                      <TooltipTrigger asChild>
                        <div
                          className={cn(
                            "group relative flex h-10 w-10 items-center justify-center rounded-lg border-2 border-dashed transition-all cursor-grab active:cursor-grabbing",
                            node.bgColor,
                            node.borderColor,
                            node.hoverBorder,
                            "hover:scale-110 hover:shadow-lg",
                            isDragging && "opacity-50 scale-95"
                          )}
                          draggable
                          onDragStart={(e) => handleDragStart(e, node.type)}
                          onDragEnd={handleDragEnd}
                        >
                          <Icon className={cn("h-5 w-5", node.color)} />
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="right" sideOffset={10}>
                        <p className="font-medium">{node.label}</p>
                        <p className="text-xs text-muted-foreground">
                          Drag to add to canvas
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  );
                }

                return (
                  <div
                    key={node.type}
                    className={cn(
                      "group relative flex w-full items-center gap-3 rounded-lg border-2 border-dashed p-3 transition-all cursor-grab active:cursor-grabbing",
                      node.borderColor,
                      node.hoverBorder,
                      "hover:bg-accent/30 hover:scale-[1.02] hover:shadow-lg",
                      isDragging && "opacity-50 scale-95"
                    )}
                    draggable
                    onDragStart={(e) => handleDragStart(e, node.type)}
                    onDragEnd={handleDragEnd}
                  >
                    {/* Drag grip indicator */}
                    <div className="absolute left-1 top-1/2 -translate-y-1/2 opacity-40 group-hover:opacity-100 transition-opacity">
                      <GripVertical className="h-4 w-4 text-muted-foreground" />
                    </div>

                    <div
                      className={cn(
                        "ml-3 flex h-9 w-9 items-center justify-center rounded-lg",
                        node.bgColor
                      )}
                    >
                      <Icon className={cn("h-5 w-5", node.color)} />
                    </div>
                    <div className="flex-1 text-left">
                      <div className="text-sm font-medium text-foreground">{node.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {node.description}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Drag hint */}
            {sidebarOpen && (
              <div className="mt-4 px-1 text-center">
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground/60">
                  Drag nodes onto the canvas
                </p>
              </div>
            )}
          </div>
        </ScrollArea>

      </div>
    </TooltipProvider>
  );
}
