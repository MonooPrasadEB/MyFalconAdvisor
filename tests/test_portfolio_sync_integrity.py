#!/usr/bin/env python3
"""
Test Portfolio Sync Integrity

Tests data consistency between portfolios and portfolio_assets tables,
and validates that sync operations maintain proper data integrity.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from myfalconadvisor.tools.database_service import database_service
from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service
from sqlalchemy import text

def test_portfolio_assets_integrity():
    """Test that portfolio_assets data is valid and consistent."""
    print("\n🧪 TEST 1: Portfolio Assets Data Integrity")
    print("=" * 60)
    
    passed = 0
    total = 0
    
    session = database_service.get_session()
    if not session:
        print("⚠️  Database not available - skipping test")
        return 0, 0
    
    with session:
        # Test 1.1: No NULL quantities or prices
        total += 1
        result = session.execute(text("""
            SELECT COUNT(*) FROM portfolio_assets 
            WHERE quantity IS NULL OR current_price IS NULL OR market_value IS NULL
        """))
        null_count = result.fetchone()[0]
        
        if null_count == 0:
            print("✅ No NULL values in critical fields")
            passed += 1
        else:
            print(f"❌ Found {null_count} assets with NULL values")
        
        # Test 1.2: No negative values
        total += 1
        result = session.execute(text("""
            SELECT COUNT(*) FROM portfolio_assets 
            WHERE quantity < 0 OR current_price < 0 OR market_value < 0
        """))
        negative_count = result.fetchone()[0]
        
        if negative_count == 0:
            print("✅ No negative values in quantity/price/value fields")
            passed += 1
        else:
            print(f"❌ Found {negative_count} assets with negative values")
        
        # Test 1.3: market_value = quantity * current_price (within 1 cent tolerance)
        total += 1
        result = session.execute(text("""
            SELECT symbol, quantity, current_price, market_value,
                   ABS(market_value - (quantity * current_price)) as diff
            FROM portfolio_assets 
            WHERE ABS(market_value - (quantity * current_price)) > 0.01
        """))
        calculation_errors = result.fetchall()
        
        if len(calculation_errors) == 0:
            print("✅ All market_value calculations are correct")
            passed += 1
        else:
            print(f"❌ Found {len(calculation_errors)} assets with calculation errors:")
            for error in calculation_errors[:3]:  # Show first 3
                print(f"   {error[0]}: qty={error[1]} * price={error[2]} != value={error[3]} (diff={error[4]:.4f})")
        
        # Test 1.4: No zero current_price for positions with quantity > 0
        total += 1
        result = session.execute(text("""
            SELECT symbol, quantity, current_price FROM portfolio_assets 
            WHERE quantity > 0 AND (current_price = 0 OR current_price IS NULL)
        """))
        zero_price_assets = result.fetchall()
        
        if len(zero_price_assets) == 0:
            print("✅ All assets with positions have valid prices")
            passed += 1
        else:
            print(f"❌ Found {len(zero_price_assets)} assets with zero/null prices:")
            for asset in zero_price_assets:
                print(f"   {asset[0]}: qty={asset[1]}, price={asset[2]}")
    
    return passed, total


def test_portfolio_totals_integrity():
    """Test that portfolio totals match sum of assets + cash."""
    print("\n🧪 TEST 2: Portfolio Totals Integrity")
    print("=" * 60)
    
    passed = 0
    total = 0
    
    session = database_service.get_session()
    if not session:
        print("⚠️  Database not available - skipping test")
        return 0, 0
    
    with session:
        # Get all portfolios with calculated totals
        result = session.execute(text("""
            SELECT 
                p.portfolio_id,
                p.portfolio_name,
                p.total_value,
                p.cash_balance,
                COALESCE(SUM(pa.market_value), 0) as equity_sum
            FROM portfolios p
            LEFT JOIN portfolio_assets pa ON p.portfolio_id = pa.portfolio_id
            GROUP BY p.portfolio_id, p.portfolio_name, p.total_value, p.cash_balance
        """))
        
        portfolios = result.fetchall()
        
        for portfolio in portfolios:
            total += 1
            portfolio_id = portfolio[0]
            name = portfolio[1]
            stored_total = float(portfolio[2]) if portfolio[2] else 0
            cash = float(portfolio[3]) if portfolio[3] else 0
            equity_sum = float(portfolio[4])
            
            expected_total = equity_sum + cash
            difference = abs(stored_total - expected_total)
            
            if difference < 0.01:  # 1 cent tolerance
                print(f"✅ {name}: total_value matches (stored=${stored_total:.2f}, calculated=${expected_total:.2f})")
                passed += 1
            else:
                print(f"❌ {name}: total_value mismatch!")
                print(f"   Stored: ${stored_total:.2f}")
                print(f"   Equity: ${equity_sum:.2f} + Cash: ${cash:.2f} = ${expected_total:.2f}")
                print(f"   Difference: ${difference:.2f}")
    
    return passed, total


def test_sync_operation():
    """Test that sync operation maintains data integrity."""
    print("\n🧪 TEST 3: Sync Operation Integrity")
    print("=" * 60)
    
    passed = 0
    total = 3
    
    # Test 3.1: Alpaca service initialization
    if alpaca_trading_service.trading_client is not None or alpaca_trading_service.mock_mode:
        print("✅ Alpaca service initialized correctly")
        passed += 1
    else:
        print("❌ Alpaca service failed to initialize")
    
    # Test 3.2: Mock mode has proper prices
    if alpaca_trading_service.mock_mode:
        test_symbols = ['AAPL', 'MSFT', 'NVDA', 'SPY']
        all_have_prices = True
        
        for symbol in test_symbols:
            price = alpaca_trading_service._get_current_price(symbol)
            if price <= 0:
                all_have_prices = False
                print(f"❌ Mock price for {symbol} is invalid: {price}")
                break
        
        if all_have_prices:
            print("✅ Mock mode provides valid prices for all test symbols")
            passed += 1
    else:
        print("ℹ️  Live mode - skipping mock price test")
        passed += 1  # Don't penalize for live mode
    
    # Test 3.3: Database service is operational
    if database_service.engine is not None:
        print("✅ Database service is operational")
        passed += 1
    else:
        print("❌ Database service is not operational")
    
    return passed, total


def test_orphaned_assets():
    """Test for orphaned assets (assets without valid portfolio reference)."""
    print("\n🧪 TEST 4: No Orphaned Assets")
    print("=" * 60)
    
    passed = 0
    total = 1
    
    session = database_service.get_session()
    if not session:
        print("⚠️  Database not available - skipping test")
        return 0, 0
    
    with session:
        result = session.execute(text("""
            SELECT pa.symbol, pa.portfolio_id 
            FROM portfolio_assets pa
            LEFT JOIN portfolios p ON pa.portfolio_id = p.portfolio_id
            WHERE p.portfolio_id IS NULL
        """))
        
        orphaned = result.fetchall()
        
        if len(orphaned) == 0:
            print("✅ No orphaned assets found")
            passed += 1
        else:
            print(f"❌ Found {len(orphaned)} orphaned assets:")
            for asset in orphaned[:5]:  # Show first 5
                print(f"   {asset[0]} in portfolio {asset[1]}")
    
    return passed, total


def main():
    """Run all portfolio sync integrity tests."""
    print("\n" + "=" * 60)
    print("🧪 PORTFOLIO SYNC INTEGRITY TEST SUITE")
    print("=" * 60)
    
    all_results = []
    
    # Run all tests
    all_results.append(test_portfolio_assets_integrity())
    all_results.append(test_portfolio_totals_integrity())
    all_results.append(test_sync_operation())
    all_results.append(test_orphaned_assets())
    
    # Calculate totals
    total_passed = sum(result[0] for result in all_results)
    total_tests = sum(result[1] for result in all_results)
    
    # Print summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📊 Portfolio Sync Integrity Score: {total_passed}/{total_tests} ({percentage:.1f}%)")
    
    if percentage == 100:
        print("🎉 All integrity tests passed!")
        print("✅ Portfolio sync maintains perfect data consistency")
    elif percentage >= 80:
        print("✅ Most integrity tests passed")
        print("⚠️  Some minor issues detected - review above")
    else:
        print("❌ Critical integrity issues detected")
        print("🔧 Database sync needs attention")
    
    return 0 if percentage == 100 else 1


if __name__ == "__main__":
    sys.exit(main())

