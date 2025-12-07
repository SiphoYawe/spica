"use client";

import { useState, useRef, useEffect } from "react";
import { useWorkflowStore, usePaymentStore, useUiStore } from "@/stores";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Map,
  Loader2,
  Rocket,
  PanelLeft,
  PanelLeftClose,
  Pencil,
  Check,
  X,
} from "lucide-react";
import { MainNav } from "./MainNav";
import { WalletDisplay } from "@/components/WalletDisplay";
import { cn } from "@/lib/utils";

export function CanvasHeader() {
  const {
    workflowName,
    workflowId,
    nodes,
    edges,
    isGenerating,
    setWorkflowName,
  } = useWorkflowStore();

  const { openModal } = usePaymentStore();

  const {
    sidebarOpen,
    toggleSidebar,
    minimapVisible,
    toggleMinimap,
  } = useUiStore();

  // Editing state
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(workflowName || "");
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when editing starts
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  // Sync edit value when workflow name changes externally
  useEffect(() => {
    if (!isEditing) {
      setEditValue(workflowName || "");
    }
  }, [workflowName, isEditing]);

  const handleStartEdit = () => {
    setEditValue(workflowName || "Untitled Workflow");
    setIsEditing(true);
  };

  const handleSave = () => {
    const trimmedValue = editValue.trim();
    if (trimmedValue) {
      setWorkflowName(trimmedValue);
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValue(workflowName || "");
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSave();
    } else if (e.key === "Escape") {
      handleCancel();
    }
  };

  const hasWorkflow = nodes.length > 0;

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex h-14 items-center border-b border-border bg-card/50 backdrop-blur-sm px-4 gap-4">
        {/* Left: Sidebar toggle + Main Navigation */}
        <div className="flex items-center gap-3 flex-shrink-0">
          {/* Sidebar Toggle Button */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={toggleSidebar}
              >
                {sidebarOpen ? (
                  <PanelLeftClose className="h-4 w-4" />
                ) : (
                  <PanelLeft className="h-4 w-4" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              {sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
            </TooltipContent>
          </Tooltip>

          <MainNav />
        </div>

        {/* Center: Workflow info - takes available space */}
        <div className="flex items-center gap-3 flex-1 min-w-0 overflow-hidden">
          {hasWorkflow && (
            <>
              <div className="h-6 w-px bg-border/50 flex-shrink-0" />
              <div className="flex items-center gap-2 min-w-0">
                {isEditing ? (
                  // Editing mode
                  <div className="flex items-center gap-1">
                    <Input
                      ref={inputRef}
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onKeyDown={handleKeyDown}
                      onBlur={handleSave}
                      className="h-7 w-48 text-sm font-medium bg-background/80 border-cyber-green/50 focus:border-cyber-green"
                      placeholder="Workflow name"
                    />
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 text-cyber-green hover:text-cyber-green hover:bg-cyber-green/10"
                          onClick={handleSave}
                        >
                          <Check className="h-3.5 w-3.5" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Save (Enter)</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 text-muted-foreground hover:text-foreground"
                          onClick={handleCancel}
                        >
                          <X className="h-3.5 w-3.5" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Cancel (Esc)</TooltipContent>
                    </Tooltip>
                  </div>
                ) : (
                  // Display mode - workflow name with node info on hover
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button
                        onClick={handleStartEdit}
                        className={cn(
                          "group flex items-center gap-1.5 rounded px-1.5 py-0.5 -ml-1.5",
                          "hover:bg-muted/50 transition-colors cursor-pointer"
                        )}
                      >
                        <h2 className="text-sm font-medium text-muted-foreground truncate max-w-[200px]">
                          {workflowName || "Untitled Workflow"}
                        </h2>
                        <Pencil className="h-3 w-3 text-muted-foreground/50 group-hover:text-muted-foreground transition-colors flex-shrink-0" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" className="flex flex-col gap-1">
                      <span className="font-medium">Click to rename</span>
                      <span className="text-xs text-muted-foreground">
                        {nodes.length} nodes • {edges.length} connections
                      </span>
                    </TooltipContent>
                  </Tooltip>
                )}
                {workflowId && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Badge variant="outline" className="text-[10px] font-mono flex-shrink-0 cursor-help">
                        {workflowId.slice(0, 8)}
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                      Workflow ID: {workflowId}
                    </TooltipContent>
                  </Tooltip>
                )}
              </div>
            </>
          )}
        </div>

        {/* Right: Canvas toggles + Actions */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Canvas view toggles */}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant={minimapVisible ? "secondary" : "ghost"}
                size="icon"
                className="h-8 w-8"
                onClick={toggleMinimap}
              >
                <Map className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Toggle Minimap</TooltipContent>
          </Tooltip>

          <div className="mx-1 h-4 w-px bg-border" />

          {/* Wallet Display */}
          <WalletDisplay />

          <div className="mx-1 h-4 w-px bg-border" />

          <Button
            variant="cyber"
            size="sm"
            className="h-8 gap-2"
            disabled={!hasWorkflow || isGenerating}
            onClick={openModal}
          >
            {isGenerating ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Rocket className="h-3.5 w-3.5" />
            )}
            Deploy
          </Button>
        </div>
      </div>
    </TooltipProvider>
  );
}
