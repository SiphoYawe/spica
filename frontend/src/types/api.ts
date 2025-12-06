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

// Parse API Types
export interface WorkflowTrigger {
  type: string;
  config: Record<string, unknown>;
}

export interface WorkflowStep {
  action: string;
  params: Record<string, unknown>;
}

export interface WorkflowSpec {
  name: string;
  description: string;
  trigger: WorkflowTrigger;
  steps: WorkflowStep[];
}

export interface ParseSuccessResponse {
  success: true;
  workflow_spec: WorkflowSpec;
  confidence: number;
  parse_time_ms: number;
  sla_exceeded: boolean;
}

export interface ParseErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: string;
    retry?: boolean;
  };
}

export type ParseResponse = ParseSuccessResponse | ParseErrorResponse;

export interface ParseRequest {
  input: string;
}

export interface ExampleWorkflow {
  input: string;
  description: string;
  category: string;
}

export interface ExamplesResponse {
  examples: ExampleWorkflow[];
}

export interface CapabilitiesResponse {
  supported_tokens: string[];
  supported_actions: string[];
  supported_triggers: string[];
}
