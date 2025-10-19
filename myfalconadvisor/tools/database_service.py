"""
Database Service for MyFalconAdvisor.

This service provides database operations for portfolio management,
transaction tracking, and audit trail maintenance.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import Pool

from ..core.config import Config

config = Config.get_instance()
logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Service for database operations related to portfolios, transactions, and audit trails.
    """
    
    def __init__(self):
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize database connection."""
        try:
            # For now, we'll create a simple connection string
            # In production, you'd use your actual database configuration
            db_url = getattr(config, 'database_url', None)
            
            if not db_url:
                # Construct from individual components if available
                db_user = getattr(config, 'db_user', 'postgres')
                db_password = getattr(config, 'db_password', 'password')
                db_host = getattr(config, 'db_host', 'localhost')
                db_port = getattr(config, 'db_port', '5432')
                db_name = getattr(config, 'db_name', 'myfalconadvisor_db')
                
                db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            self.engine = create_engine(
                db_url, 
                echo=getattr(config, 'db_echo', False),
                pool_size=5,  # Permanent connections (balanced for concurrent operations)
                max_overflow=10,  # Allow bursts up to 15 total connections
                pool_timeout=30,  # Timeout for getting connection from pool
                pool_recycle=1800,  # Recycle connections after 30 minutes
                pool_pre_ping=True,  # Verify connections before using them
                connect_args={
                    "options": "-c idle_in_transaction_session_timeout=300000"  # 5 minutes in milliseconds
                }
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Add connection pool event listeners
            self._setup_connection_events()
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Database connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            logger.warning("Database operations will run in mock mode")
            self.engine = None
            self.SessionLocal = None
    
    def get_session(self):
        """Get database session."""
        if self.SessionLocal:
            return self.SessionLocal()
        return None
    
    def dispose(self):
        """Dispose of all connections in the pool."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection pool disposed")
    
    def close_idle_connections(self):
        """Close idle connections to free up database slots."""
        if not self.engine:
            return
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE usename = :username
                    AND state = 'idle'
                    AND pid != pg_backend_pid()
                """), {"username": getattr(config, 'db_user', 'postgres')})
                conn.commit()
                logger.info("Closed idle database connections")
        except Exception as e:
            logger.error(f"Failed to close idle connections: {e}")
    
    def _setup_connection_events(self):
        """Set up connection pool event listeners for better management."""
        if not self.engine:
            return
        
        @event.listens_for(Pool, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Called when a new connection is created."""
            logger.debug("New database connection created")
        
        @event.listens_for(Pool, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Called when a connection is checked out from the pool."""
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(Pool, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Called when a connection is returned to the pool."""
            logger.debug("Connection returned to pool")
    
    def get_pool_status(self):
        """Get current connection pool status."""
        if not self.engine:
            return {"status": "unavailable"}
        
        try:
            pool = self.engine.pool
            return {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "total": pool.size() + pool.overflow()
            }
        except Exception as e:
            logger.error(f"Failed to get pool status: {e}")
            return {"error": str(e)}
    
    def update_portfolio(self, portfolio_id: str, updates: Dict) -> bool:
        """Update portfolio with new values."""
        if not self.engine:
            logger.warning("Database not available - mock update")
            return True
        
        try:
            with self.engine.connect() as conn:
                # Build update query dynamically
                set_clauses = []
                params = {"portfolio_id": portfolio_id}
                
                for key, value in updates.items():
                    if key != "portfolio_id":
                        set_clauses.append(f"{key} = :{key}")
                        params[key] = value
                
                if not set_clauses:
                    return True
                
                query = f"""
                UPDATE portfolios 
                SET {', '.join(set_clauses)}
                WHERE portfolio_id = :portfolio_id
                """
                
                result = conn.execute(text(query), params)
                conn.commit()
                
                return result.rowcount > 0
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to update portfolio {portfolio_id}: {e}")
            return False
    
    def upsert_portfolio_asset(self, asset_data: Dict) -> bool:
        """Insert or update portfolio asset."""
        if not self.engine:
            logger.warning("Database not available - mock upsert")
            return True
        
        try:
            with self.engine.connect() as conn:
                # Check if asset exists
                check_query = """
                SELECT asset_id FROM portfolio_assets 
                WHERE portfolio_id = :portfolio_id AND symbol = :symbol
                """
                
                existing = conn.execute(text(check_query), {
                    "portfolio_id": asset_data["portfolio_id"],
                    "symbol": asset_data["symbol"]
                }).fetchone()
                
                if existing:
                    # Update existing asset
                    set_clauses = []
                    params = {
                        "portfolio_id": asset_data["portfolio_id"],
                        "symbol": asset_data["symbol"]
                    }
                    
                    for key, value in asset_data.items():
                        if key not in ["portfolio_id", "symbol"]:
                            set_clauses.append(f"{key} = :{key}")
                            params[key] = value
                    
                    update_query = f"""
                    UPDATE portfolio_assets 
                    SET {', '.join(set_clauses)}
                    WHERE portfolio_id = :portfolio_id AND symbol = :symbol
                    """
                    
                    conn.execute(text(update_query), params)
                    
                else:
                    # Insert new asset
                    asset_data["asset_id"] = str(uuid.uuid4())
                    
                    columns = list(asset_data.keys())
                    placeholders = [f":{col}" for col in columns]
                    
                    insert_query = f"""
                    INSERT INTO portfolio_assets ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                    """
                    
                    conn.execute(text(insert_query), asset_data)
                
                conn.commit()
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to upsert portfolio asset: {e}")
            return False
    
    def create_transaction(self, transaction_data: Dict) -> Optional[str]:
        """Create a new transaction record."""
        if not self.engine:
            logger.warning("Database not available - mock transaction creation")
            return str(uuid.uuid4())
        
        try:
            transaction_id = str(uuid.uuid4())
            transaction_data["transaction_id"] = transaction_id
            
            with self.engine.connect() as conn:
                columns = list(transaction_data.keys())
                placeholders = [f":{col}" for col in columns]
                
                insert_query = f"""
                INSERT INTO transactions ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                """
                
                conn.execute(text(insert_query), transaction_data)
                conn.commit()
                
                return transaction_id
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to create transaction: {e}")
            return None
    
    def update_transaction_by_broker_ref(self, broker_reference: str, updates: Dict) -> bool:
        """Update transaction by broker reference."""
        if not self.engine:
            logger.warning("Database not available - mock transaction update")
            return True
        
        try:
            with self.engine.connect() as conn:
                set_clauses = []
                params = {"broker_reference": broker_reference}
                
                for key, value in updates.items():
                    if key != "broker_reference":
                        set_clauses.append(f"{key} = :{key}")
                        params[key] = value
                
                if not set_clauses:
                    return True
                
                query = f"""
                UPDATE transactions 
                SET {', '.join(set_clauses)}
                WHERE broker_reference = :broker_reference
                """
                
                result = conn.execute(text(query), params)
                conn.commit()
                
                return result.rowcount > 0
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to update transaction by broker ref {broker_reference}: {e}")
            return False
    
    def create_audit_entry(self, user_id: str, entity_type: str, entity_id: str, 
                          action: str, old_values: Optional[Dict] = None, 
                          new_values: Optional[Dict] = None) -> bool:
        """Create audit trail entry."""
        if not self.engine:
            logger.warning("Database not available - mock audit entry")
            return True
        
        try:
            import json
            
            audit_data = {
                "audit_id": str(uuid.uuid4()),
                "user_id": user_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "old_values": json.dumps(old_values) if old_values else None,
                "new_values": json.dumps(new_values) if new_values else None,
                "created_at": datetime.utcnow()
            }
            
            with self.engine.connect() as conn:
                insert_query = """
                INSERT INTO audit_trail (audit_id, user_id, entity_type, entity_id, action, old_values, new_values, created_at)
                VALUES (:audit_id, :user_id, :entity_type, :entity_id, :action, :old_values, :new_values, :created_at)
                """
                
                conn.execute(text(insert_query), audit_data)
                conn.commit()
                
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to create audit entry: {e}")
            return False
    
    def get_portfolio_by_id(self, portfolio_id: str) -> Optional[Dict]:
        """Get portfolio by ID."""
        if not self.engine:
            return None
        
        try:
            with self.engine.connect() as conn:
                query = """
                SELECT p.*, 
                       COUNT(pa.asset_id) as asset_count,
                       SUM(pa.market_value) as total_assets_value
                FROM portfolios p
                LEFT JOIN portfolio_assets pa ON p.portfolio_id = pa.portfolio_id
                WHERE p.portfolio_id = :portfolio_id
                GROUP BY p.portfolio_id, p.user_id, p.portfolio_name, p.total_value, p.cash_balance, 
                         p.portfolio_type, p.is_primary, p.portfolio_notes, p.created_at, p.updated_at
                """
                
                result = conn.execute(text(query), {"portfolio_id": portfolio_id}).fetchone()
                
                if result:
                    return dict(result._mapping)
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get portfolio {portfolio_id}: {e}")
            return None
    
    def get_user_portfolios(self, user_id: str) -> List[Dict]:
        """Get all portfolios for a user."""
        if not self.engine:
            return []
        
        try:
            with self.engine.connect() as conn:
                query = """
                SELECT p.*, 
                       COUNT(pa.asset_id) as asset_count,
                       SUM(pa.market_value) as total_assets_value
                FROM portfolios p
                LEFT JOIN portfolio_assets pa ON p.portfolio_id = pa.portfolio_id
                WHERE p.user_id = :user_id
                GROUP BY p.portfolio_id, p.user_id, p.portfolio_name, p.total_value, p.cash_balance, 
                         p.portfolio_type, p.is_primary, p.portfolio_notes, p.created_at, p.updated_at
                ORDER BY p.is_primary DESC, p.created_at DESC
                """
                
                results = conn.execute(text(query), {"user_id": user_id}).fetchall()
                
                return [dict(row._mapping) for row in results]
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get portfolios for user {user_id}: {e}")
            return []
    
    def get_portfolio_assets(self, portfolio_id: str) -> List[Dict]:
        """Get all assets in a portfolio."""
        if not self.engine:
            return []
        
        try:
            with self.engine.connect() as conn:
                query = """
                SELECT pa.*, 
                       COALESCE(s.company_name, pa.asset_name) as company_name,
                       COALESCE(pa.sector, s.sector) as sector,
                       COALESCE(pa.industry, s.industry) as industry
                FROM portfolio_assets pa
                LEFT JOIN securities s ON pa.symbol = s.symbol
                WHERE pa.portfolio_id = :portfolio_id
                ORDER BY pa.market_value DESC
                """
                
                results = conn.execute(text(query), {"portfolio_id": portfolio_id}).fetchall()
                
                return [dict(row._mapping) for row in results]
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get assets for portfolio {portfolio_id}: {e}")
            return []
    
    def create_portfolio(self, portfolio_data: Dict) -> bool:
        """Create a new portfolio record."""
        if not self.engine:
            logger.warning("Database not available - mock portfolio creation")
            return True
        
        try:
            with self.engine.connect() as conn:
                columns = list(portfolio_data.keys())
                placeholders = [f":{col}" for col in columns]
                
                insert_query = f"""
                INSERT INTO portfolios ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                """
                
                conn.execute(text(insert_query), portfolio_data)
                conn.commit()
                
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to create portfolio: {e}")
            return False

    def get_recent_transactions(self, user_id: Optional[str] = None, portfolio_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get recent transactions."""
        if not self.engine:
            return []
        
        try:
            with self.engine.connect() as conn:
                where_clauses = []
                params = {"limit": limit}
                
                if user_id:
                    where_clauses.append("t.user_id = :user_id")
                    params["user_id"] = user_id
                
                if portfolio_id:
                    where_clauses.append("t.portfolio_id = :portfolio_id")
                    params["portfolio_id"] = portfolio_id
                
                where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                
                query = f"""
                SELECT t.*, p.portfolio_name, s.company_name
                FROM transactions t
                LEFT JOIN portfolios p ON t.portfolio_id = p.portfolio_id
                LEFT JOIN securities s ON t.symbol = s.symbol
                {where_clause}
                ORDER BY t.created_at DESC
                LIMIT :limit
                """
                
                results = conn.execute(text(query), params).fetchall()
                
                return [dict(row._mapping) for row in results]
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get recent transactions: {e}")
            return []


# Create service instance
database_service = DatabaseService()
