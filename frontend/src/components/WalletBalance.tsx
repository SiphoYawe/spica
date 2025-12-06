"use client"

/**
 * WalletBalance Component
 *
 * Displays demo wallet address and token balances with neo-cyberpunk aesthetic.
 * Features holographic card design, glitch effects, and animated data streams.
 */

import { useState, useEffect } from 'react';
import { apiClient } from '@/api/client';
import type { WalletInfo } from '@/types/api';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface WalletBalanceProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export default function WalletBalance({
  autoRefresh = false,
  refreshInterval = 30000
}: WalletBalanceProps) {
  const [wallet, setWallet] = useState<WalletInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchWallet = async () => {
    try {
      setIsRefreshing(true);
      const response = await apiClient.getWallet();

      if (response.success && response.data) {
        if (response.data.success && response.data.data) {
          setWallet(response.data.data);
          setError(null);
        } else {
          setError('Failed to load wallet');
        }
      } else {
        setError(response.error?.message || 'Failed to load wallet');
      }
    } catch (err) {
      setError('Network error');
      console.error('Wallet fetch error:', err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchWallet();

    if (autoRefresh) {
      const interval = setInterval(fetchWallet, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const formatBalance = (balance: string, decimals: number): string => {
    if (decimals === 0) {
      return balance.split('.')[0];
    }

    const [intPart, decPart = ''] = balance.split('.');
    const displayDecimals = Math.min(decimals, 4);

    if (displayDecimals === 0) {
      return intPart;
    }

    const formattedDec = (decPart + '0'.repeat(displayDecimals))
      .slice(0, displayDecimals);

    return `${intPart}.${formattedDec}`;
  };

  const shortenAddress = (address: string): string => {
    if (!address || address.length < 10) return address;
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  if (loading) {
    return (
      <div
        className="mx-auto w-full max-w-[480px] font-mono text-terminal-text"
        role="status"
        aria-live="polite"
      >
        <div className="relative min-h-[280px] flex items-center justify-center rounded-2xl border-2 border-cyber-green bg-gradient-to-br from-darker-bg to-dark-bg p-6 shadow-[0_0_20px_var(--color-glow-green),inset_0_0_60px_rgba(0,255,65,0.05),0_8px_32px_rgba(0,0,0,0.6)]">
          <div className="text-center text-cyber-green">
            <div className="mx-auto my-2 h-0.5 w-[200px] overflow-hidden rounded-sm bg-cyber-green/20 relative">
              <div className="absolute top-0 -left-full h-full w-full bg-cyber-green animate-loading-pulse" />
            </div>
            <div className="mx-auto my-2 h-0.5 w-[200px] overflow-hidden rounded-sm bg-cyber-green/20 relative" style={{ animationDelay: '0.2s' }}>
              <div className="absolute top-0 -left-full h-full w-full bg-cyber-green animate-loading-pulse" style={{ animationDelay: '0.2s' }} />
            </div>
            <div className="mx-auto my-2 h-0.5 w-[200px] overflow-hidden rounded-sm bg-cyber-green/20 relative" style={{ animationDelay: '0.4s' }}>
              <div className="absolute top-0 -left-full h-full w-full bg-cyber-green animate-loading-pulse" style={{ animationDelay: '0.4s' }} />
            </div>
            <span className="mt-5 block font-display text-[11px] tracking-[2px] text-shadow-[0_0_8px_var(--color-glow-green)] animate-text-pulse">
              INITIALIZING WALLET INTERFACE
            </span>
            <span className="sr-only">Loading wallet information</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="mx-auto w-full max-w-[480px] font-mono text-terminal-text"
        role="alert"
        aria-live="assertive"
      >
        <div className="relative min-h-[280px] flex items-center justify-center rounded-2xl border-2 border-cyber-green bg-gradient-to-br from-darker-bg to-dark-bg p-6 shadow-[0_0_20px_var(--color-glow-green),inset_0_0_60px_rgba(0,255,65,0.05),0_8px_32px_rgba(0,0,0,0.6)]">
          <div className="text-center text-cyber-red">
            <div className="mb-4 text-5xl animate-error-blink" aria-hidden="true">
              ⚠
            </div>
            <div className="mb-5 font-mono text-sm text-shadow-[0_0_8px_rgba(255,0,85,0.5)]">
              {error}
            </div>
            <Button
              variant="cyber"
              onClick={fetchWallet}
              className="border-cyber-red text-cyber-red hover:bg-cyber-red/10 hover:shadow-[0_0_16px_rgba(255,0,85,0.4)]"
              aria-label="Retry wallet connection"
            >
              RETRY CONNECTION
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!wallet) return null;

  return (
    <div
      className="mx-auto w-full max-w-[480px] font-mono text-terminal-text"
      role="region"
      aria-label="Wallet balance information"
    >
      <div className="group relative overflow-hidden rounded-2xl border-2 border-cyber-green bg-gradient-to-br from-darker-bg to-dark-bg p-6 shadow-[0_0_20px_var(--color-glow-green),inset_0_0_60px_rgba(0,255,65,0.05),0_8px_32px_rgba(0,0,0,0.6)] transition-all duration-300 hover:border-cyber-blue hover:shadow-[0_0_30px_var(--color-glow-blue),inset_0_0_60px_rgba(0,217,255,0.05),0_12px_48px_rgba(0,0,0,0.8)] hover:-translate-y-0.5">
        {/* Holographic overlay effect */}
        <div
          className="pointer-events-none absolute inset-0 bg-[linear-gradient(45deg,transparent_0%,rgba(0,255,65,0.03)_25%,transparent_50%,rgba(0,217,255,0.03)_75%,transparent_100%)] bg-[length:200%_200%] opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-hover:animate-holo-shift"
          aria-hidden="true"
        />
        {/* Scanning line effect */}
        <div
          className="pointer-events-none absolute -top-full left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyber-green to-transparent opacity-0 shadow-[0_0_10px_var(--color-cyber-green)] group-hover:opacity-80 group-hover:animate-scan-line"
          aria-hidden="true"
        />

        {/* Header */}
        <div className="mb-5 flex items-center justify-between border-b border-cyber-green/20 pb-3">
          <div className="flex items-center gap-2">
            <span
              className="h-2 w-2 rounded-full bg-cyber-green shadow-[0_0_8px_var(--color-cyber-green)] animate-pulse-glow"
              aria-hidden="true"
            />
            <span
              className="font-display text-[11px] font-bold tracking-[2px] text-cyber-green text-shadow-[0_0_8px_var(--color-glow-green)]"
              aria-label={`Network: ${wallet.network}`}
            >
              {wallet.network.toUpperCase()}
            </span>
          </div>
          <button
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-md border border-cyber-green bg-transparent text-lg text-cyber-green transition-all duration-200 hover:bg-cyber-green/10 hover:shadow-[0_0_12px_var(--color-glow-green)] hover:rotate-90",
              isRefreshing && "animate-spin pointer-events-none opacity-60"
            )}
            onClick={fetchWallet}
            disabled={isRefreshing}
            aria-label={isRefreshing ? 'Refreshing balances' : 'Refresh balances'}
            title="Refresh balances"
          >
            ⟳
          </button>
        </div>

        {/* Address */}
        <div className="mb-6">
          <div
            className="mb-1.5 font-display text-[9px] tracking-[1.5px] text-terminal-dim"
            id="wallet-address-label"
          >
            WALLET ADDRESS
          </div>
          <div
            className="text-sm text-cyber-blue text-shadow-[0_0_8px_var(--color-glow-blue)] break-all"
            aria-labelledby="wallet-address-label"
            role="text"
          >
            <span className="hidden md:inline font-mono" title={wallet.address}>
              {wallet.address}
            </span>
            <span className="md:hidden font-mono" aria-label={wallet.address}>
              {shortenAddress(wallet.address)}
            </span>
          </div>
        </div>

        {/* Balances */}
        <div
          className="mb-5 grid grid-cols-1 gap-4 sm:grid-cols-[repeat(auto-fit,minmax(180px,1fr))]"
          role="list"
          aria-label="Token balances"
        >
          {wallet.balances.map((balance, index) => (
            <div
              key={balance.token}
              className="relative overflow-hidden rounded-xl border border-cyber-green/20 bg-cyber-green/[0.03] p-4 transition-all hover:border-cyber-green hover:bg-cyber-green/[0.08] hover:shadow-[0_0_16px_rgba(0,255,65,0.2)] animate-slide-up"
              role="listitem"
              style={{ animationDelay: `${index * 0.1}s` }}
              aria-label={`${balance.token}: ${formatBalance(balance.balance, balance.decimals)}`}
            >
              <div className="mb-3 flex items-center justify-between">
                <div className="font-display text-sm font-bold tracking-[2px] text-cyber-green text-shadow-[0_0_6px_var(--color-glow-green)]">
                  {balance.token}
                </div>
                <div
                  className="font-mono text-[9px] text-terminal-dim"
                  aria-label={`${balance.decimals} decimal places`}
                >
                  ×10^{balance.decimals}
                </div>
              </div>
              <div
                className="font-display text-[28px] font-black leading-none tracking-tight text-terminal-text text-shadow-[0_0_10px_rgba(255,255,255,0.3)]"
                aria-live="polite"
              >
                {formatBalance(balance.balance, balance.decimals)}
              </div>
              <div className="mt-2 h-[3px] overflow-hidden rounded-sm bg-cyber-green/10" aria-hidden="true">
                <div className="h-full w-2/5 bg-gradient-to-r from-transparent via-cyber-green to-transparent animate-stream-flow" />
              </div>
            </div>
          ))}
        </div>

        {/* Footer metadata */}
        <div className="flex items-center justify-between border-t border-cyber-green/10 pt-4 text-[10px]">
          <div className="flex flex-col gap-1">
            <span className="font-display tracking-[1px] text-terminal-dim">
              LAST SYNC
            </span>
            <span
              className="font-mono text-terminal-text"
              aria-label={`Last synced at ${new Date(wallet.timestamp).toLocaleTimeString()}`}
            >
              {new Date(wallet.timestamp).toLocaleTimeString()}
            </span>
          </div>
          <div className="flex items-center gap-1.5 font-display tracking-[1px] text-cyber-green" role="status">
            <div
              className="h-1.5 w-1.5 rounded-full bg-cyber-green shadow-[0_0_8px_var(--color-cyber-green)] animate-pulse-glow"
              aria-hidden="true"
            />
            <span>ACTIVE</span>
          </div>
        </div>
      </div>
    </div>
  );
}
