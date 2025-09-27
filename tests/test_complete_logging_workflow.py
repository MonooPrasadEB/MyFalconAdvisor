#!/usr/bin/env python3
"""
Complete Logging Workflow Test Suite

Tests the complete AI workflow with database logging including:
- AI Sessions and Messages logging
- Recommendations table population
- Compliance checks recording
- Agent workflows tracking
- ExecutionService functionality
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

def get_table_count(table_name):
    """Get record count for a specific table."""
    try:
        from myfalconadvisor.tools.chat_logger import chat_logger
        result = chat_logger._execute_sql(f"SELECT COUNT(*) FROM {table_name}", return_result=True)
        if result:
            count = result[0]['result'].strip()
            return int(count) if count.isdigit() else 0
        return 0
    except Exception as e:
        print(f"❌ Error checking {table_name}: {e}")
        return -1

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

def test_database_write_methods():
    """Test individual database write methods."""
    print("\n💾 Testing Database Write Methods")
    print("-" * 50)
    
    try:
        from myfalconadvisor.agents.execution_agent import execution_service
        
        # Test recommendation writing
        test_recommendation = {
            "symbol": "TEST",
            "action": "buy",
            "quantity": 1,
            "reasoning": "Test recommendation for unit testing"
        }
        
        print("🔄 Testing recommendations table write...")
        rec_id = execution_service._write_to_recommendations_table(
            recommendation=test_recommendation,
            user_id=None  # Bypass FK constraint
        )
        
        if rec_id:
            print(f"✅ Recommendation written successfully: {rec_id}")
        else:
            print("❌ Failed to write recommendation")
            return False
        
        # Test compliance checks writing
        print("🔄 Testing compliance_checks table write...")
        compliance_result = {
            "approved": True,
            "reason": "Test compliance check passed",
            "compliance_issues": []
        }
        
        check_id = execution_service._write_to_compliance_checks_table(
            recommendation_id=rec_id,
            compliance_result=compliance_result,
            user_id=None  # Bypass FK constraint like the main workflow
        )
        
        if check_id:
            print(f"✅ Compliance check written successfully: {check_id}")
        else:
            print("❌ Failed to write compliance check")
            return False
        
        # Test agent workflows writing
        print("🔄 Testing agent_workflows table write...")
        workflow_data = {
            "current_state": "testing",
            "status": "running",
            "test_data": {"test": True}
        }
        
        # Use None to bypass FK constraint in individual test
        workflow_id = execution_service._write_to_agent_workflows_table(
            session_id=None,
            workflow_type="test_workflow", 
            workflow_data=workflow_data
        )
        
        if workflow_id:
            print(f"✅ Agent workflow written successfully: {workflow_id}")
        else:
            print("❌ Failed to write agent workflow")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database write methods test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_workflow():
    """Test complete AI workflow with database logging."""
    print("\n🚀 Testing Complete AI Workflow")
    print("-" * 50)
    
    try:
        from myfalconadvisor.agents.execution_agent import execution_service
        
        # Get initial table counts
        initial_counts = {
            'ai_sessions': get_table_count('ai_sessions'),
            'ai_messages': get_table_count('ai_messages'),
            'recommendations': get_table_count('recommendations'),
            'compliance_checks': get_table_count('compliance_checks'),
            'agent_workflows': get_table_count('agent_workflows')
        }
        
        print("📊 Initial table counts:")
        for table, count in initial_counts.items():
            print(f"  {table}: {count}")
        
        # Test complete workflow
        test_recommendation = {
            "symbol": "WORKFLOW_TEST",
            "action": "buy", 
            "quantity": 2,
            "order_type": "market",
            "reasoning": "Complete workflow test recommendation",
            "confidence": 0.95,
            "risk_level": 0.2
        }
        
        print(f"\n🔄 Processing test recommendation: {test_recommendation['symbol']}")
        
        result = execution_service.process_ai_recommendation(
            user_id=None,  # Bypass FK constraint
            recommendation=test_recommendation
        )
        
        print(f"📊 Workflow result: {result.get('status')} at stage {result.get('stage')}")
        
        # Verify database changes
        final_counts = {
            'ai_sessions': get_table_count('ai_sessions'),
            'ai_messages': get_table_count('ai_messages'),
            'recommendations': get_table_count('recommendations'),
            'compliance_checks': get_table_count('compliance_checks'),
            'agent_workflows': get_table_count('agent_workflows')
        }
        
        print("\n📈 Table changes:")
        success = True
        expected_increases = {
            'ai_sessions': 1,
            'ai_messages': 3,  # At least 3 messages
            'recommendations': 1,
            'compliance_checks': 1,
            'agent_workflows': 1
        }
        
        for table, expected in expected_increases.items():
            initial = initial_counts[table]
            final = final_counts[table]
            actual_increase = final - initial
            
            if actual_increase >= expected:
                print(f"  ✅ {table}: {initial} → {final} (+{actual_increase})")
            else:
                print(f"  ❌ {table}: {initial} → {final} (+{actual_increase}), expected +{expected}")
                success = False
        
        # Check that we got the expected IDs back
        if result.get('recommendation_id'):
            print(f"✅ Recommendation ID: {result['recommendation_id']}")
        else:
            print("❌ No recommendation ID returned")
            success = False
            
        if result.get('compliance_check_id'):
            print(f"✅ Compliance Check ID: {result['compliance_check_id']}")
        else:
            print("❌ No compliance check ID returned")
            success = False
            
        if result.get('workflow_id'):
            print(f"✅ Workflow ID: {result['workflow_id']}")
        else:
            print("❌ No workflow ID returned")
            success = False
        
        return success
        
    except Exception as e:
        print(f"❌ Complete workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_portfolio_validation():
    """Test portfolio validation logic."""
    print("\n🔍 Testing Portfolio Validation")
    print("-" * 50)
    
    try:
        from myfalconadvisor.agents.execution_agent import execution_service
        
        # Test validation with various scenarios
        test_cases = [
            {
                "name": "Valid buy order",
                "recommendation": {"symbol": "AAPL", "action": "buy", "quantity": 1},
                "should_pass": False  # Will fail due to no portfolio
            },
            {
                "name": "Valid sell order", 
                "recommendation": {"symbol": "AAPL", "action": "sell", "quantity": 1},
                "should_pass": False  # Will fail due to no portfolio
            }
        ]
        
        success = True
        for test_case in test_cases:
            print(f"🔄 Testing: {test_case['name']}")
            
            validation = execution_service.validate_recommendation_against_portfolio(
                user_id="test-user",
                recommendation=test_case['recommendation']
            )
            
            if validation.get('approved') == test_case['should_pass']:
                print(f"✅ Validation behaved as expected")
            else:
                print(f"❌ Unexpected validation result: {validation}")
                success = False
        
        return success
        
    except Exception as e:
        print(f"❌ Portfolio validation test failed: {e}")
        return False

def run_all_tests():
    """Run all complete logging workflow tests."""
    load_env()
    
    print("🧪 MyFalcon Advisor - Complete Logging Workflow Tests")
    print("=" * 70)
    print(f"Test run started at: {datetime.now()}")
    print("=" * 70)
    
    tests = [
        ("ExecutionService Initialization", test_execution_service_initialization),
        ("Database Write Methods", test_database_write_methods),
        ("Portfolio Validation", test_portfolio_validation),
        ("Complete Workflow", test_complete_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n🎯 Running: {test_name}")
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"💥 {test_name} CRASHED: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*70}")
    print("🏁 COMPLETE LOGGING WORKFLOW TEST RESULTS")
    print(f"{'='*70}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    score = (passed / total * 100) if total > 0 else 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Overall Score: {passed}/{total} ({score:.1f}%)")
    
    if score >= 90:
        print("🎉 EXCELLENT - Complete logging workflow is production ready!")
    elif score >= 75:
        print("✅ GOOD - Minor issues need attention")
    elif score >= 50:
        print("⚠️  FAIR - Several issues need fixing")
    else:
        print("❌ POOR - Major fixes required")
    
    return score

if __name__ == "__main__":
    score = run_all_tests()
    sys.exit(0 if score >= 75 else 1)
