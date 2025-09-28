import os
import sys
from pathlib import Path

# Add the parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from myfalconadvisor.tools.database_service import DatabaseService

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

def check_db_state():
    load_env()
    db = DatabaseService()
    
    print("\n=== DATABASE STATE ===")
    
    # Check transactions
    transactions = db.get_recent_transactions()
    print(f"\nTransactions: {len(transactions)} records")
    for tx in transactions:
        print(f"\nSymbol: {tx['symbol']}")
        print(f"Side: {tx['transaction_type']}")
        print(f"Quantity: {tx['quantity']}")
        print(f"Status: {tx['status']}")
        print(f"Created: {tx['created_at']}")
        if tx.get('broker_reference'):
            print(f"Broker Ref: {tx['broker_reference']}")
    
    # Check portfolios
    main_user_id = "7baa7c7c-e0b0-4e4f-8e4d-1d1c8a92e7b8"  # Main test user
    portfolios = db.get_user_portfolios(main_user_id)
    print(f"\nPortfolios for main user: {len(portfolios)} records")
    for p in portfolios:
        print(f"\nPortfolio ID: {p['id']}")
        print(f"Total Value: ${float(p['total_value']):,.2f}")
        print(f"Cash Balance: ${float(p['cash_balance']):,.2f}")
        print(f"Created: {p['created_at']}")
        print(f"Updated: {p['updated_at']}")

if __name__ == "__main__":
    check_db_state()