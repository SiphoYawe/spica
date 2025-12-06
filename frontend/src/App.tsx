import { useState, useEffect } from 'react'
import './App.css'
import { apiClient } from './api/client'
import type { HealthResponse } from './types/api'
import WalletBalance from './components/WalletBalance'

function App() {
  const [backendStatus, setBackendStatus] = useState<string>('checking...')
  const [backendVersion, setBackendVersion] = useState<string>('')

  useEffect(() => {
    // Check backend connection on mount
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

  return (
    <div className="App">
      <header>
        <h1>Spica</h1>
        <p>AI-Powered DeFi Workflow Builder for Neo N3</p>
      </header>

      <main>
        <div className="status-card">
          <h2>System Status</h2>
          <div className="status-item">
            <span>Backend:</span>
            <span className={backendStatus === 'ok' ? 'status-ok' : 'status-error'}>
              {backendStatus}
            </span>
          </div>
          {backendVersion && (
            <div className="status-item">
              <span>Version:</span>
              <span>{backendVersion}</span>
            </div>
          )}
        </div>

        {/* Demo Wallet Balance */}
        <WalletBalance autoRefresh={true} refreshInterval={30000} />

        <div className="info-card">
          <h3>Project Scaffolding Complete</h3>
          <p>Frontend and backend are running with hot reload enabled.</p>
          <ul>
            <li>Frontend: React + TypeScript + Vite</li>
            <li>Backend: FastAPI + Python</li>
            <li>Ready for feature development</li>
          </ul>
        </div>
      </main>
    </div>
  )
}

export default App
