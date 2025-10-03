"""
Advanced portfolio analysis tools.
"""

import logging
import warnings
from typing import Dict, List, Optional
import numpy as np
from datetime import datetime, timedelta

# Suppress empyrical warning - we handle this gracefully
warnings.filterwarnings('ignore', message='empyrical not available')

logger = logging.getLogger(__name__)

class AdvancedPortfolioAnalyzer:
    """Advanced portfolio analysis with risk metrics."""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        
        # Try to import empyrical, but continue without it
        try:
            import empyrical
            self.empyrical_available = True
            self.empyrical = empyrical
        except ImportError:
            self.empyrical_available = False
            logger.debug("empyrical package not available - using basic metrics")
    
    def analyze_portfolio(self, portfolio_data: Dict) -> Dict:
        """
        Analyze portfolio performance and risk metrics.
        Falls back to basic metrics if empyrical not available.
        """
        try:
            returns = self._calculate_returns(portfolio_data)
            
            analysis = {
                "total_value": portfolio_data.get("total_value", 0),
                "cash_allocation": self._calculate_cash_allocation(portfolio_data),
                "asset_allocation": self._calculate_asset_allocation(portfolio_data),
                "basic_metrics": self._calculate_basic_metrics(returns)
            }
            
            # Add advanced metrics if available
            if self.empyrical_available:
                analysis["advanced_metrics"] = self._calculate_advanced_metrics(returns)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Portfolio analysis failed: {e}")
            return {"error": str(e)}
    
# Create service instance
portfolio_analyzer = AdvancedPortfolioAnalyzer()

def portfolio_analysis_tool(portfolio_data: Dict) -> Dict:
    """Tool wrapper for portfolio analysis."""
    try:
        return portfolio_analyzer.analyze_portfolio(portfolio_data)
    except Exception as e:
        return {"error": str(e)}
