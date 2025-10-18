"""
AI Chat Logger for MyFalconAdvisor
Logs all AI agent interactions to PostgreSQL database
"""

import os
import uuid
import time
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import subprocess

from pydantic import BaseModel, Field
from ..core.config import Config

config = Config.get_instance()
logger = logging.getLogger(__name__)


class ChatSession(BaseModel):
    """Chat session model"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_type: str = "general"  # advisory, compliance, execution, general
    status: str = "active"  # active, completed, terminated
    context_data: Optional[Dict[str, Any]] = None
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    total_messages: int = 0
    total_tokens_used: int = 0


class ChatMessage(BaseModel):
    """Chat message model"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    agent_type: str  # user, advisor, compliance, execution, supervisor
    message_type: str  # query, response, recommendation, approval_request, system
    message_content: str
    message_metadata: Optional[Dict[str, Any]] = None
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)


class PostgreSQLChatLogger:
    """PostgreSQL-based chat logger for AI interactions and trading operations"""
    
    def __init__(self):
        self.host = os.getenv("DB_HOST", "pg-2e1b40a1-falcon-horizon-5e1b-falccon.i.aivencloud.com")
        self.port = os.getenv("DB_PORT", "24382")
        self.user = os.getenv("DB_USER", "avnadmin")
        self.database = os.getenv("DB_NAME", "myfalconadvisor_db")
        self.password = os.getenv("DB_PASSWORD")
        self.current_session: Optional[ChatSession] = None
        
    def _execute_sql(self, sql: str, return_result: bool = False) -> Optional[List[Dict]]:
        """Execute SQL command using psql"""
        try:
            # Set password environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = self.password
            
            cmd = [
                "psql",
                "-h", self.host,
                "-p", self.port,
                "-U", self.user,
                "-d", self.database,
                "--set=sslmode=require",
                "-t",  # Tuples only (no headers)
                "-c", sql
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30,
                env=env
            )
            
            if result.returncode == 0:
                if return_result and result.stdout.strip():
                    # Parse simple results (for basic queries)
                    lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                    return [{"result": line} for line in lines]
                return []
            else:
                logger.error(f"SQL execution failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Database error: {e}")
            return None
    
    def _execute_sql_with_params(self, sql: str, params: tuple) -> Optional[Any]:
        """Execute SQL command with parameters using psycopg2 to avoid SQL injection"""
        if not self.password:
            logger.warning("Database password not available - skipping SQL execution")
            return True
            
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                sslmode='require'
            )
            
            with conn.cursor() as cur:
                cur.execute(sql, params)
                conn.commit()
                
                # Return results if it's a SELECT query
                if sql.strip().upper().startswith('SELECT'):
                    return cur.fetchall()
                return True
                
        except Exception as e:
            logger.error(f"Database error with params: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def start_session(self, user_id: Optional[str] = None, session_type: str = "general", 
                     context_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Start a new chat session"""
        try:
            session = ChatSession(
                user_id=user_id,
                session_type=session_type,
                context_data=context_data or {}
            )
            
            # Insert session into database using parameterized query
            context_json = json.dumps(session.context_data) if session.context_data else None
            
            # Handle user_id - create a test user UUID if string provided, otherwise NULL
            user_id_param = None
            if session.user_id and not session.user_id.startswith('test_'):
                user_id_param = session.user_id
            # For test users or no user_id, use NULL (None)
            
            sql = """
            INSERT INTO ai_sessions (
                session_id, user_id, session_type, status, context_data, 
                started_at, total_messages, total_tokens_used
            ) VALUES (
                %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 0, 0
            )
            """
            
            params = (
                session.session_id, 
                user_id_param, 
                session.session_type, 
                session.status, 
                context_json
            )
            
            result = self._execute_sql_with_params(sql, params)
            if result is not None:
                self.current_session = session
                logger.info(f"Started chat session: {session.session_id}")
                return session.session_id
            else:
                logger.error("Failed to start chat session")
                return None
                
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return None
    
    def log_message(self, agent_type: str, message_type: str, content: str,
                   session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
                   tokens_used: Optional[int] = None, processing_time_ms: Optional[int] = None) -> bool:
        """Log a chat message"""
        try:
            # Use current session if no session_id provided
            if not session_id and self.current_session:
                session_id = self.current_session.session_id
            elif not session_id:
                logger.warning("No session_id provided and no current session")
                return False
            
            message = ChatMessage(
                session_id=session_id,
                agent_type=agent_type,
                message_type=message_type,
                message_content=content,
                message_metadata=metadata,
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms
            )
            
            # Use parameterized query to avoid SQL injection
            metadata_json = json.dumps(metadata) if metadata else None
            
            sql = """
            INSERT INTO ai_messages (
                message_id, session_id, agent_type, message_type, message_content,
                message_metadata, tokens_used, processing_time_ms, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
            )
            """
            
            params = (
                message.message_id, 
                message.session_id, 
                message.agent_type,
                message.message_type, 
                content, 
                metadata_json,
                tokens_used, 
                processing_time_ms
            )
            
            result = self._execute_sql_with_params(sql, params)
            if result is not None:
                # Update session message count
                self._update_session_stats(session_id, tokens_used or 0)
                logger.debug(f"Logged message: {agent_type} -> {message_type}")
                return True
            else:
                logger.error("Failed to log message")
                return False
                
        except Exception as e:
            logger.error(f"Error logging message: {e}")
            return False
    
    def _update_session_stats(self, session_id: str, tokens_used: int):
        """Update session statistics"""
        try:
            sql = f"""
            UPDATE ai_sessions 
            SET total_messages = total_messages + 1,
                total_tokens_used = total_tokens_used + {tokens_used}
            WHERE session_id = '{session_id}';
            """
            self._execute_sql(sql)
        except Exception as e:
            logger.error(f"Error updating session stats: {e}")
    
    def end_session(self, session_id: Optional[str] = None) -> bool:
        """End a chat session"""
        try:
            if not session_id and self.current_session:
                session_id = self.current_session.session_id
            elif not session_id:
                logger.warning("No session_id provided and no current session")
                return False
            
            sql = f"""
            UPDATE ai_sessions 
            SET status = 'completed', ended_at = CURRENT_TIMESTAMP
            WHERE session_id = '{session_id}';
            """
            
            result = self._execute_sql(sql)
            if result is not None:
                if self.current_session and self.current_session.session_id == session_id:
                    self.current_session = None
                logger.info(f"Ended chat session: {session_id}")
                return True
            else:
                logger.error("Failed to end session")
                return False
                
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return False
    
    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        try:
            sql = f"""
            SELECT 
                message_id, agent_type, message_type, message_content,
                message_metadata, tokens_used, processing_time_ms, created_at
            FROM ai_messages 
            WHERE session_id = '{session_id}'
            ORDER BY created_at ASC
            LIMIT {limit};
            """
            
            result = self._execute_sql(sql, return_result=True)
            return result or []
            
        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return []
    
    def get_user_sessions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent sessions for a user"""
        try:
            sql = f"""
            SELECT 
                session_id, session_type, status, total_messages,
                total_tokens_used, started_at, ended_at
            FROM ai_sessions 
            WHERE user_id = '{user_id}'
            ORDER BY started_at DESC
            LIMIT {limit};
            """
            
            result = self._execute_sql(sql, return_result=True)
            return result or []
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []

    @contextmanager
    def session_context(self, user_id: Optional[str] = None, session_type: str = "general"):
        """Context manager for chat sessions"""
        session_id = self.start_session(user_id, session_type)
        try:
            yield session_id
        finally:
            if session_id:
                self.end_session(session_id)
    
    # New methods for trading operations
    def log_interaction(self, account_id: str, channel: str, message: str, 
                       interaction_id: Optional[str] = None) -> bool:
        """Log user interaction to interactions table"""
        try:
            if not interaction_id:
                interaction_id = f"int_{int(datetime.now().timestamp())}_{account_id}"
            
            escaped_message = message.replace("'", "''")
            
            sql = f"""
            INSERT INTO interactions (interaction_id, account_id, timestamp, channel, message)
            VALUES ('{interaction_id}', '{account_id}', CURRENT_TIMESTAMP, '{channel}', '{escaped_message}');
            """
            
            result = self._execute_sql(sql)
            if result is not None:
                logger.debug(f"Logged interaction: {interaction_id}")
                return True
            else:
                logger.error("Failed to log interaction")
                return False
                
        except Exception as e:
            logger.error(f"Error logging interaction: {e}")
            return False
    
    def log_recommendation(self, account_id: str, ticker: str, action: str, 
                          percentage: int, rationale: str, rec_id: Optional[str] = None) -> bool:
        """Log AI recommendation to recommendations table"""
        try:
            if not rec_id:
                rec_id = f"rec_{int(datetime.now().timestamp())}_{account_id}_{ticker}"
            
            escaped_rationale = rationale.replace("'", "''")
            
            sql = f"""
            INSERT INTO recommendations (rec_id, account_id, ticker, action, percentage, rationale, created_at)
            VALUES ('{rec_id}', '{account_id}', '{ticker}', '{action}', {percentage}, '{escaped_rationale}', CURRENT_TIMESTAMP);
            """
            
            result = self._execute_sql(sql)
            if result is not None:
                logger.debug(f"Logged recommendation: {rec_id}")
                return True
            else:
                logger.error("Failed to log recommendation")
                return False
                
        except Exception as e:
            logger.error(f"Error logging recommendation: {e}")
            return False
    
    # REMOVED: Unused legacy methods for orders/executions tables
    # def log_order() - Never called, system uses transactions table instead
    # def log_execution() - Never called, system uses transactions table instead
    # 
    # The system uses the transactions table as a hybrid design that combines
    # both order intent and execution results in a single record, making these
    # separate methods unnecessary.
    
    def update_position(self, account_id: str, ticker: str, sector: str, 
                       quantity: int, avg_cost: float) -> bool:
        """Update position in positions table"""
        try:
            # Use UPSERT (INSERT ... ON CONFLICT)
            sql = f"""
            INSERT INTO positions (account_id, ticker, sector, quantity, avg_cost)
            VALUES ('{account_id}', '{ticker}', '{sector}', {quantity}, {avg_cost})
            ON CONFLICT (account_id, ticker) 
            DO UPDATE SET 
                sector = EXCLUDED.sector,
                quantity = EXCLUDED.quantity,
                avg_cost = EXCLUDED.avg_cost;
            """
            
            result = self._execute_sql(sql)
            if result is not None:
                logger.debug(f"Updated position: {account_id} {ticker}")
                return True
            else:
                logger.error("Failed to update position")
                return False
                
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            return False


# Global chat logger instance
chat_logger = PostgreSQLChatLogger()


# Convenience functions for different agent types
def log_user_message(content: str, session_id: Optional[str] = None, 
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Log a user message"""
    return chat_logger.log_message("user", "query", content, session_id, metadata)


def log_advisor_response(content: str, session_id: Optional[str] = None,
                        tokens_used: Optional[int] = None, processing_time_ms: Optional[int] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Log an advisor agent response"""
    return chat_logger.log_message("advisor", "response", content, session_id, 
                                  metadata, tokens_used, processing_time_ms)


def log_compliance_check(content: str, session_id: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Log a compliance check"""
    return chat_logger.log_message("compliance", "system", content, session_id, metadata)


def log_execution_request(content: str, session_id: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Log an execution request"""
    return chat_logger.log_message("execution", "approval_request", content, session_id, metadata)


def log_supervisor_action(content: str, session_id: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Log a supervisor action"""
    return chat_logger.log_message("supervisor", "system", content, session_id, metadata)


# Convenience functions for trading operations
def log_user_interaction(account_id: str, message: str, channel: str = "web") -> bool:
    """Log a user interaction to interactions table"""
    return chat_logger.log_interaction(account_id, channel, message)

def log_ai_recommendation(account_id: str, ticker: str, action: str, 
                         percentage: int, rationale: str) -> bool:
    """Log an AI recommendation"""
    return chat_logger.log_recommendation(account_id, ticker, action, percentage, rationale)

# Removed unused wrapper functions:
# - log_trade_order() - Never called in codebase
# - log_trade_execution() - Never called in codebase
# These were redundant wrappers for chat_logger.log_order() and chat_logger.log_execution()
# which are also unused since the system uses transactions table instead of orders/executions

def update_account_position(account_id: str, ticker: str, sector: str, 
                           quantity: int, avg_cost: float) -> bool:
    """Update account position"""
    return chat_logger.update_position(account_id, ticker, sector, quantity, avg_cost)

# Decorator for automatic logging
def log_ai_interaction(agent_type: str, message_type: str = "response"):
    """Decorator to automatically log AI interactions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Execute the function
            result = func(*args, **kwargs)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Log the interaction
            if hasattr(result, 'get') and result.get('response'):
                content = result['response']
            elif isinstance(result, str):
                content = result
            else:
                content = str(result)
            
            # Extract metadata from kwargs
            metadata = {
                'function_name': func.__name__,
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            }
            
            chat_logger.log_message(
                agent_type=agent_type,
                message_type=message_type,
                content=content,
                metadata=metadata,
                processing_time_ms=processing_time_ms
            )
            
            return result
        return wrapper
    return decorator
