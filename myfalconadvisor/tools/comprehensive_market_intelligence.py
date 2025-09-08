"""Comprehensive Market Intelligence combining Yahoo Finance, Alpha Vantage, and FRED data."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from .market_data import market_data_service
from .alpha_vantage_service import alpha_vantage_service
from .fred_service import fred_service
from ..core.config import Config

config = Config.get_instance()
logger = logging.getLogger(__name__)

class ComprehensiveStockAnalysis(BaseModel):
    """Comprehensive stock analysis with macro context."""
    symbol: str
    analysis_date: datetime
    
    # Price and Performance
    current_price: float = 0.0
    price_changes: Dict[str, float] = {}  # 1d, 1w, 1m, 3m, 1y
    
    # Fundamental Analysis (Alpha Vantage)
    fundamentals: Dict[str, Optional[float]] = {}
    fundamental_score: float = 5.0  # 1-10 scale
    
    # Technical Analysis
    technical_indicators: Dict[str, Any] = {}
    technical_score: float = 5.0  # 1-10 scale
    
    # Macroeconomic Context (FRED)
    macro_context: Dict[str, Any] = {}
    macro_impact: str = "NEUTRAL"  # POSITIVE, NEGATIVE, NEUTRAL
    
    # Sector Analysis
    sector: Optional[str] = None
    sector_performance: Dict[str, float] = {}
    sector_outlook: str = "NEUTRAL"
    
    # Overall Analysis
    overall_score: float = 5.0  # 1-10 scale
    recommendation: str = "HOLD"  # BUY, SELL, HOLD
    confidence: float = 0.5  # 0-1 scale
    target_price: Optional[float] = None
    
    # Risk Assessment
    risk_factors: List[str] = []
    opportunities: List[str] = []
    
    # Investment Thesis
    bull_case: List[str] = []
    bear_case: List[str] = []
    key_catalysts: List[str] = []

class MarketOutlook(BaseModel):
    """Comprehensive market outlook combining all data sources."""
    analysis_date: datetime
    
    # Economic Environment
    economic_phase: str = "EXPANSION"
    recession_probability: float = 0.2
    gdp_growth: Optional[float] = None
    inflation_rate: Optional[float] = None
    interest_rate_environment: str = "RISING"
    
    # Market Conditions
    market_sentiment: str = "NEUTRAL"
    volatility_regime: str = "NORMAL"  # LOW, NORMAL, HIGH
    sector_rotation: Dict[str, str] = {}  # sector -> outlook
    
    # Investment Strategy
    recommended_allocation: Dict[str, float] = {}  # asset_class -> weight
    tactical_recommendations: List[str] = []
    risk_management: List[str] = []
    
    # Key Themes
    dominant_themes: List[str] = []
    emerging_risks: List[str] = []
    investment_opportunities: List[str] = []

class ComprehensiveMarketIntelligence:
    """Comprehensive market intelligence service."""
    
    def __init__(self):
        self.yahoo_service = market_data_service
        self.alpha_vantage_service = alpha_vantage_service
        self.fred_service = fred_service
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
    
    def analyze_stock_comprehensive(self, symbol: str) -> Optional[ComprehensiveStockAnalysis]:
        """Perform comprehensive stock analysis with all data sources."""
        cache_key = f"comprehensive_{symbol}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
        
        try:
            analysis = ComprehensiveStockAnalysis(
                symbol=symbol.upper(),
                analysis_date=datetime.now()
            )
            
            # 1. Get basic stock data (Yahoo Finance)
            yahoo_data = self.yahoo_service.get_stock_info(symbol)
            if not yahoo_data:
                logger.error(f"Could not get basic stock data for {symbol}")
                return None
            
            analysis.current_price = yahoo_data.current_price
            analysis.sector = yahoo_data.sector
            
            # Get historical data for price changes
            historical = self.yahoo_service.get_historical_data(symbol, period="1y")
            if historical and historical.prices:
                analysis.price_changes = self._calculate_price_changes(historical.prices)
            
            # 2. Get fundamental data (Alpha Vantage)
            try:
                av_fundamentals = self.alpha_vantage_service.get_company_overview(symbol)
                if av_fundamentals:
                    analysis.fundamentals = {
                        'pe_ratio': av_fundamentals.pe_ratio,
                        'peg_ratio': av_fundamentals.peg_ratio,
                        'price_to_book': av_fundamentals.price_to_book,
                        'roe': av_fundamentals.roe,
                        'debt_to_equity': av_fundamentals.debt_to_equity,
                        'profit_margin': av_fundamentals.profit_margin,
                        'dividend_yield': av_fundamentals.dividend_yield,
                        'beta': av_fundamentals.beta
                    }
                    analysis.fundamental_score = self._score_fundamentals(analysis.fundamentals)
            except Exception as e:
                logger.warning(f"Could not get Alpha Vantage data for {symbol}: {e}")
            
            # 3. Get macroeconomic context (FRED)
            try:
                macro_context = self.fred_service.get_macroeconomic_context()
                if macro_context:
                    analysis.macro_context = {
                        'economic_phase': macro_context.economic_phase,
                        'gdp_growth': macro_context.gdp_growth,
                        'inflation_rate': macro_context.cpi_inflation,
                        'unemployment_rate': macro_context.unemployment_rate,
                        'federal_funds_rate': macro_context.federal_funds_rate,
                        'yield_curve_slope': macro_context.yield_curve_slope,
                        'market_stress': macro_context.market_stress,
                        'recession_probability': macro_context.recession_probability
                    }
                    analysis.macro_impact = self._assess_macro_impact(analysis.sector, macro_context)
                    analysis.sector_outlook = self._assess_sector_outlook(analysis.sector, macro_context)
            except Exception as e:
                logger.warning(f"Could not get FRED data: {e}")
            
            # 4. Sector performance analysis
            if analysis.sector:
                sector_perf = self.yahoo_service.get_sector_performance()
                if analysis.sector in sector_perf:
                    analysis.sector_performance = sector_perf[analysis.sector]
            
            # 5. Generate comprehensive analysis
            analysis = self._generate_comprehensive_analysis(analysis)
            
            # Cache result
            self.cache[cache_key] = (analysis, datetime.now())
            return analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive stock analysis for {symbol}: {e}")
            return None
    
    def get_market_outlook(self) -> Optional[MarketOutlook]:
        """Get comprehensive market outlook."""
        cache_key = "market_outlook"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < timedelta(hours=2):  # Cache for 2 hours
                return cached_data
        
        try:
            outlook = MarketOutlook(analysis_date=datetime.now())
            
            # Get macroeconomic context
            macro_context = self.fred_service.get_macroeconomic_context()
            if macro_context:
                outlook.economic_phase = macro_context.economic_phase or "EXPANSION"
                outlook.recession_probability = macro_context.recession_probability or 0.2
                outlook.gdp_growth = macro_context.gdp_growth
                outlook.inflation_rate = macro_context.cpi_inflation
                
                # Determine interest rate environment
                if macro_context.federal_funds_rate and macro_context.federal_funds_rate > 4:
                    outlook.interest_rate_environment = "HIGH"
                elif macro_context.federal_funds_rate and macro_context.federal_funds_rate < 2:
                    outlook.interest_rate_environment = "LOW"
                else:
                    outlook.interest_rate_environment = "MODERATE"
                
                # Market sentiment from VIX
                if macro_context.market_stress == "LOW":
                    outlook.market_sentiment = "OPTIMISTIC"
                    outlook.volatility_regime = "LOW"
                elif macro_context.market_stress == "HIGH":
                    outlook.market_sentiment = "PESSIMISTIC"
                    outlook.volatility_regime = "HIGH"
                else:
                    outlook.market_sentiment = "NEUTRAL"
                    outlook.volatility_regime = "NORMAL"
                
                # Sector rotation based on economic phase
                outlook.sector_rotation = self._determine_sector_rotation(macro_context)
                
                # Investment strategy
                outlook = self._generate_investment_strategy(outlook, macro_context)
            
            # Cache result
            self.cache[cache_key] = (outlook, datetime.now())
            return outlook
            
        except Exception as e:
            logger.error(f"Error getting market outlook: {e}")
            return None
    
    def _calculate_price_changes(self, prices: List[Dict]) -> Dict[str, float]:
        """Calculate price changes over different periods."""
        if not prices:
            return {}
        
        current_price = prices[-1]['close']
        changes = {}
        
        # Calculate changes for different periods
        periods = {
            '1d': 1,
            '1w': 7,
            '1m': 30,
            '3m': 90,
            '1y': 252
        }
        
        for period, days in periods.items():
            if len(prices) > days:
                past_price = prices[-(days + 1)]['close']
                change = ((current_price - past_price) / past_price) * 100
                changes[period] = round(change, 2)
        
        return changes
    
    def _score_fundamentals(self, fundamentals: Dict[str, Optional[float]]) -> float:
        """Score fundamental metrics (1-10 scale)."""
        score = 5.0  # Start with neutral
        
        try:
            # P/E ratio scoring
            pe = fundamentals.get('pe_ratio')
            if pe:
                if 10 <= pe <= 20:
                    score += 1.0
                elif pe < 10:
                    score += 0.5
                elif pe > 30:
                    score -= 1.0
            
            # PEG ratio scoring
            peg = fundamentals.get('peg_ratio')
            if peg:
                if peg < 1.0:
                    score += 1.0
                elif peg > 2.0:
                    score -= 0.5
            
            # ROE scoring
            roe = fundamentals.get('roe')
            if roe:
                if roe > 0.15:
                    score += 1.0
                elif roe > 0.10:
                    score += 0.5
                elif roe < 0:
                    score -= 1.0
            
            # Debt-to-equity scoring
            de = fundamentals.get('debt_to_equity')
            if de:
                if de < 0.5:
                    score += 0.5
                elif de > 2.0:
                    score -= 1.0
            
            # Profit margin scoring
            margin = fundamentals.get('profit_margin')
            if margin:
                if margin > 0.20:
                    score += 1.0
                elif margin > 0.10:
                    score += 0.5
                elif margin < 0:
                    score -= 1.0
                    
        except Exception as e:
            logger.warning(f"Error scoring fundamentals: {e}")
        
        return max(1.0, min(10.0, score))
    
    def _assess_macro_impact(self, sector: Optional[str], macro_context) -> str:
        """Assess macroeconomic impact on sector."""
        if not sector or not macro_context:
            return "NEUTRAL"
        
        try:
            # Sector-specific macro sensitivities
            if macro_context.economic_phase == "EXPANSION":
                if sector in ["Technology", "Consumer Discretionary", "Financials"]:
                    return "POSITIVE"
                elif sector in ["Utilities", "Consumer Staples"]:
                    return "NEUTRAL"
            elif macro_context.economic_phase == "CONTRACTION":
                if sector in ["Utilities", "Consumer Staples", "Healthcare"]:
                    return "POSITIVE"
                elif sector in ["Technology", "Consumer Discretionary", "Energy"]:
                    return "NEGATIVE"
            
            # Interest rate sensitivity
            if macro_context.federal_funds_rate and macro_context.federal_funds_rate > 4:
                if sector in ["Real Estate", "Utilities"]:
                    return "NEGATIVE"
                elif sector == "Financials":
                    return "POSITIVE"
            
            return "NEUTRAL"
            
        except Exception as e:
            logger.warning(f"Error assessing macro impact: {e}")
            return "NEUTRAL"
    
    def _assess_sector_outlook(self, sector: Optional[str], macro_context) -> str:
        """Assess sector outlook based on macro conditions."""
        if not sector:
            return "NEUTRAL"
        
        try:
            # Economic phase-based sector outlook
            if macro_context.economic_phase == "EXPANSION":
                growth_sectors = ["Technology", "Consumer Discretionary", "Industrials"]
                if sector in growth_sectors:
                    return "POSITIVE"
            elif macro_context.economic_phase == "CONTRACTION":
                defensive_sectors = ["Utilities", "Consumer Staples", "Healthcare"]
                if sector in defensive_sectors:
                    return "POSITIVE"
                else:
                    return "NEGATIVE"
            
            return "NEUTRAL"
            
        except Exception as e:
            logger.warning(f"Error assessing sector outlook: {e}")
            return "NEUTRAL"
    
    def _generate_comprehensive_analysis(self, analysis: ComprehensiveStockAnalysis) -> ComprehensiveStockAnalysis:
        """Generate comprehensive analysis and recommendations."""
        try:
            # Calculate overall score
            macro_score = 5.0
            if analysis.macro_impact == "POSITIVE":
                macro_score = 7.0
            elif analysis.macro_impact == "NEGATIVE":
                macro_score = 3.0
            
            # Weight the scores
            analysis.overall_score = (
                analysis.fundamental_score * 0.4 +
                analysis.technical_score * 0.3 +
                macro_score * 0.3
            )
            
            # Generate recommendation
            if analysis.overall_score >= 7.0:
                analysis.recommendation = "BUY"
                analysis.confidence = min(0.9, (analysis.overall_score - 7.0) / 3.0 + 0.7)
            elif analysis.overall_score <= 4.0:
                analysis.recommendation = "SELL"
                analysis.confidence = min(0.9, (4.0 - analysis.overall_score) / 3.0 + 0.7)
            else:
                analysis.recommendation = "HOLD"
                analysis.confidence = 0.6
            
            # Generate target price (simple model)
            if analysis.current_price and analysis.fundamentals.get('pe_ratio'):
                sector_pe = 20  # Assume average sector P/E
                fair_pe = min(sector_pe, analysis.fundamentals['pe_ratio'] * 1.1)
                eps = analysis.current_price / analysis.fundamentals['pe_ratio']
                analysis.target_price = eps * fair_pe
            
            # Generate investment thesis
            analysis = self._generate_investment_thesis(analysis)
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Error generating comprehensive analysis: {e}")
            return analysis
    
    def _generate_investment_thesis(self, analysis: ComprehensiveStockAnalysis) -> ComprehensiveStockAnalysis:
        """Generate bull/bear case and key catalysts."""
        try:
            # Bull case
            if analysis.fundamentals.get('roe', 0) > 0.15:
                analysis.bull_case.append("Strong return on equity indicates efficient management")
            
            if analysis.fundamentals.get('profit_margin', 0) > 0.15:
                analysis.bull_case.append("High profit margins suggest competitive advantages")
            
            if analysis.macro_impact == "POSITIVE":
                analysis.bull_case.append("Favorable macroeconomic environment for sector")
            
            if analysis.price_changes.get('1y', 0) > 10:
                analysis.bull_case.append("Strong momentum with positive yearly performance")
            
            # Bear case
            if analysis.fundamentals.get('pe_ratio', 0) > 30:
                analysis.bear_case.append("High valuation may limit upside potential")
            
            if analysis.fundamentals.get('debt_to_equity', 0) > 2.0:
                analysis.bear_case.append("High debt levels increase financial risk")
            
            if analysis.macro_impact == "NEGATIVE":
                analysis.bear_case.append("Challenging macroeconomic environment for sector")
            
            if analysis.price_changes.get('3m', 0) < -10:
                analysis.bear_case.append("Recent negative momentum may continue")
            
            # Key catalysts
            if analysis.sector == "Technology":
                analysis.key_catalysts.extend(["AI adoption", "Cloud migration", "Digital transformation"])
            elif analysis.sector == "Healthcare":
                analysis.key_catalysts.extend(["Drug approvals", "Aging demographics", "Healthcare innovation"])
            elif analysis.sector == "Financials":
                analysis.key_catalysts.extend(["Interest rate changes", "Credit cycle", "Regulatory changes"])
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Error generating investment thesis: {e}")
            return analysis
    
    def _determine_sector_rotation(self, macro_context) -> Dict[str, str]:
        """Determine sector rotation based on economic conditions."""
        rotation = {}
        
        try:
            if macro_context.economic_phase == "EXPANSION":
                rotation.update({
                    "Technology": "OVERWEIGHT",
                    "Consumer Discretionary": "OVERWEIGHT",
                    "Financials": "OVERWEIGHT",
                    "Industrials": "NEUTRAL",
                    "Utilities": "UNDERWEIGHT",
                    "Consumer Staples": "UNDERWEIGHT"
                })
            elif macro_context.economic_phase == "CONTRACTION":
                rotation.update({
                    "Utilities": "OVERWEIGHT",
                    "Consumer Staples": "OVERWEIGHT",
                    "Healthcare": "OVERWEIGHT",
                    "Technology": "UNDERWEIGHT",
                    "Consumer Discretionary": "UNDERWEIGHT",
                    "Energy": "UNDERWEIGHT"
                })
            else:  # TRANSITION
                rotation.update({
                    "Healthcare": "OVERWEIGHT",
                    "Technology": "NEUTRAL",
                    "Utilities": "NEUTRAL",
                    "Consumer Discretionary": "UNDERWEIGHT"
                })
                
        except Exception as e:
            logger.warning(f"Error determining sector rotation: {e}")
        
        return rotation
    
    def _generate_investment_strategy(self, outlook: MarketOutlook, macro_context) -> MarketOutlook:
        """Generate investment strategy recommendations."""
        try:
            # Asset allocation based on economic phase
            if macro_context.economic_phase == "EXPANSION":
                outlook.recommended_allocation = {
                    "Equities": 70.0,
                    "Fixed Income": 20.0,
                    "Commodities": 5.0,
                    "Cash": 5.0
                }
                outlook.tactical_recommendations = [
                    "Overweight growth stocks",
                    "Focus on cyclical sectors",
                    "Consider international exposure"
                ]
            elif macro_context.economic_phase == "CONTRACTION":
                outlook.recommended_allocation = {
                    "Equities": 50.0,
                    "Fixed Income": 35.0,
                    "Commodities": 5.0,
                    "Cash": 10.0
                }
                outlook.tactical_recommendations = [
                    "Emphasize defensive sectors",
                    "Increase quality bias",
                    "Consider dividend-paying stocks"
                ]
            else:  # TRANSITION
                outlook.recommended_allocation = {
                    "Equities": 60.0,
                    "Fixed Income": 30.0,
                    "Commodities": 5.0,
                    "Cash": 5.0
                }
                outlook.tactical_recommendations = [
                    "Maintain balanced approach",
                    "Focus on quality companies",
                    "Monitor economic indicators closely"
                ]
            
            # Risk management
            outlook.risk_management = [
                "Maintain diversification across sectors",
                "Monitor position sizes",
                "Use stop-losses for speculative positions",
                "Regular portfolio rebalancing"
            ]
            
            # Key themes
            outlook.dominant_themes = [
                "AI and Technology Innovation",
                "Energy Transition",
                "Demographic Changes",
                "Geopolitical Tensions"
            ]
            
            if macro_context.recession_probability > 0.5:
                outlook.emerging_risks.extend([
                    "Economic recession",
                    "Credit market stress",
                    "Corporate earnings decline"
                ])
            
            if macro_context.cpi_inflation and macro_context.cpi_inflation > 3:
                outlook.emerging_risks.append("Persistent inflation")
            
            return outlook
            
        except Exception as e:
            logger.warning(f"Error generating investment strategy: {e}")
            return outlook

# Global service instance
comprehensive_market_intelligence = ComprehensiveMarketIntelligence()

class ComprehensiveAnalysisInput(BaseModel):
    """Input model for comprehensive analysis tool."""
    symbol: str = Field(..., description="Stock symbol to analyze")
    include_market_outlook: bool = Field(False, description="Include overall market outlook")

class ComprehensiveMarketIntelligenceTool(BaseTool):
    """Comprehensive market intelligence tool combining all data sources."""
    name: str = "comprehensive_market_analysis"
    description: str = """
    Perform comprehensive market analysis combining Yahoo Finance, Alpha Vantage, and FRED data.
    Provides fundamental analysis, technical indicators, macroeconomic context, and investment recommendations.
    """
    args_schema: type = ComprehensiveAnalysisInput

    def _run(self, symbol: str, include_market_outlook: bool = False) -> str:
        """Execute comprehensive market analysis."""
        try:
            result = {
                'analysis_date': datetime.now().isoformat(),
                'symbol': symbol.upper()
            }
            
            # Get comprehensive stock analysis
            analysis = comprehensive_market_intelligence.analyze_stock_comprehensive(symbol)
            if analysis:
                result['stock_analysis'] = {
                    'current_price': analysis.current_price,
                    'price_changes': analysis.price_changes,
                    'fundamental_score': analysis.fundamental_score,
                    'technical_score': analysis.technical_score,
                    'overall_score': analysis.overall_score,
                    'recommendation': analysis.recommendation,
                    'confidence': f"{analysis.confidence:.1%}",
                    'target_price': analysis.target_price,
                    'sector': analysis.sector,
                    'sector_outlook': analysis.sector_outlook,
                    'macro_impact': analysis.macro_impact,
                    'bull_case': analysis.bull_case,
                    'bear_case': analysis.bear_case,
                    'key_catalysts': analysis.key_catalysts,
                    'risk_factors': analysis.risk_factors,
                    'opportunities': analysis.opportunities
                }
            
            # Get market outlook if requested
            if include_market_outlook:
                outlook = comprehensive_market_intelligence.get_market_outlook()
                if outlook:
                    result['market_outlook'] = {
                        'economic_phase': outlook.economic_phase,
                        'recession_probability': outlook.recession_probability,
                        'market_sentiment': outlook.market_sentiment,
                        'volatility_regime': outlook.volatility_regime,
                        'sector_rotation': outlook.sector_rotation,
                        'recommended_allocation': outlook.recommended_allocation,
                        'tactical_recommendations': outlook.tactical_recommendations,
                        'dominant_themes': outlook.dominant_themes,
                        'emerging_risks': outlook.emerging_risks
                    }
            
            return f"Comprehensive Market Intelligence Analysis:\n{result}"
            
        except Exception as e:
            logger.error(f"Error in comprehensive market intelligence tool: {e}")
            return f"Error performing comprehensive analysis: {str(e)}"

# Tool instance
comprehensive_market_intelligence_tool = ComprehensiveMarketIntelligenceTool()
