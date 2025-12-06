/**
 * Payment Type Definitions
 * x402 payment protocol types
 */

export interface PaymentAccept {
  scheme: string;
  network: string;
  max_amount_required: string;
  description: string;
  pay_to: string;
  extra?: {
    currency?: string;
    memo?: string;
    metadata?: {
      workflow_id?: string;
      complexity?: string;
      [key: string]: unknown;
    };
  };
}

export interface PaymentRequest {
  x402Version: number;
  accepts: PaymentAccept[];
}

export interface PaymentResponse {
  success: boolean;
  workflow_id?: string;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: string;
  };
}

export type PaymentState = 'idle' | 'loading' | 'success' | 'error';

export interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflowId: string;
  workflowName?: string;
  onSuccess?: (workflowId: string) => void;
  onError?: (error: string) => void;
}
