"use client";

/**
 * Payment Modal Component
 * x402 payment interface for workflow deployment
 *
 * Design: Scientific instrument aesthetic with precision financial display
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
import { apiClient } from "@/api/client";
import { usePayment } from "@/hooks/usePayment";
import type { PaymentModalProps, PaymentRequest } from "@/types/payment";
import {
  Loader2,
  CheckCircle2,
  XCircle,
  Wallet,
  Zap,
  ExternalLink,
  Copy,
  Check,
  ArrowUpRight,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function PaymentModal({
  isOpen,
  onClose,
  workflowId,
  workflowName,
  onSuccess,
  onError,
}: PaymentModalProps) {
  const [paymentInfo, setPaymentInfo] = useState<PaymentRequest | null>(null);
  const [isLoadingPaymentInfo, setIsLoadingPaymentInfo] = useState(false);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [copiedAddress, setCopiedAddress] = useState(false);
  const { state, error, submitPayment, reset } = usePayment();

  // Check demo mode and fetch payment info when modal opens
  useEffect(() => {
    if (isOpen && !paymentInfo && workflowId) {
      checkDemoModeAndFetchPaymentInfo();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, workflowId]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      reset();
      setPaymentInfo(null);
      setIsDemoMode(false);
      setIsDeploying(false);
      setCopiedAddress(false);
    }
  }, [isOpen, reset]);

  // Auto-close on success after delay
  useEffect(() => {
    if (state === "success") {
      const timer = setTimeout(() => {
        onSuccess?.(workflowId);
        onClose();
      }, 2500);
      return () => clearTimeout(timer);
    }
  }, [state, workflowId, onSuccess, onClose]);

  // Notify parent of errors
  useEffect(() => {
    if (state === "error" && error) {
      onError?.(error);
    }
  }, [state, error, onError]);

  const checkDemoModeAndFetchPaymentInfo = async () => {
    if (!workflowId) {
      onError?.("No workflow ID provided");
      return;
    }

    setIsLoadingPaymentInfo(true);
    try {
      const demoModeStatus = await apiClient.getDemoMode();
      setIsDemoMode(demoModeStatus.demo_mode);

      const response = await apiClient.deployWorkflow(workflowId);

      if (response.status === 402 && response.headers) {
        const headerValue = response.headers.get("X-PAYMENT-REQUEST");
        if (headerValue) {
          const decoded = atob(headerValue);
          const parsed = JSON.parse(decoded) as PaymentRequest;
          setPaymentInfo(parsed);
        }
      } else if (response.success) {
        onSuccess?.(workflowId);
        onClose();
      } else {
        onError?.(response.error?.message || "Failed to get payment info");
      }
    } catch (err) {
      console.error("Failed to fetch payment info:", err);
      onError?.("Failed to load payment information");
    } finally {
      setIsLoadingPaymentInfo(false);
    }
  };

  const handleDemoModeDeploy = async () => {
    if (!workflowId) return;

    setIsDeploying(true);
    try {
      const demoPaymentHeader = btoa(
        JSON.stringify({
          x402Version: 1,
          demo: true,
          timestamp: new Date().toISOString(),
        })
      );

      const response = await apiClient.deployWithPayment(
        workflowId,
        demoPaymentHeader
      );
      if (response.success) {
        onSuccess?.(workflowId);
        onClose();
      } else {
        onError?.(response.error?.message || "Failed to deploy workflow");
      }
    } catch (err) {
      console.error("Demo mode deployment error:", err);
      onError?.("Failed to deploy workflow");
    } finally {
      setIsDeploying(false);
    }
  };

  const handlePayWithWallet = async () => {
    if (!paymentInfo) return;
    const result = await submitPayment(workflowId, paymentInfo);
    if (result?.success) {
      console.log("Payment successful:", result);
    }
  };

  const copyAddress = useCallback((address: string) => {
    navigator.clipboard.writeText(address);
    setCopiedAddress(true);
    setTimeout(() => setCopiedAddress(false), 2000);
  }, []);

  // Get payment details from first accept option
  const paymentAccept = paymentInfo?.accepts?.[0];
  const amount = paymentAccept?.max_amount_required || "0";
  const currency = paymentAccept?.extra?.currency || "USDC";
  const recipient = paymentAccept?.pay_to || "";
  const network = paymentAccept?.network || "base-sepolia";

  // Format amount (assuming USDC with 6 decimals)
  const formattedAmount = (parseInt(amount) / 1_000_000).toFixed(2);
  const [amountWhole, amountDecimal] = formattedAmount.split(".");

  // Truncate address
  const truncateAddress = (addr: string) => {
    if (!addr || addr.length < 12) return addr;
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent
        className={cn(
          "max-w-[420px] gap-0 overflow-hidden border-border/50 bg-card p-0",
          "shadow-2xl shadow-black/50"
        )}
      >
        {/* Top accent line */}
        <div className="h-[2px] w-full bg-gradient-to-r from-transparent via-spica to-transparent" />

        {/* Header */}
        <DialogHeader className="space-y-0 border-b border-border/50 px-6 py-5">
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-3 text-lg font-semibold tracking-tight">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-spica/10 ring-1 ring-spica/20">
                <Wallet className="h-4 w-4 text-spica" />
              </div>
              <span>Deploy Workflow</span>
            </DialogTitle>

            {isDemoMode && (
              <Badge
                variant="outline"
                className="border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-[11px] font-medium uppercase tracking-wider text-amber-400"
              >
                <Zap className="mr-1.5 h-3 w-3" />
                Demo
              </Badge>
            )}
          </div>
        </DialogHeader>

        {/* Content */}
        <div className="px-6 py-5">
          {/* Loading State */}
          {isLoadingPaymentInfo && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="relative">
                <div className="absolute inset-0 animate-ping rounded-full bg-spica/20" />
                <div className="relative flex h-14 w-14 items-center justify-center rounded-full border border-border bg-card">
                  <Loader2 className="h-6 w-6 animate-spin text-spica" />
                </div>
              </div>
              <p className="mt-5 text-sm text-muted-foreground">
                Preparing deployment...
              </p>
            </div>
          )}

          {/* Payment Details */}
          {!isLoadingPaymentInfo && paymentInfo && state !== "success" && (
            <div className="space-y-5">
              {/* Workflow Name */}
              <div className="rounded-lg border border-border/50 bg-muted/30 px-4 py-3">
                <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                  Workflow
                </p>
                <p className="mt-1 truncate font-mono text-sm text-foreground">
                  {workflowName || `wf_${workflowId.slice(0, 8)}`}
                </p>
              </div>

              {/* Payment Amount - Hero Section */}
              <div className="relative overflow-hidden rounded-xl border border-spica/20 bg-gradient-to-b from-spica/[0.08] to-transparent p-6">
                {/* Measurement grid lines */}
                <div className="pointer-events-none absolute inset-0 opacity-[0.03]">
                  <div
                    className="h-full w-full"
                    style={{
                      backgroundImage: `
                      linear-gradient(to right, currentColor 1px, transparent 1px),
                      linear-gradient(to bottom, currentColor 1px, transparent 1px)
                    `,
                      backgroundSize: "24px 24px",
                    }}
                  />
                </div>

                {/* Subtle glow */}
                <div className="absolute -top-12 left-1/2 h-24 w-48 -translate-x-1/2 rounded-full bg-spica/20 blur-3xl" />

                <div className="relative text-center">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-spica/70">
                    Deployment Cost
                  </p>
                  <div className="mt-3 flex items-baseline justify-center gap-1">
                    <span className="font-mono text-5xl font-bold tabular-nums tracking-tight text-foreground">
                      {amountWhole}
                    </span>
                    <span className="font-mono text-3xl font-bold tabular-nums text-foreground/60">
                      .{amountDecimal}
                    </span>
                    <span className="ml-2 text-lg font-semibold text-spica">
                      {currency}
                    </span>
                  </div>
                </div>
              </div>

              {/* Payment Details Grid */}
              <div className="space-y-3">
                {/* Recipient */}
                <div className="flex items-center justify-between rounded-lg border border-border/50 bg-muted/20 px-4 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                      Recipient
                    </p>
                    <p className="mt-0.5 font-mono text-sm text-foreground">
                      {truncateAddress(recipient)}
                    </p>
                  </div>
                  <button
                    onClick={() => copyAddress(recipient)}
                    className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                  >
                    {copiedAddress ? (
                      <Check className="h-3.5 w-3.5 text-spica" />
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
                    <p className="mt-0.5 font-mono text-sm capitalize text-foreground">
                      {network.replace("-", " ")}
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-spica" />
                    Connected
                  </div>
                </div>
              </div>

              {/* Error Display */}
              {state === "error" && error && (
                <div className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3">
                  <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-destructive">
                      Payment Failed
                    </p>
                    <p className="mt-0.5 text-xs text-destructive/80">
                      {error}
                    </p>
                  </div>
                </div>
              )}

              {/* x402 Protocol Info (Production Only) */}
              {!isDemoMode && (
                <div className="flex items-start gap-3 rounded-lg border border-border/50 bg-muted/20 px-4 py-3">
                  <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-spica/70" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-muted-foreground">
                      Secured by{" "}
                      <span className="font-semibold text-foreground">
                        x402 Protocol
                      </span>
                      . Connect an EVM wallet to sign the payment.
                    </p>
                    <a
                      href="https://www.x402.org/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-spica hover:underline"
                    >
                      Learn more
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Success State */}
          {state === "success" && (
            <div className="flex flex-col items-center justify-center py-10">
              <div className="relative">
                {/* Animated rings */}
                <div className="absolute inset-0 animate-ping rounded-full bg-spica/30" />
                <div
                  className="absolute inset-0 animate-ping rounded-full bg-spica/20"
                  style={{ animationDelay: "150ms" }}
                />
                {/* Icon */}
                <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-spica/20 ring-2 ring-spica/40">
                  <CheckCircle2 className="h-8 w-8 text-spica" />
                </div>
              </div>

              <div className="mt-6 text-center">
                <p className="text-lg font-semibold text-foreground">
                  Deployment Initiated
                </p>
                <p className="mt-1.5 text-sm text-muted-foreground">
                  Deploying to Neo N3 blockchain...
                </p>
              </div>

              {/* Progress indicator */}
              <div className="mt-6 h-1 w-32 overflow-hidden rounded-full bg-muted">
                <div className="h-full animate-pulse rounded-full bg-spica" />
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        {!isLoadingPaymentInfo && paymentInfo && state !== "success" && (
          <>
            <Separator className="opacity-50" />
            <div className="flex gap-3 p-5">
              <Button
                onClick={onClose}
                variant="outline"
                disabled={state === "loading" || isDeploying}
                className="flex-1 border-border/50 bg-transparent hover:bg-muted"
              >
                Cancel
              </Button>

              {isDemoMode ? (
                <Button
                  onClick={handleDemoModeDeploy}
                  disabled={isDeploying}
                  className="flex-1 gap-2 bg-spica font-semibold text-spica-900 hover:bg-spica/90"
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
              ) : (
                <Button
                  onClick={handlePayWithWallet}
                  disabled={state === "loading"}
                  className="flex-1 gap-2 bg-spica font-semibold text-spica-900 hover:bg-spica/90"
                >
                  {state === "loading" ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Wallet className="h-4 w-4" />
                      Pay & Deploy
                    </>
                  )}
                </Button>
              )}
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
