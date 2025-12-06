"use client";

import { useState } from "react";
import { ReactFlowProvider } from "@xyflow/react";
import { PanelLeftClose, PanelLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { CanvasStoreProvider } from "../store";
import { WorkflowSidebar } from "./workflow-sidebar";
import { WorkflowCanvasPro } from "../workflow-canvas-pro";
import type { SpicaNode } from "../config";
import type { SpicaEdge } from "../edges";

interface WorkflowLayoutProps {
  initialNodes?: SpicaNode[];
  initialEdges?: SpicaEdge[];
  children?: React.ReactNode;
}

/**
 * WorkflowLayout - Main layout wrapper for workflow editor
 *
 * Structure:
 * - Collapsible sidebar (left)
 * - Main canvas area (center)
 * - Header slot (via children)
 *
 * Providers:
 * - CanvasStoreProvider (Zustand)
 * - ReactFlowProvider
 */
export function WorkflowLayout({
  initialNodes = [],
  initialEdges = [],
  children,
}: WorkflowLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <CanvasStoreProvider
      initialState={{
        nodes: initialNodes,
        edges: initialEdges,
      }}
    >
      <ReactFlowProvider>
        <TooltipProvider delayDuration={0}>
          <div className="flex h-full w-full overflow-hidden bg-background">
            {/* Sidebar */}
            <WorkflowSidebar collapsed={sidebarCollapsed} />

            {/* Main content area */}
            <div className="relative flex flex-1 flex-col overflow-hidden">
              {/* Optional header slot */}
              {children}

              {/* Canvas */}
              <div className="relative flex-1">
                <WorkflowCanvasPro />

                {/* Sidebar toggle button */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute left-4 top-4 z-20 h-8 w-8 rounded-lg border border-border bg-card/95 backdrop-blur-sm shadow-lg"
                      onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                    >
                      {sidebarCollapsed ? (
                        <PanelLeft className="h-4 w-4" />
                      ) : (
                        <PanelLeftClose className="h-4 w-4" />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    {sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                  </TooltipContent>
                </Tooltip>
              </div>
            </div>
          </div>
        </TooltipProvider>
      </ReactFlowProvider>
    </CanvasStoreProvider>
  );
}
