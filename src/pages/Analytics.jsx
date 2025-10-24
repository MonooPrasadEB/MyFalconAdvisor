import { useState, useEffect } from 'react'
import axios from 'axios'

export default function Analytics({ API_BASE, user, onNavigateBack }) {
  const [analyticsData, setAnalyticsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true)
        const token = localStorage.getItem('token')
        const response = await axios.get(`${API_BASE}/analytics`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        setAnalyticsData(response.data)
      } catch (error) {
        console.error('Failed to fetch analytics:', error)
        setError('Failed to load analytics data. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [API_BASE])

  if (loading) {
    return (
      <div className="card interactive">
        <div className="card-header">
          <h2 className="card-title">📊 Portfolio Analytics</h2>
          <p className="card-subtitle">Loading your analytics data...</p>
        </div>
        <div style={{ textAlign: 'center', padding: '60px' }}>
          <div className="loading-spinner" style={{ margin: '0 auto' }}></div>
          <p style={{ marginTop: '16px', color: 'var(--gray-600)' }}>
            Analyzing your portfolio performance...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card interactive">
        <div className="card-header">
          <h2 className="card-title">📊 Portfolio Analytics</h2>
          <p className="card-subtitle">Error loading analytics</p>
        </div>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div style={{ fontSize: '3rem', marginBottom: '16px' }}>⚠️</div>
          <p style={{ color: 'var(--red-600)', marginBottom: '20px' }}>{error}</p>
          <button 
            className="btn btn-primary"
            onClick={() => window.location.reload()}
          >
            🔄 Retry
          </button>
        </div>
      </div>
    )
  }

  if (!analyticsData) {
    return (
      <div className="card interactive">
        <div className="card-header">
          <h2 className="card-title">📊 Portfolio Analytics</h2>
          <p className="card-subtitle">No analytics data available</p>
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--gray-800)', margin: '0 0 8px 0' }}>
            📊 Portfolio Analytics
          </h1>
          <p style={{ color: 'var(--gray-600)', fontSize: '1rem', margin: '0' }}>
            Comprehensive analysis of your investment performance
          </p>
        </div>
        <button 
          className="btn btn-secondary"
          onClick={onNavigateBack}
          style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          ← Back to Dashboard
        </button>
      </div>

      {/* Performance Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        <div style={{
          padding: '24px',
          background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
          borderRadius: 'var(--radius-lg)',
          color: 'white',
          border: 'none'
        }}>
          <div style={{ fontSize: '0.9rem', opacity: 0.9, marginBottom: '8px' }}>Total Portfolio Value</div>
          <div style={{ fontSize: '2rem', fontWeight: '700', marginBottom: '8px' }}>
            ${analyticsData.portfolio_performance.current_value.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>
            {analyticsData.portfolio_performance.total_return_percent >= 0 ? '+' : ''}{analyticsData.portfolio_performance.total_return_percent}% return
          </div>
        </div>

        <div style={{
          padding: '24px',
          background: 'white',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--gray-200)',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <div style={{ fontSize: '0.9rem', color: 'var(--gray-600)', marginBottom: '8px' }}>Volatility</div>
          <div style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--gray-800)', marginBottom: '8px' }}>
            {analyticsData.portfolio_performance.volatility.toFixed(1)}%
          </div>
          <div style={{ fontSize: '0.9rem', color: 'var(--gray-600)' }}>Risk measure</div>
        </div>

        <div style={{
          padding: '24px',
          background: 'white',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--gray-200)',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <div style={{ fontSize: '0.9rem', color: 'var(--gray-600)', marginBottom: '8px' }}>Total Holdings</div>
          <div style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--gray-800)', marginBottom: '8px' }}>
            {analyticsData.summary.total_holdings}
          </div>
          <div style={{ fontSize: '0.9rem', color: 'var(--gray-600)' }}>Diversified portfolio</div>
        </div>

        <div style={{
          padding: '24px',
          background: 'white',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--gray-200)',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <div style={{ fontSize: '0.9rem', color: 'var(--gray-600)', marginBottom: '8px' }}>Diversification Score</div>
          <div style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--gray-800)', marginBottom: '8px' }}>
            {analyticsData.summary.diversification_score}/10
          </div>
          <div style={{ fontSize: '0.9rem', color: 'var(--gray-600)' }}>Portfolio health</div>
        </div>
      </div>

      {/* Portfolio Performance Chart */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{
          padding: '24px',
          background: 'white',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--gray-200)',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '600', color: 'var(--gray-800)', marginBottom: '8px' }}>
            📈 Portfolio Value Performance
          </h3>
          <p style={{ color: 'var(--gray-600)', fontSize: '0.9rem', marginBottom: '24px' }}>
            Your portfolio's performance over the last 30 days
          </p>
          
          {/* Professional Portfolio Chart */}
          <div style={{ 
            height: '400px', 
            position: 'relative',
            background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
            borderRadius: 'var(--radius-md)',
            padding: '24px',
            border: '1px solid var(--gray-200)'
          }}>
            <svg 
              width="100%" 
              height="350" 
              style={{ 
                background: 'white',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--gray-200)'
              }}
            >
              {(() => {
                const data = analyticsData.portfolio_performance.historical_data;
                const width = 900;
                const height = 350;
                const padding = { top: 30, right: 50, bottom: 60, left: 80 };
                const chartWidth = width - padding.left - padding.right;
                const chartHeight = height - padding.top - padding.bottom;
                
                // Find min/max values for scaling
                const values = data.map(d => d.value);
                const minValue = Math.min(...values);
                const maxValue = Math.max(...values);
                const valueRange = maxValue - minValue;
                const paddingValue = valueRange * 0.1;
                const yMin = minValue - paddingValue;
                const yMax = maxValue + paddingValue;
                const yRange = yMax - yMin;
                
                // Create Y-axis labels
                const yTicks = 6;
                const yLabels = [];
                for (let i = 0; i <= yTicks; i++) {
                  const value = yMin + (yRange * i / yTicks);
                  yLabels.push(value);
                }
                
                // Create X-axis labels (every 5 days)
                const xLabels = [];
                const xStep = Math.max(1, Math.floor(data.length / 8));
                for (let i = 0; i < data.length; i += xStep) {
                  xLabels.push({ index: i, date: data[i].date });
                }
                
                // Create points for the line
                const points = data.map((day, index) => {
                  const x = padding.left + (index / (data.length - 1)) * chartWidth;
                  const y = padding.top + chartHeight - ((day.value - yMin) / yRange) * chartHeight;
                  return `${x},${y}`;
                }).join(' ');
                
                // Create area fill
                const areaPoints = [
                  `${padding.left},${padding.top + chartHeight}`,
                  ...points.split(' '),
                  `${padding.left + chartWidth},${padding.top + chartHeight}`,
                  `${padding.left},${padding.top + chartHeight}`
                ].join(' ');
                
                return (
                  <>
                    {/* Grid lines */}
                    {yLabels.map((value, i) => {
                      const y = padding.top + chartHeight - (i / yTicks) * chartHeight;
                      return (
                        <line
                          key={i}
                          x1={padding.left}
                          y1={y}
                          x2={padding.left + chartWidth}
                          y2={y}
                          stroke="#e5e7eb"
                          strokeWidth="1"
                          strokeDasharray="2,2"
                        />
                      );
                    })}
                    
                    {/* Area fill */}
                    <polyline
                      fill="url(#portfolioGradient)"
                      points={areaPoints}
                    />
                    
                    {/* Main line */}
                    <polyline
                      fill="none"
                      stroke="#2563eb"
                      strokeWidth="4"
                      points={points}
                    />
                    
                    {/* Data points */}
                    {data.map((day, index) => {
                      const x = padding.left + (index / (data.length - 1)) * chartWidth;
                      const y = padding.top + chartHeight - ((day.value - yMin) / yRange) * chartHeight;
                      const isHighlight = index === data.length - 1 || index % 6 === 0;
                      return (
                        <g key={index}>
                          <circle
                            cx={x}
                            cy={y}
                            r={isHighlight ? "5" : "3"}
                            fill={isHighlight ? "#2563eb" : "#60a5fa"}
                            stroke="white"
                            strokeWidth="2"
                          />
                          {isHighlight && (
                            <text
                              x={x}
                              y={y - 12}
                              textAnchor="middle"
                              fontSize="11"
                              fill="#374151"
                              fontWeight="600"
                            >
                              ${(day.value / 1000).toFixed(0)}k
                            </text>
                          )}
                        </g>
                      );
                    })}
                    
                    {/* Y-axis labels */}
                    {yLabels.map((value, i) => {
                      const y = padding.top + chartHeight - (i / yTicks) * chartHeight;
                      return (
                        <text
                          key={i}
                          x={padding.left - 15}
                          y={y + 4}
                          textAnchor="end"
                          fontSize="12"
                          fill="#6b7280"
                          fontWeight="500"
                        >
                          ${(value / 1000).toFixed(0)}k
                        </text>
                      );
                    })}
                    
                    {/* X-axis labels */}
                    {xLabels.map((label, i) => {
                      const x = padding.left + (label.index / (data.length - 1)) * chartWidth;
                      const date = new Date(label.date);
                      return (
                        <text
                          key={i}
                          x={x}
                          y={height - 15}
                          textAnchor="middle"
                          fontSize="11"
                          fill="#6b7280"
                          fontWeight="500"
                        >
                          {date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </text>
                      );
                    })}
                    
                    {/* Axes */}
                    <line
                      x1={padding.left}
                      y1={padding.top}
                      x2={padding.left}
                      y2={padding.top + chartHeight}
                      stroke="#374151"
                      strokeWidth="2"
                    />
                    <line
                      x1={padding.left}
                      y1={padding.top + chartHeight}
                      x2={padding.left + chartWidth}
                      y2={padding.top + chartHeight}
                      stroke="#374151"
                      strokeWidth="2"
                    />
                    
                    {/* Y-axis label */}
                    <text
                      x="25"
                      y={height / 2}
                      textAnchor="middle"
                      fontSize="13"
                      fill="#374151"
                      fontWeight="600"
                      transform={`rotate(-90, 25, ${height / 2})`}
                    >
                      Portfolio Value ($)
                    </text>
                    
                    {/* X-axis label */}
                    <text
                      x={width / 2}
                      y={height - 5}
                      textAnchor="middle"
                      fontSize="13"
                      fill="#374151"
                      fontWeight="600"
                    >
                      Date (Last 30 Days)
                    </text>
                    
                    {/* Performance indicator */}
                    <rect
                      x={padding.left + chartWidth - 140}
                      y={padding.top + 15}
                      width="130"
                      height="40"
                      fill="white"
                      stroke="#e5e7eb"
                      strokeWidth="1"
                      rx="6"
                    />
                    <text
                      x={padding.left + chartWidth - 75}
                      y={padding.top + 25}
                      textAnchor="middle"
                      fontSize="12"
                      fill="#374151"
                      fontWeight="700"
                    >
                      {analyticsData.portfolio_performance.total_return_percent >= 0 ? '+' : ''}{analyticsData.portfolio_performance.total_return_percent}%
                    </text>
                    <text
                      x={padding.left + chartWidth - 75}
                      y={padding.top + 40}
                      textAnchor="middle"
                      fontSize="10"
                      fill="#6b7280"
                    >
                      Total Return
                    </text>
                    
                    {/* Gradient definition */}
                    <defs>
                      <linearGradient id="portfolioGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="#2563eb" stopOpacity="0.3"/>
                        <stop offset="100%" stopColor="#2563eb" stopOpacity="0.05"/>
                      </linearGradient>
                    </defs>
                  </>
                );
              })()}
            </svg>
          </div>
        </div>
      </div>

      {/* Stock Performance Comparison */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{
          padding: '24px',
          background: 'white',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--gray-200)',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '600', color: 'var(--gray-800)', marginBottom: '8px' }}>
            📊 Individual Stock Performance Comparison
          </h3>
          <p style={{ color: 'var(--gray-600)', fontSize: '0.9rem', marginBottom: '24px' }}>
            Performance comparison of your top holdings over the last 30 days
          </p>
          
          {/* Multi-Line Chart */}
          <div style={{
            height: '400px',
            background: 'linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%)',
            borderRadius: 'var(--radius-md)',
            padding: '20px',
            border: '1px solid var(--gray-200)'
          }}>
            <svg 
              width="100%" 
              height="350" 
              style={{ 
                background: 'white',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--gray-200)'
              }}
            >
              {(() => {
                const stocks = analyticsData.stock_performance.slice(0, 6);
                const width = 900;
                const height = 350;
                const padding = { top: 30, right: 80, bottom: 60, left: 80 };
                const chartWidth = width - padding.left - padding.right;
                const chartHeight = height - padding.top - padding.bottom;
                
                // Color palette
                const colors = [
                  '#2563eb', '#dc2626', '#059669', '#7c3aed', '#ea580c', '#0891b2'
                ];
                
                // Get all values for scaling
                const allValues = [];
                stocks.forEach(stock => {
                  allValues.push(...stock.historical_data.map(d => d.value));
                });
                const minValue = Math.min(...allValues);
                const maxValue = Math.max(...allValues);
                const valueRange = maxValue - minValue;
                const paddingValue = valueRange * 0.1;
                const yMin = minValue - paddingValue;
                const yMax = maxValue + paddingValue;
                const yRange = yMax - yMin;
                
                // Y-axis labels
                const yTicks = 6;
                const yLabels = [];
                for (let i = 0; i <= yTicks; i++) {
                  const value = yMin + (yRange * i / yTicks);
                  yLabels.push(value);
                }
                
                // X-axis labels
                const dataLength = stocks[0]?.historical_data.length || 0;
                const xLabels = [];
                const xStep = Math.max(1, Math.floor(dataLength / 8));
                for (let i = 0; i < dataLength; i += xStep) {
                  if (stocks[0]?.historical_data[i]) {
                    xLabels.push({ index: i, date: stocks[0].historical_data[i].date });
                  }
                }
                
                return (
                  <>
                    {/* Grid lines */}
                    {yLabels.map((value, i) => {
                      const y = padding.top + chartHeight - (i / yTicks) * chartHeight;
                      return (
                        <line
                          key={i}
                          x1={padding.left}
                          y1={y}
                          x2={padding.left + chartWidth}
                          y2={y}
                          stroke="#e5e7eb"
                          strokeWidth="1"
                          strokeDasharray="2,2"
                        />
                      );
                    })}
                    
                    {/* Stock lines */}
                    {stocks.map((stock, stockIndex) => {
                      const color = colors[stockIndex % colors.length];
                      const data = stock.historical_data;
                      
                      const points = data.map((day, index) => {
                        const x = padding.left + (index / (data.length - 1)) * chartWidth;
                        const y = padding.top + chartHeight - ((day.value - yMin) / yRange) * chartHeight;
                        return `${x},${y}`;
                      }).join(' ');
                      
                      return (
                        <g key={stockIndex}>
                          <polyline
                            fill="none"
                            stroke={color}
                            strokeWidth="3"
                            points={points}
                          />
                          {data.map((day, index) => {
                            const x = padding.left + (index / (data.length - 1)) * chartWidth;
                            const y = padding.top + chartHeight - ((day.value - yMin) / yRange) * chartHeight;
                            const isHighlight = index === data.length - 1 || index % 8 === 0;
                            return (
                              <circle
                                key={index}
                                cx={x}
                                cy={y}
                                r={isHighlight ? "3" : "2"}
                                fill={color}
                                stroke="white"
                                strokeWidth="1"
                              />
                            );
                          })}
                        </g>
                      );
                    })}
                    
                    {/* Y-axis labels */}
                    {yLabels.map((value, i) => {
                      const y = padding.top + chartHeight - (i / yTicks) * chartHeight;
                      return (
                        <text
                          key={i}
                          x={padding.left - 15}
                          y={y + 4}
                          textAnchor="end"
                          fontSize="12"
                          fill="#6b7280"
                          fontWeight="500"
                        >
                          ${(value / 1000).toFixed(1)}k
                        </text>
                      );
                    })}
                    
                    {/* X-axis labels */}
                    {xLabels.map((label, i) => {
                      const x = padding.left + (label.index / (dataLength - 1)) * chartWidth;
                      const date = new Date(label.date);
                      return (
                        <text
                          key={i}
                          x={x}
                          y={height - 15}
                          textAnchor="middle"
                          fontSize="11"
                          fill="#6b7280"
                          fontWeight="500"
                        >
                          {date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </text>
                      );
                    })}
                    
                    {/* Axes */}
                    <line
                      x1={padding.left}
                      y1={padding.top}
                      x2={padding.left}
                      y2={padding.top + chartHeight}
                      stroke="#374151"
                      strokeWidth="2"
                    />
                    <line
                      x1={padding.left}
                      y1={padding.top + chartHeight}
                      x2={padding.left + chartWidth}
                      y2={padding.top + chartHeight}
                      stroke="#374151"
                      strokeWidth="2"
                    />
                    
                    {/* Y-axis label */}
                    <text
                      x="25"
                      y={height / 2}
                      textAnchor="middle"
                      fontSize="13"
                      fill="#374151"
                      fontWeight="600"
                      transform={`rotate(-90, 25, ${height / 2})`}
                    >
                      Stock Value ($)
                    </text>
                    
                    {/* X-axis label */}
                    <text
                      x={width / 2}
                      y={height - 5}
                      textAnchor="middle"
                      fontSize="13"
                      fill="#374151"
                      fontWeight="600"
                    >
                      Date (Last 30 Days)
                    </text>
                    
                    {/* Legend */}
                    <g transform={`translate(${padding.left + chartWidth - 200}, ${padding.top + 15})`}>
                      {stocks.map((stock, index) => {
                        const color = colors[index % colors.length];
                        const y = index * 25;
                        return (
                          <g key={index}>
                            <line
                              x1="0"
                              y1={y + 10}
                              x2="20"
                              y2={y + 10}
                              stroke={color}
                              strokeWidth="4"
                            />
                            <text
                              x="25"
                              y={y + 15}
                              fontSize="11"
                              fill="#374151"
                              fontWeight="600"
                            >
                              {stock.symbol} ({stock.allocation.toFixed(1)}%)
                            </text>
                          </g>
                        );
                      })}
                    </g>
                  </>
                );
              })()}
            </svg>
          </div>
        </div>
      </div>

      {/* Stock Performance Cards */}
      <div style={{
        padding: '24px',
        background: 'white',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--gray-200)',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
      }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: '600', color: 'var(--gray-800)', marginBottom: '8px' }}>
          🎯 Individual Stock Analysis
        </h3>
        <p style={{ color: 'var(--gray-600)', fontSize: '0.9rem', marginBottom: '24px' }}>
          Detailed performance metrics for each holding
        </p>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
          {analyticsData.stock_performance.slice(0, 8).map((stock, index) => {
            const colors = ['#2563eb', '#dc2626', '#059669', '#7c3aed', '#ea580c', '#0891b2', '#dc2626', '#059669'];
            const color = colors[index % colors.length];
            const firstValue = stock.historical_data[0]?.value || 0;
            const lastValue = stock.historical_data[stock.historical_data.length - 1]?.value || 0;
            const performance = ((lastValue - firstValue) / firstValue) * 100;
            
            return (
              <div key={index} style={{
                padding: '20px',
                background: 'white',
                borderRadius: 'var(--radius-lg)',
                border: `2px solid ${color}20`,
                borderLeft: `4px solid ${color}`,
                transition: 'all 0.2s ease',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 8px 25px rgba(0,0,0,0.1)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = 'none';
              }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div>
                    <div style={{ fontWeight: '700', color: 'var(--gray-800)', fontSize: '1.1rem' }}>
                      {stock.symbol}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--gray-500)', fontWeight: '500' }}>
                      {stock.name}
                    </div>
                  </div>
                  <div style={{
                    width: '16px',
                    height: '16px',
                    borderRadius: '50%',
                    background: color
                  }}></div>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div>
                    <div style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--gray-800)' }}>
                      ${stock.current_value.toLocaleString()}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--gray-500)' }}>
                      {stock.allocation.toFixed(1)}% of portfolio
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ 
                      fontSize: '1rem', 
                      fontWeight: '700', 
                      color: performance >= 0 ? '#059669' : '#dc2626'
                    }}>
                      {performance >= 0 ? '+' : ''}{performance.toFixed(1)}%
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--gray-500)' }}>
                      30-day return
                    </div>
                  </div>
                </div>
                
                {/* Performance bar */}
                <div style={{
                  height: '6px',
                  background: '#e5e7eb',
                  borderRadius: '3px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${Math.min(Math.abs(performance), 100)}%`,
                    background: performance >= 0 ? '#059669' : '#dc2626',
                    borderRadius: '3px'
                  }}></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  )
}
