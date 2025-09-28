# MyFalconAdvisor Utility Scripts

This directory contains utility scripts for managing and monitoring the MyFalconAdvisor system.

## Scripts

### Trading Management
- `check_alpaca_orders.py` - Display pending Alpaca orders
- `cancel_all_orders.py` - Cancel all pending Alpaca orders
- `sell_with_tracking.py` - Sell positions with transaction tracking

### Database Management
- `check_db.py` - Check database state and records
- `env_loader.py` - Load environment variables consistently

## Usage

All scripts use the same environment variables from `.env` file. To run any script:

```bash
# Activate virtual environment
source venv/bin/activate

# Run script
python utils/script_name.py
```

## Common Environment Variables

- `ALPACA_API_KEY` - Alpaca API key
- `ALPACA_SECRET_KEY` - Alpaca secret key
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password