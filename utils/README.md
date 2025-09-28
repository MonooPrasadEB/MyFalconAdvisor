# MyFalconAdvisor Utility Scripts

This directory contains utility scripts for monitoring and managing the MyFalconAdvisor system.

## Monitoring Scripts

### `check_db.py`
Monitor database state and transactions:
```bash
python utils/check_db.py
```
Shows:
- Current transactions
- Portfolio states
- Database records

### `check_orders.py` and `check_alpaca_orders.py`
Monitor Alpaca orders:
```bash
python utils/check_orders.py        # Basic order status
python utils/check_alpaca_orders.py # Detailed order information
```
Shows:
- Pending orders
- Order status
- Execution details

## Management Scripts

### `start_sync.sh`
Start the portfolio sync service with auto-restart:
```bash
./utils/start_sync.sh
```
Features:
- Auto-restarts on crashes
- Internet connectivity checks
- Error handling
- Press Ctrl+C to stop

### `cancel_test_orders.py`
Clean up test orders:
```bash
python utils/cancel_test_orders.py
```
- Identifies test orders (1-share SPY orders)
- Safely cancels them

### `quick_cancel.py`
Cancel specific orders:
```bash
python utils/quick_cancel.py
```
- Cancels orders by ID
- Use with caution

## Usage Notes

1. All scripts require:
   - Python virtual environment
   - Valid API keys in `.env`
   - Database configuration

2. Best practices:
   - Run monitoring scripts before and after trading sessions
   - Keep sync service running during market hours
   - Check logs regularly

3. Error handling:
   - Scripts include retry logic
   - Check logs for issues
   - Use `--help` for options
