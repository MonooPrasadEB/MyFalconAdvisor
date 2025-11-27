"""
Tax Loss Harvesting Service

This service identifies and executes tax-loss harvesting opportunities:
1. Identifies positions with unrealized losses
2. Finds wash-sale compliant alternatives
3. Executes sell + buy trades
4. Tracks wash sale windows (30 days)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pydantic import BaseModel

from ..tools.database_service import database_service
from ..tools.alpaca_trading_service import alpaca_trading_service
from ..tools.compliance_checker import ComplianceChecker

import logging
logger = logging.getLogger(__name__)

# ETF alternatives mapping for wash sale compliance
# Maps common ETFs to similar but not substantially identical alternatives
ETF_ALTERNATIVES = {
    "SPY": ["VOO", "IVV", "SWPPX"],  # S&P 500 ETFs
    "VOO": ["SPY", "IVV", "SWPPX"],
    "IVV": ["SPY", "VOO", "SWPPX"],
    "QQQ": ["ONEQ", "QQQM", "FTEC"],  # Nasdaq ETFs
    "VTI": ["ITOT", "SCHB", "SWTSX"],  # Total Stock Market
    "ITOT": ["VTI", "SCHB", "SWTSX"],
    "VEA": ["IXUS", "IEFA", "VXUS"],  # International Developed
    "VXUS": ["IXUS", "VEA", "IEFA"],  # International Total
    "IXUS": ["VEA", "VXUS", "IEFA"],
    "BND": ["AGG", "SCHZ", "VBTLX"],  # Total Bond Market
    "AGG": ["BND", "SCHZ", "VBTLX"],
    "GLD": ["IAU", "SGOL", "OUNZ"],  # Gold ETFs
    "IAU": ["GLD", "SGOL", "OUNZ"],
    "VNQ": ["SCHH", "USRT", "RWR"],  # REIT ETFs
    "SCHH": ["VNQ", "USRT", "RWR"],
}

# Stock sector alternatives (for individual stocks)
SECTOR_ALTERNATIVES = {
    "technology": ["XLK", "FTEC", "VGT"],
    "healthcare": ["XLV", "VHT", "FHLC"],
    "financial": ["XLF", "VFH", "FNCL"],
    "consumer": ["XLY", "VCR", "FDIS"],
    "energy": ["XLE", "VDE", "FENY"],
    "industrial": ["XLI", "VIS", "FIDU"],
    "materials": ["XLB", "VAW", "FMAT"],
    "utilities": ["XLU", "VPU", "FUTY"],
    "real_estate": ["VNQ", "SCHH", "USRT"],
}


@dataclass
class TaxLossOpportunity:
    """Represents a tax-loss harvesting opportunity"""
    symbol: str
    asset_name: str
    quantity: float
    current_price: float
    cost_basis: float
    current_value: float
    unrealized_loss: float
    loss_percentage: float
    holding_period_days: int
    potential_tax_savings: float
    alternative_symbols: List[str]
    alternative_names: List[str]
    wash_sale_risk: bool
    wash_sale_window_ends: Optional[datetime] = None


class TaxLossHarvestingService:
    """
    Service for identifying and executing tax-loss harvesting opportunities.
    """
    
    def __init__(self):
        self.compliance_checker = ComplianceChecker()
        self.min_loss_threshold = 500.0  # Minimum $500 loss to harvest
        self.min_loss_percentage = 0.05  # Minimum 5% loss
        self.tax_rate = 0.27  # Default 27% tax bracket (can be customized)
        self.wash_sale_window_days = 30
        
    def analyze_portfolio(
        self,
        portfolio_id: str,
        user_id: str,
        tax_rate: Optional[float] = None
    ) -> List[TaxLossOpportunity]:
        """
        Analyze portfolio for tax-loss harvesting opportunities.
        
        Args:
            portfolio_id: Portfolio ID to analyze
            user_id: User ID
            tax_rate: Tax rate for savings calculation (defaults to self.tax_rate)
            
        Returns:
            List of tax-loss harvesting opportunities
        """
        if tax_rate:
            self.tax_rate = tax_rate
            
        logger.info(f"Analyzing portfolio {portfolio_id} for tax-loss harvesting opportunities")
        
        # Get portfolio assets
        assets = database_service.get_portfolio_assets(portfolio_id)
        if not assets:
            logger.warning(f"No assets found for portfolio {portfolio_id}")
            return []
        
        opportunities = []
        
        # Get recent sales to check for wash sale violations
        recent_sales = self._get_recent_sales(user_id, portfolio_id)
        
        for asset in assets:
            opportunity = self._analyze_asset(asset, recent_sales)
            if opportunity:
                opportunities.append(opportunity)
        
        # Sort by potential tax savings (descending)
        opportunities.sort(key=lambda x: x.potential_tax_savings, reverse=True)
        
        logger.info(f"Found {len(opportunities)} tax-loss harvesting opportunities")
        return opportunities
    
    def _analyze_asset(
        self,
        asset: Dict,
        recent_sales: List[Dict]
    ) -> Optional[TaxLossOpportunity]:
        """
        Analyze a single asset for tax-loss harvesting opportunity.
        
        Args:
            asset: Asset dictionary from portfolio_assets
            recent_sales: List of recent sales to check for wash sale violations
            
        Returns:
            TaxLossOpportunity if eligible, None otherwise
        """
        symbol = asset.get("symbol", "").upper()
        quantity = float(asset.get("quantity", 0))
        current_price = float(asset.get("current_price", 0))
        average_cost = float(asset.get("average_cost", 0))
        
        # Skip if no position or missing data
        if quantity <= 0 or current_price <= 0 or average_cost <= 0:
            return None
        
        current_value = quantity * current_price
        cost_basis = quantity * average_cost
        unrealized_loss = current_value - cost_basis
        
        # Only consider losses
        if unrealized_loss >= 0:
            return None
        
        loss_percentage = (unrealized_loss / cost_basis) * 100
        
        # Check minimum thresholds
        if abs(unrealized_loss) < self.min_loss_threshold:
            return None
        
        if abs(loss_percentage) < (self.min_loss_percentage * 100):
            return None
        
        # Calculate holding period (approximate from created_at)
        created_at = asset.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            holding_period = (datetime.now(created_at.tzinfo) - created_at).days
        else:
            holding_period = 365  # Assume long-term if unknown
        
        # Calculate potential tax savings
        potential_tax_savings = abs(unrealized_loss) * self.tax_rate
        
        # Find wash sale compliant alternatives
        alternative_symbols, alternative_names = self._find_alternatives(symbol, asset.get("asset_type"))
        
        # Check for wash sale risk
        wash_sale_risk, wash_sale_window_ends = self._check_wash_sale_risk(
            symbol, recent_sales
        )
        
        return TaxLossOpportunity(
            symbol=symbol,
            asset_name=asset.get("asset_name", symbol),
            quantity=quantity,
            current_price=current_price,
            cost_basis=average_cost,
            current_value=current_value,
            unrealized_loss=unrealized_loss,
            loss_percentage=loss_percentage,
            holding_period_days=holding_period,
            potential_tax_savings=potential_tax_savings,
            alternative_symbols=alternative_symbols,
            alternative_names=alternative_names,
            wash_sale_risk=wash_sale_risk,
            wash_sale_window_ends=wash_sale_window_ends
        )
    
    def _find_alternatives(
        self,
        symbol: str,
        asset_type: Optional[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Find wash sale compliant alternative securities.
        
        Args:
            symbol: Original symbol
            asset_type: Type of asset (stock, etf, etc.)
            
        Returns:
            Tuple of (alternative_symbols, alternative_names)
        """
        symbol_upper = symbol.upper()
        
        # Check ETF alternatives first
        if symbol_upper in ETF_ALTERNATIVES:
            alternatives = ETF_ALTERNATIVES[symbol_upper]
            # Get names for alternatives (simplified - in production, fetch from market data)
            names = [f"{alt} ETF" for alt in alternatives]
            return alternatives, names
        
        # For individual stocks, suggest sector ETFs
        if asset_type == "stock":
            # Try to determine sector (would need to fetch from market data)
            # For now, suggest broad market ETFs
            alternatives = ["VTI", "ITOT", "SCHB"]  # Total stock market ETFs
            names = ["Vanguard Total Stock Market ETF", "iShares Core S&P Total Stock Market ETF", 
                    "Schwab U.S. Broad Market ETF"]
            return alternatives, names
        
        # Default: suggest similar but different ETFs
        return ["VTI"], ["Vanguard Total Stock Market ETF"]
    
    def _check_wash_sale_risk(
        self,
        symbol: str,
        recent_sales: List[Dict]
    ) -> Tuple[bool, Optional[datetime]]:
        """
        Check if selling this symbol would violate wash sale rules.
        
        Args:
            symbol: Symbol to check
            recent_sales: List of recent sales
            
        Returns:
            Tuple of (has_wash_sale_risk, wash_sale_window_ends)
        """
        symbol_upper = symbol.upper()
        cutoff_date = datetime.now() - timedelta(days=self.wash_sale_window_days)
        
        for sale in recent_sales:
            sale_symbol = sale.get("symbol", "").upper()
            sale_date = sale.get("execution_date") or sale.get("created_at")
            
            if not sale_date:
                continue
                
            if isinstance(sale_date, str):
                sale_date = datetime.fromisoformat(sale_date.replace('Z', '+00:00'))
            
            # Check if same symbol was sold within wash sale window
            if sale_symbol == symbol_upper and sale_date >= cutoff_date:
                wash_sale_window_ends = sale_date + timedelta(days=self.wash_sale_window_days)
                return True, wash_sale_window_ends
        
        return False, None
    
    def _get_recent_sales(
        self,
        user_id: str,
        portfolio_id: str,
        days: int = 60
    ) -> List[Dict]:
        """
        Get recent sales from transactions table.
        
        Args:
            user_id: User ID
            portfolio_id: Portfolio ID
            days: Number of days to look back
            
        Returns:
            List of sale transactions
        """
        try:
            session = database_service.get_session()
            if not session:
                logger.warning("Database service not available - returning empty sales list")
                return []
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            from sqlalchemy import text
            
            with session:
                query = text("""
                    SELECT symbol, transaction_type, execution_date, created_at, quantity, price
                    FROM transactions
                    WHERE user_id = :user_id
                      AND portfolio_id = :portfolio_id
                      AND transaction_type = 'SELL'
                      AND status = 'executed'
                      AND (execution_date >= :cutoff_date OR created_at >= :cutoff_date)
                    ORDER BY execution_date DESC, created_at DESC
                """)
                
                result = session.execute(query, {
                    "user_id": user_id,
                    "portfolio_id": portfolio_id,
                    "cutoff_date": cutoff_date
                })
                
                rows = result.fetchall()
                if rows:
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in rows]
                return []
        except Exception as e:
            logger.error(f"Error fetching recent sales: {e}")
            return []
    
    def execute_harvest(
        self,
        portfolio_id: str,
        user_id: str,
        opportunity: TaxLossOpportunity,
        alternative_symbol: Optional[str] = None,
        reinvest: bool = True
    ) -> Dict:
        """
        Execute tax-loss harvesting: sell loss position and optionally buy alternative.
        
        Args:
            portfolio_id: Portfolio ID
            user_id: User ID
            opportunity: TaxLossOpportunity to harvest
            alternative_symbol: Alternative symbol to buy (defaults to first alternative)
            reinvest: Whether to reinvest proceeds in alternative
            
        Returns:
            Dictionary with execution results
        """
        logger.info(f"Executing tax-loss harvest for {opportunity.symbol}")
        
        if opportunity.wash_sale_risk:
            logger.warning(f"Wash sale risk detected for {opportunity.symbol}")
            return {
                "success": False,
                "error": "Wash sale risk: Cannot harvest within 30 days of previous sale",
                "wash_sale_window_ends": opportunity.wash_sale_window_ends.isoformat() if opportunity.wash_sale_window_ends else None
            }
        
        results = {
            "success": False,
            "sell_order": None,
            "buy_order": None,
            "tax_savings": opportunity.potential_tax_savings,
            "realized_loss": opportunity.unrealized_loss,
            "errors": []
        }
        
        try:
            # Step 1: Sell the loss position
            sell_result = alpaca_trading_service.place_order(
                symbol=opportunity.symbol,
                qty=opportunity.quantity,
                side="sell",
                order_type="market",
                time_in_force="day",
                portfolio_id=portfolio_id,
                user_id=user_id
            )
            
            if not sell_result.get("success"):
                results["errors"].append(f"Sell order failed: {sell_result.get('error', 'Unknown error')}")
                return results
            
            results["sell_order"] = sell_result
            logger.info(f"Successfully sold {opportunity.quantity} shares of {opportunity.symbol}")
            
            # Step 2: Optionally buy alternative
            if reinvest and opportunity.alternative_symbols:
                if not alternative_symbol:
                    alternative_symbol = opportunity.alternative_symbols[0]
                
                # Calculate quantity to buy (use proceeds from sale)
                sale_proceeds = opportunity.current_value
                # Get current price of alternative (simplified - in production, fetch real-time)
                # For now, use approximate same value
                buy_qty = opportunity.quantity  # Simplified - should calculate based on alternative price
                
                buy_result = alpaca_trading_service.place_order(
                    symbol=alternative_symbol,
                    qty=buy_qty,
                    side="buy",
                    order_type="market",
                    time_in_force="day",
                    portfolio_id=portfolio_id,
                    user_id=user_id
                )
                
                if buy_result.get("success"):
                    results["buy_order"] = buy_result
                    results["alternative_symbol"] = alternative_symbol
                    logger.info(f"Successfully bought {buy_qty} shares of {alternative_symbol}")
                else:
                    results["errors"].append(f"Buy order failed: {buy_result.get('error', 'Unknown error')}")
                    # Sale succeeded but buy failed - still a partial success
                    logger.warning(f"Tax-loss harvest sale succeeded but buy failed for {alternative_symbol}")
            
            results["success"] = True
            logger.info(f"Tax-loss harvest completed for {opportunity.symbol}")
            
        except Exception as e:
            logger.error(f"Error executing tax-loss harvest: {e}")
            results["errors"].append(str(e))
            results["success"] = False
        
        return results
    
    def get_harvest_summary(
        self,
        opportunities: List[TaxLossOpportunity]
    ) -> Dict:
        """
        Generate summary of tax-loss harvesting opportunities.
        
        Args:
            opportunities: List of opportunities
            
        Returns:
            Summary dictionary
        """
        total_potential_savings = sum(opp.potential_tax_savings for opp in opportunities)
        total_realized_loss = sum(opp.unrealized_loss for opp in opportunities)
        
        return {
            "opportunities_count": len(opportunities),
            "total_potential_savings": total_potential_savings,
            "total_realized_loss": abs(total_realized_loss),
            "average_loss_percentage": sum(opp.loss_percentage for opp in opportunities) / len(opportunities) if opportunities else 0,
            "wash_sale_risks": sum(1 for opp in opportunities if opp.wash_sale_risk),
            "opportunities": [
                {
                    "symbol": opp.symbol,
                    "asset_name": opp.asset_name,
                    "quantity": opp.quantity,
                    "current_price": opp.current_price,
                    "cost_basis": opp.cost_basis,
                    "unrealized_loss": opp.unrealized_loss,
                    "loss_percentage": opp.loss_percentage,
                    "potential_tax_savings": opp.potential_tax_savings,
                    "alternative_symbols": opp.alternative_symbols,
                    "wash_sale_risk": opp.wash_sale_risk,
                }
                for opp in opportunities
            ]
        }


# Singleton instance
tax_loss_harvesting_service = TaxLossHarvestingService()

