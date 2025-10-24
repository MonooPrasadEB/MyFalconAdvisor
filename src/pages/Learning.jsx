import { useState, useEffect } from 'react'
import axios from 'axios'

export default function Learning({ API_BASE, user }) {
  const [selectedTopic, setSelectedTopic] = useState(null)
  const [completedLessons, setCompletedLessons] = useState([])
  const [userProgress, setUserProgress] = useState({})

  const learningTopics = [
    {
      id: 'stocks',
      title: '📈 Stocks & Equity',
      description: 'Learn about stock ownership, market dynamics, and equity investing',
      color: 'var(--blue-500)',
      icon: '📊',
      lessons: [
        {
          id: 'stock-basics',
          title: 'What Are Stocks?',
          duration: '5 min',
          type: 'interactive',
          content: {
            summary: 'Learn the fundamentals of stock ownership and how companies raise capital.',
            keyPoints: [
              'Stocks represent ownership in a company',
              'Share prices fluctuate based on supply and demand',
              'Dividends provide regular income to shareholders',
              'Capital gains occur when stock prices increase'
            ],
            externalResources: [
              {
                title: 'SEC: What Are Stocks?',
                url: 'https://www.sec.gov/investor/pubs/tenthingsbeforeinvesting.htm',
                type: 'official'
              },
              {
                title: 'Investopedia: Stock Basics',
                url: 'https://www.investopedia.com/terms/s/stock.asp',
                type: 'educational'
              }
            ]
          }
        },
        {
          id: 'stock-analysis',
          title: 'How to Analyze Stocks',
          duration: '8 min',
          type: 'interactive',
          content: {
            summary: 'Understand fundamental and technical analysis for stock evaluation.',
            keyPoints: [
              'P/E ratio indicates valuation relative to earnings',
              'Market cap shows company size and stability',
              'Revenue growth indicates business expansion',
              'Debt-to-equity ratio shows financial health'
            ],
            externalResources: [
              {
                title: 'Khan Academy: Stock Analysis',
                url: 'https://www.khanacademy.org/economics-finance-domain/core-finance',
                type: 'course'
              }
            ]
          }
        }
      ]
    },
    {
      id: 'bonds',
      title: '🏦 Bonds & Fixed Income',
      description: 'Understand bonds, yields, and how fixed income investments work',
      color: 'var(--green-500)',
      icon: '🏛️',
      lessons: [
        {
          id: 'bond-basics',
          title: 'Understanding Bonds',
          duration: '6 min',
          type: 'interactive',
          content: {
            summary: 'Learn how bonds work as debt instruments and income generators.',
            keyPoints: [
              'Bonds are loans you make to companies or governments',
              'Face value is the amount paid back at maturity',
              'Coupon rate determines periodic interest payments',
              'Bond prices move inversely to interest rates'
            ],
            externalResources: [
              {
                title: 'Treasury Direct: Bond Basics',
                url: 'https://www.treasurydirect.gov/indiv/research/indepth/bonds/res_bond_basics.htm',
                type: 'official'
              }
            ]
          }
        }
      ]
    },
    {
      id: 'cashflow',
      title: '💰 Cash Flow & Budgeting',
      description: 'Master personal cash flow management and budgeting strategies',
      color: 'var(--purple-500)',
      icon: '💸',
      lessons: [
        {
          id: 'cashflow-basics',
          title: 'Understanding Cash Flow',
          duration: '7 min',
          type: 'interactive',
          content: {
            summary: 'Learn to track, analyze, and optimize your personal cash flow.',
            keyPoints: [
              'Cash flow = Money in - Money out',
              'Positive cash flow enables investment and savings',
              'Track all income sources and expenses',
              'Emergency fund should cover 3-6 months of expenses'
            ],
            externalResources: [
              {
                title: 'CFPB: Managing Your Money',
                url: 'https://www.consumerfinance.gov/consumer-tools/money-as-you-grow/',
                type: 'official'
              }
            ]
          }
        }
      ]
    },
    {
      id: 'portfolio',
      title: '📋 Portfolio Management',
      description: 'Learn diversification, asset allocation, and risk management',
      color: 'var(--orange-500)',
      icon: '⚖️',
      lessons: [
        {
          id: 'diversification',
          title: 'The Power of Diversification',
          duration: '10 min',
          type: 'interactive',
          content: {
            summary: 'Understand how diversification reduces risk and improves returns.',
            keyPoints: [
              'Don\'t put all eggs in one basket',
              'Diversify across asset classes, sectors, and geography',
              'Correlation between assets affects diversification benefit',
              'Rebalancing maintains target allocation'
            ],
            externalResources: [
              {
                title: 'Bogleheads: Three-Fund Portfolio',
                url: 'https://www.bogleheads.org/wiki/Three-fund_portfolio',
                type: 'community'
              }
            ]
          }
        }
      ]
    },
    {
      id: 'retirement',
      title: '🏖️ Retirement Planning',
      description: 'Plan for long-term financial independence and retirement',
      color: 'var(--teal-500)',
      icon: '🌅',
      lessons: [
        {
          id: 'retirement-basics',
          title: '401(k) vs IRA vs Roth IRA',
          duration: '9 min',
          type: 'interactive',
          content: {
            summary: 'Compare different retirement account types and tax implications.',
            keyPoints: [
              '401(k) offers employer matching and higher limits',
              'Traditional IRA provides tax deduction today',
              'Roth IRA offers tax-free growth and withdrawals',
              'Start early to benefit from compound interest'
            ],
            externalResources: [
              {
                title: 'IRS: Retirement Topics',
                url: 'https://www.irs.gov/retirement-plans',
                type: 'official'
              }
            ]
          }
        }
      ]
    },
    {
      id: 'risk',
      title: '⚠️ Risk Management',
      description: 'Understand investment risks and how to manage them',
      color: 'var(--red-500)',
      icon: '🛡️',
      lessons: [
        {
          id: 'risk-types',
          title: 'Types of Investment Risk',
          duration: '8 min',
          type: 'interactive',
          content: {
            summary: 'Learn about different types of investment risks and mitigation strategies.',
            keyPoints: [
              'Market risk affects all investments in a market',
              'Company-specific risk can be diversified away',
              'Inflation risk erodes purchasing power over time',
              'Liquidity risk affects ability to sell quickly'
            ],
            externalResources: [
              {
                title: 'FINRA: Investment Risk',
                url: 'https://www.finra.org/investors/learn-to-invest/types-investments/investment-risk',
                type: 'official'
              }
            ]
          }
        }
      ]
    }
  ]

  useEffect(() => {
    // Load user's learning progress
    const savedProgress = localStorage.getItem(`learning_progress_${user?.id}`)
    if (savedProgress) {
      try {
        const progress = JSON.parse(savedProgress)
        setCompletedLessons(progress.completed || [])
        setUserProgress(progress.progress || {})
      } catch (error) {
        console.error('Error loading progress:', error)
      }
    }

    // Check if we should open a specific topic (from chat navigation)
    const topicToOpen = localStorage.getItem('learningTopicToOpen')
    if (topicToOpen) {
      const topic = learningTopics.find(t => t.id === topicToOpen)
      if (topic && topic.lessons.length > 0) {
        setSelectedTopic({ topic, lesson: topic.lessons[0] })
        localStorage.removeItem('learningTopicToOpen') // Clear after use
      }
    }
  }, [user, learningTopics])

  const markLessonComplete = (topicId, lessonId) => {
    const lessonKey = `${topicId}-${lessonId}`
    if (!completedLessons.includes(lessonKey)) {
      const newCompleted = [...completedLessons, lessonKey]
      setCompletedLessons(newCompleted)
      
      // Update progress
      const newProgress = { ...userProgress }
      if (!newProgress[topicId]) newProgress[topicId] = 0
      newProgress[topicId] += 1
      setUserProgress(newProgress)
      
      // Award gamification points - will be handled by database integration
      if (user?.id) {
        // TODO: Update gamification data in database
        console.log('Lesson completed - gamification points will be updated in database')
      }
      
      // Save to localStorage
      localStorage.setItem(`learning_progress_${user?.id}`, JSON.stringify({
        completed: newCompleted,
        progress: newProgress
      }))
      
      // Show reward notification
      setTimeout(() => {
        alert('🎉 Lesson completed! +50 points earned!')
      }, 500)
    }
  }

  const getTopicProgress = (topic) => {
    const completed = userProgress[topic.id] || 0
    const total = topic.lessons.length
    return { completed, total, percentage: Math.round((completed / total) * 100) }
  }

  const totalLessons = learningTopics.reduce((sum, topic) => sum + topic.lessons.length, 0)
  const totalCompleted = completedLessons.length
  const overallProgress = Math.round((totalCompleted / totalLessons) * 100)

  return (
    <div>
      {/* Learning Progress Overview */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h2 className="card-title">🎓 Financial Education Center</h2>
          <p className="card-subtitle">
            Master financial concepts to make informed investment decisions
          </p>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
          <div style={{
            padding: '20px',
            background: 'linear-gradient(135deg, var(--primary-500), var(--primary-600))',
            color: 'white',
            borderRadius: 'var(--radius-lg)'
          }}>
            <div style={{ fontSize: '2rem', fontWeight: '700' }}>{overallProgress}%</div>
            <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>Overall Progress</div>
            <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>
              {totalCompleted} of {totalLessons} lessons completed
            </div>
          </div>
          
          <div style={{
            padding: '20px',
            background: 'linear-gradient(135deg, var(--green-500), var(--green-600))',
            color: 'white',
            borderRadius: 'var(--radius-lg)'
          }}>
            <div style={{ fontSize: '2rem', fontWeight: '700' }}>{learningTopics.length}</div>
            <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>Learning Topics</div>
            <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>
              Stocks, Bonds, Portfolio & More
            </div>
          </div>
          
          <div style={{
            padding: '20px',
            background: 'linear-gradient(135deg, var(--purple-500), var(--purple-600))',
            color: 'white',
            borderRadius: 'var(--radius-lg)'
          }}>
            <div style={{ fontSize: '2rem', fontWeight: '700' }}>🏆</div>
            <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>Learning Rank</div>
            <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>
              {overallProgress >= 80 ? 'Expert' : overallProgress >= 60 ? 'Advanced' : overallProgress >= 30 ? 'Intermediate' : 'Beginner'}
            </div>
          </div>
        </div>
      </div>

      {/* Learning Topics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '24px' }}>
        {learningTopics.map(topic => {
          const progress = getTopicProgress(topic)
          return (
            <div key={topic.id} className="card interactive" style={{ position: 'relative', overflow: 'hidden' }}>
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '4px',
                background: 'var(--gray-200)'
              }}>
                <div style={{
                  height: '100%',
                  width: `${progress.percentage}%`,
                  background: topic.color,
                  transition: 'width 0.3s ease'
                }}></div>
              </div>
              
              <div className="card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '50%',
                    background: `${topic.color}20`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.5rem'
                  }}>
                    {topic.icon}
                  </div>
                  <div style={{ flex: 1 }}>
                    <h3 className="card-title" style={{ margin: 0, fontSize: '1.2rem' }}>
                      {topic.title}
                    </h3>
                    <p className="card-subtitle" style={{ margin: '4px 0 0 0' }}>
                      {topic.description}
                    </p>
                  </div>
                </div>
              </div>
              
              <div style={{ marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--gray-600)' }}>Progress</span>
                  <span style={{ fontSize: '0.85rem', fontWeight: '600', color: topic.color }}>
                    {progress.completed}/{progress.total} lessons
                  </span>
                </div>
                <div style={{
                  width: '100%',
                  height: '8px',
                  background: 'var(--gray-200)',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${progress.percentage}%`,
                    height: '100%',
                    background: topic.color,
                    borderRadius: '4px',
                    transition: 'width 0.3s ease'
                  }}></div>
                </div>
              </div>
              
              <div style={{ display: 'grid', gap: '8px' }}>
                {topic.lessons.map(lesson => {
                  const isCompleted = completedLessons.includes(`${topic.id}-${lesson.id}`)
                  return (
                    <div
                      key={lesson.id}
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        console.log('Lesson clicked:', lesson.title, 'from topic:', topic.title)
                        setSelectedTopic({ topic, lesson })
                      }}
                      style={{
                        padding: '12px 16px',
                        border: '1px solid var(--gray-200)',
                        borderRadius: 'var(--radius-md)',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        background: isCompleted ? `${topic.color}10` : 'white',
                        borderColor: isCompleted ? topic.color : 'var(--gray-200)',
                        userSelect: 'none'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = topic.color
                        e.currentTarget.style.transform = 'translateY(-1px)'
                        e.currentTarget.style.boxShadow = 'var(--shadow-md)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = isCompleted ? topic.color : 'var(--gray-200)'
                        e.currentTarget.style.transform = 'translateY(0)'
                        e.currentTarget.style.boxShadow = 'none'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{
                          width: '24px',
                          height: '24px',
                          borderRadius: '50%',
                          background: isCompleted ? topic.color : 'var(--gray-300)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'white',
                          fontSize: '0.7rem',
                          fontWeight: '600'
                        }}>
                          {isCompleted ? '✓' : ''}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: '500', fontSize: '0.9rem' }}>{lesson.title}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)' }}>
                            {lesson.duration} • {lesson.type}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

      {/* Lesson Modal/Detail View */}
      {selectedTopic && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: 'white',
            borderRadius: 'var(--radius-lg)',
            padding: '32px',
            maxWidth: '800px',
            width: '100%',
            maxHeight: '90vh',
            overflow: 'auto',
            boxShadow: 'var(--shadow-xl)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
              <div>
                <h3 style={{ margin: '0 0 8px 0', fontSize: '1.5rem' }}>
                  {selectedTopic.lesson.title}
                </h3>
                <div style={{ display: 'flex', gap: '16px', fontSize: '0.85rem', color: 'var(--gray-600)' }}>
                  <span>📚 {selectedTopic.topic.title}</span>
                  <span>⏱️ {selectedTopic.lesson.duration}</span>
                  <span>🎯 {selectedTopic.lesson.type}</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedTopic(null)}
                style={{
                  padding: '8px',
                  border: 'none',
                  background: 'var(--gray-100)',
                  borderRadius: '50%',
                  cursor: 'pointer',
                  fontSize: '1.2rem'
                }}
              >
                ✕
              </button>
            </div>
            
            <div style={{ marginBottom: '24px' }}>
              <p style={{ fontSize: '1.1rem', lineHeight: '1.6', color: 'var(--gray-700)' }}>
                {selectedTopic.lesson.content.summary}
              </p>
            </div>
            
            <div style={{ marginBottom: '24px' }}>
              <h4 style={{ margin: '0 0 16px 0', color: selectedTopic.topic.color }}>🎯 Key Learning Points</h4>
              <ul style={{ paddingLeft: '20px', lineHeight: '1.8' }}>
                {selectedTopic.lesson.content.keyPoints.map((point, index) => (
                  <li key={index} style={{ marginBottom: '8px' }}>{point}</li>
                ))}
              </ul>
            </div>
            
            <div style={{ marginBottom: '24px' }}>
              <h4 style={{ margin: '0 0 16px 0', color: selectedTopic.topic.color }}>🌐 External Resources</h4>
              <div style={{ display: 'grid', gap: '12px' }}>
                {selectedTopic.lesson.content.externalResources.map((resource, index) => (
                  <a
                    key={index}
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 16px',
                      border: '1px solid var(--gray-200)',
                      borderRadius: 'var(--radius-md)',
                      textDecoration: 'none',
                      color: 'inherit',
                      transition: 'all 0.2s ease',
                      cursor: 'pointer'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = selectedTopic.topic.color
                      e.currentTarget.style.transform = 'translateY(-1px)'
                      e.currentTarget.style.boxShadow = 'var(--shadow-md)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--gray-200)'
                      e.currentTarget.style.transform = 'translateY(0)'
                      e.currentTarget.style.boxShadow = 'none'
                    }}
                  >
                    <div style={{
                      padding: '8px',
                      borderRadius: '50%',
                      background: `${selectedTopic.topic.color}20`,
                      fontSize: '1.2rem'
                    }}>
                      {resource.type === 'official' ? '🏛️' : 
                       resource.type === 'course' ? '🎓' : 
                       resource.type === 'community' ? '👥' : '📖'}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '500' }}>{resource.title}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--gray-500)', textTransform: 'capitalize' }}>
                        {resource.type} resource
                      </div>
                    </div>
                    <div style={{ fontSize: '1.2rem', color: 'var(--gray-400)' }}>→</div>
                  </a>
                ))}
              </div>
            </div>
            
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setSelectedTopic(null)}
                className="btn btn-secondary"
              >
                Close
              </button>
              <button
                onClick={() => {
                  markLessonComplete(selectedTopic.topic.id, selectedTopic.lesson.id)
                  setSelectedTopic(null)
                }}
                className="btn btn-primary"
                disabled={completedLessons.includes(`${selectedTopic.topic.id}-${selectedTopic.lesson.id}`)}
              >
                {completedLessons.includes(`${selectedTopic.topic.id}-${selectedTopic.lesson.id}`) ? 
                  '✅ Completed' : 
                  '📚 Mark as Complete'
                }
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
