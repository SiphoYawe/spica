/**
 * Payment Hook
 * Manages x402 payment flow for workflow deployment
 */

import { useState, useCallback } from 'react';
import { apiClient } from '@/api/client';
import type { PaymentRequest, PaymentResponse, PaymentState } from '@/types/payment';

interface UsePaymentReturn {
  state: PaymentState;
  error: string | null;
  paymentRequest: PaymentRequest | null;
  parsePaymentRequest: (response: Response) => PaymentRequest | null;
  submitPayment: (workflowId: string, paymentData: PaymentRequest) => Promise<PaymentResponse | null>;
  reset: () => void;
}

export function usePayment(): UsePaymentReturn {
  const [state, setState] = useState<PaymentState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [paymentRequest, setPaymentRequest] = useState<PaymentRequest | null>(null);

  /**
   * Parse X-PAYMENT-REQUEST header from 402 response
   */
  const parsePaymentRequest = useCallback((response: Response): PaymentRequest | null => {
    try {
      const headerValue = response.headers.get('X-PAYMENT-REQUEST');
      if (!headerValue) {
        setError('No payment request header found');
        return null;
      }

      // Decode base64
      const decoded = atob(headerValue);
      const parsed = JSON.parse(decoded) as PaymentRequest;

      // Validate structure
      if (!parsed.x402Version || !parsed.accepts || parsed.accepts.length === 0) {
        setError('Invalid payment request format');
        return null;
      }

      setPaymentRequest(parsed);
      return parsed;
    } catch (err) {
      console.error('Failed to parse payment request:', err);
      setError('Failed to parse payment request');
      return null;
    }
  }, []);

  /**
   * Submit payment and deploy workflow
   */
  const submitPayment = useCallback(async (
    workflowId: string,
    paymentData: PaymentRequest
  ): Promise<PaymentResponse | null> => {
    try {
      setState('loading');
      setError(null);

      // Encode payment data as base64
      const paymentHeader = btoa(JSON.stringify(paymentData));

      // Submit with payment header
      const response = await apiClient.deployWithPayment(workflowId, paymentHeader);

      if (response.success && response.data) {
        if (response.data.success) {
          setState('success');
          return response.data as PaymentResponse;
        } else {
          const errorMsg = response.data.error?.message || 'Deployment failed';
          setError(errorMsg);
          setState('error');
          return response.data as PaymentResponse;
        }
      } else {
        const errorMsg = response.error?.message || 'Payment submission failed';
        setError(errorMsg);
        setState('error');
        return null;
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unexpected error during payment';
      console.error('Payment error:', err);
      setError(errorMsg);
      setState('error');
      return null;
    }
  }, []);

  /**
   * Reset payment state
   */
  const reset = useCallback(() => {
    setState('idle');
    setError(null);
    setPaymentRequest(null);
  }, []);

  return {
    state,
    error,
    paymentRequest,
    parsePaymentRequest,
    submitPayment,
    reset,
  };
}
