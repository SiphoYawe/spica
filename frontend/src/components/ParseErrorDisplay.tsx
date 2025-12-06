"use client"

import { useState, useEffect, useCallback } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { AlertCircle, RefreshCw, Lightbulb, HelpCircle } from 'lucide-react'
import type { ParseErrorResponse } from '@/types/api'
import { apiClient } from '@/api/client'

interface ParseErrorDisplayProps {
  error: ParseErrorResponse['error']
  onRetry?: () => void
}

export default function ParseErrorDisplay({ error, onRetry }: ParseErrorDisplayProps) {
  const [capabilities, setCapabilities] = useState<{
    tokens: string[]
    actions: string[]
    triggers: string[]
  } | null>(null)

  const [showSuggestions, setShowSuggestions] = useState(false)

  // Memoize toggle function to prevent recreation on every render
  const toggleSuggestions = useCallback(() => {
    setShowSuggestions(prev => !prev)
  }, [])

  // Fetch capabilities for contextual help
  useEffect(() => {
    const loadCapabilities = async () => {
      try {
        const response = await apiClient.getCapabilities()
        if (response.success && response.data) {
          setCapabilities({
            tokens: response.data.supported_tokens || [],
            actions: response.data.supported_actions || [],
            triggers: response.data.supported_triggers || [],
          })
        }
      } catch (err) {
        console.warn('Failed to load capabilities for error display:', err)
      }
    }

    // Only load capabilities for parse/validation errors
    if (error.code === 'PARSE_ERROR' || error.code === 'VALIDATION_ERROR') {
      loadCapabilities()
    }
  }, [error.code])

  // Determine error category and presentation
  const errorCategory = categorizeError(error)

  return (
    <Alert variant="destructive" className="animate-slide-up" aria-live="assertive">
      <AlertCircle className="h-5 w-5" />
      <AlertDescription className="ml-2 space-y-3">
        {/* Main Error Message */}
        <div>
          <strong className="font-semibold">Oops!</strong> {errorCategory.friendlyMessage}
        </div>

        {/* Contextual Help - Unsupported Token */}
        {errorCategory.type === 'unsupported_token' && capabilities?.tokens && capabilities.tokens.length > 0 && (
          <div className="space-y-2 pt-2">
            <div className="flex items-center gap-2 text-xs opacity-90">
              <Lightbulb className="h-4 w-4" />
              <span>Supported tokens:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {capabilities.tokens.map((token, index) => (
                <Badge key={`token-${token}-${index}`} variant="success" className="font-mono">
                  {token}
                </Badge>
              ))}
            </div>
            <p className="text-xs opacity-80 mt-2">
              Try using one of these tokens in your workflow description.
            </p>
          </div>
        )}

        {/* Contextual Help - Unsupported Action */}
        {errorCategory.type === 'unsupported_action' && capabilities?.actions && capabilities.actions.length > 0 && (
          <div className="space-y-2 pt-2">
            <div className="flex items-center gap-2 text-xs opacity-90">
              <Lightbulb className="h-4 w-4" />
              <span>Supported actions:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {capabilities.actions.map((action, index) => (
                <Badge key={`action-${action}-${index}`} variant="success" className="font-mono">
                  {action}
                </Badge>
              ))}
            </div>
            <p className="text-xs opacity-80 mt-2">
              Try using one of these actions in your workflow description.
            </p>
          </div>
        )}

        {/* Contextual Help - Ambiguous Input */}
        {errorCategory.type === 'ambiguous' && (
          <div className="space-y-2 pt-2 border-t border-cyber-red/30 pt-3">
            <div className="flex items-center gap-2 text-xs opacity-90">
              <HelpCircle className="h-4 w-4" />
              <span>Clarification needed:</span>
            </div>
            <p className="text-xs opacity-90">
              {errorCategory.clarificationHint || 'Please be more specific about what you want to do.'}
            </p>
            {errorCategory.suggestions && errorCategory.suggestions.length > 0 && (
              <div className="space-y-1 mt-2">
                <p className="text-xs font-semibold">Try one of these:</p>
                <ul className="list-disc list-inside text-xs opacity-80 space-y-1">
                  {errorCategory.suggestions.map((suggestion, idx) => (
                    <li key={idx}>{suggestion}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Contextual Help - Validation Error */}
        {errorCategory.type === 'validation' && (
          <div className="pt-2">
            <p className="text-xs opacity-80">
              {errorCategory.hint || 'Please check your input and try again.'}
            </p>
          </div>
        )}

        {/* Network Error - Retry Button */}
        {errorCategory.type === 'network' && error.retry && onRetry && (
          <div className="pt-2 border-t border-cyber-red/30 pt-3">
            <Button
              onClick={onRetry}
              variant="outline"
              size="sm"
              className="gap-2 border-cyber-red/30 hover:bg-cyber-red/10"
              aria-label="Retry request"
            >
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              <span>Retry</span>
            </Button>
          </div>
        )}

        {/* Show Examples Toggle */}
        {(errorCategory.type === 'parse' || errorCategory.type === 'ambiguous') && (
          <div className="pt-2 border-t border-cyber-red/30 pt-3">
            <button
              onClick={toggleSuggestions}
              className="text-xs underline hover:no-underline opacity-80 hover:opacity-100 transition-opacity"
              aria-expanded={showSuggestions}
              aria-controls="example-workflows"
            >
              {showSuggestions ? 'Hide examples' : 'Show example workflows'}
            </button>
            {showSuggestions && (
              <div id="example-workflows" className="mt-3 space-y-2 text-xs opacity-90">
                <p className="font-semibold">Example formats:</p>
                <ul className="list-disc list-inside space-y-1 opacity-80">
                  <li>&quot;When GAS price drops below $5, swap 10 GAS for NEO&quot;</li>
                  <li>&quot;Every day at 9 AM, stake 50% of my bNEO&quot;</li>
                  <li>&quot;If NEO rises above $20, transfer 5 NEO to address NXX...&quot;</li>
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Technical Details (Optional, for debugging) */}
        {error.details && process.env.NODE_ENV === 'development' && (
          <details className="pt-2 border-t border-cyber-red/30 mt-2">
            <summary className="text-xs cursor-pointer opacity-60 hover:opacity-100">
              Technical details
            </summary>
            <pre className="mt-2 text-xs opacity-60 overflow-x-auto p-2 bg-black/20 rounded">
              {error.details}
            </pre>
          </details>
        )}
      </AlertDescription>
    </Alert>
  )
}

/**
 * Categorize error for better user messaging
 */
interface ErrorCategory {
  type: 'unsupported_token' | 'unsupported_action' | 'ambiguous' | 'validation' | 'network' | 'parse' | 'unknown'
  friendlyMessage: string
  hint?: string
  clarificationHint?: string
  suggestions?: string[]
}

function categorizeError(error: ParseErrorResponse['error']): ErrorCategory {
  const code = (typeof error.code === 'string' ? error.code : 'UNKNOWN_ERROR').toUpperCase()
  const message = typeof error.message === 'string' ? error.message.toLowerCase() : ''
  const details = typeof error.details === 'string' ? error.details.toLowerCase() : ''

  // Network errors
  if (code === 'NETWORK_ERROR' || code.startsWith('HTTP_')) {
    return {
      type: 'network',
      friendlyMessage: 'Unable to connect to the server. Please check your connection.',
      hint: 'Click retry to try again.',
    }
  }

  // Helper to get friendly message
  const friendlyMessage = typeof error.message === 'string' ? error.message : 'An error occurred'

  // Unsupported token detection
  if (
    message.includes('unsupported token') ||
    message.includes('unknown token') ||
    details.includes('token')
  ) {
    return {
      type: 'unsupported_token',
      friendlyMessage,
      hint: 'We only support specific tokens on the Neo N3 blockchain.',
    }
  }

  // Unsupported action detection
  if (
    message.includes('unsupported action') ||
    message.includes('unknown action') ||
    details.includes('action')
  ) {
    return {
      type: 'unsupported_action',
      friendlyMessage,
      hint: 'Try using one of the supported actions.',
    }
  }

  // Ambiguous input detection
  if (
    message.includes('ambiguous') ||
    message.includes('unclear') ||
    message.includes('clarify') ||
    message.includes('multiple interpretations')
  ) {
    return {
      type: 'ambiguous',
      friendlyMessage,
      clarificationHint: 'Please be more specific about what you want to do.',
      suggestions: extractSuggestions(typeof error.details === 'string' ? error.details : undefined),
    }
  }

  // Validation errors
  if (code === 'VALIDATION_ERROR') {
    let hint = 'Please check your input and try again.'

    if (message.includes('too long')) {
      hint = 'Your input is too long. Please keep it under 500 characters.'
    } else if (message.includes('empty') || message.includes('required')) {
      hint = 'Please enter a workflow description.'
    }

    return {
      type: 'validation',
      friendlyMessage,
      hint,
    }
  }

  // Parse errors
  if (code === 'PARSE_ERROR') {
    return {
      type: 'parse',
      friendlyMessage: friendlyMessage || "We couldn't understand your workflow description.",
      hint: 'Try rephrasing your workflow or check the examples below.',
    }
  }

  // Generic error
  return {
    type: 'unknown',
    friendlyMessage: friendlyMessage || 'Something went wrong. Please try again.',
    hint: 'If this problem persists, please contact support.',
  }
}

/**
 * Extract suggestions from error details
 */
function extractSuggestions(details?: string): string[] | undefined {
  if (!details) return undefined

  // Look for common suggestion patterns
  const suggestions: string[] = []

  // Pattern: "Did you mean: X or Y?"
  const didYouMeanMatch = details.match(/did you mean[:\s]+(.+)/i)
  if (didYouMeanMatch) {
    const options = didYouMeanMatch[1].split(/\s+or\s+|\s*,\s*/).filter(Boolean)
    suggestions.push(...options.map(opt => opt.trim().replace(/[?.]$/, '')))
  }

  // Pattern: "Possible interpretations: X, Y, Z"
  const interpretationsMatch = details.match(/possible interpretations?[:\s]+(.+)/i)
  if (interpretationsMatch) {
    const options = interpretationsMatch[1].split(/\s*,\s*/).filter(Boolean)
    suggestions.push(...options.map(opt => opt.trim().replace(/[?.]$/, '')))
  }

  return suggestions.length > 0 ? suggestions : undefined
}
