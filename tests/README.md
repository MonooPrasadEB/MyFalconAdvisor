# MyFalconAdvisor Test Suite

This directory contains comprehensive tests for all MyFalconAdvisor components.

## 🧪 Test Files

### Core Integration Tests
- **`test_database_connection.py`** - PostgreSQL database connectivity (READ-ONLY operations)
- **`test_alpaca_integration.py`** - Alpaca API connection, market data, and order placement
- **`test_ai_agents.py`** - AI agents functionality (multi-task, compliance, execution)
- **`test_complete_logging_workflow_readonly.py`** - Complete AI workflow testing (NO DB WRITES)
- **`test_multi_client_system.py`** - Multi-client portfolio management system

### 🛡️ Production Database Protection
**IMPORTANT:** All tests have been updated to use READ-ONLY operations to protect production data:
- Database tests only perform SELECT queries
- No INSERT, UPDATE, or DELETE operations on production tables
- Method signature testing instead of actual database writes
- Mock data validation without persistence

### Test Runner
- **`run_all_tests.py`** - Master test runner that executes all test suites

## 🚀 Quick Start

### Run All Tests
```bash
cd /Users/monooprasad/Documents/MyFalconAdvisorv1
python tests/run_all_tests.py
```

### Run Individual Test Suites
```bash
# Database tests
python tests/test_database_connection.py

# Alpaca integration tests  
python tests/test_alpaca_integration.py

# AI agents tests
python tests/test_ai_agents.py

# Complete logging workflow tests
python tests/test_complete_logging_workflow.py

# Multi-client system tests
python tests/test_multi_client_system.py
```

## 📋 Prerequisites

Before running tests, ensure you have:

1. **Environment Configuration** - `.env` file with required API keys
2. **Database Access** - PostgreSQL connection to Aiven database
3. **API Keys** - OpenAI, Alpaca, Alpha Vantage, FRED (optional)
4. **Dependencies** - All Python packages installed

## 🔧 Test Categories

### 🗄️ Database Tests
- Connection validation
- Schema verification
- CRUD operations
- Transaction handling

### 📈 Alpaca Tests  
- API authentication
- Market data retrieval
- Order placement
- Account information

### 🤖 AI Agent Tests
- Multi-task agent functionality
- Compliance reviewer
- Execution service
- Tool availability

### 📝 Complete Logging Workflow Tests
- ExecutionService initialization
- Database write methods
- Portfolio validation logic
- Complete AI workflow with database logging
- Table population verification

### 🏢 Multi-Client Tests
- Portfolio creation
- Virtual trading
- Client attribution
- Database integration

## 📊 Test Results

The test runner provides:
- **Individual test scores** for each component
- **Overall system health** percentage
- **Detailed error reporting** for failed tests
- **Recommendations** for fixing issues

## 🎯 Success Criteria

- **90%+ Overall Score** - Production ready
- **75%+ Overall Score** - Good, minor issues
- **50%+ Overall Score** - Fair, needs attention
- **<50% Overall Score** - Poor, major fixes needed

## 🔍 Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```bash
   # Check your .env file has:
   OPENAI_API_KEY=your_key_here
   ALPACA_API_KEY=your_key_here
   ALPACA_SECRET_KEY=your_secret_here
   ```

2. **Database Connection**
   ```bash
   # Verify database credentials:
   DB_HOST=your_host
   DB_NAME=myfalconadvisor_db
   DB_USER=your_user
   DB_PASSWORD=your_password
   ```

3. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   # or
   pip install langchain openai alpaca-py psycopg2-binary pandas numpy
   ```

## 📝 Adding New Tests

To add new test files:

1. Create test file in `/tests/` directory
2. Follow naming convention: `test_*.py`
3. Include proper error handling and reporting
4. Add to `run_all_tests.py` test suites list

## 🏆 Best Practices

- **Run tests regularly** during development
- **Fix failing tests** before deploying
- **Check prerequisites** first if tests fail
- **Review detailed output** for specific error messages
- **Use individual test files** for focused debugging
