import { useState, useEffect } from 'react'
// Demo data import removed - ready for database integration

export default function Gamification({ user }) {
  const [gamificationData, setGamificationData] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    if (user?.id) {
      const savedData = localStorage.getItem(`gamification_${user.id}`)
      if (savedData) {
        try {
          const data = JSON.parse(savedData)
          setGamificationData(data)
          console.log('Gamification data loaded:', data)
        } catch (error) {
          console.error('Error loading gamification data:', error)
        }
      } else {
        // No gamification data found - will be loaded from database
        setGamificationData(null)
      }
    }
  }, [user])

  if (!gamificationData) {
    return (
      <div className="card">
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🎮</div>
          <h3>Gamification Coming Soon</h3>
          <p style={{ color: 'var(--gray-600)', marginTop: '16px' }}>
            Connect your database to enable gamification features, achievements, and progress tracking.
          </p>
        </div>
      </div>
    )
  }

  const getLevelName = (level) => {
    if (level >= 15) return "Investment Master"
    if (level >= 10) return "Portfolio Pro"
    if (level >= 5) return "Financial Enthusiast"
    return "Wealth Builder"
  }

  const getBadgeColor = (rarity) => {
    switch (rarity) {
      case 'legendary': return 'linear-gradient(135deg, #FFD700, #FFA500)'
      case 'rare': return 'linear-gradient(135deg, #9932CC, #8A2BE2)'
      case 'common': return 'linear-gradient(135deg, #32CD32, #228B22)'
      default: return 'linear-gradient(135deg, var(--gray-400), var(--gray-500))'
    }
  }

  const earnedAchievements = gamificationData.achievements.filter(a => a.earned)
  const availableAchievements = gamificationData.achievements.filter(a => !a.earned)
  const activeChallenges = gamificationData.challenges.filter(c => c.active)

  return (
    <div>
      {/* Gamification Header */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h2 className="card-title">🎮 Your Financial Journey</h2>
          <p className="card-subtitle">Level up your financial skills and earn rewards!</p>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
          {/* Level & XP */}
          <div style={{
            padding: '20px',
            background: 'linear-gradient(135deg, var(--primary-500), var(--primary-600))',
            color: 'white',
            borderRadius: 'var(--radius-lg)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>
              ⭐ {gamificationData.level}
            </div>
            <div style={{ fontSize: '1rem', marginBottom: '12px', opacity: 0.9 }}>
              {getLevelName(gamificationData.level)}
            </div>
            <div style={{
              width: '100%',
              height: '8px',
              background: 'rgba(255,255,255,0.3)',
              borderRadius: '4px',
              overflow: 'hidden',
              marginBottom: '8px'
            }}>
              <div style={{
                width: `${gamificationData.levelProgress}%`,
                height: '100%',
                background: 'white',
                borderRadius: '4px',
                transition: 'width 0.3s ease'
              }}></div>
            </div>
            <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>
              {gamificationData.levelProgress}% to level {gamificationData.level + 1}
            </div>
          </div>

          {/* Total Points */}
          <div style={{
            padding: '20px',
            background: 'linear-gradient(135deg, var(--yellow-500), #FFB347)',
            color: 'white',
            borderRadius: 'var(--radius-lg)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>
              💎 {gamificationData.totalPoints.toLocaleString()}
            </div>
            <div style={{ fontSize: '1rem', opacity: 0.9 }}>
              Total Points
            </div>
            <div style={{ fontSize: '0.85rem', marginTop: '8px', opacity: 0.8 }}>
              Rank: Top 15% of users
            </div>
          </div>

          {/* Current Streak */}
          <div style={{
            padding: '20px',
            background: 'linear-gradient(135deg, var(--orange-500), #FF6347)',
            color: 'white',
            borderRadius: 'var(--radius-lg)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>
              🔥 {gamificationData.streak.current}
            </div>
            <div style={{ fontSize: '1rem', marginBottom: '4px', opacity: 0.9 }}>
              Day Streak
            </div>
            <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>
              Best: {gamificationData.streak.longest} days
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{ 
        display: 'flex', 
        gap: '8px', 
        marginBottom: '24px',
        borderBottom: '1px solid var(--gray-200)',
        paddingBottom: '16px'
      }}>
        {['overview', 'achievements', 'challenges', 'badges'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '12px 20px',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              background: activeTab === tab ? 'var(--primary-500)' : 'var(--gray-100)',
              color: activeTab === tab ? 'white' : 'var(--gray-700)',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              textTransform: 'capitalize'
            }}
          >
            {tab === 'overview' && '📊'} 
            {tab === 'achievements' && '🏆'} 
            {tab === 'challenges' && '🎯'} 
            {tab === 'badges' && '🎖️'} 
            {' '}{tab}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gap: '24px' }}>
          {/* Weekly Goals */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">📅 Weekly Goals</h3>
              <p className="card-subtitle">Track your progress this week</p>
            </div>
            
            <div style={{ display: 'grid', gap: '16px' }}>
              {Object.entries(gamificationData.weeklyGoals).map(([key, goal]) => (
                <div key={key} style={{
                  padding: '16px',
                  border: '1px solid var(--gray-200)',
                  borderRadius: 'var(--radius-md)',
                  background: goal.completed ? 'var(--green-50)' : 'white'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ fontWeight: '600', textTransform: 'capitalize' }}>
                      {key === 'portfolio_review' ? 'Portfolio Review' : key.replace('_', ' ')}
                    </div>
                    <div style={{ color: goal.completed ? 'var(--green-600)' : 'var(--gray-600)' }}>
                      {goal.completed ? '✅ Complete' : `${goal.current}/${goal.target}`}
                    </div>
                  </div>
                  <div style={{
                    width: '100%',
                    height: '8px',
                    background: 'var(--gray-200)',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${Math.min((goal.current / goal.target) * 100, 100)}%`,
                      height: '100%',
                      background: goal.completed ? 'var(--green-500)' : 'var(--primary-500)',
                      borderRadius: '4px',
                      transition: 'width 0.3s ease'
                    }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Achievements */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">🏆 Recent Achievements</h3>
              <p className="card-subtitle">Your latest accomplishments</p>
            </div>
            
            <div style={{ display: 'grid', gap: '12px' }}>
              {earnedAchievements.slice(-3).reverse().map(achievement => (
                <div key={achievement.id} style={{
                  padding: '16px',
                  border: '1px solid var(--gray-200)',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--green-50)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px'
                }}>
                  <div style={{
                    fontSize: '2rem',
                    padding: '12px',
                    borderRadius: '50%',
                    background: 'var(--green-100)'
                  }}>
                    {achievement.icon}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                      {achievement.name}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--gray-600)', marginBottom: '4px' }}>
                      {achievement.description}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--green-600)' }}>
                      +{achievement.points} points • Earned {achievement.earnedDate}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Achievements Tab */}
      {activeTab === 'achievements' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🏆 Achievements</h3>
            <p className="card-subtitle">{earnedAchievements.length} of {gamificationData.achievements.length} unlocked</p>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
            {gamificationData.achievements.map(achievement => (
              <div key={achievement.id} style={{
                padding: '20px',
                border: '1px solid var(--gray-200)',
                borderRadius: 'var(--radius-lg)',
                background: achievement.earned ? 'var(--green-50)' : 'var(--gray-50)',
                opacity: achievement.earned ? 1 : 0.7,
                transition: 'all 0.2s ease'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '12px' }}>
                  <div style={{
                    fontSize: '3rem',
                    padding: '16px',
                    borderRadius: '50%',
                    background: achievement.earned ? 'var(--green-100)' : 'var(--gray-200)'
                  }}>
                    {achievement.icon}
                  </div>
                  <div>
                    <div style={{ fontWeight: '700', fontSize: '1.1rem', marginBottom: '4px' }}>
                      {achievement.name}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--gray-600)' }}>
                      {achievement.description}
                    </div>
                  </div>
                </div>
                
                {achievement.earned ? (
                  <div style={{ 
                    padding: '8px 12px',
                    background: 'var(--green-100)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--green-600)',
                    fontSize: '0.85rem',
                    fontWeight: '500'
                  }}>
                    ✅ Unlocked • +{achievement.points} points
                  </div>
                ) : achievement.progress ? (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.85rem', color: 'var(--gray-600)' }}>Progress</span>
                      <span style={{ fontSize: '0.85rem', fontWeight: '600' }}>{achievement.progress}%</span>
                    </div>
                    <div style={{
                      width: '100%',
                      height: '8px',
                      background: 'var(--gray-200)',
                      borderRadius: '4px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${achievement.progress}%`,
                        height: '100%',
                        background: 'var(--primary-500)',
                        borderRadius: '4px',
                        transition: 'width 0.3s ease'
                      }}></div>
                    </div>
                  </div>
                ) : (
                  <div style={{ 
                    padding: '8px 12px',
                    background: 'var(--gray-100)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--gray-600)',
                    fontSize: '0.85rem'
                  }}>
                    🔒 Locked • {achievement.points} points
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Challenges Tab */}
      {activeTab === 'challenges' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🎯 Active Challenges</h3>
            <p className="card-subtitle">Complete challenges to earn bonus points</p>
          </div>
          
          <div style={{ display: 'grid', gap: '16px' }}>
            {activeChallenges.map(challenge => (
              <div key={challenge.id} style={{
                padding: '20px',
                border: '1px solid var(--gray-200)',
                borderRadius: 'var(--radius-lg)',
                background: 'white'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div>
                    <div style={{ fontWeight: '700', fontSize: '1.1rem', marginBottom: '4px' }}>
                      {challenge.name}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--gray-600)', marginBottom: '8px' }}>
                      {challenge.description}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--orange-600)' }}>
                      Deadline: {challenge.deadline}
                    </div>
                  </div>
                  <div style={{
                    padding: '8px 12px',
                    background: 'var(--primary-100)',
                    borderRadius: 'var(--radius-sm)',
                    color: 'var(--primary-700)',
                    fontSize: '0.85rem',
                    fontWeight: '600'
                  }}>
                    {challenge.points} points
                  </div>
                </div>
                
                <div style={{ marginBottom: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontSize: '0.9rem', color: 'var(--gray-600)' }}>Progress</span>
                    <span style={{ fontSize: '0.9rem', fontWeight: '600' }}>
                      {challenge.current}/{challenge.target}
                    </span>
                  </div>
                  <div style={{
                    width: '100%',
                    height: '10px',
                    background: 'var(--gray-200)',
                    borderRadius: '5px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${Math.min((challenge.current / challenge.target) * 100, 100)}%`,
                      height: '100%',
                      background: challenge.current >= challenge.target ? 'var(--green-500)' : 'var(--primary-500)',
                      borderRadius: '5px',
                      transition: 'width 0.3s ease'
                    }}></div>
                  </div>
                </div>

                {challenge.current >= challenge.target && (
                  <div style={{
                    padding: '12px',
                    background: 'var(--green-50)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--green-200)',
                    textAlign: 'center',
                    color: 'var(--green-600)',
                    fontWeight: '600'
                  }}>
                    🎉 Challenge Complete! Claim your reward
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Badges Tab */}
      {activeTab === 'badges' && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">🎖️ Badge Collection</h3>
            <p className="card-subtitle">Special badges earned through achievements</p>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px' }}>
            {gamificationData.badges.map(badge => (
              <div key={badge.id} style={{
                padding: '24px',
                borderRadius: 'var(--radius-lg)',
                background: getBadgeColor(badge.rarity),
                color: 'white',
                textAlign: 'center',
                position: 'relative',
                overflow: 'hidden'
              }}>
                <div style={{
                  position: 'absolute',
                  top: '12px',
                  right: '12px',
                  padding: '4px 8px',
                  background: 'rgba(255,255,255,0.2)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.7rem',
                  fontWeight: '600',
                  textTransform: 'uppercase'
                }}>
                  {badge.rarity}
                </div>
                
                <div style={{ fontSize: '4rem', marginBottom: '16px' }}>
                  {badge.icon}
                </div>
                <div style={{ fontWeight: '700', fontSize: '1.2rem', marginBottom: '8px' }}>
                  {badge.name}
                </div>
                <div style={{ fontSize: '0.9rem', opacity: 0.9 }}>
                  {badge.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
