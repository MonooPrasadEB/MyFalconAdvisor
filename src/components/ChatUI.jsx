import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function ChatUI({ API_BASE, user, onNavigateToLearning }) {
  const [messages, setMessages] = useState([])
  const [initialGreeting, setInitialGreeting] = useState(null)
  const [isLoadingGreeting, setIsLoadingGreeting] = useState(true)
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isInitialLoad, setIsInitialLoad] = useState(true)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  // Fetch user data and create personalized greeting
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem('token')
        if (token) {
          // Fetch user profile
          const profileResponse = await axios.get(`${API_BASE}/profile`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          const profile = profileResponse.data
          
          // Fetch portfolio data
          const portfolioResponse = await axios.get(`${API_BASE}/portfolio`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          const portfolio = portfolioResponse.data
          
                  // Create personalized greeting
                  const greeting = {
                    role: 'assistant',
                    content: `👋 Hello ${profile.first_name || 'there'}! I'm your personal AI financial advisor.
        
        I can see your portfolio is valued at **$${portfolio.total_value.toLocaleString()}** with ${portfolio.holdings?.length || 0} holdings. I'm here to help you make the most of your investments!
        
        **I can help you with:**
        * Portfolio performance analysis
        * Investment strategy optimization  
        * Market trends and insights
        * Risk management advice
        * Financial planning guidance
        
        **Try asking me:**
        * "How is my portfolio performing?"
        * "What are the current market trends?"
        * "Should I rebalance my holdings?"
        * "What's your investment outlook?"
        
        What would you like to know about your investments?`,
                    timestamp: new Date()
                  }
          
          setInitialGreeting(greeting)
          setMessages([greeting])
        }
      } catch (error) {
        console.error('Failed to fetch user data:', error)
                // Fallback greeting
                const fallbackGreeting = {
                  role: 'assistant',
                  content: `👋 Hello! I'm your personal AI financial advisor. I'm here to help you with investment questions and portfolio analysis.
        
        **I can help you with:**
        * Portfolio performance analysis
        * Investment strategy optimization  
        * Market trends and insights
        * Risk management advice
        
        What would you like to know about your investments?`,
                  timestamp: new Date()
                }
        setInitialGreeting(fallbackGreeting)
        setMessages([fallbackGreeting])
      } finally {
        setIsLoadingGreeting(false)
      }
    }
    
    fetchUserData()
  }, [API_BASE])

  useEffect(() => {
    // Only scroll to bottom for new messages, not on initial load
    if (!isInitialLoad) {
      scrollToBottom()
    } else {
      setIsInitialLoad(false)
    }
  }, [messages, isInitialLoad])

  const sendMessage = async () => {
    if (!input.trim()) return
    
    const userMsg = { 
      role: 'user', 
      content: input, 
      timestamp: new Date() 
    }
    
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setIsTyping(true)

    try {
      const token = localStorage.getItem('token')
      const res = await axios.post(`${API_BASE}/chat`, 
        { query: userMsg.content },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      const bot = res.data
      
      setTimeout(() => {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: bot.advisor_reply,
          timestamp: new Date(),
          complianceChecked: bot.compliance_checked,
          complianceNotes: bot.compliance_notes,
          actions: bot.suggested_actions,
          learningResources: bot.learning_suggestions // New field for learning suggestions
        }])
        setIsTyping(false)
      }, 1000) // Simulate thinking time
      
    } catch (e) {
      setTimeout(() => {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: '❌ Sorry, I encountered an error. Please make sure the backend is running and try again.',
          timestamp: new Date(),
          isError: true
        }])
        setIsTyping(false)
      }, 500)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  return (
    <div className="card" style={{ padding: 0 }}>
      <div className="card-header" style={{ margin: 0, padding: '20px 24px', borderBottom: '1px solid var(--gray-200)' }}>
        <h2 className="card-title">💬 Financial Advisor Chat</h2>
        <p className="card-subtitle">
          Ask questions about your portfolio, investments, or financial planning
        </p>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {isLoadingGreeting ? (
            <div className="chat-message assistant">
              <div className="chat-avatar assistant">🤖</div>
              <div className="chat-content">
                <div className="chat-bubble assistant">
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span>Loading your personalized advisor...</span>
                    <div style={{ display: 'flex', gap: '2px' }}>
                      <div className="typing-dot" style={{ animationDelay: '0ms' }}></div>
                      <div className="typing-dot" style={{ animationDelay: '150ms' }}></div>
                      <div className="typing-dot" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            messages.map((message, i) => (
            <div key={i} className={`chat-message ${message.role}`}>
              <div className={`chat-avatar ${message.role}`}>
                {message.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="chat-content">
                <div className={`chat-bubble ${message.role} ${message.isError ? 'error' : ''}`}>
                  {message.role === 'assistant' ? (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        // Customize markdown rendering
                        p: ({node, ...props}) => <p style={{margin: '0 0 12px 0'}} {...props} />,
                        ul: ({node, ...props}) => <ul style={{margin: '8px 0', paddingLeft: '24px'}} {...props} />,
                        ol: ({node, ...props}) => <ol style={{margin: '8px 0', paddingLeft: '24px'}} {...props} />,
                        li: ({node, ...props}) => <li style={{margin: '4px 0'}} {...props} />,
                        strong: ({node, ...props}) => <strong style={{color: 'var(--primary-700)'}} {...props} />,
                        h3: ({node, ...props}) => <h3 style={{margin: '16px 0 8px 0', fontSize: '1.1rem'}} {...props} />,
                        table: ({node, ...props}) => (
                          <table style={{
                            width: '100%',
                            borderCollapse: 'collapse',
                            margin: '12px 0',
                            fontSize: '0.9rem'
                          }} {...props} />
                        ),
                        thead: ({node, ...props}) => (
                          <thead style={{
                            background: 'var(--primary-50)',
                            borderBottom: '2px solid var(--primary-300)'
                          }} {...props} />
                        ),
                        th: ({node, ...props}) => (
                          <th style={{
                            padding: '10px 12px',
                            textAlign: 'left',
                            fontWeight: '600',
                            color: 'var(--primary-700)',
                            borderBottom: '2px solid var(--primary-300)'
                          }} {...props} />
                        ),
                        td: ({node, ...props}) => (
                          <td style={{
                            padding: '10px 12px',
                            borderBottom: '1px solid var(--gray-200)'
                          }} {...props} />
                        ),
                        tr: ({node, ...props}) => (
                          <tr style={{
                            transition: 'background 0.15s',
                          }} {...props} />
                        ),
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    message.content
                  )}
                  
                  {/* Hide compliance notes - they're just generic disclaimers */}
                  
                  {/* Show suggested actions */}
                  {message.role === 'assistant' && message.actions && message.actions.length > 0 && (
                    <div style={{ marginTop: '8px' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)', marginBottom: '4px' }}>
                        Suggested Actions:
                      </div>
                      {message.actions.map((action, idx) => (
                        <div key={idx} style={{
                          padding: '6px 10px',
                          background: 'var(--primary-50)',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '0.8rem',
                          marginBottom: '4px',
                          color: 'var(--primary-700)'
                        }}>
                          📈 {action.type}: {action.from} → {action.to} ({action.amount_pct}%)
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* Show learning resources */}
                  {message.role === 'assistant' && message.learningResources && message.learningResources.length > 0 && (
                    <div style={{ marginTop: '8px' }}>
                      <div style={{ fontSize: '0.8rem', color: 'var(--gray-600)', marginBottom: '4px' }}>
                        📚 Learn More:
                      </div>
                      {message.learningResources.map((resource, idx) => (
                        <div key={idx} style={{
                          padding: '6px 10px',
                          background: 'var(--purple-50)',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '0.8rem',
                          marginBottom: '4px',
                          color: 'var(--purple-700)',
                          cursor: 'pointer',
                          border: '1px solid var(--purple-200)'
                        }}
                        onClick={(e) => {
                          e.preventDefault()
                          console.log('Learning suggestion clicked:', resource.topic, 'Navigation function:', !!onNavigateToLearning)
                          if (onNavigateToLearning) {
                            // Visual feedback
                            e.target.style.background = 'var(--primary-500)'
                            e.target.style.color = 'white'
                            e.target.innerHTML = '🎓 Opening Learning Center...'
                            
                            // Navigate after a brief delay for feedback
                            setTimeout(() => {
                              console.log('Navigating to learning with topic:', resource.topic)
                              onNavigateToLearning(resource.topic)
                            }, 500)
                          }
                        }}>
                          🎓 {resource.title} → {resource.topic}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div style={{
                  fontSize: '0.7rem',
                  color: 'var(--gray-400)',
                  marginTop: '4px',
                  textAlign: message.role === 'user' ? 'right' : 'left'
                }}>
                  {formatTime(message.timestamp)}
                </div>
              </div>
            </div>
          ))
          )}
          
          {/* Typing Indicator */}
          {isTyping && (
            <div className="chat-message assistant">
              <div className="chat-avatar assistant">🤖</div>
              <div className="chat-content">
                <div className="chat-bubble assistant" style={{ background: 'linear-gradient(135deg, var(--primary-50) 0%, var(--blue-50) 100%)' }}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={{ fontSize: '1.1rem', fontWeight: '600', color: 'var(--primary-700)' }}>
                      🧠 Analyzing your portfolio...
                    </span>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <div className="typing-dot-large" style={{ animationDelay: '0ms' }}></div>
                      <div className="typing-dot-large" style={{ animationDelay: '150ms' }}></div>
                      <div className="typing-dot-large" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-container">
          <input 
            className="chat-input"
            value={input} 
            onChange={e => setInput(e.target.value)} 
            onKeyPress={handleKeyPress}
            placeholder={isLoadingGreeting ? "Loading your advisor..." : "Ask about your portfolio, market trends, or investment advice..."}
            disabled={isTyping || isLoadingGreeting}
          />
          <button 
            className="btn btn-primary"
            onClick={sendMessage}
            disabled={!input.trim() || isTyping || isLoadingGreeting}
            style={{ 
              minWidth: '80px',
              opacity: (!input.trim() || isTyping || isLoadingGreeting) ? 0.5 : 1 
            }}
          >
            {isLoadingGreeting ? '⏳' : isTyping ? '💭' : '🚀'} Send
          </button>
        </div>
      </div>

      <style jsx>{`
        .typing-dot {
          width: 4px;
          height: 4px;
          background: var(--gray-400);
          border-radius: 50%;
          animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-dot-large {
          width: 8px;
          height: 8px;
          background: var(--primary-500);
          border-radius: 50%;
          animation: typing-large 1.4s infinite ease-in-out;
          box-shadow: 0 0 4px rgba(59, 130, 246, 0.5);
        }
        
        @keyframes typing {
          0%, 80%, 100% {
            transform: scale(0);
            opacity: 0.5;
          }
          40% {
            transform: scale(1);
            opacity: 1;
          }
        }
        
        @keyframes typing-large {
          0%, 80%, 100% {
            transform: scale(0.5);
            opacity: 0.3;
          }
          40% {
            transform: scale(1.2);
            opacity: 1;
          }
        }
        
        .chat-bubble.error {
          background: var(--red-100) !important;
          color: var(--red-700) !important;
          border-color: var(--red-200) !important;
        }
      `}</style>
    </div>
  )
}
