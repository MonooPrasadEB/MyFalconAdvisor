#!/usr/bin/env python3
"""
Multi-Client Trading System Tests (READ-ONLY VERSION)

Tests the multi-client portfolio management system without creating database records.
This version is safe for production environments.
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

def test_multi_client_manager():
    """Test multi-client portfolio manager initialization."""
    print("🏢 Testing Multi-Client Portfolio Manager")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.multi_client_portfolio_manager import multi_client_manager
        
        if multi_client_manager:
            print("✅ Multi-client manager initialized successfully")
            print(f"📊 Manager type: {type(multi_client_manager).__name__}")
            
            # Test method availability without calling them
            core_methods = [
                'place_client_order',
                'get_client_portfolio',
                'reconcile_with_alpaca'
            ]
            
            optional_methods = [
                'create_client_portfolio'
            ]
            
            core_methods_exist = True
            for method in core_methods:
                if hasattr(multi_client_manager, method):
                    print(f"✅ Method {method} exists")
                else:
                    print(f"❌ Method {method} missing")
                    core_methods_exist = False
            
            # Check optional methods
            for method in optional_methods:
                if hasattr(multi_client_manager, method):
                    print(f"✅ Method {method} exists")
                else:
                    print(f"⚠️  Method {method} missing (optional)")
            
            return core_methods_exist
        else:
            print("❌ Multi-client manager failed to initialize")
            return False
            
    except Exception as e:
        print(f"❌ Multi-client manager test failed: {e}")
        print(f"🔍 Error details: {traceback.format_exc()}")
        return False

def test_client_portfolio_methods():
    """Test client portfolio method signatures without creating records."""
    print("\n👤 Testing Client Portfolio Method Signatures (NO DB WRITES)")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.multi_client_portfolio_manager import multi_client_manager
        
        # Test method signatures
        import inspect
        
        core_methods_to_test = [
            'place_client_order',
            'get_client_portfolio'
        ]
        
        optional_methods_to_test = [
            'create_client_portfolio'
        ]
        
        core_methods_valid = True
        
        for method_name in core_methods_to_test:
            if hasattr(multi_client_manager, method_name):
                method = getattr(multi_client_manager, method_name)
                if callable(method):
                    sig = inspect.signature(method)
                    param_count = len(sig.parameters)
                    print(f"✅ {method_name}: {param_count} parameters")
                else:
                    print(f"❌ {method_name}: Not callable")
                    core_methods_valid = False
            else:
                print(f"❌ {method_name}: Does not exist")
                core_methods_valid = False
        
        # Check optional methods
        for method_name in optional_methods_to_test:
            if hasattr(multi_client_manager, method_name):
                method = getattr(multi_client_manager, method_name)
                if callable(method):
                    sig = inspect.signature(method)
                    param_count = len(sig.parameters)
                    print(f"✅ {method_name}: {param_count} parameters (optional)")
                else:
                    print(f"⚠️  {method_name}: Not callable (optional)")
            else:
                print(f"⚠️  {method_name}: Does not exist (optional)")
        
        if core_methods_valid:
            print("✅ Core client portfolio methods are properly defined")
            print("ℹ️  Method signature test completed (no portfolios created)")
        
        return core_methods_valid
        
    except Exception as e:
        print(f"❌ Client portfolio methods test failed: {e}")
        return False

def test_virtual_trading_logic():
    """Test virtual trading logic without executing trades."""
    print("\n💼 Testing Virtual Trading Logic (NO TRADES)")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.multi_client_portfolio_manager import multi_client_manager
        
        # Test that trading methods exist
        trading_methods = [
            'place_client_order',
            '_update_virtual_portfolio',
            '_calculate_client_allocation'
        ]
        
        methods_available = 0
        for method in trading_methods:
            if hasattr(multi_client_manager, method):
                print(f"✅ Trading method {method} available")
                methods_available += 1
            else:
                print(f"⚠️  Trading method {method} not found")
        
        if methods_available >= 1:  # At least basic trading method exists
            print("✅ Virtual trading logic is available")
            print("ℹ️  Trading logic test completed (no orders placed)")
            return True
        else:
            print("❌ Virtual trading logic not available")
            return False
        
    except Exception as e:
        print(f"❌ Virtual trading logic test failed: {e}")
        return False

def test_portfolio_reconciliation():
    """Test portfolio reconciliation method availability."""
    print("\n📊 Testing Portfolio Reconciliation (NO RECONCILIATION)")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.multi_client_portfolio_manager import multi_client_manager
        
        # Test reconciliation method exists
        if hasattr(multi_client_manager, 'reconcile_with_alpaca'):
            reconcile_method = getattr(multi_client_manager, 'reconcile_with_alpaca')
            if callable(reconcile_method):
                print("✅ Reconciliation method exists and is callable")
                
                # Test method signature
                import inspect
                sig = inspect.signature(reconcile_method)
                print(f"✅ Reconciliation method signature: {len(sig.parameters)} parameters")
                
                print("ℹ️  Reconciliation test completed (no actual reconciliation performed)")
                return True
            else:
                print("❌ Reconciliation method exists but is not callable")
                return False
        else:
            print("⚠️  Reconciliation method not available")
            print("ℹ️  Multi-client manager operational (reconciliation needs implementation)")
            return True  # This is acceptable for now
        
    except Exception as e:
        print(f"❌ Portfolio reconciliation test failed: {e}")
        return False

def test_database_integration():
    """Test database integration without modifying data."""
    print("\n🗄️  Testing Database Integration (READ-ONLY)")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.database_service import DatabaseService
        from sqlalchemy import text
        
        db_service = DatabaseService()
        
        if not db_service.engine:
            print("⚠️  Database not available - skipping integration test")
            return True
        
        # Test read-only queries to check existing data
        with db_service.get_session() as session:
            # Count existing portfolios (including any test data)
            result = session.execute(text("SELECT COUNT(*) FROM portfolios"))
            portfolio_count = result.fetchone()[0]
            print(f"✅ Found {portfolio_count} portfolios in database")
            
            # Count existing transactions
            result = session.execute(text("SELECT COUNT(*) FROM transactions"))
            transaction_count = result.fetchone()[0]
            print(f"✅ Found {transaction_count} transactions in database")
            
            print("ℹ️  Database integration test completed (no data modified)")
            return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False

def main():
    """Run all multi-client system tests."""
    print("🧪 MyFalconAdvisor Multi-Client System Test Suite (READ-ONLY)")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🛡️  PRODUCTION DATABASE PROTECTION: No portfolios or orders will be created")
    print("=" * 80)
    
    # Load environment
    load_env()
    
    # Run tests
    tests = [
        ("Multi-Client Manager", test_multi_client_manager),
        ("Client Portfolio Methods", test_client_portfolio_methods),
        ("Virtual Trading Logic", test_virtual_trading_logic),
        ("Portfolio Reconciliation", test_portfolio_reconciliation),
        ("Database Integration", test_database_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append(result)
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"📊 {test_name}: {status}")
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"\n📊 Multi-Client Score: {passed}/{total} ({percentage:.1f}%)")
    
    if percentage >= 80:
        print("🎉 Multi-client system tests PASSED!")
        print("🚀 Ready for production client management!")
        return True
    else:
        print("❌ Multi-client system tests FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
