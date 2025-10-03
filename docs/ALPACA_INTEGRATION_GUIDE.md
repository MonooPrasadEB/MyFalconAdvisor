# Alpaca Integration Testing Guide

This guide walks you through testing your Alpaca integration with your PostgreSQL data.

## 🚀 Quick Start

### 1. Prerequisites

- ✅ PostgreSQL database set up with your schema
- ✅ Data populated in your database tables
- 📋 Alpaca paper trading account (free at [alpaca.markets](https://alpaca.markets))
- 🔑 Alpaca API keys

### 2. Setup Configuration

1. **Get Alpaca API Keys:**
   - Sign up at [alpaca.markets](https://alpaca.markets)
   - Create a paper trading account
   - Generate API keys from your dashboard

2. **Configure Environment:**
   ```bash
   cp env.example .env
   ```
   
   Edit your `.env` file:
   ```env
   # Add your Alpaca credentials
   ALPACA_API_KEY=your_alpaca_api_key_here
   ALPACA_SECRET_KEY=your_alpaca_secret_key_here
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   ALPACA_PAPER_TRADING=true
   
   # Your existing database config
   DB_USER=myfalcon_team
   DB_PASSWORD=your_team_password_here
   ```

3. **Install Dependencies:**
   ```bash
   pip install -e .
   ```

## 🧪 Testing Your Integration

### Step 1: Run the Comprehensive Test Suite

```bash
cd examples
python test_alpaca_integration.py
```

This will test:
- ✅ API connection and authentication
- ✅ Database connectivity
- ✅ Market data retrieval
- ✅ Order placement (mock/real)
- ✅ Portfolio synchronization
- ✅ Full integration workflow

### Step 2: Test Individual Components

#### Test API Connection
```python
from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service

# Test connection
result = alpaca_trading_service.test_connection()
print(result)
```

#### Test Market Data
```python
# Get market data for a symbol
market_data = alpaca_trading_service.get_market_data("AAPL")
print(f"AAPL Price: ${market_data.get('latest_price', 'N/A')}")
```

#### Test Portfolio Sync
```python
import uuid

user_id = str(uuid.uuid4())
portfolio_id = str(uuid.uuid4())

# Sync portfolio from Alpaca to database
sync_result = alpaca_trading_service.sync_portfolio_from_alpaca(user_id, portfolio_id)
print(sync_result)
```

#### Test Order Placement
```python
# Place a paper trading order
order_result = alpaca_trading_service.place_order(
    symbol="AAPL",
    side="buy",
    quantity=1,
    order_type="market",
    user_id=user_id,
    portfolio_id=portfolio_id
)
print(order_result)
```

### Step 3: Test with Your Existing System

#### Using the Updated Execution Agent
```python
from myfalconadvisor.agents.execution_agent import execution_agent

# Create a trade order
order_response = execution_agent.create_trade_order(
    client_id="test_client",
    symbol="SPY",
    action="buy",
    quantity=10,
    order_type="market",
    portfolio_value=100000
)

print(f"Order created: {order_response}")

if order_response.get("order_id"):
    # Approve the order
    approval = execution_agent.approve_order(
        order_response["order_id"],
        user_confirmation=True,
        approval_notes="Test order approval"
    )
    print(f"Order approval: {approval}")
    
    # Execute the order
    if approval.get("status") == "approved":
        execution = execution_agent.execute_order(order_response["order_id"])
        print(f"Execution result: {execution}")
```

## 📊 Database Integration Testing

### Check Data Synchronization

1. **Verify Portfolio Data:**
   ```sql
   SELECT * FROM portfolios WHERE portfolio_id = 'your_test_portfolio_id';
   ```

2. **Check Asset Positions:**
   ```sql
   SELECT * FROM portfolio_assets WHERE portfolio_id = 'your_test_portfolio_id';
   ```

3. **Review Transactions:**
   ```sql
   SELECT * FROM transactions WHERE portfolio_id = 'your_test_portfolio_id' ORDER BY created_at DESC;
   ```

4. **Audit Trail:**
   ```sql
   SELECT * FROM audit_trail WHERE entity_type = 'portfolio' ORDER BY created_at DESC LIMIT 10;
   ```

### Test Database Service Directly
```python
from myfalconadvisor.tools.database_service import database_service
import uuid
from datetime import datetime

# Test portfolio operations
portfolio_id = str(uuid.uuid4())
user_id = str(uuid.uuid4())

# Update portfolio
update_result = database_service.update_portfolio(portfolio_id, {
    "total_value": 50000.00,
    "cash_balance": 5000.00,
    "updated_at": datetime.now()
})

# Add asset
asset_result = database_service.upsert_portfolio_asset({
    "portfolio_id": portfolio_id,
    "symbol": "AAPL",
    "asset_name": "Apple Inc.",
    "asset_type": "stock",
    "quantity": 100,
    "current_price": 193.50,
    "market_value": 19350.00
})

print(f"Portfolio updated: {update_result}")
print(f"Asset added: {asset_result}")
```

## 🔄 Real-World Testing Scenarios

### Scenario 1: Portfolio Sync from Alpaca
```python
# 1. Have some positions in your Alpaca paper account
# 2. Run sync to pull into database
sync_result = alpaca_trading_service.sync_portfolio_from_alpaca(
    user_id="your_user_id",
    portfolio_id="your_portfolio_id"
)

# 3. Verify data in database
portfolio_data = database_service.get_portfolio_by_id("your_portfolio_id")
assets = database_service.get_portfolio_assets("your_portfolio_id")

print(f"Synced portfolio: {portfolio_data}")
print(f"Assets: {len(assets)} positions")
```

### Scenario 2: End-to-End Trade Execution
```python
# 1. Use your AI system to generate a recommendation
# 2. Create order through execution agent
# 3. Approve and execute
# 4. Verify in both Alpaca and database

from myfalconadvisor.core.supervisor import investment_advisor_supervisor

# Get AI recommendation
recommendation = investment_advisor_supervisor.process_client_request(
    request="I want to buy some Apple stock",
    client_profile={"risk_tolerance": "moderate", "age": 35},
    portfolio_data={"total_value": 100000}
)

print(f"AI Recommendation: {recommendation}")
```

### Scenario 3: Market Data Integration
```python
# Test real-time data flow
symbols = ["AAPL", "MSFT", "GOOGL", "SPY", "QQQ"]

for symbol in symbols:
    data = alpaca_trading_service.get_market_data(symbol)
    if not data.get("error"):
        print(f"{symbol}: ${data.get('latest_price', 'N/A')}")
        
        # Store in your database if needed
        # (You could enhance database_service to store market data)
```

## 🚨 Troubleshooting

### Common Issues

1. **"Mock Mode" Messages:**
   - Check your API keys in `.env`
   - Verify keys are valid in Alpaca dashboard
   - Ensure `ALPACA_PAPER_TRADING=true` for testing

2. **Database Connection Errors:**
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure database schema is created

3. **Import Errors:**
   - Run `pip install -e .` to install in development mode
   - Check all dependencies are installed

4. **API Rate Limits:**
   - Alpaca has rate limits (200 requests/minute)
   - The service includes basic rate limiting

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎯 Next Steps

Once basic testing works:

1. **Production Setup:**
   - Switch to live Alpaca API (`ALPACA_PAPER_TRADING=false`)
   - Implement proper error handling
   - Add monitoring and alerting

2. **Enhanced Features:**
   - Real-time portfolio sync scheduling
   - Advanced order types (stop-loss, etc.)
   - Risk management integration
   - Performance analytics

3. **Integration with Your AI System:**
   - Connect recommendations to actual trades
   - Implement approval workflows
   - Add compliance checking

4. **Monitoring:**
   - Set up logging and metrics
   - Monitor API usage and costs
   - Track execution performance

## 📞 Support

- **Alpaca Documentation:** [docs.alpaca.markets](https://docs.alpaca.markets)
- **PostgreSQL Docs:** [postgresql.org/docs](https://www.postgresql.org/docs/)
- **Test Issues:** Check logs and error messages in the test output

---

**⚠️ Important:** Always test with paper trading first. Never use live trading without thorough testing and proper risk management controls.
