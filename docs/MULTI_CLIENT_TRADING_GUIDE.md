# Multi-Client Trading with Single Alpaca Account

This guide explains how to handle multiple clients using your single Alpaca paper trading account while maintaining proper separation, attribution, and compliance.

## 🏗️ **Architecture Overview**

Since Alpaca accounts are individual-based, we use a **"Master Account + Virtual Portfolios"** approach:

```
┌─────────────────────────────────────┐
│        Alpaca Master Account       │
│     ($100k Paper Trading)          │
└─────────────────┬───────────────────┘
                  │
        ┌─────────┴─────────┐
        │   MyFalcon DB     │
        │   (PostgreSQL)    │
        └─────────┬─────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐    ┌───▼───┐    ┌───▼───┐
│Client │    │Client │    │Client │
│   A   │    │   B   │    │   C   │
│$25k   │    │$35k   │    │$40k   │
└───────┘    └───────┘    └───────┘
```

## 🎯 **Strategy 1: Virtual Portfolio Management (Recommended)**

### **How It Works:**
1. **Single Alpaca Account**: Your master trading account
2. **Virtual Client Portfolios**: Separate records in your database
3. **Order Attribution**: Every trade tagged with client ID
4. **Cash Allocation**: Track each client's allocated funds
5. **Position Tracking**: Maintain client-specific positions

### **Key Benefits:**
- ✅ Complete client separation in database
- ✅ Individual performance tracking
- ✅ Proper compliance per client
- ✅ Detailed audit trails
- ✅ Scalable to many clients
- ✅ Cost-effective (one Alpaca account)

## 📊 **Implementation Details**

### **Database Schema Enhancements**

Your existing schema already supports this with these key tables:

```sql
-- Each client gets their own portfolio record
portfolios (
    portfolio_id,     -- Unique per client
    user_id,         -- Client identifier
    portfolio_name,   -- "Client Name - Virtual Portfolio"
    total_value,     -- Client's total value
    cash_balance,    -- Client's cash allocation
    portfolio_type   -- "virtual_managed"
)

-- All positions tracked per client
portfolio_assets (
    portfolio_id,    -- Links to client's portfolio
    symbol,
    quantity,        -- Client's shares in this symbol
    market_value     -- Client's value in this position
)

-- Every trade attributed to specific client
transactions (
    portfolio_id,    -- Client's portfolio
    user_id,        -- Client ID
    broker_reference, -- Alpaca order ID
    notes           -- "Client order via master account"
)
```

### **Client Portfolio Management**

```python
from myfalconadvisor.tools.multi_client_portfolio_manager import multi_client_manager

# 1. Initialize client portfolio
result = multi_client_manager.initialize_client_portfolio(
    user_id="client_123",
    client_name="John Conservative",
    initial_cash=25000.0,
    risk_tolerance="conservative"
)

# 2. Place client-attributed order
order = multi_client_manager.place_client_order(
    user_id="client_123",
    symbol="AAPL",
    side="buy",
    quantity=10,
    order_type="market"
)

# 3. Get client portfolio
portfolio = multi_client_manager.get_client_portfolio("client_123")
```

## 🔄 **Order Flow Process**

### **When a Client Places an Order:**

1. **Validation**: Check client has sufficient funds/shares
2. **Attribution**: Tag order with client ID and portfolio ID
3. **Alpaca Execution**: Place order through master account
4. **Database Recording**: Record transaction with client attribution
5. **Portfolio Update**: Update client's virtual portfolio
6. **Audit Trail**: Log all actions for compliance

```python
# Example: Client wants to buy 100 AAPL shares
def process_client_order(client_id, symbol, quantity):
    # 1. Validate client funds
    client_portfolio = get_client_portfolio(client_id)
    required_cash = quantity * get_current_price(symbol)
    
    if client_portfolio['cash_balance'] < required_cash:
        return {"error": "Insufficient funds"}
    
    # 2. Place order through Alpaca
    alpaca_order = alpaca_service.place_order(
        symbol=symbol,
        quantity=quantity,
        user_id=client_id  # Attribution
    )
    
    # 3. Record in database with client attribution
    transaction_id = db_service.create_transaction({
        "portfolio_id": client_portfolio['portfolio_id'],
        "user_id": client_id,
        "symbol": symbol,
        "quantity": quantity,
        "broker_reference": alpaca_order['order_id'],
        "notes": f"Order for client {client_id}"
    })
    
    # 4. Update client's virtual portfolio
    update_client_positions(client_id, symbol, quantity)
```

## 📈 **Portfolio Reconciliation**

### **Why Reconciliation is Important:**
- Ensure virtual portfolios match actual Alpaca positions
- Catch any discrepancies from order failures
- Maintain data integrity across systems

### **Reconciliation Process:**
```python
def reconcile_portfolios():
    # 1. Get actual Alpaca positions
    alpaca_positions = alpaca_service.get_positions()
    
    # 2. Calculate total virtual positions
    virtual_totals = {}
    for client_id in all_clients:
        client_positions = get_client_positions(client_id)
        for symbol, quantity in client_positions.items():
            virtual_totals[symbol] = virtual_totals.get(symbol, 0) + quantity
    
    # 3. Compare and report discrepancies
    for symbol in virtual_totals:
        virtual_qty = virtual_totals[symbol]
        actual_qty = alpaca_positions.get(symbol, 0)
        
        if virtual_qty != actual_qty:
            log_discrepancy(symbol, virtual_qty, actual_qty)
```

## 🧪 **Testing Your Multi-Client Setup**

### **Step 1: Run the Multi-Client Demo**
```bash
cd /Users/monooprasad/Documents/MyFalconAdvisorv1
python examples/test_multi_client_trading.py
```

This will:
- Create 3 sample clients with different risk profiles
- Execute appropriate trades for each client
- Show individual portfolio performance
- Demonstrate system reconciliation

### **Step 2: Verify Database Records**
```sql
-- Check client portfolios
SELECT portfolio_name, total_value, cash_balance 
FROM portfolios 
WHERE portfolio_type = 'virtual_managed';

-- Check client positions
SELECT p.portfolio_name, pa.symbol, pa.quantity, pa.market_value
FROM portfolio_assets pa
JOIN portfolios p ON pa.portfolio_id = p.portfolio_id
WHERE p.portfolio_type = 'virtual_managed';

-- Check attributed transactions
SELECT p.portfolio_name, t.symbol, t.transaction_type, t.quantity, t.broker_reference
FROM transactions t
JOIN portfolios p ON t.portfolio_id = p.portfolio_id
WHERE p.portfolio_type = 'virtual_managed'
ORDER BY t.created_at DESC;
```

## 🔐 **Compliance and Risk Management**

### **Per-Client Compliance:**
```python
def check_client_compliance(client_id, order):
    client_profile = get_client_risk_profile(client_id)
    
    # Check position concentration
    if order.position_size > client_profile.max_position_size:
        return {"approved": False, "reason": "Exceeds position limit"}
    
    # Check risk tolerance
    if order.risk_score > client_profile.risk_tolerance_score:
        return {"approved": False, "reason": "Exceeds risk tolerance"}
    
    return {"approved": True}
```

### **Risk Monitoring:**
- Individual client position limits
- Portfolio concentration rules
- Risk tolerance adherence
- Regulatory compliance per client

## 📊 **Alternative Strategies**

### **Strategy 2: Fractional Share Allocation**
```python
# Example: Multiple clients want AAPL exposure
# Buy 100 AAPL shares, allocate fractionally:
# Client A (conservative): 20 shares
# Client B (moderate): 30 shares  
# Client C (aggressive): 50 shares
```

### **Strategy 3: ETF-Based Separation**
```python
# Use different ETFs for different client types:
# Conservative clients: BND (bonds), VTI (total market)
# Moderate clients: SPY, QQQ
# Aggressive clients: Individual growth stocks
```

### **Strategy 4: Time-Based Separation**
```python
# Execute trades for different clients at different times
# Morning: Conservative clients
# Midday: Moderate clients
# Afternoon: Aggressive clients
```

## 🎯 **Best Practices**

### **1. Cash Management**
- Always track allocated vs. available cash
- Prevent over-allocation
- Handle dividends and corporate actions

### **2. Order Management**
- Tag every order with client attribution
- Handle partial fills properly
- Maintain order audit trails

### **3. Reporting**
- Generate individual client statements
- Calculate client-specific performance
- Provide detailed trade confirmations

### **4. Reconciliation**
- Run daily reconciliation
- Monitor for discrepancies
- Alert on significant variances

## 🚀 **Scaling Considerations**

### **When You Have Many Clients:**
- Consider batch order processing
- Implement order aggregation
- Use priority queues for different client tiers
- Monitor Alpaca rate limits (200 requests/minute)

### **Advanced Features:**
- Client-specific rebalancing
- Automated tax-loss harvesting
- Performance attribution
- Risk monitoring dashboards

## 💡 **Production Deployment**

### **Before Going Live:**
1. ✅ Test thoroughly with paper trading
2. ✅ Implement comprehensive error handling
3. ✅ Set up monitoring and alerting
4. ✅ Create client onboarding process
5. ✅ Establish reconciliation procedures
6. ✅ Document compliance procedures

### **Operational Considerations:**
- Daily reconciliation reports
- Client performance statements
- Error handling and recovery
- Backup and disaster recovery
- Compliance reporting

---

**🎉 You now have a complete multi-client trading system that uses your single Alpaca account while maintaining proper client separation and compliance!**
