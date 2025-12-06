"use client";

import { useState, useCallback } from "react";
import { Panel } from "@xyflow/react";
import { Play, Pause } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * FlowRunButton - Workflow execution control
 *
 * Positioned at top-right of canvas
 * Toggles between run/stop states
 */
export function FlowRunButton() {
  const [isRunning, setIsRunning] = useState(false);

  const onClickRun = useCallback(() => {
    setIsRunning((prev) => !prev);
    // TODO: Integrate with workflow runner
  }, []);

  return (
    <Panel position="top-right" className="!m-4">
      <Button
        onClick={onClickRun}
        size="sm"
        className={
          isRunning
            ? "bg-amber-500 hover:bg-amber-600 text-white"
            : "bg-spica hover:bg-spica/90 text-spica-foreground"
        }
      >
        {isRunning ? (
          <>
            <Pause className="mr-2 h-4 w-4" />
            Stop Workflow
          </>
        ) : (
          <>
            <Play className="mr-2 h-4 w-4" />
            Run Workflow
          </>
        )}
      </Button>
    </Panel>
  );
}
