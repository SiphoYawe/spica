"use client";

import { cn } from "@/lib/utils";
import { useUiStore } from "@/stores";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  PanelLeftClose,
  PanelLeftOpen,
  Zap,
  ArrowLeftRight,
  Lock,
  Send,
  Workflow,
  Settings,
  HelpCircle,
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
    borderColor: "border-amber-500/30",
  },
  {
    type: "swap",
    label: "Swap",
    description: "Exchange one token for another",
    icon: ArrowLeftRight,
    color: "text-cyan-500",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/30",
  },
  {
    type: "stake",
    label: "Stake",
    description: "Lock tokens to earn rewards",
    icon: Lock,
    color: "text-emerald-500",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/30",
  },
  {
    type: "transfer",
    label: "Transfer",
    description: "Send tokens to an address",
    icon: Send,
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/30",
  },
];

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUiStore();

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex h-full flex-col">
        {/* Logo & Toggle */}
        <div className="flex h-28 items-center justify-between border-b border-border px-4">
          <div className="relative h-24 w-24">
            <Image
              src="/spica-logo.svg"
              alt="Spica"
              fill
              className="object-contain"
              priority
            />
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={toggleSidebar}
            aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          >
            {sidebarOpen ? (
              <PanelLeftClose className="h-4 w-4" />
            ) : (
              <PanelLeftOpen className="h-4 w-4" />
            )}
          </Button>
        </div>

        {/* Node Palette */}
        <ScrollArea className="flex-1">
          <div className="p-3">
            {sidebarOpen && (
              <div className="mb-3 flex items-center gap-2 px-1">
                <Workflow className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Node Types
                </span>
              </div>
            )}

            <div className={cn("space-y-2", !sidebarOpen && "space-y-3")}>
              {nodeTypes.map((node) => {
                const Icon = node.icon;

                if (!sidebarOpen) {
                  return (
                    <Tooltip key={node.type}>
                      <TooltipTrigger asChild>
                        <button
                          className={cn(
                            "flex h-10 w-10 items-center justify-center rounded-lg border transition-all",
                            node.bgColor,
                            node.borderColor,
                            "hover:border-opacity-60"
                          )}
                          draggable
                          onDragStart={(e) => {
                            e.dataTransfer.setData(
                              "application/reactflow",
                              node.type
                            );
                            e.dataTransfer.effectAllowed = "move";
                          }}
                        >
                          <Icon className={cn("h-5 w-5", node.color)} />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent side="right" sideOffset={10}>
                        <p className="font-medium">{node.label}</p>
                        <p className="text-xs text-muted-foreground">
                          {node.description}
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  );
                }

                return (
                  <button
                    key={node.type}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-lg border p-3 transition-all",
                      node.borderColor,
                      "hover:border-opacity-60 hover:bg-accent/50"
                    )}
                    draggable
                    onDragStart={(e) => {
                      e.dataTransfer.setData(
                        "application/reactflow",
                        node.type
                      );
                      e.dataTransfer.effectAllowed = "move";
                    }}
                  >
                    <div
                      className={cn(
                        "flex h-9 w-9 items-center justify-center rounded-lg",
                        node.bgColor
                      )}
                    >
                      <Icon className={cn("h-5 w-5", node.color)} />
                    </div>
                    <div className="flex-1 text-left">
                      <div className="text-sm font-medium">{node.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {node.description}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </ScrollArea>

        {/* Bottom Actions */}
        <div className="border-t border-border p-3">
          <Separator className="mb-3" />
          <div className={cn("flex", sidebarOpen ? "flex-col gap-2" : "flex-col items-center gap-3")}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size={sidebarOpen ? "default" : "icon"}
                  className={cn(
                    sidebarOpen ? "justify-start" : "h-10 w-10"
                  )}
                >
                  <Settings className="h-4 w-4" />
                  {sidebarOpen && <span className="ml-2">Settings</span>}
                </Button>
              </TooltipTrigger>
              {!sidebarOpen && (
                <TooltipContent side="right">Settings</TooltipContent>
              )}
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size={sidebarOpen ? "default" : "icon"}
                  className={cn(
                    sidebarOpen ? "justify-start" : "h-10 w-10"
                  )}
                >
                  <HelpCircle className="h-4 w-4" />
                  {sidebarOpen && <span className="ml-2">Help</span>}
                </Button>
              </TooltipTrigger>
              {!sidebarOpen && (
                <TooltipContent side="right">Help</TooltipContent>
              )}
            </Tooltip>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}
