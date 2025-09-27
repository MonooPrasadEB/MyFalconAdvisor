import { useEffect, useState } from 'react'
import axios from 'axios'
import { getDemoInsights, getDemoUserInfo } from '../utils/demoData'
import TaxOptimization from '../components/TaxOptimization'

export default function Dashboard({ API_BASE, user }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedHolding, setSelectedHolding] = useState(null)
  const [showMetricDetails, setShowMetricDetails] = useState(null)
  
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

  useEffect(() => {
    const fetchPortfolio = async () => {
      try {
        const response = await axios.get(`${API_BASE}/portfolio`)
        setData(response.data)
      } catch (error) {
        setData({ error: true })
      } finally {
        setLoading(false)
      }
    }
    
    fetchPortfolio()
  }, [API_BASE])

  if (loading) {
    return (
      <div className="card">
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div className="loading-spinner" style={{ margin: '0 auto 16px' }}></div>
          <p>Loading your portfolio...</p>
        </div>
      </div>
    )
  }

  if (data?.error) {
    return (
      <div className="card">
        <div className="notification error">
          ❌ Failed to load portfolio. Please ensure the backend is running.
        </div>
      </div>
    )
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value)
  }

  const formatPercent = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: 1,
      maximumFractionDigits: 1
    }).format(value / 100)
  }

  const getPerformanceColor = (change) => {
    if (change > 0) return 'var(--green-500)'
    if (change < 0) return 'var(--red-500)'
    return 'var(--gray-500)'
  }

  // Portfolio data comes from backend with allocation already calculated

  return (
    <div>
      {/* Portfolio Metrics Cards - Interactive */}
      <div className="portfolio-grid">
        <div 
          className="metric-card"
          onClick={() => setShowMetricDetails(showMetricDetails === 'value' ? null : 'value')}
        >
          <div className="metric-value">{formatCurrency(data.total_value)}</div>
          <div className="metric-label">Total Portfolio Value</div>
          {showMetricDetails === 'value' && (
            <div style={{ 
              marginTop: '12px', 
              fontSize: '0.8rem', 
              opacity: 0.9,
              padding: '8px 0',
              borderTop: '1px solid rgba(255,255,255,0.2)'
            }}>
              📈 +12.5% this year<br/>
              💰 +$932 this month
            </div>
          )}
        </div>
        
        <div 
          className="card metric-card" 
          style={{ 
            background: data.total_day_change_percent >= 0 
              ? 'linear-gradient(135deg, var(--green-500), var(--green-600))' 
              : 'linear-gradient(135deg, var(--red-500), #dc2626)', 
            color: 'white' 
          }}
          onClick={() => setShowMetricDetails(showMetricDetails === 'performance' ? null : 'performance')}
        >
          <div className="metric-value">
            {data.total_day_change_percent >= 0 ? '+' : ''}{data.total_day_change_percent?.toFixed(2)}%
          </div>
          <div className="metric-label">Today's Performance</div>
          <div style={{ fontSize: '0.8rem', opacity: 0.9, marginTop: '4px' }}>
            {data.total_day_change >= 0 ? '+' : ''}${data.total_day_change?.toFixed(2)}
          </div>
          {showMetricDetails === 'performance' && (
            <div style={{ 
              marginTop: '12px', 
              fontSize: '0.8rem', 
              opacity: 0.9,
              padding: '8px 0',
              borderTop: '1px solid rgba(255,255,255,0.2)'
            }}>
              📈 YTD: +{data.performance_metrics?.ytd_return}%<br/>
              🎯 1Y Return: +{data.performance_metrics?.one_year_return}%<br/>
              📊 Sharpe Ratio: {data.performance_metrics?.sharpe_ratio}
            </div>
          )}
        </div>
        
        <div 
          className="card metric-card" 
          style={{ background: 'linear-gradient(135deg, var(--gray-600), var(--gray-700))', color: 'white' }}
          onClick={() => setShowMetricDetails(showMetricDetails === 'holdings' ? null : 'holdings')}
        >
          <div className="metric-value">{data.holdings.length}</div>
          <div className="metric-label">Holdings</div>
          {showMetricDetails === 'holdings' && (
            <div style={{ 
              marginTop: '12px', 
              fontSize: '0.8rem', 
              opacity: 0.9,
              padding: '8px 0',
              borderTop: '1px solid rgba(255,255,255,0.2)'
            }}>
              📊 Well diversified<br/>
              ⚖️ Balanced allocation
            </div>
          )}
        </div>
      </div>

      {/* Holdings Table */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">📊 Portfolio Holdings</h3>
          <p className="card-subtitle">Your current investment allocation</p>
        </div>
        
        <table className="holdings-table">
          <thead>
            <tr>
              <th>Asset</th>
              <th>Shares</th>
              <th>Price</th>
              <th>Value</th>
              <th>Allocation</th>
              <th>Change</th>
            </tr>
          </thead>
          <tbody>
            {data.holdings.map(holding => (
              <tr 
                key={holding.ticker}
                onClick={() => setSelectedHolding(selectedHolding === holding.ticker ? null : holding.ticker)}
                style={{ 
                  background: selectedHolding === holding.ticker ? 'var(--primary-50)' : 'transparent',
                  borderLeft: selectedHolding === holding.ticker ? '4px solid var(--primary-500)' : 'none'
                }}
              >
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="ticker-badge">{holding.ticker}</span>
                    <div>
                      <div style={{ fontWeight: '500' }}>
                        {holding.name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--gray-500)' }}>
                        {holding.sector}
                      </div>
                    </div>
                  </div>
                </td>
                <td style={{ fontWeight: '500' }}>{holding.shares.toLocaleString()}</td>
                <td>{formatCurrency(holding.price)}</td>
                <td style={{ fontWeight: '600' }}>{formatCurrency(holding.value)}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{
                      width: '40px',
                      height: '6px',
                      background: 'var(--gray-200)',
                      borderRadius: '3px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${holding.allocation}%`,
                        height: '100%',
                        background: 'var(--primary-500)',
                        borderRadius: '3px'
                      }}></div>
                    </div>
                    <span style={{ fontSize: '0.85rem', fontWeight: '500' }}>
                      {holding.allocation.toFixed(1)}%
                    </span>
                  </div>
                </td>
                <td>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <span style={{ 
                      color: getPerformanceColor(holding.dayChangePercent),
                      fontWeight: '500',
                      fontSize: '0.9rem'
                    }}>
                      {holding.dayChangePercent >= 0 ? '+' : ''}{holding.dayChangePercent?.toFixed(2)}%
                    </span>
                    <span style={{ 
                      color: getPerformanceColor(holding.dayChange),
                      fontSize: '0.75rem'
                    }}>
                      {holding.dayChange >= 0 ? '+' : ''}${holding.dayChange?.toFixed(2)}
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {/* Selected Holding Details */}
        {selectedHolding && (
          <div style={{
            marginTop: '16px',
            padding: '20px',
            background: 'linear-gradient(135deg, var(--primary-50), var(--primary-100))',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--primary-200)',
            animation: 'slideIn 0.3s ease'
          }}>
            <h4 style={{ margin: '0 0 16px 0', color: 'var(--primary-700)' }}>
              📈 {selectedHolding} Details
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)' }}>52-Week Range</div>
                <div style={{ fontWeight: '600' }}>$180.50 - $520.30</div>
              </div>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)' }}>Market Cap</div>
                <div style={{ fontWeight: '600' }}>$480.2B</div>
              </div>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)' }}>P/E Ratio</div>
                <div style={{ fontWeight: '600' }}>24.5</div>
              </div>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)' }}>Dividend Yield</div>
                <div style={{ fontWeight: '600' }}>1.2%</div>
              </div>
            </div>
            <button 
              onClick={() => setSelectedHolding(null)}
              style={{
                marginTop: '16px',
                padding: '8px 16px',
                background: 'var(--primary-500)',
                color: 'white',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
            >
              Close Details
            </button>
          </div>
        )}
      </div>

      {/* Recommendations Card */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">🎯 Latest Recommendation</h3>
          <p className="card-subtitle">AI-generated, compliance-validated advice</p>
        </div>
        
        <div style={{
          background: data.last_recommendation.compliance_status === 'passed' 
            ? 'var(--green-50)' 
            : 'var(--red-50)',
          padding: '20px',
          borderRadius: 'var(--radius-lg)',
          border: `1px solid ${data.last_recommendation.compliance_status === 'passed' 
            ? 'var(--green-200)' 
            : 'var(--red-200)'}`
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '12px',
            marginBottom: '12px'
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              background: data.last_recommendation.compliance_status === 'passed' 
                ? 'var(--green-500)' 
                : 'var(--red-500)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: '1.2rem'
            }}>
              {data.last_recommendation.compliance_status === 'passed' ? '✅' : '⚠️'}
            </div>
            <div>
              <div style={{ fontWeight: '600', fontSize: '1.1rem' }}>
                Compliance Status: {data.last_recommendation.compliance_status.toUpperCase()}
              </div>
              <div style={{ 
                fontSize: '0.85rem', 
                color: 'var(--gray-600)',
                marginTop: '2px'
              }}>
                Recommendation validated by our compliance engine
              </div>
            </div>
          </div>
          
          <div style={{
            background: 'white',
            padding: '16px',
            borderRadius: 'var(--radius-md)',
            fontSize: '1rem',
            lineHeight: '1.5',
            border: '1px solid var(--gray-200)'
          }}>
            💡 {data.last_recommendation.text}
          </div>
          
          <div style={{ 
            marginTop: '12px',
            fontSize: '0.8rem',
            color: 'var(--gray-500)'
          }}>
            📅 Generated just now • 🤖 AI Advisor • ✅ Compliance Checked
          </div>
        </div>
      </div>

      {/* Tax-Loss Harvesting */}
      {data.tax_loss_harvesting && (
        <TaxOptimization 
          taxData={data} 
          onExecuteHarvest={handleExecuteHarvest}
        />
      )}

      {/* AI Insights & Recommendations - Demo */}
      {user?.id === "1" && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🤖 AI Insights & Recommendations</h3>
            <p className="card-subtitle">Personalized analysis based on your portfolio and goals</p>
          </div>
          
          <div style={{ display: 'grid', gap: '16px' }}>
            {getDemoInsights().map((insight, index) => (
              <div key={index} style={{
                padding: '16px',
                border: '1px solid var(--gray-200)',
                borderRadius: 'var(--radius-md)',
                background: insight.priority === 'high' ? 'var(--primary-25)' : 
                           insight.priority === 'medium' ? 'var(--yellow-50)' :
                           insight.priority === 'info' ? 'var(--green-50)' : 'var(--gray-50)',
                borderLeft: `4px solid ${insight.priority === 'high' ? 'var(--primary-500)' : 
                                        insight.priority === 'medium' ? 'var(--yellow-500)' :
                                        insight.priority === 'info' ? 'var(--green-500)' : 'var(--gray-400)'}`
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                  <div style={{
                    fontSize: '1.5rem',
                    lineHeight: 1,
                    marginTop: '2px'
                  }}>
                    {insight.icon}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{
                      fontWeight: '600',
                      marginBottom: '4px',
                      color: insight.priority === 'high' ? 'var(--primary-700)' : 'var(--gray-800)'
                    }}>
                      {insight.title}
                    </div>
                    <div style={{
                      fontSize: '0.9rem',
                      lineHeight: '1.5',
                      color: 'var(--gray-600)'
                    }}>
                      {insight.description}
                    </div>
                    {insight.action && (
                      <button 
                        className="btn btn-primary"
                        style={{ 
                          marginTop: '8px',
                          fontSize: '0.8rem',
                          padding: '6px 12px'
                        }}
                        onClick={() => {
                          if (insight.action === 'learning') {
                            // This would trigger navigation to learning
                            console.log('Navigate to learning section')
                          }
                        }}
                      >
                        📚 Continue Learning
                      </button>
                    )}
                  </div>
                  <div style={{
                    fontSize: '0.7rem',
                    color: 'var(--gray-500)',
                    textTransform: 'uppercase',
                    fontWeight: '600',
                    letterSpacing: '0.5px'
                  }}>
                    {insight.priority}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Gamification Summary - Demo */}
      {user?.id === "1" && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🎮 Your Financial Journey</h3>
            <p className="card-subtitle">Level up your financial skills and earn rewards!</p>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
            <div style={{
              padding: '16px',
              background: 'linear-gradient(135deg, var(--primary-500), var(--primary-600))',
              color: 'white',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '4px' }}>⭐ 8</div>
              <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>Financial Enthusiast</div>
              <div style={{ fontSize: '0.8rem', marginTop: '4px', opacity: 0.8 }}>67% to level 9</div>
            </div>
            
            <div style={{
              padding: '16px',
              background: 'linear-gradient(135deg, var(--yellow-500), #FFB347)',
              color: 'white',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '4px' }}>💎 2,450</div>
              <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>Total Points</div>
              <div style={{ fontSize: '0.8rem', marginTop: '4px', opacity: 0.8 }}>Top 15% of users</div>
            </div>
            
            <div style={{
              padding: '16px',
              background: 'linear-gradient(135deg, var(--orange-500), #FF6347)',
              color: 'white',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '4px' }}>🔥 12</div>
              <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>Day Streak</div>
              <div style={{ fontSize: '0.8rem', marginTop: '4px', opacity: 0.8 }}>Best: 18 days</div>
            </div>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div style={{
              padding: '16px',
              background: 'var(--green-50)',
              border: '1px solid var(--green-200)',
              borderRadius: 'var(--radius-md)'
            }}>
              <div style={{ fontWeight: '600', marginBottom: '8px', color: 'var(--green-700)' }}>
                🏆 Recent Achievement
              </div>
              <div style={{ fontSize: '0.9rem', marginBottom: '4px' }}>Growing Wealth</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)' }}>
                Reached $10,000 portfolio value (+500 points)
              </div>
            </div>
            
            <div style={{
              padding: '16px',
              background: 'var(--blue-50)',
              border: '1px solid var(--blue-200)',
              borderRadius: 'var(--radius-md)'
            }}>
              <div style={{ fontWeight: '600', marginBottom: '8px', color: 'var(--blue-700)' }}>
                🎯 Active Challenge
              </div>
              <div style={{ fontSize: '0.9rem', marginBottom: '4px' }}>Learning Sprint</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)' }}>
                Complete 3 lessons this week (2/3)
              </div>
            </div>
          </div>
          
          <div style={{ marginTop: '16px', textAlign: 'center' }}>
            <button 
              className="btn btn-primary"
              onClick={() => {
                // This would navigate to gamification tab
                console.log('Navigate to gamification')
              }}
              style={{ fontSize: '0.9rem' }}
            >
              🎮 View All Rewards & Achievements
            </button>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">⚡ Quick Actions</h3>
          <p className="card-subtitle">Common portfolio management tasks</p>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          <button className="btn btn-secondary" style={{ padding: '16px', justifyContent: 'flex-start' }}>
            📈 Rebalance Portfolio
          </button>
          <button className="btn btn-secondary" style={{ padding: '16px', justifyContent: 'flex-start' }}>
            💰 Add Funds
          </button>
          <button className="btn btn-secondary" style={{ padding: '16px', justifyContent: 'flex-start' }}>
            📊 View Analytics
          </button>
          <button className="btn btn-secondary" style={{ padding: '16px', justifyContent: 'flex-start' }}>
            📄 Download Report
          </button>
        </div>
      </div>
    </div>
  )
}
