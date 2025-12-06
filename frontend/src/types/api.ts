/**
 * API Type Definitions
 * TypeScript interfaces for API requests and responses
 */

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface DetailedHealthResponse {
  status: string;
  services: Record<string, string>;
}

// Wallet Types
export interface WalletBalance {
  token: string;
  balance: string;
  decimals: number;
}

export interface WalletInfo {
  address: string;
  balances: WalletBalance[];
  network: string;
  timestamp: string;
}

export interface WalletResponse {
  success: boolean;
  data: WalletInfo;
  message?: string;
  timestamp: string;
}
