# MyFalconAdvisor

AI-powered investment advisor with comprehensive logging, database integration, and Alpaca trading.

## 🚀 System Status: Production Ready
- ✅ **100% Test Coverage** - All test suites passing
- ✅ **Daily Automatic Sync** - Portfolio syncs at 10 AM weekdays via cron
- ✅ **Secure Database User** - Using `myfalcon_app` (non-superuser)
- ✅ **Comprehensive Logging** - Dedicated log files in `/tmp/falcon/`
- ✅ **Clean Architecture** - Optimized sync process, no background service issues

## Core Components

### 🔧 Active Tools
- `alpaca_trading_service.py` - Primary trading interface with Alpaca API
- `database_service.py` - Core database operations with connection pooling
- `portfolio_analyzer.py` - Advanced portfolio analysis and risk metrics
- `risk_assessment.py` - Quantitative risk management
- `compliance_checker.py` - Regulatory compliance validation
- `chat_logger.py` - AI interaction logging to PostgreSQL
- `portfolio_sync_service.py` - Portfolio synchronization with Alpaca (manual/cron)
- `execution_agent.py` - Trade execution and validation
- `multi_task_agent.py` - AI-powered portfolio analysis and recommendations

### 🔮 Optional Tools (Future Features)
- `alpha_vantage_service.py` - Fundamental data integration
- `fred_service.py` - Economic indicators
- `multi_client_portfolio_manager.py` - Multi-user portfolio management

### 📁 Utility Scripts
See [utils/README.md](utils/README.md) for comprehensive utility documentation.

## 📊 Logging System

All services write to dedicated log files in `/tmp/falcon/`:

```bash
# Monitor trade execution (most important)
tail -f /tmp/falcon/execution_agent.log

# Monitor daily sync activity
tail -f /tmp/falcon/daily_sync.log

# Manual portfolio sync
./sync_now.sh

# Monitor Alpaca API interactions
tail -f /tmp/falcon/alpaca_trading.log

# Monitor all critical services
tail -f /tmp/falcon/execution_agent.log /tmp/falcon/portfolio_sync.log /tmp/falcon/alpaca_trading.log
```

### Log Files:
- `execution_agent.log` - Trade execution, validation, order management
- `portfolio_sync.log` - Background sync, Alpaca monitoring, portfolio updates
- `alpaca_trading.log` - Alpaca API calls, market data, order placement
- `multi_task_agent.log` - AI recommendations, portfolio analysis
- `database_service.log` - Database operations, transactions
- `system.log` - System-wide events, startup, configuration

## Setup

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Copy environment template:**
```bash
cp env.example .env
```

4. **Edit `.env` with your credentials:**
```bash
# Trading API
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_PAPER_TRADING=true

# Database
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=your_db_port
DB_NAME=your_db_name

# AI Services
OPENAI_API_KEY=your_openai_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FRED_API_KEY=your_fred_key

# Logging
LOG_LEVEL=INFO
```

## Usage

### 🧪 Running Tests
```bash
# Run comprehensive test suite (100% coverage)
python tests/run_all_tests.py

# Run specific test suites
python tests/test_alpaca_integration.py
python tests/test_execution_service_safe.py
python tests/test_ai_agents.py
```

### 📈 System Monitoring
```bash
# Manual portfolio sync (run anytime)
./sync_now.sh

# View log monitoring commands (shows all available log commands)
./utils/log_commands.sh

# Monitor daily sync activity
tail -f /tmp/falcon/daily_sync.log

# Check cron job status
crontab -l
```

### 🔄 Daily Sync Status
```bash
# Check cron job schedule
crontab -l

# Monitor daily sync logs
tail -f /tmp/falcon/daily_sync.log

# Daily automatic sync runs at 10:00 AM weekdays
```

## Architecture

### 🗄️ Database Design
**Primary Tables:**
- `transactions` - **Hybrid table** for order intent + execution results
- `portfolios` - Portfolio metadata and total values
- `portfolio_assets` - Individual stock positions (updated by sync service)
- `users` - User profiles and risk tolerance

**AI & Logging Tables:**
- `ai_sessions` - AI conversation sessions
- `ai_messages` - Individual AI interactions  
- `recommendations` - AI-generated trade recommendations
- `compliance_checks` - Regulatory validation results
- `agent_workflows` - Multi-agent process tracking

**Legacy Tables (Unused):**
- `orders` - Redundant with transactions table
- `executions` - Redundant with transactions table
- `interactions` - Legacy chat logging

### 🤖 AI Agent Architecture
- **Multi-Task Agent** - Portfolio analysis, risk assessment, recommendations
- **Execution Agent** - Trade validation, execution, database logging
- **Compliance Agent** - Regulatory checks, risk validation
- **Supervisor** - Orchestrates multi-agent workflows

### 🔄 Data Flow
1. **AI generates recommendation** → `recommendations` table
2. **Execution agent validates** → `compliance_checks` table
3. **Trade executed via Alpaca** → `transactions` table
4. **Daily sync updates** → `portfolio_assets` table (via cron job)
5. **All activity logged** → `/tmp/falcon/*.log` files

## 🔐 Database Configuration

### Secure Database User
- **Database User**: `myfalcon_app` (non-superuser)
- **Database Host**: `pg-2e1b40a1-falcon-horizon-5e1b-falccon.i.aivencloud.com`
- **Database Name**: `defaultdb`
- **Connection Type**: Secure, limited permissions
- **Benefits**: No superuser connection conflicts, proper security isolation

### Daily Portfolio Sync
- **Schedule**: Every weekday at 10:00 AM
- **Method**: Cron job (reliable, no background processes)
- **Manual Sync**: `./sync_now.sh` (available anytime)
- **Logs**: `/tmp/falcon/daily_sync.log`

## 🛡️ Production Safety

### Test Protection
- **READ-ONLY database operations** during testing
- **Mock mode enforced** for all external APIs
- **Automatic cleanup** of test data
- **Retry logic** for transient database errors

### Monitoring
- **Comprehensive logging** with rotation (10MB max, 5 backups)
- **Service-specific log files** for targeted monitoring
- **Real-time log monitoring** with `tail -f` commands
- **Error tracking** with detailed stack traces

## Contributing

1. **Create feature branch:**
```bash
git checkout -b feature/your-feature
```

2. **Make changes and run tests:**
```bash
python tests/run_all_tests.py
```

3. **Verify logs are clean:**
```bash
ls -lh /tmp/falcon/
tail -f /tmp/falcon/system.log
```

4. **Create pull request with:**
- Clear description of changes
- Test results (should be 100%)
- Any database schema changes
- Log file examples if relevant

## 📋 System Requirements

- Python 3.13+
- PostgreSQL database
- Alpaca trading account (paper trading recommended)
- OpenAI API key for AI features
- 10MB+ disk space for logs

## 🎯 Next Steps

- **Web Interface** - Frontend for portfolio management
- **Real-time Dashboard** - Live portfolio monitoring
- **Advanced Analytics** - Performance attribution, risk metrics
- **Multi-client Support** - Manage multiple portfolios
- **Mobile Notifications** - Trade alerts and updates