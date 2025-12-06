# ParseErrorDisplay Component

**Purpose:** Display contextual, user-friendly error messages for workflow parsing failures

---

## Component Signature

```typescript
interface ParseErrorDisplayProps {
  error: ParseErrorResponse['error']  // Structured error from API
  onRetry?: () => void                // Optional retry callback
}

export default function ParseErrorDisplay({
  error,
  onRetry
}: ParseErrorDisplayProps)
```

---

## Props

### `error` (required)
Structured error object from the parse API response.

**Type:**
```typescript
{
  code: string        // Error code (e.g., "PARSE_ERROR", "NETWORK_ERROR")
  message: string     // User-friendly error message
  details?: string    // Optional technical details
  retry?: boolean     // Whether retry might help
}
```

**Example:**
```typescript
{
  code: "PARSE_ERROR",
  message: "Unsupported token 'BITCOIN'",
  details: "Token BITCOIN is not supported on Neo N3",
  retry: false
}
```

### `onRetry` (optional)
Callback function to retry the failed operation. Only displayed when `error.retry === true`.

**Type:** `() => void`

**Example:**
```typescript
const handleRetry = () => {
  // Re-submit the parse request
  parseWorkflow(userInput)
}

<ParseErrorDisplay error={error} onRetry={handleRetry} />
```

---

## Error Categories

The component automatically categorizes errors and displays appropriate UI:

### 1. Unsupported Token
**Detection:** Message contains "unsupported token" or "unknown token"

**UI:**
- Error message
- "Supported tokens:" label
- Badges for each supported token (GAS, NEO, bNEO)
- Hint text

**Capabilities Fetch:** Yes (from `/api/v1/parse/capabilities`)

---

### 2. Unsupported Action
**Detection:** Message contains "unsupported action" or "unknown action"

**UI:**
- Error message
- "Supported actions:" label
- Badges for each supported action (swap, stake, transfer)
- Hint text

**Capabilities Fetch:** Yes

---

### 3. Ambiguous Input
**Detection:** Message contains "ambiguous", "unclear", "clarify", "multiple interpretations"

**UI:**
- Error message
- "Clarification needed:" section
- Extracted suggestions (parsed from error.details)
- Example workflows toggle

**Capabilities Fetch:** No

---

### 4. Validation Error
**Detection:** `error.code === "VALIDATION_ERROR"`

**UI:**
- Error message
- Specific hint based on message:
  - "too long" → "Keep it under 500 characters"
  - "empty" / "required" → "Please enter a workflow description"

**Capabilities Fetch:** Yes (for general context)

---

### 5. Network Error
**Detection:** `error.code === "NETWORK_ERROR"` or `error.code.startsWith("HTTP_")`

**UI:**
- User-friendly connection message
- Retry button (if `onRetry` provided)

**Capabilities Fetch:** No

---

### 6. Parse Error
**Detection:** `error.code === "PARSE_ERROR"` (not matching other patterns)

**UI:**
- Error message
- General parsing hint
- Example workflows toggle

**Capabilities Fetch:** Yes

---

### 7. Unknown Error
**Detection:** Fallback for unrecognized errors

**UI:**
- Generic error message
- Contact support hint

**Capabilities Fetch:** No

---

## State Management

### Internal State

#### `capabilities`
```typescript
{
  tokens: string[]     // Supported tokens (e.g., ["GAS", "NEO", "bNEO"])
  actions: string[]    // Supported actions (e.g., ["swap", "stake", "transfer"])
  triggers: string[]   // Supported triggers (e.g., ["price", "time"])
} | null
```

**Source:** `GET /api/v1/parse/capabilities`

**Loading Strategy:**
- Lazy load when error type requires it
- Only fetches for PARSE_ERROR or VALIDATION_ERROR
- Graceful degradation on fetch failure

#### `showSuggestions`
```typescript
boolean  // Toggle for example workflows section
```

**Default:** `false`

**User Action:** Click "Show example workflows" / "Hide examples"

---

## Effects

### Capabilities Loading Effect
```typescript
useEffect(() => {
  const loadCapabilities = async () => {
    // Fetch from API
    // Update state
    // Handle errors gracefully
  }

  // Only load for parse/validation errors
  if (error.code === 'PARSE_ERROR' || error.code === 'VALIDATION_ERROR') {
    loadCapabilities()
  }
}, [error.code])
```

**Dependency:** `error.code`

**Performance:** Parallel with render, non-blocking

---

## UI Sections

### 1. Main Error Message
Always displayed.

```tsx
<div>
  <strong>Oops!</strong> {errorCategory.friendlyMessage}
</div>
```

---

### 2. Contextual Help (Conditional)

#### Unsupported Token
```tsx
<div>
  <div className="flex items-center gap-2">
    <Lightbulb className="h-4 w-4" />
    <span>Supported tokens:</span>
  </div>
  <div className="flex flex-wrap gap-2">
    {capabilities.tokens.map(token => (
      <Badge variant="success">{token}</Badge>
    ))}
  </div>
  <p>Try using one of these tokens...</p>
</div>
```

#### Unsupported Action
Similar to token, but for actions.

#### Ambiguous Input
```tsx
<div>
  <div className="flex items-center gap-2">
    <HelpCircle className="h-4 w-4" />
    <span>Clarification needed:</span>
  </div>
  <p>{errorCategory.clarificationHint}</p>
  {errorCategory.suggestions && (
    <ul>
      {errorCategory.suggestions.map(s => (
        <li>{s}</li>
      ))}
    </ul>
  )}
</div>
```

---

### 3. Action Buttons (Conditional)

#### Retry Button (Network Errors)
```tsx
<Button onClick={onRetry} variant="outline" size="sm">
  <RefreshCw className="h-4 w-4" />
  <span>Retry</span>
</Button>
```

**Condition:** `error.retry === true` AND `onRetry !== undefined`

---

### 4. Example Workflows Toggle (Conditional)
```tsx
<button onClick={() => setShowSuggestions(!showSuggestions)}>
  {showSuggestions ? 'Hide examples' : 'Show example workflows'}
</button>

{showSuggestions && (
  <ul>
    <li>"When GAS price drops below $5, swap 10 GAS for NEO"</li>
    <li>"Every day at 9 AM, stake 50% of my bNEO"</li>
    <li>"If NEO rises above $20, transfer 5 NEO to address NXX..."</li>
  </ul>
)}
```

**Condition:** `errorCategory.type === 'parse' || errorCategory.type === 'ambiguous'`

---

### 5. Technical Details (Dev Mode Only)
```tsx
{error.details && import.meta.env.DEV && (
  <details>
    <summary>Technical details</summary>
    <pre>{error.details}</pre>
  </details>
)}
```

**Condition:** `import.meta.env.DEV === true`

---

## Styling

All styles use **Tailwind CSS** and **shadcn/ui** components (per CLAUDE.md).

### Color Scheme
- **Error Red:** `border-cyber-red/30`, `bg-cyber-red/10`, `text-cyber-red`
- **Success Green:** `variant="success"` badges
- **Accent Blue:** Icons and highlights

### Layout
- `space-y-3` - Vertical spacing between sections
- `border-t border-cyber-red/30 pt-3` - Section dividers
- `flex flex-wrap gap-2` - Badge layout
- `text-xs opacity-80` - Secondary text

### Components Used
- `Alert` (variant: destructive)
- `AlertDescription`
- `Badge` (variants: success, outline)
- `Button` (variant: outline, size: sm)
- Icons: `AlertCircle`, `RefreshCw`, `Lightbulb`, `HelpCircle`

---

## Accessibility

### ARIA Attributes
- `role="alert"` on Alert component
- `aria-live="assertive"` on Alert (errors are important)

### Keyboard Navigation
- All interactive elements keyboard accessible
- Retry button focusable and activatable

### Screen Readers
- Descriptive error messages
- Icon context provided by surrounding text
- Details element with proper summary

---

## Usage Examples

### Basic Parse Error
```tsx
import ParseErrorDisplay from '@/components/ParseErrorDisplay'

const error = {
  code: 'PARSE_ERROR',
  message: 'Could not parse workflow',
  retry: false
}

<ParseErrorDisplay error={error} />
```

---

### Unsupported Token
```tsx
const error = {
  code: 'PARSE_ERROR',
  message: 'Unsupported token "BITCOIN"',
  details: 'Token BITCOIN is not supported',
  retry: false
}

<ParseErrorDisplay error={error} />
```

**Result:** Shows GAS, NEO, bNEO badges

---

### Network Error with Retry
```tsx
const error = {
  code: 'NETWORK_ERROR',
  message: 'Connection failed',
  retry: true
}

const handleRetry = () => {
  // Retry logic
}

<ParseErrorDisplay error={error} onRetry={handleRetry} />
```

**Result:** Shows retry button

---

### Ambiguous Input
```tsx
const error = {
  code: 'PARSE_ERROR',
  message: 'Ambiguous input',
  details: 'Did you mean: swap or transfer?',
  retry: false
}

<ParseErrorDisplay error={error} />
```

**Result:** Shows clarification with suggestions "swap" and "transfer"

---

## Integration with WorkflowInput

```tsx
// WorkflowInput.tsx
import ParseErrorDisplay from '@/components/ParseErrorDisplay'

const [error, setError] = useState<ParseErrorResponse['error'] | null>(null)

// On API error
setError({
  code: response.error.code,
  message: response.error.message,
  details: response.error.details,
  retry: response.error.code === 'NETWORK_ERROR'
})

// Render
{error && (
  <ParseErrorDisplay
    error={error}
    onRetry={error.retry ? handleSubmit : undefined}
  />
)}
```

---

## Helper Functions

### `categorizeError(error: ParseErrorResponse['error']): ErrorCategory`
**Purpose:** Analyze error and determine category + friendly messaging

**Returns:**
```typescript
{
  type: 'unsupported_token' | 'unsupported_action' | 'ambiguous' |
        'validation' | 'network' | 'parse' | 'unknown'
  friendlyMessage: string
  hint?: string
  clarificationHint?: string
  suggestions?: string[]
}
```

**Logic:**
1. Check error code (NETWORK_ERROR, VALIDATION_ERROR, etc.)
2. Pattern match error message
3. Extract suggestions from details
4. Return appropriate category with friendly messaging

---

### `extractSuggestions(details?: string): string[] | undefined`
**Purpose:** Parse error details to extract suggestions

**Patterns Detected:**
- "Did you mean: X or Y?"
- "Possible interpretations: X, Y, Z"

**Returns:** Array of suggestion strings or undefined

---

## Performance Considerations

1. **Lazy Capabilities Loading**
   - Only fetches when error type requires it
   - Avoids unnecessary API calls

2. **Parallel Rendering**
   - Error displays immediately
   - Capabilities load in background
   - No blocking

3. **Conditional Rendering**
   - Only renders relevant sections
   - Minimizes DOM size

4. **Memoization Opportunities** (future)
   - Could memoize `categorizeError`
   - Could memoize capabilities per session

---

## Error Handling

### Capabilities Fetch Failure
**Behavior:** Graceful degradation

```typescript
try {
  const response = await apiClient.getCapabilities()
  // ...
} catch (err) {
  console.warn('Failed to load capabilities:', err)
  // Component still renders without capabilities
}
```

**User Impact:** None - error still displays, just without token/action badges

---

## Testing

### Unit Tests Location
`/src/components/__tests__/ParseErrorDisplay.test.tsx`

### Test Coverage
- ✅ All 7 error categories
- ✅ Capabilities loading
- ✅ User interactions (retry, toggle)
- ✅ Accessibility
- ✅ Technical details visibility
- ✅ User-friendly messaging

### Example Test
```typescript
it('displays unsupported token error with available tokens', async () => {
  vi.mocked(apiClient.getCapabilities).mockResolvedValue({
    success: true,
    data: { supported_tokens: ['GAS', 'NEO', 'bNEO'], ... }
  })

  const error = {
    code: 'PARSE_ERROR',
    message: 'Unsupported token "BITCOIN"',
    retry: false
  }

  render(<ParseErrorDisplay error={error} />)

  await waitFor(() => {
    expect(screen.getByText('Supported tokens:')).toBeInTheDocument()
  })

  expect(screen.getByText('GAS')).toBeInTheDocument()
  expect(screen.getByText('NEO')).toBeInTheDocument()
  expect(screen.getByText('bNEO')).toBeInTheDocument()
})
```

---

## Future Enhancements

1. **Inline Fixes**
   - "Fix it for me" button
   - Auto-replace unsupported token with suggestion

2. **Smart Suggestions**
   - Fuzzy matching for typos
   - Learn from user corrections

3. **Error Analytics**
   - Track common errors
   - Improve parser based on data

4. **Contextual Examples**
   - Show relevant examples based on error type
   - Highlight differences

---

## Dependencies

### Internal
- `@/components/ui/alert` - Alert component
- `@/components/ui/badge` - Badge component
- `@/components/ui/button` - Button component
- `@/api/client` - API client for capabilities
- `@/types/api` - Type definitions

### External
- `lucide-react` - Icons
- `react` - Hooks (useState, useEffect)

---

## Browser Support

Same as parent application (modern browsers with ES6+ support).

---

**Component Version:** 1.0.0
**Last Updated:** 2025-12-06
**Author:** Dev Agent (BMAD Framework)
