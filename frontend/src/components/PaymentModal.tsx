"use client";

/**
 * Payment Modal Component
 * x402 payment interface for workflow deployment
 *
 * Simplified for hackathon demo - always works, no backend dependency
 * On success, saves the workflow to the backend as an active workflow
 */

import { useState, useEffect, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Loader2,
  CheckCircle2,
  Wallet,
  Zap,
  ExternalLink,
  Copy,
  Check,
  ArrowUpRight,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useWorkflowStore } from "@/stores";
import { apiClient } from "@/api/client";

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflowId: string;
  workflowName?: string;
  onSuccess?: (workflowId: string) => void;
  onError?: (error: string) => void;
}

export default function PaymentModal({
  isOpen,
  onClose,
  workflowId,
  workflowName,
  onSuccess,
  onError,
}: PaymentModalProps) {
  const [isDeploying, setIsDeploying] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [copiedAddress, setCopiedAddress] = useState(false);
  const [activatedWorkflowId, setActivatedWorkflowId] = useState<string | null>(null);

  // Get workflow data from store
  const { nodes, edges, workflowDescription } = useWorkflowStore();

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setIsDeploying(false);
      setIsSuccess(false);
      setCopiedAddress(false);
      setActivatedWorkflowId(null);
    }
  }, [isOpen]);

  // Auto-close on success after delay
  useEffect(() => {
    if (isSuccess && activatedWorkflowId) {
      const timer = setTimeout(() => {
        onSuccess?.(activatedWorkflowId);
        onClose();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isSuccess, activatedWorkflowId, onSuccess, onClose]);

  const handleDeploy = async () => {
    setIsDeploying(true);

    try {
      // First simulate payment processing
      await new Promise((resolve) => setTimeout(resolve, 800));

      // Then activate the workflow on the backend
      const name = workflowName || `Workflow ${workflowId?.slice(0, 8) || "New"}`;

      // Prepare nodes for API (convert to expected format)
      const apiNodes = nodes.map((node) => ({
        id: node.id,
        type: node.type || "unknown",
        position: {
          x: node.position?.x || 0,
          y: node.position?.y || 0,
        },
        data: node.data || {},
      }));

      // Prepare edges for API
      const apiEdges = edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        animated: true,
      }));

      const result = await apiClient.activateWorkflow({
        workflow_name: name,
        workflow_description: workflowDescription || `Automated DeFi workflow: ${name}`,
        nodes: apiNodes,
        edges: apiEdges,
      });

      if (result.success && result.data?.workflow_id) {
        setActivatedWorkflowId(result.data.workflow_id);
        setIsSuccess(true);
      } else {
        // Even if API fails, show success for demo purposes
        console.warn("API activation failed, using demo mode:", result.error);
        setActivatedWorkflowId(workflowId || `wf_demo_${Date.now()}`);
        setIsSuccess(true);
      }
    } catch (error) {
      console.error("Deploy error:", error);
      // Fallback to demo mode on error
      setActivatedWorkflowId(workflowId || `wf_demo_${Date.now()}`);
      setIsSuccess(true);
    } finally {
      setIsDeploying(false);
    }
  };

  const copyAddress = useCallback((address: string) => {
    navigator.clipboard.writeText(address);
    setCopiedAddress(true);
    setTimeout(() => setCopiedAddress(false), 2000);
  }, []);

  // Fixed demo values
  const recipient = "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD78";

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent
        className={cn(
          "max-w-[420px] gap-0 overflow-hidden border-border bg-card p-0",
          "shadow-2xl shadow-black/50"
        )}
      >
        {/* Header */}
        <DialogHeader className="space-y-0 border-b border-border/50 px-6 py-5">
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-3 text-lg font-semibold tracking-tight">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
                <Wallet className="h-4 w-4 text-foreground" />
              </div>
              <span>Deploy Workflow</span>
            </DialogTitle>

            <Badge
              variant="outline"
              className="border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[11px] font-medium uppercase tracking-wider text-amber-400"
            >
              <Zap className="mr-1.5 h-3 w-3" />
              Demo
            </Badge>
          </div>
        </DialogHeader>

        {/* Content */}
        <div className="px-6 py-5">
          {isSuccess ? (
            /* Success State */
            <div className="flex flex-col items-center justify-center py-10">
              <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/20 ring-2 ring-emerald-500/40">
                <CheckCircle2 className="h-8 w-8 text-emerald-500" />
              </div>

              <div className="mt-6 text-center">
                <p className="text-lg font-semibold text-foreground">
                  Deployment Initiated
                </p>
                <p className="mt-1.5 text-sm text-muted-foreground">
                  Deploying to Neo N3 blockchain...
                </p>
              </div>

              <div className="mt-6 h-1 w-32 overflow-hidden rounded-full bg-muted">
                <div className="h-full animate-pulse rounded-full bg-emerald-500" />
              </div>
            </div>
          ) : (
            /* Payment Details */
            <div className="space-y-5">
              {/* Workflow Name */}
              <div className="rounded-lg border border-border/50 bg-muted/30 px-4 py-3">
                <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                  Workflow
                </p>
                <p className="mt-1 truncate font-mono text-sm text-foreground">
                  {workflowName || (workflowId ? `wf_${workflowId.slice(0, 8)}` : "New Workflow")}
                </p>
              </div>

              {/* Payment Amount */}
              <div className="relative overflow-hidden rounded-xl border border-border bg-muted/20 p-6">
                <div className="relative text-center">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                    Deployment Cost
                  </p>
                  <div className="mt-3 flex items-baseline justify-center gap-1">
                    <span className="font-mono text-5xl font-bold tabular-nums tracking-tight text-foreground">
                      0
                    </span>
                    <span className="font-mono text-3xl font-bold tabular-nums text-foreground/60">
                      .02
                    </span>
                    <span className="ml-2 text-lg font-semibold text-muted-foreground">
                      USDC
                    </span>
                  </div>
                </div>
              </div>

              {/* Recipient */}
              <div className="flex items-center justify-between rounded-lg border border-border/50 bg-muted/20 px-4 py-3">
                <div className="min-w-0 flex-1">
                  <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                    Recipient
                  </p>
                  <p className="mt-0.5 font-mono text-sm text-foreground">
                    {`${recipient.slice(0, 6)}...${recipient.slice(-4)}`}
                  </p>
                </div>
                <button
                  onClick={() => copyAddress(recipient)}
                  className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                >
                  {copiedAddress ? (
                    <Check className="h-3.5 w-3.5 text-emerald-500" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                </button>
              </div>

              {/* Network */}
              <div className="flex items-center justify-between rounded-lg border border-border/50 bg-muted/20 px-4 py-3">
                <div>
                  <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                    Network
                  </p>
                  <p className="mt-0.5 font-mono text-sm text-foreground">
                    Base Sepolia
                  </p>
                </div>
                <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Ready
                </div>
              </div>

              {/* x402 Info */}
              <div className="flex items-start gap-3 rounded-lg border border-border/50 bg-muted/20 px-4 py-3">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-muted-foreground">
                    Powered by{" "}
                    <span className="font-semibold text-foreground">
                      x402 Protocol
                    </span>
                    . Demo mode - no real payment required.
                  </p>
                  <a
                    href="https://www.x402.org/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground hover:underline"
                  >
                    Learn more
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {!isSuccess && (
          <>
            <Separator className="opacity-50" />
            <div className="flex gap-3 p-5">
              <Button
                onClick={onClose}
                variant="outline"
                disabled={isDeploying}
                className="flex-1 border-border bg-transparent hover:bg-muted"
              >
                Cancel
              </Button>

              <Button
                onClick={handleDeploy}
                disabled={isDeploying}
                className="flex-1 gap-2 bg-foreground font-semibold text-background hover:bg-foreground/90"
              >
                {isDeploying ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Deploying...
                  </>
                ) : (
                  <>
                    <ArrowUpRight className="h-4 w-4" />
                    Deploy Now
                  </>
                )}
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
