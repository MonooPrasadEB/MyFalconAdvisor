#!/usr/bin/env python3
"""
Quick Health Check

Performs a fast system health check without running full test suites.
"""

import os
import sys
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

def quick_database_check():
    """Quick database connectivity check."""
    try:
        from myfalconadvisor.tools.database_service import database_service
        if database_service.engine:
            with database_service.engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            return "✅ Connected"
        else:
            return "⚠️  Mock mode"
    except Exception as e:
        return f"❌ Failed: {str(e)[:50]}..."

def quick_alpaca_check():
    """Quick Alpaca API connectivity check."""
    try:
        from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service
        result = alpaca_trading_service.test_connection()
        if result.get('success'):
            return "✅ Connected"
        else:
            return f"❌ Failed: {result.get('error', 'Unknown')[:50]}..."
    except Exception as e:
        return f"❌ Failed: {str(e)[:50]}..."

def quick_ai_check():
    """Quick AI agents check."""
    try:
        from myfalconadvisor.agents.multi_task_agent import MultiTaskAgent
        agent = MultiTaskAgent()
        return "✅ Initialized"
    except Exception as e:
        return f"❌ Failed: {str(e)[:50]}..."

def main():
    """Run quick health check."""
    print("⚡ MyFalconAdvisor Quick Health Check")
    print("=" * 50)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    load_env()
    
    # API Keys status
    print(f"\n🔑 API Keys:")
    keys = {
        "OpenAI": "✅" if os.getenv("OPENAI_API_KEY") else "❌",
        "Alpaca": "✅" if os.getenv("ALPACA_API_KEY") else "❌",
        "Alpha Vantage": "✅" if os.getenv("ALPHA_VANTAGE_API_KEY") else "❌",
        "FRED": "✅" if os.getenv("FRED_API_KEY") else "❌"
    }
    for service, status in keys.items():
        print(f"  {service}: {status}")
    
    # Quick component checks
    print(f"\n🧪 Component Status:")
    print(f"  Database: {quick_database_check()}")
    print(f"  Alpaca API: {quick_alpaca_check()}")
    print(f"  AI Agents: {quick_ai_check()}")
    
    # Environment info
    print(f"\n🌐 Environment:")
    print(f"  Database: {os.getenv('DB_HOST', 'Not set')}")
    print(f"  Alpaca Mode: {'Paper' if os.getenv('ALPACA_PAPER_TRADING', 'true').lower() == 'true' else 'Live'}")
    
    print(f"\n💡 For detailed testing, run: python tests/run_all_tests.py")

if __name__ == "__main__":
    main()
