#!/usr/bin/env python3
"""
Test script for Tax Loss Harvesting functionality
Tests the new tax loss harvesting endpoints and service
"""

import sys
import requests
import json
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000"
TEST_USER_TOKEN = "usr_348784c4-6f83-4857-b7dc-f5132a38dfee"  # Demo user token

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def test_health_check():
    """Test if the API is running"""
    print_header("Health Check")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"API is healthy: {data.get('status')}")
            print_info(f"Services: {data.get('services', {})}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API. Is the backend running?")
        print_info("Start the backend with: python start_web_api.py")
        return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False

def test_analyze_tax_loss_harvesting():
    """Test the tax loss harvesting analysis endpoint"""
    print_header("Test: Analyze Tax Loss Harvesting")
    
    try:
        headers = {
            "Authorization": f"Bearer {TEST_USER_TOKEN}",
            "Content-Type": "application/json"
        }
        
        print_info("Calling GET /tax-loss-harvesting/analyze...")
        response = requests.get(
            f"{API_BASE}/tax-loss-harvesting/analyze",
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Analysis completed successfully!")
            
            summary = data.get("summary", {})
            opportunities = data.get("opportunities", [])
            
            print(f"\n📊 Summary:")
            print(f"   Opportunities found: {summary.get('opportunities_count', 0)}")
            print(f"   Total potential savings: ${summary.get('total_potential_savings', 0):,.2f}")
            print(f"   Total realized loss: ${summary.get('total_realized_loss', 0):,.2f}")
            print(f"   Average loss %: {summary.get('average_loss_percentage', 0):.2f}%")
            print(f"   Wash sale risks: {summary.get('wash_sale_risks', 0)}")
            
            if opportunities:
                print(f"\n💰 Opportunities:")
                for i, opp in enumerate(opportunities[:5], 1):  # Show first 5
                    print(f"\n   {i}. {opp.get('symbol')} - {opp.get('asset_name', 'N/A')}")
                    print(f"      Loss: ${opp.get('unrealized_loss', 0):,.2f} ({opp.get('loss_percentage', 0):.2f}%)")
                    print(f"      Tax Savings: ${opp.get('potential_tax_savings', 0):,.2f}")
                    print(f"      Alternatives: {', '.join(opp.get('alternative_symbols', []))}")
                    if opp.get('wash_sale_risk'):
                        print(f"      ⚠️  Wash sale risk detected!")
            else:
                print_info("No tax-loss harvesting opportunities found.")
                print_info("This could mean:")
                print_info("  - Portfolio has no positions with losses")
                print_info("  - Losses are below minimum thresholds ($500 and 5%)")
                print_info("  - Portfolio is empty or not configured")
            
            return True, data
        elif response.status_code == 404:
            print_error("Portfolio not found")
            print_info("User may not have a portfolio set up yet")
            return False, None
        else:
            print_error(f"Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except requests.exceptions.Timeout:
        print_error("Request timed out")
        return False, None
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_execute_tax_loss_harvest(symbol=None):
    """Test the tax loss harvesting execution endpoint"""
    print_header("Test: Execute Tax Loss Harvesting")
    
    if not symbol:
        print_info("Skipping execution test (no symbol provided)")
        print_info("To test execution, provide a symbol with a loss opportunity")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {TEST_USER_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "symbol": symbol,
            "reinvest": True
        }
        
        print_info(f"Calling POST /tax-loss-harvesting/execute for {symbol}...")
        print_warning("⚠️  This will execute a REAL trade! Use paper trading account.")
        
        # Ask for confirmation in interactive mode
        if sys.stdin.isatty():
            confirm = input("\nContinue with execution? (yes/no): ").lower()
            if confirm != 'yes':
                print_info("Execution test skipped")
                return False
        
        response = requests.post(
            f"{API_BASE}/tax-loss-harvesting/execute",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Tax-loss harvest executed successfully!")
            print(f"\n📊 Results:")
            print(f"   Tax Savings: ${data.get('tax_savings', 0):,.2f}")
            print(f"   Realized Loss: ${data.get('realized_loss', 0):,.2f}")
            if data.get('sell_order'):
                print(f"   Sell Order: {data.get('sell_order', {}).get('order_id', 'N/A')}")
            if data.get('buy_order'):
                print(f"   Buy Order: {data.get('buy_order', {}).get('order_id', 'N/A')}")
            if data.get('alternative_symbol'):
                print(f"   Alternative: {data.get('alternative_symbol')}")
            return True
        else:
            print_error(f"Execution failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service_directly():
    """Test the tax loss harvesting service directly (without API)"""
    print_header("Test: Direct Service Test")
    
    try:
        print_info("Importing tax loss harvesting service...")
        from myfalconadvisor.tools.tax_loss_harvesting_service import tax_loss_harvesting_service
        print_success("Service imported successfully")
        
        print_info("Testing service initialization...")
        print(f"   Min loss threshold: ${tax_loss_harvesting_service.min_loss_threshold}")
        print(f"   Min loss %: {tax_loss_harvesting_service.min_loss_percentage * 100}%")
        print(f"   Tax rate: {tax_loss_harvesting_service.tax_rate * 100}%")
        print(f"   Wash sale window: {tax_loss_harvesting_service.wash_sale_window_days} days")
        
        print_success("Service is properly initialized")
        return True
        
    except ImportError as e:
        print_error(f"Failed to import service: {e}")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  Tax Loss Harvesting Test Suite")
    print("=" * 60)
    print(f"API Base URL: {API_BASE}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "health_check": False,
        "service_test": False,
        "analyze_endpoint": False,
        "execute_endpoint": False
    }
    
    # Test 1: Health check
    results["health_check"] = test_health_check()
    if not results["health_check"]:
        print("\n⚠️  Backend is not running. Please start it first.")
        print("   Run: python start_web_api.py")
        return
    
    # Test 2: Direct service test
    results["service_test"] = test_service_directly()
    
    # Test 3: Analyze endpoint
    success, data = test_analyze_tax_loss_harvesting()
    results["analyze_endpoint"] = success
    
    # Test 4: Execute endpoint (only if we have opportunities)
    if success and data:
        opportunities = data.get("opportunities", [])
        if opportunities:
            first_symbol = opportunities[0].get("symbol")
            if first_symbol:
                print(f"\n💡 Found opportunity for {first_symbol}")
                print_info("You can test execution with this symbol")
                # Uncomment to actually execute (be careful!)
                # results["execute_endpoint"] = test_execute_tax_loss_harvest(first_symbol)
    
    # Summary
    print_header("Test Summary")
    print(f"Health Check:        {'✅ PASS' if results['health_check'] else '❌ FAIL'}")
    print(f"Service Import:      {'✅ PASS' if results['service_test'] else '❌ FAIL'}")
    print(f"Analyze Endpoint:    {'✅ PASS' if results['analyze_endpoint'] else '❌ FAIL'}")
    print(f"Execute Endpoint:    {'⏭️  SKIP' if not results.get('execute_endpoint') else ('✅ PASS' if results['execute_endpoint'] else '❌ FAIL')}")
    
    all_passed = all([
        results["health_check"],
        results["service_test"],
        results["analyze_endpoint"]
    ])
    
    if all_passed:
        print("\n🎉 All critical tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()

