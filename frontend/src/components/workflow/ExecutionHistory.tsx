"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// Time constants
const MS_PER_MINUTE = 60000;
const MS_PER_HOUR = 3600000;
const MS_PER_DAY = 86400000;

// Neo Explorer URLs - configurable for mainnet/testnet
const NEO_EXPLORER_URLS = {
  testnet: "https://testnet.neotube.io/transaction",
  mainnet: "https://neotube.io/transaction",
} as const;

// Use testnet by default, can be configured via env or prop
const NEO_EXPLORER_URL =
  process.env.NEXT_PUBLIC_NEO_NETWORK === "mainnet"
    ? NEO_EXPLORER_URLS.mainnet
    : NEO_EXPLORER_URLS.testnet;

interface ExecutionRecord {
  id: string;
  workflow_id: string;
  triggered_at: string;
  executed_at?: string;
  status: "pending" | "running" | "success" | "failed";
  transaction_hash?: string;
  result?: Record<string, unknown>;
  error?: string;
  duration_ms?: number;
}

interface ExecutionHistoryProps {
  executions: ExecutionRecord[];
  className?: string;
}

export function ExecutionHistory({ executions, className }: ExecutionHistoryProps) {
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
      success: "border-spica/50 text-spica",
      failed: "border-destructive/50 text-destructive",
      running: "border-blue-500/50 text-blue-500",
      pending: "border-amber-500/50 text-amber-500",
    };
    return (
      <Badge variant="outline" className={cn("text-[10px]", variants[status])}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  if (executions.length === 0) {
    return (
      <div className={cn("text-center py-8", className)}>
        <Clock className="h-8 w-8 mx-auto text-muted-foreground/50 mb-2" />
        <p className="text-sm text-muted-foreground">No executions yet</p>
        <p className="text-xs text-muted-foreground/70 mt-1">
          Executions will appear here when the workflow triggers
        </p>
      </div>
    );
  }

  return (
    <TooltipProvider delayDuration={0}>
      <div className={cn("space-y-2", className)}>
        {executions.map((execution) => (
          <div
            key={execution.id}
            className={cn(
              "group relative flex items-center gap-3 p-3 rounded-lg",
              "bg-card/30 border border-border/50 hover:border-border transition-colors"
            )}
          >
            {/* Status indicator line */}
            <div
              className={cn(
                "absolute left-0 top-0 h-full w-0.5 rounded-l-lg",
                execution.status === "success" && "bg-spica",
                execution.status === "failed" && "bg-destructive",
                execution.status === "running" && "bg-blue-500",
                execution.status === "pending" && "bg-amber-500"
              )}
            />

            {/* Status icon */}
            <div className="shrink-0">{getStatusIcon(execution.status)}</div>

            {/* Main content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                {getStatusBadge(execution.status)}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeTime(execution.triggered_at)}
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>{formatDate(execution.triggered_at)}</TooltipContent>
                </Tooltip>
              </div>

              {execution.error && (
                <p className="text-xs text-destructive mt-1 truncate">{execution.error}</p>
              )}

              {execution.transaction_hash && (
                <a
                  href={`${NEO_EXPLORER_URL}/${execution.transaction_hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-spica hover:underline mt-1"
                >
                  <span className="font-mono truncate max-w-[120px]">
                    {execution.transaction_hash.slice(0, 8)}...{execution.transaction_hash.slice(-6)}
                  </span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>

            {/* Duration */}
            <div className="shrink-0 text-right">
              <span className="text-xs text-muted-foreground font-mono">
                {formatDuration(execution.duration_ms)}
              </span>
            </div>

            {/* Chevron for expandability */}
            <ChevronRight className="h-4 w-4 text-muted-foreground/50 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        ))}
      </div>
    </TooltipProvider>
  );
}
