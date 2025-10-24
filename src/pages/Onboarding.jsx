import { useState, useEffect } from 'react'
import axios from 'axios'

export default function Onboarding({ API_BASE, user }) {
  // Default form values for new users
  const initialForm = { income: '', expenses: '', goal: 'retirement', horizon: 10 }
    
  const [form, setForm] = useState(initialForm)
  const [status, setStatus] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingProfile, setIsLoadingProfile] = useState(false)

  // Fetch user profile data on component mount
  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const token = localStorage.getItem('token')
        if (token) {
          const response = await axios.get(`${API_BASE}/profile`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          
          const profileData = response.data
          
          // Map database goal values to form values
          const goalMapping = {
            'income': 'retirement',
            'growth': 'retirement', 
            'wealth_building': 'retirement',
            'retirement': 'retirement'
          }
          
          // Populate form with real user data
          setForm({
            income: profileData.annual_income || '',
            expenses: Math.round((profileData.annual_income || 0) * 0.7) || '', // Estimate expenses as 70% of income
            goal: goalMapping[profileData.primary_goal] || 'retirement',
            horizon: profileData.time_horizon || 10
          })
        }
      } catch (error) {
        console.error('Failed to fetch user profile:', error)
        // Keep default values if fetch fails
      } finally {
        setIsLoadingProfile(false)
      }
    }

    fetchUserProfile()
  }, [API_BASE])

  const submit = async (e) => {
    e.preventDefault()
    setStatus('')
    setIsLoading(true)
    try {
      const res = await axios.post(`${API_BASE}/onboarding`, form)
      setStatus({ type: 'success', message: res.data.msg })
    } catch {
      setStatus({ type: 'error', message: 'Failed to submit onboarding.' })
    } finally {
      setIsLoading(false)
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', { 
      style: 'currency', 
      currency: 'USD',
      minimumFractionDigits: 0 
    }).format(value || 0)
  }

  const disposableIncome = (form.income || 0) - (form.expenses || 0)

  // Show loading state while fetching profile data
  if (isLoadingProfile) {
    return (
      <div className="card interactive">
        <div className="card-header">
          <h2 className="card-title">🎯 Financial Profile Setup</h2>
          <p className="card-subtitle">Loading your profile data...</p>
        </div>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div className="loading-spinner" style={{ margin: '0 auto' }}></div>
          <p style={{ marginTop: '16px', color: 'var(--gray-600)' }}>
            Fetching your financial information...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="card interactive">
      
      <div className="card-header">
        <h2 className="card-title">🎯 Financial Profile Setup</h2>
        <p className="card-subtitle">
          Your financial profile loaded from database. Update as needed.
        </p>
      </div>

      <form onSubmit={submit} className="form-container">
        <div className="form-group">
          <label className="form-label">💰 Annual Income</label>
          <input 
            type="number" 
            className="form-input"
            value={form.income} 
            onChange={e => setForm({...form, income:e.target.value})}
            placeholder="e.g., 75000"
            required
          />
          <small style={{ color: 'var(--gray-500)', fontSize: '0.8rem' }}>
            Your gross annual income before taxes {form.income && '• Loaded from database'}
          </small>
        </div>

        <div className="form-group">
          <label className="form-label">💸 Annual Expenses</label>
          <input 
            type="number" 
            className="form-input"
            value={form.expenses} 
            onChange={e => setForm({...form, expenses:e.target.value})}
            placeholder="e.g., 45000"
            required
          />
          <small style={{ color: 'var(--gray-500)', fontSize: '0.8rem' }}>
            Your total yearly expenses (housing, food, transport, etc.) {form.expenses && '• Estimated from income'}
          </small>
        </div>

        <div className="form-group">
          <label className="form-label">🎯 Primary Financial Goal</label>
          <select 
            className="form-select"
            value={form.goal} 
            onChange={e => setForm({...form, goal:e.target.value})}
          >
            <option value="retirement">🏖️ Retirement Planning</option>
            <option value="house">🏠 House Down Payment</option>
            <option value="education">🎓 Education Fund</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">⏰ Investment Horizon</label>
          <input 
            type="range" 
            min="1" 
            max="40" 
            value={form.horizon} 
            onChange={e => setForm({...form, horizon:+e.target.value})}
            style={{
              width: '100%',
              height: '6px',
              borderRadius: '3px',
              background: 'var(--gray-200)',
              outline: 'none'
            }}
          />
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            fontSize: '0.875rem',
            color: 'var(--gray-500)',
            marginTop: '8px'
          }}>
            <span>1 year</span>
            <span style={{ fontWeight: '600', color: 'var(--primary-600)' }}>
              {form.horizon} years
            </span>
            <span>40+ years</span>
          </div>
        </div>

        {/* Financial Summary Card */}
        {(form.income && form.expenses) && (
          <div style={{
            background: 'linear-gradient(135deg, var(--primary-50), var(--primary-100))',
            padding: '20px',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--primary-200)',
            marginTop: '8px'
          }}>
            <h4 style={{ margin: '0 0 12px 0', color: 'var(--primary-700)' }}>
              📊 Quick Financial Summary
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px' }}>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)' }}>Income</div>
                <div style={{ fontSize: '1.1rem', fontWeight: '600' }}>{formatCurrency(form.income)}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)' }}>Expenses</div>
                <div style={{ fontSize: '1.1rem', fontWeight: '600' }}>{formatCurrency(form.expenses)}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)' }}>Available to Invest</div>
                <div style={{ 
                  fontSize: '1.1rem', 
                  fontWeight: '600',
                  color: disposableIncome > 0 ? 'var(--green-500)' : 'var(--red-500)'
                }}>
                  {formatCurrency(disposableIncome)}
                </div>
              </div>
            </div>
          </div>
        )}

        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={isLoading}
          style={{ marginTop: '16px' }}
        >
          {isLoading ? (
            <>
              <div className="loading-spinner"></div>
              Saving Profile...
            </>
          ) : (
            <>
              💾 Save Financial Profile
            </>
          )}
        </button>

        {status && (
          <div className={`notification ${status.type}`}>
            {status.type === 'success' ? '✅' : '❌'} {status.message}
          </div>
        )}
      </form>
    </div>
  )
}
