/**
 * Payment Modal Component
 * x402 payment interface for workflow deployment
 */

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/api/client';
import { usePayment } from '@/hooks/usePayment';
import type { PaymentModalProps, PaymentRequest } from '@/types/payment';
import { Loader2, CheckCircle2, XCircle, Wallet, ArrowRight, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

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
  const { state, error, submitPayment, reset } = usePayment();

  // Check demo mode and fetch payment info when modal opens
  useEffect(() => {
    if (isOpen && !paymentInfo) {
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
    }
  }, [isOpen, reset]);

  // Auto-close on success after delay
  useEffect(() => {
    if (state === 'success') {
      const timer = setTimeout(() => {
        onSuccess?.(workflowId);
        onClose();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [state, workflowId, onSuccess, onClose]);

  // Notify parent of errors
  useEffect(() => {
    if (state === 'error' && error) {
      onError?.(error);
    }
  }, [state, error, onError]);

  const checkDemoModeAndFetchPaymentInfo = async () => {
    setIsLoadingPaymentInfo(true);
    try {
      // Check if demo mode is enabled
      const demoModeStatus = await apiClient.getDemoMode();
      setIsDemoMode(demoModeStatus.demo_mode);

      const response = await apiClient.deployWorkflow(workflowId);

      if (response.status === 402 && response.headers) {
        // Parse X-PAYMENT-REQUEST header
        const headerValue = response.headers.get('X-PAYMENT-REQUEST');
        if (headerValue) {
          const decoded = atob(headerValue);
          const parsed = JSON.parse(decoded) as PaymentRequest;
          setPaymentInfo(parsed);
        }
      } else if (response.success) {
        // Already paid or demo mode - close modal
        onSuccess?.(workflowId);
        onClose();
      }
    } catch (err) {
      console.error('Failed to fetch payment info:', err);
      onError?.('Failed to load payment information');
    } finally {
      setIsLoadingPaymentInfo(false);
    }
  };

  const handlePayment = async () => {
    if (!paymentInfo) return;

    // In demo mode, bypass actual payment and directly deploy
    if (isDemoMode) {
      console.log('Demo mode - bypassing payment and deploying directly');
      try {
        // Call deploy endpoint directly (backend will bypass payment verification)
        const response = await apiClient.deployWorkflow(workflowId);
        if (response.success) {
          onSuccess?.(workflowId);
          onClose();
        } else {
          onError?.(response.error?.message || 'Failed to deploy workflow in demo mode');
        }
      } catch (err) {
        console.error('Demo mode deployment error:', err);
        onError?.('Failed to deploy workflow in demo mode');
      }
      return;
    }

    // Production mode - submit actual payment
    const result = await submitPayment(workflowId, paymentInfo);
    if (result?.success) {
      // Success handling is done in useEffect
      console.log('Payment successful:', result);
    }
  };

  // Get payment details from first accept option
  const paymentAccept = paymentInfo?.accepts?.[0];
  const amount = paymentAccept?.max_amount_required || '0';
  const currency = paymentAccept?.extra?.currency || 'USDC';
  const recipient = paymentAccept?.pay_to || '';
  const description = paymentAccept?.description || 'Deploy workflow';

  // Format amount (assuming USDC with 6 decimals)
  const formattedAmount = (parseInt(amount) / 1_000_000).toFixed(2);

  // Truncate address
  const truncateAddress = (addr: string) => {
    if (!addr || addr.length < 12) return addr;
    return `${addr.slice(0, 6)}...${addr.slice(-6)}`;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className={cn(
        "max-w-md border-cyber-green/20 bg-gradient-to-br from-card to-darker-bg",
        "shadow-[0_0_40px_rgba(0,255,65,0.15)]"
      )}>
        {/* Holographic accent line */}
        <div className="absolute left-0 top-0 h-1 w-full bg-gradient-to-r from-cyber-green via-cyber-blue to-cyber-purple opacity-70" />

        <DialogHeader className="space-y-3 pt-2">
          <DialogTitle className="flex items-center gap-2 font-display text-2xl tracking-wide text-cyber-green">
            <Wallet className="h-6 w-6" />
            Payment Required
            {isDemoMode && (
              <Badge
                variant="outline"
                className="ml-2 border-amber-500/50 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20"
              >
                <Zap className="mr-1 h-3 w-3" />
                Demo Mode
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription className="text-base text-muted-foreground">
            {isDemoMode
              ? 'Payment verification bypassed - deploy immediately'
              : 'Deploy your workflow to Neo N3 blockchain'
            }
          </DialogDescription>
        </DialogHeader>

        {/* Loading State */}
        {isLoadingPaymentInfo && (
          <div className="flex flex-col items-center justify-center space-y-4 py-12">
            <Loader2 className="h-12 w-12 animate-spin text-cyber-green" />
            <p className="text-sm text-muted-foreground">Loading payment details...</p>
          </div>
        )}

        {/* Payment Details */}
        {!isLoadingPaymentInfo && paymentInfo && state !== 'success' && (
          <div className="space-y-6 py-4">
            {/* Workflow Info */}
            <div className="rounded-lg border border-card-border bg-darker-bg/50 p-4">
              <div className="space-y-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Workflow
                  </p>
                  <p className="mt-1 font-mono text-sm text-foreground">
                    {workflowName || `Workflow ${workflowId.slice(0, 8)}`}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Description
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {description}
                  </p>
                </div>
              </div>
            </div>

            {/* Payment Amount - Highlighted */}
            <div className="relative rounded-lg border-2 border-cyber-green/40 bg-cyber-green/5 p-6 shadow-[0_0_20px_rgba(0,255,65,0.1)]">
              <div className="text-center">
                <p className="text-xs font-semibold uppercase tracking-widest text-cyber-green/80">
                  Amount
                </p>
                <div className="mt-2 flex items-baseline justify-center gap-2">
                  <span className="font-display text-5xl font-bold text-cyber-green">
                    {formattedAmount}
                  </span>
                  <span className="font-display text-2xl text-cyber-green/70">
                    {currency}
                  </span>
                </div>
              </div>
            </div>

            {/* Recipient Info */}
            <div className="rounded-lg border border-card-border bg-darker-bg/50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Recipient Address
              </p>
              <div className="mt-2 flex items-center gap-2">
                <code className="font-mono text-sm text-cyber-blue">
                  {truncateAddress(recipient)}
                </code>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </div>
            </div>

            {/* Network Info */}
            <div className="flex items-center justify-between rounded-lg border border-card-border bg-darker-bg/30 px-4 py-3">
              <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Network
              </span>
              <span className="font-mono text-sm text-foreground">
                {paymentAccept?.network || 'base-sepolia'}
              </span>
            </div>

            {/* Error Display */}
            {state === 'error' && error && (
              <Alert variant="destructive" className="animate-slide-up">
                <XCircle className="h-5 w-5" />
                <AlertDescription className="ml-2">
                  <strong className="font-semibold">Payment Failed:</strong> {error}
                </AlertDescription>
              </Alert>
            )}
          </div>
        )}

        {/* Success State */}
        {state === 'success' && (
          <div className="flex flex-col items-center justify-center space-y-4 py-12">
            <div className="relative">
              <div className="absolute inset-0 animate-pulse-glow rounded-full bg-cyber-green/30 blur-xl" />
              <CheckCircle2 className="relative h-16 w-16 text-cyber-green" />
            </div>
            <div className="text-center">
              <p className="font-display text-xl font-semibold text-cyber-green">
                Payment Successful!
              </p>
              <p className="mt-2 text-sm text-muted-foreground">
                Deploying your workflow to Neo N3...
              </p>
            </div>
          </div>
        )}

        {/* Footer Actions */}
        {!isLoadingPaymentInfo && paymentInfo && state !== 'success' && (
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              onClick={onClose}
              variant="ghost"
              disabled={state === 'loading'}
              className="w-full sm:w-auto"
            >
              Cancel
            </Button>
            <Button
              onClick={handlePayment}
              variant="cyber"
              disabled={state === 'loading'}
              className="w-full gap-2 sm:w-auto"
            >
              {state === 'loading' ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {isDemoMode ? 'Deploying...' : 'Processing...'}
                </>
              ) : isDemoMode ? (
                <>
                  <Zap className="h-4 w-4" />
                  Deploy (Demo)
                </>
              ) : (
                <>
                  <Wallet className="h-4 w-4" />
                  Pay & Deploy
                </>
              )}
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}
