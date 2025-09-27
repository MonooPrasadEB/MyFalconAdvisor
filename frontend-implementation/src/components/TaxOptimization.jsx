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
          <h3 className="card-title">💰 Tax-Loss Harvesting</h3>
          <p className="card-subtitle">No harvesting opportunities currently available</p>
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
        <h3 className="card-title">💰 Tax-Loss Harvesting Opportunities</h3>
        <p className="card-subtitle">
          Optimize your tax situation by harvesting investment losses
        </p>
      </div>

      {/* Summary Card */}
      <div style={{
        background: 'linear-gradient(135deg, var(--primary-500), var(--primary-600))',
        color: 'white',
        padding: '24px',
        borderRadius: 'var(--radius-lg)',
        marginBottom: '24px'
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '4px' }}>
              {opportunities.length}
            </div>
            <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>
              Harvesting Opportunities
            </div>
          </div>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '4px' }}>
              {formatCurrency(totalSavings)}
            </div>
            <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>
              Potential Tax Savings
            </div>
          </div>
          <div>
            <div style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '4px' }}>
              {taxData.tax_optimization.current_tax_bracket}
            </div>
            <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>
              Current Tax Bracket
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
                  {opp.shares} shares • Purchased {opp.purchase_date}
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
