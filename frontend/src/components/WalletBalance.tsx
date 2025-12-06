/**
 * WalletBalance Component
 *
 * Displays demo wallet address and token balances with neo-cyberpunk aesthetic.
 * Features holographic card design, glitch effects, and animated data streams.
 */

import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import type { WalletInfo } from '../types/api';
import './WalletBalance.css';

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
        // response.data is the WalletResponse containing { success, data: WalletInfo }
        // So response.data.data is the actual WalletInfo
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
    // Use string-based formatting to preserve precision for financial values
    // Avoid parseFloat which can introduce precision loss

    if (decimals === 0) {
      // For indivisible tokens (NEO), just return the integer part
      return balance.split('.')[0];
    }

    // For decimal tokens, format to appropriate decimal places
    // Preserve string precision throughout
    const [intPart, decPart = ''] = balance.split('.');
    const displayDecimals = Math.min(decimals, 4);

    if (displayDecimals === 0) {
      return intPart;
    }

    // Pad or truncate decimal part
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
      <div className="wallet-balance wallet-loading" role="status" aria-live="polite">
        <div className="loading-terminal">
          <div className="loading-line" aria-hidden="true"></div>
          <div className="loading-line" aria-hidden="true"></div>
          <div className="loading-line" aria-hidden="true"></div>
          <span className="loading-text">INITIALIZING WALLET INTERFACE</span>
          <span className="sr-only">Loading wallet information</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="wallet-balance wallet-error" role="alert" aria-live="assertive">
        <div className="error-terminal">
          <div className="error-icon" aria-hidden="true">⚠</div>
          <div className="error-message">{error}</div>
          <button
            className="retry-button"
            onClick={fetchWallet}
            aria-label="Retry wallet connection"
          >
            RETRY CONNECTION
          </button>
        </div>
      </div>
    );
  }

  if (!wallet) return null;

  return (
    <div className="wallet-balance" role="region" aria-label="Wallet balance information">
      <div className="wallet-card">
        {/* Holographic overlay effect */}
        <div className="holo-overlay" aria-hidden="true"></div>
        <div className="holo-scan" aria-hidden="true"></div>

        {/* Header */}
        <div className="wallet-header">
          <div className="header-label">
            <span className="network-indicator" aria-hidden="true"></span>
            <span className="network-text" aria-label={`Network: ${wallet.network}`}>
              {wallet.network.toUpperCase()}
            </span>
          </div>
          <button
            className={`refresh-btn ${isRefreshing ? 'refreshing' : ''}`}
            onClick={fetchWallet}
            disabled={isRefreshing}
            aria-label={isRefreshing ? 'Refreshing balances' : 'Refresh balances'}
            title="Refresh balances"
          >
            ⟳
          </button>
        </div>

        {/* Address */}
        <div className="wallet-address-section">
          <div className="address-label" id="wallet-address-label">WALLET ADDRESS</div>
          <div
            className="address-value"
            aria-labelledby="wallet-address-label"
            role="text"
          >
            <span className="address-full" title={wallet.address}>
              {wallet.address}
            </span>
            <span className="address-short" aria-label={wallet.address}>
              {shortenAddress(wallet.address)}
            </span>
          </div>
        </div>

        {/* Balances */}
        <div className="balances-grid" role="list" aria-label="Token balances">
          {wallet.balances.map((balance, index) => (
            <div
              key={balance.token}
              className="balance-item"
              role="listitem"
              style={{ animationDelay: `${index * 0.1}s` }}
              aria-label={`${balance.token}: ${formatBalance(balance.balance, balance.decimals)}`}
            >
              <div className="balance-header">
                <div className="token-symbol">{balance.token}</div>
                <div className="token-decimals" aria-label={`${balance.decimals} decimal places`}>
                  ×10^{balance.decimals}
                </div>
              </div>
              <div className="balance-amount" aria-live="polite">
                {formatBalance(balance.balance, balance.decimals)}
              </div>
              <div className="balance-stream" aria-hidden="true">
                <div className="stream-line"></div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer metadata */}
        <div className="wallet-footer">
          <div className="footer-item">
            <span className="footer-label">LAST SYNC</span>
            <span className="footer-value" aria-label={`Last synced at ${new Date(wallet.timestamp).toLocaleTimeString()}`}>
              {new Date(wallet.timestamp).toLocaleTimeString()}
            </span>
          </div>
          <div className="footer-status" role="status">
            <div className="status-dot" aria-hidden="true"></div>
            <span>ACTIVE</span>
          </div>
        </div>
      </div>
    </div>
  );
}
