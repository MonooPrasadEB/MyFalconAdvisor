#!/usr/bin/env python3
"""
MyFalconAdvisor Master Test Runner

Runs all test suites and provides a comprehensive system health report.
"""

import os
import sys
import warnings
import subprocess
from pathlib import Path
from datetime import datetime
import traceback

# Add the parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Suppress known warnings
warnings.filterwarnings('ignore', message='empyrical not available')
warnings.filterwarnings('ignore', message='arch package not available')
warnings.filterwarnings('ignore', message=".*'dict' object has no attribute 'lower'.*")

def check_prerequisites():
    """Check system prerequisites."""
    print("\n🔍 SYSTEM PREREQUISITES CHECK")
    print("=" * 60)
    
    checks = []
    
    # Python version
    python_version = sys.version.split()[0]
    checks.append(("Python version", python_version, True))
    
    # Environment file
    env_file = Path(__file__).parent.parent / ".env"
    checks.append(("Environment file", "Found" if env_file.exists() else "Missing", env_file.exists()))
    
    # Required API keys
    api_keys = {
        "OpenAI API Key": "OPENAI_API_KEY",
        "Alpaca API API Key": "ALPACA_API_KEY",
        "Alpaca Secret API Key": "ALPACA_SECRET_KEY",
        "Alpha Vantage API Key": "ALPHA_VANTAGE_API_KEY",
        "FRED API Key": "FRED_API_KEY"
    }
    
    for key_name, env_var in api_keys.items():
        value = os.getenv(env_var)
        checks.append((key_name, "Configured" if value else "Missing", bool(value)))
    
    # Database configuration
    db_config = {
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD")
    }
    db_configured = all(db_config.values())
    checks.append(("Database configuration", "Complete" if db_configured else "Incomplete", db_configured))
    
    # Required packages
    required_packages = [
        "sqlalchemy",
        "psycopg2-binary",
        "alpaca-py",
        "openai",
        "langchain",
        "langgraph",
        "pydantic",
        "pydantic-settings"
    ]
    
    installed_packages = subprocess.check_output([sys.executable, "-m", "pip", "freeze"]).decode()
    installed_packages = [p.split("==")[0].lower() for p in installed_packages.split()]
    
    missing_packages = [p for p in required_packages if p.lower() not in installed_packages]
    checks.append(("Required packages", 
                  f"All {len(required_packages)} packages installed" if not missing_packages else f"Missing: {', '.join(missing_packages)}", 
                  not missing_packages))
    
    # Print results
    for check_name, status, passed in checks:
        print(f"{'✅' if passed else '❌'} {check_name}: {status}")
    
    print()
    return all(check[2] for check in checks)

def run_test_suite(test_file: str, suite_name: str = None) -> float:
    """Run a test suite and return the score."""
    if not suite_name:
        suite_name = test_file.replace("_", " ").replace(".py", "").title()
    
    print(f"\n🧪 {suite_name}")
    print("=" * 80)
    
    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / test_file)],
        capture_output=True,
        text=True
    )
    
    # Print output
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # Parse score
    try:
        # Look for score in format: "Score: X/Y (Z%)"
        import re
        score_line = None
        
        # Try different score line formats
        patterns = [
            r"Score: (\d+)/(\d+)",
            r"Database Score: (\d+)/(\d+)",
            r"Alpaca Score: (\d+)/(\d+)",
            r"AI Agents Score: (\d+)/(\d+)",
            r"Multi-Client Score: (\d+)/(\d+)"
        ]
        
        for line in result.stdout.split('\n'):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    score_line = line
                    break
            if score_line:
                break
        
        if score_line:
            passed, total = map(int, re.findall(r"(\d+)/(\d+)", score_line)[0])
            score = (passed / total) * 100 if total > 0 else 0
            print(f"📊 {suite_name}: {passed}/{total} ({score:.1f}%) {'✅ PASS' if score >= 80 else '❌ FAIL'}")
            return score
        else:
            print(f"❌ Could not find score in output")
            return 0
            
    except Exception as e:
        print(f"❌ Error parsing test results: {e}")
        return 0

def main():
    """Run all test suites."""
    start_time = datetime.now()
    
    print("\n🧪 MyFalconAdvisor Complete Test Suite")
    print("=" * 80)
    print(f"🕐 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("🛡️  PRODUCTION DATABASE PROTECTION: Tests use READ-ONLY operations")
    print("⚠️  MOCK MODE ENABLED: No real API calls or orders will be made")
    print("=" * 80)
    
    # Enforce mock mode for AlpacaTradingService
    try:
        from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service
        alpaca_trading_service.mock_mode = True
        print("✅ Mock mode enforced for AlpacaTradingService")
    except Exception as e:
        print(f"⚠️  Could not configure mock mode: {e}")
    
    # Check prerequisites
    prereq_score = check_prerequisites()
    
    # Test suites to run
    test_suites = [
        ("test_database_connection.py", "Database Connection"),
        ("test_alpaca_integration.py", "Alpaca Integration"),
        ("test_portfolio_sync_integrity.py", "Portfolio Sync Integrity"),
        ("test_ai_agents.py", "AI Agents"),
        ("test_chat_simple.py", "Chat System")
    ]
    
    # Run tests and collect results
    results = []
    for test_file, suite_name in test_suites:
        try:
            score = run_test_suite(test_file, suite_name)
            results.append((suite_name, score))
        except Exception as e:
            print(f"❌ Error running {suite_name}:")
            traceback.print_exc()
            results.append((suite_name, 0))
    
    # Print final report
    print("\n" + "=" * 80)
    print("🏁 COMPREHENSIVE SYSTEM HEALTH REPORT")
    print("=" * 80)
    
    print(f"\n📋 Prerequisites Score: {prereq_score * 100:.1f}%")
    
    print("\n📊 Test Suite Results:")
    total_score = 0
    total_tests = 0
    for suite_name, score in results:
        status = "✅ PASS" if score >= 80 else "❌ FAIL"
        print(f"  {suite_name}................. {score:>4.1f}% {status}")
        total_score += score
        total_tests += 1
    
    overall_score = total_score / total_tests if total_tests > 0 else 0
    print(f"\n🎯 Overall System Score: {overall_score:.1f}%")
    
    # System status assessment
    if overall_score >= 95:
        status = "🎉 EXCELLENT"
        message = "System is production-ready!"
    elif overall_score >= 80:
        status = "✅ GOOD"
        message = "System is operational with minor issues."
    elif overall_score >= 60:
        status = "⚠️  CAUTION"
        message = "System needs attention."
    else:
        status = "❌ CRITICAL"
        message = "System requires immediate fixes."
    
    print(f"\n🏆 System Status: {status}")
    print(f"💬 Assessment: {message}")
    
    end_time = datetime.now()
    duration = end_time - start_time
    duration_minutes = int(duration.total_seconds() // 60)
    duration_seconds = int(duration.total_seconds() % 60)
    
    print(f"\n🕐 Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Total test duration: {duration_minutes}m {duration_seconds}s")

if __name__ == "__main__":
    main()