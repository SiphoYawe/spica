import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Lock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StakeNodeData {
  label: string;
  icon?: string;
  status?: string;
  token?: string;
  amount?: number;
  pool?: string;
  duration?: string;
}

function StakeNode({ data, selected }: NodeProps<StakeNodeData>) {
  // Format display text
  let displayText = data.label;
  if (data.token && data.amount !== undefined) {
    displayText = `Stake ${data.amount} ${data.token}`;
    if (data.pool) {
      displayText += ` in ${data.pool}`;
    }
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
      aria-label={`Stake node: ${displayText}`}
      aria-selected={selected}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      className={cn(
        'min-w-[220px] rounded-lg border-2 bg-card shadow-lg transition-all duration-200',
        selected
          ? 'border-cyber-purple shadow-[0_0_20px_rgba(168,85,247,0.4)]'
          : 'border-card-border hover:border-cyber-purple/50'
      )}
    >
      {/* Status Indicator Bar */}
      <div className="h-1 w-full rounded-t-md bg-gradient-to-r from-cyber-purple to-purple-400 opacity-60" />

      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="h-3 w-3 border-2 border-cyber-purple bg-card"
      />

      {/* Node Content */}
      <div className="p-4">
        {/* Header */}
        <div className="mb-3 flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-cyber-purple/20 to-purple-400/20">
            <Lock className="h-4 w-4 text-cyber-purple" />
          </div>
          <div className="flex-1">
            <div className="text-xs font-medium uppercase tracking-wider text-muted">
              Stake
            </div>
          </div>
        </div>

        {/* Main Label */}
        <div className="space-y-2">
          <div className="text-sm font-semibold text-foreground">{displayText}</div>

          {/* Token & Amount Details */}
          {data.token && data.amount !== undefined && (
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center rounded-full border border-purple-500/30 bg-purple-950/30 px-2 py-0.5 text-xs font-medium text-purple-400">
                {data.amount} {data.token}
              </span>
            </div>
          )}

          {/* Pool Details */}
          {data.pool && (
            <div className="text-xs text-muted-foreground">
              Pool: {data.pool}
            </div>
          )}

          {/* Duration */}
          {data.duration && (
            <div className="text-xs text-muted-foreground">
              Duration: {data.duration}
            </div>
          )}
        </div>
      </div>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="h-3 w-3 border-2 border-cyber-purple bg-card"
      />
    </div>
  );
}

export default memo(StakeNode);
