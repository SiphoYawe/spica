import { useState, useEffect } from 'react'
import { apiClient } from './api/client'
import type { HealthResponse, WorkflowSpec } from './types/api'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import WalletBalance from './components/WalletBalance'
import WorkflowInput from './components/WorkflowInput'
import ErrorBoundary from './components/ErrorBoundary'

function App() {
  const [backendStatus, setBackendStatus] = useState<string>('checking...')
  const [backendVersion, setBackendVersion] = useState<string>('')
  const [workflowSpec, setWorkflowSpec] = useState<WorkflowSpec | null>(null)

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

  const handleWorkflowGenerated = (workflow: WorkflowSpec) => {
    setWorkflowSpec(workflow)
    console.log('Workflow generated:', workflow)
  }

  return (
    <ErrorBoundary>
      <div className="mx-auto max-w-5xl p-8">
        <header className="mb-12 text-center">
          <h1 className="mb-2 text-5xl font-bold bg-gradient-to-r from-accent to-accent-secondary bg-clip-text text-transparent">
            Spica
          </h1>
          <p className="text-lg text-muted">
            AI-Powered DeFi Workflow Builder for Neo N3
          </p>
        </header>

        <main className="mx-auto grid max-w-3xl gap-8">
          {/* Workflow Input - Primary Feature */}
          <WorkflowInput onWorkflowGenerated={handleWorkflowGenerated} />

          {/* Workflow Preview - Shows after generation */}
          {workflowSpec && (
            <Card className="border-cyber-blue/20 bg-gradient-to-br from-card to-darker-bg shadow-[0_0_24px_rgba(0,217,255,0.1)] animate-slide-up">
              <div className="absolute left-0 top-0 h-1 w-full bg-gradient-to-r from-cyber-blue via-cyber-purple to-cyber-green opacity-60" />
              <CardHeader>
                <CardTitle className="font-display text-xl">Generated Workflow</CardTitle>
                <CardDescription>{workflowSpec.description}</CardDescription>
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
