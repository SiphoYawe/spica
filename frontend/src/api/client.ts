/**
 * API Client for Spica Backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: string;
  };
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Generic fetch wrapper with error handling
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          success: false,
          error: {
            code: `HTTP_${response.status}`,
            message: errorData.detail || response.statusText,
          },
        };
      }

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error) {
      // Detect different error types for better debugging
      let errorCode = 'UNKNOWN_ERROR';
      let errorMessage = 'An unknown error occurred';
      let errorDetails: string | undefined;

      if (error instanceof TypeError) {
        // Network errors, CORS issues, or invalid URLs
        errorCode = 'NETWORK_ERROR';
        errorMessage = 'Network error: Unable to connect to server';
        errorDetails = error.message;
      } else if (error instanceof SyntaxError) {
        // JSON parsing errors
        errorCode = 'PARSE_ERROR';
        errorMessage = 'Failed to parse server response';
        errorDetails = error.message;
      } else if (error instanceof DOMException && error.name === 'AbortError') {
        // Request was aborted
        errorCode = 'REQUEST_ABORTED';
        errorMessage = 'Request was aborted';
        errorDetails = error.message;
      } else if (error instanceof Error) {
        // Generic error
        errorCode = 'REQUEST_ERROR';
        errorMessage = error.message;
        errorDetails = error.stack;
      }

      return {
        success: false,
        error: {
          code: errorCode,
          message: errorMessage,
          details: errorDetails,
        },
      };
    }
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  /**
   * Health check
   */
  async healthCheck() {
    return this.get<{ status: string; services: Record<string, string> }>('/health');
  }

  /**
   * Get wallet information and balances
   */
  async getWallet() {
    // API returns WalletResponse = { success, data: WalletInfo, message?, timestamp }
    return this.get<{
      success: boolean;
      data: {
        address: string;
        balances: Array<{ token: string; balance: string; decimals: number }>;
        network: string;
        timestamp: string;
      };
      message?: string;
      timestamp: string;
    }>('/api/v1/wallet');
  }

  /**
   * Get balance for specific token
   */
  async getTokenBalance(token: string) {
    return this.get<{
      success: boolean;
      data: {
        token: string;
        balance: string;
        decimals: number;
      };
      timestamp: string;
    }>(`/api/v1/wallet/balance/${token}`);
  }

  /**
   * Parse natural language input into workflow spec
   */
  async parseWorkflow(input: string) {
    return this.post<{
      success: boolean;
      workflow_spec?: {
        name: string;
        description: string;
        trigger: { type: string; config: Record<string, unknown> };
        steps: Array<{ action: string; params: Record<string, unknown> }>;
      };
      confidence?: number;
      parse_time_ms?: number;
      sla_exceeded?: boolean;
      error?: {
        code: string;
        message: string;
        details?: string;
        retry?: boolean;
      };
    }>('/api/v1/parse', { input });
  }

  /**
   * Get example workflows
   */
  async getExamples() {
    return this.get<{
      examples: Array<{
        input: string;
        description: string;
        category: string;
      }>;
    }>('/api/v1/parse/examples');
  }

  /**
   * Get parser capabilities
   */
  async getCapabilities() {
    return this.get<{
      supported_tokens: string[];
      supported_actions: string[];
      supported_triggers: string[];
    }>('/api/v1/parse/capabilities');
  }

  /**
   * Generate workflow graph from workflow spec
   */
  async generateWorkflow(workflowSpec: unknown, userId?: string, userAddress?: string) {
    return this.post<{
      success: boolean;
      workflow_id?: string;
      nodes?: Array<{
        id: string;
        type: string;
        label: string;
        parameters?: Record<string, unknown>;
        position: { x: number; y: number };
        data: Record<string, unknown>;
      }>;
      edges?: Array<{
        id: string;
        source: string;
        target: string;
        type: string;
        animated?: boolean;
      }>;
      workflow_name?: string;
      workflow_description?: string;
      generation_time_ms?: number;
      sla_exceeded?: boolean;
      timestamp?: string;
      error?: {
        code: string;
        message: string;
        details?: string;
        retry?: boolean;
      };
    }>('/api/v1/generate', {
      workflow_spec: workflowSpec,
      user_id: userId,
      user_address: userAddress,
    });
  }

  /**
   * Update workflow with modified nodes/edges
   */
  async updateWorkflow(workflowId: string, data: { nodes: unknown[]; edges: unknown[] }) {
    return this.put<{
      success: boolean;
      workflow_id: string;
      message?: string;
      timestamp?: string;
      error?: {
        code: string;
        message: string;
        details?: string;
      };
    }>(`/api/v1/workflows/${workflowId}`, data);
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;
