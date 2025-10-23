"""
Portfolio Synchronization Service

Intelligent background service that syncs portfolio data from Alpaca to PostgreSQL database.
Handles pending orders, filled trades, and portfolio updates with market-aware scheduling.
"""

import schedule
import time
import threading
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional
import logging
from sqlalchemy import text

from .database_service import database_service
from .alpaca_trading_service import alpaca_trading_service
from ..core.logging_config import get_portfolio_sync_logger

logger = get_portfolio_sync_logger()


class PortfolioSyncService:
    """
    Intelligent portfolio synchronization service that adapts to market hours.
    
    Features:
    - Market-aware scheduling (5min during market, 30min after hours)
    - Automatic pending order monitoring
    - Portfolio data synchronization
    - Error handling and retry logic
    """
    
    def __init__(self):
        self.db_service = database_service  # Use shared singleton
        self.alpaca_service = alpaca_trading_service
        self.is_running = False
        self.sync_thread = None
        
    def start_sync_service(self):
        """Start the background sync service."""
        if self.is_running:
            logger.info("Sync service already running")
            return
            
        self.is_running = True
        
        # Clear any existing scheduled jobs
        schedule.clear()
        
        # Schedule different frequencies based on market hours
        schedule.every(5).minutes.do(self._sync_during_market_hours)
        schedule.every(30).minutes.do(self._sync_after_hours)
        schedule.every(2).hours.do(self._sync_weekends)
        
        # Start background thread
        self.sync_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.sync_thread.start()
        
        logger.info("🔄 Portfolio sync service started")
        logger.info("📅 Schedule: 5min (market hours), 30min (after hours), 2hr (weekends)")
        
        # Run initial sync
        self._sync_all_portfolios()
    
    def stop_sync_service(self):
        """Stop the background sync service."""
        self.is_running = False
        schedule.clear()
        logger.info("Portfolio sync service stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in background thread."""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Continue running even if error
    
    def _sync_during_market_hours(self):
        """Sync every 5 minutes during market hours (9:30 AM - 4:00 PM ET)."""
        if self._is_market_hours():
            logger.debug("🕐 Market hours sync triggered")
            self._sync_all_portfolios()
    
    def _sync_after_hours(self):
        """Sync every 30 minutes after market hours."""
        if not self._is_market_hours() and not self._is_weekend():
            logger.debug("🌙 After hours sync triggered")
            self._sync_all_portfolios()
    
    def _sync_weekends(self):
        """Sync every 2 hours on weekends (minimal activity)."""
        if self._is_weekend():
            logger.debug("📅 Weekend sync triggered")
            self._sync_all_portfolios()
    
    def _sync_all_portfolios(self):
        """Sync all user portfolios with pending transactions."""
        try:
            # Get all users with pending transactions or recent activity
            users_to_sync = self._get_users_to_sync()
            
            if not users_to_sync:
                logger.debug("No portfolios need syncing")
                return
            
            synced_count = 0
            for user_data in users_to_sync:
                try:
                    self._sync_user_portfolio(
                        user_data['user_id'], 
                        user_data['portfolio_id']
                    )
                    synced_count += 1
                except Exception as e:
                    logger.error(f"Failed to sync user {user_data['user_id']}: {e}")
                    
            logger.info(f"✅ Synced {synced_count}/{len(users_to_sync)} portfolios")
            
        except Exception as e:
            logger.error(f"Portfolio sync error: {e}")
    
    def _get_users_to_sync(self) -> List[Dict]:
        """Get users who need portfolio synchronization."""
        try:
            with self.db_service.get_session() as session:
                # Get users with pending transactions or recent activity
                result = session.execute(text("""
                    SELECT DISTINCT p.user_id, p.portfolio_id, u.first_name, u.last_name
                    FROM portfolios p
                    JOIN users u ON p.user_id = u.user_id
                    LEFT JOIN transactions t ON p.portfolio_id = t.portfolio_id
                    WHERE t.status = 'pending' 
                       OR t.created_at > NOW() - INTERVAL '24 hours'
                       OR p.updated_at < NOW() - INTERVAL '1 hour'
                    ORDER BY p.user_id
                """))
                
                users = []
                for row in result.fetchall():
                    users.append({
                        'user_id': row[0],
                        'portfolio_id': row[1],
                        'name': f"{row[2]} {row[3]}".strip()
                    })
                
                return users
                
        except Exception as e:
            logger.error(f"Error getting users to sync: {e}")
            return []
    
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
                    "updated_at": datetime.utcnow()
                }
                
                # Add execution details if order was filled
                if status == "executed" and order_data.get("filled_avg_price"):
                    update_data.update({
                        "price": float(order_data["filled_avg_price"]),
                        "execution_date": datetime.utcnow(),
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
                    # Handle timezone-aware/naive datetime comparison
                    updated_at = row[0]
                    now = datetime.utcnow()
                    
                    # Make both timezone-naive for comparison
                    if updated_at.tzinfo is not None:
                        updated_at = updated_at.replace(tzinfo=None)
                    if now.tzinfo is not None:
                        now = now.replace(tzinfo=None)
                        
                    time_diff = now - updated_at
                    logger.debug(f"Last update: {updated_at}, Now: {now}, Diff: {time_diff.total_seconds()}s")
                    return time_diff.total_seconds() > 3600  # 1 hour
                    
                return True  # Sync if no update time found
                
        except Exception as e:
            logger.warning(f"Could not check portfolio update time: {e}")
            return True
    
    def _is_market_hours(self) -> bool:
        """Check if current time is during market hours (9:30 AM - 4:00 PM ET)."""
        import pytz
        
        # Get current time in Eastern Time
        now_utc = datetime.now(pytz.UTC)
        now_et = now_utc.astimezone(pytz.timezone('US/Eastern'))
        
        market_open = dt_time(9, 30)
        market_close = dt_time(16, 0)
        
        return (market_open <= now_et.time() <= market_close and 
                now_et.weekday() < 5)  # Monday = 0, Friday = 4
    
    def _is_weekend(self) -> bool:
        """Check if current day is weekend."""
        return datetime.now().weekday() >= 5  # Saturday = 5, Sunday = 6
    
    def sync_user_now(self, user_id: str) -> Dict:
        """Manually trigger immediate sync for a specific user."""
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
    
    def get_sync_status(self) -> Dict:
        """Get current sync service status."""
        return {
            "is_running": self.is_running,
            "market_hours": self._is_market_hours(),
            "is_weekend": self._is_weekend(),
            "next_sync": "5 minutes" if self._is_market_hours() else "30 minutes" if not self._is_weekend() else "2 hours",
            "scheduled_jobs": len(schedule.jobs)
        }


# Global service instance
portfolio_sync_service = PortfolioSyncService()


def start_background_sync():
    """Convenience function to start the sync service."""
    portfolio_sync_service.start_sync_service()


def stop_background_sync():
    """Convenience function to stop the sync service."""
    portfolio_sync_service.stop_sync_service()


if __name__ == "__main__":
    # Allow running as standalone script
    print("🚀 Starting Portfolio Sync Service...")
    start_background_sync()
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(60)
            status = portfolio_sync_service.get_sync_status()
            print(f"📊 Status: Running={status['is_running']}, Market={status['market_hours']}, Next sync in {status['next_sync']}")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping Portfolio Sync Service...")
        stop_background_sync()
        print("✅ Service stopped")
