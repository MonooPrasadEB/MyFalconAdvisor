"""
Multi-Client Portfolio Manager for MyFalconAdvisor.

This service manages multiple client portfolios using a single Alpaca account
by maintaining virtual portfolios and proper attribution in the database.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import uuid

from .alpaca_trading_service import alpaca_trading_service
from .database_service import database_service
from ..core.config import Config

config = Config.get_instance()
logger = logging.getLogger(__name__)


class MultiClientPortfolioManager:
    """
    Manages multiple client portfolios using a single Alpaca account.
    
    Key Features:
    - Virtual portfolio separation per client
    - Proper order attribution and tracking
    - Cash allocation management
    - Portfolio performance isolation
    - Compliance per client
    """
    
    def __init__(self):
        self.alpaca_service = alpaca_trading_service
        self.db_service = database_service
        
        # Track client allocations
        self.client_allocations: Dict[str, Dict] = {}
        self.master_portfolio_id = "master_alpaca_portfolio"
    
    def _create_user_if_not_exists(self, user_data: Dict) -> str:
        """Create user if they don't exist, return the actual user_id."""
        if not self.db_service.engine:
            logger.warning("Database not available - mock user creation")
            return user_data["user_id"]
        
        try:
            from sqlalchemy import text
            with self.db_service.engine.connect() as conn:
                # Check if user exists by email (since emails are unique)
                check_query = "SELECT user_id FROM users WHERE email = :email"
                result = conn.execute(text(check_query), {"email": user_data["email"]})
                existing_user = result.fetchone()
                
                if existing_user:
                    return existing_user[0]  # Return existing user_id
                
                # Create user with new ID
                columns = list(user_data.keys())
                placeholders = [f":{col}" for col in columns]
                
                insert_query = f"""
                INSERT INTO users ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                """
                
                conn.execute(text(insert_query), user_data)
                conn.commit()
                return user_data["user_id"]
                
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return user_data["user_id"]  # Return the intended user_id anyway
        
    def initialize_client_portfolio(
        self, 
        user_id: str, 
        client_name: str,
        initial_cash: float = 10000.0,
        risk_tolerance: str = "moderate"
    ) -> Dict:
        """
        Initialize a new client's virtual portfolio.
        
        Args:
            user_id: Unique user identifier
            client_name: Client display name
            initial_cash: Starting cash allocation
            risk_tolerance: Risk profile
        
        Returns:
            Dictionary with portfolio details
        """
        try:
            portfolio_id = str(uuid.uuid4())
            
            # First, create the user if they don't exist
            user_data = {
                "user_id": user_id,
                "email": f"{client_name.lower().replace(' ', '.')}@example.com",
                "first_name": client_name.split()[0],
                "last_name": client_name.split()[-1] if len(client_name.split()) > 1 else "Client",
                "risk_profile": risk_tolerance,
                "annual_income_usd": initial_cash * 2,  # Assume income is 2x initial investment
                "net_worth_usd": initial_cash * 5,  # Assume net worth is 5x initial investment
            }
            
            # Try to create user (returns existing or new user_id)
            actual_user_id = self._create_user_if_not_exists(user_data)
            
            # Create portfolio record in database
            portfolio_data = {
                "portfolio_id": portfolio_id,
                "user_id": actual_user_id,
                "portfolio_name": f"{client_name} - Virtual Portfolio",
                "total_value": initial_cash,
                "cash_balance": initial_cash,
                "portfolio_type": "other",  # Use 'other' since 'virtual_managed' isn't in the check constraint
                "is_primary": True,
                "portfolio_notes": f"Virtual portfolio managed via Alpaca master account. Risk: {risk_tolerance}",
                "created_at": datetime.now()
            }
            
            # Store in database
            success = self.db_service.create_portfolio(portfolio_data)
            if not success:
                return {"error": "Failed to create portfolio in database"}
            
            # Track client allocation
            self.client_allocations[user_id] = {
                "portfolio_id": portfolio_id,
                "client_name": client_name,
                "cash_allocated": initial_cash,
                "positions": {},
                "total_value": initial_cash,
                "risk_tolerance": risk_tolerance,
                "created_at": datetime.now()
            }
            
            # Create audit entry
            self.db_service.create_audit_entry(
                user_id=user_id,
                entity_type="portfolio",
                entity_id=portfolio_id,
                action="create_virtual_portfolio",
                new_values={
                    "initial_cash": initial_cash,
                    "client_name": client_name,
                    "portfolio_type": "virtual_managed"
                }
            )
            
            return {
                "success": True,
                "portfolio_id": portfolio_id,
                "user_id": user_id,
                "client_name": client_name,
                "initial_cash": initial_cash,
                "message": "Virtual portfolio created successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize client portfolio: {e}")
            return {"error": str(e)}
    
    def place_client_order(
        self,
        user_id: str,
        symbol: str,
        side: str,  # "buy" or "sell"
        quantity: float,
        order_type: str = "market",
        limit_price: Optional[float] = None
    ) -> Dict:
        """
        Place an order attributed to a specific client.
        
        This method:
        1. Validates client has sufficient funds/positions
        2. Places order through Alpaca
        3. Records attribution in database
        4. Updates virtual portfolio
        """
        try:
            if user_id not in self.client_allocations:
                return {"error": f"Client {user_id} not found. Initialize portfolio first."}
            
            client_data = self.client_allocations[user_id]
            portfolio_id = client_data["portfolio_id"]
            
            # Get current price for validation
            current_price = self._get_current_price(symbol)
            if not current_price:
                return {"error": f"Could not get current price for {symbol}"}
            
            estimated_cost = quantity * current_price
            
            # Validate client has sufficient funds (for buy orders)
            if side.lower() == "buy":
                available_cash = client_data.get("cash_allocated", 0)
                if estimated_cost > available_cash:
                    return {
                        "error": f"Insufficient funds. Need ${estimated_cost:,.2f}, have ${available_cash:,.2f}",
                        "required": estimated_cost,
                        "available": available_cash
                    }
            
            # Validate client has sufficient shares (for sell orders)
            elif side.lower() == "sell":
                current_position = client_data["positions"].get(symbol, 0)
                if quantity > current_position:
                    return {
                        "error": f"Insufficient shares. Need {quantity}, have {current_position}",
                        "required": quantity,
                        "available": current_position
                    }
            
            # Place order through Alpaca with client attribution
            alpaca_result = self.alpaca_service.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=order_type,
                limit_price=limit_price,
                user_id=user_id,
                portfolio_id=portfolio_id
            )
            
            if not alpaca_result.get("success"):
                return {"error": f"Alpaca order failed: {alpaca_result.get('error')}"}
            
            # Record client-attributed transaction
            transaction_data = {
                "portfolio_id": portfolio_id,
                "user_id": user_id,
                "symbol": symbol,
                "transaction_type": side.upper(),
                "quantity": quantity,
                "price": limit_price or current_price,
                "total_amount": estimated_cost,
                "order_type": order_type,
                "status": "pending",
                "broker_reference": alpaca_result.get("order_id"),
                "notes": f"Client order via master Alpaca account. Client: {client_data['client_name']}",
                "created_at": datetime.now()
            }
            
            transaction_id = self.db_service.create_transaction(transaction_data)
            
            # Update virtual portfolio (optimistic - will be reconciled later)
            self._update_virtual_portfolio(user_id, symbol, side, quantity, current_price)
            
            return {
                "success": True,
                "client_order_id": transaction_id,
                "alpaca_order_id": alpaca_result.get("order_id"),
                "user_id": user_id,
                "client_name": client_data["client_name"],
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "estimated_price": current_price,
                "estimated_cost": estimated_cost,
                "status": "pending_execution"
            }
            
        except Exception as e:
            logger.error(f"Failed to place client order: {e}")
            return {"error": str(e)}
    
    def get_client_portfolio(self, user_id: str) -> Dict:
        """Get client's virtual portfolio with current values."""
        try:
            if user_id not in self.client_allocations:
                return {"error": f"Client {user_id} not found"}
            
            client_data = self.client_allocations[user_id]
            portfolio_id = client_data["portfolio_id"]
            
            # Get positions from database
            assets = self.db_service.get_portfolio_assets(portfolio_id)
            
            # Calculate current values
            total_value = client_data["cash_allocated"]
            positions_summary = []
            
            for asset in assets:
                current_price = self._get_current_price(asset["symbol"])
                current_value = asset["quantity"] * current_price if current_price else 0
                total_value += current_value
                
                positions_summary.append({
                    "symbol": asset["symbol"],
                    "quantity": asset["quantity"],
                    "avg_cost": asset.get("average_cost", 0),
                    "current_price": current_price,
                    "market_value": current_value,
                    "unrealized_pl": current_value - (asset["quantity"] * asset.get("average_cost", 0))
                })
            
            return {
                "user_id": user_id,
                "portfolio_id": portfolio_id,
                "client_name": client_data["client_name"],
                "total_value": total_value,
                "cash_balance": client_data["cash_allocated"],
                "positions": positions_summary,
                "positions_count": len(positions_summary),
                "risk_tolerance": client_data["risk_tolerance"],
                "created_at": client_data["created_at"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get client portfolio: {e}")
            return {"error": str(e)}
    
    def reconcile_with_alpaca(self) -> Dict:
        """
        Reconcile all client positions with actual Alpaca account.
        
        This should be run periodically to ensure virtual portfolios
        match the actual master account state.
        """
        try:
            # Get actual Alpaca positions
            alpaca_positions = self.alpaca_service.get_positions()
            
            if alpaca_positions.get("error"):
                return {"error": f"Could not get Alpaca positions: {alpaca_positions['error']}"}
            
            actual_positions = {pos["symbol"]: pos for pos in alpaca_positions.get("positions", [])}
            
            # Calculate total virtual positions per symbol
            virtual_totals = {}
            for user_id, client_data in self.client_allocations.items():
                for symbol, quantity in client_data["positions"].items():
                    virtual_totals[symbol] = virtual_totals.get(symbol, 0) + quantity
            
            # Compare and report discrepancies
            discrepancies = []
            
            for symbol, virtual_qty in virtual_totals.items():
                actual_qty = actual_positions.get(symbol, {}).get("quantity", 0)
                if abs(virtual_qty - actual_qty) > 0.01:  # Allow for small rounding differences
                    discrepancies.append({
                        "symbol": symbol,
                        "virtual_quantity": virtual_qty,
                        "actual_quantity": actual_qty,
                        "difference": actual_qty - virtual_qty
                    })
            
            return {
                "success": True,
                "reconciliation_time": datetime.now().isoformat(),
                "total_virtual_symbols": len(virtual_totals),
                "total_actual_symbols": len(actual_positions),
                "discrepancies": discrepancies,
                "discrepancy_count": len(discrepancies)
            }
            
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")
            return {"error": str(e)}
    
    def get_all_clients_summary(self) -> Dict:
        """Get summary of all client portfolios."""
        try:
            clients_summary = []
            total_allocated = 0
            
            for user_id, client_data in self.client_allocations.items():
                portfolio = self.get_client_portfolio(user_id)
                if not portfolio.get("error"):
                    clients_summary.append({
                        "user_id": user_id,
                        "client_name": client_data["client_name"],
                        "portfolio_value": portfolio.get("total_value", 0),
                        "cash_balance": portfolio.get("cash_balance", 0),
                        "positions_count": portfolio.get("positions_count", 0),
                        "risk_tolerance": client_data["risk_tolerance"]
                    })
                    total_allocated += portfolio.get("total_value", 0)
            
            # Get master Alpaca account info
            alpaca_account = self.alpaca_service.test_connection()
            
            return {
                "total_clients": len(clients_summary),
                "total_allocated_value": total_allocated,
                "master_account_value": alpaca_account.get("portfolio_value", 0),
                "master_cash": alpaca_account.get("cash", 0),
                "clients": clients_summary,
                "summary_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get clients summary: {e}")
            return {"error": str(e)}
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        try:
            market_data = self.alpaca_service.get_market_data(symbol)
            if market_data and not market_data.get("error"):
                return market_data.get("latest_price")
            return None
        except:
            return None
    
    def _update_virtual_portfolio(self, user_id: str, symbol: str, side: str, quantity: float, price: float):
        """Update virtual portfolio positions (optimistic update)."""
        try:
            client_data = self.client_allocations[user_id]
            
            if side.lower() == "buy":
                # Add to position
                current_pos = client_data["positions"].get(symbol, 0)
                client_data["positions"][symbol] = current_pos + quantity
                # Reduce cash
                client_data["cash_allocated"] -= quantity * price
                
            elif side.lower() == "sell":
                # Reduce position
                current_pos = client_data["positions"].get(symbol, 0)
                client_data["positions"][symbol] = max(0, current_pos - quantity)
                # Add cash
                client_data["cash_allocated"] += quantity * price
                
        except Exception as e:
            logger.warning(f"Failed to update virtual portfolio: {e}")


# Create service instance
multi_client_manager = MultiClientPortfolioManager()
