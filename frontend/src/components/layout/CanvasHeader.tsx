"use client";

import { useWorkflowStore, usePaymentStore, useUiStore } from "@/stores";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Save,
  Share2,
  Undo2,
  Redo2,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Grid3X3,
  Map,
  Loader2,
  Rocket,
} from "lucide-react";

export function CanvasHeader() {
  const {
    workflowName,
    workflowId,
    nodes,
    edges,
    isGenerating,
  } = useWorkflowStore();

  const { openModal } = usePaymentStore();

  const {
    minimapVisible,
    toggleMinimap,
    gridVisible,
    toggleGridVisible,
    canvasZoom,
    setCanvasZoom,
  } = useUiStore();

  const hasWorkflow = nodes.length > 0;

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex h-12 items-center justify-between border-b border-border bg-card/50 backdrop-blur-sm px-4">
        {/* Left: Workflow info */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-medium">
              {workflowName || "Untitled Workflow"}
            </h2>
            {workflowId && (
              <Badge variant="outline" className="text-[10px] font-mono">
                {workflowId.slice(0, 8)}
              </Badge>
            )}
          </div>

          {hasWorkflow && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span>{nodes.length} nodes</span>
              <span className="text-border">•</span>
              <span>{edges.length} connections</span>
            </div>
          )}
        </div>

        {/* Center: Canvas controls */}
        <div className="flex items-center gap-1">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setCanvasZoom(Math.max(0.1, canvasZoom - 0.1))}
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Zoom Out</TooltipContent>
          </Tooltip>

          <div className="w-12 text-center text-xs text-muted-foreground tabular-nums">
            {Math.round(canvasZoom * 100)}%
          </div>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setCanvasZoom(Math.min(2, canvasZoom + 0.1))}
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Zoom In</TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setCanvasZoom(1)}
              >
                <Maximize2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Fit to View</TooltipContent>
          </Tooltip>

          <div className="mx-2 h-4 w-px bg-border" />

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant={gridVisible ? "secondary" : "ghost"}
                size="icon"
                className="h-8 w-8"
                onClick={toggleGridVisible}
              >
                <Grid3X3 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Toggle Grid</TooltipContent>
          </Tooltip>

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
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8" disabled>
                <Undo2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Undo</TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8" disabled>
                <Redo2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Redo</TooltipContent>
          </Tooltip>

          <div className="mx-1 h-4 w-px bg-border" />

          <Button variant="outline" size="sm" className="h-8 gap-2">
            <Save className="h-3.5 w-3.5" />
            Save
          </Button>

          <Button variant="outline" size="sm" className="h-8 gap-2">
            <Share2 className="h-3.5 w-3.5" />
            Share
          </Button>

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
