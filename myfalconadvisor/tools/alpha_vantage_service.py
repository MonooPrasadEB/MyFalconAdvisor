"""Alpha Vantage API integration for premium financial data."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import time

from ..core.config import Config

config = Config.get_instance()
logger = logging.getLogger(__name__)

class AlphaVantageRateLimiter:
    """Rate limiter for Alpha Vantage API (5 requests per minute)."""
    
    def __init__(self, max_requests: int = 5, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def wait_if_needed(self):
        """Wait if we've hit the rate limit."""
        now = time.time()
        
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.time_window]
        
        # If we're at the limit, wait
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]) + 1
            logger.info(f"Rate limit reached. Waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
            self.requests = []
        
        # Record this request
        self.requests.append(now)

class TechnicalIndicator(BaseModel):
    """Technical indicator data model."""
    symbol: str
    indicator: str
    period: int
    data: List[Dict[str, Union[str, float]]]
    last_updated: datetime

class FundamentalData(BaseModel):
    """Fundamental data model."""
    symbol: str
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    dividend_yield: Optional[float] = None
    eps: Optional[float] = None
    revenue_ttm: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    profit_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    beta: Optional[float] = None
    analyst_target_price: Optional[float] = None

class EconomicIndicator(BaseModel):
    """Economic indicator data model."""
    indicator: str
    name: str
    data: List[Dict[str, Union[str, float]]]
    unit: str
    last_updated: datetime

class NewsSentiment(BaseModel):
    """News sentiment data model."""
    symbol: str
    overall_sentiment_score: float
    overall_sentiment_label: str  # Bearish, Somewhat-Bearish, Neutral, Somewhat-Bullish, Bullish
    articles: List[Dict[str, Any]]
    last_updated: datetime

class AlphaVantageService:
    """Service for Alpha Vantage API integration."""
    
    def __init__(self):
        self.api_key = config.alpha_vantage_api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limiter = AlphaVantageRateLimiter()
        self.cache = {}
        self.cache_duration = timedelta(hours=config.cache_duration_hours)
    
    def _make_request(self, params: Dict[str, str]) -> Optional[Dict]:
        """Make API request with rate limiting."""
        if not self.api_key:
            logger.error("Alpha Vantage API key not configured")
            return None
        
        # Add API key to parameters
        params['apikey'] = self.api_key
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for API error messages
            if "Error Message" in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return None
            elif "Note" in data:
                logger.warning(f"Alpha Vantage API note: {data['Note']}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Alpha Vantage API request failed: {e}")
            return None
        except ValueError as e:
            logger.error(f"Alpha Vantage API response parsing failed: {e}")
            return None
    
    def get_company_overview(self, symbol: str) -> Optional[FundamentalData]:
        """Get comprehensive company fundamental data."""
        cache_key = f"overview_{symbol}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
        
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        if not data:
            return None
        
        try:
            def safe_float(value):
                """Safely convert to float, return None if not possible."""
                if value == 'None' or value == '-' or not value:
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            fundamental_data = FundamentalData(
                symbol=symbol.upper(),
                market_cap=safe_float(data.get('MarketCapitalization')),
                pe_ratio=safe_float(data.get('PERatio')),
                peg_ratio=safe_float(data.get('PEGRatio')),
                price_to_book=safe_float(data.get('PriceToBookRatio')),
                dividend_yield=safe_float(data.get('DividendYield')),
                eps=safe_float(data.get('EPS')),
                revenue_ttm=safe_float(data.get('RevenueTTM')),
                gross_margin=safe_float(data.get('GrossProfitTTM')),
                operating_margin=safe_float(data.get('OperatingMarginTTM')),
                profit_margin=safe_float(data.get('ProfitMargin')),
                roe=safe_float(data.get('ReturnOnEquityTTM')),
                roa=safe_float(data.get('ReturnOnAssetsTTM')),
                debt_to_equity=safe_float(data.get('DebtToEquityRatio')),
                current_ratio=safe_float(data.get('CurrentRatio')),
                beta=safe_float(data.get('Beta')),
                analyst_target_price=safe_float(data.get('AnalystTargetPrice'))
            )
            
            # Cache result
            self.cache[cache_key] = (fundamental_data, datetime.now())
            return fundamental_data
            
        except Exception as e:
            logger.error(f"Error parsing company overview for {symbol}: {e}")
            return None
    
    def get_technical_indicator(
        self, 
        symbol: str, 
        indicator: str, 
        interval: str = "daily",
        time_period: int = 14
    ) -> Optional[TechnicalIndicator]:
        """Get technical indicator data."""
        cache_key = f"tech_{symbol}_{indicator}_{interval}_{time_period}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
        
        # Map indicator names to Alpha Vantage function names
        indicator_functions = {
            'RSI': 'RSI',
            'MACD': 'MACD',
            'SMA': 'SMA',
            'EMA': 'EMA',
            'BBANDS': 'BBANDS',
            'STOCH': 'STOCH',
            'ADX': 'ADX',
            'CCI': 'CCI',
            'AROON': 'AROON',
            'OBV': 'OBV'
        }
        
        if indicator.upper() not in indicator_functions:
            logger.error(f"Unsupported technical indicator: {indicator}")
            return None
        
        params = {
            'function': indicator_functions[indicator.upper()],
            'symbol': symbol,
            'interval': interval,
            'time_period': str(time_period)
        }
        
        data = self._make_request(params)
        if not data:
            return None
        
        try:
            # Extract the technical indicator data
            tech_data_key = f"Technical Analysis: {indicator.upper()}"
            if tech_data_key not in data:
                logger.error(f"Technical indicator data not found for {symbol}")
                return None
            
            tech_data = data[tech_data_key]
            
            # Convert to list of dictionaries
            indicator_data = []
            for date, values in tech_data.items():
                entry = {'date': date}
                for key, value in values.items():
                    try:
                        entry[key] = float(value)
                    except (ValueError, TypeError):
                        entry[key] = value
                indicator_data.append(entry)
            
            # Sort by date (newest first)
            indicator_data.sort(key=lambda x: x['date'], reverse=True)
            
            technical_indicator = TechnicalIndicator(
                symbol=symbol.upper(),
                indicator=indicator.upper(),
                period=time_period,
                data=indicator_data,
                last_updated=datetime.now()
            )
            
            # Cache result
            self.cache[cache_key] = (technical_indicator, datetime.now())
            return technical_indicator
            
        except Exception as e:
            logger.error(f"Error parsing technical indicator {indicator} for {symbol}: {e}")
            return None
    
    def get_economic_indicator(self, indicator: str) -> Optional[EconomicIndicator]:
        """Get economic indicator data from FRED."""
        cache_key = f"econ_{indicator}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
        
        # Map common economic indicators
        economic_functions = {
            'GDP': 'REAL_GDP',
            'INFLATION': 'CPI', 
            'UNEMPLOYMENT': 'UNEMPLOYMENT',
            'FEDERAL_FUNDS_RATE': 'FEDERAL_FUNDS_RATE',
            'TREASURY_YIELD': 'TREASURY_YIELD'
        }
        
        if indicator.upper() not in economic_functions:
            logger.error(f"Unsupported economic indicator: {indicator}")
            return None
        
        params = {
            'function': economic_functions[indicator.upper()],
            'interval': 'monthly'
        }
        
        data = self._make_request(params)
        if not data:
            return None
        
        try:
            # Extract economic data (structure varies by indicator)
            data_key = 'data'
            if data_key not in data:
                logger.error(f"Economic indicator data not found for {indicator}")
                return None
            
            econ_data = []
            for entry in data[data_key]:
                econ_data.append({
                    'date': entry.get('date'),
                    'value': float(entry.get('value', 0))
                })
            
            economic_indicator = EconomicIndicator(
                indicator=indicator.upper(),
                name=data.get('name', indicator),
                data=econ_data,
                unit=data.get('unit', ''),
                last_updated=datetime.now()
            )
            
            # Cache result
            self.cache[cache_key] = (economic_indicator, datetime.now())
            return economic_indicator
            
        except Exception as e:
            logger.error(f"Error parsing economic indicator {indicator}: {e}")
            return None
    
    def get_news_sentiment(self, symbol: str) -> Optional[NewsSentiment]:
        """Get news and sentiment analysis for a symbol."""
        cache_key = f"news_{symbol}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(hours=1):  # News expires faster
                return cached_data
        
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': symbol,
            'limit': '50'
        }
        
        data = self._make_request(params)
        if not data:
            return None
        
        try:
            sentiment_data = NewsSentiment(
                symbol=symbol.upper(),
                overall_sentiment_score=float(data.get('overall_sentiment_score', 0)),
                overall_sentiment_label=data.get('overall_sentiment_label', 'Neutral'),
                articles=data.get('feed', []),
                last_updated=datetime.now()
            )
            
            # Cache result
            self.cache[cache_key] = (sentiment_data, datetime.now())
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error parsing news sentiment for {symbol}: {e}")
            return None

# Global service instance
alpha_vantage_service = AlphaVantageService()

class AlphaVantageInput(BaseModel):
    """Input model for Alpha Vantage tool."""
    symbol: str = Field(..., description="Stock symbol to analyze")
    include_fundamentals: bool = Field(True, description="Include fundamental analysis")
    include_technicals: bool = Field(True, description="Include technical indicators")
    include_news: bool = Field(False, description="Include news sentiment analysis")
    technical_indicators: List[str] = Field(["RSI", "MACD"], description="Technical indicators to fetch")

class AlphaVantageTool(BaseTool):
    """Tool for Alpha Vantage premium financial data."""
    name: str = "get_alpha_vantage_data"
    description: str = """
    Fetch premium financial data from Alpha Vantage including:
    - Comprehensive fundamental analysis
    - Technical indicators (RSI, MACD, Bollinger Bands, etc.)
    - News sentiment analysis
    - Economic indicators
    """
    args_schema: type = AlphaVantageInput

    def _run(
        self, 
        symbol: str,
        include_fundamentals: bool = True,
        include_technicals: bool = True,
        include_news: bool = False,
        technical_indicators: List[str] = ["RSI", "MACD"]
    ) -> str:
        """Execute Alpha Vantage data fetch."""
        try:
            result = {
                'symbol': symbol.upper(),
                'timestamp': datetime.now().isoformat(),
                'data_sources': ['Alpha Vantage']
            }
            
            # Get fundamental data
            if include_fundamentals:
                fundamentals = alpha_vantage_service.get_company_overview(symbol)
                if fundamentals:
                    result['fundamentals'] = fundamentals.dict()
            
            # Get technical indicators
            if include_technicals:
                result['technical_indicators'] = {}
                for indicator in technical_indicators:
                    tech_data = alpha_vantage_service.get_technical_indicator(symbol, indicator)
                    if tech_data:
                        # Include only recent data points (last 30 days)
                        recent_data = tech_data.data[:30] if len(tech_data.data) > 30 else tech_data.data
                        result['technical_indicators'][indicator] = {
                            'indicator': tech_data.indicator,
                            'period': tech_data.period,
                            'recent_data': recent_data,
                            'latest_value': recent_data[0] if recent_data else None
                        }
            
            # Get news sentiment
            if include_news:
                news = alpha_vantage_service.get_news_sentiment(symbol)
                if news:
                    result['news_sentiment'] = {
                        'overall_score': news.overall_sentiment_score,
                        'overall_label': news.overall_sentiment_label,
                        'article_count': len(news.articles),
                        'recent_articles': news.articles[:5]  # Top 5 articles
                    }
            
            return f"Alpha Vantage data retrieved for {symbol}:\n{result}"
            
        except Exception as e:
            logger.error(f"Error in Alpha Vantage tool: {e}")
            return f"Error fetching Alpha Vantage data: {str(e)}"

# Tool instance
alpha_vantage_tool = AlphaVantageTool()
