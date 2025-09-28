"""
Test Alpaca integration using mock mode only.
NO REAL ORDERS SHOULD BE PLACED BY TESTS.
"""

import os
import traceback
from datetime import datetime, timedelta

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
        
        if not spy_data.get("error"):
            print("✅ Market data retrieved successfully")
            print(f"📈 Latest SPY price: ${spy_data.get('latest_price', 'N/A')}")
            return True
        else:
            print(f"⚠️  Market data error: {spy_data.get('error')}")
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
            return True
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
        if connection.get("connected"):
            print("✅ Service connection test passed")
        else:
            print(f"⚠️  Connection issues: {connection.get('error')}")
            return False
            
        # Test getting positions (should return mock data)
        positions = alpaca_trading_service.get_positions()
        if not positions.get("error"):
            print("✅ Position retrieval test passed")
        else:
            print(f"⚠️  Position retrieval issues: {positions.get('error')}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Service integration test failed: {e}")
        return False

def main():
    """Run all Alpaca integration tests."""
    tests = [
        test_alpaca_market_data,
        test_alpaca_order_placement,
        test_alpaca_service_integration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    total = len(results)
    passed = sum(1 for r in results if r)
    
    print("\n=== TEST RESULTS ===")
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    return passed == total

if __name__ == "__main__":
    main()