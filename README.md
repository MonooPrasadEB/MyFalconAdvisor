# MyFalconAdvisor

AI-powered investment advisor with Alpaca integration.

## Core Components

### Tools
- `alpaca_trading_service.py` - Primary trading interface
- `database_service.py` - Core database operations
- `portfolio_analyzer.py` - Portfolio analysis
- `risk_assessment.py` - Risk management
- `compliance_checker.py` - Regulatory compliance
- `chat_logger.py` - AI interaction logging
- `portfolio_sync_service.py` - Alpaca sync service

### Optional Tools (Future Features)
- `alpha_vantage_service.py` - Fundamental data
- `fred_service.py` - Economic indicators
- `multi_client_portfolio_manager.py` - Multi-user support

### Utility Scripts
See [utils/README.md](utils/README.md) for utility script documentation.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment template:
```bash
cp env.example .env
```

4. Edit `.env` with your credentials:
```
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

## Usage

### Running Tests
```bash
# Run all tests (enforces mock mode)
python tests/run_all_tests.py

# Run specific test
python tests/test_alpaca_integration.py
```

### Managing Orders
```bash
# Check pending orders
python utils/check_alpaca_orders.py

# Cancel all orders
python utils/cancel_all_orders.py
```

### Database Operations
```bash
# Check database state
python utils/check_db.py
```

## Architecture

### Database Tables
- `transactions` - Primary trading table (order intent + execution)
- `portfolios` - Portfolio metadata and total values
- `portfolio_assets` - Individual stock positions
- `users` - User profiles and risk tolerance

### AI Components
- `ai_sessions` - AI conversation sessions
- `ai_messages` - Individual AI interactions
- `recommendations` - AI-generated recommendations
- `compliance_checks` - Regulatory validation
- `agent_workflows` - Multi-agent process tracking

## Contributing

1. Create feature branch:
```bash
git checkout -b feature/your-feature
```

2. Make changes and run tests:
```bash
python tests/run_all_tests.py
```

3. Create pull request with:
- Clear description
- Test results
- Any database changes