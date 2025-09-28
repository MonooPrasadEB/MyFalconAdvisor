import os
from pathlib import Path
from alpaca.trading.client import TradingClient

def load_env():
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    try:
                        key, value = line.strip().split("=", 1)
                        os.environ[key] = value
                    except ValueError:
                        continue

def cancel_order():
    load_env()
    
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    
    if not api_key or not secret_key:
        print("API keys not found")
        return
        
    client = TradingClient(api_key, secret_key, paper=True)
    
    try:
        client.cancel_order_by_id("687e8362-aa2d-4571-8a3a-96b5699878fb")
        print("Order cancelled successfully")
    except Exception as e:
        print(f"Error cancelling order: {e}")

if __name__ == "__main__":
    cancel_order()