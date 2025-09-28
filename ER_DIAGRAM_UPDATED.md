# MyFalconAdvisor - Updated Entity Relationship Diagram

## 📊 Database Schema with Active/Unused Table Classification

```
                    MyFalconAdvisor Database Schema
                           (Updated Architecture)

┌─────────────────────────────────────────────────────────────────────────────┐
│                           🔄 ACTIVE TABLES                                  │
│                        (Used by All Components)                             │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │     users       │
                              │ ✅ ACTIVE       │
                              │                 │
                              │ user_id (PK)    │
                              │ email           │
                              │ first_name      │
                              │ last_name       │
                              │ dob             │
                              │ risk_profile    │
                              │ annual_income   │
                              │ objective       │
                              │ created_at      │
                              └─────────────────┘
                                       │
                                       │ 1:N
                                       ▼
                              ┌─────────────────┐
                              │   portfolios    │
                              │ ✅ ACTIVE       │
                              │                 │
                              │ portfolio_id(PK)│
                              │ user_id (FK)    │
                              │ portfolio_name  │
                              │ portfolio_type  │
                              │ total_value     │
                              │ cash_balance    │
                              │ created_at      │
                              │ updated_at      │
                              └─────────────────┘
                                       │
                          ┌────────────┼────────────┐
                          │ 1:N        │ 1:N        │
                          ▼            ▼            ▼
              ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
              │portfolio_assets │ │  transactions   │ │   accounts      │
              │ ✅ ACTIVE       │ │ ✅ PRIMARY      │ │ ✅ ACTIVE       │
              │                 │ │ TRADING TABLE   │ │                 │
              │ asset_id (PK)   │ │                 │ │ account_id (PK) │
              │ portfolio_id(FK)│ │ transaction_id  │ │ user_id (FK)    │
              │ symbol          │ │ portfolio_id(FK)│ │ account_type    │
              │ quantity        │ │ user_id (FK)    │ │ broker_name     │
              │ current_price   │ │ symbol          │ │ account_number  │
              │ market_value    │ │ transaction_type│ │ is_active       │
              │ average_cost    │ │ quantity        │ │ created_at      │
              │ allocation_%    │ │ price           │ └─────────────────┘
              │ updated_at      │ │ total_amount    │
              └─────────────────┘ │ fees            │
                                  │ order_type      │
                                  │ status          │ ◄─── 🎯 KEY FIELD
                                  │ execution_date  │      (pending→executed)
                                  │ broker_reference│ ◄─── 🔗 Alpaca Order ID
                                  │ notes           │
                                  │ created_at      │
                                  │ updated_at      │
                                  └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           🤖 AI & COMPLIANCE TABLES                         │
│                        (Used by Multi-Agent System)                         │
└─────────────────────────────────────────────────────────────────────────────┘

              ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
              │  ai_sessions    │ │  ai_messages    │ │ recommendations │
              │ ✅ ACTIVE       │ │ ✅ ACTIVE       │ │ ✅ ACTIVE       │
              │                 │ │                 │ │                 │
              │ session_id (PK) │ │ message_id (PK) │ │ rec_id (PK)     │
              │ user_id (FK)    │ │ session_id (FK) │ │ account_id      │
              │ session_type    │ │ agent_type      │ │ ticker          │
              │ started_at      │ │ message_type    │ │ action          │
              │ ended_at        │ │ content         │ │ percentage      │
              │ context_data    │ │ metadata        │ │ rationale       │
              └─────────────────┘ │ created_at      │ │ created_at      │
                       │          └─────────────────┘ └─────────────────┘
                       │ 1:N               │                    │
                       └───────────────────┘                    │
                                                               │
              ┌─────────────────┐ ┌─────────────────┐          │
              │compliance_checks│ │ agent_workflows │          │
              │ ✅ ACTIVE       │ │ ✅ ACTIVE       │          │
              │                 │ │                 │          │
              │ check_id (PK)   │ │ workflow_id(PK) │          │
              │ rec_id (FK)     │ │ session_id (FK) │          │
              │ user_id         │ │ workflow_type   │          │
              │ check_type      │ │ current_state   │          │
              │ status          │ │ workflow_data   │          │
              │ details         │ │ status          │          │
              │ created_at      │ │ created_at      │          │
              └─────────────────┘ │ updated_at      │          │
                       ▲          └─────────────────┘          │
                       │                                       │
                       └───────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           ❌ UNUSED TABLES                                  │
│                        (Architectural Legacy)                               │
└─────────────────────────────────────────────────────────────────────────────┘

              ┌─────────────────┐ ┌─────────────────┐
              │     orders      │ │   executions    │
              │ ❌ UNUSED       │ │ ❌ UNUSED       │
              │ LEGACY TABLE    │ │ LEGACY TABLE    │
              │                 │ │                 │
              │ order_id (PK)   │ │ exec_id (PK)    │
              │ account_id      │ │ order_id (FK)   │
              │ ticker          │ │ filled_quantity │
              │ sector          │ │ fill_price      │
              │ quantity        │ │ exec_timestamp  │
              │ order_type      │ │                 │
              │ limit_price     │ │ ⚠️  Methods      │
              │ timestamp       │ │    exist but    │
              │ time_in_force   │ │    never called │
              │                 │ │                 │
              │ ⚠️  Methods      │ │                 │
              │    exist but    │ │                 │
              │    never called │ │                 │
              └─────────────────┘ └─────────────────┘
                       ▲                    ▲
                       │                    │
                       └────────────────────┘
                              REDUNDANT
                         (Replaced by transactions)

┌─────────────────────────────────────────────────────────────────────────────┐
│                           🎯 KEY RELATIONSHIPS                              │
└─────────────────────────────────────────────────────────────────────────────┘

1. users (1) ──── (N) portfolios
2. portfolios (1) ──── (N) portfolio_assets  
3. portfolios (1) ──── (N) transactions ◄─── 🎯 PRIMARY TRADING FLOW
4. users (1) ──── (N) ai_sessions
5. ai_sessions (1) ──── (N) ai_messages
6. recommendations (1) ──── (N) compliance_checks

┌─────────────────────────────────────────────────────────────────────────────┐
│                           📊 ARCHITECTURE DECISION                          │
└─────────────────────────────────────────────────────────────────────────────┘

🎯 HYBRID TRANSACTIONS TABLE DESIGN:
   Traditional: orders + executions (2 tables, complex JOINs)
   MyFalcon:   transactions (1 table, complete lifecycle)

✅ ADVANTAGES:
   • Single source of truth for order lifecycle
   • Atomic status updates (pending → executed)
   • Simplified queries (no JOINs required)
   • Better performance (fewer table lookups)
   • Cleaner architecture (no foreign key complexity)

🔄 LIFECYCLE:
   1. Order placed    → status: 'pending', broker_reference: alpaca_id
   2. Order fills     → status: 'executed', price: fill_price, execution_date: now
   3. Sync complete   → portfolio_assets updated, portfolios.total_value updated

❌ UNUSED TABLES:
   • orders: Methods exist but workflows bypass this table
   • executions: Methods exist but never called in practice
   • All agents use alpaca_service.place_order() → transactions table
```

## 🚀 Summary

**MyFalconAdvisor uses a superior hybrid architecture**:
- ✅ **`transactions` table**: Handles complete order lifecycle
- ✅ **All agents**: Write to `transactions` for trading operations  
- ✅ **Background sync**: Monitors `transactions.broker_reference`
- ❌ **`orders`/`executions`**: Architectural dead weight, safely ignored

**The system is production-ready for web interface integration.**
