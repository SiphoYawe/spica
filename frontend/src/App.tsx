import { useState, useEffect } from 'react'
import type { Node } from 'reactflow'
import { apiClient } from './api/client'
import type { HealthResponse, WorkflowSpec, GraphNode, GraphEdge } from './types/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import WalletBalance from './components/WalletBalance'
import WorkflowInput from './components/WorkflowInput'
import WorkflowGraph from './components/workflow/WorkflowGraph'
import ParameterPanel from './components/workflow/ParameterPanel'
import PaymentModal from './components/PaymentModal'
import DemoModeBanner from './components/DemoModeBanner'
import ErrorBoundary from './components/ErrorBoundary'
import { Rocket, CheckCircle2 } from 'lucide-react'

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
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false)
  const [deploySuccess, setDeploySuccess] = useState(false)
  const [deployError, setDeployError] = useState<string | null>(null)
  const [isDemoMode, setIsDemoMode] = useState(false)

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

    const checkDemoMode = async () => {
      const demoModeStatus = await apiClient.getDemoMode()
      setIsDemoMode(demoModeStatus.demo_mode)
    }

    checkBackend()
    checkDemoMode()
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

  const handleDeployClick = () => {
    setDeployError(null)
    setDeploySuccess(false)
    setIsPaymentModalOpen(true)
  }

  const handlePaymentSuccess = (deployedWorkflowId: string) => {
    setDeploySuccess(true)
    setDeployError(null)
    console.log('Workflow deployed successfully:', deployedWorkflowId)
    // Auto-hide success message after 5 seconds
    setTimeout(() => setDeploySuccess(false), 5000)
  }

  const handlePaymentError = (error: string) => {
    setDeployError(error)
    setDeploySuccess(false)
  }

  return (
    <ErrorBoundary>
      {/* Demo Mode Banner - Sticky at top */}
      {isDemoMode && <DemoModeBanner />}

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

          {/* Deploy Button - Shows after graph is generated */}
          {graphNodes.length > 0 && !isGeneratingGraph && workflowId && (
            <div className="animate-slide-up">
              <Card className="border-cyber-green/20 bg-gradient-to-br from-card to-darker-bg shadow-[0_0_24px_rgba(0,255,65,0.1)]">
                <CardContent className="p-6">
                  <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-between">
                    <div className="space-y-1 text-center sm:text-left">
                      <h3 className="font-display text-lg font-semibold tracking-wide text-foreground">
                        Ready to Deploy
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        Deploy your workflow to Neo N3 blockchain
                      </p>
                    </div>
                    <Button
                      onClick={handleDeployClick}
                      variant="cyber"
                      size="lg"
                      disabled={deploySuccess}
                      className="gap-2 px-8"
                    >
                      {deploySuccess ? (
                        <>
                          <CheckCircle2 className="h-5 w-5" />
                          Deployed
                        </>
                      ) : (
                        <>
                          <Rocket className="h-5 w-5" />
                          Deploy Workflow
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Deploy Success Message */}
          {deploySuccess && (
            <Alert variant="success" className="animate-slide-up" aria-live="polite">
              <CheckCircle2 className="h-5 w-5" />
              <AlertDescription className="ml-2">
                <strong className="font-semibold">Success!</strong> Workflow deployed to Neo N3 blockchain.
              </AlertDescription>
            </Alert>
          )}

          {/* Deploy Error Message */}
          {deployError && (
            <Alert variant="destructive" className="animate-slide-up">
              <AlertDescription>
                <strong className="font-semibold">Deployment Error:</strong> {deployError}
              </AlertDescription>
            </Alert>
          )}

          {/* Parameter Panel - Shown when node is selected */}
          {selectedNode && (
            <ParameterPanel
              node={selectedNode}
              onClose={handleParameterPanelClose}
              onSave={handleParameterSave}
            />
          )}

          {/* Payment Modal - Shows when Deploy is clicked */}
          {workflowId && (
            <PaymentModal
              isOpen={isPaymentModalOpen}
              onClose={() => setIsPaymentModalOpen(false)}
              workflowId={workflowId}
              workflowName={workflowSpec?.name}
              onSuccess={handlePaymentSuccess}
              onError={handlePaymentError}
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
