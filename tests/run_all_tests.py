#!/usr/bin/env python3
"""
MyFalconAdvisor Master Test Runner

Runs all test suites and provides a comprehensive system health report.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import traceback

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

def force_mock_mode():
    """Force mock mode for all tests by setting environment variable."""
    os.environ["MYFALCON_TEST_MODE"] = "mock"
    
    # Import and configure AlpacaTradingService
    try:
        from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service
        alpaca_trading_service.mock_mode = True
        print("✅ Mock mode enforced for AlpacaTradingService")
    except Exception as e:
        print(f"⚠️  Could not configure mock mode: {e}")

def run_test_suite(test_file, suite_name):
    """Run a single test suite and return results."""
    print(f"\n{'='*80}")
    print(f"🧪 RUNNING {suite_name.upper()} TESTS")
    print(f"{'='*80}")
    
    try:
        # Set mock mode in environment for subprocess
        env = os.environ.copy()
        env["MYFALCON_TEST_MODE"] = "mock"
        
        # Run the test file
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per test suite
            env=env  # Pass modified environment
        )
        
        # Print the output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Parse results from output
        output_lines = result.stdout.split('\n')
        
        # Look for score line - handle multiple formats
        score_info = {"passed": 0, "total": 0, "percentage": 0}
        for line in output_lines:
            # Format 1: "3/6 tests passed (50.0%)"
            # Format 2: "📊 Overall Score: 4/4 (100.0%)"
            # Format 3: "📊 Multi-Client Score: 5/5 (100.0%)"
            if ("tests passed" in line or "Overall Score:" in line or "Multi-Client Score:" in line) and "%" in line:
                try:
                    # Extract numbers from lines with X/Y format
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "/" in part:
                            passed, total = part.split("/")
                            score_info["passed"] = int(passed)
                            score_info["total"] = int(total)
                            # Look for percentage
                            for j in range(i, min(i+5, len(parts))):
                                if "%" in parts[j]:
                                    pct_str = parts[j].replace("(", "").replace("%)", "").replace("%", "")
                                    score_info["percentage"] = float(pct_str)
                                    break
                            break
                except:
                    pass
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "score": score_info
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Test suite timed out after 5 minutes",
            "score": {"passed": 0, "total": 0, "percentage": 0}
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "score": {"passed": 0, "total": 0, "percentage": 0}
        }

def check_system_prerequisites():
    """Check system prerequisites and configuration."""
    print("🔍 SYSTEM PREREQUISITES CHECK")
    print("=" * 60)
    
    checks = []
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        checks.append(True)
    else:
        print(f"❌ Python version: {python_version.major}.{python_version.minor}.{python_version.micro} (requires 3.8+)")
        checks.append(False)
    
    # Check environment file
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print("✅ Environment file: Found")
        checks.append(True)
    else:
        print("❌ Environment file: Missing (.env file not found)")
        checks.append(False)
    
    # Check API keys
    load_env()
    
    api_keys = {
        "OpenAI": os.getenv("OPENAI_API_KEY"),
        "Alpaca API": os.getenv("ALPACA_API_KEY"),
        "Alpaca Secret": os.getenv("ALPACA_SECRET_KEY"),
        "Alpha Vantage": os.getenv("ALPHA_VANTAGE_API_KEY"),
        "FRED": os.getenv("FRED_API_KEY")
    }
    
    for service, key in api_keys.items():
        if key and len(key) > 10:
            print(f"✅ {service} API Key: Configured")
            checks.append(True)
        else:
            print(f"⚠️  {service} API Key: Not configured")
            checks.append(False)
    
    # Check database configuration
    db_config = {
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD")
    }
    
    db_configured = all(db_config.values())
    if db_configured:
        print("✅ Database configuration: Complete")
        checks.append(True)
    else:
        print("⚠️  Database configuration: Incomplete")
        checks.append(False)
    
    # Check required packages
    required_packages = [
        ("langchain", "langchain"),
        ("openai", "openai"), 
        ("alpaca-py", "alpaca"),  # Package name vs import name
        ("psycopg2", "psycopg2"), 
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("requests", "requests"),
        ("pydantic", "pydantic")
    ]
    
    missing_packages = []
    for display_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(display_name)
    
    if not missing_packages:
        print(f"✅ Required packages: All {len(required_packages)} packages installed")
        checks.append(True)
    else:
        print(f"❌ Required packages: {len(missing_packages)} missing: {', '.join(missing_packages)}")
        checks.append(False)
    
    return sum(checks) / len(checks) if checks else 0

def main():
    """Run all test suites and generate comprehensive report."""
    print("🧪 MyFalconAdvisor Complete Test Suite")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🛡️  PRODUCTION DATABASE PROTECTION: Tests use READ-ONLY operations")
    print("⚠️  MOCK MODE ENABLED: No real API calls or orders will be made")
    print("=" * 80)
    
    # Force mock mode
    force_mock_mode()
    
    # Check prerequisites
    prereq_score = check_system_prerequisites()
    
    # Define test suites
    test_suites = [
        ("tests/test_database_connection.py", "Database Connection"),
        ("tests/test_alpaca_integration.py", "Alpaca Integration"),
        ("tests/test_ai_agents.py", "AI Agents"),
        ("tests/test_complete_logging_workflow_readonly.py", "Complete Logging Workflow (READ-ONLY)"),
        ("tests/test_multi_client_system_readonly.py", "Multi-Client System (READ-ONLY)")
    ]
    
    results = {}
    
    # Run each test suite
    for test_file, suite_name in test_suites:
        test_path = Path(__file__).parent.parent / test_file
        if test_path.exists():
            results[suite_name] = run_test_suite(str(test_path), suite_name)
        else:
            print(f"⚠️  Test file not found: {test_file}")
            results[suite_name] = {
                "success": False,
                "output": "",
                "error": f"Test file not found: {test_file}",
                "score": {"passed": 0, "total": 0, "percentage": 0}
            }
    
    # Generate comprehensive report
    print(f"\n{'='*80}")
    print("🏁 COMPREHENSIVE SYSTEM HEALTH REPORT")
    print(f"{'='*80}")
    
    print(f"\n📋 Prerequisites Score: {prereq_score*100:.1f}%")
    
    total_passed = 0
    total_tests = 0
    
    print(f"\n📊 Test Suite Results:")
    for suite_name, result in results.items():
        score = result["score"]
        passed = score["passed"]
        total = score["total"]
        percentage = score["percentage"]
        
        total_passed += passed
        total_tests += total
        
        status = "✅ PASS" if result["success"] and percentage >= 70 else "❌ FAIL"
        print(f"  {suite_name:.<35} {passed:>2}/{total:<2} ({percentage:>5.1f}%) {status}")
    
    overall_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n🎯 Overall System Score: {total_passed}/{total_tests} ({overall_percentage:.1f}%)")
    
    # System status
    if overall_percentage >= 90:
        status = "🎉 EXCELLENT"
        message = "System is production-ready!"
    elif overall_percentage >= 75:
        status = "👍 GOOD"
        message = "System is mostly operational with minor issues."
    elif overall_percentage >= 50:
        status = "⚠️  FAIR"
        message = "System has significant issues that need attention."
    else:
        status = "❌ POOR"
        message = "System requires major fixes before use."
    
    print(f"\n🏆 System Status: {status}")
    print(f"💬 Assessment: {message}")
    
    # Recommendations
    if overall_percentage < 90:
        print(f"\n💡 Recommendations:")
        
        if prereq_score < 0.8:
            print("1. Fix prerequisite issues (API keys, environment configuration)")
        
        failed_suites = [name for name, result in results.items() 
                        if not result["success"] or result["score"]["percentage"] < 70]
        
        if failed_suites:
            print(f"2. Focus on failed test suites: {', '.join(failed_suites)}")
        
        if total_tests == 0:
            print("3. Ensure all test files are present and executable")
        
        print("4. Check the detailed test outputs above for specific error messages")
        print("5. Verify all dependencies are properly installed")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit with appropriate code
    exit_code = 0 if overall_percentage >= 70 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()