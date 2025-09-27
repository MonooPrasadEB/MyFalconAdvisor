import { useEffect, useState } from 'react'
import axios from 'axios'
import ChatUI from './components/ChatUI'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import Learning from './pages/Learning'
import Gamification from './components/Gamification'
import Login from './components/Login'
import Signup from './components/Signup'
import { initializeDemoData } from './utils/demoData'
import './styles/modern-ui.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export default function App() {
  const [backendMsg, setBackendMsg] = useState('')
  const [view, setView] = useState('onboarding') // onboarding | chat | dashboard
  const [authView, setAuthView] = useState('login') // login | signup
  const [isConnected, setIsConnected] = useState(false)
  const [user, setUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    // Check for existing authentication
    const token = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    
    if (token && savedUser) {
      try {
        const userData = JSON.parse(savedUser)
        setUser(userData)
        setIsAuthenticated(true)
        // Set authorization header for future requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      } catch (error) {
        // Invalid stored data, clear it
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    }

    // Check backend health
    axios.get(`${API_BASE}/health`)
      .then(r => {
        setBackendMsg(r.data.msg)
        setIsConnected(true)
      })
      .catch(() => {
        setBackendMsg('Backend not reachable')
        setIsConnected(false)
      })
  }, [])

  const handleLogin = (userData) => {
    setUser(userData)
    setIsAuthenticated(true)
    
    // Initialize demo data for demo user
    if (userData.id === "1") {
      initializeDemoData(userData.id)
      console.log('Demo data initialized for user:', userData.id)
      setView('dashboard') // Demo user goes directly to dashboard
    } else {
      setView('onboarding') // Other users go to onboarding
    }
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
            <div>
              <h1 className="app-title">MyFalconAdvisor</h1>
              <p className="app-subtitle">AI-Powered Financial Advisory Platform</p>
            </div>
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
          <div>
            <h1 className="app-title">MyFalconAdvisor</h1>
            <p className="app-subtitle">Welcome back, {user?.firstName || 'User'}! 👋</p>
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