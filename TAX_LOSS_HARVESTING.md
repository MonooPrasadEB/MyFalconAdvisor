# Tax Loss Harvesting Implementation

## Overview

Tax loss harvesting is now fully integrated into MyFalconAdvisor. This feature automatically identifies unrealized losses in your portfolio and helps you realize them for tax benefits while maintaining market exposure through wash-sale compliant alternatives.

## Features

### 1. **Automatic Loss Detection**
- Analyzes all portfolio positions for unrealized losses
- Uses actual cost basis from `portfolio_assets.average_cost`
- Minimum thresholds: $500 loss and 5% loss percentage
- Calculates potential tax savings based on your tax bracket

### 2. **Wash Sale Compliance**
- Tracks recent sales (last 30 days) to detect wash sale violations
- Automatically finds compliant alternatives for each position
- Prevents harvesting if wash sale window is active
- Provides alternative ETF suggestions (e.g., SPY → VOO, QQQ → QQQM)

### 3. **Automated Execution**
- Executes sell order for loss position
- Optionally buys alternative security to maintain exposure
- Integrates with Alpaca trading service
- Records all transactions in database

## API Endpoints

### Analyze Tax Loss Harvesting Opportunities

```bash
GET /tax-loss-harvesting/analyze
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "opportunities": [
    {
      "symbol": "SPY",
      "asset_name": "SPDR S&P 500 ETF Trust",
      "quantity": 22.5,
      "current_price": 535.82,
      "cost_basis": 580.00,
      "unrealized_loss": -995.55,
      "loss_percentage": -7.65,
      "potential_tax_savings": 268.80,
      "alternative_symbols": ["VOO", "IVV", "SWPPX"],
      "wash_sale_risk": false
    }
  ],
  "summary": {
    "opportunities_count": 3,
    "total_potential_savings": 1250.50,
    "total_realized_loss": 4630.00,
    "average_loss_percentage": -8.2,
    "wash_sale_risks": 0
  }
}
```

### Execute Tax Loss Harvesting

```bash
POST /tax-loss-harvesting/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "symbol": "SPY",
  "alternative_symbol": "VOO",  // Optional, defaults to first alternative
  "reinvest": true  // Whether to buy alternative immediately
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Tax-loss harvest executed for SPY",
  "tax_savings": 268.80,
  "realized_loss": -995.55,
  "sell_order": {
    "order_id": "abc123",
    "status": "filled",
    "executed_price": 535.82
  },
  "buy_order": {
    "order_id": "def456",
    "status": "filled",
    "executed_price": 535.50
  },
  "alternative_symbol": "VOO"
}
```

## Service Architecture

### TaxLossHarvestingService

Located in `myfalconadvisor/tools/tax_loss_harvesting_service.py`

**Key Methods:**

1. **`analyze_portfolio(portfolio_id, user_id, tax_rate)`**
   - Analyzes all positions for harvesting opportunities
   - Returns list of `TaxLossOpportunity` objects

2. **`execute_harvest(portfolio_id, user_id, opportunity, alternative_symbol, reinvest)`**
   - Executes sell + buy trades
   - Checks wash sale compliance
   - Returns execution results

3. **`get_harvest_summary(opportunities)`**
   - Generates summary statistics
   - Calculates total potential savings

### Integration Points

- **Database Service**: Reads `portfolio_assets` for cost basis and `transactions` for wash sale detection
- **Alpaca Trading Service**: Executes sell and buy orders
- **Compliance Checker**: Validates wash sale rules
- **Execution Agent**: Can be integrated for automated harvesting

## Wash Sale Alternatives

The service includes a comprehensive mapping of ETF alternatives:

| Original | Alternatives |
|----------|-------------|
| SPY | VOO, IVV, SWPPX |
| QQQ | ONEQ, QQQM, FTEC |
| VTI | ITOT, SCHB, SWTSX |
| VEA | IXUS, IEFA, VXUS |
| BND | AGG, SCHZ, VBTLX |
| GLD | IAU, SGOL, OUNZ |

For individual stocks, the service suggests sector ETFs or broad market ETFs.

## Configuration

Default settings in `TaxLossHarvestingService`:

- **Minimum Loss Threshold**: $500
- **Minimum Loss Percentage**: 5%
- **Default Tax Rate**: 27%
- **Wash Sale Window**: 30 days

These can be customized when initializing the service.

## Database Schema

The service uses existing tables:

- **`portfolio_assets`**: Contains `average_cost` (used as cost basis)
- **`transactions`**: Tracks recent sales for wash sale detection
- **`portfolios`**: Portfolio metadata

## Frontend Integration

The frontend `TaxOptimization.jsx` component can now call:

```javascript
// Analyze opportunities
const response = await axios.get(`${API_BASE}/tax-loss-harvesting/analyze`, {
  headers: { Authorization: `Bearer ${token}` }
});

// Execute harvest
await axios.post(`${API_BASE}/tax-loss-harvesting/execute`, {
  symbol: "SPY",
  alternative_symbol: "VOO",
  reinvest: true
}, {
  headers: { Authorization: `Bearer ${token}` }
});
```

## Testing

To test the tax loss harvesting:

1. **Ensure portfolio has positions with losses**:
   - Positions should have `average_cost > current_price`
   - Loss should be > $500 and > 5%

2. **Test analysis endpoint**:
   ```bash
   curl -X GET http://localhost:8000/tax-loss-harvesting/analyze \
     -H "Authorization: Bearer <token>"
   ```

3. **Test execution endpoint**:
   ```bash
   curl -X POST http://localhost:8000/tax-loss-harvesting/execute \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"symbol": "SPY", "reinvest": true}'
   ```

## Future Enhancements

- [ ] Tax lot tracking (FIFO, LIFO, specific identification)
- [ ] Long-term vs short-term gain/loss tracking
- [ ] Automated harvesting on schedule (e.g., monthly)
- [ ] Integration with tax filing software
- [ ] Real-time cost basis updates from brokerage feeds
- [ ] Multi-account harvesting coordination

## Compliance Notes

- Always consult with a tax advisor before executing tax-loss harvesting
- Wash sale rules apply to substantially identical securities
- Tax-loss harvesting is most effective in taxable accounts
- Consider holding period for long-term vs short-term gains
- Maximum $3,000 can be deducted against ordinary income per year

## Support

For issues or questions, check:
- API documentation: `http://localhost:8000/docs`
- Service logs: `/tmp/falcon/tax_loss_harvesting.log`
- Database logs: `/tmp/falcon/database_service.log`

