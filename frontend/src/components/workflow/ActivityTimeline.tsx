"use client";

import { cn } from "@/lib/utils";
import {
  Zap,
  Play,
  Pause,
  CheckCircle2,
  XCircle,
  Settings,
  Clock,
} from "lucide-react";

interface ActivityEvent {
  id: string;
  type: "created" | "activated" | "paused" | "executed" | "failed" | "updated";
  timestamp: string;
  message: string;
  details?: string;
}

interface ActivityTimelineProps {
  events: ActivityEvent[];
  className?: string;
}

export function ActivityTimeline({ events, className }: ActivityTimelineProps) {
  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  const getEventIcon = (type: ActivityEvent["type"]) => {
    const iconClass = "h-3.5 w-3.5";
    switch (type) {
      case "created":
        return <Zap className={cn(iconClass, "text-spica")} />;
      case "activated":
        return <Play className={cn(iconClass, "text-green-500")} />;
      case "paused":
        return <Pause className={cn(iconClass, "text-amber-500")} />;
      case "executed":
        return <CheckCircle2 className={cn(iconClass, "text-spica")} />;
      case "failed":
        return <XCircle className={cn(iconClass, "text-destructive")} />;
      case "updated":
        return <Settings className={cn(iconClass, "text-blue-500")} />;
      default:
        return <Clock className={iconClass} />;
    }
  };

  const getEventColor = (type: ActivityEvent["type"]) => {
    switch (type) {
      case "created":
        return "bg-spica";
      case "activated":
        return "bg-green-500";
      case "paused":
        return "bg-amber-500";
      case "executed":
        return "bg-spica";
      case "failed":
        return "bg-destructive";
      case "updated":
        return "bg-blue-500";
      default:
        return "bg-muted-foreground";
    }
  };

  if (events.length === 0) {
    return (
      <div className={cn("text-center py-8", className)}>
        <Clock className="h-8 w-8 mx-auto text-muted-foreground/50 mb-2" />
        <p className="text-sm text-muted-foreground">No activity yet</p>
      </div>
    );
  }

  return (
    <div className={cn("relative", className)}>
      {/* Timeline line */}
      <div className="absolute left-[11px] top-2 bottom-2 w-px bg-border" />

      <div className="space-y-4">
        {events.map((event, index) => (
          <div key={event.id} className="relative flex gap-3 items-start">
            {/* Timeline dot */}
            <div
              className={cn(
                "relative z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full",
                "bg-card border-2 border-border"
              )}
            >
              {getEventIcon(event.type)}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 pt-0.5">
              <div className="flex items-center gap-2 text-xs">
                <span className="font-medium">{event.message}</span>
                <span className="text-muted-foreground/70">
                  {index === 0
                    ? formatTime(event.timestamp)
                    : `${formatDate(event.timestamp)} ${formatTime(event.timestamp)}`}
                </span>
              </div>
              {event.details && (
                <p className="text-xs text-muted-foreground mt-0.5">{event.details}</p>
              )}
            </div>

            {/* Connecting dot indicator */}
            <div
              className={cn(
                "absolute left-[9px] top-[10px] h-1.5 w-1.5 rounded-full",
                getEventColor(event.type)
              )}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
