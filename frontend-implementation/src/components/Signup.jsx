import { useState } from 'react'
import axios from 'axios'

export default function Signup({ API_BASE, onSignup, onSwitchToLogin }) {
  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    // Validation
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    if (form.password.length < 6) {
      setError('Password must be at least 6 characters long')
      setLoading(false)
      return
    }

    try {
      const response = await axios.post(`${API_BASE}/signup`, {
        firstName: form.firstName,
        lastName: form.lastName,
        email: form.email,
        password: form.password
      })
      
      const { user, token } = response.data
      
      // Store token in localStorage
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
      
      onSignup(user)
    } catch (err) {
      setError(err.response?.data?.message || 'Signup failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const passwordStrength = (password) => {
    if (password.length < 6) return { strength: 'weak', color: 'var(--red-500)', width: '25%' }
    if (password.length < 8) return { strength: 'fair', color: 'var(--yellow-500)', width: '50%' }
    if (password.length < 12) return { strength: 'good', color: 'var(--blue-500)', width: '75%' }
    return { strength: 'strong', color: 'var(--green-500)', width: '100%' }
  }

  const strength = passwordStrength(form.password)

  return (
    <div className="card" style={{ maxWidth: '500px', margin: '0 auto' }}>
      <div className="card-header" style={{ textAlign: 'center' }}>
        <h2 className="card-title">🚀 Join MyFalconAdvisor</h2>
        <p className="card-subtitle">
          Create your account to start your financial journey
        </p>
      </div>

      <form onSubmit={handleSubmit} className="form-container">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div className="form-group">
            <label className="form-label">👤 First Name</label>
            <input
              type="text"
              className="form-input"
              value={form.firstName}
              onChange={(e) => setForm({ ...form, firstName: e.target.value })}
              placeholder="John"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">👤 Last Name</label>
            <input
              type="text"
              className="form-input"
              value={form.lastName}
              onChange={(e) => setForm({ ...form, lastName: e.target.value })}
              placeholder="Doe"
              required
            />
          </div>
        </div>

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
            placeholder="Create a secure password"
            required
          />
          {form.password && (
            <div style={{ marginTop: '8px' }}>
              <div style={{
                width: '100%',
                height: '4px',
                background: 'var(--gray-200)',
                borderRadius: '2px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: strength.width,
                  height: '100%',
                  background: strength.color,
                  transition: 'all 0.3s ease',
                  borderRadius: '2px'
                }}></div>
              </div>
              <div style={{
                fontSize: '0.75rem',
                color: strength.color,
                marginTop: '4px',
                textTransform: 'capitalize'
              }}>
                Password strength: {strength.strength}
              </div>
            </div>
          )}
        </div>

        <div className="form-group">
          <label className="form-label">🔒 Confirm Password</label>
          <input
            type="password"
            className="form-input"
            value={form.confirmPassword}
            onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
            placeholder="Confirm your password"
            required
          />
          {form.confirmPassword && form.password !== form.confirmPassword && (
            <div style={{ fontSize: '0.75rem', color: 'var(--red-500)', marginTop: '4px' }}>
              ❌ Passwords do not match
            </div>
          )}
        </div>

        {error && (
          <div className="notification error">
            ❌ {error}
          </div>
        )}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || form.password !== form.confirmPassword}
          style={{ width: '100%', marginTop: '16px' }}
        >
          {loading ? (
            <>
              <div className="loading-spinner"></div>
              Creating Account...
            </>
          ) : (
            <>
              ✨ Create Account
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
            Already have an account?
          </p>
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="btn btn-secondary"
            style={{ fontSize: '0.9rem' }}
          >
            Sign In
          </button>
        </div>

        {/* Terms and Privacy */}
        <div style={{
          marginTop: '16px',
          fontSize: '0.75rem',
          color: 'var(--gray-500)',
          textAlign: 'center',
          lineHeight: '1.4'
        }}>
          By creating an account, you agree to our{' '}
          <a href="#" style={{ color: 'var(--primary-500)' }}>Terms of Service</a>
          {' '}and{' '}
          <a href="#" style={{ color: 'var(--primary-500)' }}>Privacy Policy</a>
        </div>
      </form>
    </div>
  )
}
