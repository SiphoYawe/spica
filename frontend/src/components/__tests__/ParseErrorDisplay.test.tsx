import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ParseErrorDisplay from '../ParseErrorDisplay'
import { apiClient } from '@/api/client'

// Mock API client
vi.mock('@/api/client', () => ({
  apiClient: {
    getCapabilities: vi.fn(),
  },
}))

describe('ParseErrorDisplay', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Error Categorization', () => {
    it('displays unsupported token error with available tokens', async () => {
      // Mock capabilities response
      vi.mocked(apiClient.getCapabilities).mockResolvedValue({
        success: true,
        data: {
          supported_tokens: ['GAS', 'NEO', 'bNEO'],
          supported_actions: [],
          supported_triggers: [],
        },
      })

      const error = {
        code: 'PARSE_ERROR',
        message: 'Unsupported token "BITCOIN"',
        details: 'Token BITCOIN is not supported',
        retry: false,
      }

      render(<ParseErrorDisplay error={error} />)

      // Check error message is displayed
      expect(screen.getByText(/Unsupported token/i)).toBeInTheDocument()

      // Wait for capabilities to load
      await waitFor(() => {
        expect(screen.getByText('Supported tokens:')).toBeInTheDocument()
      })

      // Check all tokens are displayed as badges
      expect(screen.getByText('GAS')).toBeInTheDocument()
      expect(screen.getByText('NEO')).toBeInTheDocument()
      expect(screen.getByText('bNEO')).toBeInTheDocument()

      // Check hint message
      expect(screen.getByText(/Try using one of these tokens/i)).toBeInTheDocument()
    })

    it('displays unsupported action error with available actions', async () => {
      vi.mocked(apiClient.getCapabilities).mockResolvedValue({
        success: true,
        data: {
          supported_tokens: [],
          supported_actions: ['swap', 'stake', 'transfer'],
          supported_triggers: [],
        },
      })

      const error = {
        code: 'PARSE_ERROR',
        message: 'Unsupported action "send"',
        details: 'Action send is not supported',
        retry: false,
      }

      render(<ParseErrorDisplay error={error} />)

      await waitFor(() => {
        expect(screen.getByText('Supported actions:')).toBeInTheDocument()
      })

      expect(screen.getByText('swap')).toBeInTheDocument()
      expect(screen.getByText('stake')).toBeInTheDocument()
      expect(screen.getByText('transfer')).toBeInTheDocument()
    })

    it('displays ambiguous error with clarification', () => {
      const error = {
        code: 'PARSE_ERROR',
        message: 'Ambiguous input',
        details: 'Did you mean: swap or transfer?',
        retry: false,
      }

      render(<ParseErrorDisplay error={error} />)

      expect(screen.getByText(/Ambiguous input/i)).toBeInTheDocument()
      expect(screen.getByText('Clarification needed:')).toBeInTheDocument()
      expect(screen.getByText('swap')).toBeInTheDocument()
      expect(screen.getByText('transfer')).toBeInTheDocument()
    })

    it('displays validation error with helpful hint', () => {
      const error = {
        code: 'VALIDATION_ERROR',
        message: 'Input too long',
        details: 'Maximum 500 characters allowed',
        retry: false,
      }

      render(<ParseErrorDisplay error={error} />)

      expect(screen.getByText(/Input too long/i)).toBeInTheDocument()
      expect(screen.getByText(/keep it under 500 characters/i)).toBeInTheDocument()
    })

    it('displays network error with retry button', () => {
      const mockRetry = vi.fn()

      const error = {
        code: 'NETWORK_ERROR',
        message: 'Failed to connect',
        retry: true,
      }

      render(<ParseErrorDisplay error={error} onRetry={mockRetry} />)

      expect(screen.getByText(/Unable to connect to the server/i)).toBeInTheDocument()

      const retryButton = screen.getByRole('button', { name: /retry/i })
      expect(retryButton).toBeInTheDocument()
    })
  })

  describe('User Interactions', () => {
    it('calls onRetry when retry button is clicked', async () => {
      const user = userEvent.setup()
      const mockRetry = vi.fn()

      const error = {
        code: 'NETWORK_ERROR',
        message: 'Connection failed',
        retry: true,
      }

      render(<ParseErrorDisplay error={error} onRetry={mockRetry} />)

      const retryButton = screen.getByRole('button', { name: /retry/i })
      await user.click(retryButton)

      expect(mockRetry).toHaveBeenCalledTimes(1)
    })

    it('toggles example workflows when link is clicked', async () => {
      const user = userEvent.setup()

      const error = {
        code: 'PARSE_ERROR',
        message: 'Could not parse input',
        retry: false,
      }

      render(<ParseErrorDisplay error={error} />)

      // Examples should not be visible initially
      expect(screen.queryByText(/When GAS price drops/i)).not.toBeInTheDocument()

      // Click show examples
      const showLink = screen.getByText('Show example workflows')
      await user.click(showLink)

      // Examples should now be visible
      expect(screen.getByText(/When GAS price drops/i)).toBeInTheDocument()

      // Click hide examples
      const hideLink = screen.getByText('Hide examples')
      await user.click(hideLink)

      // Examples should be hidden again
      expect(screen.queryByText(/When GAS price drops/i)).not.toBeInTheDocument()
    })
  })

  describe('Capabilities Loading', () => {
    it('handles capabilities loading failure gracefully', async () => {
      vi.mocked(apiClient.getCapabilities).mockRejectedValue(
        new Error('Failed to load capabilities')
      )

      const error = {
        code: 'PARSE_ERROR',
        message: 'Unsupported token "BTC"',
        details: 'Token not supported',
        retry: false,
      }

      // Should not throw error
      render(<ParseErrorDisplay error={error} />)

      expect(screen.getByText(/Unsupported token/i)).toBeInTheDocument()

      // Should not display capabilities section since loading failed
      await waitFor(() => {
        expect(screen.queryByText('Supported tokens:')).not.toBeInTheDocument()
      })
    })

    it('does not load capabilities for non-parse errors', () => {
      const error = {
        code: 'NETWORK_ERROR',
        message: 'Connection failed',
        retry: true,
      }

      render(<ParseErrorDisplay error={error} />)

      // Should not call getCapabilities for network errors
      expect(apiClient.getCapabilities).not.toHaveBeenCalled()
    })

    it('handles empty capabilities arrays gracefully', async () => {
      vi.mocked(apiClient.getCapabilities).mockResolvedValue({
        success: true,
        data: {
          supported_tokens: [],
          supported_actions: [],
          supported_triggers: [],
        },
      })

      const error = {
        code: 'PARSE_ERROR',
        message: 'Unsupported token "BTC"',
        details: 'Token not supported',
        retry: false,
      }

      render(<ParseErrorDisplay error={error} />)

      // Should display error message
      expect(screen.getByText(/Unsupported token/i)).toBeInTheDocument()

      // Should not display capabilities section when arrays are empty
      await waitFor(() => {
        expect(screen.queryByText('Supported tokens:')).not.toBeInTheDocument()
        expect(screen.queryByText('Supported actions:')).not.toBeInTheDocument()
      })
    })
  })

  describe('Technical Details', () => {
    it('shows technical details in development mode', () => {
      // Mock import.meta.env.DEV to true
      vi.stubGlobal('import.meta', { env: { DEV: true } })

      const error = {
        code: 'PARSE_ERROR',
        message: 'Parse failed',
        details: 'Stack trace: error at line 42',
        retry: false,
      }

      render(<ParseErrorDisplay error={error} />)

      expect(screen.getByText('Technical details')).toBeInTheDocument()
      expect(screen.getByText(/Stack trace: error at line 42/i)).toBeInTheDocument()

      vi.unstubAllGlobals()
    })

    it('hides technical details in production mode', () => {
      // Mock import.meta.env.DEV to false
      vi.stubGlobal('import.meta', { env: { DEV: false } })

      const error = {
        code: 'PARSE_ERROR',
        message: 'Parse failed',
        details: 'Stack trace: error at line 42',
        retry: false,
      }

      render(<ParseErrorDisplay error={error} />)

      expect(screen.queryByText('Technical details')).not.toBeInTheDocument()

      vi.unstubAllGlobals()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      const error = {
        code: 'PARSE_ERROR',
        message: 'Parse failed',
        retry: false,
      }

      const { container } = render(<ParseErrorDisplay error={error} />)

      const alert = container.querySelector('[role="alert"]')
      expect(alert).toBeInTheDocument()
      expect(alert).toHaveAttribute('aria-live', 'assertive')
    })

    it('retry button is accessible', () => {
      const mockRetry = vi.fn()

      const error = {
        code: 'NETWORK_ERROR',
        message: 'Connection failed',
        retry: true,
      }

      render(<ParseErrorDisplay error={error} onRetry={mockRetry} />)

      const retryButton = screen.getByRole('button', { name: /retry/i })
      expect(retryButton).toBeInTheDocument()
      expect(retryButton).toBeEnabled()
    })
  })

  describe('User-Friendly Messaging', () => {
    it('converts technical errors to user-friendly messages', () => {
      const error = {
        code: 'INTERNAL_SERVER_ERROR',
        message: 'NullPointerException at TokenParser.java:142',
        retry: false,
      }

      render(<ParseErrorDisplay error={error} />)

      // Should show user-friendly message, not technical jargon
      expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument()
      // Technical details should be hidden in the details section
      expect(screen.queryByText(/NullPointerException/i)).not.toBeInTheDocument()
    })
  })
})
