import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

export default function ChatUI({ API_BASE, user, onNavigateToLearning }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant', 
      content: `👋 Hello Alex! I'm your personal AI financial advisor, and I'm excited to work with you on your wealth-building journey.

I've reviewed your portfolio ($26,792) and I'm impressed with your disciplined approach - your 35% savings rate puts you in the top 10% of investors your age! Your diversified mix of SPY, QQQ, AGG, VTI, and VXUS shows sophisticated thinking.

**I can help you with:**
• Portfolio optimization and rebalancing strategies
• Market analysis and economic outlook
• Retirement planning (you're on track for $2M+ by age 53!)
• Tax-efficient investing strategies
• Risk management and asset allocation

**Try asking me specific questions like:**
• "How's my portfolio performing compared to the market?"
• "Should I increase my international allocation?"
• "What's your outlook on bonds with current interest rates?"
• "How can I optimize my retirement savings strategy?"

I'll provide detailed, personalized advice based on your goals, risk tolerance, and current market conditions. If you'd like to learn more about any financial concepts, just ask me to explain them!

What would you like to discuss about your financial strategy?`,
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isInitialLoad, setIsInitialLoad] = useState(true)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

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
      const res = await axios.post(`${API_BASE}/chat`, { query: userMsg.content })
      const bot = res.data
      
      setTimeout(() => {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: bot.advisor_reply,
          timestamp: new Date(),
          compliance: bot.compliance_checked,
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
          {messages.map((message, i) => (
            <div key={i} className={`chat-message ${message.role}`}>
              <div className={`chat-avatar ${message.role}`}>
                {message.role === 'user' ? '👤' : '🤖'}
              </div>
              <div className="chat-content">
                <div className={`chat-bubble ${message.role} ${message.isError ? 'error' : ''}`}>
                  {message.content}
                  
                  {/* Show compliance status for advisor messages */}
                  {message.role === 'assistant' && message.compliance && (
                    <div style={{
                      marginTop: '8px',
                      padding: '8px 12px',
                      background: message.compliance.passed ? 'var(--green-100)' : 'var(--red-100)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.8rem',
                      color: message.compliance.passed ? 'var(--green-500)' : 'var(--red-500)'
                    }}>
                      {message.compliance.passed ? '✅' : '⚠️'} Compliance: {message.compliance.notes}
                    </div>
                  )}
                  
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
          ))}
          
          {/* Typing Indicator */}
          {isTyping && (
            <div className="chat-message assistant">
              <div className="chat-avatar assistant">🤖</div>
              <div className="chat-content">
                <div className="chat-bubble assistant">
                  <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                    <span>Thinking</span>
                    <div style={{ display: 'flex', gap: '2px' }}>
                      <div className="typing-dot" style={{ animationDelay: '0ms' }}></div>
                      <div className="typing-dot" style={{ animationDelay: '150ms' }}></div>
                      <div className="typing-dot" style={{ animationDelay: '300ms' }}></div>
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
            placeholder="Ask about your portfolio, market trends, or investment advice..."
            disabled={isTyping}
          />
          <button 
            className="btn btn-primary"
            onClick={sendMessage}
            disabled={!input.trim() || isTyping}
            style={{ 
              minWidth: '80px',
              opacity: (!input.trim() || isTyping) ? 0.5 : 1 
            }}
          >
            {isTyping ? '💭' : '🚀'} Send
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
        
        .chat-bubble.error {
          background: var(--red-100) !important;
          color: var(--red-700) !important;
          border-color: var(--red-200) !important;
        }
      `}</style>
    </div>
  )
}
