"""
Execution Agent for validating and executing trades.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel

from ..tools.alpaca_trading_service import alpaca_trading_service
from ..tools.database_service import database_service
from ..tools.chat_logger import chat_logger
from ..core.config import Config
from ..core.logging_config import get_execution_logger

config = Config.get_instance()
logger = get_execution_logger()

class TradeOrder(BaseModel):
    """
    Model for trade orders.
    """
    order_id: str = None
    client_id: str
    symbol: str
    action: str  # buy/sell
    quantity: float
    price: Optional[float] = None
    order_type: str = "market"  # market/limit
    time_in_force: str = "day"
    status: str = "pending"
    created_at: datetime = None
    updated_at: datetime = None

class OrderType:
    """
    Enum for order types.
    """
    MARKET = "market"
    LIMIT = "limit"

class OrderAction:
    """
    Enum for order actions.
    """
    BUY = "buy"
    SELL = "sell"

class OrderStatus:
    """
    Enum for order statuses.
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"

class ExecutionResult(BaseModel):
    """
    Model for execution results.
    """
    success: bool
    order_id: str
    executed_price: Optional[float] = None
    executed_quantity: Optional[float] = None
    execution_timestamp: Optional[datetime] = None
    commission_paid: Optional[float] = None
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
    """
    
    def __init__(self):
        self.read_only_mode = False  # For testing
        self.pending_orders: Dict[str, TradeOrder] = {}
        self.executed_orders: Dict[str, TradeOrder] = {}
        self.mock_prices = {
            "AAPL": 193.50,
            "MSFT": 417.10,
            "GOOGL": 175.20,
            "AMZN": 151.94,
            "TSLA": 248.42,
            "SPY": 502.43
        }
    
    def process_ai_recommendation(self, user_id: str, recommendation: Dict, session_id: Optional[str] = None) -> Dict:
        """
        Process an AI-generated trade recommendation.
        
        Args:
            user_id: The user ID to execute the trade for
            recommendation: The trade recommendation details
            session_id: Optional AI session ID for logging
            
        Returns:
            Dict containing the execution result
        """
        try:
            # Log recommendation
            logger.info(f"Processing AI recommendation for user {user_id}: {recommendation}")
            
            # Write recommendation to database
            rec_id = self._write_to_recommendations_table(user_id, recommendation)
            if rec_id:
                logger.info(f"Successfully wrote recommendation to database: {rec_id}")
            
            # Start workflow
            workflow_id = self._write_to_agent_workflows_table(user_id, "trade_execution", {
                "recommendation_id": rec_id,
                "status": "started",
                "session_id": session_id
            })
            
            # Validate recommendation against portfolio
            validation_result = self.validate_recommendation_against_portfolio(user_id, recommendation)
            if not validation_result["success"]:
                # Write compliance check
                self._write_to_compliance_checks_table(user_id, rec_id, {
                    "check_type": "portfolio_validation",
                    "result": "fail",
                    "details": validation_result["message"]
                })
                
                return {
                    "status": "rejected",
                    "stage": "portfolio_validation",
                    "message": validation_result["message"]
                }
            
            # If in read-only mode, stop here
            if self.read_only_mode:
                return {
                    "status": "rejected",
                    "stage": "portfolio_validation",
                    "message": "Read-only mode enabled"
                }
            
            # Create order
            order = TradeOrder(
                order_id=str(uuid.uuid4()),
                client_id=user_id,
                symbol=recommendation["symbol"],
                action=recommendation["action"],
                quantity=recommendation["quantity"],
                price=recommendation.get("price"),
                order_type=recommendation.get("order_type", "market"),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Add to pending orders
            self.pending_orders[order.order_id] = order
            
            # Execute order
            result = self._execute_approved_order(order.order_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing AI recommendation: {e}")
            return {
                "status": "failed",
                "stage": "processing",
                "message": str(e)
            }
    
    def validate_recommendation_against_portfolio(self, user_id: str, recommendation: Dict) -> Dict:
        """
        Validate a trade recommendation against user's portfolio.
        
        Args:
            user_id: The user ID to validate for
            recommendation: The trade recommendation to validate
            
        Returns:
            Dict containing validation result
        """
        try:
            # Get user portfolios
            portfolios = database_service.get_user_portfolios(user_id)
            if not portfolios:
                return {
                    "success": False,
                    "message": "No portfolio found for user"
                }
            
            # Use the first portfolio (or primary if exists)
            portfolio = next((p for p in portfolios if p.get("is_primary")), portfolios[0])
            
            # Get current positions
            positions = database_service.get_portfolio_assets(portfolio["portfolio_id"])
            
            # Validate based on action
            action = recommendation["action"].lower()
            symbol = recommendation["symbol"]
            quantity = float(recommendation["quantity"])
            
            if action == "sell":
                # Check if user has enough shares
                asset = next((p for p in positions if p["symbol"] == symbol), None)
                if not asset:
                    return {
                        "success": False,
                        "message": f"No position found for {symbol}"
                    }
                
                if asset["quantity"] < quantity:
                    return {
                        "success": False,
                        "message": f"Insufficient shares: have {asset['quantity']}, need {quantity}"
                    }
                
            elif action == "buy":
                # Check if user has enough cash
                price = recommendation.get("price", self._get_current_price(symbol))
                total_cost = price * quantity
                
                if portfolio["cash_balance"] < total_cost:
                    return {
                        "success": False,
                        "message": f"Insufficient cash: have ${portfolio['cash_balance']:.2f}, need ${total_cost:.2f}"
                    }
            
            return {
                "success": True,
                "message": "Validation passed"
            }
            
        except Exception as e:
            logger.error(f"Error validating recommendation: {e}")
            return {
                "success": False,
                "message": str(e)
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
            
            # Simulate execution (in real system, this would call Alpaca API)
            filled_quantity = order.quantity
            fill_price = order.price if order.price else 100.0  # Mock price
            
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
                "fill_price": fill_price
            }
            
        except Exception as e:
            logger.error(f"Error executing order {order_id}: {e}")
            return {
                "status": "failed",
                "message": f"Execution error: {str(e)}"
            }
    
    def _simulate_trade_execution(self, order: TradeOrder) -> ExecutionResult:
        """Execute trade through Alpaca API and write to proper database tables."""
        try:
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
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol (mock data for testing)."""
        return self.mock_prices.get(symbol, 100.0)  # Default mock price
    
    def _update_positions_table(self, account_id: str, symbol: str, action: str, quantity: float, price: float):
        """Update positions table with trade execution."""
        try:
            # Get current position
            position = database_service.get_position(account_id, symbol)
            
            # Calculate new position
            if action.lower() == "buy":
                new_quantity = (position["quantity"] if position else 0) + quantity
                new_cost = (position["cost_basis"] if position else 0) + (quantity * price)
            else:  # sell
                new_quantity = (position["quantity"] if position else 0) - quantity
                new_cost = (position["cost_basis"] if position else 0) - (quantity * price)
            
            # Update or insert position
            if position:
                database_service.update_position(account_id, symbol, new_quantity, new_cost)
            else:
                database_service.insert_position(account_id, symbol, new_quantity, new_cost)
                
        except Exception as e:
            logger.error(f"Error updating positions table: {e}")
            raise
    
    def _write_to_recommendations_table(self, user_id: str, recommendation: Dict) -> Optional[str]:
        """Write recommendation to database."""
        try:
            if self.read_only_mode:
                return str(uuid.uuid4())  # Return mock ID in read-only mode
                
            rec_id = str(uuid.uuid4())
            database_service.insert_recommendation(
                rec_id=rec_id,
                user_id=user_id,
                recommendation=recommendation
            )
            return rec_id
            
        except Exception as e:
            logger.error(f"Error writing to recommendations table: {e}")
            return None
    
    def _write_to_agent_workflows_table(self, user_id: str, workflow_type: str, workflow_data: Dict) -> Optional[str]:
        """Write workflow to database."""
        try:
            if self.read_only_mode:
                return str(uuid.uuid4())  # Return mock ID in read-only mode
                
            workflow_id = str(uuid.uuid4())
            database_service.insert_workflow(
                workflow_id=workflow_id,
                user_id=user_id,
                workflow_type=workflow_type,
                workflow_data=workflow_data
            )
            return workflow_id
            
        except Exception as e:
            logger.error(f"Error writing to agent_workflows table: {e}")
            return None
    
    def _write_to_compliance_checks_table(self, user_id: str, rec_id: str, check_data: Dict) -> Optional[str]:
        """Write compliance check to database."""
        try:
            if self.read_only_mode:
                return str(uuid.uuid4())  # Return mock ID in read-only mode
                
            check_id = str(uuid.uuid4())
            database_service.insert_compliance_check(
                check_id=check_id,
                user_id=user_id,
                rec_id=rec_id,
                check_data=check_data
            )
            return check_id
            
        except Exception as e:
            logger.error(f"Error writing to compliance_checks table: {e}")
            return None

# Create service instance
execution_service = ExecutionService()