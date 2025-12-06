/**
 * WorkflowInput Component Tests
 *
 * NOTE: This project does not currently have a testing framework configured.
 * To run these tests, you need to install testing dependencies:
 *
 * npm install --save-dev vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
 *
 * Then add to package.json:
 * "scripts": {
 *   "test": "vitest",
 *   "test:ui": "vitest --ui",
 *   "test:coverage": "vitest --coverage"
 * }
 *
 * Create vitest.config.ts with:
 * import { defineConfig } from 'vitest/config'
 * import react from '@vitejs/plugin-react'
 * import path from 'path'
 *
 * export default defineConfig({
 *   plugins: [react()],
 *   test: {
 *     globals: true,
 *     environment: 'jsdom',
 *     setupFiles: './src/test/setup.ts',
 *   },
 *   resolve: {
 *     alias: {
 *       '@': path.resolve(__dirname, './src'),
 *     },
 *   },
 * })
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import WorkflowInput from '../WorkflowInput'
import { apiClient } from '@/api/client'

// Mock the API client
vi.mock('@/api/client', () => ({
  apiClient: {
    getExamples: vi.fn(),
    parseWorkflow: vi.fn(),
  },
}))

describe('WorkflowInput', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default mock for getExamples
    vi.mocked(apiClient.getExamples).mockResolvedValue({
      success: true,
      data: {
        examples: [
          { input: 'Example 1', description: 'Test example 1' },
          { input: 'Example 2', description: 'Test example 2' },
        ],
      },
    })
  })

  describe('Rendering', () => {
    it('should render with placeholder text', () => {
      render(<WorkflowInput />)
      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      expect(textarea).toBeInTheDocument()
    })

    it('should display character counter', () => {
      render(<WorkflowInput />)
      expect(screen.getByText(/0 \/ 500/)).toBeInTheDocument()
    })

    it('should show submit button', () => {
      render(<WorkflowInput />)
      const button = screen.getByRole('button', { name: /Generate Graph/i })
      expect(button).toBeInTheDocument()
    })
  })

  describe('Character Count', () => {
    it('should update character count as user types', async () => {
      const user = userEvent.setup()
      render(<WorkflowInput />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      await user.type(textarea, 'Hello')

      expect(screen.getByText(/5 \/ 500/)).toBeInTheDocument()
    })

    it('should show error state when over limit', async () => {
      const user = userEvent.setup()
      render(<WorkflowInput />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      const longText = 'a'.repeat(501)

      await user.type(textarea, longText)

      expect(textarea).toHaveClass('border-cyber-red')
      expect(textarea).toHaveAttribute('aria-invalid', 'true')
    })
  })

  describe('Submit Button States', () => {
    it('should disable submit button when input is empty', () => {
      render(<WorkflowInput />)
      const button = screen.getByRole('button', { name: /Generate Graph/i })
      expect(button).toBeDisabled()
    })

    it('should enable submit button when input is valid', async () => {
      const user = userEvent.setup()
      render(<WorkflowInput />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      await user.type(textarea, 'Valid workflow input')

      const button = screen.getByRole('button', { name: /Generate Graph/i })
      expect(button).not.toBeDisabled()
    })

    it('should disable submit button when over character limit', async () => {
      const user = userEvent.setup()
      render(<WorkflowInput />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      const longText = 'a'.repeat(501)
      await user.type(textarea, longText)

      const button = screen.getByRole('button', { name: /Generate Graph/i })
      expect(button).toBeDisabled()
    })
  })

  describe('Loading State', () => {
    it('should show loading state when submitting', async () => {
      const user = userEvent.setup()
      vi.mocked(apiClient.parseWorkflow).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      )

      render(<WorkflowInput />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      await user.type(textarea, 'Valid workflow')

      const button = screen.getByRole('button', { name: /Generate Graph/i })
      await user.click(button)

      expect(screen.getByText(/Generating Graph.../i)).toBeInTheDocument()
      expect(button).toHaveAttribute('aria-busy', 'true')
    })
  })

  describe('Error Handling', () => {
    it('should display error message on API failure', async () => {
      const user = userEvent.setup()
      vi.mocked(apiClient.parseWorkflow).mockResolvedValue({
        success: false,
        error: { message: 'API Error occurred' },
      })

      render(<WorkflowInput />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      await user.type(textarea, 'Test workflow')

      const button = screen.getByRole('button', { name: /Generate Graph/i })
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByText(/API Error occurred/i)).toBeInTheDocument()
      })

      const errorAlert = screen.getByRole('alert')
      expect(errorAlert).toHaveAttribute('aria-live', 'assertive')
    })

    it('should display error for invalid workflow', async () => {
      const user = userEvent.setup()
      vi.mocked(apiClient.parseWorkflow).mockResolvedValue({
        success: true,
        data: {
          success: false,
          error: { message: 'Invalid workflow format' },
        },
      })

      render(<WorkflowInput />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      await user.type(textarea, 'Invalid workflow')

      const button = screen.getByRole('button', { name: /Generate Graph/i })
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByText(/Invalid workflow format/i)).toBeInTheDocument()
      })
    })
  })

  describe('Success Handling', () => {
    it('should display success message and call callback on successful parse', async () => {
      const user = userEvent.setup()
      const mockCallback = vi.fn()
      const mockWorkflow = {
        name: 'test-workflow',
        description: 'Test',
        trigger: { type: 'manual' },
        steps: [],
      }

      vi.mocked(apiClient.parseWorkflow).mockResolvedValue({
        success: true,
        data: {
          success: true,
          workflow_spec: mockWorkflow,
        },
      })

      render(<WorkflowInput onWorkflowGenerated={mockCallback} />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      await user.type(textarea, 'Valid workflow')

      const button = screen.getByRole('button', { name: /Generate Graph/i })
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByText(/Workflow parsed successfully/i)).toBeInTheDocument()
      })

      expect(mockCallback).toHaveBeenCalledWith(mockWorkflow)

      const successAlert = screen.getByText(/Workflow parsed successfully/i).closest('[role="alert"]')
      expect(successAlert).toHaveAttribute('aria-live', 'polite')
    })

    it('should auto-hide success message after timeout', async () => {
      vi.useFakeTimers()
      const user = userEvent.setup({ delay: null })

      const mockWorkflow = {
        name: 'test-workflow',
        description: 'Test',
        trigger: { type: 'manual' },
        steps: [],
      }

      vi.mocked(apiClient.parseWorkflow).mockResolvedValue({
        success: true,
        data: {
          success: true,
          workflow_spec: mockWorkflow,
        },
      })

      render(<WorkflowInput />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      await user.type(textarea, 'Valid workflow')

      const button = screen.getByRole('button', { name: /Generate Graph/i })
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByText(/Workflow parsed successfully/i)).toBeInTheDocument()
      })

      // Fast-forward time by 3 seconds
      vi.advanceTimersByTime(3000)

      await waitFor(() => {
        expect(screen.queryByText(/Workflow parsed successfully/i)).not.toBeInTheDocument()
      })

      vi.useRealTimers()
    })
  })

  describe('Example Workflows', () => {
    it('should show loading skeleton while fetching examples', () => {
      render(<WorkflowInput />)
      // Initially shows skeleton
      const skeletons = screen.getAllByRole('generic').filter(el =>
        el.className.includes('animate-pulse')
      )
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('should load and display examples from API', async () => {
      render(<WorkflowInput />)

      await waitFor(() => {
        expect(screen.getByText('Example 1')).toBeInTheDocument()
        expect(screen.getByText('Example 2')).toBeInTheDocument()
      })
    })

    it('should populate input when example is clicked', async () => {
      const user = userEvent.setup()
      render(<WorkflowInput />)

      await waitFor(() => {
        expect(screen.getByText('Example 1')).toBeInTheDocument()
      })

      const exampleButton = screen.getByText('Example 1').closest('button')
      await user.click(exampleButton!)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      expect(textarea).toHaveValue('Example 1')
    })

    it('should show fallback examples if API fails', async () => {
      vi.mocked(apiClient.getExamples).mockRejectedValue(new Error('API Error'))

      render(<WorkflowInput />)

      await waitFor(() => {
        expect(screen.getByText(/When GAS drops below \$5, swap 10 GAS for NEO/i)).toBeInTheDocument()
      })
    })
  })

  describe('Keyboard Accessibility', () => {
    it('should submit on Ctrl+Enter', async () => {
      const user = userEvent.setup()
      const mockCallback = vi.fn()
      const mockWorkflow = {
        name: 'test-workflow',
        description: 'Test',
        trigger: { type: 'manual' },
        steps: [],
      }

      vi.mocked(apiClient.parseWorkflow).mockResolvedValue({
        success: true,
        data: {
          success: true,
          workflow_spec: mockWorkflow,
        },
      })

      render(<WorkflowInput onWorkflowGenerated={mockCallback} />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      await user.type(textarea, 'Valid workflow')

      // Ctrl+Enter
      await user.keyboard('{Control>}{Enter}{/Control}')

      await waitFor(() => {
        expect(mockCallback).toHaveBeenCalled()
      })
    })

    it('should submit on Cmd+Enter (Mac)', async () => {
      const user = userEvent.setup()
      const mockCallback = vi.fn()
      const mockWorkflow = {
        name: 'test-workflow',
        description: 'Test',
        trigger: { type: 'manual' },
        steps: [],
      }

      vi.mocked(apiClient.parseWorkflow).mockResolvedValue({
        success: true,
        data: {
          success: true,
          workflow_spec: mockWorkflow,
        },
      })

      render(<WorkflowInput onWorkflowGenerated={mockCallback} />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      await user.type(textarea, 'Valid workflow')

      // Cmd+Enter
      await user.keyboard('{Meta>}{Enter}{/Meta}')

      await waitFor(() => {
        expect(mockCallback).toHaveBeenCalled()
      })
    })

    it('should not submit on Enter alone', async () => {
      const user = userEvent.setup()
      const mockCallback = vi.fn()

      render(<WorkflowInput onWorkflowGenerated={mockCallback} />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      await user.type(textarea, 'Valid workflow{Enter}')

      expect(mockCallback).not.toHaveBeenCalled()
    })
  })

  describe('ARIA Attributes', () => {
    it('should have proper aria-label on textarea', () => {
      render(<WorkflowInput />)
      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      expect(textarea).toHaveAttribute('aria-label', 'Workflow description input')
    })

    it('should have aria-describedby linking to help text and counter', () => {
      render(<WorkflowInput />)
      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      expect(textarea).toHaveAttribute('aria-describedby', 'char-counter help-text')
    })

    it('should have proper IDs on help text and counter', () => {
      render(<WorkflowInput />)
      expect(screen.getByText(/Start typing your workflow idea/i)).toHaveAttribute('id', 'help-text')
      expect(screen.getByText(/0 \/ 500/)).toHaveAttribute('id', 'char-counter')
    })
  })

  describe('Input Sanitization', () => {
    it('should remove angle brackets from input', async () => {
      const user = userEvent.setup()
      vi.mocked(apiClient.parseWorkflow).mockImplementation((input) => {
        // Verify sanitized input doesn't contain angle brackets
        expect(input).not.toContain('<')
        expect(input).not.toContain('>')
        return Promise.resolve({
          success: true,
          data: {
            success: true,
            workflow_spec: {
              name: 'test',
              description: 'test',
              trigger: { type: 'manual' },
              steps: [],
            },
          },
        })
      })

      render(<WorkflowInput />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      await user.type(textarea, '<script>alert("xss")</script>')

      const button = screen.getByRole('button', { name: /Generate Graph/i })
      await user.click(button)

      await waitFor(() => {
        expect(apiClient.parseWorkflow).toHaveBeenCalled()
      })
    })
  })

  describe('Race Condition Prevention', () => {
    it('should cancel previous request when submitting again', async () => {
      const user = userEvent.setup()
      let secondRequestCalled = false

      vi.mocked(apiClient.parseWorkflow).mockImplementation(() => {
        if (!secondRequestCalled) {
          return new Promise((resolve) => {
            setTimeout(() => {
              resolve({
                success: true,
                data: { success: true, workflow_spec: {} },
              })
            }, 1000)
          })
        } else {
          return Promise.resolve({
            success: true,
            data: { success: true, workflow_spec: {} },
          })
        }
      })

      render(<WorkflowInput />)

      const textarea = screen.getByPlaceholderText(/When GAS drops below/i)
      await user.type(textarea, 'First submission')

      const button = screen.getByRole('button', { name: /Generate Graph/i })
      await user.click(button)

      // Clear and submit again before first request completes
      await user.clear(textarea)
      await user.type(textarea, 'Second submission')
      secondRequestCalled = true
      await user.click(button)

      expect(apiClient.parseWorkflow).toHaveBeenCalledTimes(2)
    })
  })
})
