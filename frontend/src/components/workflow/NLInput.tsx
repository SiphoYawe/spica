"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import { useWorkflowStore, type GraphNode } from "@/stores";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Sparkles,
  Loader2,
  Lightbulb,
  ChevronDown,
  X,
} from "lucide-react";
import { apiClient } from "@/api/client";
import ParseErrorDisplay from "@/components/ParseErrorDisplay";
import type { ParseErrorResponse } from "@/types/api";

// Example workflow prompts - simple, reliable examples that parse correctly
const examplePrompts = [
  // Simple time-based swap
  "Every Monday at 9am, swap 10 GAS to NEO",
  // Price trigger with swap
  "When NEO rises above $20, swap 50% of my NEO to GAS",
  // Daily staking
  "Every day at 9am, stake 25% of my NEO",
  // Price-triggered accumulation
  "When GAS drops below $5, swap 100 GAS to NEO",
];

export function NLInput() {
  const [input, setInput] = useState("");
  const [showExamples, setShowExamples] = useState(false);
  const [localError, setLocalError] = useState<ParseErrorResponse["error"] | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    isParsing,
    setIsParsing,
    setWorkflowSpec,
    setNodes,
    setEdges,
    setWorkflowId,
    setIsGenerating,
    setError,
    clearErrors,
  } = useWorkflowStore();

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSubmit = useCallback(async () => {
    if (!input.trim() || isParsing) return;

    clearErrors();
    setLocalError(null);
    setIsParsing(true);

    try {
      // Step 1: Parse the natural language input
      const parseResponse = await apiClient.parseWorkflow(input);

      // Check for API-level errors
      if (!parseResponse.success && parseResponse.error) {
        setLocalError({
          code: parseResponse.error.code,
          message: parseResponse.error.message,
          details: parseResponse.error.details,
          retry: parseResponse.error.code === "NETWORK_ERROR",
        });
        return;
      }

      // Check for parse errors in the response data
      if (parseResponse.data?.error) {
        setLocalError(parseResponse.data.error);
        return;
      }

      if (parseResponse.data?.workflow_spec) {
        setWorkflowSpec(parseResponse.data.workflow_spec);

        // Step 2: Generate the visual workflow
        setIsGenerating(true);
        const generateResponse = await apiClient.generateWorkflow(
          parseResponse.data.workflow_spec
        );

        // Check for generation errors
        if (!generateResponse.success && generateResponse.error) {
          setLocalError({
            code: generateResponse.error.code,
            message: generateResponse.error.message,
            details: generateResponse.error.details,
            retry: generateResponse.error.code === "NETWORK_ERROR",
          });
          return;
        }

        // Check for generation errors in response data
        if (generateResponse.data?.error) {
          setLocalError(generateResponse.data.error);
          return;
        }

        if (generateResponse.data) {
          // Map API nodes to GraphNode type
          // Backend now includes all parameters in node.data
          const nodes = (generateResponse.data.nodes || []).map((node) => {
            const nodeLabel = typeof node.label === "string" ? node.label : "";
            const dataLabel = typeof node.data?.label === "string" ? node.data.label : "";

            return {
              id: node.id,
              type: node.type,
              position: node.position,
              data: {
                ...node.data,  // Includes all parameters (token, amount, percentage, etc.)
                label: nodeLabel || dataLabel || "Untitled",
              },
            };
          });
          setNodes(nodes as GraphNode[]);
          setEdges(generateResponse.data.edges || []);
          setWorkflowId(generateResponse.data.workflow_id || null);
        }
      } else {
        // No workflow spec and no error - generic failure
        setLocalError({
          code: "PARSE_ERROR",
          message: "Could not understand the workflow description. Please try rephrasing.",
          retry: false,
        });
      }
    } catch (err) {
      console.error("Workflow generation error:", err);
      setLocalError({
        code: "UNKNOWN_ERROR",
        message: err instanceof Error ? err.message : "An unexpected error occurred",
        details: err instanceof Error ? err.stack : undefined,
        retry: true,
      });
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to generate workflow");
      }
    } finally {
      setIsParsing(false);
      setIsGenerating(false);
    }
  }, [
    input,
    isParsing,
    clearErrors,
    setIsParsing,
    setWorkflowSpec,
    setIsGenerating,
    setNodes,
    setEdges,
    setWorkflowId,
    setError,
  ]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleExampleClick = (example: string) => {
    setInput(example);
    setShowExamples(false);
    textareaRef.current?.focus();
  };

  const handleClear = () => {
    setInput("");
    setLocalError(null);
    textareaRef.current?.focus();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Clear error when user starts typing
    if (localError) {
      setLocalError(null);
    }
  };

  return (
    <TooltipProvider delayDuration={0}>
      <div className="relative w-full max-w-3xl mx-auto">
        {/* Main input container */}
        <div
          className={cn(
            "relative rounded-xl border transition-all duration-200",
            "bg-zinc-800 border-zinc-700/60",
            "hover:border-zinc-600/80",
            "focus-within:border-spica/40 focus-within:shadow-[0_0_20px_rgba(0,255,72,0.08)]"
          )}
        >
          {/* Input area */}
          <div className="flex items-start gap-3 p-3">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-spica/10 border border-spica/20">
              <Sparkles className="h-4 w-4 text-spica" />
            </div>

            <div className="flex-1 min-w-0">
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Describe your DeFi workflow in plain English..."
                className={cn(
                  "min-h-[40px] max-h-[120px] resize-none border-0 bg-transparent p-0",
                  "text-sm text-zinc-100 placeholder:text-zinc-500",
                  "focus-visible:ring-0 focus-visible:ring-offset-0"
                )}
                disabled={isParsing}
              />
            </div>

            {/* Clear button */}
            {input && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 flex-shrink-0 text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50"
                    onClick={handleClear}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Clear</TooltipContent>
              </Tooltip>
            )}
          </div>

          {/* Action bar */}
          <div className="flex items-center justify-between border-t border-zinc-800/50 px-3 py-2">
            {/* Examples dropdown */}
            <Button
              variant="ghost"
              size="sm"
              className="h-7 gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50"
              onClick={() => setShowExamples(!showExamples)}
            >
              <Lightbulb className="h-3.5 w-3.5" />
              Examples
              <ChevronDown
                className={cn(
                  "h-3 w-3 transition-transform",
                  showExamples && "rotate-180"
                )}
              />
            </Button>

            {/* Submit button */}
            <Button
              variant="cyber"
              size="sm"
              className="h-7 gap-2"
              onClick={handleSubmit}
              disabled={!input.trim() || isParsing}
            >
              {isParsing ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5" />
                  Generate Workflow
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Examples dropdown panel */}
        {showExamples && (
          <div className="absolute left-0 right-0 top-full z-10 mt-2 rounded-lg border border-zinc-800/60 bg-zinc-900/95 backdrop-blur-sm p-2 shadow-xl animate-fade-in-up">
            <div className="space-y-1">
              {examplePrompts.map((example, index) => (
                <button
                  key={index}
                  className={cn(
                    "w-full rounded-md px-3 py-2 text-left text-sm text-zinc-300 transition-colors",
                    "hover:bg-zinc-800/60 hover:text-zinc-100"
                  )}
                  onClick={() => handleExampleClick(example)}
                >
                  <span className="text-zinc-600">&quot;</span>
                  {example}
                  <span className="text-zinc-600">&quot;</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Keyboard hint */}
        <div className="mt-3 text-center">
          <span className="text-xs text-zinc-600">
            Press <kbd className="rounded border border-zinc-800 bg-zinc-900/80 px-1.5 py-0.5 text-xs font-medium text-zinc-400">Enter</kbd> to generate,{" "}
            <kbd className="rounded border border-zinc-800 bg-zinc-900/80 px-1.5 py-0.5 text-xs font-medium text-zinc-400">Shift+Enter</kbd> for new line
          </span>
        </div>

        {/* Error display */}
        {localError && (
          <div className="mt-4">
            <ParseErrorDisplay
              error={localError}
              onRetry={localError.retry ? handleSubmit : undefined}
            />
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
