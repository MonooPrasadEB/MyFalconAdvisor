"""
Test Alpaca integration using mock mode only.
NO REAL ORDERS SHOULD BE PLACED BY TESTS.
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

def test_alpaca_market_data():
    """Test market data functionality."""
    print("\n📊 Testing Market Data")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service
        
        # Force mock mode for tests
        alpaca_trading_service.mock_mode = True
        
        # Test getting market data
        spy_data = alpaca_trading_service.get_market_data("SPY")
        
        # In mock mode, we expect the error "Market data not available in mock mode"
        if spy_data.get("error") == "Market data not available in mock mode":
            print("✅ Mock mode correctly prevents market data access")
            return True
        else:
            print(f"⚠️  Unexpected response in mock mode: {spy_data}")
            return False
            
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        print(f"🔍 Error details: {traceback.format_exc()}")
        return False

def test_alpaca_order_placement():
    """Test order placement functionality using mock mode."""
    print("\n📝 Testing Alpaca Order Placement (MOCK MODE)")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service
        
        # Force mock mode for tests
        alpaca_trading_service.mock_mode = True
        
        # Place a test order using our service (will be mocked)
        order_result = alpaca_trading_service.place_order(
            symbol="SPY",
            side="buy",
            quantity=1,
            order_type="market"
        )
        
        if order_result.get("success"):
            print("✅ Mock order placed successfully")
            print(f"📋 Order ID: {order_result.get('order_id')}")
            print(f"📊 Symbol: {order_result.get('symbol')}")
            print(f"📈 Side: {order_result.get('side')}")
            print(f"📦 Quantity: {order_result.get('quantity')}")
            print(f"⏰ Status: {order_result.get('status')}")
            print(f"💡 Note: {order_result.get('note')}")
            
            # Verify mock order properties
            if (order_result.get("status") == "mock_pending" and
                "mock" in order_result.get("note", "").lower()):
                return True
            else:
                print("⚠️  Order response missing mock indicators")
                return False
        else:
            print(f"⚠️  Order placement had issues: {order_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Order placement test failed: {e}")
        return False

def test_alpaca_service_integration():
    """Test our custom Alpaca service integration."""
    print("\n🔄 Testing Service Integration")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service
        
        # Force mock mode for tests
        alpaca_trading_service.mock_mode = True
        
        # Test connection
        connection = alpaca_trading_service.test_connection()
        if connection.get("mode") == "mock":
            print("✅ Service correctly reports mock mode")
        else:
            print(f"⚠️  Unexpected mode: {connection.get('mode')}")
            return False
            
        # Test getting positions (should return mock data)
        positions = alpaca_trading_service.get_positions()
        if isinstance(positions, dict) and "positions" in positions:
            print("✅ Position retrieval returns mock data")
            print(f"📊 Mock positions: {len(positions['positions'])} positions")
            print(f"💰 Mock total value: ${positions.get('total_market_value', 0):,.2f}")
            return True
        else:
            print(f"⚠️  Position retrieval issues: {positions.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Service integration test failed: {e}")
        return False

def main():
    """Run all Alpaca integration tests."""
    print("🧪 MyFalconAdvisor Alpaca Integration Test Suite")
    print("=" * 70)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("⚠️  RUNNING IN MOCK MODE - NO REAL ORDERS WILL BE PLACED")
    print("=" * 70)
    
    # Load environment
    load_env()
    
    # Show configuration
    api_key = os.getenv("ALPACA_API_KEY", "Not Set")
    base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    print(f"🔑 API Key: {api_key[:8]}..." if len(api_key) > 8 else "Not Set")
    print(f"🌐 Base URL: {base_url}")
    print(f"📝 Paper Trading: {os.getenv('ALPACA_PAPER_TRADING', 'true')}")
    
    tests = [
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
        print("🎉 Mock integration tests passed!")
    elif passed >= total * 0.7:
        print("👍 Most mock tests passed. Check failures above.")
    else:
        print("⚠️  Multiple mock tests failed. Check implementation.")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()