"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { AppLayout, Sidebar, CanvasHeader } from "@/components/layout";
import { useAppInitialization } from "@/hooks";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Fragment } from "react";
import {
  History,
  Plus,
  RefreshCw,
  Filter,
  X,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Copy,
  AlertCircle,
  Search,
  Calendar,
} from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/api/client";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

// Time constants
const MS_PER_MINUTE = 60000;
const MS_PER_HOUR = 3600000;
const MS_PER_DAY = 86400000;

// Neo Explorer URLs
const NEO_EXPLORER_URL =
  process.env.NEXT_PUBLIC_NEO_NETWORK === "mainnet"
    ? "https://neotube.io/transaction"
    : "https://testnet.neotube.io/transaction";

interface WorkflowSummary {
  workflow_id: string;
  workflow_name: string;
}

interface ExecutionRecord {
  id: string;
  workflow_id: string;
  workflow_name: string;
  triggered_at: string;
  executed_at?: string;
  status: "pending" | "running" | "success" | "failed" | "completed";
  trigger_type: string;
  action_summary: string;
  transaction_hash?: string;
  result?: Record<string, unknown>;
  error?: string;
  duration_ms?: number;
}

export default function HistoryPage() {
  useAppInitialization();

  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [dateFilter, setDateFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Expanded rows
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Fetch workflows for reference
      const workflowResult = await apiClient.listWorkflows();
      if (workflowResult.success && workflowResult.data) {
        // Check for backend success and workflows array
        if (workflowResult.data.success !== false && Array.isArray(workflowResult.data.workflows)) {
          const workflowSummaries = workflowResult.data.workflows.map((w) => ({
            workflow_id: w.workflow_id,
            workflow_name: w.workflow_name,
          }));
          setWorkflows(workflowSummaries);
        }
      }

      // Fetch real executions from API
      const executionsResult = await apiClient.listExecutions({
        status: statusFilter !== "all" ? statusFilter : undefined,
        limit: 100,
      });

      if (executionsResult.success && executionsResult.data &&
          Array.isArray(executionsResult.data.executions)) {
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
            workflow_name: e.workflow_name,
            triggered_at: e.started_at,
            executed_at: e.completed_at || undefined,
            status,
            trigger_type: e.trigger_type,
            action_summary: e.action_summary,
            transaction_hash: e.tx_hash || undefined,
            error: e.error || undefined,
            duration_ms,
          };
        });
        setExecutions(mappedExecutions);
      } else if (!executionsResult.success) {
        // If API returns empty or error, show empty state (not error)
        setExecutions([]);
      }
    } catch (err) {
      console.error("Failed to load execution history:", err);
      setError("Failed to load execution history");
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Filter executions
  const filteredExecutions = useMemo(() => {
    const now = new Date();
    return executions.filter((exec) => {
      // Date filter
      if (dateFilter !== "all") {
        const execDate = new Date(exec.triggered_at);
        const diffMs = now.getTime() - execDate.getTime();

        switch (dateFilter) {
          case "today":
            if (diffMs > MS_PER_DAY) return false;
            break;
          case "week":
            if (diffMs > MS_PER_DAY * 7) return false;
            break;
          case "month":
            if (diffMs > MS_PER_DAY * 30) return false;
            break;
        }
      }

      if (statusFilter !== "all" && exec.status !== statusFilter) return false;
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        if (
          !exec.workflow_name.toLowerCase().includes(query) &&
          !exec.action_summary.toLowerCase().includes(query) &&
          !(exec.transaction_hash?.toLowerCase().includes(query))
        ) {
          return false;
        }
      }
      return true;
    });
  }, [executions, dateFilter, statusFilter, searchQuery]);

  const toggleRowExpanded = (id: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard");
  };

  const clearFilters = () => {
    setDateFilter("all");
    setStatusFilter("all");
    setSearchQuery("");
  };

  const hasActiveFilters = dateFilter !== "all" || statusFilter !== "all" || searchQuery !== "";

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatRelativeTime = (dateStr: string) => {
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

  const formatDuration = (ms?: number) => {
    if (!ms) return "-";
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const getStatusIcon = (status: ExecutionRecord["status"]) => {
    switch (status) {
      case "success":
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-spica" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-destructive" />;
      case "running":
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case "pending":
        return <Clock className="h-4 w-4 text-amber-500" />;
    }
  };

  const getStatusBadge = (status: ExecutionRecord["status"]) => {
    const variants: Record<ExecutionRecord["status"], string> = {
      success: "border-spica/50 text-spica bg-spica/10",
      completed: "border-spica/50 text-spica bg-spica/10",
      failed: "border-destructive/50 text-destructive bg-destructive/10",
      running: "border-blue-500/50 text-blue-500 bg-blue-500/10",
      pending: "border-amber-500/50 text-amber-500 bg-amber-500/10",
    };
    return (
      <Badge variant="outline" className={cn("text-xs font-mono", variants[status])}>
        {status.toUpperCase()}
      </Badge>
    );
  };

  // Loading skeleton - zinc color palette for consistency
  if (isLoading) {
    return (
      <AppLayout sidebar={<Sidebar />} header={<CanvasHeader />} canvasVariant="subtle">
        <div className="h-full w-full overflow-auto p-6">
          <div className="flex items-center justify-between mb-6">
            <Skeleton className="h-8 w-48 bg-zinc-800/80" />
            <Skeleton className="h-8 w-24 bg-zinc-800/80" />
          </div>
          <div className="flex gap-4 mb-6">
            <Skeleton className="h-10 w-48 bg-zinc-800/60" />
            <Skeleton className="h-10 w-32 bg-zinc-800/60" />
            <Skeleton className="h-10 w-32 bg-zinc-800/60" />
          </div>
          <Card className="bg-[#0a0a0c] border-zinc-800/80">
            <CardContent className="p-0">
              <div className="space-y-0">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-4 p-4 border-b border-zinc-800/50">
                    <Skeleton className="h-4 w-4 bg-zinc-800/60" />
                    <Skeleton className="h-4 w-32 bg-zinc-800/60" />
                    <Skeleton className="h-4 w-40 bg-zinc-800/60" />
                    <Skeleton className="h-4 w-24 bg-zinc-800/60" />
                    <Skeleton className="h-6 w-20 bg-zinc-800/80" />
                    <Skeleton className="h-4 w-32 bg-zinc-800/60" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </AppLayout>
    );
  }

  // Error state
  if (error) {
    return (
      <AppLayout sidebar={<Sidebar />} header={<CanvasHeader />} canvasVariant="subtle">
        <div className="flex h-full w-full items-center justify-center p-8">
          <div className="flex flex-col items-center gap-6 text-center max-w-md">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
              <AlertCircle className="h-8 w-8 text-destructive" />
            </div>
            <div>
              <p className="font-medium">Failed to load execution history</p>
              <p className="text-sm text-muted-foreground mt-1">{error}</p>
            </div>
            <Button onClick={fetchData}>Try Again</Button>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout sidebar={<Sidebar />} header={<CanvasHeader />} canvasVariant="subtle">
      <TooltipProvider delayDuration={0}>
        <div className="h-full w-full overflow-auto p-6">
          {/* Page Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-semibold">Execution History</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Audit trail of all workflow executions
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchData}
              disabled={isLoading}
            >
              <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
              Refresh
            </Button>
          </div>

          {/* Filters */}
          <Card className="mb-6 bg-card/50 backdrop-blur-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Filter className="h-4 w-4" />
                Filters
                {hasActiveFilters && (
                  <Badge variant="secondary" className="text-xs">
                    {filteredExecutions.length} of {executions.length}
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-4">
                {/* Search */}
                <div className="relative flex-1 min-w-[200px]">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" aria-hidden="true" />
                  <Input
                    placeholder="Search by name, action, or tx hash..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 bg-background/50"
                    aria-label="Search executions by name, action, or transaction hash"
                  />
                </div>

                {/* Date filter */}
                <Select value={dateFilter} onValueChange={setDateFilter}>
                  <SelectTrigger className="w-[140px] bg-background/50">
                    <SelectValue placeholder="All Time" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Time</SelectItem>
                    <SelectItem value="today">Today</SelectItem>
                    <SelectItem value="week">Last 7 Days</SelectItem>
                    <SelectItem value="month">Last 30 Days</SelectItem>
                  </SelectContent>
                </Select>

                {/* Status filter */}
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[140px] bg-background/50">
                    <SelectValue placeholder="All Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="success">Success</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="running">Running</SelectItem>
                  </SelectContent>
                </Select>

                {/* Clear filters */}
                {hasActiveFilters && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearFilters}
                    className="text-muted-foreground"
                  >
                    <X className="h-4 w-4 mr-1" />
                    Clear
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Table */}
          {filteredExecutions.length === 0 ? (
            <div className="flex h-64 items-center justify-center">
              <div className="flex flex-col items-center gap-6 text-center max-w-md">
                <div className="relative">
                  <div className="absolute inset-0 bg-spica/20 blur-2xl rounded-full" />
                  <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-card border border-border">
                    <History className="h-10 w-10 text-muted-foreground" />
                  </div>
                </div>

                <div className="space-y-2">
                  <h2 className="text-xl font-semibold">
                    {hasActiveFilters ? "No Matching Executions" : "No Execution History"}
                  </h2>
                  <p className="text-muted-foreground text-sm">
                    {hasActiveFilters
                      ? "Try adjusting your filters to see more results."
                      : "Your workflow execution history will appear here once you deploy and run your first workflow."}
                  </p>
                </div>

                {hasActiveFilters ? (
                  <Button variant="outline" onClick={clearFilters}>
                    Clear Filters
                  </Button>
                ) : (
                  <Link href="/">
                    <Button variant="cyber" className="gap-2">
                      <Plus className="h-4 w-4" />
                      Create Workflow
                    </Button>
                  </Link>
                )}
              </div>
            </div>
          ) : (
            <Card className="bg-card/50 backdrop-blur-sm">
              <Table className="w-full">
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-border/50">
                    <TableHead className="w-10 shrink-0"></TableHead>
                    <TableHead className="w-24 shrink-0">Timestamp</TableHead>
                    <TableHead className="min-w-[140px]">Workflow</TableHead>
                    <TableHead className="hidden md:table-cell">Action</TableHead>
                    <TableHead className="w-24 shrink-0">Status</TableHead>
                    <TableHead className="hidden lg:table-cell">Transaction</TableHead>
                    <TableHead className="w-16 shrink-0 text-right">Duration</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredExecutions.map((execution) => {
                    const isExpanded = expandedRows.has(execution.id);
                    return (
                      <Fragment key={execution.id}>
                        <TableRow
                          className={cn(
                            "group cursor-pointer border-border/50",
                            isExpanded && "bg-muted/30"
                          )}
                          onClick={() => toggleRowExpanded(execution.id)}
                        >
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6"
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleRowExpanded(execution.id);
                              }}
                            >
                              {isExpanded ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </Button>
                          </TableCell>
                          <TableCell className="py-3">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <span className="text-sm text-muted-foreground whitespace-nowrap">
                                  {formatRelativeTime(execution.triggered_at)}
                                </span>
                              </TooltipTrigger>
                              <TooltipContent>
                                {formatDate(execution.triggered_at)}
                              </TooltipContent>
                            </Tooltip>
                          </TableCell>
                          <TableCell className="py-3" onClick={(e) => e.stopPropagation()}>
                            <Link
                              href={`/workflows/${execution.workflow_id}`}
                              className="text-sm font-medium hover:text-spica transition-colors line-clamp-1"
                            >
                              {execution.workflow_name}
                            </Link>
                          </TableCell>
                          <TableCell className="hidden md:table-cell py-3">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <Badge variant="outline" className="text-[10px] font-mono shrink-0">
                                {execution.trigger_type}
                              </Badge>
                              <span className="truncate max-w-[150px]">{execution.action_summary}</span>
                            </div>
                          </TableCell>
                          <TableCell className="py-3">
                            <div className="flex items-center gap-1.5">
                              {getStatusIcon(execution.status)}
                              {getStatusBadge(execution.status)}
                            </div>
                          </TableCell>
                          <TableCell className="hidden lg:table-cell py-3" onClick={(e) => e.stopPropagation()}>
                            {execution.transaction_hash ? (
                              <div className="flex items-center gap-1">
                                <code className="text-xs font-mono text-muted-foreground truncate max-w-[80px]">
                                  {execution.transaction_hash.slice(0, 8)}...
                                </code>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      className="h-6 w-6"
                                      onClick={() => copyToClipboard(execution.transaction_hash!)}
                                    >
                                      <Copy className="h-3 w-3" />
                                    </Button>
                                  </TooltipTrigger>
                                  <TooltipContent>Copy hash</TooltipContent>
                                </Tooltip>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <a
                                      href={`${NEO_EXPLORER_URL}/${execution.transaction_hash}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-spica hover:text-spica/80"
                                    >
                                      <ExternalLink className="h-3 w-3" />
                                    </a>
                                  </TooltipTrigger>
                                  <TooltipContent>View on Neo Explorer</TooltipContent>
                                </Tooltip>
                              </div>
                            ) : (
                              <span className="text-xs text-muted-foreground/50">-</span>
                            )}
                          </TableCell>
                          <TableCell className="text-right py-3">
                            <span className="text-xs font-mono text-muted-foreground whitespace-nowrap">
                              {formatDuration(execution.duration_ms)}
                            </span>
                          </TableCell>
                        </TableRow>
                        {isExpanded && (
                          <TableRow className="bg-muted/20 hover:bg-muted/20 border-border/50">
                            <TableCell colSpan={7} className="p-4">
                              <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
                                <div>
                                  <span className="text-xs text-muted-foreground">Triggered At</span>
                                  <p className="text-sm font-mono">
                                    {formatDate(execution.triggered_at)}
                                  </p>
                                </div>
                                {execution.executed_at && (
                                  <div>
                                    <span className="text-xs text-muted-foreground">
                                      Executed At
                                    </span>
                                    <p className="text-sm font-mono">
                                      {formatDate(execution.executed_at)}
                                    </p>
                                  </div>
                                )}
                                <div>
                                  <span className="text-xs text-muted-foreground">Duration</span>
                                  <p className="text-sm font-mono">
                                    {formatDuration(execution.duration_ms)}
                                  </p>
                                </div>
                                <div>
                                  <span className="text-xs text-muted-foreground">
                                    Execution ID
                                  </span>
                                  <p className="text-sm font-mono truncate">{execution.id}</p>
                                </div>
                                {/* Action details - always visible in expanded view */}
                                <div className="col-span-2">
                                  <span className="text-xs text-muted-foreground">Action</span>
                                  <div className="flex items-center gap-2 mt-1">
                                    <Badge variant="outline" className="text-[10px] font-mono">
                                      {execution.trigger_type}
                                    </Badge>
                                    <span className="text-sm">{execution.action_summary}</span>
                                  </div>
                                </div>
                                {execution.error && (
                                  <div className="col-span-2 lg:col-span-4">
                                    <span className="text-xs text-destructive">Error</span>
                                    <p className="text-sm text-destructive bg-destructive/10 p-2 rounded mt-1">
                                      {execution.error}
                                    </p>
                                  </div>
                                )}
                                {execution.transaction_hash && (
                                  <div className="col-span-2 lg:col-span-4">
                                    <span className="text-xs text-muted-foreground">
                                      Transaction Hash
                                    </span>
                                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                                      <code className="text-sm font-mono bg-muted/30 px-2 py-1 rounded truncate max-w-full">
                                        {execution.transaction_hash}
                                      </code>
                                      <div className="flex items-center gap-1">
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={() => copyToClipboard(execution.transaction_hash!)}
                                        >
                                          <Copy className="h-4 w-4" />
                                        </Button>
                                        <a
                                          href={`${NEO_EXPLORER_URL}/${execution.transaction_hash}`}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                        >
                                          <Button variant="outline" size="sm" className="gap-1">
                                            <ExternalLink className="h-4 w-4" />
                                            Explorer
                                          </Button>
                                        </a>
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </TableCell>
                          </TableRow>
                        )}
                      </Fragment>
                    );
                  })}
                </TableBody>
              </Table>

              {/* Table footer with count */}
              <div className="border-t border-border/50 px-4 py-3 text-xs text-muted-foreground">
                Showing {filteredExecutions.length} of {executions.length} executions
              </div>
            </Card>
          )}
        </div>
      </TooltipProvider>
    </AppLayout>
  );
}
