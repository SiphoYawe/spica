"use client";

import { useEffect, useRef, useCallback } from "react";
import { useWalletStore } from "@/stores";

interface UseWalletOptions {
  /** Auto-fetch wallet on mount (default: true) */
  autoFetch?: boolean;
  /** Auto-refresh interval in ms (default: 30000, 0 to disable) */
  refreshInterval?: number;
}

/**
 * useWallet - Hook for wallet state management
 *
 * Provides wallet data with auto-fetch and optional auto-refresh.
 * Uses the global wallet store for state.
 *
 * @example
 * const { wallet, loading, error, refresh } = useWallet();
 * const { wallet } = useWallet({ autoFetch: true, refreshInterval: 60000 });
 */
export function useWallet(options: UseWalletOptions = {}) {
  const { autoFetch = true, refreshInterval = 30000 } = options;

  const wallet = useWalletStore((s) => s.wallet);
  const loading = useWalletStore((s) => s.loading);
  const error = useWalletStore((s) => s.error);
  const lastFetched = useWalletStore((s) => s.lastFetched);
  const fetchWallet = useWalletStore((s) => s.fetchWallet);
  const getFormattedBalance = useWalletStore((s) => s.getFormattedBalance);
  const shortenAddress = useWalletStore((s) => s.shortenAddress);
  const getTotalGas = useWalletStore((s) => s.getTotalGas);

  // Track if we've done initial fetch
  const hasFetchedRef = useRef(false);

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch && !hasFetchedRef.current && !wallet) {
      hasFetchedRef.current = true;
      fetchWallet();
    }
  }, [autoFetch, wallet, fetchWallet]);

  // Auto-refresh interval
  useEffect(() => {
    if (refreshInterval <= 0) return;

    const interval = setInterval(() => {
      fetchWallet();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval, fetchWallet]);

  // Manual refresh function
  const refresh = useCallback(() => {
    fetchWallet();
  }, [fetchWallet]);

  return {
    // State
    wallet,
    loading,
    error,
    lastFetched,

    // Computed
    address: wallet?.address ?? null,
    shortAddress: shortenAddress(),
    network: wallet?.network ?? null,
    balances: wallet?.balances ?? [],
    gasBalance: getTotalGas(),
    isConnected: !!wallet,

    // Helpers
    getFormattedBalance,

    // Actions
    refresh,
  };
}
