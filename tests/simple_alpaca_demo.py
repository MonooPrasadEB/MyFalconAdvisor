#!/usr/bin/env python3
"""
Simple Alpaca Integration Demo

This script demonstrates basic Alpaca functionality without complex dependencies.
Perfect for initial testing with your API keys.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def test_basic_alpaca_connection():
    """Test basic Alpaca connection with minimal dependencies."""
    print("🔑 Testing Basic Alpaca Connection")
    print("=" * 50)
    
    # Check if API keys are set
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    
    if not api_key or not secret_key:
        print("❌ Alpaca API keys not found in environment variables")
        print("\n📋 To test with real Alpaca API:")
        print("1. Create a .env file with your Alpaca credentials:")
        print("   ALPACA_API_KEY=your_api_key_here")
        print("   ALPACA_SECRET_KEY=your_secret_key_here")
        print("2. Run: source .env (or restart your shell)")
        print("3. Run this script again")
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
        
        # Get positions
        positions = trading_client.get_all_positions()
        print(f"📋 Current Positions: {len(positions)}")
        
        for pos in positions[:5]:  # Show first 5 positions
            print(f"  • {pos.symbol}: {float(pos.qty)} shares @ ${float(pos.current_price):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_market_data():
    """Test market data retrieval."""
    print("\n📈 Testing Market Data")
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
        symbols = ["AAPL", "MSFT", "GOOGL"]
        
        for symbol in symbols:
            try:
                request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
                quotes = data_client.get_stock_latest_quote(request)
                
                if symbol in quotes:
                    quote = quotes[symbol]
                    print(f"✅ {symbol}: Bid ${float(quote.bid_price):.2f} | Ask ${float(quote.ask_price):.2f}")
                else:
                    print(f"⚠️  {symbol}: No quote data available")
                    
            except Exception as e:
                print(f"❌ {symbol}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        return False

def test_simple_order():
    """Test placing a simple paper trading order."""
    print("\n📝 Testing Order Placement")
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
        print("💡 This might be expected if markets are closed or if you have insufficient buying power")
        return False

def main():
    """Run all basic tests."""
    print("🧪 Simple Alpaca Integration Demo")
    print("=" * 60)
    
    # Load environment variables if .env exists
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print(f"📁 Loading environment from {env_file}")
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    try:
                        key, value = line.strip().split("=", 1)
                        os.environ[key] = value
                    except ValueError:
                        continue
    
    tests = [
        ("Basic Connection", test_basic_alpaca_connection),
        ("Market Data", test_market_data),
        ("Order Placement", test_simple_order)
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
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your Alpaca integration is working!")
    else:
        print("\n💡 Next Steps:")
        print("1. Make sure you have valid Alpaca API keys")
        print("2. Ensure you're using paper trading keys")
        print("3. Check that markets are open for order testing")
        print("4. Verify your account has sufficient buying power")

if __name__ == "__main__":
    main()
