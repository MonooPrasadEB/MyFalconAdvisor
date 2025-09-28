# MyFalconAdvisor - Advanced AI Investment Platform

**Project Updates**: For the latest team updates and project status, see our [Project Document](https://docs.google.com/document/d/1H-Onfe3Oi-8sa-IJBGKt1kV9QNT-M3fU6o2CYknTxbs/edit?tab=t.cwgg688j0fv4).

MyFalconAdvisor is a sophisticated multi-agent AI investment platform that combines cutting-edge artificial intelligence with quantitative finance to deliver personalized investment advice at scale. Built with Python, LangGraph, and real financial data integration.

## 🎯 Project Overview

MyFalconAdvisor revolutionizes traditional robo-advisors by introducing **conversation-driven financial guidance**. Unlike static dashboards that quietly adjust portfolios in the background, our platform engages users in natural dialogue to deliver personalized insights, compliance-checked recommendations, and transparent execution support.

### Problem Statement
Traditional robo-advisors lack interactivity and dynamic personalization, leaving users detached from their financial journey. Early-career investors and underserved individuals need guidance that is contextual, transparent, and interactive—not just automated rebalancing.

### Solution Approach
This system implements a **3-agent architecture** powered by LangGraph orchestration, replacing static recommendations with dynamic, conversational financial guidance that democratizes access to high-quality investment advice.

### Core Agents

1. **🧠 Multi-Task Agent**: Portfolio analysis, risk evaluation, and customer engagement
2. **⚡ Execution Agent**: Trade execution with regulatory compliance and user approval workflows
3. **✅ Compliance Reviewer**: SEC/FINRA/IRS policy validation and client communication optimization

## 🚀 Key Features

- **Real Financial Data**: Integration with yfinance, Alpha Vantage, and FRED for live market data
- **Quantitative Analysis**: Modern portfolio theory, VaR calculations, and stress testing
- **Regulatory Compliance**: Automated SEC, FINRA, and IRS compliance checking
- **Risk Assessment**: Interactive risk profiling with scenario analysis
- **Multi-Agent Coordination**: LangGraph-powered agent orchestration
- **Plain English Communication**: Complex financial concepts explained clearly

## 🛠 Technology Stack

- **Python 3.9+**: Core application language
- **LangChain/LangGraph**: Multi-agent framework and LLM orchestration
- **yfinance**: Real-time market data
- **pandas/numpy**: Financial data analysis
- **scipy**: Portfolio optimization
- **Rich**: Beautiful CLI interface
- **OpenAI GPT-4**: Conversational AI capabilities

## ⚡ Quick Start

> **🌐 Note**: The CLI is a development tool for testing the AI agents. The **primary interface will be a web application** providing a seamless user experience with authentication, portfolio management, and conversational AI guidance.

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd myfalconadvisor

# Install dependencies
pip install -e .

# Or install with optional advanced features
pip install -e ".[dev,jupyter,advanced-finance]"
```

### 2. Configuration

Create a `.env` file with your API keys and database credentials:

```bash
# Required - AI and Market Data
OPENAI_API_KEY=your_openai_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FRED_API_KEY=your_fred_key

# Required - Database Connection
DB_USER=your_database_user
DB_PASSWORD=your_database_password

# Optional - Trading Integration (Paper Trading)
ALPACA_API_KEY=your_alpaca_paper_key
ALPACA_SECRET_KEY=your_alpaca_paper_secret
```

### 3. Database-Driven CLI (Development Tool)

The CLI automatically loads user data from the database - no file uploads needed:

```bash
# Quick demo with your real portfolio data
myfalcon demo "How is my portfolio performing?"

# Interactive AI conversation mode
myfalcon interactive

# Analyze your portfolio from database
myfalcon portfolio

# Risk assessment using your profile
myfalcon risk

# Get rebalancing recommendations
myfalcon rebalance

# Simulate trades
myfalcon simulate --symbol AAPL --action buy --quantity 10

# View your transaction history
myfalcon transactions --limit 20

# Validate system configuration
myfalcon validate
```

### 🌐 Web Application (Primary Interface)

The web application will provide:
- **User Authentication**: Secure login and profile management
- **Portfolio Dashboard**: Real-time portfolio visualization
- **Conversational AI**: Natural language financial guidance
- **Trade Execution**: Seamless order placement and tracking
- **Compliance Integration**: Automated regulatory validation
- **Mobile Responsive**: Access from any device

## 📊 Usage Examples

### Database-Driven Portfolio Analysis
```python
from myfalconadvisor.core.supervisor import investment_advisor_supervisor
from myfalconadvisor.tools.database_service import DatabaseService

# Initialize database service
db_service = DatabaseService()

# Load real user data from database
user_id = "usr_348784c4-6f83-4857-b7dc-f5132a38dfee"  # Authenticated user
portfolios = db_service.get_user_portfolios(user_id)
portfolio_data = portfolios[0] if portfolios else None

# Load user profile from database
with db_service.get_session() as session:
    result = session.execute(text("""
        SELECT age, risk_profile, annual_income_usd, objective
        FROM users WHERE user_id = :user_id
    """), {"user_id": user_id})
    user_row = result.fetchone()
    
    client_profile = {
        "age": calculate_age_from_dob(user_row.dob),
        "risk_tolerance": user_row.risk_profile,
        "annual_income": float(user_row.annual_income_usd),
        "primary_goal": user_row.objective
    }

# Get AI-powered analysis using real data
result = investment_advisor_supervisor.process_client_request(
    request="Analyze my portfolio and suggest improvements",
    client_profile=client_profile,
    portfolio_data=portfolio_data,
    user_id=user_id
)

print(result["response"])
```

### Web Application Integration
```javascript
// Frontend API call to get portfolio analysis
const response = await fetch('/api/portfolio/analyze', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        query: "How is my portfolio performing this month?",
        include_recommendations: true
    })
});

const analysis = await response.json();
// Display AI response in chat interface
displayAIResponse(analysis.response);
```

## 🏗 System Architecture

### Multi-Agent Workflow (LangGraph Orchestration)
```
                    📱 User Interface (Web/Mobile)
                              ↓
                    🧠 LangGraph Supervisor Agent
                              ↓
          ┌─────────────────┼─────────────────┐
          ↓                 ↓                 ↓
    🎯 Advisor Agent   ✅ Compliance Agent  ⚡ Execution Agent
    ┌─────────────┐    ┌─────────────┐     ┌─────────────┐
    │• Portfolio  │    │• SEC/FINRA  │     │• Trade      │
    │  Analysis   │    │  Validation │     │  Execution  │
    │• Risk       │    │• Policy     │     │• User       │
    │  Assessment │    │  Feeds      │     │  Consent    │
    │• Scenario   │    │• Content    │     │• Alpaca     │
    │  Simulation │    │  Rewriting  │     │  Integration│
    │• Market     │    │• Compliance │     │• Audit      │
    │  Analysis   │    │  Scoring    │     │  Trail      │
    └─────────────┘    └─────────────┘     └─────────────┘
          ↓                 ↓                 ↓
          └─────────────────┼─────────────────┘
                            ↓
                  📊 Integrated Response
                            ↓
              🔄 Full Advisory Loop Complete
    (Advice → Compliance → User Approval → Execution)
```

### Data Flow Architecture
```
📊 Market Data APIs          🏛️ Regulatory Data         👤 User Data
┌─────────────────┐         ┌─────────────────┐        ┌─────────────────┐
│• Yahoo Finance  │         │• SEC Feeds      │        │• Profile Data   │
│• Alpha Vantage  │    →    │• FINRA Rules    │   →    │• Portfolio      │
│• FRED           │         │• IRS Policy     │        │• Goals & Risk   │
│• Bloomberg      │         │• Real-time      │        │• Preferences    │
└─────────────────┘         │  Updates        │        └─────────────────┘
                            └─────────────────┘
                                     ↓
                    🧠 MyFalconAdvisor Multi-Agent System
                                     ↓
                    📱 User Interface & Experience Layer
                                     ↓
                    📈 Personalized Investment Guidance
```

### Technology Stack Architecture
```
🌐 Frontend Layer
├── React/Vue.js (Web Interface)
├── Mobile-Responsive Design
└── Real-time Chat Interface

🔧 Backend Services
├── Python FastAPI/Flask
├── LangGraph Multi-Agent Orchestration
├── LangChain AI Framework
└── OpenAI GPT-4 Integration

💾 Data Layer
├── Real-time Market Data APIs
├── Regulatory Policy Feeds
├── User Profile Management
└── Portfolio & Transaction Storage

🔒 Security & Compliance
├── Immutable Audit Trails
├── Regulatory Validation Engine
├── Secure API Authentication
└── Data Encryption & Privacy

☁️ Infrastructure
├── Cloud Deployment (AWS/GCP)
├── API Gateway & Load Balancing
├── Monitoring & Logging
└── Automated Testing & CI/CD
```

### Project Structure
```
myfalconadvisor/
├── agents/                     # Multi-Agent System Components
│   ├── multi_task_agent.py    # Advisor Agent: Portfolio analysis & conversational AI
│   ├── execution_agent.py     # Execution Service: Database-driven trade validation
│   └── compliance_reviewer.py # Compliance Agent: Regulatory validation
├── tools/                      # Financial Analysis & Data Tools
│   ├── database_service.py    # PostgreSQL database integration
│   ├── market_data.py         # Real-time market data (Yahoo Finance, Alpha Vantage)
│   ├── portfolio_analyzer.py  # Portfolio optimization & analytics
│   ├── risk_assessment.py     # Risk profiling & scenario simulation
│   ├── compliance_checker.py  # SEC/FINRA/IRS compliance validation
│   ├── chat_logger.py         # AI conversation logging
│   └── trade_simulator.py     # Trade simulation & backtesting
├── core/                       # System Architecture
│   ├── config.py              # Configuration & API key management
│   └── supervisor.py          # LangGraph multi-agent orchestration
├── DBAdmin/                    # Database Administration
│   ├── database_config.py     # Database connection configuration
│   ├── all_ddls.sql          # Complete database schema
│   └── setup_database.sh     # Database initialization script
├── tests/                      # Comprehensive Test Suite
│   ├── run_all_tests.py      # Complete system testing
│   ├── test_ai_agents.py     # AI agent functionality tests
│   └── test_complete_logging_workflow.py  # Database logging tests
├── cli.py                      # Database-driven CLI (development tool)
└── pyproject.toml             # Package configuration & dependencies
```

## 🏛️ System Architecture & Components

### Multi-Agent Framework (LangGraph Orchestration)

MyFalconAdvisor implements a sophisticated **3-agent architecture** that provides end-to-end financial advisory services:

#### 1. 🧠 **Advisor Agent** (Conversational AI Engine)
**Team Lead:** Akshay Prabu / Monoo Prasad

**Core Responsibilities:**
- **Portfolio Analysis**: Real-time assessment of portfolio health and performance
- **Conversational AI**: Natural language interaction for personalized advice
- **Scenario Simulation**: "What-if" modeling (job loss, pay increase, market downturns)
- **Market Intelligence**: Integration with Yahoo Finance, Alpha Vantage, FRED APIs
- **User Profiling**: Income, expenses, goals, and risk tolerance analysis

**Technical Implementation:**
- LangGraph + LangChain dialogue management
- Real-time market data integration
- Portfolio optimization algorithms
- Scenario-based stress testing
- Natural language generation for financial advice

#### 2. ✅ **Compliance Agent** (Regulatory Validation)
**Team Lead:** Nuzhat

**Core Responsibilities:**
- **Regulatory Validation**: SEC, FINRA, IRS policy compliance checking
- **Real-time Policy Feeds**: Live regulatory updates and rule enforcement
- **Content Rewriting**: Transform non-compliant recommendations
- **Audit Trail**: Compliance scoring and violation tracking
- **Risk Mitigation**: Automated disclosure generation

**Technical Implementation:**
- Rules engine for regulatory compliance
- Real-time policy feed integration
- Compliance scoring algorithms
- Automated content validation and rewriting
- Edge case simulation and testing

#### 3. ⚡ **Execution Agent** (Trade Execution & Paper Trail)
**Team Lead:** Monoo Prasad

**Core Responsibilities:**
- **User Consent Management**: Explicit approval workflows
- **Trade Execution**: Alpaca API integration for paper trading
- **Immutable Logging**: Complete audit trail and transaction history
- **Partial Trade Support**: Advanced order management
- **Portfolio Updates**: Real-time position tracking

**Technical Implementation:**
- Secure transaction logging and error handling
- Alpaca API integration for realistic trading
- User confirmation flows and approval workflows
- Immutable paper trail system
- Portfolio synchronization and updates

#### 4. 🌐 **Web & UX Platform** (Frontend & Data Integration)
**Team Lead:** Vibha Gupta

**Core Responsibilities:**
- **Responsive Web Interface**: Desktop and mobile-optimized design
- **Natural Language Chat**: Conversational UI for user interactions
- **Data Onboarding**: Income, expenses, account linking workflows
- **Analytics Dashboard**: Portfolio visualization and simulation results
- **User Journey Management**: End-to-end experience optimization

**Technical Implementation:**
- ReactJS/VueJS frontend development
- Backend API endpoints and webhook integration
- Secure user authentication and data handling
- Real-time data visualization and charts
- Mobile-responsive design patterns

### Optional Enhancement Track
#### 📊 **Scenario Simulation & Analytics** (Advanced Features)
**Team Leads:** Akshay / Nuzhat (Quantitative Analysis)

**Advanced Capabilities:**
- **Stress Testing**: Portfolio resilience analysis
- **Demographic Benchmarking**: Peer comparison analytics
- **Tax-Loss Harvesting**: Automated tax optimization
- **Gamification**: User engagement and financial literacy
- **ESG Integration**: Sustainable investing options

## 🎯 Research Objectives

MyFalconAdvisor addresses key research challenges in AI-driven financial advisory services:

### Primary Objectives
1. **Conversational AI Integration**: Develop contextual portfolio analysis through natural language interaction
2. **Real-time Compliance Validation**: Implement automated SEC, FINRA, and IRS policy enforcement
3. **Transparent Execution**: Build immutable audit trails with explicit user consent workflows
4. **Scenario-based Planning**: Enable "what-if" simulations for enhanced financial literacy

### Success Metrics
- **User Engagement**: Increased interaction time vs. traditional robo-advisors
- **Compliance Accuracy**: >95% regulatory validation success rate
- **Portfolio Performance**: Risk-adjusted returns aligned with user goals
- **Trust & Transparency**: Complete audit trail accessibility

## 📊 Data Sources & Integration

### Real-Time Market Data
- **Yahoo Finance**: Live stock prices, historical data, and market indicators
- **Alpha Vantage**: Professional-grade financial data and technical indicators
- **FRED (Federal Reserve)**: Economic data, interest rates, and macroeconomic indicators
- **Bloomberg API**: Advanced market data (enterprise tier)

### Regulatory & Compliance Data
- **SEC Feeds**: Investment Advisers Act compliance rules
- **FINRA**: Suitability requirements (Rule 2111) and best interest standards
- **IRS**: Tax regulations and reporting requirements
- **Real-time Policy Updates**: Live regulatory changes and enforcement updates

### Synthetic Training Data
- **AI-Generated Profiles**: Diverse demographic and goal-based user profiles
- **Scenario Data**: Historical market downturns, economic shocks, and stress events
- **Portfolio Simulations**: Backtesting data for strategy validation

### Limitations & Considerations
- **API Reliability**: Real-time policy data integration may face connectivity issues
- **Behavioral Finance**: Synthetic data may not fully capture psychological trading patterns
- **Regulatory Changes**: Compliance rules may update faster than system adaptation

## 🚀 What Differentiates MyFalconAdvisor

### vs. Traditional Robo-Advisors (Betterment, Vanguard Digital, Fidelity Go)

| **Feature** | **Traditional Robo-Advisors** | **MyFalconAdvisor** |
|-------------|-------------------------------|---------------------|
| **User Interaction** | Static dashboards, background automation | Conversational AI, natural language queries |
| **Personalization** | Predefined risk models | Dynamic, context-aware recommendations |
| **Compliance** | Basic suitability checks | Real-time SEC/FINRA/IRS validation |
| **Transparency** | Limited execution details | Immutable audit trail, full transparency |
| **Engagement** | Passive portfolio monitoring | Active dialogue, scenario simulation |
| **Accessibility** | High minimum investments | Democratized access for all income levels |

### Core Differentiators

#### 1. **Conversation-Driven Guidance**
- Natural language interaction vs. static forms
- Contextual advice based on user queries ("How's my portfolio during this market downturn?")
- Educational explanations that build financial literacy

#### 2. **Full Advisory Loop Integration**
- **Advice → Compliance → Execution** in single workflow
- Real-time regulatory validation before user sees recommendations
- Explicit consent and approval at every execution step

#### 3. **Advanced Features**
- **Scenario Simulation**: "What if I lose my job?" or "What if I get a 20% raise?"
- **Tax-Loss Harvesting**: Automated tax optimization strategies
- **Gamification**: Financial goal tracking and achievement rewards
- **Alpaca Integration**: Realistic paper trading and backtesting

#### 4. **Trust & Transparency**
- Complete audit trail for all recommendations and trades
- Compliance-first approach with detailed regulatory explanations
- Open-source architecture for community validation and improvement

## 🎓 Capstone Project Impact

### Academic Contributions
- **Multi-Agent AI Systems**: Novel application of LangGraph in financial services
- **Regulatory Compliance Automation**: Real-time policy validation framework
- **Conversational Finance**: Natural language interface for complex financial decisions
- **Behavioral Finance Integration**: User engagement through gamification and education

### Real-World Applications
- **Financial Inclusion**: Affordable advice for underserved populations
- **Scalability**: Serving millions without human advisor overhead
- **Regulatory Innovation**: Automated compliance for fintech platforms
- **Educational Impact**: Improving financial literacy through interactive guidance

### Expected Outcomes
- **Increased User Engagement**: 3x higher interaction rates vs. traditional platforms
- **Improved Investment Outcomes**: Better risk-adjusted returns through personalized advice
- **Enhanced Trust**: Complete transparency and regulatory compliance
- **Market Disruption**: New standard for AI-driven financial advisory services

## 🔬 Advanced Features

### Quantitative Finance
- Modern Portfolio Theory optimization
- Value-at-Risk (VaR) and Expected Shortfall calculations
- Monte Carlo simulations for stress testing
- Sharpe ratio, Sortino ratio, and other performance metrics
- Factor model analysis and attribution

### Regulatory Compliance
- **SEC Investment Advisers Act** compliance checking
- **FINRA Rule 2111** suitability requirements
- **Regulation BI** best interest standards
- Automated disclosure generation
- Audit trail maintenance

### Risk Management
- Interactive risk tolerance assessment
- Scenario-based stress testing (market crashes, interest rate shocks)
- Behavioral finance considerations (loss aversion, overconfidence)
- Position sizing and concentration limits
- Diversification analysis across sectors and asset classes

## 🧪 Development

### Setup Development Environment
```bash
# Install with development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest

# Code formatting
black myfalconadvisor/
isort myfalconadvisor/

# Type checking
mypy myfalconadvisor/
```

### Database Setup

The system uses PostgreSQL for data persistence. Set up your database:

```bash
# Initialize database schema
cd DBAdmin/
./setup_database.sh

# Or manually run the schema
psql -h your_host -U your_user -d myfalconadvisor_db -f all_ddls.sql
```

**Database Schema Includes**:
- **users**: User profiles with risk tolerance and financial data
- **portfolios**: User portfolio information and cash balances
- **portfolio_assets**: Individual holdings and allocations
- **transactions**: Complete transaction history
- **ai_sessions**: AI conversation sessions
- **ai_messages**: Individual AI interactions
- **recommendations**: AI-generated investment recommendations
- **compliance_checks**: Regulatory validation results
- **agent_workflows**: Multi-agent process tracking

### Testing the System

```bash
# Run comprehensive test suite
python tests/run_all_tests.py

# Test specific components
python tests/test_ai_agents.py
python tests/test_complete_logging_workflow.py

# Test CLI functionality
myfalcon demo "How is my portfolio performing?"
myfalcon interactive
```

## 📈 Real Financial Data

The system integrates with multiple financial data providers:

- **yfinance**: Real-time stock prices and historical data
- **Alpha Vantage**: Professional-grade financial data API
- **FRED**: Economic data from the Federal Reserve
- **Market sectors**: Real-time sector performance analysis
- **Risk-free rates**: Current Treasury rates for calculations

## 🎓 Masters Capstone Project

This project demonstrates:

- **Advanced AI Integration**: Multi-agent systems with LangGraph
- **Financial Domain Expertise**: Quantitative finance and regulatory compliance
- **Real-world Application**: Production-ready financial advisory system
- **Scalable Architecture**: Handles millions of users without human advisors
- **Educational Impact**: Makes sophisticated investment management accessible

## 👥 Team & Roles

### Core Development Team

| **Role** | **Team Member** | **Responsibilities** |
|----------|-----------------|---------------------|
| **Advisor Agent Lead** | Akshay Prabu / Monoo Prasad | Conversational AI, portfolio analysis, scenario simulation |
| **Compliance Agent Lead** | Nuzhat | Regulatory validation, rules engines, compliance monitoring |
| **Execution Agent Lead** | Monoo Prasad | Trade execution, logging, transaction security, Alpaca integration |
| **Web & UX Lead** | Vibha Gupta | Frontend/backend integration, UX flows, data onboarding |
| **Quantitative Analyst** | Akshay Prabu / Nuzhat | Scenario modeling, portfolio stress testing, analytics |
| **Technical Documentation** | All Team Members | Project report, API documentation, user guides |

### Contribution Areas
- **AI/ML Development**: Multi-agent systems, natural language processing, LangGraph orchestration
- **Financial Engineering**: Portfolio optimization, risk assessment, compliance validation
- **Full-Stack Development**: React/Vue frontend, Python backend, API integration
- **Data Engineering**: Real-time data feeds, market data processing, regulatory data integration
- **DevOps & Security**: Secure logging, audit trails, API security, deployment automation

## 🎯 Project Timeline & Milestones

### Phase 1: Foundation (Weeks 1-4)
- ✅ Multi-agent architecture setup with LangGraph
- ✅ Core compliance checking framework
- ✅ Basic CLI interface and portfolio analysis
- ✅ Market data integration (Yahoo Finance, Alpha Vantage)

### Phase 2: Core Features (Weeks 5-8)
- 🔄 Conversational AI interface development
- 🔄 Real-time compliance validation
- 🔄 Alpaca API integration for trade execution
- 🔄 Scenario simulation engine

### Phase 3: Advanced Features (Weeks 9-12)
- 📋 Web frontend development (React/Vue)
- 📋 Tax-loss harvesting algorithms
- 📋 Gamification and user engagement features
- 📋 Mobile-responsive design

### Phase 4: Testing & Deployment (Weeks 13-16)
- 📋 Comprehensive system testing
- 📋 Performance optimization
- 📋 Security audit and compliance validation
- 📋 Production deployment and documentation

## 📝 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

This is a Masters Capstone project developed by the MyFalconAdvisor team. For academic collaboration or questions:

1. Review our project documentation and codebase
2. Create issues for bugs or feature suggestions
3. Fork the repository for experimental features
4. Submit pull requests with detailed descriptions
5. Follow our coding standards and testing requirements

## 📧 Contact & Support

### Academic Inquiries
For questions about this Masters Capstone project, research methodology, or technical implementation:
- **Project Repository**: [GitHub Issues](https://github.com/MonooPrasadEB/MyFalconAdvisor/issues)
- **Academic Supervisor**: [Contact through university channels]
- **Technical Documentation**: See `/docs` folder for detailed API and system documentation

### Industry Collaboration
For potential partnerships, licensing, or commercial applications:
- **Business Development**: Contact through repository maintainers
- **Technical Integration**: Review our API documentation and integration guides
- **Research Collaboration**: Open to academic and industry research partnerships

---

**MyFalconAdvisor** - Democratizing AI-powered financial advisory services through conversation-driven guidance, regulatory compliance, and transparent execution.

*Built with ❤️ by the MyFalconAdvisor team as part of the BAN 693 Masters Capstone program.*
