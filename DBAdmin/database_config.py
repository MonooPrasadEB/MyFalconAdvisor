"""
Database configuration for MyFalconAdvisor with Aiven PostgreSQL
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)

# Database configuration
class DatabaseConfig:
    """Database configuration for Aiven PostgreSQL"""
    
    # Aiven PostgreSQL connection details
    DB_HOST = "pg-2e1b40a1-falcon-horizon-5e1b-falccon.i.aivencloud.com"
    DB_PORT = "24382"
    DB_NAME = "myfalconadvisor_db"
    SSL_MODE = "require"
    
    # Team user credentials (set via environment variables)
    DB_USER = os.getenv("DB_USER", "avnadmin")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    
    # Connection pool settings
    POOL_SIZE = 5
    MAX_OVERFLOW = 10
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600  # 1 hour
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get the database connection URL"""
        if not cls.DB_PASSWORD:
            raise ValueError("DB_PASSWORD environment variable is required")
        
        return (
            f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@"
            f"{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?sslmode={cls.SSL_MODE}"
        )
    
    @classmethod
    def create_engine(cls):
        """Create SQLAlchemy engine with connection pooling"""
        database_url = cls.get_database_url()
        
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=cls.POOL_SIZE,
            max_overflow=cls.MAX_OVERFLOW,
            pool_timeout=cls.POOL_TIMEOUT,
            pool_recycle=cls.POOL_RECYCLE,
            echo=os.getenv("DB_ECHO", "false").lower() == "true",  # Set to true for SQL debugging
        )
        
        return engine

# Global database setup
engine = None
SessionLocal = None
Base = declarative_base()

def init_database():
    """Initialize database connection"""
    global engine, SessionLocal
    
    try:
        engine = DatabaseConfig.create_engine()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            logger.info(f"Connected to PostgreSQL: {version}")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def get_db():
    """Get database session (for dependency injection)"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Test database connection"""
    try:
        if not engine:
            init_database()
        
        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT 1 as test;"))
            test_value = result.fetchone()[0]
            
            # Test table existence
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                LIMIT 5;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print("✅ Database connection successful!")
            print(f"📊 Test query result: {test_value}")
            print(f"📋 Available tables: {', '.join(tables) if tables else 'None (run schema first)'}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    """Test script - run this to verify database connection"""
    import sys
    
    print("🔍 Testing MyFalconAdvisor Database Connection")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv("DB_PASSWORD"):
        print("❌ DB_PASSWORD environment variable not set")
        print("   Set it with: export DB_PASSWORD='your_team_password'")
        sys.exit(1)
    
    # Test connection
    if test_connection():
        print("\n🎉 Database setup is working correctly!")
    else:
        print("\n💥 Database connection failed. Check your credentials.")
        sys.exit(1)
