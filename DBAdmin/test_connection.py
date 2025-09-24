#!/usr/bin/env python3
"""
Database Connection Test Script

Quick script to test database connectivity and basic operations.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import traceback

# Add the parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print(f"📁 Loading environment from {env_file}")
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    try:
                        key, value = line.strip().split("=", 1)
                        os.environ[key] = value
                    except ValueError:
                        continue
    else:
        print("⚠️  No .env file found")

def test_raw_connection():
    """Test raw psycopg2 connection."""
    print("🔌 Testing Raw psycopg2 Connection")
    print("=" * 50)
    
    try:
        import psycopg2
        
        # Get connection parameters
        conn_params = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'sslmode': os.getenv('DB_SSLMODE', 'require')
        }
        
        print(f"🌐 Host: {conn_params['host']}")
        print(f"🚪 Port: {conn_params['port']}")
        print(f"🗄️  Database: {conn_params['database']}")
        print(f"👤 User: {conn_params['user']}")
        print(f"🔒 SSL Mode: {conn_params['sslmode']}")
        
        # Test connection
        print("\n🔄 Attempting connection...")
        conn = psycopg2.connect(**conn_params)
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        print(f"✅ Connection successful!")
        print(f"📊 PostgreSQL Version: {version.split(',')[0]}")
        
        # Test basic operations
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()[0]
        print(f"📋 Tables in public schema: {table_count}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"🔍 Error details: {traceback.format_exc()}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection."""
    print("\n🔧 Testing SQLAlchemy Connection")
    print("=" * 50)
    
    try:
        from sqlalchemy import create_engine, text
        
        # Build connection string
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_sslmode = os.getenv('DB_SSLMODE', 'require')
        
        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}"
        
        print(f"🔗 Connection String: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}")
        
        # Create engine
        engine = create_engine(connection_string, echo=False)
        
        # Test connection
        print("\n🔄 Testing SQLAlchemy engine...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user, current_timestamp"))
            row = result.fetchone()
            
            print(f"✅ SQLAlchemy connection successful!")
            print(f"🗄️  Current Database: {row[0]}")
            print(f"👤 Current User: {row[1]}")
            print(f"🕐 Server Time: {row[2]}")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        print(f"🔍 Error details: {traceback.format_exc()}")
        return False

def test_application_service():
    """Test application database service."""
    print("\n🏗️  Testing Application Database Service")
    print("=" * 50)
    
    try:
        from myfalconadvisor.tools.database_service import database_service
        
        if database_service.engine:
            print("✅ Database service initialized successfully")
            
            # Test query through service
            with database_service.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SELECT 'Hello from MyFalconAdvisor!' as message"))
                message = result.fetchone()[0]
                print(f"📨 Test Message: {message}")
            
            return True
        else:
            print("⚠️  Database service not available (mock mode)")
            return False
            
    except Exception as e:
        print(f"❌ Application service test failed: {e}")
        print(f"🔍 Error details: {traceback.format_exc()}")
        return False

def main():
    """Run all database connection tests."""
    print("🧪 Database Connection Diagnostic Tool")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment
    load_env()
    
    # Check required environment variables
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("💡 Please check your .env file configuration")
        return False
    
    # Run tests
    tests = [
        ("Raw psycopg2 Connection", test_raw_connection),
        ("SQLAlchemy Connection", test_sqlalchemy_connection),
        ("Application Service", test_application_service)
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
    print("🏁 DATABASE CONNECTION TEST RESULTS")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n🎯 Connection Score: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All database connections are working perfectly!")
    elif passed > 0:
        print("⚠️  Some connection methods are working. Check failed tests above.")
    else:
        print("❌ No database connections are working. Check configuration.")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
