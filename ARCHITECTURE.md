# MyFalconAdvisor - System Architecture

## 📊 Database Architecture & Codebase Usage Analysis

Based on comprehensive codebase analysis of 30 Python files checking 24 database tables.

### **✅ CORE PRODUCTION TABLES (4 tables - 17%)**
**Essential functionality - Heavily referenced in code**

#### **Core Trading Tables**
- **`transactions`** - **PRIMARY TRADING TABLE**
  - **Purpose**: Complete order lifecycle (intent → execution)
  - **Used by**: All agents, alpaca_trading_service, sync services
  - **Lifecycle**: `pending` → `executed`/`canceled`
  - **Key Fields**: `broker_reference` (Alpaca order ID), `status`, `price`, `execution_date`

#### **Portfolio Management Tables**
- **`portfolios`** - Portfolio metadata and total values
- **`portfolio_assets`** - Individual stock positions and allocations
- **`users`** - User profiles, risk tolerance, financial data

#### **AI & Compliance Tables**
- **`ai_sessions`** - AI conversation sessions
- **`ai_messages`** - Individual AI interactions and responses
- **`recommendations`** - AI-generated investment recommendations
- **`compliance_checks`** - Regulatory validation results
- **`agent_workflows`** - Multi-agent process tracking

### **❌ Unused Tables (Architectural Legacy)**

#### **Redundant Trading Tables**
- **`orders`** - ❌ **NOT USED**
  - Methods exist (`log_order()`, `_write_to_orders_table()`) but **never called**
  - Redundant with `transactions` table
  - All workflows bypass this table

- **`executions`** - ❌ **NOT USED**
  - Methods exist (`log_execution()`) but **never called**
  - Redundant with `transactions` table
  - All execution tracking done via `transactions.status` updates

### **📊 Architecture Decision: Hybrid Transactions Table**

The `transactions` table implements a **superior hybrid design** that combines traditional `orders` + `executions` functionality:

```sql
-- Traditional Approach (2 tables)
orders:     order_id, symbol, quantity, order_type, timestamp
executions: exec_id, order_id, fill_price, fill_quantity, exec_timestamp

-- MyFalconAdvisor Hybrid Approach (1 table)
transactions: transaction_id, symbol, quantity, order_type, 
              status, price, execution_date, broker_reference
```

#### **Advantages of Hybrid Design**:
- ✅ **Single Source of Truth**: Complete lifecycle in one record
- ✅ **Atomic Updates**: `pending` → `executed` status changes
- ✅ **Simplified Queries**: No complex JOINs required
- ✅ **Better Performance**: Fewer table lookups
- ✅ **Cleaner Architecture**: Eliminates foreign key complexity

## 🔄 Agent & Tool Database Usage

### **🤖 Execution Agent**
**Writes to**:
- ✅ `recommendations` (AI recommendations)
- ✅ `compliance_checks` (regulatory validation)
- ✅ `agent_workflows` (process tracking)
- ✅ `ai_sessions` (conversation logging)
- ✅ `ai_messages` (interaction logging)
- ✅ `transactions` (via `alpaca_service.place_order()`)

**Does NOT write to**:
- ❌ `orders` (method exists but bypassed)
- ❌ `executions` (not used)

### **🔧 Alpaca Trading Service**
**Writes to**:
- ✅ `transactions` (`place_order()` method)
- ✅ `portfolio_assets` (`sync_portfolio_from_alpaca()`)
- ✅ `portfolios` (total value updates)

**Does NOT write to**:
- ❌ `orders` (not used)
- ❌ `executions` (not used)

### **🔄 Portfolio Sync Service**
**Updates**:
- ✅ `transactions` (status: `pending` → `executed`)
- ✅ `portfolio_assets` (position syncing)
- ✅ `portfolios` (total value recalculation)

**Does NOT touch**:
- ❌ `orders` (not monitored)
- ❌ `executions` (not created)

### **📝 Chat Logger**
**Writes to**:
- ✅ `ai_sessions`
- ✅ `ai_messages`

**Has unused methods for**:
- ❌ `orders` (`log_order()` - never called)
- ❌ `executions` (`log_execution()` - never called)

## 🎯 Web Interface Workflow

### **Complete Trading Workflow**:
1. **User Request**: "Buy 100 shares of AAPL"
2. **Execution Agent**: Validates against portfolio
3. **Compliance Agent**: Checks regulatory requirements
4. **User Approval**: Web UI confirmation
5. **Trade Execution**: `alpaca_service.place_order()`
6. **Database Write**: Single record to `transactions` table
7. **Background Sync**: Monitors `broker_reference` for fills
8. **Status Update**: `transactions.status` → `executed`

### **Database Tables Updated**:
- ✅ `transactions` (order lifecycle)
- ✅ `portfolio_assets` (new positions)
- ✅ `portfolios` (total value)
- ✅ `ai_sessions` (conversation)
- ✅ `ai_messages` (interactions)
- ✅ `recommendations` (AI advice)
- ✅ `compliance_checks` (validation)

### **Tables NOT Used**:
- ❌ `orders` (architectural dead weight)
- ❌ `executions` (architectural dead weight)

## 📊 Updated Entity Relationship Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     users       │    │   portfolios    │    │ portfolio_assets│
│ ✅ ACTIVE       │────│ ✅ ACTIVE       │────│ ✅ ACTIVE       │
│                 │    │                 │    │                 │
│ user_id (PK)    │    │ portfolio_id    │    │ asset_id (PK)   │
│ email           │    │ user_id (FK)    │    │ portfolio_id    │
│ risk_profile    │    │ total_value     │    │ symbol          │
│ annual_income   │    │ cash_balance    │    │ quantity        │
└─────────────────┘    └─────────────────┘    │ current_price   │
                                              │ market_value    │
                                              └─────────────────┘
         │
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  transactions   │    │ ai_sessions     │    │  ai_messages    │
│ ✅ PRIMARY      │    │ ✅ ACTIVE       │    │ ✅ ACTIVE       │
│ TRADING TABLE   │    │                 │    │                 │
│                 │    │ session_id (PK) │    │ message_id (PK) │
│ transaction_id  │    │ user_id         │    │ session_id (FK) │
│ portfolio_id    │    │ session_type    │    │ agent_type      │
│ user_id (FK)    │    │ started_at      │    │ message_type    │
│ symbol          │    │ ended_at        │    │ content         │
│ quantity        │    │ context_data    │    │ created_at      │
│ status          │────┼─────────────────┼────┼─────────────────│
│ price           │    │                 │    │                 │
│ broker_reference│    │                 │    │                 │
│ execution_date  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ recommendations │    │compliance_checks│    │ agent_workflows │
│ ✅ ACTIVE       │    │ ✅ ACTIVE       │    │ ✅ ACTIVE       │
│                 │    │                 │    │                 │
│ rec_id (PK)     │    │ check_id (PK)   │    │ workflow_id     │
│ account_id      │    │ rec_id (FK)     │    │ session_id (FK) │
│ ticker          │    │ user_id         │    │ workflow_type   │
│ action          │    │ check_type      │    │ current_state   │
│ percentage      │    │ status          │    │ workflow_data   │
│ rationale       │    │ details         │    │ created_at      │
└─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────┐    ┌─────────────────┐
│     orders      │    │   executions    │
│ ❌ UNUSED       │    │ ❌ UNUSED       │
│ LEGACY TABLE    │    │ LEGACY TABLE    │
│                 │    │                 │
│ order_id (PK)   │    │ exec_id (PK)    │
│ account_id      │    │ order_id (FK)   │
│ ticker          │    │ filled_quantity │
│ quantity        │    │ fill_price      │
│ order_type      │    │ exec_timestamp  │
│ limit_price     │    │                 │
│ timestamp       │    │ ⚠️  Methods      │
│                 │    │    exist but    │
│ ⚠️  Methods      │    │    never called │
│    exist but    │    │                 │
│    never called │    │                 │
└─────────────────┘    └─────────────────┘
```

## 🚀 Conclusion

**MyFalconAdvisor's architecture is already optimized**:

- ✅ **`transactions` table**: Superior hybrid design handling complete order lifecycle
- ✅ **All agents**: Use `transactions` table for trading operations
- ✅ **Background sync**: Monitors `transactions.broker_reference` for status updates
- ✅ **Web interface**: Will work seamlessly with current architecture

**Unused tables can be safely ignored**:
- ❌ **`orders`**: Architectural dead weight
- ❌ **`executions`**: Architectural dead weight

The system is **production-ready** for web interface integration without architectural changes.
