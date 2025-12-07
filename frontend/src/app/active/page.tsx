"use client";

import { useEffect, useState, useCallback } from "react";
import { AppLayout, Sidebar, CanvasHeader } from "@/components/layout";
import { useAppInitialization } from "@/hooks";
import { WorkflowCard } from "@/components/workflow";
import { Activity, Plus, RefreshCw, AlertCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { apiClient } from "@/api/client";

interface WorkflowSummary {
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
}

export default function ActiveWorkflowsPage() {
  useAppInitialization();

  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Skeleton loader component for loading state - matches WorkflowCard design
  const WorkflowCardSkeleton = () => (
    <div className="relative overflow-hidden rounded-xl bg-[#0a0a0c] border border-zinc-800/80">
      {/* Status line skeleton */}
      <div className="absolute top-0 left-0 right-0 h-px bg-zinc-700/50" />

      <div className="p-5">
        {/* Header skeleton */}
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex-1 space-y-3">
            <Skeleton className="h-5 w-40 bg-zinc-800/80" />
            <Skeleton className="h-4 w-full bg-zinc-800/50" />
          </div>
          <Skeleton className="h-7 w-20 rounded-full bg-zinc-800/80" />
        </div>

        {/* Trigger info skeleton */}
        <div className="rounded-lg p-3 mb-4 bg-zinc-900/80 border border-zinc-800/80">
          <div className="flex items-center gap-2">
            <Skeleton className="h-8 w-8 rounded-lg bg-zinc-800/80" />
            <Skeleton className="h-4 w-32 bg-zinc-800/60" />
          </div>
        </div>

        {/* Stats grid skeleton */}
        <div className="grid grid-cols-3 gap-3 mb-5">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex flex-col gap-2 p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/60">
              <Skeleton className="h-3 w-12 bg-zinc-800/60" />
              <Skeleton className="h-5 w-8 bg-zinc-800/80" />
            </div>
          ))}
        </div>

        {/* Actions skeleton */}
        <div className="flex items-center gap-2 pt-4 border-t border-zinc-800/80">
          <Skeleton className="h-10 flex-1 rounded-md bg-zinc-800/60" />
          <Skeleton className="h-10 w-10 rounded-md bg-zinc-800/60" />
        </div>
      </div>
    </div>
  );

  const fetchWorkflows = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await apiClient.listWorkflows();
      if (result.success && result.data) {
        // Check for backend success and workflows array
        if (result.data.success !== false && Array.isArray(result.data.workflows)) {
          setWorkflows(result.data.workflows);
        } else {
          // Handle backend error response structure
          const backendError = result.data as unknown as { error?: { message?: string } };
          setError(backendError.error?.message || "Failed to load workflows");
        }
      } else {
        setError(result.error?.message || "Failed to load workflows");
      }
    } catch {
      setError("Failed to load workflows");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  return (
    <AppLayout sidebar={<Sidebar />} header={<CanvasHeader />} canvasVariant="subtle">
      <div className="h-full w-full overflow-auto p-6">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold">Active Workflows</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Manage and monitor your automated DeFi workflows
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchWorkflows}
              disabled={isLoading}
            >
              <RefreshCw
                className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
            <Link href="/">
              <Button variant="cyber" size="sm">
                <Plus className="h-4 w-4 mr-2" />
                New Workflow
              </Button>
            </Link>
          </div>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <WorkflowCardSkeleton key={i} />
            ))}
          </div>
        ) : error ? (
          <div className="flex h-64 items-center justify-center">
            <div className="flex flex-col items-center gap-4 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
                <AlertCircle className="h-8 w-8 text-destructive" />
              </div>
              <div>
                <p className="font-medium">Failed to load workflows</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {typeof error === 'string' ? error : 'An error occurred'}
                </p>
              </div>
              <Button variant="outline" onClick={fetchWorkflows}>
                Try Again
              </Button>
            </div>
          </div>
        ) : workflows.length === 0 ? (
          <div className="flex h-64 items-center justify-center">
            <div className="flex flex-col items-center gap-6 text-center max-w-md">
              <div className="relative">
                <div className="absolute inset-0 bg-spica/20 blur-2xl rounded-full" />
                <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-card border border-border">
                  <Activity className="h-10 w-10 text-muted-foreground" />
                </div>
              </div>

              <div className="space-y-2">
                <h2 className="text-xl font-semibold">No Active Workflows</h2>
                <p className="text-muted-foreground text-sm">
                  You don&apos;t have any active workflows yet. Create your
                  first workflow to start automating your DeFi strategies.
                </p>
              </div>

              <Link href="/">
                <Button variant="cyber" className="gap-2">
                  <Plus className="h-4 w-4" />
                  Create Workflow
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
            {workflows.map((workflow) => (
              <WorkflowCard
                key={workflow.workflow_id}
                workflow={workflow}
                onUpdate={fetchWorkflows}
              />
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
