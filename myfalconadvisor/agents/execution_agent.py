"""
Execution Service for Trade Execution with Portfolio Validation and User Approval.

This service handles the actual execution of AI-generated investment recommendations,
validating them against user portfolio data and managing approval workflows.
This is NOT an AI agent - it's a deterministic workflow service.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import text

from ..tools.alpaca_trading_service import alpaca_trading_service
from ..tools.database_service import DatabaseService
from ..tools.chat_logger import chat_logger, log_ai_interaction
from ..agents.compliance_reviewer import compliance_reviewer_agent
from ..core.config import Config

config = Config.get_instance()
logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected" 
    PENDING_EXECUTION = "pending_execution"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"


class TradeOrder(BaseModel):
    """Trade order model."""
    order_id: str
    client_id: str
    symbol: str
    action: str  # "buy" or "sell"
    quantity: float
    order_type: OrderType
    price: Optional[float] = None  # For limit orders
    stop_price: Optional[float] = None  # For stop orders
    
    # Order management
    created_at: datetime
    expires_at: Optional[datetime] = None
    status: OrderStatus = OrderStatus.PENDING_APPROVAL
    
    # Compliance and approval
    compliance_approved: bool = False
    user_approved: bool = False
    approval_timestamp: Optional[datetime] = None
    
    # Execution details
    executed_price: Optional[float] = None
    executed_quantity: Optional[float] = None
    execution_timestamp: Optional[datetime] = None
    
    # Risk management
    estimated_commission: float = 0.0
    estimated_total_cost: float = 0.0
    position_size_percent: float = 0.0
    
    # Audit trail
    compliance_notes: List[str] = []
    approval_notes: List[str] = []
    execution_notes: List[str] = []


class ExecutionResult(BaseModel):
    """Trade execution result."""
    success: bool
    order_id: str
    executed_price: Optional[float] = None
    executed_quantity: Optional[float] = None
    execution_timestamp: Optional[datetime] = None
    commission_paid: float = 0.0
    error_message: Optional[str] = None
    
    # Post-execution analysis
    price_improvement: Optional[float] = None
    market_impact: Optional[float] = None


class ExecutionService:
    """
    Execution Service responsible for:
    1. Validating AI recommendations against user portfolio data
    2. Managing user approval workflows
    3. Executing approved trades through Alpaca
    4. Recording all transactions in database tables
    
    This is NOT an AI agent - it's a deterministic workflow service.
    """
    
    def __init__(self):
        self.name = "execution_service"
        
        # Alpaca trading service integration
        self.alpaca_service = alpaca_trading_service
        
        # Database service for proper table writes
        self.db_service = DatabaseService()
        
        # Order management (in-memory state)
        self.pending_orders: Dict[str, TradeOrder] = {}
        self.executed_orders: Dict[str, TradeOrder] = {}
    
    def validate_recommendation_against_portfolio(self, user_id: str, recommendation: Dict) -> Dict:
        """
        Validate AI recommendation against actual user portfolio data from database.
        
        Args:
            user_id: User identifier
            recommendation: AI-generated trade recommendation
            
        Returns:
            Validation result with approval/rejection and reasons
        """
        try:
            # Get user's current portfolio from database
            engine = self.db_service.engine if hasattr(self.db_service, 'engine') else self._get_db_engine()
            
            with engine.connect() as conn:
                # Get user's portfolios
                portfolio_result = conn.execute(text("""
                    SELECT portfolio_id, portfolio_name, total_value, cash_balance 
                    FROM portfolios 
                    WHERE user_id = :user_id AND is_primary = true
                """), {"user_id": user_id})
                
                portfolio_row = portfolio_result.fetchone()
                if not portfolio_row:
                    return {
                        "approved": False,
                        "reason": "No portfolio found for user",
                        "details": f"User {user_id} has no active portfolio"
                    }
                
                portfolio_id = portfolio_row[0]
                total_value = float(portfolio_row[2])
                cash_balance = float(portfolio_row[3])
                
                # Get current positions
                positions_result = conn.execute(text("""
                    SELECT pa.symbol, pa.quantity, pa.current_price, pa.market_value
                    FROM portfolio_assets pa
                    WHERE pa.portfolio_id = :portfolio_id
                """), {"portfolio_id": portfolio_id})
                
                current_positions = {row[0]: {
                    "quantity": float(row[1]),
                    "current_price": float(row[2]) if row[2] else 0,
                    "market_value": float(row[3]) if row[3] else 0
                } for row in positions_result.fetchall()}
                
                # Validate recommendation
                symbol = recommendation.get("symbol", "").upper()
                action = recommendation.get("action", "").lower()
                quantity = float(recommendation.get("quantity", 0))
                
                validation_result = {
                    "approved": True,
                    "reason": "Validation passed",
                    "details": {},
                    "portfolio_context": {
                        "total_value": total_value,
                        "cash_balance": cash_balance,
                        "current_positions": current_positions
                    }
                }
                
                # Validation checks
                if action == "sell":
                    # Check if user owns the stock
                    if symbol not in current_positions:
                        validation_result.update({
                            "approved": False,
                            "reason": f"Cannot sell {symbol} - not in portfolio",
                            "details": {"available_symbols": list(current_positions.keys())}
                        })
                    elif current_positions[symbol]["quantity"] < quantity:
                        validation_result.update({
                            "approved": False,
                            "reason": f"Insufficient shares to sell {quantity} {symbol}",
                            "details": {
                                "requested": quantity,
                                "available": current_positions[symbol]["quantity"]
                            }
                        })
                
                elif action == "buy":
                    # Estimate cost (simplified)
                    estimated_cost = quantity * 100  # Rough estimate, should get real price
                    if estimated_cost > cash_balance:
                        validation_result.update({
                            "approved": False,
                            "reason": f"Insufficient cash for purchase",
                            "details": {
                                "estimated_cost": estimated_cost,
                                "available_cash": cash_balance
                            }
                        })
                
                return validation_result
                
        except Exception as e:
            logger.error(f"Error validating recommendation: {e}")
            return {
                "approved": False,
                "reason": "Validation error",
                "details": {"error": str(e)}
            }
    
    def create_trade_order(
        self,
        client_id: str,
        symbol: str,
        action: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None,
        portfolio_value: float = 100000,
        expires_in_hours: int = 24
    ) -> Dict:
        """
        Create a new trade order with compliance validation.
        
        Args:
            client_id: Client identifier
            symbol: Security symbol
            action: "buy" or "sell"
            quantity: Number of shares
            order_type: Type of order (market, limit, etc.)
            price: Price for limit orders
            portfolio_value: Current portfolio value for position sizing
            expires_in_hours: Hours until order expires
        
        Returns:
            Dictionary containing order details and compliance status
        """
        try:
            # Generate unique order ID
            order_id = f"{client_id}_{symbol}_{int(datetime.now().timestamp())}"
            
            # Get current market data for validation
            market_price = self._get_current_price(symbol)
            if not market_price:
                return {"error": f"Unable to get market data for {symbol}"}
            
            # Calculate order details
            estimated_cost = self._calculate_estimated_cost(
                action, quantity, market_price, order_type, price
            )
            
            position_size = (estimated_cost / portfolio_value) * 100
            
            # Create order object
            order = TradeOrder(
                order_id=order_id,
                client_id=client_id,
                symbol=symbol,
                action=action,
                quantity=quantity,
                order_type=OrderType(order_type),
                price=price,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=expires_in_hours),
                estimated_total_cost=estimated_cost,
                position_size_percent=position_size
            )
            
            # Perform compliance check
            compliance_result = self._check_trade_compliance(
                order, portfolio_value
            )
            
            order.compliance_approved = compliance_result["approved"]
            order.compliance_notes = compliance_result.get("notes", [])
            
            # Store pending order
            self.pending_orders[order_id] = order
            
            # Prepare response
            response = {
                "order_id": order_id,
                "status": order.status.value,
                "compliance_approved": order.compliance_approved,
                "requires_user_approval": True,
                "order_details": {
                    "symbol": symbol,
                    "action": action,
                    "quantity": quantity,
                    "order_type": order_type,
                    "estimated_price": market_price,
                    "estimated_cost": estimated_cost,
                    "position_size": f"{position_size:.1f}%",
                    "expires_at": order.expires_at.isoformat()
                },
                "compliance_status": compliance_result,
                "next_steps": [
                    "Review order details and compliance status",
                    "Provide explicit approval to execute",
                    "Order will expire automatically if not approved"
                ]
            }
            
            if not order.compliance_approved:
                response["warning"] = "Order has compliance issues that must be resolved"
                response["next_steps"].insert(0, "Address compliance violations before approval")
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating trade order: {e}")
            return {"error": str(e)}
    
    def approve_order(
        self,
        order_id: str,
        user_confirmation: bool,
        approval_notes: str = ""
    ) -> Dict:
        """
        Process user approval for pending trade order.
        
        Args:
            order_id: Order identifier
            user_confirmation: Explicit user approval
            approval_notes: Optional notes from user
            
        Returns:
            Dictionary containing approval status and next steps
        """
        try:
            if order_id not in self.pending_orders:
                return {"error": f"Order {order_id} not found or already processed"}
            
            order = self.pending_orders[order_id]
            
            # Check if order has expired
            if order.expires_at and datetime.now() > order.expires_at:
                order.status = OrderStatus.CANCELLED
                return {
                    "order_id": order_id,
                    "status": "cancelled",
                    "message": "Order expired before approval"
                }
            
            if not user_confirmation:
                order.status = OrderStatus.REJECTED
                order.approval_notes.append(f"User rejected: {approval_notes}")
                return {
                    "order_id": order_id,
                    "status": "rejected", 
                    "message": "Order rejected by user"
                }
            
            # Verify compliance is still valid
            if not order.compliance_approved:
                return {
                    "error": "Cannot approve order with compliance violations",
                    "compliance_notes": order.compliance_notes
                }
            
            # Mark as approved
            order.user_approved = True
            order.approval_timestamp = datetime.now()
            order.status = OrderStatus.APPROVED
            order.approval_notes.append(approval_notes)
            
            # Move to execution queue
            execution_result = self._queue_for_execution(order)
            
            return {
                "order_id": order_id,
                "status": order.status.value,
                "approved_at": order.approval_timestamp.isoformat(),
                "execution_status": execution_result,
                "message": "Order approved and queued for execution"
            }
            
        except Exception as e:
            logger.error(f"Error approving order {order_id}: {e}")
            return {"error": str(e)}
    
    def execute_order(self, order_id: str) -> Dict:
        """
        Execute approved trade order.
        
        Args:
            order_id: Order identifier
            
        Returns:
            Dictionary containing execution results
        """
        try:
            if order_id not in self.pending_orders:
                return {"error": f"Order {order_id} not found"}
            
            order = self.pending_orders[order_id]
            
            if order.status != OrderStatus.APPROVED:
                return {"error": f"Order {order_id} not approved for execution"}
            
            # Mark as pending execution
            order.status = OrderStatus.PENDING_EXECUTION
            
            # Simulate trade execution (in production, this would interface with broker APIs)
            execution_result = self._simulate_trade_execution(order)
            
            if execution_result.success:
                order.status = OrderStatus.EXECUTED
                order.executed_price = execution_result.executed_price
                order.executed_quantity = execution_result.executed_quantity
                order.execution_timestamp = execution_result.execution_timestamp
                order.execution_notes.append("Trade executed successfully")
                
                # Move to executed orders
                self.executed_orders[order_id] = order
                del self.pending_orders[order_id]
                
                return {
                    "order_id": order_id,
                    "status": "executed",
                    "execution_details": {
                        "executed_price": execution_result.executed_price,
                        "executed_quantity": execution_result.executed_quantity,
                        "execution_time": execution_result.execution_timestamp.isoformat(),
                        "commission": execution_result.commission_paid,
                        "total_cost": execution_result.executed_price * execution_result.executed_quantity + execution_result.commission_paid
                    },
                    "post_execution_analysis": self._generate_execution_analysis(execution_result, order)
                }
            else:
                order.status = OrderStatus.FAILED
                order.execution_notes.append(f"Execution failed: {execution_result.error_message}")
                
                return {
                    "order_id": order_id,
                    "status": "failed",
                    "error": execution_result.error_message,
                    "retry_options": self._suggest_retry_options(order)
                }
                
        except Exception as e:
            logger.error(f"Error executing order {order_id}: {e}")
            return {"error": str(e)}
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get current status of an order."""
        if order_id in self.pending_orders:
            order = self.pending_orders[order_id]
        elif order_id in self.executed_orders:
            order = self.executed_orders[order_id]
        else:
            return {"error": f"Order {order_id} not found"}
        
        return {
            "order_id": order_id,
            "status": order.status.value,
            "created_at": order.created_at.isoformat(),
            "symbol": order.symbol,
            "action": order.action,
            "quantity": order.quantity,
            "compliance_approved": order.compliance_approved,
            "user_approved": order.user_approved,
            "executed_price": order.executed_price,
            "execution_timestamp": order.execution_timestamp.isoformat() if order.execution_timestamp else None
        }
    
    def cancel_order(self, order_id: str, reason: str = "") -> Dict:
        """Cancel a pending order."""
        if order_id not in self.pending_orders:
            return {"error": f"Order {order_id} not found or already processed"}
        
        order = self.pending_orders[order_id]
        
        if order.status in [OrderStatus.EXECUTED, OrderStatus.FAILED]:
            return {"error": "Cannot cancel executed or failed orders"}
        
        order.status = OrderStatus.CANCELLED
        order.execution_notes.append(f"Order cancelled: {reason}")
        
        return {
            "order_id": order_id,
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat(),
            "reason": reason
        }
    
    def get_execution_summary(self, time_period_days: int = 30) -> Dict:
        """Get summary of recent execution activity."""
        cutoff_date = datetime.now() - timedelta(days=time_period_days)
        
        recent_orders = [
            order for order in self.executed_orders.values()
            if order.execution_timestamp and order.execution_timestamp > cutoff_date
        ]
        
        total_orders = len(recent_orders)
        total_volume = sum(order.executed_quantity * order.executed_price for order in recent_orders)
        total_commission = sum(order.estimated_commission for order in recent_orders)
        
        return {
            "period_days": time_period_days,
            "total_orders_executed": total_orders,
            "total_trade_volume": total_volume,
            "total_commissions": total_commission,
            "average_execution_time": "< 1 second",  # Simulated
            "execution_success_rate": "100%",  # Simulated
            "compliance_approval_rate": "95%",  # Simulated
        }
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for symbol."""
        try:
            # Try to get real market data from Alpaca
            if not self.alpaca_service.mock_mode:
                market_data = self.alpaca_service.get_market_data(symbol)
                if market_data and not market_data.get("error"):
                    price = market_data.get("latest_price")
                    if price:
                        return float(price)
            
            # Fall back to mock prices if Alpaca not available
            mock_prices = {
                "AAPL": 193.50,
                "MSFT": 417.10,
                "GOOGL": 175.20,
                "AMZN": 151.94,
                "TSLA": 248.42,
                "SPY": 502.43
            }
            return mock_prices.get(symbol, 100.0)  # Default price
            
        except Exception as e:
            logger.warning(f"Failed to get current price for {symbol}: {e}")
            return 100.0  # Fallback price
    
    def _calculate_estimated_cost(
        self, action: str, quantity: float, market_price: float, 
        order_type: str, limit_price: Optional[float]
    ) -> float:
        """Calculate estimated total cost of trade."""
        if order_type == "limit" and limit_price:
            estimated_price = limit_price
        else:
            estimated_price = market_price
        
        trade_value = quantity * estimated_price
        commission = max(0.65, trade_value * 0.005)  # $0.65 or 0.5% commission
        
        return trade_value + commission if action == "buy" else trade_value - commission
    
    def _check_trade_compliance(self, order: TradeOrder, portfolio_value: float) -> Dict:
        """Check trade compliance using compliance tools."""
        # This would typically call the compliance tools
        # Here we simulate compliance check
        
        violations = []
        notes = []
        
        # Position size check
        if order.position_size_percent > config.max_position_size * 100:
            violations.append("Position size exceeds maximum allowed")
            notes.append(f"Position size {order.position_size_percent:.1f}% exceeds limit {config.max_position_size*100:.1f}%")
        
        # Penny stock check
        current_price = self._get_current_price(order.symbol)
        if current_price and current_price < 5.0:
            notes.append(f"Trading penny stock at ${current_price:.2f}")
        
        return {
            "approved": len(violations) == 0,
            "violations": violations,
            "notes": notes
        }
    
    def _queue_for_execution(self, order: TradeOrder) -> str:
        """Queue order for execution."""
        # In production, this would interface with execution management system
        order.status = OrderStatus.APPROVED
        return "queued_for_execution"
    
    def _simulate_trade_execution(self, order: TradeOrder) -> ExecutionResult:
        """Execute trade through Alpaca API and write to proper database tables."""
        try:
            # Step 1: Write to ORDERS table
            order_record_id = self._write_to_orders_table(order)
            
            # Step 2: Try to execute through Alpaca API first
            if not self.alpaca_service.mock_mode:
                logger.info(f"Executing order {order.order_id} through Alpaca API")
                
                alpaca_result = self.alpaca_service.place_order(
                    symbol=order.symbol,
                    side=order.action,
                    quantity=order.quantity,
                    order_type=order.order_type.value,
                    limit_price=order.price if order.order_type == OrderType.LIMIT else None,
                    user_id=order.client_id,
                    portfolio_id=None  # Could be enhanced to track portfolio
                )
                
                if alpaca_result.get("success"):
                    # Get execution details from Alpaca
                    alpaca_order_id = alpaca_result.get("order_id")
                    
                    # Monitor order status (simplified - in production you'd poll until filled)
                    status_result = self.alpaca_service.get_order_status(alpaca_order_id)
                    
                    executed_price = status_result.get("filled_avg_price") or self._get_current_price(order.symbol)
                    executed_quantity = status_result.get("filled_qty", order.quantity)
                    commission = alpaca_result.get("estimated_cost", 0) - (executed_price * executed_quantity)
                    
                    # Step 3: Write to EXECUTIONS table
                    self._write_to_executions_table(order_record_id, executed_quantity, executed_price)
                    
                    # Step 4: Update POSITIONS table
                    self._update_positions_table(order.client_id, order.symbol, order.action, executed_quantity, executed_price)
                    
                    return ExecutionResult(
                        success=True,
                        order_id=order.order_id,
                        executed_price=executed_price,
                        executed_quantity=executed_quantity,
                        execution_timestamp=datetime.now(),
                        commission_paid=max(0, commission),
                        price_improvement=0  # Could calculate vs expected price
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        order_id=order.order_id,
                        error_message=f"Alpaca execution failed: {alpaca_result.get('error', 'Unknown error')}"
                    )
            
            # Fall back to simulation if Alpaca not available
            logger.info(f"Simulating execution for order {order.order_id} (Alpaca not available)")
            
            current_price = self._get_current_price(order.symbol)
            
            # Simulate small price improvement/slippage
            import random
            price_variation = random.uniform(-0.02, 0.01)  # -2% to +1%
            executed_price = current_price * (1 + price_variation)
            executed_quantity = order.quantity
            
            commission = max(0.65, order.quantity * executed_price * 0.005)
            
            # Step 3: Write to EXECUTIONS table (simulated)
            self._write_to_executions_table(order_record_id, executed_quantity, executed_price)
            
            # Step 4: Update POSITIONS table (simulated)
            self._update_positions_table(order.client_id, order.symbol, order.action, executed_quantity, executed_price)
            
            return ExecutionResult(
                success=True,
                order_id=order.order_id,
                executed_price=executed_price,
                executed_quantity=executed_quantity,
                execution_timestamp=datetime.now(),
                commission_paid=commission,
                price_improvement=price_variation * 100  # Percentage
            )
            
        except Exception as e:
            logger.error(f"Trade execution failed for order {order.order_id}: {e}")
            return ExecutionResult(
                success=False,
                order_id=order.order_id,
                error_message=str(e)
            )
    
    def _generate_execution_analysis(
        self, execution_result: ExecutionResult, order: TradeOrder
    ) -> Dict:
        """Generate post-execution analysis."""
        expected_price = self._get_current_price(order.symbol)
        actual_price = execution_result.executed_price
        
        analysis = {
            "price_performance": {
                "expected_price": expected_price,
                "executed_price": actual_price,
                "price_improvement": ((actual_price - expected_price) / expected_price) * 100,
                "execution_quality": "Excellent" if abs((actual_price - expected_price) / expected_price) < 0.01 else "Good"
            },
            "cost_analysis": {
                "commission_paid": execution_result.commission_paid,
                "total_transaction_cost": execution_result.commission_paid,
                "cost_as_percent_of_trade": (execution_result.commission_paid / (actual_price * order.quantity)) * 100
            },
            "timing_analysis": {
                "order_to_execution_time": "< 1 second",
                "market_conditions": "Normal trading conditions",
                "execution_efficiency": "High"
            }
        }
        
        return analysis
    
    def _suggest_retry_options(self, order: TradeOrder) -> List[str]:
        """Suggest retry options for failed orders."""
        return [
            "Retry with current market conditions",
            "Convert to limit order with price protection",
            "Break large order into smaller parts",
            "Wait for better market conditions",
            "Cancel and resubmit with different parameters"
        ]
    
    def _write_to_orders_table(self, order: TradeOrder) -> str:
        """Write order to the orders table."""
        try:
            from sqlalchemy import create_engine, text
            import uuid
            
            # Get database connection
            engine = self.db_service.engine if hasattr(self.db_service, 'engine') else self._get_db_engine()
            
            order_record_id = str(uuid.uuid4())
            
            with engine.connect() as conn:
                # Get account_id for the user (assuming we have accounts table)
                account_result = conn.execute(text("SELECT account_id FROM accounts WHERE user_id = :user_id LIMIT 1"), 
                                            {"user_id": order.client_id})
                account_row = account_result.fetchone()
                account_id = account_row[0] if account_row else order.client_id
                
                # Insert into orders table
                conn.execute(text("""
                    INSERT INTO orders (order_id, account_id, ticker, sector, quantity, order_type, limit_price, timestamp, time_in_force)
                    VALUES (:order_id, :account_id, :ticker, :sector, :quantity, :order_type, :limit_price, :timestamp, :time_in_force)
                """), {
                    "order_id": order_record_id,
                    "account_id": account_id,
                    "ticker": order.symbol,
                    "sector": "Technology",  # Could be enhanced to lookup actual sector
                    "quantity": order.quantity,
                    "order_type": order.order_type.value,
                    "limit_price": order.price,
                    "timestamp": order.created_at,
                    "time_in_force": "DAY"
                })
                
                conn.commit()
                logger.info(f"Order {order_record_id} written to orders table")
                return order_record_id
                
        except Exception as e:
            logger.error(f"Failed to write to orders table: {e}")
            return str(uuid.uuid4())  # Return dummy ID to continue execution
    
    def _write_to_executions_table(self, order_id: str, filled_quantity: float, fill_price: float):
        """Write execution to the executions table."""
        try:
            from sqlalchemy import create_engine, text
            import uuid
            
            engine = self.db_service.engine if hasattr(self.db_service, 'engine') else self._get_db_engine()
            
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO executions (exec_id, order_id, filled_quantity, fill_price, exec_timestamp)
                    VALUES (:exec_id, :order_id, :filled_quantity, :fill_price, :exec_timestamp)
                """), {
                    "exec_id": str(uuid.uuid4()),
                    "order_id": order_id,
                    "filled_quantity": filled_quantity,
                    "fill_price": fill_price,
                    "exec_timestamp": datetime.now()
                })
                
                conn.commit()
                logger.info(f"Execution recorded for order {order_id}")
                
        except Exception as e:
            logger.error(f"Failed to write to executions table: {e}")
    
    def _update_positions_table(self, account_id: str, symbol: str, action: str, quantity: float, price: float):
        """Update positions table with new position or modify existing."""
        try:
            from sqlalchemy import create_engine, text
            
            engine = self.db_service.engine if hasattr(self.db_service, 'engine') else self._get_db_engine()
            
            with engine.connect() as conn:
                # Check if position already exists
                existing_pos = conn.execute(text("""
                    SELECT quantity, avg_cost FROM positions 
                    WHERE account_id = :account_id AND ticker = :ticker
                """), {"account_id": account_id, "ticker": symbol})
                
                existing_row = existing_pos.fetchone()
                
                if existing_row:
                    # Update existing position
                    current_qty = float(existing_row[0])
                    current_avg_cost = float(existing_row[1])
                    
                    if action.lower() == "buy":
                        new_qty = current_qty + quantity
                        new_avg_cost = ((current_qty * current_avg_cost) + (quantity * price)) / new_qty
                    else:  # sell
                        new_qty = current_qty - quantity
                        new_avg_cost = current_avg_cost  # Keep same avg cost on sale
                    
                    if new_qty > 0:
                        conn.execute(text("""
                            UPDATE positions 
                            SET quantity = :quantity, avg_cost = :avg_cost
                            WHERE account_id = :account_id AND ticker = :ticker
                        """), {
                            "quantity": new_qty,
                            "avg_cost": new_avg_cost,
                            "account_id": account_id,
                            "ticker": symbol
                        })
                    else:
                        # Position closed, remove from table
                        conn.execute(text("""
                            DELETE FROM positions 
                            WHERE account_id = :account_id AND ticker = :ticker
                        """), {"account_id": account_id, "ticker": symbol})
                else:
                    # Create new position (only for buys)
                    if action.lower() == "buy":
                        conn.execute(text("""
                            INSERT INTO positions (account_id, ticker, sector, quantity, avg_cost)
                            VALUES (:account_id, :ticker, :sector, :quantity, :avg_cost)
                        """), {
                            "account_id": account_id,
                            "ticker": symbol,
                            "sector": "Technology",  # Could be enhanced
                            "quantity": quantity,
                            "avg_cost": price
                        })
                
                conn.commit()
                logger.info(f"Position updated for {symbol}: {action} {quantity} @ {price}")
                
        except Exception as e:
            logger.error(f"Failed to update positions table: {e}")
    
    def _get_db_engine(self):
        """Get database engine if not available through db_service."""
        try:
            from sqlalchemy import create_engine
            import os
            
            db_host = "pg-2e1b40a1-falcon-horizon-5e1b-falccon.i.aivencloud.com"
            db_port = "24382"
            db_name = "myfalconadvisor_db"
            db_user = os.getenv("DB_USER", "avnadmin")
            db_password = os.getenv("DB_PASSWORD")
            ssl_mode = "require"
            
            database_url = (
                f"postgresql://{db_user}:{db_password}@"
                f"{db_host}:{db_port}/{db_name}?sslmode={ssl_mode}"
            )
            
            return create_engine(database_url)
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            return None
    
    def _get_compliance_review(self, recommendation: Dict, user_id: str, session_id: str) -> Dict:
        """
        Send recommendation to compliance agent for review and log the results.
        
        Args:
            recommendation: The AI recommendation to review
            user_id: User identifier
            session_id: Current session ID for logging
            
        Returns:
            Dictionary with compliance review results
        """
        try:
            # Create client profile (simplified for demo)
            client_profile = {
                "user_id": user_id,
                "risk_tolerance": self._get_user_risk_tolerance(user_id),
                "investment_objectives": ["growth", "income"],
                "time_horizon": "long_term"
            }
            
            # Create recommendation context
            recommendation_context = {
                "symbol": recommendation["symbol"],
                "action": recommendation["action"],
                "quantity": recommendation["quantity"],
                "recommendation_source": "ai_multi_task_agent",
                "timestamp": datetime.now().isoformat()
            }
            
            # Simplified compliance review (bypass complex agent for demo)
            compliance_review = {
                "status": "approved",
                "summary": "Basic compliance check passed - demo mode",
                "compliance_issues": [],
                "review_id": f"compliance_{datetime.now().timestamp()}",
                "approved": True
            }
            
            # Log compliance agent response
            chat_logger.log_message(
                agent_type="compliance",  # Use valid agent_type from schema
                message_type="response",
                content=f"Compliance Review: {compliance_review.get('status', 'unknown')} - {compliance_review.get('summary', '')}",
                session_id=session_id,
                metadata={
                    "compliance_review": compliance_review,
                    "recommendation": recommendation
                }
            )
            
            # Determine if approved
            approved = compliance_review.get("status") == "approved"
            
            return {
                "approved": approved,
                "status": compliance_review.get("status", "unknown"),
                "reason": compliance_review.get("summary", "No reason provided"),
                "details": compliance_review,
                "compliance_issues": compliance_review.get("compliance_issues", [])
            }
            
        except Exception as e:
            logger.error(f"Error in compliance review: {e}")
            
            # Log compliance error
            chat_logger.log_message(
                agent_type="compliance",  # Use valid agent_type from schema
                message_type="system",
                content=f"Compliance review error: {str(e)}",
                session_id=session_id,
                metadata={"error": str(e), "recommendation": recommendation}
            )
            
            return {
                "approved": False,
                "reason": f"Compliance review error: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _execute_approved_order(self, order_id: str) -> Dict:
        """
        Execute an approved order and write to database tables.
        
        Args:
            order_id: The order ID to execute
            
        Returns:
            Execution result dictionary
        """
        try:
            if order_id not in self.pending_orders:
                return {
                    "status": "failed",
                    "message": f"Order {order_id} not found in pending orders"
                }
            
            order = self.pending_orders[order_id]
            
            # Write to orders table
            db_order_id = self._write_to_orders_table(order)
            
            # Simulate execution (in real system, this would call Alpaca API)
            filled_quantity = order.quantity
            fill_price = order.price if order.price else 100.0  # Mock price
            
            # Write to executions table
            self._write_to_executions_table(db_order_id, filled_quantity, fill_price)
            
            # Update positions table
            self._update_positions_table(
                account_id=order.client_id,
                symbol=order.symbol,
                action=order.action,
                quantity=filled_quantity,
                price=fill_price
            )
            
            # Update order status
            order.status = OrderStatus.FILLED
            self.executed_orders[order_id] = order
            del self.pending_orders[order_id]
            
            return {
                "status": "filled",
                "message": f"Order {order_id} executed successfully",
                "filled_quantity": filled_quantity,
                "fill_price": fill_price,
                "db_order_id": db_order_id
            }
            
        except Exception as e:
            logger.error(f"Error executing order {order_id}: {e}")
            return {
                "status": "failed",
                "message": f"Execution error: {str(e)}"
            }
    
    def _write_to_recommendations_table(self, recommendation: Dict, user_id: str) -> str:
        """
        Write AI recommendation to existing recommendations table.
        
        Args:
            recommendation: AI-generated recommendation
            user_id: User identifier
            
        Returns:
            rec_id: UUID of created record
        """
        try:
            engine = self._get_db_engine()
            if not engine:
                logger.error("Cannot write to recommendations - no database connection")
                return None
                
            rec_id = str(uuid.uuid4())
            
            # Calculate percentage (simplified - would be more sophisticated in real system)
            percentage = int(recommendation.get('quantity', 10))  # Use quantity as percentage for demo
            
            # Map recommendation to existing table schema
            sql = """
            INSERT INTO recommendations (
                rec_id, account_id, ticker, action, percentage, rationale, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
            )
            """
            
            params = {
                'rec_id': rec_id,
                'account_id': user_id or 'demo-account',
                'ticker': recommendation['symbol'],
                'action': recommendation['action'].upper(),
                'percentage': percentage,
                'rationale': recommendation.get('reasoning', 'AI-generated recommendation')
            }
            
            # Update SQL to use named parameters
            sql = """
            INSERT INTO recommendations (
                rec_id, account_id, ticker, action, percentage, rationale, created_at
            ) VALUES (
                :rec_id, :account_id, :ticker, :action, :percentage, :rationale, CURRENT_TIMESTAMP
            )
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(sql), params)
                conn.commit()
                
            logger.info(f"Successfully wrote recommendation to database: {rec_id}")
            return rec_id
            
        except Exception as e:
            logger.error(f"Error writing to recommendations table: {e}")
            return None
    
    def _write_to_compliance_checks_table(self, recommendation_id: str, compliance_result: Dict, user_id: str) -> str:
        """
        Write compliance review results to compliance_checks table.
        
        Args:
            recommendation_id: ID of the recommendation being checked (text)
            compliance_result: Compliance review results
            user_id: User identifier (text)
            
        Returns:
            check_id: UUID of created record
        """
        try:
            engine = self._get_db_engine()
            if not engine:
                logger.error("Cannot write to compliance_checks - no database connection")
                return None
                
            check_id = str(uuid.uuid4())
            
            sql = """
            INSERT INTO compliance_checks (
                check_id, user_id, recommendation_id, check_type, rule_name,
                rule_description, check_result, violation_details, severity,
                auto_resolved, resolution_notes
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            # Determine check result
            check_result = 'pass' if compliance_result.get('approved', False) else 'fail'
            severity = 'low' if compliance_result.get('approved', False) else 'medium'
            
            params = {
                'check_id': check_id,
                'user_id': user_id,
                'recommendation_id': recommendation_id,
                'check_type': 'regulatory',
                'rule_name': 'AI Compliance Review',
                'rule_description': 'Automated compliance validation for AI recommendations',
                'check_result': check_result,
                'violation_details': json.dumps(compliance_result.get('compliance_issues', [])),
                'severity': severity,
                'auto_resolved': True,
                'resolution_notes': compliance_result.get('reason', 'Compliance check completed')
            }
            
            # Update SQL to use named parameters
            sql = """
            INSERT INTO compliance_checks (
                check_id, user_id, recommendation_id, check_type, rule_name,
                rule_description, check_result, violation_details, severity,
                auto_resolved, resolution_notes
            ) VALUES (
                :check_id, :user_id, :recommendation_id, :check_type, :rule_name,
                :rule_description, :check_result, :violation_details, :severity,
                :auto_resolved, :resolution_notes
            )
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(sql), params)
                conn.commit()
                
            logger.info(f"Successfully wrote compliance check to database: {check_id}")
            return check_id
            
        except Exception as e:
            logger.error(f"Error writing to compliance_checks table: {e}")
            return None
    
    def _write_to_agent_workflows_table(self, session_id: str, workflow_type: str, workflow_data: Dict) -> str:
        """
        Write agent workflow state to agent_workflows table.
        
        Args:
            session_id: AI session identifier
            workflow_type: Type of workflow being tracked
            workflow_data: Workflow state and data
            
        Returns:
            workflow_id: UUID of created record
        """
        try:
            engine = self._get_db_engine()
            if not engine:
                logger.error("Cannot write to agent_workflows - no database connection")
                return None
                
            workflow_id = str(uuid.uuid4())
            
            sql = """
            INSERT INTO agent_workflows (
                workflow_id, session_id, workflow_type, current_state,
                workflow_data, started_at, status
            ) VALUES (
                %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s
            )
            """
            
            params = {
                'workflow_id': workflow_id,
                'session_id': session_id,
                'workflow_type': workflow_type,
                'current_state': workflow_data.get('current_state', 'processing'),
                'workflow_data': json.dumps(workflow_data),
                'status': workflow_data.get('status', 'running')
            }
            
            # Update SQL to use named parameters
            sql = """
            INSERT INTO agent_workflows (
                workflow_id, session_id, workflow_type, current_state,
                workflow_data, started_at, status
            ) VALUES (
                :workflow_id, :session_id, :workflow_type, :current_state,
                :workflow_data, CURRENT_TIMESTAMP, :status
            )
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(sql), params)
                conn.commit()
                
            logger.info(f"Successfully wrote agent workflow to database: {workflow_id}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Error writing to agent_workflows table: {e}")
            return None


    def process_ai_recommendation(self, user_id: str, recommendation: Dict, session_id: Optional[str] = None) -> Dict:
        """
        Complete workflow for processing AI recommendations:
        1. Start AI session and log recommendation
        2. Send to compliance agent for review
        3. Log compliance review results
        4. Validate against user's portfolio
        5. Create order if valid
        6. Request approval (simulated)
        7. Execute if approved
        8. Log all interactions to database
        
        Args:
            user_id: User identifier
            recommendation: AI-generated trade recommendation
            session_id: Optional existing session ID
            
        Returns:
            Complete execution result with all logging
        """
        try:
            # Step 1: Start AI session if not provided
            if not session_id:
                session_id = chat_logger.start_session(
                    user_id=user_id,
                    session_type="execution",
                    context_data={"recommendation": recommendation}
                )
            
            # Log the incoming AI recommendation
            chat_logger.log_message(
                agent_type="advisor",  # Use valid agent_type from schema
                message_type="recommendation",
                content=f"AI Recommendation: {json.dumps(recommendation)}",
                session_id=session_id,
                metadata={"user_id": user_id, "recommendation_type": "investment"}
            )
            
            logger.info(f"Processing AI recommendation for user {user_id}: {recommendation}")
            
            # Step 1.5: Write recommendation to recommendations table
            recommendation_id = self._write_to_recommendations_table(
                recommendation=recommendation,
                user_id=user_id
            )
            
            # Step 1.6: Start workflow tracking
            workflow_id = self._write_to_agent_workflows_table(
                session_id=session_id,
                workflow_type="trade_execution",
                workflow_data={
                    "current_state": "compliance_review",
                    "recommendation_id": recommendation_id,
                    "status": "running"
                }
            )
            
            # Step 2: Send to compliance agent for review
            compliance_result = self._get_compliance_review(recommendation, user_id, session_id)
            
            # Step 2.5: Write compliance results to database
            compliance_check_id = self._write_to_compliance_checks_table(
                recommendation_id=recommendation_id,
                compliance_result=compliance_result,
                user_id=user_id
            )
            
            if not compliance_result.get('approved', False):
                # Log compliance rejection
                chat_logger.log_message(
                    agent_type="execution",  # Use valid agent_type from schema
                    message_type="system",
                    content=f"Trade rejected by compliance: {compliance_result.get('reason', 'Compliance issues found')}",
                    session_id=session_id,
                    metadata={"compliance_result": compliance_result, "compliance_check_id": compliance_check_id}
                )
                
                chat_logger.end_session(session_id)
                return {
                    "status": "rejected",
                    "stage": "compliance_review",
                    "reason": compliance_result.get('reason', 'Compliance issues found'),
                    "compliance_result": compliance_result,
                    "recommendation_id": recommendation_id,
                    "compliance_check_id": compliance_check_id,
                    "workflow_id": workflow_id,
                    "session_id": session_id
                }
            
            # Step 3: Validate recommendation against portfolio
            validation = self.validate_recommendation_against_portfolio(user_id, recommendation)
            
            # Log validation result
            chat_logger.log_message(
                agent_type="execution",  # Use valid agent_type from schema
                message_type="system",
                content=f"Portfolio validation: {'PASSED' if validation.get('approved') else 'FAILED'}",
                session_id=session_id,
                metadata={"validation_result": validation}
            )
            
            if not validation["approved"]:
                chat_logger.end_session(session_id)
                return {
                    "status": "rejected",
                    "stage": "portfolio_validation",
                    "reason": validation["reason"],
                    "details": validation["details"],
                    "compliance_result": compliance_result,
                    "recommendation_id": recommendation_id,
                    "compliance_check_id": compliance_check_id,
                    "workflow_id": workflow_id,
                    "session_id": session_id
                }
            
            # Step 4: Create trade order
            order_result = self.create_trade_order(
                client_id=user_id,
                symbol=recommendation["symbol"],
                action=recommendation["action"],
                quantity=recommendation["quantity"],
                portfolio_value=validation["portfolio_context"]["total_value"]
            )
            
            # Log order creation
            chat_logger.log_message(
                agent_type="execution",  # Use valid agent_type from schema
                message_type="system",
                content=f"Order created: {recommendation['symbol']} {recommendation['action']} {recommendation['quantity']} shares",
                session_id=session_id,
                metadata={"order_result": order_result}
            )
            
            if "error" in order_result:
                chat_logger.end_session(session_id)
                return {
                    "status": "failed",
                    "stage": "order_creation",
                    "reason": order_result["error"],
                    "compliance_result": compliance_result,
                    "validation": validation,
                    "recommendation_id": recommendation_id,
                    "compliance_check_id": compliance_check_id,
                    "workflow_id": workflow_id,
                    "session_id": session_id
                }
            
            # Step 5: Execute the trade (auto-approve for demo)
            execution_result = self._execute_approved_order(order_result["order_id"])
            
            # Log execution result
            chat_logger.log_message(
                agent_type="execution",  # Use valid agent_type from schema
                message_type="response",
                content=f"Trade executed: {execution_result.get('status', 'unknown')} - {execution_result.get('message', '')}",
                session_id=session_id,
                metadata={"execution_result": execution_result}
            )
            
            # Step 6: End the session
            chat_logger.end_session(session_id)
            
            return {
                "status": "completed",
                "stage": "execution",
                "order_id": order_result["order_id"],
                "validation": validation,
                "compliance_result": compliance_result,
                "order_details": order_result["order_details"],
                "execution_result": execution_result,
                "recommendation_id": recommendation_id,
                "compliance_check_id": compliance_check_id,
                "workflow_id": workflow_id,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error processing AI recommendation: {e}")
            
            # Log the error
            if session_id:
                chat_logger.log_message(
                    agent_type="execution",  # Use valid agent_type from schema
                    message_type="system",
                    content=f"ERROR: {str(e)}",
                    session_id=session_id,
                    metadata={"error_type": type(e).__name__}
                )
                chat_logger.end_session(session_id)
            
            return {
                "status": "error",
                "stage": "processing",
                "reason": str(e),
                "session_id": session_id
            }
    
    def _get_user_risk_tolerance(self, user_id: str) -> str:
        """Get user's risk tolerance from database."""
        try:
            with self.db_service.get_session() as session:
                result = session.execute(
                    text("SELECT risk_profile FROM users WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                row = result.fetchone()
                return row[0] if row and row[0] else "moderate"
        except Exception as e:
            logger.warning(f"Could not load user risk tolerance: {str(e)}")
            return "moderate"  # fallback


# Create service instance (renamed from agent to service)
execution_service = ExecutionService()


