"use client";

import { useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
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
  ArrowUpRight,
  Loader2,
  AlertTriangle,
  Zap,
  Calendar,
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
      <div
        className={cn(
          "group relative overflow-hidden rounded-xl transition-all duration-300",
          // Dark black background with no gradient
          "bg-[#0a0a0c]",
          // Subtle light grey border for all states
          "border border-zinc-700/60 hover:border-zinc-600/80",
          // Subtle shadow on hover
          "hover:shadow-lg",
          isActive && "hover:shadow-spica/5"
        )}
      >
        {/* Subtle corner glow on hover - only for active */}
        {isActive && (
          <div className="absolute -top-20 -right-20 w-40 h-40 bg-spica/5 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        )}

        {/* Content */}
        <div className="relative p-4 sm:p-5">
          {/* Header - Stack on mobile, row on larger */}
          <div className="flex flex-col gap-3 mb-4">
            {/* Title row with badge */}
            <div className="flex items-start justify-between gap-3">
              <Link
                href={`/workflows/${workflow.workflow_id}`}
                className="group/link flex-1 min-w-0"
              >
                <h3 className="font-semibold text-base text-white group-hover/link:text-spica transition-colors line-clamp-2 leading-tight">
                  {workflow.workflow_name}
                  <ArrowUpRight className="inline-block ml-1 h-3.5 w-3.5 opacity-0 group-hover/link:opacity-100 transition-all text-spica" />
                </h3>
              </Link>

              {/* Status Badge */}
              <div
                className={cn(
                  "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] sm:text-xs font-semibold uppercase tracking-wider shrink-0",
                  isActive
                    ? "bg-spica/15 text-spica border border-spica/30"
                    : "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                )}
              >
                <span className={cn(
                  "w-1.5 h-1.5 rounded-full",
                  isActive ? "bg-spica animate-pulse" : "bg-amber-400"
                )} />
                {isActive ? "Active" : "Paused"}
              </div>
            </div>

            {/* Description */}
            <p className="text-sm text-zinc-400 line-clamp-2 leading-relaxed">
              {workflow.workflow_description}
            </p>
          </div>

          {/* Trigger Info Card */}
          <div className={cn(
            "rounded-lg p-2.5 sm:p-3 mb-4",
            "bg-zinc-900/80 border border-zinc-800/80"
          )}>
            <div className="flex items-center gap-2 text-sm">
              <div className={cn(
                "flex items-center justify-center w-7 h-7 sm:w-8 sm:h-8 rounded-lg shrink-0",
                isActive ? "bg-spica/10" : "bg-amber-500/10"
              )}>
                <Clock className={cn(
                  "h-3.5 w-3.5 sm:h-4 sm:w-4",
                  isActive ? "text-spica" : "text-amber-400"
                )} />
              </div>
              <span className="text-zinc-300 font-medium text-xs sm:text-sm leading-tight">
                {workflow.trigger_summary}
              </span>
            </div>
          </div>

          {/* Stats Grid - Responsive */}
          <div className="grid grid-cols-3 gap-2 sm:gap-3 mb-4 sm:mb-5">
            {/* Executions */}
            <div className="flex flex-col gap-0.5 sm:gap-1 p-2 sm:p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/60">
              <div className="flex items-center gap-1 text-zinc-500">
                <Activity className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                <span className="text-[9px] sm:text-[10px] font-medium uppercase tracking-wide">Runs</span>
              </div>
              <span className="text-base sm:text-lg font-bold text-white tabular-nums">
                {workflow.execution_count}
              </span>
            </div>

            {/* Last Run */}
            <div className="flex flex-col gap-0.5 sm:gap-1 p-2 sm:p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/60">
              <div className="flex items-center gap-1 text-zinc-500">
                <Zap className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                <span className="text-[9px] sm:text-[10px] font-medium uppercase tracking-wide">Last</span>
              </div>
              <span className="text-xs sm:text-sm font-semibold text-zinc-300 truncate">
                {formatRelativeTime(workflow.last_executed_at)}
              </span>
            </div>

            {/* Created */}
            <div className="flex flex-col gap-0.5 sm:gap-1 p-2 sm:p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/60">
              <div className="flex items-center gap-1 text-zinc-500">
                <Calendar className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                <span className="text-[9px] sm:text-[10px] font-medium uppercase tracking-wide">Created</span>
              </div>
              <span className="text-xs sm:text-sm font-semibold text-zinc-300">
                {formatDate(workflow.created_at)}
              </span>
            </div>
          </div>

          {/* Next Check (if active) */}
          {isActive && formatNextCheck(workflow.next_check_at) && (
            <div className="flex items-center justify-center gap-2 py-2 mb-4 rounded-lg bg-spica/10 border border-spica/20">
              <div className="w-2 h-2 rounded-full bg-spica animate-pulse" />
              <span className="text-xs font-medium text-spica">
                Next check in {formatNextCheck(workflow.next_check_at)}
              </span>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 pt-3 sm:pt-4 border-t border-zinc-800/80">
            <Button
              variant="outline"
              size="sm"
              className={cn(
                "flex-1 h-9 sm:h-10 gap-1.5 sm:gap-2 font-medium transition-all text-xs sm:text-sm",
                "bg-transparent border-zinc-700/60",
                isActive
                  ? "hover:bg-amber-500/10 hover:border-amber-500/50 hover:text-amber-400"
                  : "hover:bg-spica/10 hover:border-spica/50 hover:text-spica"
              )}
              onClick={handleToggle}
              disabled={isToggling}
            >
              {isToggling ? (
                <Loader2 className="h-3.5 w-3.5 sm:h-4 sm:w-4 animate-spin" />
              ) : isActive ? (
                <Pause className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              ) : (
                <Play className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
              )}
              {isActive ? "Pause" : "Resume"}
            </Button>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className={cn(
                    "h-9 w-9 sm:h-10 sm:w-10 p-0",
                    "bg-transparent border-zinc-700/60",
                    "hover:bg-red-500/10 hover:border-red-500/50 hover:text-red-400",
                    "transition-all"
                  )}
                  onClick={() => setShowDeleteDialog(true)}
                >
                  <Trash2 className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Delete workflow</TooltipContent>
            </Tooltip>
          </div>
        </div>

        {/* Delete confirmation dialog */}
        <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
          <DialogContent className="bg-[#0a0a0c] border-zinc-800">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-3 text-white">
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-500/10">
                  <AlertTriangle className="h-5 w-5 text-red-400" />
                </div>
                Delete Workflow
              </DialogTitle>
              <DialogDescription className="text-zinc-400 pt-2">
                Are you sure you want to delete <span className="text-white font-medium">&ldquo;{workflow.workflow_name}&rdquo;</span>?
                This action cannot be undone and all execution history will be lost.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="gap-2 sm:gap-2">
              <Button
                variant="outline"
                onClick={() => setShowDeleteDialog(false)}
                disabled={isDeleting}
                className="border-zinc-700 hover:bg-zinc-900"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleDelete}
                disabled={isDeleting}
                className="bg-red-500/90 hover:bg-red-500"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Deleting...
                  </>
                ) : (
                  "Delete Workflow"
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
}
