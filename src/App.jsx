import { useEffect, useState } from 'react'
import axios from 'axios'
import ChatUI from './components/ChatUI'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Learning from './pages/Learning'
import Gamification from './components/Gamification'
import Login from './components/Login'
import Signup from './components/Signup'
// Demo data import removed - ready for database integration
import './styles/modern-ui.css'

// Import logo
import logoImage from './assets/logo.jpeg'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export default function App() {
  const [backendMsg, setBackendMsg] = useState('')
  const [view, setView] = useState('onboarding') // onboarding | chat | dashboard
  const [authView, setAuthView] = useState('login') // login | signup
  const [isConnected, setIsConnected] = useState(false)
  const [user, setUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    // Set demo user and skip authentication for now
    const demoUser = {
      id: "usr_348784c4-6f83-4857-b7dc-f5132a38dfee",
      firstName: "Elijah",
      lastName: "Martin",
      email: "elijah.martin@example.com"
    }
    const token = "usr_348784c4-6f83-4857-b7dc-f5132a38dfee"
    
    // Store token in localStorage
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(demoUser))
    
    setUser(demoUser)
    setIsAuthenticated(true)
    setIsConnected(true)
    setBackendMsg('Connected')
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }, [])

  const handleLogin = (userData) => {
    const token = localStorage.getItem('token')
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
    
    setUser(userData)
    setIsAuthenticated(true)
    
    // All users go to onboarding after login
    setView('onboarding')
  }

  const handleSignup = (userData) => {
    setUser(userData)
    setIsAuthenticated(true)
    setView('onboarding') // Redirect to onboarding after signup
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    delete axios.defaults.headers.common['Authorization']
    setUser(null)
    setIsAuthenticated(false)
    setView('onboarding')
  }

  const handleNavigateToLearning = (topic = null) => {
    setView('learning')
    // Store the topic to highlight in learning page
    if (topic) {
      localStorage.setItem('learningTopicToOpen', topic)
    }
  }

  // Show authentication screens if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="app-container">
        <div className="app-content">
          <header className="app-header" style={{ justifyContent: 'center', textAlign: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', justifyContent: 'center' }}>
              {logoImage && <img src={logoImage} alt="MyFalconAdvisor Logo" className="app-logo" />}
              <h1 className="app-title">MyFalconAdvisor</h1>
            </div>
            <p className="app-subtitle">AI-Powered Financial Advisory Platform</p>
          </header>
          
          <div className={`status-badge ${isConnected ? 'connected' : 'disconnected'}`} style={{ marginBottom: '32px' }}>
            <div className="status-indicator"></div>
            Backend: {backendMsg}
          </div>

          <main style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
            {authView === 'login' ? (
              <Login 
                API_BASE={API_BASE}
                onLogin={handleLogin}
                onSwitchToSignup={() => setAuthView('signup')}
              />
            ) : (
              <Signup 
                API_BASE={API_BASE}
                onSignup={handleSignup}
                onSwitchToLogin={() => setAuthView('login')}
              />
            )}
          </main>
        </div>
      </div>
    )
  }

  // Show main application if authenticated
  return (
    <div className="app-container">
      <div className="app-content">
        <header className="app-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {logoImage && <img src={logoImage} alt="MyFalconAdvisor Logo" className="app-logo" />}
            <div>
              <h1 className="app-title">MyFalconAdvisor</h1>
              <p className="app-subtitle">Welcome back, {user?.firstName || 'User'}! 👋</p>
            </div>
          </div>
          <nav className="nav-container">
            <button 
              className={`nav-button ${view === 'onboarding' ? 'active' : ''}`}
              onClick={() => setView('onboarding')}
            >
              📋 Profile
            </button>
            <button 
              className={`nav-button ${view === 'chat' ? 'active' : ''}`}
              onClick={() => setView('chat')}
            >
              💬 Chat
            </button>
            <button 
              className={`nav-button ${view === 'dashboard' ? 'active' : ''}`}
              onClick={() => setView('dashboard')}
            >
              📊 Dashboard
            </button>
            <button 
              className={`nav-button ${view === 'learning' ? 'active' : ''}`}
              onClick={() => setView('learning')}
            >
              🎓 Learn
            </button>
            <button 
              className={`nav-button ${view === 'gamification' ? 'active' : ''}`}
              onClick={() => setView('gamification')}
            >
              🎮 Rewards
            </button>
            <button 
              className="nav-button"
              onClick={handleLogout}
              style={{ background: 'var(--red-100)', color: 'var(--red-600)' }}
            >
              🚪 Logout
            </button>
          </nav>
        </header>
        
        <div className={`status-badge ${isConnected ? 'connected' : 'disconnected'}`}>
          <div className="status-indicator"></div>
          Backend: {backendMsg} • Logged in as {user?.email}
        </div>

        <main>
          {view === 'onboarding' && <Onboarding API_BASE={API_BASE} user={user} />}
          {view === 'chat' && <ChatUI API_BASE={API_BASE} user={user} onNavigateToLearning={handleNavigateToLearning} />}
          {view === 'dashboard' && <Dashboard API_BASE={API_BASE} user={user} />}
          {view === 'learning' && <Learning API_BASE={API_BASE} user={user} />}
          {view === 'gamification' && <Gamification user={user} />}
        </main>
      </div>
    </div>
  )
}