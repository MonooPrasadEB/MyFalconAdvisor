#!/usr/bin/env python3
"""
Alpaca Trading Integration Tests

Tests Alpaca API connectivity, market data retrieval, and order placement functionality.
"""

import os
import sys
from pathlib import Path
import traceback
from datetime import datetime

# Add the parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    try:
                        key, value = line.strip().split("=", 1)
                        os.environ[key] = value
                    except ValueError:
                        continue

def test_alpaca_connection():
    """Test basic Alpaca API connection."""
    print("🔑 Testing Alpaca API Connection")
    print("=" * 50)
    
    # Check if API keys are set
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    
    if not api_key or not secret_key:
        print("❌ Alpaca API keys not found in environment variables")
        return False
    
    try:
        from alpaca.trading.client import TradingClient
        
        # Initialize client
        trading_client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=True  # Always use paper trading for testing
        )
        
        # Test connection by getting account info
        account = trading_client.get_account()
        
        print("✅ Successfully connected to Alpaca!")
        print(f"📊 Account ID: {account.id}")
        print(f"💰 Buying Power: ${float(account.buying_power):,.2f}")
        print(f"💼 Portfolio Value: ${float(account.portfolio_value):,.2f}")
        print(f"💵 Cash: ${float(account.cash):,.2f}")
        print(f"📈 Day Trade Count: {account.daytrade_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_alpaca_market_data():
    """Test market data retrieval."""
    print("\n📈 Testing Alpaca Market Data")
    print("=" * 50)
    
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockLatestQuoteRequest
        
        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")
        
        if not api_key or not secret_key:
            print("❌ API keys not available")
            return False
        
        data_client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)
        
        # Test symbols
        symbols = ["AAPL", "MSFT", "SPY"]
        successful_quotes = 0
        
        for symbol in symbols:
            try:
                request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
                quotes = data_client.get_stock_latest_quote(request)
                
                if symbol in quotes:
                    quote = quotes[symbol]
                    print(f"✅ {symbol}: Bid ${float(quote.bid_price):.2f} | Ask ${float(quote.ask_price):.2f}")
                    successful_quotes += 1
                else:
                    print(f"⚠️  {symbol}: No quote data available")
                    
            except Exception as e:
                print(f"❌ {symbol}: Error - {e}")
        
        return successful_quotes > 0
        
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        return False

def test_alpaca_order_placement():
    """Test order placement functionality."""
    print("\n📝 Testing Alpaca Order Placement")
    print("=" * 50)
    
    try:
        from alpaca.trading.client import TradingClient
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce
        
        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")
        
        if not api_key or not secret_key:
            print("❌ API keys not available")
            return False
        
        trading_client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=True
        )
        
        # Create a small test order
        order_request = MarketOrderRequest(
            symbol="SPY",
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        
        print("🔄 Placing test order for 1 share of SPY...")
        order = trading_client.submit_order(order_request)
        
        print(f"✅ Order placed successfully!")
        print(f"📋 Order ID: {order.id}")
        print(f"📊 Symbol: {order.symbol}")
        print(f"📈 Side: {order.side}")
        print(f"📦 Quantity: {order.qty}")
        print(f"⏰ Status: {order.status}")
        print(f"🕐 Submitted: {order.submitted_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ Order placement failed: {e}")
        return False

def test_alpaca_service_integration():
    """Test our custom Alpaca service integration."""
    print("\n🛠️  Testing Alpaca Service Integration")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service
        
        # Test service initialization
        if alpaca_trading_service:
            print("✅ Alpaca service initialized successfully")
        else:
            print("❌ Alpaca service failed to initialize")
            return False
        
        # Test connection
        connection_test = alpaca_trading_service.test_connection()
        if connection_test.get('success', False):
            print("✅ Service connection test passed")
            account_info = connection_test.get('account_info', {})
            print(f"📊 Account Value: ${account_info.get('portfolio_value', 'N/A')}")
        else:
            print(f"❌ Service connection test failed: {connection_test.get('error', 'Unknown error')}")
            return False
        
        # Test market data
        try:
            price_data = alpaca_trading_service.get_current_price("AAPL")
            if price_data and price_data > 0:
                print(f"✅ Market data retrieval successful: AAPL @ ${price_data:.2f}")
            else:
                print("⚠️  Market data retrieval returned no data")
        except Exception as e:
            print(f"⚠️  Market data test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Alpaca service integration test failed: {e}")
        return False

def main():
    """Run all Alpaca integration tests."""
    print("🧪 MyFalconAdvisor Alpaca Integration Test Suite")
    print("=" * 70)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment
    load_env()
    
    # Show configuration
    api_key = os.getenv("ALPACA_API_KEY", "Not Set")
    base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    print(f"🔑 API Key: {api_key[:8]}..." if len(api_key) > 8 else "Not Set")
    print(f"🌐 Base URL: {base_url}")
    print(f"📝 Paper Trading: {os.getenv('ALPACA_PAPER_TRADING', 'true')}")
    
    tests = [
        ("Alpaca Connection", test_alpaca_connection),
        ("Market Data", test_alpaca_market_data),
        ("Order Placement", test_alpaca_order_placement),
        ("Service Integration", test_alpaca_service_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*70}")
    print("🏁 ALPACA INTEGRATION TEST RESULTS")
    print(f"{'='*70}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n🎯 Alpaca Score: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 Alpaca integration is fully operational!")
    elif passed >= total * 0.7:
        print("👍 Alpaca integration is mostly working. Check failed tests above.")
    else:
        print("⚠️  Alpaca integration needs attention. Check API keys and connectivity.")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Recommendations
    if passed < total:
        print(f"\n💡 Troubleshooting:")
        print("1. Verify ALPACA_API_KEY and ALPACA_SECRET_KEY in .env file")
        print("2. Ensure you're using paper trading keys (not live trading)")
        print("3. Check that your Alpaca account is active and funded")
        print("4. Verify network connectivity to Alpaca servers")

if __name__ == "__main__":
    main()
