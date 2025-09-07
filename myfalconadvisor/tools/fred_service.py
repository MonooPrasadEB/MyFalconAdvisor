"""FRED (Federal Reserve Economic Data) API integration for macroeconomic intelligence."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from ..core.config import Config

config = Config.get_instance()
logger = logging.getLogger(__name__)

class EconomicIndicator(BaseModel):
    """Economic indicator data model."""
    series_id: str
    title: str
    units: str
    frequency: str
    seasonal_adjustment: str
    last_updated: datetime
    data: List[Dict[str, Union[str, float]]]  # [{'date': '2024-01-01', 'value': 3.2}]
    
    # Calculated metrics
    latest_value: Optional[float] = None
    previous_value: Optional[float] = None
    change_percent: Optional[float] = None
    trend: Optional[str] = None  # "RISING", "FALLING", "STABLE"

class MacroeconomicContext(BaseModel):
    """Comprehensive macroeconomic context for investment decisions."""
    analysis_date: datetime
    
    # Growth Indicators
    gdp_growth: Optional[float] = None
    gdp_trend: Optional[str] = None
    
    # Inflation Indicators
    cpi_inflation: Optional[float] = None
    core_inflation: Optional[float] = None
    inflation_trend: Optional[str] = None
    
    # Employment Indicators
    unemployment_rate: Optional[float] = None
    employment_trend: Optional[str] = None
    
    # Interest Rate Environment
    federal_funds_rate: Optional[float] = None
    ten_year_treasury: Optional[float] = None
    yield_curve_slope: Optional[float] = None
    
    # Market Stress Indicators
    vix_level: Optional[float] = None
    market_stress: Optional[str] = None  # "LOW", "MODERATE", "HIGH"
    
    # Economic Phase
    economic_phase: Optional[str] = None  # "EXPANSION", "PEAK", "CONTRACTION", "TROUGH"
    recession_probability: Optional[float] = None
    
    # Investment Implications
    recommended_sectors: List[str] = []
    risk_assessment: str = "MODERATE"
    investment_outlook: str = "NEUTRAL"

class FREDService:
    """Service for FRED API integration."""
    
    def __init__(self):
        self.api_key = config.fred_api_key
        self.base_url = "https://api.stlouisfed.org/fred"
        self.cache = {}
        self.cache_duration = timedelta(hours=6)  # Economic data changes less frequently
        
        # Key economic series IDs
        self.series_map = {
            # GDP and Growth
            'GDP': 'GDP',  # Gross Domestic Product
            'GDPC1': 'GDPC1',  # Real GDP
            'GDPPOT': 'GDPPOT',  # Real Potential GDP
            
            # Inflation
            'CPIAUCSL': 'CPIAUCSL',  # Consumer Price Index
            'CPILFESL': 'CPILFESL',  # Core CPI (ex food & energy)
            'PCEPI': 'PCEPI',  # PCE Price Index
            
            # Employment
            'UNRATE': 'UNRATE',  # Unemployment Rate
            'PAYEMS': 'PAYEMS',  # Nonfarm Payrolls
            'CIVPART': 'CIVPART',  # Labor Force Participation Rate
            
            # Interest Rates
            'FEDFUNDS': 'FEDFUNDS',  # Federal Funds Rate
            'DGS10': 'DGS10',  # 10-Year Treasury Rate
            'DGS2': 'DGS2',  # 2-Year Treasury Rate
            'DGS3MO': 'DGS3MO',  # 3-Month Treasury Rate
            
            # Market Indicators
            'VIXCLS': 'VIXCLS',  # VIX Volatility Index
            'UMCSENT': 'UMCSENT',  # Consumer Sentiment
            'HOUST': 'HOUST',  # Housing Starts
            
            # International
            'DEXUSEU': 'DEXUSEU',  # USD/EUR Exchange Rate
            'DEXJPUS': 'DEXJPUS',  # JPY/USD Exchange Rate
        }
    
    def _make_request(self, endpoint: str, params: Dict[str, str]) -> Optional[Dict]:
        """Make FRED API request."""
        if not self.api_key:
            logger.error("FRED API key not configured")
            return None
        
        # Add API key and format
        params.update({
            'api_key': self.api_key,
            'file_type': 'json'
        })
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if 'error_code' in data:
                logger.error(f"FRED API error: {data.get('error_message', 'Unknown error')}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"FRED API request failed: {e}")
            return None
        except ValueError as e:
            logger.error(f"FRED API response parsing failed: {e}")
            return None
    
    def get_economic_indicator(
        self, 
        series_id: str, 
        limit: int = 100,
        start_date: Optional[str] = None
    ) -> Optional[EconomicIndicator]:
        """Get economic indicator data from FRED."""
        cache_key = f"fred_{series_id}_{limit}_{start_date}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
        
        try:
            # Get series info
            series_params = {'series_id': series_id}
            series_info = self._make_request('series', series_params)
            if not series_info or 'seriess' not in series_info:
                logger.error(f"Could not get series info for {series_id}")
                return None
            
            series_data = series_info['seriess'][0]
            
            # Get observations
            obs_params = {
                'series_id': series_id,
                'limit': str(limit),
                'sort_order': 'desc'
            }
            if start_date:
                obs_params['start_date'] = start_date
            
            observations = self._make_request('series/observations', obs_params)
            if not observations or 'observations' not in observations:
                logger.error(f"Could not get observations for {series_id}")
                return None
            
            # Process data
            data_points = []
            valid_values = []
            
            for obs in observations['observations']:
                try:
                    value = float(obs['value']) if obs['value'] != '.' else None
                    data_points.append({
                        'date': obs['date'],
                        'value': value
                    })
                    if value is not None:
                        valid_values.append(value)
                except (ValueError, TypeError):
                    continue
            
            if not valid_values:
                logger.warning(f"No valid data points for {series_id}")
                return None
            
            # Calculate metrics
            latest_value = valid_values[0] if valid_values else None
            previous_value = valid_values[1] if len(valid_values) > 1 else None
            
            change_percent = None
            trend = None
            if latest_value and previous_value and previous_value != 0:
                change_percent = ((latest_value - previous_value) / previous_value) * 100
                if abs(change_percent) < 0.1:
                    trend = "STABLE"
                elif change_percent > 0:
                    trend = "RISING"
                else:
                    trend = "FALLING"
            
            indicator = EconomicIndicator(
                series_id=series_id,
                title=series_data.get('title', series_id),
                units=series_data.get('units', ''),
                frequency=series_data.get('frequency', ''),
                seasonal_adjustment=series_data.get('seasonal_adjustment', ''),
                last_updated=datetime.now(),
                data=data_points,
                latest_value=latest_value,
                previous_value=previous_value,
                change_percent=change_percent,
                trend=trend
            )
            
            # Cache result
            self.cache[cache_key] = (indicator, datetime.now())
            return indicator
            
        except Exception as e:
            logger.error(f"Error getting economic indicator {series_id}: {e}")
            return None
    
    def get_macroeconomic_context(self) -> Optional[MacroeconomicContext]:
        """Get comprehensive macroeconomic context for investment decisions."""
        try:
            context = MacroeconomicContext(analysis_date=datetime.now())
            
            # Get key indicators
            indicators = {}
            key_series = [
                'GDPC1',      # Real GDP
                'CPIAUCSL',   # CPI
                'CPILFESL',   # Core CPI
                'UNRATE',     # Unemployment
                'FEDFUNDS',   # Fed Funds Rate
                'DGS10',      # 10-Year Treasury
                'DGS2',       # 2-Year Treasury
                'VIXCLS',     # VIX
            ]
            
            for series_id in key_series:
                indicator = self.get_economic_indicator(series_id, limit=12)  # Last 12 observations
                if indicator:
                    indicators[series_id] = indicator
            
            # Process GDP
            if 'GDPC1' in indicators:
                gdp = indicators['GDPC1']
                context.gdp_growth = gdp.change_percent
                context.gdp_trend = gdp.trend
            
            # Process Inflation
            if 'CPIAUCSL' in indicators:
                cpi = indicators['CPIAUCSL']
                context.cpi_inflation = cpi.change_percent
                context.inflation_trend = cpi.trend
            
            if 'CPILFESL' in indicators:
                core_cpi = indicators['CPILFESL']
                context.core_inflation = core_cpi.change_percent
            
            # Process Employment
            if 'UNRATE' in indicators:
                unemployment = indicators['UNRATE']
                context.unemployment_rate = unemployment.latest_value
                context.employment_trend = unemployment.trend
            
            # Process Interest Rates
            if 'FEDFUNDS' in indicators:
                fed_funds = indicators['FEDFUNDS']
                context.federal_funds_rate = fed_funds.latest_value
            
            if 'DGS10' in indicators:
                ten_year = indicators['DGS10']
                context.ten_year_treasury = ten_year.latest_value
            
            # Calculate yield curve slope
            if 'DGS10' in indicators and 'DGS2' in indicators:
                ten_year_rate = indicators['DGS10'].latest_value
                two_year_rate = indicators['DGS2'].latest_value
                if ten_year_rate and two_year_rate:
                    context.yield_curve_slope = ten_year_rate - two_year_rate
            
            # Process Market Stress
            if 'VIXCLS' in indicators:
                vix = indicators['VIXCLS']
                context.vix_level = vix.latest_value
                if vix.latest_value:
                    if vix.latest_value < 20:
                        context.market_stress = "LOW"
                    elif vix.latest_value < 30:
                        context.market_stress = "MODERATE"
                    else:
                        context.market_stress = "HIGH"
            
            # Determine economic phase and investment implications
            context = self._analyze_economic_phase(context)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting macroeconomic context: {e}")
            return None
    
    def _analyze_economic_phase(self, context: MacroeconomicContext) -> MacroeconomicContext:
        """Analyze economic phase and provide investment implications."""
        try:
            # Simple economic phase analysis
            expansion_signals = 0
            contraction_signals = 0
            
            # GDP growth signal
            if context.gdp_growth and context.gdp_growth > 2:
                expansion_signals += 1
            elif context.gdp_growth and context.gdp_growth < 0:
                contraction_signals += 1
            
            # Unemployment signal
            if context.unemployment_rate and context.employment_trend == "FALLING":
                expansion_signals += 1
            elif context.unemployment_rate and context.employment_trend == "RISING":
                contraction_signals += 1
            
            # Yield curve signal
            if context.yield_curve_slope and context.yield_curve_slope > 1:
                expansion_signals += 1
            elif context.yield_curve_slope and context.yield_curve_slope < 0:
                contraction_signals += 2  # Inverted yield curve is strong recession signal
            
            # Market stress signal
            if context.market_stress == "LOW":
                expansion_signals += 1
            elif context.market_stress == "HIGH":
                contraction_signals += 1
            
            # Determine phase
            if expansion_signals > contraction_signals:
                context.economic_phase = "EXPANSION"
                context.recession_probability = 0.2
                context.recommended_sectors = ["Technology", "Consumer Discretionary", "Financials"]
                context.risk_assessment = "MODERATE"
                context.investment_outlook = "POSITIVE"
            elif contraction_signals > expansion_signals:
                context.economic_phase = "CONTRACTION"
                context.recession_probability = 0.7
                context.recommended_sectors = ["Utilities", "Consumer Staples", "Healthcare"]
                context.risk_assessment = "HIGH"
                context.investment_outlook = "DEFENSIVE"
            else:
                context.economic_phase = "TRANSITION"
                context.recession_probability = 0.4
                context.recommended_sectors = ["Healthcare", "Technology", "Utilities"]
                context.risk_assessment = "MODERATE"
                context.investment_outlook = "NEUTRAL"
            
            return context
            
        except Exception as e:
            logger.error(f"Error analyzing economic phase: {e}")
            return context

# Global service instance
fred_service = FREDService()

class FREDInput(BaseModel):
    """Input model for FRED tool."""
    indicators: List[str] = Field(
        default=["GDP", "INFLATION", "UNEMPLOYMENT", "INTEREST_RATES"],
        description="Economic indicators to analyze"
    )
    include_context: bool = Field(True, description="Include macroeconomic context analysis")
    time_period: str = Field("1Y", description="Time period for analysis (1Y, 2Y, 5Y)")

class FREDTool(BaseTool):
    """Tool for FRED economic data analysis."""
    name: str = "get_economic_data"
    description: str = """
    Get comprehensive macroeconomic data and analysis from the Federal Reserve Economic Data (FRED).
    Provides GDP, inflation, employment, interest rates, and market indicators with investment implications.
    """
    args_schema: type = FREDInput

    def _run(
        self, 
        indicators: List[str] = ["GDP", "INFLATION", "UNEMPLOYMENT", "INTEREST_RATES"],
        include_context: bool = True,
        time_period: str = "1Y"
    ) -> str:
        """Execute FRED economic data analysis."""
        try:
            result = {
                'analysis_date': datetime.now().isoformat(),
                'indicators': {},
                'macroeconomic_context': None
            }
            
            # Map indicator names to series IDs
            indicator_map = {
                'GDP': 'GDPC1',
                'INFLATION': 'CPIAUCSL',
                'CORE_INFLATION': 'CPILFESL',
                'UNEMPLOYMENT': 'UNRATE',
                'INTEREST_RATES': 'FEDFUNDS',
                'TREASURY_10Y': 'DGS10',
                'VIX': 'VIXCLS',
                'CONSUMER_SENTIMENT': 'UMCSENT'
            }
            
            # Get requested indicators
            for indicator in indicators:
                series_id = indicator_map.get(indicator.upper())
                if series_id:
                    data = fred_service.get_economic_indicator(series_id, limit=12)
                    if data:
                        result['indicators'][indicator] = {
                            'title': data.title,
                            'latest_value': data.latest_value,
                            'change_percent': data.change_percent,
                            'trend': data.trend,
                            'units': data.units,
                            'recent_data': data.data[:6]  # Last 6 observations
                        }
            
            # Get macroeconomic context if requested
            if include_context:
                context = fred_service.get_macroeconomic_context()
                if context:
                    result['macroeconomic_context'] = {
                        'economic_phase': context.economic_phase,
                        'recession_probability': context.recession_probability,
                        'gdp_growth': context.gdp_growth,
                        'inflation_rate': context.cpi_inflation,
                        'unemployment_rate': context.unemployment_rate,
                        'federal_funds_rate': context.federal_funds_rate,
                        'yield_curve_slope': context.yield_curve_slope,
                        'market_stress': context.market_stress,
                        'recommended_sectors': context.recommended_sectors,
                        'risk_assessment': context.risk_assessment,
                        'investment_outlook': context.investment_outlook
                    }
            
            return f"FRED Economic Analysis:\n{result}"
            
        except Exception as e:
            logger.error(f"Error in FRED tool: {e}")
            return f"Error fetching economic data: {str(e)}"

# Tool instance
fred_tool = FREDTool()
