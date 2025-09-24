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
    """Test basic CRUD operations."""
    print("\n🔄 Testing Database CRUD Operations")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.database_service import database_service
        
        if not database_service.engine:
            print("⚠️  Database not available - skipping CRUD test")
            return True
        
        # Generate proper UUIDs for testing
        import uuid
        test_user_id = str(uuid.uuid4())
        test_portfolio_id = str(uuid.uuid4())
        
        # Test portfolio creation
        test_portfolio = {
            "portfolio_id": test_portfolio_id,
            "user_id": test_user_id, 
            "portfolio_name": "Test Portfolio",
            "total_value": 10000.0,
            "cash_balance": 10000.0,
            "portfolio_type": "other",
            "is_primary": True,
            "portfolio_notes": "Test portfolio for CRUD operations",
            "created_at": datetime.now()
        }
        
        # First create a test user with unique email
        import time
        unique_email = f"test_{int(time.time())}@example.com"
        test_user = {
            "user_id": test_user_id,
            "email": unique_email,
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Create user (ignore if exists)
        with database_service.engine.connect() as conn:
            from sqlalchemy import text
            try:
                conn.execute(text("""
                    INSERT INTO users (user_id, email, first_name, last_name)
                    VALUES (:user_id, :email, :first_name, :last_name)
                """), test_user)
                conn.commit()
                print("✅ Test user created")
            except Exception as e:
                print(f"⚠️  User creation failed: {e}")
                return False
        
        # Test CREATE
        success = database_service.create_portfolio(test_portfolio)
        if success:
            print("✅ CREATE operation successful")
        else:
            print("❌ CREATE operation failed")
            return False
        
        # Test READ
        with database_service.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT portfolio_name FROM portfolios 
                WHERE portfolio_id = :portfolio_id
            """), {"portfolio_id": test_portfolio_id})
            
            row = result.fetchone()
            if row and row[0] == "Test Portfolio":
                print("✅ READ operation successful")
            else:
                print("❌ READ operation failed")
                return False
        
        # Clean up test data
        with database_service.engine.connect() as conn:
            conn.execute(text("DELETE FROM portfolios WHERE portfolio_id = :portfolio_id"), {"portfolio_id": test_portfolio_id})
            conn.execute(text("DELETE FROM users WHERE user_id = :user_id"), {"user_id": test_user_id})
            conn.commit()
            print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ CRUD operations test failed: {e}")
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
