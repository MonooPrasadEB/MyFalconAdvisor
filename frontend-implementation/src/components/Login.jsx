import { useState } from 'react'
import axios from 'axios'

export default function Login({ API_BASE, onLogin, onSwitchToSignup }) {
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      const response = await axios.post(`${API_BASE}/login`, form)
      const { user, token } = response.data
      
      // Store token in localStorage
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
      
      onLogin(user)
    } catch (err) {
      setError(err.response?.data?.message || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card" style={{ maxWidth: '500px', margin: '0 auto' }}>
      <div className="card-header" style={{ textAlign: 'center' }}>
        <h2 className="card-title">🔐 Welcome Back</h2>
        <p className="card-subtitle">
          Sign in to access your financial advisor dashboard
        </p>
      </div>

      <form onSubmit={handleSubmit} className="form-container">
        <div className="form-group">
          <label className="form-label">📧 Email Address</label>
          <input
            type="email"
            className="form-input"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            placeholder="your.email@example.com"
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label">🔒 Password</label>
          <input
            type="password"
            className="form-input"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            placeholder="Enter your password"
            required
          />
        </div>

        {error && (
          <div className="notification error">
            ❌ {error}
          </div>
        )}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading}
          style={{ width: '100%', marginTop: '16px' }}
        >
          {loading ? (
            <>
              <div className="loading-spinner"></div>
              Signing In...
            </>
          ) : (
            <>
              🚀 Sign In
            </>
          )}
        </button>

        <div style={{ 
          textAlign: 'center', 
          marginTop: '24px',
          padding: '16px',
          background: 'var(--gray-50)',
          borderRadius: 'var(--radius-md)'
        }}>
          <p style={{ margin: '0 0 8px 0', fontSize: '0.9rem', color: 'var(--gray-600)' }}>
            Don't have an account?
          </p>
          <button
            type="button"
            onClick={onSwitchToSignup}
            className="btn btn-secondary"
            style={{ fontSize: '0.9rem' }}
          >
            Create Account
          </button>
        </div>

        {/* Demo Credentials */}
        <div style={{
          marginTop: '16px',
          padding: '12px',
          background: 'var(--primary-50)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--primary-200)'
        }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--primary-700)', marginBottom: '8px' }}>
            <strong>📝 Demo Credentials:</strong>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--gray-600)', fontFamily: 'monospace' }}>
            Email: demo@falconadvisor.com<br/>
            Password: demo123
          </div>
        </div>
      </form>
    </div>
  )
}
