"""Enhanced market data service combining Yahoo Finance and Alpha Vantage."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from .market_data import market_data_service, StockInfo, HistoricalData
from .alpha_vantage_service import alpha_vantage_service, FundamentalData, TechnicalIndicator
from ..core.config import Config

config = Config.get_instance()
logger = logging.getLogger(__name__)

class EnhancedStockInfo(BaseModel):
    """Enhanced stock information combining multiple data sources."""
    # Basic info (from Yahoo Finance)
    symbol: str
    name: str
    current_price: float
    market_cap: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    
    # Enhanced fundamentals (from Alpha Vantage)
    pe_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    dividend_yield: Optional[float] = None
    eps: Optional[float] = None
    revenue_ttm: Optional[float] = None
    profit_margin: Optional[float] = None
    roe: Optional[float] = None
    debt_to_equity: Optional[float] = None
    beta: Optional[float] = None
    
    # Technical indicators
    rsi: Optional[float] = None
    macd_signal: Optional[str] = None  # "BUY", "SELL", "HOLD"
    
    # Data sources used
    data_sources: List[str] = []
    last_updated: datetime = Field(default_factory=datetime.now)

class MarketAnalysis(BaseModel):
    """Comprehensive market analysis."""
    symbol: str
    analysis_type: str
    
    # Price analysis
    current_price: float
    price_change_1d: Optional[float] = None
    price_change_1w: Optional[float] = None
    price_change_1m: Optional[float] = None
    
    # Fundamental analysis
    valuation_score: Optional[float] = None  # 1-10 scale
    financial_health_score: Optional[float] = None  # 1-10 scale
    
    # Technical analysis
    technical_score: Optional[float] = None  # 1-10 scale
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    
    # Overall recommendation
    recommendation: str = "HOLD"  # BUY, SELL, HOLD
    confidence: float = 0.5  # 0-1 scale
    
    # Analysis details
    strengths: List[str] = []
    concerns: List[str] = []
    
    timestamp: datetime = Field(default_factory=datetime.now)

class EnhancedMarketDataService:
    """Enhanced market data service with multiple providers."""
    
    def __init__(self):
        self.yahoo_service = market_data_service
        self.alpha_vantage_service = alpha_vantage_service
        self.cache = {}
        self.cache_duration = timedelta(hours=config.cache_duration_hours)
    
    def get_enhanced_stock_info(self, symbol: str) -> Optional[EnhancedStockInfo]:
        """Get comprehensive stock information from multiple sources."""
        cache_key = f"enhanced_{symbol}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
        
        try:
            # Start with Yahoo Finance data (fast and reliable)
            yahoo_data = self.yahoo_service.get_stock_info(symbol)
            if not yahoo_data:
                logger.warning(f"Could not get basic stock info for {symbol}")
                return None
            
            # Initialize enhanced data with Yahoo Finance info
            enhanced_data = EnhancedStockInfo(
                symbol=yahoo_data.symbol,
                name=yahoo_data.name,
                current_price=yahoo_data.current_price,
                market_cap=yahoo_data.market_cap,
                sector=yahoo_data.sector,
                industry=yahoo_data.industry,
                pe_ratio=yahoo_data.pe_ratio,
                dividend_yield=yahoo_data.dividend_yield,
                beta=yahoo_data.beta,
                data_sources=["Yahoo Finance"]
            )
            
            # Enhance with Alpha Vantage fundamentals (if available)
            try:
                av_fundamentals = self.alpha_vantage_service.get_company_overview(symbol)
                if av_fundamentals:
                    # Override with more comprehensive Alpha Vantage data
                    enhanced_data.pe_ratio = av_fundamentals.pe_ratio or enhanced_data.pe_ratio
                    enhanced_data.peg_ratio = av_fundamentals.peg_ratio
                    enhanced_data.price_to_book = av_fundamentals.price_to_book
                    enhanced_data.dividend_yield = av_fundamentals.dividend_yield or enhanced_data.dividend_yield
                    enhanced_data.eps = av_fundamentals.eps
                    enhanced_data.revenue_ttm = av_fundamentals.revenue_ttm
                    enhanced_data.profit_margin = av_fundamentals.profit_margin
                    enhanced_data.roe = av_fundamentals.roe
                    enhanced_data.debt_to_equity = av_fundamentals.debt_to_equity
                    enhanced_data.beta = av_fundamentals.beta or enhanced_data.beta
                    enhanced_data.data_sources.append("Alpha Vantage")
                    
            except Exception as e:
                logger.warning(f"Could not get Alpha Vantage fundamentals for {symbol}: {e}")
            
            # Add technical indicators (if available)
            try:
                # Get RSI
                rsi_data = self.alpha_vantage_service.get_technical_indicator(symbol, "RSI")
                if rsi_data and rsi_data.data:
                    latest_rsi = rsi_data.data[0]
                    enhanced_data.rsi = latest_rsi.get('RSI')
                
                # Get MACD signal
                macd_data = self.alpha_vantage_service.get_technical_indicator(symbol, "MACD")
                if macd_data and macd_data.data:
                    latest_macd = macd_data.data[0]
                    macd_value = latest_macd.get('MACD', 0)
                    macd_signal = latest_macd.get('MACD_Signal', 0)
                    
                    if macd_value > macd_signal:
                        enhanced_data.macd_signal = "BUY"
                    elif macd_value < macd_signal:
                        enhanced_data.macd_signal = "SELL"
                    else:
                        enhanced_data.macd_signal = "HOLD"
                        
            except Exception as e:
                logger.warning(f"Could not get technical indicators for {symbol}: {e}")
            
            # Cache result
            self.cache[cache_key] = (enhanced_data, datetime.now())
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Error getting enhanced stock info for {symbol}: {e}")
            return None
    
    def analyze_stock(self, symbol: str) -> Optional[MarketAnalysis]:
        """Perform comprehensive stock analysis."""
        try:
            enhanced_info = self.get_enhanced_stock_info(symbol)
            if not enhanced_info:
                return None
            
            # Get historical data for trend analysis
            historical_data = self.yahoo_service.get_historical_data(symbol, period="3mo")
            if not historical_data:
                return None
            
            analysis = MarketAnalysis(
                symbol=symbol,
                analysis_type="COMPREHENSIVE",
                current_price=enhanced_info.current_price
            )
            
            # Calculate price changes
            if len(historical_data.prices) >= 7:
                week_ago_price = historical_data.prices[-7]['close']
                analysis.price_change_1w = ((enhanced_info.current_price - week_ago_price) / week_ago_price) * 100
            
            if len(historical_data.prices) >= 30:
                month_ago_price = historical_data.prices[-30]['close']
                analysis.price_change_1m = ((enhanced_info.current_price - month_ago_price) / month_ago_price) * 100
            
            # Fundamental analysis scoring
            fundamental_score = self._calculate_fundamental_score(enhanced_info)
            analysis.financial_health_score = fundamental_score
            
            # Technical analysis scoring
            technical_score = self._calculate_technical_score(enhanced_info, historical_data)
            analysis.technical_score = technical_score
            
            # Overall recommendation
            recommendation, confidence = self._generate_recommendation(
                fundamental_score, technical_score, enhanced_info
            )
            analysis.recommendation = recommendation
            analysis.confidence = confidence
            
            # Generate strengths and concerns
            analysis.strengths, analysis.concerns = self._generate_insights(enhanced_info, historical_data)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing stock {symbol}: {e}")
            return None
    
    def _calculate_fundamental_score(self, info: EnhancedStockInfo) -> float:
        """Calculate fundamental analysis score (1-10)."""
        score = 5.0  # Start with neutral
        
        try:
            # P/E ratio scoring
            if info.pe_ratio:
                if 10 <= info.pe_ratio <= 20:
                    score += 1.0  # Good P/E range
                elif info.pe_ratio < 10:
                    score += 0.5  # Potentially undervalued
                elif info.pe_ratio > 30:
                    score -= 1.0  # Potentially overvalued
            
            # PEG ratio scoring
            if info.peg_ratio:
                if info.peg_ratio < 1.0:
                    score += 1.0  # Undervalued growth
                elif info.peg_ratio > 2.0:
                    score -= 0.5  # Overvalued growth
            
            # ROE scoring
            if info.roe:
                if info.roe > 0.15:  # 15%+
                    score += 1.0
                elif info.roe > 0.10:  # 10-15%
                    score += 0.5
                elif info.roe < 0:
                    score -= 1.0
            
            # Debt-to-equity scoring
            if info.debt_to_equity:
                if info.debt_to_equity < 0.5:
                    score += 0.5  # Low debt
                elif info.debt_to_equity > 2.0:
                    score -= 1.0  # High debt
            
            # Dividend yield scoring
            if info.dividend_yield and info.dividend_yield > 0.02:  # 2%+
                score += 0.5
                
        except Exception as e:
            logger.warning(f"Error calculating fundamental score: {e}")
        
        return max(1.0, min(10.0, score))  # Clamp between 1-10
    
    def _calculate_technical_score(self, info: EnhancedStockInfo, hist_data: HistoricalData) -> float:
        """Calculate technical analysis score (1-10)."""
        score = 5.0  # Start with neutral
        
        try:
            # RSI scoring
            if info.rsi:
                if 30 <= info.rsi <= 70:
                    score += 0.5  # Neutral zone
                elif info.rsi < 30:
                    score += 1.0  # Oversold - potential buy
                elif info.rsi > 70:
                    score -= 1.0  # Overbought - potential sell
            
            # MACD signal scoring
            if info.macd_signal:
                if info.macd_signal == "BUY":
                    score += 1.0
                elif info.macd_signal == "SELL":
                    score -= 1.0
            
            # Volatility scoring (lower is better for stability)
            if hist_data.volatility < 0.2:  # 20% annual volatility
                score += 0.5
            elif hist_data.volatility > 0.5:  # 50% annual volatility
                score -= 0.5
            
            # Sharpe ratio scoring
            if hist_data.sharpe_ratio and hist_data.sharpe_ratio > 1.0:
                score += 1.0
            elif hist_data.sharpe_ratio and hist_data.sharpe_ratio < 0:
                score -= 1.0
                
        except Exception as e:
            logger.warning(f"Error calculating technical score: {e}")
        
        return max(1.0, min(10.0, score))  # Clamp between 1-10
    
    def _generate_recommendation(
        self, 
        fundamental_score: float, 
        technical_score: float, 
        info: EnhancedStockInfo
    ) -> tuple[str, float]:
        """Generate overall recommendation and confidence."""
        try:
            # Weight the scores
            overall_score = (fundamental_score * 0.6) + (technical_score * 0.4)
            
            # Generate recommendation
            if overall_score >= 7.0:
                recommendation = "BUY"
                confidence = min(0.9, (overall_score - 7.0) / 3.0 + 0.7)
            elif overall_score <= 4.0:
                recommendation = "SELL"
                confidence = min(0.9, (4.0 - overall_score) / 3.0 + 0.7)
            else:
                recommendation = "HOLD"
                confidence = 0.6
            
            return recommendation, confidence
            
        except Exception as e:
            logger.warning(f"Error generating recommendation: {e}")
            return "HOLD", 0.5
    
    def _generate_insights(
        self, 
        info: EnhancedStockInfo, 
        hist_data: HistoricalData
    ) -> tuple[List[str], List[str]]:
        """Generate strengths and concerns."""
        strengths = []
        concerns = []
        
        try:
            # Fundamental insights
            if info.roe and info.roe > 0.15:
                strengths.append(f"Strong ROE of {info.roe:.1%}")
            elif info.roe and info.roe < 0:
                concerns.append(f"Negative ROE of {info.roe:.1%}")
            
            if info.debt_to_equity and info.debt_to_equity < 0.5:
                strengths.append(f"Low debt-to-equity ratio of {info.debt_to_equity:.2f}")
            elif info.debt_to_equity and info.debt_to_equity > 2.0:
                concerns.append(f"High debt-to-equity ratio of {info.debt_to_equity:.2f}")
            
            if info.dividend_yield and info.dividend_yield > 0.03:
                strengths.append(f"Attractive dividend yield of {info.dividend_yield:.1%}")
            
            # Technical insights
            if info.rsi and info.rsi < 30:
                strengths.append(f"RSI indicates oversold condition ({info.rsi:.1f})")
            elif info.rsi and info.rsi > 70:
                concerns.append(f"RSI indicates overbought condition ({info.rsi:.1f})")
            
            if hist_data.sharpe_ratio and hist_data.sharpe_ratio > 1.0:
                strengths.append(f"Good risk-adjusted returns (Sharpe: {hist_data.sharpe_ratio:.2f})")
            elif hist_data.sharpe_ratio and hist_data.sharpe_ratio < 0:
                concerns.append(f"Poor risk-adjusted returns (Sharpe: {hist_data.sharpe_ratio:.2f})")
            
            if hist_data.volatility > 0.5:
                concerns.append(f"High volatility ({hist_data.volatility:.1%} annually)")
                
        except Exception as e:
            logger.warning(f"Error generating insights: {e}")
        
        return strengths, concerns

# Global service instance
enhanced_market_service = EnhancedMarketDataService()

class EnhancedMarketDataInput(BaseModel):
    """Input model for enhanced market data tool."""
    symbol: str = Field(..., description="Stock symbol to analyze")
    analysis_type: str = Field("comprehensive", description="Type of analysis: basic, comprehensive, or technical")
    include_recommendations: bool = Field(True, description="Include buy/sell recommendations")

class EnhancedMarketDataTool(BaseTool):
    """Enhanced market data tool combining multiple providers."""
    name: str = "get_enhanced_market_data"
    description: str = """
    Get comprehensive market analysis combining Yahoo Finance and Alpha Vantage data.
    Provides fundamental analysis, technical indicators, and actionable recommendations.
    """
    args_schema: type = EnhancedMarketDataInput

    def _run(
        self, 
        symbol: str,
        analysis_type: str = "comprehensive",
        include_recommendations: bool = True
    ) -> str:
        """Execute enhanced market data analysis."""
        try:
            if analysis_type.lower() == "comprehensive":
                # Full analysis
                enhanced_info = enhanced_market_service.get_enhanced_stock_info(symbol)
                analysis = enhanced_market_service.analyze_stock(symbol)
                
                if not enhanced_info or not analysis:
                    return f"Could not retrieve comprehensive data for {symbol}"
                
                result = {
                    'symbol': symbol.upper(),
                    'current_price': enhanced_info.current_price,
                    'data_sources': enhanced_info.data_sources,
                    'fundamental_metrics': {
                        'pe_ratio': enhanced_info.pe_ratio,
                        'peg_ratio': enhanced_info.peg_ratio,
                        'roe': enhanced_info.roe,
                        'debt_to_equity': enhanced_info.debt_to_equity,
                        'dividend_yield': enhanced_info.dividend_yield
                    },
                    'technical_indicators': {
                        'rsi': enhanced_info.rsi,
                        'macd_signal': enhanced_info.macd_signal
                    },
                    'analysis_scores': {
                        'financial_health': analysis.financial_health_score,
                        'technical_score': analysis.technical_score
                    },
                    'recommendation': {
                        'action': analysis.recommendation,
                        'confidence': f"{analysis.confidence:.1%}",
                        'strengths': analysis.strengths,
                        'concerns': analysis.concerns
                    } if include_recommendations else None,
                    'timestamp': datetime.now().isoformat()
                }
                
                return f"Enhanced market analysis for {symbol}:\n{result}"
                
            else:
                # Basic analysis
                enhanced_info = enhanced_market_service.get_enhanced_stock_info(symbol)
                if not enhanced_info:
                    return f"Could not retrieve basic data for {symbol}"
                
                return f"Basic market data for {symbol}:\n{enhanced_info.dict()}"
                
        except Exception as e:
            logger.error(f"Error in enhanced market data tool: {e}")
            return f"Error fetching enhanced market data: {str(e)}"

# Tool instance
enhanced_market_data_tool = EnhancedMarketDataTool()
