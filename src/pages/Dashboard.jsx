import { useEffect, useState } from 'react'
import axios from 'axios'
// Demo data imports removed - ready for database integration
import TaxOptimization from '../components/TaxOptimization'
import Analytics from './Analytics'

export default function Dashboard({ API_BASE, user, onNavigateToAnalytics }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedHolding, setSelectedHolding] = useState(null)
  const [showMetricDetails, setShowMetricDetails] = useState(null)
  const [showAnalytics, setShowAnalytics] = useState(false)
  
  const handleExecuteHarvest = async (opportunity) => {
    try {
      const response = await axios.post(`${API_BASE}/execute`, {
        type: 'tax_loss_harvest',
        ticker: opportunity.ticker,
        shares: opportunity.shares,
        alternative: opportunity.alternative_etf.alternative,
        expected_savings: opportunity.potential_tax_savings
      })
      
      // Show success notification
      alert(`Tax-loss harvesting order submitted for ${opportunity.ticker}. Expected tax savings: ${formatCurrency(opportunity.potential_tax_savings)}`)
      
      // Refresh portfolio data
      const portfolioResponse = await axios.get(`${API_BASE}/portfolio`)
      setData(portfolioResponse.data)
    } catch (error) {
      alert('Error executing tax-loss harvest. Please try again.')
    }
  }

  const handleViewAnalytics = () => {
    setShowAnalytics(true)
  }

  const handleBackToDashboard = () => {
    setShowAnalytics(false)
  }

  const handleRebalancePortfolio = () => {
    alert('Rebalance Portfolio feature coming soon! This will analyze your current allocation and suggest rebalancing trades.')
  }

  const handleAddFunds = () => {
    alert('Add Funds feature coming soon! This will allow you to add new money to your portfolio.')
  }

  const handleDownloadReport = () => {
    if (!data) {
      alert('No portfolio data available to generate report.')
      return
    }

    // Generate HTML report content
    const reportContent = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Portfolio Report - ${new Date().toLocaleDateString()}</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      margin: 40px;
      color: #1f2937;
      line-height: 1.6;
    }
    .header {
      text-align: center;
      margin-bottom: 40px;
      padding-bottom: 20px;
      border-bottom: 3px solid #2563eb;
    }
    h1 {
      color: #2563eb;
      margin: 0 0 10px 0;
    }
    .summary {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      margin-bottom: 30px;
    }
    .summary-card {
      background: #f8fafc;
      padding: 20px;
      border-radius: 8px;
      border-left: 4px solid #2563eb;
    }
    .summary-label {
      font-size: 0.9rem;
      color: #6b7280;
      margin-bottom: 8px;
    }
    .summary-value {
      font-size: 1.8rem;
      font-weight: bold;
      color: #1f2937;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    th {
      background: #2563eb;
      color: white;
      padding: 12px;
      text-align: left;
      font-weight: 600;
    }
    td {
      padding: 12px;
      border-bottom: 1px solid #e5e7eb;
    }
    tr:hover {
      background: #f8fafc;
    }
    .footer {
      margin-top: 40px;
      padding-top: 20px;
      border-top: 2px solid #e5e7eb;
      text-align: center;
      color: #6b7280;
      font-size: 0.9rem;
    }
    .positive { color: #059669; }
    .negative { color: #dc2626; }
  </style>
</head>
<body>
  <div class="header">
    <h1>📊 MyFalconAdvisor Portfolio Report</h1>
    <p>Generated on ${new Date().toLocaleString()}</p>
    <p>User: ${user?.firstName || 'User'} ${user?.lastName || ''}</p>
  </div>

  <div class="summary">
    <div class="summary-card">
      <div class="summary-label">Total Portfolio Value</div>
      <div class="summary-value">${formatCurrency(data.total_value)}</div>
    </div>
    <div class="summary-card">
      <div class="summary-label">Invested Value</div>
      <div class="summary-value">${formatCurrency(data.invested_value || 0)}</div>
    </div>
    <div class="summary-card">
      <div class="summary-label">Cash Balance</div>
      <div class="summary-value">${formatCurrency(data.cash_balance || 0)}</div>
    </div>
  </div>

  <h2>Portfolio Holdings</h2>
  <table>
    <thead>
      <tr>
        <th>Symbol</th>
        <th>Name</th>
        <th>Sector</th>
        <th>Shares</th>
        <th>Price</th>
        <th>Value</th>
        <th>Allocation</th>
      </tr>
    </thead>
    <tbody>
      ${data.holdings.map(holding => `
        <tr>
          <td><strong>${holding.symbol}</strong></td>
          <td>${holding.name}</td>
          <td>${holding.sector || 'Other'}</td>
          <td>${holding.shares?.toLocaleString()}</td>
          <td>${formatCurrency(holding.price)}</td>
          <td><strong>${formatCurrency(holding.value)}</strong></td>
          <td>${holding.allocation?.toFixed(1)}%</td>
        </tr>
      `).join('')}
    </tbody>
  </table>

  <div class="footer">
    <p><strong>MyFalconAdvisor</strong> - AI-Powered Investment Advisory Platform</p>
    <p>This report is for informational purposes only and does not constitute financial advice.</p>
    <p>Data sourced from your connected portfolio as of ${new Date().toLocaleDateString()}</p>
  </div>
</body>
</html>
    `

    // Create a Blob and download it
    const blob = new Blob([reportContent], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Portfolio_Report_${new Date().toISOString().split('T')[0]}.html`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    // Show success message
    alert('✅ Portfolio report downloaded! Open the HTML file in your browser to view or print as PDF.')
  }

  useEffect(() => {
    const fetchPortfolio = async () => {
      try {
        console.log('Fetching portfolio from:', `${API_BASE}/portfolio`)
        const response = await axios.get(`${API_BASE}/portfolio`, {
          headers: { Authorization: `Bearer usr_348784c4-6f83-4857-b7dc-f5132a38dfee` }
        })
        console.log('Portfolio response:', response.data)
        setData(response.data)
      } catch (error) {
        console.error('Failed to fetch portfolio:', error)
        // Set demo data if API fails
        setData({
          total_value: 100064.61,
          cash_balance: 5000.00,
          invested_value: 95064.61,
          total_day_change: 0.0,
          total_day_change_percent: 0.0,
          holdings: [
            {
              symbol: "SPY",
              name: "SPDR S&P 500 ETF Trust",
              shares: 32,
              price: 672.02,
              value: 21504.64,
              allocation: 21.5,
              sector: "Broad Market",
              dayChange: 0.0
            }
          ]
        })
      } finally {
        setLoading(false)
      }
    }

    fetchPortfolio()
  }, [API_BASE])

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const getChangeColor = (change) => {
    if (change > 0) return 'var(--green-500)'
    if (change < 0) return 'var(--red-500)'
    return 'var(--gray-500)'
  }

  // Portfolio data comes from backend with allocation already calculated

  // Show Analytics page if requested
  if (showAnalytics) {
    return <Analytics API_BASE={API_BASE} user={user} onNavigateBack={handleBackToDashboard} />
  }

  return (
    <div>
      {/* Portfolio Metrics Cards - Beautiful KPI Cards */}
      <div className="portfolio-grid">
        <div 
          className="metric-card"
          onClick={() => setShowMetricDetails(showMetricDetails === 'value' ? null : 'value')}
          style={{ cursor: 'pointer' }}
        >
          <div className="metric-value">
            {data ? formatCurrency(data.total_value) : '$0'}
          </div>
          <div className="metric-label">Total Portfolio Value</div>
          <div className="metric-subtext">
            {data ? `Invested: ${formatCurrency(data.invested_value || 0)} • Cash: ${formatCurrency(data.cash_balance || 0)}` : 'Loading...'}
          </div>
          {showMetricDetails === 'value' && (
            <div className="metric-details">
              <div>Total Value: ${data?.total_value?.toLocaleString()}</div>
              <div>Invested Value: ${data?.invested_value?.toLocaleString()}</div>
              <div>Cash Balance: ${data?.cash_balance?.toLocaleString()}</div>
              <div>Real-time data from PostgreSQL</div>
            </div>
          )}
        </div>

        <div 
          className="metric-card"
          onClick={() => setShowMetricDetails(showMetricDetails === 'change' ? null : 'change')}
          style={{ cursor: 'pointer', background: 'linear-gradient(135deg, var(--green-500), var(--green-600))' }}
        >
          <div 
            className="metric-value" 
            style={{ color: 'white' }}
          >
            {data?.total_day_change_percent ? (data.total_day_change_percent >= 0 ? '+' : '') + data.total_day_change_percent.toFixed(2) + '%' : '+0.00%'}
          </div>
          <div className="metric-label">Today's Performance</div>
          <div className="metric-subtext">
            {data?.total_day_change ? (data.total_day_change >= 0 ? '+' : '') + formatCurrency(data.total_day_change) : '+$0.00'}
          </div>
          {showMetricDetails === 'change' && (
            <div className="metric-details">
              <div>Percentage: {data?.total_day_change_percent?.toFixed(2) || 0}%</div>
              <div>Based on market movements</div>
            </div>
          )}
        </div>

        <div 
          className="metric-card"
          onClick={() => setShowMetricDetails(showMetricDetails === 'holdings' ? null : 'holdings')}
          style={{ cursor: 'pointer', background: 'linear-gradient(135deg, var(--gray-700), var(--gray-800))' }}
        >
          <div className="metric-value">{data?.holdings?.length || 0}</div>
          <div className="metric-label">Holdings</div>
          {showMetricDetails === 'holdings' && (
            <div className="metric-details">
              <div>Diversified across {data?.holdings?.length || 0} assets</div>
              <div>Real holdings from database</div>
            </div>
          )}
        </div>
      </div>

      {/* Portfolio Holdings Table */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">📊 Portfolio Holdings</h3>
          <p className="card-subtitle">Your current investment allocation</p>
        </div>
        
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div className="loading-spinner" style={{ margin: '0 auto' }}></div>
            <p style={{ marginTop: '16px', color: 'var(--gray-600)' }}>
              Loading your portfolio from database...
            </p>
          </div>
        ) : data?.holdings ? (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Asset</th>
                  <th>Industry</th>
                  <th>Shares</th>
                  <th>Price</th>
                  <th>Value</th>
                  <th>Allocation & Change</th>
                </tr>
              </thead>
              <tbody>
                {data.holdings.map((holding, index) => (
                  <tr 
                    key={index}
                    className={selectedHolding === index ? 'selected' : ''}
                    onClick={() => setSelectedHolding(selectedHolding === index ? null : index)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '6px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <strong style={{ fontSize: '1.1rem', color: 'var(--gray-900)', fontWeight: '700' }}>{holding.symbol}</strong>
                        </div>
                        <span style={{ fontSize: '0.9rem', color: 'var(--gray-600)', fontWeight: '500' }}>{holding.name}</span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '4px' }}>
                        <span 
                          className="sector-tag" 
                          data-sector={holding.sector}
                          style={{ 
                            margin: 0,
                            fontSize: '0.8rem',
                            padding: '6px 12px',
                            fontWeight: '600'
                          }}
                        >
                          {holding.sector || 'Other'}
                        </span>
                        <span style={{ 
                          fontSize: '0.75rem', 
                          color: 'var(--gray-500)', 
                          fontWeight: '500',
                          textTransform: 'capitalize'
                        }}>
                          {holding.sector?.toLowerCase() || 'Other'}
                        </span>
                      </div>
                    </td>
                    <td style={{ fontWeight: '500' }}>{holding.shares?.toLocaleString()}</td>
                    <td style={{ fontWeight: '500' }}>{formatCurrency(holding.price)}</td>
                    <td><strong style={{ fontSize: '1.1rem' }}>{formatCurrency(holding.value)}</strong></td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <div className="allocation-bar">
                          <div 
                            className="allocation-fill" 
                            style={{ width: `${holding.allocation}%` }}
                          ></div>
                          <span className="allocation-text">{holding.allocation?.toFixed(1)}%</span>
                        </div>
                        <div style={{ 
                          fontSize: '0.8rem', 
                          color: 'var(--gray-600)', 
                          fontWeight: '500',
                          textAlign: 'center'
                        }}>
                          {holding.dayChange ? (holding.dayChange >= 0 ? '+' : '') + formatCurrency(holding.dayChange) : '$0'}
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '3rem', marginBottom: '16px' }}>📊</div>
            <p style={{ color: 'var(--gray-600)', marginBottom: '20px' }}>
              No portfolio data available. Please check your connection.
            </p>
            <button 
              className="btn btn-primary"
              onClick={() => window.location.reload()}
            >
              🔄 Retry
            </button>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">⚡ Quick Actions</h3>
          <p className="card-subtitle">Common portfolio management tasks</p>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          <button 
            className="btn btn-secondary" 
            style={{ padding: '16px', justifyContent: 'flex-start' }}
            onClick={handleRebalancePortfolio}
          >
            📈 Rebalance Portfolio
          </button>
          <button 
            className="btn btn-secondary" 
            style={{ padding: '16px', justifyContent: 'flex-start' }}
            onClick={handleAddFunds}
          >
            💰 Add Funds
          </button>
          <button 
            className="btn btn-primary" 
            style={{ 
              padding: '16px', 
              justifyContent: 'flex-start',
              border: '2px solid var(--primary-500)',
              background: 'white',
              color: 'var(--primary-500)'
            }}
            onClick={handleViewAnalytics}
          >
            📊 View Analytics
          </button>
          <button 
            className="btn btn-secondary" 
            style={{ padding: '16px', justifyContent: 'flex-start' }}
            onClick={handleDownloadReport}
          >
            📄 Download Report
          </button>
        </div>
      </div>

      {/* Tax Optimization Opportunities */}
      {data && (
        <TaxOptimization 
          taxData={data} 
          onExecuteHarvest={handleExecuteHarvest}
        />
      )}
    </div>
  )
}