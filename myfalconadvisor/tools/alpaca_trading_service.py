"""
Alpaca Trading Service for MyFalconAdvisor.

This service handles integration with Alpaca's trading API for paper trading
and live trading execution, portfolio synchronization, and order management.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from decimal import Decimal
import json

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest, LimitOrderRequest, StopOrderRequest,
    GetAssetsRequest, GetOrdersRequest
)
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType, AssetClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from ..core.config import Config
from ..tools.database_service import database_service
from ..core.logging_config import get_alpaca_logger

config = Config.get_instance()
logger = get_alpaca_logger()


class AlpacaTradingService:
    """
    Service for Alpaca API integration with database synchronization.
    
    Handles:
    - Paper trading and live trading
    - Portfolio synchronization with PostgreSQL
    - Order management and execution
    - Account and position tracking
    - Market data integration
    """
    
    def __init__(self):
        self.config = config
        self.db_service = database_service  # Use shared singleton
        
        # Initialize Alpaca clients
        if not config.alpaca_api_key or not config.alpaca_secret_key:
            logger.warning("Alpaca API keys not configured - service will run in mock mode")
            self.trading_client = None
            self.data_client = None
            self.mock_mode = True
        else:
            try:
                self.trading_client = TradingClient(
                    api_key=config.alpaca_api_key,
                    secret_key=config.alpaca_secret_key,
                    paper=config.alpaca_paper_trading,
                    url_override=config.alpaca_base_url if config.alpaca_paper_trading else None
                )
                
                self.data_client = StockHistoricalDataClient(
                    api_key=config.alpaca_api_key,
                    secret_key=config.alpaca_secret_key
                )
                
                self.mock_mode = False
                logger.info(f"Alpaca API initialized - Paper Trading: {config.alpaca_paper_trading}")
                
            except Exception as e:
                logger.error(f"Failed to initialize Alpaca API: {e}")
                self.trading_client = None
                self.data_client = None
                self.mock_mode = True
    
    def test_connection(self) -> Dict:
        """Test Alpaca API connection and return account info."""
        if self.mock_mode:
            return {
                "connected": False,
                "mode": "mock",
                "message": "Running in mock mode - no API keys configured"
            }
        
        try:
            account = self.trading_client.get_account()
            positions = self.trading_client.get_all_positions()
            
            return {
                "connected": True,
                "mode": "paper" if config.alpaca_paper_trading else "live",
                "account_id": str(account.id),
                "account_status": account.status,
                "buying_power": float(account.buying_power),
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "positions_count": len(positions),
                "day_trade_count": getattr(account, 'day_trade_count', 0),
                "pattern_day_trader": getattr(account, 'pattern_day_trader', False)
            }
            
        except Exception as e:
            logger.error(f"Alpaca connection test failed: {e}")
            return {
                "connected": False,
                "mode": "error",
                "error": str(e)
            }
    
    def sync_portfolio_from_alpaca(self, user_id: str, portfolio_id: str) -> Dict:
        """
        Synchronize portfolio data from Alpaca to PostgreSQL database.
        
        Args:
            user_id: User identifier in database
            portfolio_id: Portfolio identifier in database
        
        Returns:
            Dictionary with sync results
        """
        if self.mock_mode:
            return {"error": "Cannot sync in mock mode"}
        
        try:
            # Get account and positions from Alpaca
            account = self.trading_client.get_account()
            positions = self.trading_client.get_all_positions()
            
            # Update portfolio total value
            portfolio_update = {
                "total_value": float(account.portfolio_value),
                "cash_balance": float(account.cash),
                "updated_at": datetime.utcnow()
            }
            
            portfolio_updated = self.db_service.update_portfolio(
                portfolio_id, portfolio_update
            )
            
            if not portfolio_updated:
                return {"error": "Failed to update portfolio in database"}
            
            # Sync positions
            synced_positions = []
            for position in positions:
                # Use current_price from Alpaca position object (more reliable than separate API call)
                current_price = float(position.current_price) if hasattr(position, 'current_price') and position.current_price else self._get_current_price(position.symbol)
                
                asset_data = {
                    "portfolio_id": portfolio_id,
                    "symbol": position.symbol,
                    "asset_name": position.symbol,  # Could enhance with company name lookup
                    "asset_type": "stock",  # Default to stock, could enhance
                    "quantity": float(position.qty),
                    "average_cost": float(position.avg_entry_price) if position.avg_entry_price else 0,
                    "current_price": current_price,
                    "market_value": float(position.market_value) if position.market_value else 0,
                    "allocation_percent": (float(position.market_value) / float(account.portfolio_value)) if position.market_value and account.portfolio_value else 0,
                    "updated_at": datetime.utcnow()
                }
                
                # Update or create position in database
                position_result = self.db_service.upsert_portfolio_asset(asset_data)
                if position_result:
                    synced_positions.append({
                        "symbol": position.symbol,
                        "quantity": float(position.qty),
                        "market_value": float(position.market_value) if position.market_value else 0
                    })
            
            # Create audit trail entry
            self.db_service.create_audit_entry(
                user_id=user_id,
                entity_type="portfolio",
                entity_id=portfolio_id,
                action="alpaca_sync",
                new_values={
                    "total_value": float(account.portfolio_value),
                    "positions_count": len(positions),
                    "sync_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "success": True,
                "portfolio_value": float(account.portfolio_value),
                "cash_balance": float(account.cash),
                "positions_synced": len(synced_positions),
                "positions": synced_positions,
                    "sync_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Portfolio sync failed: {e}")
            return {"error": str(e)}
    
    def place_order(
        self,
        symbol: str,
        side: str,  # "buy" or "sell"
        quantity: float,
        order_type: str = "market",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "day",
        user_id: Optional[str] = None,
        portfolio_id: Optional[str] = None
    ) -> Dict:
        """
        Place an order through Alpaca API and record in database.
        
        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            order_type: "market", "limit", "stop", "stop_limit"
            limit_price: Price for limit orders
            stop_price: Price for stop orders
            time_in_force: "day", "gtc", "ioc", "fok"
            user_id: User ID for audit trail
            portfolio_id: Portfolio ID for tracking
        
        Returns:
            Dictionary with order details
        """
        if self.mock_mode:
            return self._mock_place_order(symbol, side, quantity, order_type, limit_price)
        
        try:
            # Convert parameters to Alpaca enums
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
            tif = TimeInForce.DAY if time_in_force.lower() == "day" else TimeInForce.GTC
            
            # Create appropriate order request
            if order_type.lower() == "market":
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=order_side,
                    time_in_force=tif
                )
            elif order_type.lower() == "limit":
                if not limit_price:
                    return {"error": "Limit price required for limit orders"}
                order_request = LimitOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=order_side,
                    time_in_force=tif,
                    limit_price=limit_price
                )
            elif order_type.lower() == "stop":
                if not stop_price:
                    return {"error": "Stop price required for stop orders"}
                order_request = StopOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=order_side,
                    time_in_force=tif,
                    stop_price=stop_price
                )
            else:
                return {"error": f"Unsupported order type: {order_type}"}
            
            # Submit order to Alpaca
            order = self.trading_client.submit_order(order_request)
            
            # Record transaction in database
            transaction_data = {
                "portfolio_id": portfolio_id,
                "user_id": user_id,
                "symbol": symbol,
                "transaction_type": side.upper(),
                "quantity": quantity,
                "price": limit_price or stop_price,
                "order_type": order_type,
                "status": "pending",
                "broker_reference": str(order.id),
                "notes": f"Alpaca order submitted: {order.id}",
                "created_at": datetime.utcnow()
            }
            
            transaction_id = self.db_service.create_transaction(transaction_data)
            
            return {
                "success": True,
                "order_id": str(order.id),
                "transaction_id": transaction_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "order_type": order_type,
                "status": order.status,
                "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
                "estimated_cost": self._calculate_order_cost(quantity, limit_price or self._get_current_price(symbol))
            }
            
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return {"error": str(e)}
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get order status from Alpaca and update database."""
        if self.mock_mode:
            return {"error": "Cannot get order status in mock mode"}
        
        try:
            order = self.trading_client.get_order_by_id(order_id)
            
            # Update transaction status in database if needed
            if order.status in ["filled", "canceled", "rejected"]:
                self.db_service.update_transaction_by_broker_ref(
                    broker_reference=order_id,
                    updates={
                        "status": "executed" if order.status == "filled" else order.status,
                        "execution_date": datetime.utcnow() if order.status == "filled" else None,
                        "price": float(order.filled_avg_price) if order.filled_avg_price else None,
                        "total_amount": float(order.filled_qty) * float(order.filled_avg_price) if order.filled_avg_price and order.filled_qty else None
                    }
                )
            
            return {
                "order_id": str(order.id),
                "status": order.status,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": float(order.qty),
                "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
                "filled_at": order.filled_at.isoformat() if order.filled_at else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get order status: {e}")
            return {"error": str(e)}
    
    def get_positions(self) -> Dict:
        """Get all positions from Alpaca."""
        if self.mock_mode:
            return {"positions": [], "total_value": 0}
        
        try:
            positions = self.trading_client.get_all_positions()
            account = self.trading_client.get_account()
            
            position_list = []
            for position in positions:
                position_list.append({
                    "symbol": position.symbol,
                    "quantity": float(position.qty),
                    "market_value": float(position.market_value) if position.market_value else 0,
                    "avg_cost": float(position.avg_entry_price) if position.avg_entry_price else 0,
                    "unrealized_pl": float(position.unrealized_pl) if position.unrealized_pl else 0,
                    "unrealized_plpc": float(position.unrealized_plpc) if position.unrealized_plpc else 0,
                    "current_price": float(position.current_price) if position.current_price else 0
                })
            
            return {
                "positions": position_list,
                "total_value": float(account.portfolio_value),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power)
            }
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return {"error": str(e)}
    
    def get_market_data(self, symbol: str, timeframe: str = "1Day", limit: int = 100) -> Dict:
        """Get market data for a symbol."""
        if self.mock_mode or not self.data_client:
            return {"error": "Market data not available in mock mode"}
        
        try:
            # Get latest quote
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = self.data_client.get_stock_latest_quote(quote_request)
            
            # Get historical bars
            bars_request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,  # Default to daily
                limit=limit
            )
            bars = self.data_client.get_stock_bars(bars_request)
            
            latest_quote = quotes[symbol] if symbol in quotes else None
            symbol_bars = bars[symbol] if symbol in bars else []
            
            return {
                "symbol": symbol,
                "latest_price": float(latest_quote.ask_price) if latest_quote else None,
                "bid_price": float(latest_quote.bid_price) if latest_quote else None,
                "ask_price": float(latest_quote.ask_price) if latest_quote else None,
                "timestamp": latest_quote.timestamp.isoformat() if latest_quote else None,
                "bars_count": len(symbol_bars),
                "latest_bar": {
                    "open": float(symbol_bars[-1].open) if symbol_bars else None,
                    "high": float(symbol_bars[-1].high) if symbol_bars else None,
                    "low": float(symbol_bars[-1].low) if symbol_bars else None,
                    "close": float(symbol_bars[-1].close) if symbol_bars else None,
                    "volume": int(symbol_bars[-1].volume) if symbol_bars else None,
                    "timestamp": symbol_bars[-1].timestamp.isoformat() if symbol_bars else None
                } if symbol_bars else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return {"error": str(e)}
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol (helper method)."""
        if self.mock_mode:
            # Mock prices for testing
            mock_prices = {
                "AAPL": 193.50, "MSFT": 417.10, "GOOGL": 175.20,
                "AMZN": 151.94, "TSLA": 248.42, "SPY": 502.43,
                "NVDA": 182.30, "TSLA": 445.25, "BND": 74.30,
                "JNJ": 180.34, "KO": 65.75, "PG": 152.40,
                "QQQ": 599.31, "VTI": 327.55
            }
            return mock_prices.get(symbol, 100.0)
        
        try:
            market_data = self.get_market_data(symbol)
            # Check if there's an error first
            if "error" in market_data:
                logger.warning(f"Could not get price for {symbol}: {market_data['error']}")
                return 100.0
            
            # Get latest_price, fallback to None check
            latest_price = market_data.get("latest_price")
            if latest_price is not None:
                return float(latest_price)
            
            # Fallback: try to get close price from latest bar
            latest_bar = market_data.get("latest_bar")
            if latest_bar and latest_bar.get("close"):
                return float(latest_bar["close"])
                
            logger.warning(f"No price data available for {symbol}, using fallback")
            return 100.0
            
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return 100.0  # Fallback price
    
    def _calculate_order_cost(self, quantity: float, price: float) -> float:
        """Calculate estimated order cost including commissions."""
        trade_value = quantity * price
        # Alpaca typically has no commission for stocks, but add small fee for calculation
        commission = max(0.01, trade_value * 0.001)  # 0.1% or $0.01 minimum
        return trade_value + commission
    
    def _mock_place_order(self, symbol: str, side: str, quantity: float, order_type: str, limit_price: Optional[float] = None) -> Dict:
        """Mock order placement for testing."""
        import uuid
        mock_order_id = str(uuid.uuid4())
        
        estimated_price = limit_price or self._get_current_price(symbol)
        estimated_cost = self._calculate_order_cost(quantity, estimated_price)
        
        return {
            "success": True,
            "order_id": mock_order_id,
            "transaction_id": None,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "order_type": order_type,
            "status": "mock_pending",
            "submitted_at": datetime.utcnow().isoformat(),
            "estimated_cost": estimated_cost,
            "note": "This is a mock order - no actual trade was placed"
        }


# Create service instance
alpaca_trading_service = AlpacaTradingService()
