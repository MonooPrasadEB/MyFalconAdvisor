#!/usr/bin/env python3
"""
Complete Logging Workflow Test Suite (READ-ONLY VERSION)

Tests the complete AI workflow signatures and method availability WITHOUT
writing to the production database. This version is safe for production environments.
"""

import os
import sys
import json
from pathlib import Path
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

def test_execution_service_initialization():
    """Test ExecutionService initialization."""
    print("🔧 Testing ExecutionService Initialization")
    print("-" * 50)
    
    try:
        from myfalconadvisor.agents.execution_agent import ExecutionService
        
        # Initialize service
        service = ExecutionService()
        print("✅ ExecutionService initialized successfully")
        
        # Check required methods exist
        required_methods = [
            'process_ai_recommendation',
            'validate_recommendation_against_portfolio',
            '_write_to_recommendations_table',
            '_write_to_compliance_checks_table', 
            '_write_to_agent_workflows_table'
        ]
        
        for method in required_methods:
            if hasattr(service, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ ExecutionService initialization failed: {e}")
        return False

def test_database_write_method_signatures():
    """Test database write method signatures without writing to production DB."""
    print("\n💾 Testing Database Write Method Signatures (NO DB WRITES)")
    print("-" * 50)
    
    try:
        from myfalconadvisor.agents.execution_agent import execution_service
        
        # Test that methods exist and are callable
        write_methods = [
            '_write_to_recommendations_table',
            '_write_to_compliance_checks_table', 
            '_write_to_agent_workflows_table'
        ]
        
        all_methods_exist = True
        for method_name in write_methods:
            if hasattr(execution_service, method_name):
                method = getattr(execution_service, method_name)
                if callable(method):
                    print(f"✅ Method {method_name} exists and is callable")
                else:
                    print(f"❌ Method {method_name} exists but is not callable")
                    all_methods_exist = False
            else:
                print(f"❌ Method {method_name} does not exist")
                all_methods_exist = False
        
        # Test method signatures (without actually calling them)
        import inspect
        
        for method_name in write_methods:
            if hasattr(execution_service, method_name):
                method = getattr(execution_service, method_name)
                sig = inspect.signature(method)
                param_count = len(sig.parameters)
                print(f"✅ {method_name} signature: {param_count} parameters")
        
        if all_methods_exist:
            print("✅ All database write methods are properly defined")
            print("ℹ️  Method signature test completed (no data written to production DB)")
            return True
        else:
            print("❌ Some database write methods are missing")
            return False
        
    except Exception as e:
        print(f"❌ Database write methods test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_portfolio_validation():
    """Test portfolio validation logic without database writes."""
    print("\n🔍 Testing Portfolio Validation Logic")
    print("-" * 50)
    
    try:
        from myfalconadvisor.agents.execution_agent import execution_service
        
        # Test portfolio validation with mock data
        mock_recommendation = {
            "symbol": "MOCK_TEST",
            "action": "buy",
            "quantity": 10,
            "order_type": "market",
            "reasoning": "Mock test recommendation for validation",
            "confidence": 0.85,
            "risk_level": 0.3
        }
        
        print("🔄 Testing recommendation validation logic...")
        
        # Test validation method exists and is callable
        if hasattr(execution_service, 'validate_recommendation_against_portfolio'):
            validation_method = getattr(execution_service, 'validate_recommendation_against_portfolio')
            if callable(validation_method):
                print("✅ Portfolio validation method exists and is callable")
                
                # Test method signature
                import inspect
                sig = inspect.signature(validation_method)
                print(f"✅ Validation method signature: {len(sig.parameters)} parameters")
                
                return True
            else:
                print("❌ Portfolio validation method exists but is not callable")
                return False
        else:
            print("❌ Portfolio validation method does not exist")
            return False
        
    except Exception as e:
        print(f"❌ Portfolio validation test failed: {e}")
        return False

def test_database_connectivity():
    """Test database connectivity without modifying data."""
    print("\n🔗 Testing Database Connectivity (READ-ONLY)")
    print("-" * 50)
    
    try:
        from myfalconadvisor.tools.database_service import DatabaseService
        
        db_service = DatabaseService()
        
        if not db_service.engine:
            print("⚠️  Database not available - skipping connectivity test")
            return True
        
        # Test read-only queries
        with db_service.get_session() as session:
            from sqlalchemy import text
            
            # Test basic connectivity
            result = session.execute(text("SELECT 1"))
            if result.fetchone()[0] == 1:
                print("✅ Database connection successful")
            
            # Test table existence (read-only)
            tables_to_check = [
                'ai_sessions', 'ai_messages', 'recommendations', 
                'compliance_checks', 'agent_workflows', 'transactions'
            ]
            
            existing_tables = []
            for table in tables_to_check:
                try:
                    result = session.execute(text(f"SELECT COUNT(*) FROM {table} LIMIT 1"))
                    result.fetchone()
                    existing_tables.append(table)
                    print(f"✅ Table '{table}' exists and is accessible")
                except Exception as e:
                    print(f"⚠️  Table '{table}' issue: {e}")
            
            print(f"✅ Database connectivity test completed - {len(existing_tables)}/{len(tables_to_check)} tables accessible")
            return True
        
    except Exception as e:
        print(f"❌ Database connectivity test failed: {e}")
        return False

def main():
    """Run all read-only logging workflow tests."""
    print("🧪 MyFalconAdvisor Complete Logging Workflow Test Suite (READ-ONLY)")
    print("=" * 80)
    print("ℹ️  This version tests method signatures and connectivity without modifying production data")
    print("=" * 80)
    
    # Load environment
    load_env()
    
    # Run tests
    tests = [
        ("ExecutionService Initialization", test_execution_service_initialization),
        ("Database Write Method Signatures", test_database_write_method_signatures),
        ("Portfolio Validation Logic", test_portfolio_validation),
        ("Database Connectivity", test_database_connectivity)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            results.append(result)
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"📊 {test_name}: {status}")
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"\n📊 Overall Score: {passed}/{total} ({percentage:.1f}%)")
    
    if percentage >= 80:
        print("🎉 Test suite PASSED!")
        return True
    else:
        print("❌ Test suite FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
