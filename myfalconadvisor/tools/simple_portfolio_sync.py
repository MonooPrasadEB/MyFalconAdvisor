"""
Simple Portfolio Synchronization Service

A lightweight version that handles manual syncing and order monitoring
without requiring background scheduling dependencies.
"""

import time
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional
import logging
from sqlalchemy import text

from .database_service import DatabaseService
from .alpaca_trading_service import alpaca_trading_service

logger = logging.getLogger(__name__)


class SimplePortfolioSync:
    """
    Simple portfolio synchronization service for manual syncing.
    """
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.alpaca_service = alpaca_trading_service
    
    def sync_user_now(self, user_id: str) -> Dict:
        """Manually sync portfolio immediately."""
        try:
            # Get user's portfolios
            portfolios = self.db_service.get_user_portfolios(user_id)
            
            if not portfolios:
                return {"error": "No portfolios found for user"}
            
            results = []
            for portfolio in portfolios:
                self._sync_user_portfolio(user_id, portfolio['portfolio_id'])
                results.append({
                    "portfolio_id": portfolio['portfolio_id'],
                    "portfolio_name": portfolio.get('portfolio_name', 'Unknown'),
                    "status": "synced"
                })
            
            return {
                "success": True,
                "message": f"Synced {len(results)} portfolios",
                "portfolios": results
            }
            
        except Exception as e:
            logger.error(f"Manual sync failed for {user_id}: {e}")
            return {"error": str(e)}
    
    def _sync_user_portfolio(self, user_id: str, portfolio_id: str):
        """Sync individual user portfolio."""
        try:
            # Step 1: Check for filled orders first
            filled_orders = self._update_filled_orders(user_id)
            
            # Step 2: Sync portfolio from Alpaca if we have filled orders or it's been a while
            if filled_orders > 0 or self._should_sync_portfolio(portfolio_id):
                sync_result = self.alpaca_service.sync_portfolio_from_alpaca(
                    user_id, portfolio_id
                )
                
                if sync_result.get("error"):
                    logger.warning(f"Sync failed for {user_id}: {sync_result['error']}")
                else:
                    logger.debug(f"✅ Synced portfolio for {user_id}")
                    
        except Exception as e:
            logger.error(f"Error syncing {user_id}: {e}")
    
    def _update_filled_orders(self, user_id: str) -> int:
        """Check and update filled orders for user. Returns count of filled orders."""
        filled_count = 0
        
        try:
            # Get pending transactions with broker references
            with self.db_service.get_session() as session:
                result = session.execute(text("""
                    SELECT transaction_id, broker_reference, symbol, quantity, transaction_type
                    FROM transactions 
                    WHERE user_id = :user_id 
                      AND status = 'pending'
                      AND broker_reference IS NOT NULL
                    ORDER BY created_at DESC
                """), {"user_id": user_id})
                
                pending_orders = result.fetchall()
            
            # Check each order status with Alpaca
            for order in pending_orders:
                try:
                    order_status = self.alpaca_service.get_order_status(order.broker_reference)
                    
                    if order_status.get("status") == "filled":
                        # Update transaction status
                        self._update_transaction_status(
                            order.transaction_id, 
                            "executed",
                            order_status
                        )
                        
                        filled_count += 1
                        logger.info(f"📈 Order filled: {order.symbol} {order.transaction_type} {order.quantity} shares")
                        
                    elif order_status.get("status") in ["canceled", "rejected"]:
                        # Update failed orders
                        self._update_transaction_status(
                            order.transaction_id,
                            order_status.get("status"),
                            order_status
                        )
                        logger.info(f"❌ Order {order_status.get('status')}: {order.symbol}")
                        
                except Exception as e:
                    logger.warning(f"Could not check order {order.broker_reference}: {e}")
                    
            return filled_count
                    
        except Exception as e:
            logger.error(f"Error updating filled orders for {user_id}: {e}")
            return 0
    
    def _update_transaction_status(self, transaction_id: str, status: str, order_data: Dict):
        """Update transaction status and execution details."""
        try:
            with self.db_service.get_session() as session:
                update_data = {
                    "transaction_id": transaction_id,
                    "status": status,
                    "updated_at": datetime.now()
                }
                
                # Add execution details if order was filled
                if status == "executed" and order_data.get("filled_avg_price"):
                    update_data.update({
                        "price": float(order_data["filled_avg_price"]),
                        "execution_date": datetime.now(),
                        "total_amount": float(order_data["filled_qty"]) * float(order_data["filled_avg_price"])
                    })
                
                # Build dynamic update query
                set_clauses = []
                for key in update_data.keys():
                    if key != "transaction_id":
                        set_clauses.append(f"{key} = :{key}")
                
                update_query = f"""
                UPDATE transactions 
                SET {', '.join(set_clauses)}
                WHERE transaction_id = :transaction_id
                """
                
                session.execute(text(update_query), update_data)
                session.commit()
                
                logger.debug(f"Updated transaction {transaction_id} to {status}")
                
        except Exception as e:
            logger.error(f"Error updating transaction status: {e}")
    
    def _should_sync_portfolio(self, portfolio_id: str) -> bool:
        """Check if portfolio needs syncing based on last update time."""
        try:
            with self.db_service.get_session() as session:
                result = session.execute(text("""
                    SELECT updated_at FROM portfolios 
                    WHERE portfolio_id = :portfolio_id
                """), {"portfolio_id": portfolio_id})
                
                row = result.fetchone()
                if row and row[0]:
                    # Sync if not updated in last hour
                    time_diff = datetime.now() - row[0]
                    return time_diff.total_seconds() > 3600  # 1 hour
                    
                return True  # Sync if no update time found
                
        except Exception as e:
            logger.warning(f"Could not check portfolio update time: {e}")
            return True
    
    def get_pending_orders(self, user_id: str) -> List[Dict]:
        """Get pending orders for a user."""
        try:
            with self.db_service.get_session() as session:
                result = session.execute(text("""
                    SELECT t.transaction_id, t.symbol, t.transaction_type, t.quantity, 
                           t.price, t.created_at, t.broker_reference, t.status
                    FROM transactions t
                    WHERE t.user_id = :user_id 
                      AND t.status IN ('pending', 'submitted')
                    ORDER BY t.created_at DESC
                """), {"user_id": user_id})
                
                orders = []
                for row in result.fetchall():
                    orders.append({
                        "transaction_id": row[0],
                        "symbol": row[1],
                        "transaction_type": row[2],
                        "quantity": row[3],
                        "price": row[4],
                        "created_at": row[5],
                        "broker_reference": row[6],
                        "status": row[7]
                    })
                
                return orders
                
        except Exception as e:
            logger.error(f"Error getting pending orders: {e}")
            return []
    
    def _is_market_hours(self) -> bool:
        """Check if current time is during market hours (9:30 AM - 4:00 PM ET)."""
        now = datetime.now()
        market_open = dt_time(9, 30)
        market_close = dt_time(16, 0)
        
        return (market_open <= now.time() <= market_close and 
                now.weekday() < 5)  # Monday = 0, Friday = 4
    
    def _is_weekend(self) -> bool:
        """Check if current day is weekend."""
        return datetime.now().weekday() >= 5  # Saturday = 5, Sunday = 6
    
    def get_sync_status(self) -> Dict:
        """Get current sync service status."""
        return {
            "is_running": False,  # Simple version doesn't run in background
            "market_hours": self._is_market_hours(),
            "is_weekend": self._is_weekend(),
            "next_sync": "Manual sync only",
            "scheduled_jobs": 0
        }


# Global service instance
simple_portfolio_sync = SimplePortfolioSync()
