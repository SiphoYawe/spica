/**
 * API Client for Spica Backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

  /**
   * Deploy workflow (returns 402 if unpaid)
   */
  async deployWorkflow(workflowId: string): Promise<{
    success: boolean;
    status?: number;
    headers?: Headers;
    data?: unknown;
    error?: {
      code: string;
      message: string;
      details?: string;
    };
  }> {
    try {
      const url = `${this.baseUrl}/api/v1/workflows/${workflowId}/deploy`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      // Handle 402 Payment Required specially
      if (response.status === 402) {
        return {
          success: false,
          status: 402,
          headers: response.headers,
          error: {
            code: 'PAYMENT_REQUIRED',
            message: 'Payment required to deploy workflow',
          },
        };
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return {
          success: false,
          status: response.status,
          error: {
            code: `HTTP_${response.status}`,
            message: errorData.detail || response.statusText,
          },
        };
      }

      const data = await response.json();
      return {
        success: true,
        status: response.status,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: {
          code: 'NETWORK_ERROR',
          message: error instanceof Error ? error.message : 'Network error',
        },
      };
    }
  }

  /**
   * Deploy workflow with payment header
   */
  async deployWithPayment(workflowId: string, paymentHeader: string) {
    try {
      const url = `${this.baseUrl}/api/v1/workflows/${workflowId}/deploy`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-PAYMENT': paymentHeader,
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
      return {
        success: false,
        error: {
          code: 'NETWORK_ERROR',
          message: error instanceof Error ? error.message : 'Network error',
        },
      };
    }
  }

  /**
   * PATCH request
   */
  async patch<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // ========================================================================
  // Workflow Management - Story 6.8
  // ========================================================================

  /**
   * List all workflows
   */
  async listWorkflows(params?: { status?: string; user_id?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.set('workflow_status', params.status);
    if (params?.user_id) queryParams.set('user_id', params.user_id);
    const query = queryParams.toString();

    return this.get<{
      success: boolean;
      workflows: Array<{
        workflow_id: string;
        workflow_name: string;
        workflow_description: string;
        status: string;
        enabled: boolean;
        trigger_type: string;
        trigger_summary: string;
        execution_count: number;
        created_at: string;
        last_executed_at: string | null;
      }>;
      total: number;
      timestamp: string;
    }>(`/api/v1/workflows${query ? `?${query}` : ''}`);
  }

  /**
   * Get workflow details
   */
  async getWorkflow(workflowId: string) {
    return this.get<{
      success: boolean;
      workflow_id: string;
      workflow_name: string;
      workflow_description: string;
      status: string;
      enabled: boolean;
      trigger_type: string;
      trigger_summary: string;
      nodes: Array<{
        id: string;
        type: string;
        label: string;
        parameters: Record<string, unknown>;
        position: { x: number; y: number };
        data: Record<string, unknown>;
      }>;
      edges: Array<{
        id: string;
        source: string;
        target: string;
        type: string;
        animated: boolean;
      }>;
      execution_count: number;
      trigger_count: number;
      created_at: string;
      updated_at: string;
      last_executed_at: string | null;
      last_error: string | null;
      timestamp: string;
    }>(`/api/v1/workflows/${workflowId}`);
  }

  /**
   * Pause/Resume workflow
   */
  async toggleWorkflow(workflowId: string, enabled: boolean) {
    return this.patch<{
      success: boolean;
      workflow_id: string;
      status: string;
      enabled: boolean;
      message: string;
      timestamp: string;
    }>(`/api/v1/workflows/${workflowId}`, {
      enabled,
      status: enabled ? 'active' : 'paused',
    });
  }

  /**
   * Delete workflow
   */
  async deleteWorkflow(workflowId: string) {
    return this.delete<{
      success: boolean;
      workflow_id: string;
      message: string;
      timestamp: string;
    }>(`/api/v1/workflows/${workflowId}`);
  }

  /**
   * Get demo mode status
   * Returns whether the application is running in demo mode (bypasses payments)
   */
  async getDemoMode(): Promise<{
    demo_mode: boolean;
    message: string;
  }> {
    try {
      const response = await this.get<{
        demo_mode: boolean;
        message: string;
      }>('/api/v1/demo-mode');

      if (response.success && response.data) {
        return response.data;
      }

      // Default to production mode on error
      return {
        demo_mode: false,
        message: 'Failed to check demo mode status',
      };
    } catch (error) {
      console.error('Failed to check demo mode:', error);
      // Default to production mode on error
      return {
        demo_mode: false,
        message: 'Failed to check demo mode status',
      };
    }
  }

  // ========================================================================
  // Executions API - Task 4.4
  // ========================================================================

  /**
   * List execution records with pagination and filters
   */
  async listExecutions(params?: {
    workflow_id?: string;
    status?: string;
    page?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.workflow_id) queryParams.set('workflow_id', params.workflow_id);
    if (params?.status) queryParams.set('status', params.status);
    if (params?.page) queryParams.set('page', String(params.page));
    if (params?.limit) queryParams.set('limit', String(params.limit));
    const query = queryParams.toString();

    return this.get<{
      executions: Array<{
        execution_id: string;
        workflow_id: string;
        workflow_name: string;
        status: string;
        trigger_type: string;
        action_summary: string;
        started_at: string;
        completed_at: string | null;
        tx_hash: string | null;
        error: string | null;
        gas_used: string | null;
      }>;
      total: number;
      page: number;
      limit: number;
      has_next: boolean;
    }>(`/api/v1/executions${query ? `?${query}` : ''}`);
  }

  /**
   * Get execution details by ID
   */
  async getExecution(executionId: string) {
    return this.get<{
      execution_id: string;
      workflow_id: string;
      workflow_name: string;
      status: string;
      trigger_type: string;
      action_summary: string;
      started_at: string;
      completed_at: string | null;
      tx_hash: string | null;
      error: string | null;
      gas_used: string | null;
    }>(`/api/v1/executions/${executionId}`);
  }

  /**
   * Activate workflow from canvas data (create active workflow)
   */
  async activateWorkflow(data: {
    workflow_name: string;
    workflow_description: string;
    nodes: Array<{
      id: string;
      type: string;
      position: { x: number; y: number };
      data: Record<string, unknown>;
    }>;
    edges: Array<{
      id: string;
      source: string;
      target: string;
      animated?: boolean;
    }>;
    user_id?: string;
    user_address?: string;
  }) {
    return this.post<{
      success: boolean;
      workflow_id: string;
      workflow_name: string;
      message: string;
      timestamp: string;
    }>('/api/v1/workflows/activate', data);
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;
