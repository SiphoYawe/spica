import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { apiClient } from '@/api/client';
import type { WalletInfo, WalletBalance } from '@/types/api';

interface WalletState {
  // Wallet data
  wallet: WalletInfo | null;
  loading: boolean;
  error: string | null;
  lastFetched: Date | null;

  // Actions
  fetchWallet: () => Promise<void>;
  clearError: () => void;
  reset: () => void;

  // Computed helpers
  getBalance: (token: string) => WalletBalance | undefined;
  getTotalGas: () => string;
  getFormattedBalance: (token: string, maxDecimals?: number) => string;
  shortenAddress: () => string;
}

export const useWalletStore = create<WalletState>()(
  devtools(
    (set, get) => ({
      // Initial state
      wallet: null,
      loading: false,
      error: null,
      lastFetched: null,

      // Fetch wallet data from API
      fetchWallet: async () => {
        // Don't fetch if already loading
        if (get().loading) return;

        set({ loading: true, error: null }, false, 'fetchWallet/start');

        try {
          const response = await apiClient.getWallet();

          if (response.success && response.data) {
            // Handle nested response structure
            if (response.data.success && response.data.data) {
              set({
                wallet: response.data.data,
                loading: false,
                error: null,
                lastFetched: new Date(),
              }, false, 'fetchWallet/success');
            } else {
              set({
                loading: false,
                error: 'Invalid wallet response',
              }, false, 'fetchWallet/invalid');
            }
          } else {
            set({
              loading: false,
              error: response.error?.message || 'Failed to load wallet',
            }, false, 'fetchWallet/error');
          }
        } catch (err) {
          set({
            loading: false,
            error: err instanceof Error ? err.message : 'Network error',
          }, false, 'fetchWallet/exception');
        }
      },

      // Clear error state
      clearError: () => set({ error: null }, false, 'clearError'),

      // Reset wallet state
      reset: () => set({
        wallet: null,
        loading: false,
        error: null,
        lastFetched: null,
      }, false, 'reset'),

      // Get balance for a specific token
      getBalance: (token: string) => {
        const { wallet } = get();
        if (!wallet) return undefined;
        return wallet.balances.find(b =>
          b.token.toLowerCase() === token.toLowerCase()
        );
      },

      // Get GAS balance as formatted string
      getTotalGas: () => {
        const { wallet } = get();
        if (!wallet) return '0';
        const gasBalance = wallet.balances.find(b =>
          b.token.toLowerCase() === 'gas'
        );
        if (!gasBalance) return '0';
        return gasBalance.balance;
      },

      // Format balance with max decimals
      getFormattedBalance: (token: string, maxDecimals = 4) => {
        const balance = get().getBalance(token);
        if (!balance) return '0';

        const [intPart, decPart = ''] = balance.balance.split('.');
        if (balance.decimals === 0 || maxDecimals === 0) {
          return intPart;
        }

        const displayDecimals = Math.min(balance.decimals, maxDecimals);
        const formattedDec = (decPart + '0'.repeat(displayDecimals))
          .slice(0, displayDecimals);

        // Remove trailing zeros
        const trimmedDec = formattedDec.replace(/0+$/, '');
        return trimmedDec ? `${intPart}.${trimmedDec}` : intPart;
      },

      // Shorten wallet address for display
      shortenAddress: () => {
        const { wallet } = get();
        if (!wallet?.address) return '';
        const addr = wallet.address;
        if (addr.length < 10) return addr;
        return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
      },
    }),
    { name: 'wallet-store' }
  )
);
