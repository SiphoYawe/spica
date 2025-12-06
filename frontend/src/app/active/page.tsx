"use client";

import { useEffect, useState, useCallback } from "react";
import { AppLayout, Sidebar, CanvasHeader } from "@/components/layout";
import { useAppInitialization } from "@/hooks";
import { WorkflowCard } from "@/components/workflow";
import { Activity, Plus, RefreshCw, AlertCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
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

  // Skeleton loader component for loading state
  const WorkflowCardSkeleton = () => (
    <Card className="relative overflow-hidden bg-card/50 backdrop-blur-sm">
      <div className="absolute left-0 top-0 h-full w-1 bg-muted" />
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-48" />
          </div>
          <Skeleton className="h-5 w-14 rounded-full" />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Skeleton className="h-3 w-40" />
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Skeleton className="h-3 w-8" />
            <Skeleton className="h-3 w-16" />
          </div>
          <Skeleton className="h-3 w-24" />
        </div>
        <div className="flex items-center gap-2 pt-2 border-t border-border/50">
          <Skeleton className="h-8 flex-1" />
          <Skeleton className="h-8 w-8" />
        </div>
      </CardContent>
    </Card>
  );

  const fetchWorkflows = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await apiClient.listWorkflows();
      if (result.success && result.data) {
        setWorkflows(result.data.workflows);
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
    <AppLayout sidebar={<Sidebar />} header={<CanvasHeader />}>
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
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
                <p className="text-sm text-muted-foreground mt-1">{error}</p>
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
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
