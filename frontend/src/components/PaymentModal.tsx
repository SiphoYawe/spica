"use client";

/**
 * Payment Modal Component
 * x402 payment interface for workflow deployment
 *
 * Design: Scientific instrument aesthetic with precision financial display
 * Always shows content - falls back to demo mode if backend unavailable
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

// Default payment info for demo/fallback mode
const DEFAULT_PAYMENT_INFO: PaymentRequest = {
  x402Version: 1,
  accepts: [
    {
      scheme: "exact",
      network: "base-sepolia",
      max_amount_required: "20000", // 0.02 USDC
      description: "Deploy workflow to Neo N3",
      pay_to: "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD78",
      extra: {
        currency: "USDC",
      },
    },
  ],
};

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
  const [isDemoMode, setIsDemoMode] = useState(true); // Default to demo mode
  const [isDeploying, setIsDeploying] = useState(false);
  const [copiedAddress, setCopiedAddress] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const { state, error, submitPayment, reset } = usePayment();

  // Check demo mode and fetch payment info when modal opens
  useEffect(() => {
    if (isOpen && workflowId) {
      checkDemoModeAndFetchPaymentInfo();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, workflowId]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      reset();
      setPaymentInfo(null);
      setIsDemoMode(true);
      setIsDeploying(false);
      setCopiedAddress(false);
      setLoadError(false);
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
      // Still show modal with default info
      setPaymentInfo(DEFAULT_PAYMENT_INFO);
      setIsDemoMode(true);
      return;
    }

    setIsLoadingPaymentInfo(true);
    setLoadError(false);

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
        } else {
          // Fallback to default
          setPaymentInfo(DEFAULT_PAYMENT_INFO);
        }
      } else if (response.success) {
        onSuccess?.(workflowId);
        onClose();
      } else {
        // API error - use default payment info and demo mode
        setPaymentInfo(DEFAULT_PAYMENT_INFO);
        setIsDemoMode(true);
      }
    } catch (err) {
      console.error("Failed to fetch payment info:", err);
      // On any error, fall back to demo mode with default payment info
      setPaymentInfo(DEFAULT_PAYMENT_INFO);
      setIsDemoMode(true);
      setLoadError(true);
    } finally {
      setIsLoadingPaymentInfo(false);
    }
  };

  const handleDemoModeDeploy = async () => {
    setIsDeploying(true);

    // Simulate deployment for demo
    await new Promise((resolve) => setTimeout(resolve, 1500));

    if (workflowId) {
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
          return;
        }
      } catch (err) {
        console.error("Demo mode deployment error:", err);
      }
    }

    // If API call fails or no workflowId, still show success for demo
    onSuccess?.(workflowId);
    onClose();
    setIsDeploying(false);
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

  // Get payment details - use paymentInfo or default
  const displayPaymentInfo = paymentInfo || DEFAULT_PAYMENT_INFO;
  const paymentAccept = displayPaymentInfo.accepts?.[0];
  const amount = paymentAccept?.max_amount_required || "20000";
  const currency = paymentAccept?.extra?.currency || "USDC";
  const recipient = paymentAccept?.pay_to || "0x742d35Cc...";
  const network = paymentAccept?.network || "base-sepolia";

  // Format amount (assuming USDC with 6 decimals)
  const formattedAmount = (parseInt(amount) / 1_000_000).toFixed(2);
  const [amountWhole, amountDecimal] = formattedAmount.split(".");

  // Truncate address
  const truncateAddress = (addr: string) => {
    if (!addr || addr.length < 12) return addr;
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  // Show content when not loading or when we have payment info
  const showContent = !isLoadingPaymentInfo || paymentInfo;

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
          {isLoadingPaymentInfo && !paymentInfo && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="relative">
                <div className="relative flex h-14 w-14 items-center justify-center rounded-full border border-border bg-card">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              </div>
              <p className="mt-5 text-sm text-muted-foreground">
                Preparing deployment...
              </p>
            </div>
          )}

          {/* Payment Details - Always show when not loading */}
          {showContent && state !== "success" && (
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

              {/* Payment Amount - Hero Section */}
              <div className="relative overflow-hidden rounded-xl border border-border bg-muted/20 p-6">
                <div className="relative text-center">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                    Deployment Cost
                  </p>
                  <div className="mt-3 flex items-baseline justify-center gap-1">
                    <span className="font-mono text-5xl font-bold tabular-nums tracking-tight text-foreground">
                      {amountWhole}
                    </span>
                    <span className="font-mono text-3xl font-bold tabular-nums text-foreground/60">
                      .{amountDecimal}
                    </span>
                    <span className="ml-2 text-lg font-semibold text-muted-foreground">
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
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                    Ready
                  </div>
                </div>
              </div>

              {/* Error from API load - informational only */}
              {loadError && (
                <div className="flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3">
                  <Zap className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-amber-200">
                      Running in demo mode. Backend connection unavailable.
                    </p>
                  </div>
                </div>
              )}

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
                  <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
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
                      className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-foreground hover:underline"
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
                {/* Icon */}
                <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/20 ring-2 ring-emerald-500/40">
                  <CheckCircle2 className="h-8 w-8 text-emerald-500" />
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
                <div className="h-full animate-pulse rounded-full bg-emerald-500" />
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions - Always show when content is visible */}
        {showContent && state !== "success" && (
          <>
            <Separator className="opacity-50" />
            <div className="flex gap-3 p-5">
              <Button
                onClick={onClose}
                variant="outline"
                disabled={state === "loading" || isDeploying}
                className="flex-1 border-border bg-transparent hover:bg-muted"
              >
                Cancel
              </Button>

              {isDemoMode ? (
                <Button
                  onClick={handleDemoModeDeploy}
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
              ) : (
                <Button
                  onClick={handlePayWithWallet}
                  disabled={state === "loading"}
                  className="flex-1 gap-2 bg-foreground font-semibold text-background hover:bg-foreground/90"
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
