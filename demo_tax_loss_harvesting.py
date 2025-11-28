#!/usr/bin/env python3
"""
Tax Loss Harvesting Demo
Demonstrates the tax loss harvesting feature with mock portfolio data
"""

import sys
from datetime import datetime, timedelta
from typing import List, Dict

# Add the project to path
sys.path.insert(0, '/Users/akshay_m3/MyFalconAdvisor/MyFalconAdvisor-1')

from myfalconadvisor.tools.tax_loss_harvesting_service import (
    tax_loss_harvesting_service, 
    TaxLossOpportunity
)

def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_section(text: str):
    """Print a section header"""
    print(f"\n{'─' * 70}")
    print(f"  {text}")
    print(f"{'─' * 70}")

def format_currency(value: float) -> str:
    """Format value as currency"""
    return f"${value:,.2f}"

def format_percent(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.2f}%"

def create_demo_portfolio() -> List[Dict]:
    """Create a mock portfolio with some losses and gains"""
    
    now = datetime.now()
    
    portfolio = [
        {
            "symbol": "SPY",
            "asset_name": "SPDR S&P 500 ETF Trust",
            "quantity": 50.0,
            "current_price": 450.00,  # Down from $500
            "average_cost": 500.00,   # Original purchase price
            "asset_type": "etf",
            "created_at": now - timedelta(days=120),  # Owned for 120 days
            "market_value": 22500.00,
            "sector": "Broad Market"
        },
        {
            "symbol": "QQQ",
            "asset_name": "Invesco QQQ Trust",
            "quantity": 30.0,
            "current_price": 380.00,  # Down from $420
            "average_cost": 420.00,
            "asset_type": "etf",
            "created_at": now - timedelta(days=90),
            "market_value": 11400.00,
            "sector": "Technology"
        },
        {
            "symbol": "AAPL",
            "asset_name": "Apple Inc.",
            "quantity": 20.0,
            "current_price": 180.00,  # Up from $175
            "average_cost": 175.00,
            "asset_type": "stock",
            "created_at": now - timedelta(days=60),
            "market_value": 3600.00,
            "sector": "Technology"
        },
        {
            "symbol": "MSFT",
            "asset_name": "Microsoft Corporation",
            "quantity": 15.0,
            "current_price": 400.00,  # Down from $450
            "average_cost": 450.00,
            "asset_type": "stock",
            "created_at": now - timedelta(days=180),
            "market_value": 6000.00,
            "sector": "Technology"
        },
        {
            "symbol": "VTI",
            "asset_name": "Vanguard Total Stock Market ETF",
            "quantity": 25.0,
            "current_price": 220.00,  # Down from $240
            "average_cost": 240.00,
            "asset_type": "etf",
            "created_at": now - timedelta(days=200),
            "market_value": 5500.00,
            "sector": "Broad Market"
        },
        {
            "symbol": "BND",
            "asset_name": "Vanguard Total Bond Market ETF",
            "quantity": 40.0,
            "current_price": 75.00,   # Down from $80
            "average_cost": 80.00,
            "asset_type": "etf",
            "created_at": now - timedelta(days=150),
            "market_value": 3000.00,
            "sector": "Fixed Income"
        }
    ]
    
    return portfolio

def analyze_opportunities(portfolio: List[Dict]) -> List[TaxLossOpportunity]:
    """Analyze portfolio for tax loss harvesting opportunities"""
    
    opportunities = []
    
    for asset in portfolio:
        # Use the service's analyze method logic
        opportunity = tax_loss_harvesting_service._analyze_asset(asset, [])
        if opportunity:
            opportunities.append(opportunity)
    
    # Sort by potential tax savings
    opportunities.sort(key=lambda x: x.potential_tax_savings, reverse=True)
    
    return opportunities

def display_portfolio(portfolio: List[Dict]):
    """Display the portfolio holdings"""
    print_section("📊 Current Portfolio Holdings")
    
    total_value = 0
    total_cost = 0
    
    print(f"\n{'Symbol':<8} {'Name':<30} {'Shares':>8} {'Cost':>12} {'Current':>12} {'Value':>12} {'P/L':>12} {'P/L %':>8}")
    print("─" * 110)
    
    for asset in portfolio:
        symbol = asset["symbol"]
        name = asset["asset_name"][:28]  # Truncate long names
        quantity = asset["quantity"]
        cost_basis = asset["average_cost"]
        current_price = asset["current_price"]
        current_value = quantity * current_price
        cost_total = quantity * cost_basis
        pnl = current_value - cost_total
        pnl_percent = (pnl / cost_total) * 100 if cost_total > 0 else 0
        
        total_value += current_value
        total_cost += cost_total
        
        # Color coding
        pnl_color = "🔴" if pnl < 0 else "🟢" if pnl > 0 else "⚪"
        pnl_sign = "+" if pnl >= 0 else ""
        
        print(f"{symbol:<8} {name:<30} {quantity:>8.2f} {format_currency(cost_basis):>12} "
              f"{format_currency(current_price):>12} {format_currency(current_value):>12} "
              f"{pnl_color} {pnl_sign}{format_currency(pnl):>10} {pnl_sign}{format_percent(pnl_percent):>7}")
    
    print("─" * 110)
    total_pnl = total_value - total_cost
    total_pnl_percent = (total_pnl / total_cost) * 100 if total_cost > 0 else 0
    pnl_sign = "+" if total_pnl >= 0 else ""
    
    print(f"{'TOTAL':<8} {'Portfolio Total':<30} {'':>8} {format_currency(total_cost):>12} "
          f"{'':>12} {format_currency(total_value):>12} "
          f"{pnl_sign}{format_currency(total_pnl):>12} {pnl_sign}{format_percent(total_pnl_percent):>8}")

def display_opportunities(opportunities: List[TaxLossOpportunity]):
    """Display tax loss harvesting opportunities"""
    
    if not opportunities:
        print("\n✅ No tax loss harvesting opportunities found.")
        print("   All positions are either at a gain or losses are below the minimum threshold.")
        return
    
    print_section(f"💰 Tax Loss Harvesting Opportunities ({len(opportunities)} found)")
    
    total_savings = sum(opp.potential_tax_savings for opp in opportunities)
    total_loss = sum(opp.unrealized_loss for opp in opportunities)
    
    print(f"\n{'#':<4} {'Symbol':<8} {'Loss':>12} {'Loss %':>8} {'Tax Savings':>14} {'Alternatives':<30}")
    print("─" * 90)
    
    for i, opp in enumerate(opportunities, 1):
        alternatives_str = ", ".join(opp.alternative_symbols[:3])  # Show first 3
        
        print(f"{i:<4} {opp.symbol:<8} {format_currency(abs(opp.unrealized_loss)):>12} "
              f"{format_percent(opp.loss_percentage):>8} {format_currency(opp.potential_tax_savings):>14} "
              f"{alternatives_str:<30}")
    
    print("─" * 90)
    print(f"{'TOTAL':<4} {'All':<8} {format_currency(abs(total_loss)):>12} "
          f"{'':>8} {format_currency(total_savings):>14} {'':<30}")

def display_detailed_opportunity(opportunity: TaxLossOpportunity, index: int):
    """Display detailed information about a specific opportunity"""
    
    print_section(f"📋 Opportunity #{index}: {opportunity.symbol}")
    
    print(f"\n📊 Position Details:")
    print(f"   Symbol:              {opportunity.symbol}")
    print(f"   Asset Name:          {opportunity.asset_name}")
    print(f"   Quantity:            {opportunity.quantity:.2f} shares")
    print(f"   Current Price:       {format_currency(opportunity.current_price)}")
    print(f"   Cost Basis:          {format_currency(opportunity.cost_basis)} per share")
    print(f"   Current Value:       {format_currency(opportunity.current_value)}")
    print(f"   Unrealized Loss:     {format_currency(opportunity.unrealized_loss)} ({format_percent(opportunity.loss_percentage)})")
    print(f"   Holding Period:      {opportunity.holding_period_days} days")
    
    print(f"\n💵 Tax Benefits:")
    print(f"   Potential Savings:   {format_currency(opportunity.potential_tax_savings)}")
    print(f"   Tax Rate Used:       {tax_loss_harvesting_service.tax_rate * 100}%")
    
    print(f"\n🔄 Alternatives (Wash Sale Compliant):")
    for alt_symbol, alt_name in zip(opportunity.alternative_symbols, opportunity.alternative_names):
        print(f"   • {alt_symbol}: {alt_name}")
    
    if opportunity.wash_sale_risk:
        print(f"\n⚠️  Wash Sale Risk:")
        print(f"   Cannot harvest within 30 days of previous sale")
        if opportunity.wash_sale_window_ends:
            print(f"   Window ends: {opportunity.wash_sale_window_ends.strftime('%Y-%m-%d')}")
    else:
        print(f"\n✅ Wash Sale Status: Clear (no recent sales detected)")

def demonstrate_execution_flow():
    """Demonstrate what happens when executing a harvest"""
    
    print_section("🚀 Execution Flow Demonstration")
    
    print("\nWhen you execute tax loss harvesting, here's what happens:\n")
    
    print("Step 1: Sell the loss position")
    print("   📤 Sell 50 shares of SPY at $450/share")
    print("   💰 Receive: $22,500")
    print("   📉 Realize loss: -$2,500")
    
    print("\nStep 2: Buy alternative immediately")
    print("   📥 Buy 50 shares of VOO at $450/share")
    print("   💰 Invest: $22,500")
    print("   ✅ Maintain market exposure")
    
    print("\nStep 3: Tax benefits")
    print("   💵 Tax loss: -$2,500")
    print("   💰 Tax savings: $675 (at 27% tax rate)")
    print("   📋 Can offset capital gains or reduce taxable income")
    
    print("\nStep 4: Result")
    print("   ✅ You still own S&P 500 exposure (via VOO)")
    print("   ✅ You can claim the $2,500 loss on taxes")
    print("   ✅ You save $675 in taxes this year")
    print("   ✅ No wash sale violation (different ETF)")

def main():
    """Run the tax loss harvesting demo"""
    
    print_header("🦅 Tax Loss Harvesting Demo")
    
    print("\nWelcome to the Tax Loss Harvesting demonstration!")
    print("This demo shows how the system identifies and executes tax-saving opportunities.")
    
    # Create demo portfolio
    portfolio = create_demo_portfolio()
    
    # Display portfolio
    display_portfolio(portfolio)
    
    # Analyze for opportunities
    print_section("🔍 Analyzing Portfolio for Tax Loss Opportunities")
    print("\nAnalyzing positions with losses > $500 and > 5%...")
    
    opportunities = analyze_opportunities(portfolio)
    
    # Display opportunities
    display_opportunities(opportunities)
    
    # Show detailed view of first opportunity
    if opportunities:
        display_detailed_opportunity(opportunities[0], 1)
        
        # Show execution flow
        demonstrate_execution_flow()
        
        # Summary
        print_section("📊 Summary")
        total_savings = sum(opp.potential_tax_savings for opp in opportunities)
        total_loss = sum(opp.unrealized_loss for opp in opportunities)
        
        print(f"\n💰 Total Potential Tax Savings: {format_currency(total_savings)}")
        print(f"📉 Total Realized Losses: {format_currency(abs(total_loss))}")
        print(f"📈 Number of Opportunities: {len(opportunities)}")
        print(f"\n💡 By harvesting these losses, you could save {format_currency(total_savings)} in taxes!")
        print("   while maintaining your market exposure through alternative ETFs.")
    else:
        print("\n💡 This portfolio doesn't have eligible losses for harvesting.")
        print("   The system only harvests losses that are:")
        print("   • Greater than $500 in value")
        print("   • Greater than 5% loss percentage")
    
    print_section("🎓 How It Works")
    print("""
1. The system scans your portfolio for positions with unrealized losses
2. It filters for losses above minimum thresholds ($500 and 5%)
3. It checks for wash sale violations (30-day window)
4. It finds compliant alternatives (similar but different ETFs)
5. It calculates potential tax savings
6. You can execute the harvest to realize losses and buy alternatives
7. You save on taxes while staying invested in the market!
    """)
    
    print_header("✅ Demo Complete")
    print("\nTo use this feature with your real portfolio:")
    print("1. Connect to your database with portfolio data")
    print("2. Call: GET /tax-loss-harvesting/analyze")
    print("3. Execute: POST /tax-loss-harvesting/execute")
    print("\nSee TAX_LOSS_HARVESTING.md for full documentation!")

if __name__ == "__main__":
    main()

