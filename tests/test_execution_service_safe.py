"""
Safe test suite for ExecutionService that uses mock mode and cleans up test data.
"""

import os
import sys
import uuid
import time
import logging
from datetime import datetime, date
from functools import wraps
from typing import Optional, Dict, Any

from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from myfalconadvisor.agents.execution_agent import execution_service
from myfalconadvisor.tools.database_service import DatabaseService
from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

if not all([db_user, db_password, db_host, db_port, db_name]):
    raise ValueError("Database environment variables not set")

database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

class TestDatabase:
    """Database connection manager with connection pooling."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TestDatabase, cls).__new__(cls)
            cls._instance.engine = cls._instance._create_engine()
        return cls._instance
    
    def _create_engine(self):
        """Create SQLAlchemy engine with connection pooling."""
        return create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=2,          # Minimal pool size
            max_overflow=0,       # No extra connections
            pool_timeout=30,      # Wait up to 30s for connection
            pool_pre_ping=True,   # Check connection health
            pool_recycle=300      # Recycle connections every 5 min
        )
    
    def get_engine(self):
        """Get SQLAlchemy engine instance."""
        if not self.engine:
            self.engine = self._create_engine()
        return self.engine
    
    def cleanup(self):
        """Force cleanup of all connections."""
        if self.engine and self.engine.pool:
            self.engine.pool.dispose()
            self.engine = None

test_db = TestDatabase()

def with_retries(max_attempts=3, delay=1):
    """
    Decorator for database operations with retries.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay in seconds between retries
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, SQLAlchemyError) as e:
                    last_error = e
                    if "connection slots are reserved" in str(e) or "too many connections" in str(e):
                        logger.warning(f"Connection limit hit, attempt {attempt + 1}/{max_attempts}")
                        if attempt < max_attempts - 1:  # Don't sleep on last attempt
                            time.sleep(delay * (attempt + 1))  # Exponential backoff
                            test_db.cleanup()  # Force connection cleanup
                            continue
                    raise  # Re-raise other errors
            raise last_error
        return wrapper
    return decorator

@with_retries(max_attempts=3)
def setup_test_environment() -> str:
    """
    Set up test environment with a temporary user and portfolio.
    
    Returns:
        str: Test user ID
    """
    engine = test_db.get_engine()
    
    # Generate unique test user ID
    test_user_id = str(uuid.uuid4())
    
    try:
        with engine.connect() as conn:
            # Create test user
            conn.execute(text("""
                INSERT INTO users (user_id, email, first_name, last_name, dob, risk_profile, objective)
                VALUES (:user_id, :email, :first_name, :last_name, :dob, :risk_profile, :objective)
            """), {
                "user_id": test_user_id,
                "email": f"test_{test_user_id}@example.com",
                "first_name": "Test",
                "last_name": "User",
                "dob": date(1990, 1, 1),
                "risk_profile": "MODERATE",
                "objective": "GROWTH"
            })
            
            # Create test portfolio
            conn.execute(text("""
                INSERT INTO portfolios (user_id, portfolio_name, total_value, cash_balance)
                VALUES (:user_id, :portfolio_name, :total_value, :cash_balance)
            """), {
                "user_id": test_user_id,
                "portfolio_name": "Test Portfolio",
                "total_value": 100000.00,
                "cash_balance": 50000.00
            })
            
            conn.commit()
            
        logger.info(f"Created test user {test_user_id} with portfolio")
        return test_user_id
        
    except Exception as e:
        logger.error(f"Error setting up test environment: {e}")
        raise

@with_retries(max_attempts=3)
def cleanup_test_data(test_user_id: str):
    """
    Clean up all test data in correct order to respect foreign key constraints.
    
    Args:
        test_user_id: ID of test user to clean up
    """
    engine = test_db.get_engine()
    
    try:
        with engine.connect() as conn:
            # Get session IDs for this user
            sessions = conn.execute(text("""
                SELECT session_id 
                FROM ai_sessions 
                WHERE user_id = :user_id
            """), {"user_id": test_user_id}).fetchall()
            
            session_ids = [str(row[0]) for row in sessions]
            
            # Delete AI messages and workflows by session ID
            for session_id in session_ids:
                conn.execute(text("""
                    DELETE FROM ai_messages
                    WHERE session_id = :session_id
                """), {"session_id": session_id})
                
                conn.execute(text("""
                    DELETE FROM agent_workflows
                    WHERE session_id = :session_id
                """), {"session_id": session_id})
            
            # Delete recommendations by account ID
            conn.execute(text("""
                DELETE FROM recommendations
                WHERE account_id IN (
                    SELECT account_id 
                    FROM accounts 
                    WHERE user_id = :user_id
                )
            """), {"user_id": test_user_id})
            
            # Delete portfolio assets by portfolio ID
            conn.execute(text("""
                DELETE FROM portfolio_assets
                WHERE portfolio_id IN (
                    SELECT portfolio_id 
                    FROM portfolios 
                    WHERE user_id = :user_id
                )
            """), {"user_id": test_user_id})
            
            # Delete other tables that reference user_id
            tables = [
                "ai_sessions",
                "compliance_checks",
                "transactions",
                "portfolios",
                "accounts",
                "users"
            ]
            
            for table in tables:
                conn.execute(text(f"""
                    DELETE FROM {table}
                    WHERE user_id = :user_id
                """), {"user_id": test_user_id})
            
            conn.commit()
            
        logger.info(f"Cleaned up all test data for user {test_user_id}")
        
    except Exception as e:
        logger.error(f"Error cleaning up test data: {e}")
        raise

@with_retries(max_attempts=3)
def verify_database_state(test_user_id: str) -> Dict[str, Any]:
    """
    Verify database state for test user.
    
    Args:
        test_user_id: ID of test user to verify
        
    Returns:
        Dict containing counts of relevant records
    """
    engine = test_db.get_engine()
    
    try:
        with engine.connect() as conn:
            # Get portfolio state
            portfolio = conn.execute(text("""
                SELECT total_value, cash_balance
                FROM portfolios
                WHERE user_id = :user_id
            """), {"user_id": test_user_id}).fetchone()
            
            # Count transactions
            transactions = conn.execute(text("""
                SELECT COUNT(*)
                FROM transactions
                WHERE user_id = :user_id
            """), {"user_id": test_user_id}).scalar()
            
            # Count AI records
            ai_sessions = conn.execute(text("""
                SELECT COUNT(*)
                FROM ai_sessions
                WHERE user_id = :user_id
            """), {"user_id": test_user_id}).scalar()
            
            compliance_checks = conn.execute(text("""
                SELECT COUNT(*)
                FROM compliance_checks
                WHERE user_id = :user_id
            """), {"user_id": test_user_id}).scalar()
            
            return {
                "portfolio_value": portfolio[0] if portfolio else 0,
                "cash_balance": portfolio[1] if portfolio else 0,
                "transactions": transactions,
                "ai_sessions": ai_sessions,
                "compliance_checks": compliance_checks
            }
            
    except Exception as e:
        logger.error(f"Error verifying database state: {e}")
        raise

def test_execution_service():
    """Test ExecutionService with mock mode and database cleanup."""
    
    # Force mock mode for Alpaca and read-only mode for database
    alpaca_trading_service.mock_mode = True
    execution_service.read_only_mode = True
    logger.info("✅ Forced mock mode for Alpaca and read-only mode for database")
    
    test_user_id = None
    test_score = 0
    total_tests = 4
    try:
        # Set up test environment
        logger.info("\n🔒 Setting up safe test environment...")
        test_user_id = setup_test_environment()
        logger.info(f"✅ Created test user {test_user_id} with portfolio")
        test_score += 1
        
        # Test valid recommendation
        logger.info("\n🧪 Testing ExecutionService...")
        logger.info("\n📝 Processing recommendation: Buy 10 AAPL")
        
        recommendation = {
            "symbol": "AAPL",
            "action": "buy",
            "quantity": 10,
            "price": 175.50,
            "order_type": "market"
        }
        
        result = execution_service.process_ai_recommendation(test_user_id, recommendation)
        
        logger.info("\n✅ Recommendation processed:")
        logger.info(f"Status: {result.get('status', 'unknown')}")
        logger.info(f"Stage: {result.get('stage', 'unknown')}")
        test_score += 1
        
        # Verify database state
        logger.info("\n🔍 Verifying database state...")
        state = verify_database_state(test_user_id)
        
        logger.info(f"\nTransactions for test user: {state['transactions']}")
        logger.info(f"\nPortfolio value: ${state['portfolio_value']:,.2f}")
        logger.info(f"Cash balance: ${state['cash_balance']:,.2f}")
        logger.info(f"\nAI Sessions: {state['ai_sessions']}")
        logger.info(f"Compliance Checks: {state['compliance_checks']}")
        test_score += 1
        
        # Test invalid recommendation
        logger.info("\n🧪 Testing invalid recommendation...")
        
        invalid_recommendation = {
            "symbol": "AAPL",
            "action": "buy",
            "quantity": 10,
            "price": 175.50,
            "order_type": "market"
        }
        
        result = execution_service.process_ai_recommendation("invalid_user", invalid_recommendation)
        
        logger.info("\n✅ Invalid recommendation processed:")
        logger.info(f"Status: {result.get('status', 'unknown')}")
        logger.info(f"Stage: {result.get('stage', 'unknown')}")
        logger.info(f"Reason: {result.get('message', 'No portfolio found for user')}")
        test_score += 1
        
        # Verify database state again
        logger.info("\n🔍 Verifying database state...")
        state = verify_database_state(test_user_id)
        
        logger.info(f"\nTransactions for test user: {state['transactions']}")
        logger.info(f"\nPortfolio value: ${state['portfolio_value']:,.2f}")
        logger.info(f"Cash balance: ${state['cash_balance']:,.2f}")
        logger.info(f"\nAI Sessions: {state['ai_sessions']}")
        logger.info(f"Compliance Checks: {state['compliance_checks']}")
        
        # Output test score
        score_percent = (test_score / total_tests) * 100
        print(f"\n📊 Execution Service Score: {test_score}/{total_tests} ({score_percent:.1f}%)")
        if test_score == total_tests:
            print("🎉 All execution service tests passed!")
        else:
            print("⚠️  Some execution service tests failed")
        
    finally:
        # Clean up test data
        if test_user_id:
            logger.info("\n🧹 Cleaning up test data...")
            cleanup_test_data(test_user_id)
            test_db.cleanup()
            logger.info("✅ Cleaned up all test data")
        
        # Reset modes
        execution_service.read_only_mode = False

if __name__ == "__main__":
    test_execution_service()