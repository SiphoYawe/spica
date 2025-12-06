"use client";

import { useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Play,
  Pause,
  Trash2,
  Clock,
  Activity,
  ExternalLink,
  Loader2,
  AlertTriangle,
} from "lucide-react";
import { apiClient } from "@/api/client";
import { toast } from "sonner";

// Time constants for readability
const MS_PER_MINUTE = 60000;
const MS_PER_HOUR = 3600000;
const MS_PER_DAY = 86400000;

interface WorkflowCardProps {
  workflow: {
    workflow_id: string;
    workflow_name: string;
    workflow_description: string;
    status: string;
    enabled: boolean;
    trigger_type: string;
    trigger_summary: string;
    execution_count: number;
    created_at: string;
    last_executed_at: string | null;
    next_check_at?: string | null;
  };
  onUpdate?: () => void;
}

export function WorkflowCard({ workflow, onUpdate }: WorkflowCardProps) {
  const [isToggling, setIsToggling] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const isActive = workflow.status === "active" && workflow.enabled;

  const handleToggle = async () => {
    setIsToggling(true);
    try {
      const result = await apiClient.toggleWorkflow(workflow.workflow_id, !workflow.enabled);
      if (result.success) {
        toast.success(workflow.enabled ? "Workflow paused" : "Workflow resumed");
        onUpdate?.();
      } else {
        toast.error(result.error?.message || "Failed to update workflow");
      }
    } catch {
      toast.error("Failed to update workflow");
    } finally {
      setIsToggling(false);
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      const result = await apiClient.deleteWorkflow(workflow.workflow_id);
      if (result.success) {
        toast.success("Workflow deleted");
        setShowDeleteDialog(false);
        onUpdate?.();
      } else {
        toast.error(result.error?.message || "Failed to delete workflow");
      }
    } catch {
      toast.error("Failed to delete workflow");
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatRelativeTime = (dateStr: string | null) => {
    if (!dateStr) return "Never";
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / MS_PER_MINUTE);
    const hours = Math.floor(diff / MS_PER_HOUR);
    const days = Math.floor(diff / MS_PER_DAY);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const formatNextCheck = (dateStr: string | null | undefined) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    const now = new Date();
    const diff = date.getTime() - now.getTime();

    if (diff < 0) return "Checking...";

    const minutes = Math.floor(diff / MS_PER_MINUTE);
    const hours = Math.floor(diff / MS_PER_HOUR);

    if (minutes < 1) return "< 1m";
    if (minutes < 60) return `${minutes}m`;
    return `${hours}h ${minutes % 60}m`;
  };

  return (
    <TooltipProvider delayDuration={0}>
      <Card
        className={cn(
          "group relative overflow-hidden transition-all duration-200 hover:border-spica/30",
          "bg-card/50 backdrop-blur-sm",
          isActive && "border-spica/20"
        )}
      >
        {/* Status indicator line */}
        <div
          className={cn(
            "absolute left-0 top-0 h-full w-1 transition-colors",
            isActive ? "bg-spica" : "bg-amber-500"
          )}
        />

        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <Link
                href={`/workflows/${workflow.workflow_id}`}
                className="group/link flex items-center gap-2"
              >
                <h3 className="font-medium text-sm truncate group-hover/link:text-spica transition-colors">
                  {workflow.workflow_name}
                </h3>
                <ExternalLink className="h-3 w-3 opacity-0 group-hover/link:opacity-100 transition-opacity text-muted-foreground" />
              </Link>
              <p className="text-xs text-muted-foreground truncate mt-1">
                {workflow.workflow_description}
              </p>
            </div>

            <Badge
              variant="outline"
              className={cn(
                "text-[10px] shrink-0",
                isActive
                  ? "border-spica/50 text-spica"
                  : "border-amber-500/50 text-amber-500"
              )}
            >
              {isActive ? "Active" : "Paused"}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Trigger info */}
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <Clock className="h-3.5 w-3.5" aria-hidden="true" />
              <span className="truncate">{workflow.trigger_summary}</span>
            </div>
            {isActive && formatNextCheck(workflow.next_check_at) && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-spica font-medium shrink-0">
                    Next: {formatNextCheck(workflow.next_check_at)}
                  </span>
                </TooltipTrigger>
                <TooltipContent>Next trigger check</TooltipContent>
              </Tooltip>
            )}
          </div>

          {/* Stats row */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-4">
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-1.5 text-muted-foreground">
                    <Activity className="h-3.5 w-3.5" />
                    <span>{workflow.execution_count}</span>
                  </div>
                </TooltipTrigger>
                <TooltipContent>Executions</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="text-muted-foreground">
                    Last: {formatRelativeTime(workflow.last_executed_at)}
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  {workflow.last_executed_at
                    ? formatDate(workflow.last_executed_at)
                    : "Never executed"}
                </TooltipContent>
              </Tooltip>
            </div>

            <div className="text-muted-foreground/60">
              Created {formatDate(workflow.created_at)}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 pt-2 border-t border-border/50" role="group" aria-label="Workflow actions">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 flex-1 gap-2"
                  onClick={handleToggle}
                  disabled={isToggling}
                  aria-label={isActive ? "Pause workflow" : "Resume workflow"}
                >
                  {isToggling ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                  ) : isActive ? (
                    <Pause className="h-3.5 w-3.5" aria-hidden="true" />
                  ) : (
                    <Play className="h-3.5 w-3.5" aria-hidden="true" />
                  )}
                  {isActive ? "Pause" : "Resume"}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {isActive ? "Pause workflow" : "Resume workflow"}
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                  onClick={() => setShowDeleteDialog(true)}
                  aria-label={`Delete workflow ${workflow.workflow_name}`}
                >
                  <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Delete workflow</TooltipContent>
            </Tooltip>
          </div>
        </CardContent>

        {/* Delete confirmation dialog */}
        <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-destructive" />
                Delete Workflow
              </DialogTitle>
              <DialogDescription>
                Are you sure you want to delete &ldquo;{workflow.workflow_name}&rdquo;? This
                action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowDeleteDialog(false)}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleDelete}
                disabled={isDeleting}
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Deleting...
                  </>
                ) : (
                  "Delete"
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </Card>
    </TooltipProvider>
  );
}
