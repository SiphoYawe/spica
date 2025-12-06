import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Send } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TransferNodeData {
  label: string;
  icon?: string;
  status?: string;
  token?: string;
  amount?: number;
  to_address?: string;
  recipient?: string;
}

function TransferNode({ data, selected }: NodeProps<TransferNodeData>) {
  // Format display text
  let displayText = data.label;
  if (data.token && data.amount !== undefined) {
    displayText = `Send ${data.amount} ${data.token}`;
  }

  // Truncate address for display
  const formatAddress = (address: string) => {
    if (address.length > 12) {
      return `${address.slice(0, 6)}...${address.slice(-4)}`;
    }
    return address;
  };

  const recipient = data.to_address || data.recipient;

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
      aria-label={`Transfer node: ${displayText}`}
      aria-selected={selected}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      className={cn(
        'min-w-[220px] rounded-lg border-2 bg-card shadow-lg transition-all duration-200',
        selected
          ? 'border-amber-400 shadow-[0_0_20px_rgba(251,191,36,0.4)]'
          : 'border-card-border hover:border-amber-400/50'
      )}
    >
      {/* Status Indicator Bar */}
      <div className="h-1 w-full rounded-t-md bg-gradient-to-r from-amber-400 to-orange-400 opacity-60" />

      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="h-3 w-3 border-2 border-amber-400 bg-card"
      />

      {/* Node Content */}
      <div className="p-4">
        {/* Header */}
        <div className="mb-3 flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-amber-400/20 to-orange-400/20">
            <Send className="h-4 w-4 text-amber-400" />
          </div>
          <div className="flex-1">
            <div className="text-xs font-medium uppercase tracking-wider text-muted">
              Transfer
            </div>
          </div>
        </div>

        {/* Main Label */}
        <div className="space-y-2">
          <div className="text-sm font-semibold text-foreground">{displayText}</div>

          {/* Token & Amount Details */}
          {data.token && data.amount !== undefined && (
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center rounded-full border border-amber-500/30 bg-amber-950/30 px-2 py-0.5 text-xs font-medium text-amber-400">
                {data.amount} {data.token}
              </span>
            </div>
          )}

          {/* Recipient Address */}
          {recipient && (
            <div className="text-xs text-muted-foreground">
              To: <span className="font-mono">{formatAddress(recipient)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="h-3 w-3 border-2 border-amber-400 bg-card"
      />
    </div>
  );
}

export default memo(TransferNode);
