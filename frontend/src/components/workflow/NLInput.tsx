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

// Example workflow prompts
const examplePrompts = [
  "When NEO price drops below $10, swap 50 NEO to GAS",
  "Every day at 9am, stake 100 GAS in Flamingo pool",
  "If GAS > $5, transfer 25 GAS to wallet N3...",
  "When ETH price hits $4000, swap all ETH to USDC",
];

export function NLInput() {
  const [input, setInput] = useState("");
  const [showExamples, setShowExamples] = useState(false);
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
    setIsParsing(true);

    try {
      // Step 1: Parse the natural language input
      const parseResponse = await apiClient.parseWorkflow(input);

      if (parseResponse.data?.workflow_spec) {
        setWorkflowSpec(parseResponse.data.workflow_spec);

        // Step 2: Generate the visual workflow
        setIsGenerating(true);
        const generateResponse = await apiClient.generateWorkflow(
          parseResponse.data.workflow_spec
        );

        if (generateResponse.data) {
          // Map API nodes to GraphNode type with explicit typing
          const nodes = (generateResponse.data.nodes || []).map((node) => {
            const nodeLabel = typeof node.label === "string" ? node.label : "";
            const dataLabel = typeof node.data?.label === "string" ? node.data.label : "";
            const icon = typeof node.data?.icon === "string" ? node.data.icon : undefined;
            const status = typeof node.data?.status === "string" ? node.data.status : undefined;

            return {
              id: node.id,
              type: node.type,
              position: node.position,
              data: {
                ...node.data,
                label: nodeLabel || dataLabel || "Untitled",
                icon,
                status,
              },
            };
          });
          setNodes(nodes as GraphNode[]);
          setEdges(generateResponse.data.edges || []);
          setWorkflowId(generateResponse.data.workflow_id || null);
        }
      }
    } catch (err) {
      console.error("Workflow generation error:", err);
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
    textareaRef.current?.focus();
  };

  return (
    <TooltipProvider delayDuration={0}>
      <div className="relative w-full max-w-3xl mx-auto">
        {/* Main input container */}
        <div
          className={cn(
            "relative rounded-xl border bg-card/95 backdrop-blur-sm transition-all duration-200",
            "border-border hover:border-muted-foreground/30",
            "focus-within:border-spica/50 focus-within:shadow-[0_0_20px_rgba(0,255,72,0.1)]"
          )}
        >
          {/* Input area */}
          <div className="flex items-start gap-3 p-3">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-spica/10">
              <Sparkles className="h-4 w-4 text-spica" />
            </div>

            <div className="flex-1 min-w-0">
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Describe your DeFi workflow in plain English..."
                className={cn(
                  "min-h-[40px] max-h-[120px] resize-none border-0 bg-transparent p-0",
                  "text-sm placeholder:text-muted-foreground/60",
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
                    className="h-8 w-8 flex-shrink-0"
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
          <div className="flex items-center justify-between border-t border-border/50 px-3 py-2">
            {/* Examples dropdown */}
            <Button
              variant="ghost"
              size="sm"
              className="h-7 gap-1.5 text-xs text-muted-foreground"
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
          <div className="absolute left-0 right-0 top-full z-10 mt-2 rounded-lg border border-border bg-card p-2 shadow-lg animate-fade-in-up">
            <div className="space-y-1">
              {examplePrompts.map((example, index) => (
                <button
                  key={index}
                  className={cn(
                    "w-full rounded-md px-3 py-2 text-left text-sm transition-colors",
                    "hover:bg-accent hover:text-accent-foreground"
                  )}
                  onClick={() => handleExampleClick(example)}
                >
                  <span className="text-muted-foreground">&quot;</span>
                  {example}
                  <span className="text-muted-foreground">&quot;</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Keyboard hint */}
        <div className="mt-2 text-center">
          <span className="text-[10px] text-muted-foreground/60">
            Press <kbd className="rounded border border-border bg-muted px-1 py-0.5 text-[10px]">Enter</kbd> to generate,{" "}
            <kbd className="rounded border border-border bg-muted px-1 py-0.5 text-[10px]">Shift+Enter</kbd> for new line
          </span>
        </div>
      </div>
    </TooltipProvider>
  );
}
