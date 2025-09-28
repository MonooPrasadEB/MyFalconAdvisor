"""Check pending Alpaca orders."""

import os
import sys
from pathlib import Path

# Add the parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service
from alpaca.trading.requests import GetOrdersRequest

def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print(f"Loading environment from {env_file}")
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    try:
                        key, value = line.strip().split("=", 1)
                        os.environ[key] = value.strip('"').strip("'")
                    except ValueError:
                        continue
    else:
        print(f"Error: .env file not found at {env_file}")

def check_pending_orders():
    """Check and display all pending Alpaca orders."""
    load_env()
    
    print("\n=== PENDING ALPACA ORDERS ===")
    
    try:
        orders = alpaca_trading_service.trading_client.get_orders(
            GetOrdersRequest(status='open')
        )
        
        if not orders:
            print("\nNo pending orders found.")
            return
            
        print(f"\nFound {len(orders)} pending orders:")
        for order in orders:
            print(f"\nSymbol: {order.symbol}")
            print(f"Order Type: {order.type}")
            print(f"Side: {order.side}")
            print(f"Quantity: {order.qty}")
            print(f"Status: {order.status}")
            print(f"Created At: {order.created_at}")
            if order.limit_price:
                print(f"Limit Price: ${order.limit_price}")
            if order.notional:
                print(f"Notional Value: ${order.notional}")
            print(f"Order ID: {order.id}")
            
    except Exception as e:
        print(f"Error checking orders: {e}")

if __name__ == "__main__":
    check_pending_orders()