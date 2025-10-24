import { useState } from 'react'

export default function TaxOptimization({ taxData, onExecuteHarvest }) {
  const [selectedOpportunity, setSelectedOpportunity] = useState(null)

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value || 0)
  }

  const formatPercent = (value) => {
    return `${value >= 0 ? '+' : ''}${value?.toFixed(2)}%`
  }

  const getSeverityColor = (lossPercent) => {
    if (lossPercent <= -10) return 'var(--red-500)'
    if (lossPercent <= -5) return 'var(--orange-500)'
    return 'var(--yellow-500)'
  }

  if (!taxData?.tax_loss_harvesting?.opportunities?.length) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">💰 Tax-Loss Harvesting Analysis</h3>
          <p className="card-subtitle">Intelligent tax optimization for your portfolio</p>
        </div>
        
        {/* Demo Mode Banner */}
        <div style={{
          padding: '12px 16px',
          background: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)',
          border: '1px solid #60a5fa',
          borderRadius: 'var(--radius-md)',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <span style={{ fontSize: '1.2rem' }}>ℹ️</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: '600', color: '#1e40af', marginBottom: '2px' }}>
              Demo Mode - Simulated Analysis
            </div>
            <div style={{ fontSize: '0.85rem', color: '#1e40af' }}>
              This analysis uses simulated cost basis data for demonstration. Connect your actual cost basis for real tax-loss harvesting opportunities.
            </div>
          </div>
        </div>
        
        <div style={{
          padding: '40px',
          textAlign: 'center',
          background: 'var(--green-50)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--green-200)'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🎯</div>
          <h4 style={{ color: 'var(--green-600)', marginBottom: '8px' }}>
            Portfolio in Good Tax Position
          </h4>
          <p style={{ color: 'var(--gray-600)', maxWidth: '400px', margin: '0 auto' }}>
            Your current holdings don't have significant unrealized losses suitable for tax-loss harvesting. 
            We'll monitor your portfolio and alert you when opportunities arise.
          </p>
        </div>
      </div>
    )
  }

  const opportunities = taxData.tax_loss_harvesting.opportunities
  const totalSavings = taxData.tax_loss_harvesting.total_potential_savings

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">💰 Tax-Loss Harvesting Analysis</h3>
        <p className="card-subtitle">
          Intelligent tax optimization strategies for your portfolio
        </p>
      </div>

      {/* Demo Mode Information Banner */}
      <div style={{
        padding: '16px',
        background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
        border: '2px solid #f59e0b',
        borderRadius: 'var(--radius-lg)',
        marginBottom: '20px'
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <span style={{ fontSize: '1.5rem', marginTop: '2px' }}>⚠️</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: '700', color: '#92400e', fontSize: '1.05rem', marginBottom: '6px' }}>
              Demo Mode - Simulated Tax Analysis
            </div>
            <div style={{ fontSize: '0.9rem', color: '#78350f', lineHeight: '1.6', marginBottom: '8px' }}>
              The opportunities shown below are based on <strong>simulated cost basis data</strong> for demonstration purposes. 
              In production, this would use your actual purchase prices and transaction history from your brokerage account.
            </div>
            <div style={{ 
              padding: '10px 12px', 
              background: 'rgba(255, 255, 255, 0.7)', 
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.85rem',
              color: '#78350f'
            }}>
              <strong>How it works:</strong> We analyze ~30% of holdings with simulated 8-17% losses to demonstrate tax-loss harvesting strategies. 
              Real implementation would track your actual cost basis, purchase dates, and tax lots.
            </div>
          </div>
        </div>
      </div>

      {/* Educational Info Card */}
      <div style={{
        padding: '16px',
        background: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)',
        border: '1px solid #60a5fa',
        borderRadius: 'var(--radius-md)',
        marginBottom: '20px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <span style={{ fontSize: '1.2rem' }}>📚</span>
          <span style={{ fontWeight: '600', color: '#1e40af' }}>What is Tax-Loss Harvesting?</span>
        </div>
        <div style={{ fontSize: '0.9rem', color: '#1e40af', lineHeight: '1.6' }}>
          Tax-loss harvesting involves selling investments at a loss to offset capital gains and reduce your tax bill. 
          You can then reinvest in similar (but not identical) securities to maintain market exposure while avoiding the wash sale rule.
        </div>
      </div>

      {/* Summary Card */}
      <div style={{
        background: 'linear-gradient(135deg, var(--primary-500), var(--primary-600))',
        color: 'white',
        padding: '24px',
        borderRadius: 'var(--radius-lg)',
        marginBottom: '24px',
        position: 'relative'
      }}>
        <div style={{ 
          position: 'absolute', 
          top: '12px', 
          right: '12px',
          background: 'rgba(255, 255, 255, 0.2)',
          padding: '4px 10px',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.75rem',
          fontWeight: '600',
          border: '1px solid rgba(255, 255, 255, 0.3)'
        }}>
          SIMULATED DATA
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '4px' }}>
              {opportunities.length}
            </div>
            <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>
              Harvesting Opportunities (Demo)
            </div>
          </div>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '4px' }}>
              {formatCurrency(totalSavings)}
            </div>
            <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>
              Potential Tax Savings (Est.)
            </div>
          </div>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '4px' }}>
              {taxData.tax_optimization.current_tax_bracket}
            </div>
            <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>
              Assumed Tax Bracket
            </div>
          </div>
        </div>
      </div>

      {/* Opportunities List */}
      <div style={{ display: 'grid', gap: '16px', marginBottom: '24px' }}>
        {opportunities.map((opp, index) => (
          <div
            key={index}
            style={{
              border: '1px solid var(--gray-200)',
              borderRadius: 'var(--radius-lg)',
              padding: '20px',
              background: selectedOpportunity === index ? 'var(--primary-25)' : 'white',
              borderColor: selectedOpportunity === index ? 'var(--primary-300)' : 'var(--gray-200)',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onClick={() => setSelectedOpportunity(selectedOpportunity === index ? null : index)}
            onMouseEnter={(e) => {
              if (selectedOpportunity !== index) {
                e.currentTarget.style.borderColor = 'var(--primary-200)'
                e.currentTarget.style.transform = 'translateY(-1px)'
              }
            }}
            onMouseLeave={(e) => {
              if (selectedOpportunity !== index) {
                e.currentTarget.style.borderColor = 'var(--gray-200)'
                e.currentTarget.style.transform = 'translateY(0)'
              }
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  <span style={{
                    padding: '4px 8px',
                    background: 'var(--gray-100)',
                    borderRadius: 'var(--radius-sm)',
                    fontWeight: '600',
                    fontSize: '0.9rem'
                  }}>
                    {opp.ticker}
                  </span>
                  <span style={{ fontWeight: '500', color: 'var(--gray-700)' }}>
                    {opp.name}
                  </span>
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--gray-500)' }}>
                  {opp.shares} shares • Purchased {opp.purchase_date} • <span style={{ color: '#f59e0b', fontWeight: '600' }}>Simulated Data</span>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{
                  fontSize: '1.1rem',
                  fontWeight: '600',
                  color: getSeverityColor(opp.loss_percentage),
                  marginBottom: '4px'
                }}>
                  {formatPercent(opp.loss_percentage)}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--gray-500)' }}>
                  {formatCurrency(opp.unrealized_loss)} loss
                </div>
              </div>
            </div>

            {selectedOpportunity === index && (
              <div style={{
                marginTop: '16px',
                padding: '16px',
                background: 'var(--gray-50)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--gray-200)'
              }}>
                <h5 style={{ margin: '0 0 12px 0', color: 'var(--primary-700)' }}>
                  💡 Tax-Loss Harvesting Strategy
                </h5>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                  <div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)', marginBottom: '4px' }}>
                      Current Position
                    </div>
                    <div style={{ fontWeight: '500' }}>
                      {opp.shares} shares @ {formatCurrency(opp.current_price)}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--gray-500)' }}>
                      Cost basis: {formatCurrency(opp.cost_basis)}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)', marginBottom: '4px' }}>
                      Tax Benefit
                    </div>
                    <div style={{ fontWeight: '500', color: 'var(--green-600)' }}>
                      {formatCurrency(opp.potential_tax_savings)} savings
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--gray-500)' }}>
                      At 27% tax rate
                    </div>
                  </div>
                </div>

                {opp.alternative_etf && (
                  <div style={{
                    padding: '12px',
                    background: 'var(--blue-50)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--blue-200)',
                    marginBottom: '16px'
                  }}>
                    <div style={{ fontSize: '0.85rem', color: 'var(--blue-700)', marginBottom: '4px' }}>
                      <strong>🔄 Wash Sale Compliant Alternative:</strong>
                    </div>
                    <div style={{ fontSize: '0.9rem', fontWeight: '500' }}>
                      {opp.alternative_etf.alternative} - {opp.alternative_etf.name}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)', marginTop: '4px' }}>
                      Immediately reinvest to maintain market exposure while harvesting the loss
                    </div>
                  </div>
                )}

                <div style={{ display: 'flex', gap: '12px' }}>
                  <button 
                    className="btn btn-primary"
                    onClick={(e) => {
                      e.stopPropagation()
                      onExecuteHarvest && onExecuteHarvest(opp)
                    }}
                    style={{ flex: 1 }}
                  >
                    💰 Execute Harvest
                  </button>
                  <button 
                    className="btn btn-secondary"
                    onClick={(e) => {
                      e.stopPropagation()
                      setSelectedOpportunity(null)
                    }}
                    style={{ flex: 1 }}
                  >
                    📋 View Details
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Tax Optimization Insights */}
      <div>
        <h4 style={{ margin: '0 0 16px 0', color: 'var(--gray-800)' }}>
          🎯 Tax Optimization Insights
        </h4>
        <div style={{ display: 'grid', gap: '12px' }}>
          {taxData.tax_optimization.insights.map((insight, index) => (
            <div
              key={index}
              style={{
                padding: '16px',
                background: insight.importance === 'high' ? 'var(--green-50)' : 'var(--gray-50)',
                border: `1px solid ${insight.importance === 'high' ? 'var(--green-200)' : 'var(--gray-200)'}`,
                borderRadius: 'var(--radius-md)',
                borderLeft: `4px solid ${insight.importance === 'high' ? 'var(--green-500)' : 'var(--gray-400)'}`
              }}
            >
              <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                {insight.title}
              </div>
              <div style={{ fontSize: '0.9rem', color: 'var(--gray-600)' }}>
                {insight.description}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Year-End Planning */}
      <div style={{
        marginTop: '24px',
        padding: '16px',
        background: 'var(--yellow-50)',
        border: '1px solid var(--yellow-200)',
        borderRadius: 'var(--radius-md)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <span style={{ fontSize: '1.2rem' }}>📅</span>
          <span style={{ fontWeight: '600', color: 'var(--yellow-700)' }}>
            Year-End Tax Planning
          </span>
        </div>
        <div style={{ fontSize: '0.9rem', color: 'var(--gray-600)' }}>
          Best time for tax-loss harvesting is typically November-December. 
          We'll monitor your portfolio and notify you of optimal timing for maximum tax benefits.
        </div>
      </div>
    </div>
  )
}
