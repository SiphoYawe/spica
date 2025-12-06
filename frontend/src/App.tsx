import { useState, useEffect } from 'react'
import type { Node } from 'reactflow'
import { apiClient } from './api/client'
import type { HealthResponse, WorkflowSpec, GraphNode, GraphEdge } from './types/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { cn } from '@/lib/utils'
import WalletBalance from './components/WalletBalance'
import WorkflowInput from './components/WorkflowInput'
import WorkflowGraph from './components/workflow/WorkflowGraph'
import ParameterPanel from './components/workflow/ParameterPanel'
import ErrorBoundary from './components/ErrorBoundary'

function App() {
  const [backendStatus, setBackendStatus] = useState<string>('checking...')
  const [backendVersion, setBackendVersion] = useState<string>('')
  const [workflowSpec, setWorkflowSpec] = useState<WorkflowSpec | null>(null)
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([])
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([])
  const [workflowId, setWorkflowId] = useState<string | null>(null)
  const [isGeneratingGraph, setIsGeneratingGraph] = useState(false)
  const [graphError, setGraphError] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)

  useEffect(() => {
    const checkBackend = async () => {
      const response = await apiClient.get<HealthResponse>('/')
      if (response.success && response.data) {
        setBackendStatus(response.data.status)
        setBackendVersion(response.data.version)
      } else {
        setBackendStatus('disconnected')
      }
    }

    checkBackend()
  }, [])

  const handleWorkflowGenerated = async (workflow: WorkflowSpec) => {
    setWorkflowSpec(workflow)
    setGraphError(null)
    setIsGeneratingGraph(true)
    console.log('Workflow generated:', workflow)

    try {
      // Call the generate endpoint to get graph nodes and edges
      const response = await apiClient.generateWorkflow(workflow)

      if (response.success && response.data) {
        const data = response.data

        if (data.success && data.nodes && data.edges) {
          // Successfully generated graph - map to GraphNode type
          // Issue #5 fix: Proper type validation instead of unsafe assertions
          const nodes: GraphNode[] = data.nodes.map(node => {
            const icon = typeof node.data.icon === 'string' ? node.data.icon : '';
            const status = typeof node.data.status === 'string' ? node.data.status : undefined;

            return {
              ...node,
              data: {
                ...node.data,
                label: node.label,
                icon,
                status,
              }
            };
          });
          setGraphNodes(nodes)
          setGraphEdges(data.edges as GraphEdge[])
          setWorkflowId(data.workflow_id || null)
          console.log('Graph generated:', {
            workflowId: data.workflow_id,
            nodes: data.nodes.length,
            edges: data.edges.length,
          })
        } else if (data.error) {
          // Backend returned an error
          setGraphError(data.error.message || 'Failed to generate workflow graph')
          console.error('Graph generation error:', data.error)
        }
      } else {
        // API call failed
        setGraphError(response.error?.message || 'Failed to generate workflow graph')
        console.error('API error:', response.error)
      }
    } catch (error) {
      setGraphError('Unexpected error generating workflow graph')
      console.error('Graph generation exception:', error)
    } finally {
      setIsGeneratingGraph(false)
    }
  }

  const handleNodeClick = (node: Node) => {
    setSelectedNode(node)
  }

  const handleParameterSave = async (nodeId: string, data: Record<string, unknown>) => {
    // Update the node in the graph
    const updatedNodes = graphNodes.map((node) => {
      if (node.id === nodeId) {
        return {
          ...node,
          data: {
            ...node.data,
            ...data,
          },
        }
      }
      return node
    })

    setGraphNodes(updatedNodes)

    // Optionally: Save to backend immediately
    if (workflowId) {
      try {
        await apiClient.updateWorkflow(workflowId, {
          nodes: updatedNodes,
          edges: graphEdges,
        })
        console.log('Workflow updated successfully')
      } catch (error) {
        console.error('Failed to save workflow:', error)
      }
    }
  }

  const handleParameterPanelClose = () => {
    setSelectedNode(null)
  }

  return (
    <ErrorBoundary>
      <div className="mx-auto max-w-7xl p-8">
        <header className="mb-12 text-center">
          <h1 className="mb-2 text-5xl font-bold bg-gradient-to-r from-accent to-accent-secondary bg-clip-text text-transparent">
            Spica
          </h1>
          <p className="text-lg text-muted">
            AI-Powered DeFi Workflow Builder for Neo N3
          </p>
        </header>

        <main className="mx-auto grid max-w-5xl gap-8">
          {/* Workflow Input - Primary Feature */}
          <WorkflowInput onWorkflowGenerated={handleWorkflowGenerated} />

          {/* Graph Generation Loading State */}
          {isGeneratingGraph && (
            <Card className="border-cyber-blue/20 bg-gradient-to-br from-card to-darker-bg animate-pulse">
              <CardContent className="p-8 text-center">
                <div className="text-muted-foreground">Generating workflow graph...</div>
              </CardContent>
            </Card>
          )}

          {/* Graph Generation Error */}
          {graphError && !isGeneratingGraph && (
            <Alert variant="destructive">
              <AlertDescription>{graphError}</AlertDescription>
            </Alert>
          )}

          {/* Workflow Graph - Visual Display */}
          {graphNodes.length > 0 && !isGeneratingGraph && (
            <div className="animate-slide-up">
              <WorkflowGraph
                nodes={graphNodes}
                edges={graphEdges}
                workflowName={workflowSpec?.name}
                workflowDescription={workflowSpec?.description}
                onNodeClick={handleNodeClick}
              />
            </div>
          )}

          {/* Parameter Panel - Shown when node is selected */}
          {selectedNode && (
            <ParameterPanel
              node={selectedNode}
              onClose={handleParameterPanelClose}
              onSave={handleParameterSave}
            />
          )}

          {/* Workflow Spec Details (Collapsed) - Shows after generation */}
          {workflowSpec && graphNodes.length > 0 && (
            <Card className="border-card-border bg-card animate-slide-up">
              <CardHeader>
                <CardTitle className="text-base">Workflow Details</CardTitle>
                <CardDescription className="text-sm">
                  {workflowId && (
                    <span className="font-mono text-xs text-muted-foreground">
                      ID: {workflowId}
                    </span>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 rounded-lg border border-card-border bg-darker-bg/50 p-4 font-mono text-sm">
                  <div>
                    <span className="text-muted-foreground">Name:</span>{' '}
                    <span className="text-cyber-green">{workflowSpec.name}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Trigger:</span>{' '}
                    <span className="text-cyber-blue">{workflowSpec.trigger.type}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Steps:</span>{' '}
                    <span className="text-foreground">{workflowSpec.steps.length} action(s)</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Demo Wallet Balance */}
          <WalletBalance autoRefresh={true} refreshInterval={30000} />

          {/* System Status - Moved to bottom */}
          <Card className="border-card-border bg-card p-8 text-left">
            <CardHeader className="p-0 pb-6">
              <CardTitle>System Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 p-0">
              <div className="flex items-center justify-between border-b border-card-border/50 py-3">
                <span className="font-medium text-muted">Backend:</span>
                <span
                  className={cn(
                    "text-sm font-semibold uppercase",
                    backendStatus === 'ok' ? 'text-success' : 'text-error'
                  )}
                >
                  {backendStatus}
                </span>
              </div>
              {backendVersion && (
                <div className="flex items-center justify-between py-3">
                  <span className="font-medium text-muted">Version:</span>
                  <span>{backendVersion}</span>
                </div>
              )}
            </CardContent>
          </Card>
        </main>
      </div>
    </ErrorBoundary>
  )
}

export default App
