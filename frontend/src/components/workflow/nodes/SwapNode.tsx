import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { ArrowLeftRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SwapNodeData {
  label: string;
  icon?: string;
  status?: string;
  from_token?: string;
  to_token?: string;
  amount?: number;
  min_output?: number;
}

function SwapNode({ data, selected }: NodeProps<SwapNodeData>) {
  // Format display text
  let displayText = data.label;
  if (data.from_token && data.to_token && data.amount !== undefined) {
    displayText = `${data.amount} ${data.from_token} → ${data.to_token}`;
  }

  // Issue #6 fix: Keyboard navigation handler
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      // Node selection is handled by ReactFlow
    }
  };

  return (
    <div
      role="article"
      aria-label={`Swap node: ${displayText}`}
      aria-selected={selected}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      className={cn(
        'min-w-[220px] rounded-lg border-2 bg-card shadow-lg transition-all duration-200',
        selected
          ? 'border-cyber-green shadow-[0_0_20px_rgba(16,185,129,0.4)]'
          : 'border-card-border hover:border-cyber-green/50'
      )}
    >
      {/* Status Indicator Bar */}
      <div className="h-1 w-full rounded-t-md bg-gradient-to-r from-cyber-green to-emerald-400 opacity-60" />

      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="h-3 w-3 border-2 border-cyber-green bg-card"
      />

      {/* Node Content */}
      <div className="p-4">
        {/* Header */}
        <div className="mb-3 flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-cyber-green/20 to-emerald-400/20">
            <ArrowLeftRight className="h-4 w-4 text-cyber-green" />
          </div>
          <div className="flex-1">
            <div className="text-xs font-medium uppercase tracking-wider text-muted">
              Swap
            </div>
          </div>
        </div>

        {/* Main Label */}
        <div className="space-y-2">
          <div className="text-sm font-semibold text-foreground">{displayText}</div>

          {/* Token Details */}
          {data.from_token && data.to_token && (
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center rounded-full border border-emerald-500/30 bg-emerald-950/30 px-2 py-0.5 text-xs font-medium text-emerald-400">
                {data.from_token}
              </span>
              <ArrowLeftRight className="h-3 w-3 text-muted" />
              <span className="inline-flex items-center rounded-full border border-emerald-500/30 bg-emerald-950/30 px-2 py-0.5 text-xs font-medium text-emerald-400">
                {data.to_token}
              </span>
            </div>
          )}

          {/* Minimum Output */}
          {data.min_output !== undefined && (
            <div className="text-xs text-muted-foreground">
              Min: {data.min_output} {data.to_token}
            </div>
          )}
        </div>
      </div>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="h-3 w-3 border-2 border-cyber-green bg-card"
      />
    </div>
  );
}

export default memo(SwapNode);
