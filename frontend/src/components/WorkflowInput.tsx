import { useState, useEffect, useCallback, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { apiClient } from '@/api/client'
import type { WorkflowSpec, ExampleWorkflow, ParseErrorResponse } from '@/types/api'
import { Loader2, Sparkles, Zap, CheckCircle2 } from 'lucide-react'
import ParseErrorDisplay from '@/components/ParseErrorDisplay'

const MAX_CHARS = 500
const SUCCESS_MESSAGE_TIMEOUT = 3000

interface WorkflowInputProps {
  onWorkflowGenerated?: (workflow: WorkflowSpec) => void
}

export default function WorkflowInput({ onWorkflowGenerated }: WorkflowInputProps) {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<ParseErrorResponse['error'] | null>(null)
  const [examples, setExamples] = useState<ExampleWorkflow[]>([])
  const [isLoadingExamples, setIsLoadingExamples] = useState(true)
  const [showSuccess, setShowSuccess] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Load examples on mount with error handling
  useEffect(() => {
    const loadExamples = async () => {
      try {
        setIsLoadingExamples(true)
        const response = await apiClient.getExamples()
        if (response.success && response.data) {
          setExamples(response.data.examples.slice(0, 4))
        } else {
          console.warn('Failed to load examples, using fallback examples')
        }
      } catch (err) {
        console.warn('Error loading examples, using fallback examples:', err)
      } finally {
        setIsLoadingExamples(false)
      }
    }
    loadExamples()
  }, [])

  // Cleanup timeout for success message
  useEffect(() => {
    if (showSuccess) {
      const timeoutId = setTimeout(() => setShowSuccess(false), SUCCESS_MESSAGE_TIMEOUT)
      return () => clearTimeout(timeoutId)
    }
  }, [showSuccess])

  // Cleanup abort controller on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  // Sanitize user input
  const sanitizeInput = (text: string): string => {
    // Remove potentially dangerous characters
    return text.replace(/[<>]/g, '').slice(0, MAX_CHARS)
  }

  const handleSubmit = useCallback(async () => {
    if (!input.trim() || input.length > MAX_CHARS || isLoading) return

    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // Create new abort controller
    const controller = new AbortController()
    abortControllerRef.current = controller

    // Sanitize input before submission
    const sanitizedInput = sanitizeInput(input.trim())

    setIsLoading(true)
    setError(null)
    setShowSuccess(false)

    try {
      const response = await apiClient.parseWorkflow(sanitizedInput)

      // Check if request was aborted
      if (controller.signal.aborted) return

      if (response.success && response.data) {
        if (response.data.success && response.data.workflow_spec) {
          // Success case
          setShowSuccess(true)
          onWorkflowGenerated?.(response.data.workflow_spec)
        } else if (response.data.error) {
          // API returned structured error
          setError(response.data.error)
        }
      } else if (response.error) {
        // Network or fetch error - convert to structured format
        setError({
          code: response.error.code,
          message: response.error.message,
          details: response.error.details,
          retry: response.error.code === 'NETWORK_ERROR' || response.error.code.startsWith('HTTP_'),
        })
      }
    } catch {
      if (!controller.signal.aborted) {
        setError({
          code: 'UNKNOWN_ERROR',
          message: 'An unexpected error occurred',
          retry: false,
        })
      }
    } finally {
      if (!controller.signal.aborted) {
        setIsLoading(false)
        abortControllerRef.current = null
      }
    }
  }, [input, isLoading, onWorkflowGenerated])

  const handleExampleClick = useCallback((exampleInput: string) => {
    setInput(exampleInput)
    setError(null)
    setShowSuccess(false)
  }, [])

  const charCount = input.length
  const isOverLimit = charCount > MAX_CHARS
  const canSubmit = input.trim().length > 0 && !isOverLimit && !isLoading

  return (
    <Card className="relative overflow-hidden border-cyber-green/20 bg-gradient-to-br from-card to-darker-bg shadow-[0_0_24px_rgba(0,255,65,0.1)]">
      {/* Holographic accent line */}
      <div className="absolute left-0 top-0 h-1 w-full bg-gradient-to-r from-cyber-green via-cyber-blue to-cyber-purple opacity-60" />

      <CardHeader className="space-y-2 pb-6">
        <div className="flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-cyber-green" />
          <CardTitle className="font-display text-2xl tracking-wide">
            Describe Your Workflow
          </CardTitle>
        </div>
        <CardDescription className="text-base text-muted-foreground">
          Tell us what you want to automate in plain English. Our AI will build it for you.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Main Input Area */}
        <div className="relative space-y-3">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && canSubmit) {
                e.preventDefault()
                handleSubmit()
              }
            }}
            placeholder="When GAS drops below $5, swap 10 GAS for NEO..."
            className={`min-h-[140px] font-mono text-base leading-relaxed ${
              isOverLimit ? 'border-cyber-red focus-visible:ring-cyber-red' : ''
            }`}
            disabled={isLoading}
            maxLength={MAX_CHARS + 50} // Soft limit
            aria-label="Workflow description input"
            aria-describedby="char-counter help-text"
            aria-invalid={isOverLimit}
          />

          {/* Character Counter */}
          <div className="flex items-center justify-between text-xs">
            <span id="help-text" className="text-muted-foreground">
              {input.trim().length === 0 ? 'Start typing your workflow idea...' : 'Looking good! Press Ctrl+Enter to submit.'}
            </span>
            <span
              id="char-counter"
              className={`font-mono font-semibold ${
                isOverLimit
                  ? 'text-cyber-red'
                  : charCount > MAX_CHARS * 0.9
                  ? 'text-cyber-blue'
                  : 'text-muted-foreground'
              }`}
            >
              {charCount} / {MAX_CHARS}
            </span>
          </div>
        </div>

        {/* Generate Button */}
        <Button
          onClick={handleSubmit}
          disabled={!canSubmit}
          variant="cyber"
          size="lg"
          className="w-full gap-3 text-base"
          aria-busy={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Generating Graph...</span>
            </>
          ) : (
            <>
              <Zap className="h-5 w-5" />
              <span>Generate Graph</span>
            </>
          )}
        </Button>

        {/* Error Display */}
        {error && (
          <ParseErrorDisplay
            error={error}
            onRetry={error.retry ? handleSubmit : undefined}
          />
        )}

        {/* Success Display */}
        {showSuccess && (
          <Alert variant="success" className="animate-slide-up" aria-live="polite">
            <CheckCircle2 className="h-5 w-5" />
            <AlertDescription className="ml-2">
              <strong className="font-semibold">Success!</strong> Workflow parsed successfully.
            </AlertDescription>
          </Alert>
        )}

        {/* Example Prompts */}
        <div className="space-y-3 border-t border-card-border pt-6">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
            <Sparkles className="h-4 w-4" />
            Example Workflows
          </h3>

          <div className="grid gap-2">
            {isLoadingExamples ? (
              // Loading skeleton
              <div className="space-y-2">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 rounded-lg border border-card-border bg-card/50 p-3"
                  >
                    <div className="h-4 w-4 mt-0.5 rounded bg-muted-foreground/20 animate-pulse" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-muted-foreground/20 rounded animate-pulse" style={{ width: `${60 + i * 10}%` }} />
                      <div className="h-3 bg-muted-foreground/20 rounded animate-pulse" style={{ width: `${40 + i * 5}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : examples.length > 0 ? (
              examples.map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => handleExampleClick(example.input)}
                  disabled={isLoading}
                  className="group flex items-start gap-3 rounded-lg border border-card-border bg-card/50 p-3 text-left text-sm transition-all hover:border-cyber-green/40 hover:bg-card hover:shadow-[0_0_12px_rgba(0,255,65,0.1)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Zap className="h-4 w-4 mt-0.5 flex-shrink-0 text-cyber-green opacity-60 transition-opacity group-hover:opacity-100" />
                  <div className="space-y-1">
                    <p className="font-mono leading-relaxed text-foreground">
                      {example.input}
                    </p>
                    {example.description && (
                      <p className="text-xs text-muted-foreground">
                        {example.description}
                      </p>
                    )}
                  </div>
                </button>
              ))
            ) : (
              // Fallback examples
              <div className="space-y-2">
                <ExampleButton onClick={handleExampleClick} disabled={isLoading}>
                  When GAS drops below $5, swap 10 GAS for NEO
                </ExampleButton>
                <ExampleButton onClick={handleExampleClick} disabled={isLoading}>
                  Every day at 9 AM, stake 50% of my bNEO
                </ExampleButton>
                <ExampleButton onClick={handleExampleClick} disabled={isLoading}>
                  If NEO price rises above $20, transfer 5 NEO to NXXXabc123...
                </ExampleButton>
                <ExampleButton onClick={handleExampleClick} disabled={isLoading}>
                  Swap 100 GAS to bNEO and stake all of it
                </ExampleButton>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// Helper component for example buttons
function ExampleButton({
  children,
  onClick,
  disabled
}: {
  children: string
  onClick: (text: string) => void
  disabled?: boolean
}) {
  return (
    <button
      onClick={() => onClick(children)}
      disabled={disabled}
      className="group flex items-start gap-3 rounded-lg border border-card-border bg-card/50 p-3 text-left text-sm transition-all hover:border-cyber-green/40 hover:bg-card hover:shadow-[0_0_12px_rgba(0,255,65,0.1)] disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <Zap className="h-4 w-4 mt-0.5 flex-shrink-0 text-cyber-green opacity-60 transition-opacity group-hover:opacity-100" />
      <p className="font-mono leading-relaxed text-foreground">
        {children}
      </p>
    </button>
  )
}
