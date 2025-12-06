import ReactFlow, {
  type Node,
  type Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  Panel,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { nodeTypes } from './nodes';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface WorkflowGraphProps {
  nodes: Node[];
  edges: Edge[];
  workflowName?: string;
  workflowDescription?: string;
  className?: string;
  onNodeClick?: (node: Node) => void;
}

// Move defaultEdgeOptions outside component to prevent re-creation on every render
// Issue #3 fix: Memoization for defaultEdgeOptions
// Issue #1 fix: Using CSS classes instead of inline styles
const defaultEdgeOptions = {
  animated: true,
};

export default function WorkflowGraph({
  nodes: initialNodes,
  edges: initialEdges,
  workflowName,
  workflowDescription,
  className,
  onNodeClick,
}: WorkflowGraphProps) {
  // Issue #9 fix: Use props directly since graph is read-only
  // Removed unused state variables, using initialNodes/initialEdges with state hooks
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  // Handle node click
  const handleNodeClick = (_event: React.MouseEvent, node: Node) => {
    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  return (
    <Card
      className={cn(
        'relative overflow-hidden border-cyber-blue/20 bg-gradient-to-br from-card to-darker-bg shadow-[0_0_24px_rgba(0,217,255,0.1)]',
        className
      )}
    >
      {/* Top gradient border */}
      <div className="absolute left-0 top-0 h-1 w-full bg-gradient-to-r from-cyber-blue via-cyber-purple to-cyber-green opacity-60" />

      {/* Graph Container */}
      <div className="h-[600px] w-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          nodeTypes={nodeTypes}
          defaultEdgeOptions={defaultEdgeOptions}
          fitView
          fitViewOptions={{
            padding: 0.2,
            minZoom: 0.5,
            maxZoom: 1.5,
          }}
          minZoom={0.1}
          maxZoom={2}
          attributionPosition="bottom-right"
          className="bg-darker-bg"
        >
          {/* Background pattern */}
          <Background
            variant={BackgroundVariant.Dots}
            gap={16}
            size={1}
            color="rgba(100, 116, 139, 0.2)"
          />

          {/* Controls (zoom in/out, fit view) */}
          <Controls
            className="rounded-lg border border-card-border bg-card/95 shadow-lg"
            showInteractive={false}
          />

          {/* MiniMap for navigation */}
          <MiniMap
            className="rounded-lg border border-card-border bg-card/95 shadow-lg"
            nodeColor={(node) => {
              switch (node.type) {
                case 'trigger':
                  return 'rgba(0, 217, 255, 0.8)';
                case 'swap':
                  return 'rgba(16, 185, 129, 0.8)';
                case 'stake':
                  return 'rgba(168, 85, 247, 0.8)';
                case 'transfer':
                  return 'rgba(251, 191, 36, 0.8)';
                default:
                  return 'rgba(100, 116, 139, 0.8)';
              }
            }}
            maskColor="rgba(0, 0, 0, 0.6)"
          />

          {/* Info Panel */}
          {(workflowName || workflowDescription) && (
            <Panel position="top-left" className="space-y-2">
              <div className="rounded-lg border border-card-border bg-card/95 p-4 shadow-lg backdrop-blur-sm">
                {workflowName && (
                  <h3 className="mb-1 font-semibold text-foreground">{workflowName}</h3>
                )}
                {workflowDescription && (
                  <p className="text-sm text-muted-foreground">{workflowDescription}</p>
                )}
                <div className="mt-2 flex items-center gap-2">
                  <Badge variant="secondary" className="text-xs">
                    {nodes.length} {nodes.length === 1 ? 'node' : 'nodes'}
                  </Badge>
                  <Badge variant="secondary" className="text-xs">
                    {edges.length} {edges.length === 1 ? 'edge' : 'edges'}
                  </Badge>
                </div>
              </div>
            </Panel>
          )}
        </ReactFlow>
      </div>
    </Card>
  );
}
