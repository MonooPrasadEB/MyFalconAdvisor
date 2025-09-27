// Demo data initialization for showcase
export const initializeDemoData = (userId) => {
  if (userId === "1") { // Demo user Alex Johnson
    // Initialize demo learning progress
    const demoLearningProgress = {
      completed: [
        "stocks-stock-basics",
        "stocks-stock-analysis", 
        "cashflow-cashflow-basics",
        "portfolio-diversification",
        "bonds-bond-basics"
      ],
      progress: {
        stocks: 2,     // Completed both lessons
        cashflow: 1,   // Completed 1 lesson
        portfolio: 1,  // Completed 1 lesson  
        bonds: 1,      // Completed 1 lesson
        retirement: 0, // Not started
        risk: 0        // Not started
      }
    }
    
    localStorage.setItem(`learning_progress_${userId}`, JSON.stringify(demoLearningProgress))
    
    // Initialize demo onboarding data
    const demoProfile = {
      income: 85000,
      expenses: 55000,
      goal: 'retirement',
      horizon: 25
    }
    
    localStorage.setItem(`profile_${userId}`, JSON.stringify(demoProfile))
    
    // Initialize gamification data
    const gamificationData = {
      totalPoints: 2450,
      level: 8,
      levelProgress: 67, // % to next level
      streak: {
        current: 12,
        longest: 18,
        type: "daily_login"
      },
      achievements: [
        {
          id: "first_investment",
          name: "First Investment",
          description: "Made your first investment",
          icon: "🎯",
          points: 100,
          earned: true,
          earnedDate: "2024-01-15"
        },
        {
          id: "portfolio_1k",
          name: "Portfolio Pioneer",
          description: "Reached $1,000 portfolio value",
          icon: "💰",
          points: 200,
          earned: true,
          earnedDate: "2024-02-01"
        },
        {
          id: "learning_streak_7",
          name: "Knowledge Seeker",
          description: "Completed lessons for 7 days straight",
          icon: "🎓",
          points: 150,
          earned: true,
          earnedDate: "2024-02-15"
        },
        {
          id: "diversification_master",
          name: "Diversification Master",
          description: "Portfolio spread across 5+ asset classes",
          icon: "🌟",
          points: 300,
          earned: true,
          earnedDate: "2024-03-01"
        },
        {
          id: "tax_optimizer",
          name: "Tax Optimizer",
          description: "Executed first tax-loss harvest",
          icon: "💎",
          points: 250,
          earned: false,
          progress: 80 // 80% towards earning
        },
        {
          id: "portfolio_10k",
          name: "Growing Wealth",
          description: "Reached $10,000 portfolio value",
          icon: "🚀",
          points: 500,
          earned: true,
          earnedDate: "2024-03-15"
        },
        {
          id: "learning_graduate",
          name: "Financial Graduate",
          description: "Completed all learning modules",
          icon: "🎓",
          points: 750,
          earned: false,
          progress: 67 // 67% complete
        }
      ],
      challenges: [
        {
          id: "monthly_investment",
          name: "Consistent Investor",
          description: "Invest every month for 6 months",
          type: "monthly",
          target: 6,
          current: 4,
          points: 400,
          deadline: "2024-12-31",
          active: true
        },
        {
          id: "learning_week",
          name: "Learning Sprint",
          description: "Complete 3 lessons this week",
          type: "weekly",
          target: 3,
          current: 2,
          points: 200,
          deadline: "2024-09-30",
          active: true
        },
        {
          id: "portfolio_balance",
          name: "Portfolio Perfectionist",
          description: "Maintain target allocation for 30 days",
          type: "special",
          target: 30,
          current: 12,
          points: 300,
          deadline: "2024-10-25",
          active: true
        }
      ],
      badges: [
        {
          id: "early_adopter",
          name: "Early Adopter",
          description: "One of the first 100 users",
          rarity: "legendary",
          icon: "🏆"
        },
        {
          id: "learning_enthusiast",
          name: "Learning Enthusiast",
          description: "Completed 10+ lessons",
          rarity: "rare",
          icon: "📚"
        },
        {
          id: "portfolio_builder",
          name: "Portfolio Builder",
          description: "Created well-diversified portfolio",
          rarity: "common",
          icon: "🏗️"
        }
      ],
      weeklyGoals: {
        investment: { target: 500, current: 300, completed: false },
        learning: { target: 2, current: 2, completed: true },
        portfolio_review: { target: 1, current: 1, completed: true }
      }
    }
    
    localStorage.setItem(`gamification_${userId}`, JSON.stringify(gamificationData))
    
    console.log('Demo data initialized for Alex Johnson')
  }
}

export const getDemoUserInfo = (userId) => {
  if (userId === "1") {
    return {
      name: "Alex Johnson",
      experience: "Intermediate investor with 3 years experience",
      goals: "Building retirement portfolio over 25-year horizon",
      riskProfile: "Moderate risk tolerance",
      learningProgress: "67% complete - Focus on retirement and risk management",
      portfolioValue: "$26,792.15",
      todayReturn: "+$36.87 (+0.14%)"
    }
  }
  return null
}

export const getDemoInsights = () => {
  return [
    {
      type: "tax",
      title: "Tax-Loss Harvesting Opportunity Detected",
      description: "VXUS position shows $157 in potential tax savings. Consider harvesting before year-end to optimize your tax situation.",
      priority: "high", 
      icon: "💰",
      action: "tax_harvest"
    },
    {
      type: "learning", 
      title: "Complete Retirement Planning Module",
      description: "You're 67% through your financial education journey. The retirement planning module will help optimize your 25-year strategy.",
      priority: "high",
      icon: "🎓",
      action: "learning"
    },
    {
      type: "performance",
      title: "Strong YTD Performance", 
      description: "Your portfolio is up 12.4% this year, outperforming the S&P 500 by 1.2%. Great job maintaining discipline!",
      priority: "info",
      icon: "📈"
    },
    {
      type: "recommendation",
      title: "Portfolio Rebalancing Opportunity",
      description: "Consider increasing bond allocation by 5% to better align with your moderate risk tolerance and 25-year time horizon.",
      priority: "medium",
      icon: "⚖️"
    }
  ]
}
