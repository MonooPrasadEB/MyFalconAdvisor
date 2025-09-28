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
from ..tools.database_service import DatabaseService

config = Config.get_instance()
logger = logging.getLogger(__name__)


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
        self.db_service = DatabaseService()
        self.mock_mode = False
        
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
                
                logger.info(f"Alpaca API initialized - Paper Trading: {config.alpaca_paper_trading}")
                
            except Exception as e:
                logger.error(f"Failed to initialize Alpaca API: {e}")
                self.trading_client = None
                self.data_client = None
                self.mock_mode = True
    
    def test_connection(self) -> Dict:
        """Test connection to Alpaca API."""
        if self.mock_mode:
            return {
                "connected": True,
                "mode": "mock",
                "message": "Mock mode active - no real API connection"
            }
            
        try:
            account = self.trading_client.get_account()
            return {
                "connected": True,
                "mode": "paper" if self.config.alpaca_paper_trading else "live",
                "account_id": account.id,
                "status": account.status,
                "currency": account.currency,
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value)
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "connected": False,
                "error": str(e)
            }
    
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
        """Place an order with Alpaca."""
        
        if self.mock_mode:
            return self._mock_place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=order_type,
                limit_price=limit_price
            )
        
        try:
            # Normalize parameters
            side = side.lower()
            order_type = order_type.lower()
            time_in_force = time_in_force.lower()
            
            # Create order request based on type
            if order_type == "market":
                order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                )
            elif order_type == "limit" and limit_price:
                order_data = LimitOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                    limit_price=limit_price
                )
            else:
                return {"error": "Invalid order type or missing price"}
            
            # Submit order
            order = self.trading_client.submit_order(order_data)
            
            # Record in database if user_id provided
            if user_id and self.db_service:
                transaction_id = self.db_service.record_transaction(
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    quantity=quantity,
                    side=side,
                    order_type=order_type,
                    status="pending",
                    broker_reference=str(order.id)
                )
            else:
                transaction_id = None
            
            return {
                "success": True,
                "order_id": str(order.id),
                "transaction_id": transaction_id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": float(order.qty),
                "order_type": order.type,
                "status": order.status,
                "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None
            }
            
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return {"error": str(e)}
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get order status from Alpaca and update database."""
        if self.mock_mode:
            return {
                "order_id": order_id,
                "status": "mock_pending",
                "symbol": "MOCK",
                "side": "buy",
                "quantity": 0,
                "filled_qty": 0,
                "filled_avg_price": None,
                "submitted_at": datetime.now().isoformat(),
                "filled_at": None,
                "note": "Mock mode - no real order status"
            }
        
        try:
            order = self.trading_client.get_order_by_id(order_id)
            
            # Update transaction status in database if needed
            if order.status in ["filled", "canceled", "rejected"]:
                self.db_service.update_transaction_by_broker_ref(
                    broker_reference=order_id,
                    updates={
                        "status": "executed" if order.status == "filled" else order.status,
                        "execution_date": datetime.now() if order.status == "filled" else None,
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
            return {
                "positions": [
                    {
                        "symbol": "AAPL",
                        "qty": 10,
                        "market_value": 1935.00,
                        "avg_entry_price": 180.50,
                        "current_price": 193.50,
                        "unrealized_pl": 130.00
                    },
                    {
                        "symbol": "MSFT",
                        "qty": 5,
                        "market_value": 2085.50,
                        "avg_entry_price": 380.10,
                        "current_price": 417.10,
                        "unrealized_pl": 185.00
                    }
                ],
                "total_market_value": 4020.50,
                "total_unrealized_pl": 315.00
            }
            
        try:
            positions = self.trading_client.get_all_positions()
            
            formatted_positions = []
            total_market_value = 0
            total_unrealized_pl = 0
            
            for pos in positions:
                market_value = float(pos.market_value)
                unrealized_pl = float(pos.unrealized_pl)
                
                formatted_positions.append({
                    "symbol": pos.symbol,
                    "qty": float(pos.qty),
                    "market_value": market_value,
                    "avg_entry_price": float(pos.avg_entry_price),
                    "current_price": float(pos.current_price),
                    "unrealized_pl": unrealized_pl
                })
                
                total_market_value += market_value
                total_unrealized_pl += unrealized_pl
            
            return {
                "positions": formatted_positions,
                "total_market_value": total_market_value,
                "total_unrealized_pl": total_unrealized_pl
            }
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return {"error": str(e)}
    
    def get_market_data(self, symbol: str, timeframe: str = "1Day", limit: int = 100) -> Dict:
        """Get market data for a symbol."""
        if self.mock_mode:
            mock_prices = {
                "AAPL": 193.50,
                "MSFT": 417.10,
                "GOOGL": 175.20,
                "AMZN": 151.94,
                "TSLA": 248.42,
                "SPY": 502.43,
                "QQQ": 427.31,
                "VTI": 215.64,
                "BND": 72.46,
                "JNJ": 155.12,
                "PG": 152.96,
                "KO": 58.35,
                "NVDA": 875.28
            }
            
            price = mock_prices.get(symbol, 100.0)
            now = datetime.now()
            
            return {
                "symbol": symbol,
                "latest_price": price,
                "last_updated": now.isoformat(),
                "bars": [
                    {
                        "timestamp": (now - timedelta(days=i)).isoformat(),
                        "open": price * (1 - 0.01 * i),
                        "high": price * (1 + 0.005 * i),
                        "low": price * (1 - 0.015 * i),
                        "close": price * (1 - 0.005 * i),
                        "volume": 1000000 - (i * 50000)
                    }
                    for i in range(5)  # Last 5 days of mock data
                ]
            }
        
        try:
            # Get latest quote
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = self.data_client.get_stock_latest_quote(quote_request)
            
            symbol_quote = quotes[symbol]
            latest_price = (float(symbol_quote.ask_price) + float(symbol_quote.bid_price)) / 2
            
            # Get historical bars
            bars_request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                limit=5  # Last 5 days
            )
            
            bars = self.data_client.get_stock_bars(bars_request)
            symbol_bars = bars[symbol] if symbol in bars else None
            
            return {
                "symbol": symbol,
                "latest_price": latest_price,
                "last_updated": datetime.now().isoformat(),
                "bars": [
                    {
                        "timestamp": bar.timestamp.isoformat(),
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": bar.volume
                    }
                    for bar in symbol_bars
                ] if symbol_bars else None
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
                "QQQ": 427.31, "VTI": 215.64, "BND": 72.46,
                "JNJ": 155.12, "PG": 152.96, "KO": 58.35,
                "NVDA": 875.28
            }
            return mock_prices.get(symbol, 100.0)
        
        try:
            market_data = self.get_market_data(symbol)
            return market_data.get("latest_price", 100.0)
        except:
            return 100.0  # Fallback price
    
    def _calculate_order_cost(self, quantity: float, price: float) -> float:
        """Calculate estimated order cost including commissions."""
        trade_value = quantity * price
        commission = max(trade_value * 0.001, 0.01)  # 0.1% or $0.01 minimum
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
            "submitted_at": datetime.now().isoformat(),
            "estimated_cost": estimated_cost,
            "note": "This is a mock order - no actual trade was placed"
        }


# Create service instance
alpaca_trading_service = AlpacaTradingService()