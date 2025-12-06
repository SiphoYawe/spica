import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

// Payment request from x402 protocol
export interface PaymentRequest {
  paymentId?: string;
  amount?: string;
  currency?: string;
  receiver?: string;
  network?: string;
  [key: string]: unknown;
}

// Payment state enum
export type PaymentStatus = 'idle' | 'loading' | 'confirming' | 'processing' | 'success' | 'error';

interface PaymentState {
  // Modal state
  isModalOpen: boolean;

  // Payment data
  paymentRequest: PaymentRequest | null;

  // Status
  status: PaymentStatus;
  error: string | null;

  // Demo mode
  isDemoMode: boolean;

  // Deployment
  deploySuccess: boolean;
  deployError: string | null;

  // Actions
  openModal: () => void;
  closeModal: () => void;
  setPaymentRequest: (request: PaymentRequest | null) => void;
  setStatus: (status: PaymentStatus) => void;
  setError: (error: string | null) => void;
  setIsDemoMode: (demo: boolean) => void;
  setDeploySuccess: (success: boolean) => void;
  setDeployError: (error: string | null) => void;

  // Complex actions
  startPayment: () => void;
  completePayment: () => void;
  failPayment: (error: string) => void;
  resetPayment: () => void;
}

export const usePaymentStore = create<PaymentState>()(
  devtools(
    (set) => ({
      // Initial state
      isModalOpen: false,
      paymentRequest: null,
      status: 'idle',
      error: null,
      isDemoMode: false,
      deploySuccess: false,
      deployError: null,

      // Modal actions
      openModal: () => set({ isModalOpen: true }, false, 'openModal'),
      closeModal: () => set({ isModalOpen: false }, false, 'closeModal'),

      // Setters
      setPaymentRequest: (request) => set({ paymentRequest: request }, false, 'setPaymentRequest'),
      setStatus: (status) => set({ status }, false, 'setStatus'),
      setError: (error) => set({ error }, false, 'setError'),
      setIsDemoMode: (demo) => set({ isDemoMode: demo }, false, 'setIsDemoMode'),
      setDeploySuccess: (success) => set({ deploySuccess: success }, false, 'setDeploySuccess'),
      setDeployError: (error) => set({ deployError: error }, false, 'setDeployError'),

      // Complex actions
      startPayment: () =>
        set(
          { status: 'loading', error: null },
          false,
          'startPayment'
        ),

      completePayment: () =>
        set(
          { status: 'success', deploySuccess: true, isModalOpen: false },
          false,
          'completePayment'
        ),

      failPayment: (error) =>
        set(
          { status: 'error', error, deployError: error },
          false,
          'failPayment'
        ),

      resetPayment: () =>
        set(
          {
            isModalOpen: false,
            paymentRequest: null,
            status: 'idle',
            error: null,
            deploySuccess: false,
            deployError: null,
          },
          false,
          'resetPayment'
        ),
    }),
    { name: 'payment-store' }
  )
);
