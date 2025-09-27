import { useEffect, useState } from 'react'
import axios from 'axios'

export default function AuditTrail({ API_BASE }) {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await axios.get(`${API_BASE}/audit-logs`)
        setLogs(res.data.logs || [])
      } catch (error) {
        console.error('Failed to fetch audit logs:', error)
        // Mock data for development
        setLogs([
          {
            id: '1',
            timestamp: new Date().toISOString(),
            type: 'recommendation',
            action: 'Generated portfolio advice',
            status: 'completed',
            details: 'Recommended rebalancing 10% from SPY to AGG'
          },
          {
            id: '2',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            type: 'compliance',
            action: 'Validated recommendation',
            status: 'passed',
            details: 'All compliance checks passed'
          }
        ])
      } finally {
        setLoading(false)
      }
    }

    fetchLogs()
  }, [API_BASE])

  if (loading) return <p>Loading audit trail...</p>

  return (
    <div>
      <h2>Audit Trail</h2>
      <p style={{ opacity: 0.7, marginBottom: 16 }}>
        Complete log of all recommendations, compliance checks, and executions
      </p>
      
      <div style={{ display: 'grid', gap: 12 }}>
        {logs.length === 0 ? (
          <p>No audit logs available</p>
        ) : (
          logs.map(log => (
            <div key={log.id} style={{
              border: '1px solid #ddd',
              borderRadius: 8,
              padding: 16,
              backgroundColor: log.status === 'failed' ? '#fff5f5' : '#f9f9f9'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ 
                  fontWeight: 'bold',
                  color: log.status === 'failed' ? '#dc3545' : log.status === 'passed' ? '#28a745' : '#007bff'
                }}>
                  {log.type.toUpperCase()}
                </span>
                <span style={{ fontSize: '0.85em', opacity: 0.7 }}>
                  {new Date(log.timestamp).toLocaleString()}
                </span>
              </div>
              <div style={{ marginBottom: 8 }}>
                <strong>Action:</strong> {log.action}
              </div>
              <div style={{ fontSize: '0.9em', opacity: 0.8 }}>
                {log.details}
              </div>
              <div style={{ marginTop: 8, fontSize: '0.8em' }}>
                <span style={{
                  padding: '2px 8px',
                  borderRadius: 12,
                  backgroundColor: log.status === 'failed' ? '#dc3545' : log.status === 'passed' ? '#28a745' : '#007bff',
                  color: 'white'
                }}>
                  {log.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
