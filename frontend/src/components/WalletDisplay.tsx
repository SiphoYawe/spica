"use client";

/**
 * WalletDisplay - Compact wallet display for header
 *
 * Shows wallet address and token balances in a compact, elegant format.
 * Designed for the CanvasHeader with matching neo-cyberpunk styling.
 */

import { useState } from "react";
import { useWallet } from "@/hooks/useWallet";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Wallet, RefreshCw, Copy, Check, ExternalLink } from "lucide-react";

export function WalletDisplay() {
  const {
    wallet,
    loading,
    error,
    shortAddress,
    balances,
    network,
    isConnected,
    getFormattedBalance,
    refresh,
  } = useWallet({ autoFetch: true, refreshInterval: 30000 });

  const [copied, setCopied] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleCopy = async () => {
    if (!wallet?.address) return;
    await navigator.clipboard.writeText(wallet.address);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refresh();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  // Get primary balance (GAS)
  const gasBalance = getFormattedBalance("GAS", 2);

  if (loading && !wallet) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-border/50 bg-muted/30 px-3 py-1.5">
        <div className="h-4 w-4 animate-pulse rounded-full bg-muted-foreground/20" />
        <div className="h-3 w-16 animate-pulse rounded bg-muted-foreground/20" />
      </div>
    );
  }

  if (error && !wallet) {
    // Ensure error is rendered as a string
    const errorMessage = typeof error === 'string' ? error : 'Connection error';
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-2 border-destructive/50 text-destructive hover:bg-destructive/10"
            onClick={handleRefresh}
          >
            <Wallet className="h-3.5 w-3.5" />
            <span className="text-xs">Retry</span>
          </Button>
        </TooltipTrigger>
        <TooltipContent>{errorMessage}</TooltipContent>
      </Tooltip>
    );
  }

  if (!isConnected) {
    return (
      <Button
        variant="outline"
        size="sm"
        className="h-8 gap-2"
        onClick={handleRefresh}
      >
        <Wallet className="h-3.5 w-3.5" />
        <span className="text-xs">Connect</span>
      </Button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn(
            "h-8 gap-2 border-spica/30 bg-spica/5 font-mono text-xs",
            "hover:border-spica/50 hover:bg-spica/10",
            "focus-visible:ring-spica/30",
            "transition-all duration-200"
          )}
        >
          {/* Status indicator */}
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-spica opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-spica" />
          </span>

          {/* Address */}
          <span className="text-muted-foreground">{shortAddress}</span>

          {/* Balances preview */}
          <span className="hidden items-center gap-1.5 border-l border-border/50 pl-2 sm:flex">
            <span className="text-spica">{gasBalance}</span>
            <span className="text-muted-foreground/60">GAS</span>
          </span>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-72">
        <DropdownMenuLabel className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wallet className="h-4 w-4 text-spica" />
            <span>Demo Wallet</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="rounded bg-spica/10 px-1.5 py-0.5 text-[10px] font-medium uppercase text-spica">
              {network}
            </span>
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        {/* Address section */}
        <div className="px-2 py-2">
          <div className="mb-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            Address
          </div>
          <div className="flex items-center gap-2">
            <code className="flex-1 truncate rounded bg-muted/50 px-2 py-1 font-mono text-xs">
              {wallet?.address}
            </code>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 shrink-0"
                  onClick={handleCopy}
                >
                  {copied ? (
                    <Check className="h-3.5 w-3.5 text-spica" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{copied ? "Copied!" : "Copy address"}</TooltipContent>
            </Tooltip>
          </div>
        </div>

        <DropdownMenuSeparator />

        {/* Balances section */}
        <div className="px-2 py-2">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              Balances
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw
                className={cn(
                  "h-3 w-3",
                  isRefreshing && "animate-spin"
                )}
              />
            </Button>
          </div>

          <div className="space-y-2">
            {balances.map((balance) => (
              <div
                key={balance.token}
                className="flex items-center justify-between rounded-lg bg-muted/30 px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <div
                    className={cn(
                      "flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold",
                      balance.token === "GAS"
                        ? "bg-spica/20 text-spica"
                        : balance.token === "NEO"
                        ? "bg-emerald-500/20 text-emerald-500"
                        : "bg-muted text-muted-foreground"
                    )}
                  >
                    {balance.token.slice(0, 1)}
                  </div>
                  <span className="text-sm font-medium">{balance.token}</span>
                </div>
                <span className="font-mono text-sm tabular-nums">
                  {getFormattedBalance(balance.token, 4)}
                </span>
              </div>
            ))}

            {balances.length === 0 && (
              <div className="py-4 text-center text-sm text-muted-foreground">
                No tokens found
              </div>
            )}
          </div>
        </div>

        <DropdownMenuSeparator />

        {/* Footer */}
        <div className="flex items-center justify-between px-2 py-2">
          <span className="text-[10px] text-muted-foreground">
            Demo mode • Pre-funded wallet
          </span>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => {
                  if (wallet?.address) {
                    window.open(
                      `https://dora.coz.io/address/neo3/testnet/${wallet.address}`,
                      "_blank"
                    );
                  }
                }}
              >
                <ExternalLink className="h-3 w-3" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>View on Dora Explorer</TooltipContent>
          </Tooltip>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
