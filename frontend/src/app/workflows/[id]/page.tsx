"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AppLayout, Sidebar, CanvasHeader } from "@/components/layout";
import { useAppInitialization } from "@/hooks";
import { ReadOnlyGraph, ExecutionHistory, ActivityTimeline } from "@/components/workflow";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  ArrowLeft,
  Play,
  Pause,
  Clock,
  Activity,
  Zap,
  RefreshCw,
  AlertCircle,
  Settings2,
  History,
  Loader2,
} from "lucide-react";
import { apiClient } from "@/api/client";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import type { Node, Edge } from "@xyflow/react";

interface WorkflowDetail {
  workflow_id: string;
  workflow_name: string;
  workflow_description: string;
  status: string;
  enabled: boolean;
  trigger_type: string;
  trigger_summary: string;
  nodes: Node[];
  edges: Edge[];
  execution_count: number;
  trigger_count: number;
  created_at: string;
  updated_at: string;
  last_executed_at: string | null;
  last_error: string | null;
}

// Execution record type for history display (matches ExecutionHistory component)
interface ExecutionRecord {
  id: string;
  workflow_id: string;
  triggered_at: string;
  executed_at?: string;
  status: "pending" | "running" | "success" | "failed";
  transaction_hash?: string;
  error?: string;
  duration_ms?: number;
}

export default function WorkflowDetailPage() {
  const params = useParams();
  const workflowId = params.id as string;

  useAppInitialization();

  const [workflow, setWorkflow] = useState<WorkflowDetail | null>(null);
  const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isToggling, setIsToggling] = useState(false);

  const fetchWorkflow = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Fetch workflow details and executions in parallel
      const [workflowResult, executionsResult] = await Promise.all([
        apiClient.getWorkflow(workflowId),
        apiClient.listExecutions({ workflow_id: workflowId, limit: 20 })
      ]);

      // Handle workflow response
      if (workflowResult.success && workflowResult.data) {
        if (workflowResult.data.success !== false && workflowResult.data.workflow_id) {
          setWorkflow(workflowResult.data as unknown as WorkflowDetail);
        } else {
          const backendError = workflowResult.data as unknown as { error?: { message?: string } };
          setError(backendError.error?.message || "Failed to load workflow");
          return;
        }
      } else {
        setError(workflowResult.error?.message || "Failed to load workflow");
        return;
      }

      // Handle executions response
      if (executionsResult.success && executionsResult.data?.executions) {
        const mappedExecutions: ExecutionRecord[] = executionsResult.data.executions.map(e => {
          // Calculate duration if both timestamps exist
          let duration_ms: number | undefined;
          if (e.started_at && e.completed_at) {
            duration_ms = new Date(e.completed_at).getTime() - new Date(e.started_at).getTime();
          }

          // Map API status to UI status
          let status: ExecutionRecord["status"] = "pending";
          if (e.status === "completed") status = "success";
          else if (e.status === "failed") status = "failed";
          else if (e.status === "running") status = "running";

          return {
            id: e.execution_id,
            workflow_id: e.workflow_id,
            triggered_at: e.started_at,
            executed_at: e.completed_at || undefined,
            status,
            transaction_hash: e.tx_hash || undefined,
            error: e.error || undefined,
            duration_ms,
          };
        });
        setExecutions(mappedExecutions);
      } else {
        // If no executions, set empty array
        setExecutions([]);
      }
    } catch {
      setError("Failed to load workflow");
    } finally {
      setIsLoading(false);
    }
  }, [workflowId]);

  useEffect(() => {
    fetchWorkflow();
  }, [fetchWorkflow]);

  const handleToggle = async () => {
    if (!workflow) return;
    setIsToggling(true);
    try {
      const result = await apiClient.toggleWorkflow(workflow.workflow_id, !workflow.enabled);
      if (result.success) {
        toast.success(workflow.enabled ? "Workflow paused" : "Workflow resumed");
        fetchWorkflow();
      } else {
        toast.error(result.error?.message || "Failed to update workflow");
      }
    } catch {
      toast.error("Failed to update workflow");
    } finally {
      setIsToggling(false);
    }
  };

  const isActive = workflow?.status === "active" && workflow?.enabled;

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Activity event type
  type ActivityEvent = {
    id: string;
    type: "created" | "activated" | "paused" | "executed" | "failed" | "updated";
    timestamp: string;
    message: string;
    details?: string;
  };

  // Generate activity events from workflow data
  const activityEvents = useMemo((): ActivityEvent[] => {
    if (!workflow) return [];
    const events: ActivityEvent[] = [
      {
        id: "created",
        type: "created",
        timestamp: workflow.created_at,
        message: "Workflow created",
        details: workflow.workflow_name,
      },
    ];

    if (workflow.enabled) {
      events.push({
        id: "activated",
        type: "activated",
        timestamp: workflow.updated_at,
        message: "Workflow activated",
      });
    } else if (workflow.status === "paused") {
      events.push({
        id: "paused",
        type: "paused",
        timestamp: workflow.updated_at,
        message: "Workflow paused",
      });
    }

    if (workflow.last_executed_at) {
      events.push({
        id: "executed",
        type: "executed",
        timestamp: workflow.last_executed_at,
        message: "Last execution",
        details: workflow.last_error ? `Error: ${workflow.last_error}` : "Completed successfully",
      });
    }

    return events.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [workflow]);

  // Loading skeleton
  if (isLoading) {
    return (
      <AppLayout sidebar={<Sidebar />} header={<CanvasHeader />}>
        <div className="h-full w-full overflow-auto p-6">
          {/* Header skeleton */}
          <div className="flex items-center gap-4 mb-6">
            <Skeleton className="h-8 w-8 rounded" />
            <div className="flex-1">
              <Skeleton className="h-6 w-48 mb-2" />
              <Skeleton className="h-4 w-96" />
            </div>
            <Skeleton className="h-8 w-20" />
          </div>

          {/* Main content skeleton */}
          <div className="grid gap-6 lg:grid-cols-[350px_1fr]">
            <div className="space-y-4">
              <Skeleton className="h-40 rounded-lg" />
              <Skeleton className="h-32 rounded-lg" />
            </div>
            <Skeleton className="h-[400px] rounded-lg" />
          </div>
        </div>
      </AppLayout>
    );
  }

  // Error state
  if (error || !workflow) {
    return (
      <AppLayout sidebar={<Sidebar />} header={<CanvasHeader />}>
        <div className="flex h-full w-full items-center justify-center p-8">
          <div className="flex flex-col items-center gap-6 text-center max-w-md">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
              <AlertCircle className="h-8 w-8 text-destructive" />
            </div>
            <div>
              <p className="font-medium">Failed to load workflow</p>
              <p className="text-sm text-muted-foreground mt-1">{error}</p>
            </div>
            <div className="flex gap-2">
              <Link href="/active">
                <Button variant="outline" className="gap-2">
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </Button>
              </Link>
              <Button onClick={fetchWorkflow}>Try Again</Button>
            </div>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout sidebar={<Sidebar />} header={<CanvasHeader />}>
      <TooltipProvider delayDuration={0}>
        <div className="h-full w-full overflow-auto">
          {/* Header */}
          <div className="sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-border px-6 py-4">
            <div className="flex items-center gap-4">
              <Link href="/active">
                <Button variant="ghost" size="icon" className="shrink-0">
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              </Link>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3">
                  <h1 className="text-xl font-semibold truncate">{workflow.workflow_name}</h1>
                  <Badge
                    variant="outline"
                    className={cn(
                      "shrink-0",
                      isActive
                        ? "border-spica/50 text-spica"
                        : "border-amber-500/50 text-amber-500"
                    )}
                  >
                    {isActive ? "Active" : "Paused"}
                  </Badge>
                </div>
                <p className="text-base text-muted-foreground truncate">
                  {workflow.workflow_description}
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={fetchWorkflow}
                  disabled={isLoading}
                >
                  <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
                </Button>
                <Button
                  variant={isActive ? "outline" : "cyber"}
                  size="sm"
                  onClick={handleToggle}
                  disabled={isToggling}
                  className="gap-2"
                >
                  {isToggling ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : isActive ? (
                    <Pause className="h-4 w-4" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  {isActive ? "Pause" : "Resume"}
                </Button>
              </div>
            </div>
          </div>

          {/* Main content */}
          <div className="p-6">
            <div className="grid gap-6 lg:grid-cols-[350px_1fr]">
              {/* Left column - Info */}
              <div className="space-y-4">
                {/* Trigger Card */}
                <Card className="bg-card/50 backdrop-blur-sm">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base font-medium flex items-center gap-2">
                      <Zap className="h-4 w-4 text-amber-500" />
                      Trigger Configuration
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Type</span>
                      <Badge variant="secondary" className="text-sm">
                        {workflow.trigger_type}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Condition</span>
                      <span className="text-sm font-mono">{workflow.trigger_summary}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Trigger Count</span>
                      <span className="text-sm font-mono">{workflow.trigger_count}</span>
                    </div>
                  </CardContent>
                </Card>

                {/* Stats Card */}
                <Card className="bg-card/50 backdrop-blur-sm">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base font-medium flex items-center gap-2">
                      <Activity className="h-4 w-4 text-spica" />
                      Statistics
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Executions</span>
                      <span className="text-sm font-mono">{workflow.execution_count}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Created</span>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="text-sm">{formatDate(workflow.created_at)}</span>
                        </TooltipTrigger>
                        <TooltipContent>{workflow.created_at}</TooltipContent>
                      </Tooltip>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Last Updated</span>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="text-sm">{formatDate(workflow.updated_at)}</span>
                        </TooltipTrigger>
                        <TooltipContent>{workflow.updated_at}</TooltipContent>
                      </Tooltip>
                    </div>
                    {workflow.last_executed_at && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Last Executed</span>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="text-sm">{formatDate(workflow.last_executed_at)}</span>
                          </TooltipTrigger>
                          <TooltipContent>{workflow.last_executed_at}</TooltipContent>
                        </Tooltip>
                      </div>
                    )}
                    {workflow.last_error && (
                      <div className="pt-2 border-t border-border/50">
                        <span className="text-sm text-destructive">
                          Error: {workflow.last_error}
                        </span>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Parameters Card */}
                <Card className="bg-card/50 backdrop-blur-sm">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base font-medium flex items-center gap-2">
                      <Settings2 className="h-4 w-4 text-blue-500" />
                      Step Parameters
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {workflow.nodes
                        .filter((n) => n.type !== "trigger")
                        .map((node, index) => (
                          <div
                            key={node.id}
                            className="p-3 rounded bg-muted/30 border border-border/50"
                          >
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-sm font-medium text-muted-foreground">
                                Step {index + 1}
                              </span>
                              <Badge variant="outline" className="text-xs">
                                {node.type}
                              </Badge>
                            </div>
                            <div className="text-sm font-mono text-muted-foreground">
                              {node.data?.label as string || node.type}
                            </div>
                          </div>
                        ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Right column - Graph & History */}
              <div className="space-y-4">
                {/* Graph */}
                <Card className="bg-card/50 backdrop-blur-sm overflow-hidden">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base font-medium">Workflow Graph</CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    <div className="h-[350px] border-t border-border/50">
                      <ReadOnlyGraph nodes={workflow.nodes} edges={workflow.edges} />
                    </div>
                  </CardContent>
                </Card>

                {/* Tabs for History & Activity */}
                <Card className="bg-card/50 backdrop-blur-sm">
                  <Tabs defaultValue="executions" className="w-full">
                    <CardHeader className="pb-0">
                      <TabsList className="grid w-full grid-cols-2">
                        <TabsTrigger value="executions" className="gap-2 text-sm">
                          <History className="h-4 w-4" />
                          Executions
                        </TabsTrigger>
                        <TabsTrigger value="activity" className="gap-2 text-sm">
                          <Clock className="h-4 w-4" />
                          Activity
                        </TabsTrigger>
                      </TabsList>
                    </CardHeader>
                    <CardContent className="pt-4">
                      <TabsContent value="executions" className="mt-0">
                        <ExecutionHistory
                          executions={executions}
                        />
                      </TabsContent>
                      <TabsContent value="activity" className="mt-0">
                        <ActivityTimeline events={activityEvents} />
                      </TabsContent>
                    </CardContent>
                  </Tabs>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </TooltipProvider>
    </AppLayout>
  );
}
