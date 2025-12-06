"use client";

import { useCallback } from "react";
import {
  Panel,
  useReactFlow,
  useStore,
  useViewport,
} from "@xyflow/react";
import {
  Maximize,
  Route,
  Minus,
  Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useLayout } from "../hooks";

/**
 * ZoomSlider - Zoom control with slider and buttons
 */
function ZoomSlider() {
  const { zoomIn, zoomOut, fitView, setViewport } = useReactFlow();
  const { zoom } = useViewport();

  // Get zoom limits from store
  const minZoom = useStore((state) => state.minZoom);
  const maxZoom = useStore((state) => state.maxZoom);

  // Handle slider change
  const onZoomChange = useCallback(
    (value: number[]) => {
      setViewport({ x: 0, y: 0, zoom: value[0] }, { duration: 300 });
    },
    [setViewport]
  );

  // Zoom percentage display
  const zoomPercent = Math.round(zoom * 100);

  return (
    <TooltipProvider delayDuration={0}>
      <Panel
        position="bottom-left"
        className="!m-4 flex items-center gap-1 rounded-lg border border-border bg-card/95 p-1 backdrop-blur-sm shadow-lg"
      >
        {/* Zoom out */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => zoomOut({ duration: 300 })}
            >
              <Minus className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">Zoom out</TooltipContent>
        </Tooltip>

        {/* Slider */}
        <div className="w-[100px] px-2">
          <Slider
            value={[zoom]}
            min={minZoom}
            max={maxZoom}
            step={0.01}
            onValueChange={onZoomChange}
            className="cursor-pointer"
          />
        </div>

        {/* Zoom in */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => zoomIn({ duration: 300 })}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">Zoom in</TooltipContent>
        </Tooltip>

        {/* Separator */}
        <div className="mx-1 h-5 w-px bg-border" />

        {/* Zoom percentage */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-12 text-xs font-mono"
              onClick={() => setViewport({ x: 0, y: 0, zoom: 1 }, { duration: 300 })}
            >
              {zoomPercent}%
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">Reset zoom to 100%</TooltipContent>
        </Tooltip>

        {/* Fit view */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => fitView({ duration: 300, padding: 0.2 })}
            >
              <Maximize className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">Fit to view</TooltipContent>
        </Tooltip>
      </Panel>
    </TooltipProvider>
  );
}

/**
 * LayoutButton - Auto-layout trigger
 */
function LayoutButton() {
  const applyLayout = useLayout();

  return (
    <TooltipProvider delayDuration={0}>
      <Panel
        position="bottom-right"
        className="!m-4 rounded-lg border border-border bg-card/95 p-1 backdrop-blur-sm shadow-lg"
      >
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={applyLayout}
            >
              <Route className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="left">Auto-layout nodes</TooltipContent>
        </Tooltip>
      </Panel>
    </TooltipProvider>
  );
}

/**
 * WorkflowControls - Combined zoom and layout controls
 */
export function WorkflowControls() {
  return (
    <>
      <ZoomSlider />
      <LayoutButton />
    </>
  );
}
