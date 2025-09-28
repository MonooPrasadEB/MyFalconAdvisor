from alpaca.trading.client import TradingClient
import os
from pathlib import Path

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

def check_orders():
    load_env()
    
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    
    if not api_key or not secret_key:
        print("API keys not found in .env file")
        print("Please ensure ALPACA_API_KEY and ALPACA_SECRET_KEY are set")
        return
        
    client = TradingClient(api_key, secret_key, paper=True)
    
    try:
        orders = client.get_orders()
        
        print("\n=== PENDING ALPACA ORDERS ===")
        if not orders:
            print("No pending orders found")
            return
            
        print(f"Found {len(orders)} pending orders:")
        for order in orders:
            print(f"\nSymbol: {order.symbol}")
            print(f"Side: {order.side}")
            print(f"Quantity: {order.qty}")
            print(f"Type: {order.type}")
            print(f"Status: {order.status}")
            print(f"Submitted: {order.submitted_at}")
            if hasattr(order, "limit_price") and order.limit_price:
                print(f"Limit Price: ${order.limit_price}")
                
    except Exception as e:
        print(f"Error checking orders: {e}")

if __name__ == "__main__":
    check_orders()