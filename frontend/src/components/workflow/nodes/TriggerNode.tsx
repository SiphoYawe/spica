import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import { Clock, DollarSign } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TriggerNodeData {
  label: string;
  icon?: string;
  status?: string;
  type?: string;
  token?: string;
  operator?: string;
  value?: number;
  interval?: string;
  time?: string;
}

function TriggerNode({ data, selected }: NodeProps<TriggerNodeData>) {
  const isPriceCondition = data.type === 'price' || data.token;

  const Icon = isPriceCondition ? DollarSign : Clock;

  // Format display text
  let displayText = data.label;
  if (data.token && data.operator && data.value !== undefined) {
    displayText = `${data.token} ${data.operator} $${data.value.toFixed(2)}`;
  } else if (data.interval || data.time) {
    displayText = data.interval ? `Every ${data.interval}` : data.time || data.label;
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
      aria-label={`Trigger node: ${displayText}`}
      aria-selected={selected}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      className={cn(
        'min-w-[220px] rounded-lg border-2 bg-card shadow-lg transition-all duration-200',
        selected
          ? 'border-cyber-blue shadow-[0_0_20px_rgba(0,217,255,0.4)]'
          : 'border-card-border hover:border-cyber-blue/50'
      )}
    >
      {/* Status Indicator Bar */}
      <div className="h-1 w-full rounded-t-md bg-gradient-to-r from-cyber-purple via-cyber-blue to-cyber-green opacity-60" />

      {/* Node Content */}
      <div className="p-4">
        {/* Header */}
        <div className="mb-3 flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-cyber-blue/20 to-cyber-purple/20">
            <Icon className="h-4 w-4 text-cyber-blue" />
          </div>
          <div className="flex-1">
            <div className="text-xs font-medium uppercase tracking-wider text-muted">
              Trigger
            </div>
          </div>
        </div>

        {/* Main Label */}
        <div className="space-y-2">
          <div className="text-sm font-semibold text-foreground">{displayText}</div>

          {/* Additional Details */}
          {data.type && (
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center rounded-full border border-card-border bg-darker-bg px-2 py-0.5 text-xs font-medium text-muted-foreground">
                {data.type}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="h-3 w-3 border-2 border-cyber-blue bg-card"
      />
    </div>
  );
}

export default memo(TriggerNode);
