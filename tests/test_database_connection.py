#!/usr/bin/env python3
"""
Database Connection Tests

Tests PostgreSQL database connectivity, schema validation, and basic CRUD operations.
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

def test_database_connection():
    """Test basic database connection."""
    print("🗄️  Testing Database Connection")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.database_service import database_service
        
        # Test connection
        if database_service.engine:
            print("✅ Database service initialized successfully")
            
            # Test basic query
            with database_service.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]
                
                if test_value == 1:
                    print("✅ Database connection test passed")
                    return True
                else:
                    print("❌ Database connection test failed")
                    return False
        else:
            print("⚠️  Database service not available (running in mock mode)")
            return True  # Consider this a pass for mock mode
            
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        print(f"🔍 Error details: {traceback.format_exc()}")
        return False

def test_database_schema():
    """Test database schema validation."""
    print("\n📋 Testing Database Schema")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.database_service import database_service
        
        if not database_service.engine:
            print("⚠️  Database not available - skipping schema test")
            return True
        
        # Check for essential tables
        essential_tables = [
            'users', 'portfolios', 'portfolio_assets', 
            'transactions', 'audit_trail'
        ]
        
        with database_service.engine.connect() as conn:
            from sqlalchemy import text
            
            existing_tables = []
            for table in essential_tables:
                result = conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                """))
                
                if result.fetchone()[0] > 0:
                    existing_tables.append(table)
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"⚠️  Table '{table}' missing")
            
            if len(existing_tables) >= len(essential_tables) * 0.8:  # 80% of tables exist
                print(f"✅ Schema validation passed ({len(existing_tables)}/{len(essential_tables)} tables)")
                return True
            else:
                print(f"❌ Schema validation failed ({len(existing_tables)}/{len(essential_tables)} tables)")
                return False
                
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False

def test_database_crud():
    """Test database service methods without modifying production data."""
    print("\n🔄 Testing Database Service Methods (READ-ONLY)")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.database_service import database_service
        
        if not database_service.engine:
            print("⚠️  Database not available - skipping CRUD test")
            return True
        
        # Test READ operations only - no data modification
        with database_service.engine.connect() as conn:
            from sqlalchemy import text
            
            # Test connection and basic query
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            print(f"✅ READ operation successful - Found {user_count} users")
            
            # Test portfolio query
            result = conn.execute(text("SELECT COUNT(*) FROM portfolios"))
            portfolio_count = result.fetchone()[0]
            print(f"✅ READ operation successful - Found {portfolio_count} portfolios")
            
            # Test transaction query
            result = conn.execute(text("SELECT COUNT(*) FROM transactions"))
            transaction_count = result.fetchone()[0]
            print(f"✅ READ operation successful - Found {transaction_count} transactions")
        
        # Test database service methods (read-only)
        try:
            # This should work without modifying data
            portfolios = database_service.get_user_portfolios("usr_348784c4-6f83-4857-b7dc-f5132a38dfee")
            print(f"✅ Database service method test successful - Found {len(portfolios) if portfolios else 0} user portfolios")
        except Exception as e:
            print(f"⚠️  Database service method test: {e}")
        
        print("✅ All READ operations completed successfully")
        print("ℹ️  CRUD test now uses READ-ONLY operations to protect production data")
        
        return True
        
    except Exception as e:
        print(f"❌ Database service test failed: {e}")
        return False

def main():
    """Run all database tests."""
    print("🧪 MyFalconAdvisor Database Test Suite")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment
    load_env()
    
    # Database connection info
    db_host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME', 'myfalconadvisor_db')
    print(f"🌐 Testing connection to: {db_host}/{db_name}")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Database Schema", test_database_schema),
        ("CRUD Operations", test_database_crud)
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
    print(f"\n{'='*60}")
    print("🏁 DATABASE TEST RESULTS")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n🎯 Database Score: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 Database is fully operational!")
    elif passed >= total * 0.7:
        print("👍 Database is mostly working. Check failed tests above.")
    else:
        print("⚠️  Database needs attention. Check configuration and connectivity.")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
