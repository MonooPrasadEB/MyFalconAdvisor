"""
Test suite for enhanced compliance agent system.

Tests the new dynamic policy engine, compliance scoring, and database integration.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from myfalconadvisor.core.compliance_agent import (
    ComplianceChecker,
    PolicyStore,
    ComplianceRule,
    TradeComplianceCheck,
    PortfolioComplianceCheck,
    default_rules
)
from myfalconadvisor.agents.compliance_adapter import ComplianceAdapter


class TestPolicyStore:
    """Test policy loading and management."""
    
    def test_load_default_rules(self):
        """Test loading default compliance rules."""
        rules_data = default_rules("v1")
        
        assert rules_data["version"] == "v1"
        assert "rules" in rules_data
        assert len(rules_data["rules"]) >= 8  # At least 8 core rules
        
        # Check required rules exist
        required_rules = ["CONC-001", "CONC-002", "SUIT-001", "TAX-001", "TRAD-001", "PENNY-001"]
        for rule_id in required_rules:
            assert rule_id in rules_data["rules"], f"Rule {rule_id} missing"
        
        print(f"✅ Default rules loaded: {len(rules_data['rules'])} rules")
    
    def test_policy_store_initialization(self):
        """Test PolicyStore initialization."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        
        snapshot = store.snapshot()
        assert snapshot.version == "v1"
        assert len(snapshot.rules) >= 8
        assert snapshot.checksum is not None
        
        print(f"✅ PolicyStore initialized with version {snapshot.version}")
        print(f"   Checksum: {snapshot.checksum[:16]}...")
    
    def test_policy_versioning(self):
        """Test policy version tracking."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        
        snapshot = store.snapshot()
        assert snapshot.version == "v1"
        assert snapshot.checksum is not None
        assert snapshot.loaded_at is not None
        
        print(f"✅ Policy versioning working")
        print(f"   Version: {snapshot.version}")
        print(f"   Loaded at: {snapshot.loaded_at}")


class TestComplianceChecker:
    """Test compliance checking logic."""
    
    def test_checker_initialization(self):
        """Test ComplianceChecker initialization."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        checker = ComplianceChecker(store)
        
        assert checker.policy_store is not None
        assert checker.get_rule("CONC-001") is not None
        
        print("✅ ComplianceChecker initialized successfully")
    
    def test_position_concentration_check(self):
        """Test position concentration validation."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        checker = ComplianceChecker(store)
        
        # Test compliant position (20% of portfolio)
        violations = checker.validate_position_concentration(20000, 100000)
        assert len(violations) == 0
        print("✅ Compliant position (20%) passes")
        
        # Test non-compliant position (40% of portfolio)
        violations = checker.validate_position_concentration(40000, 100000)
        assert len(violations) == 1
        assert violations[0].rule_id == "CONC-001"
        print("✅ Non-compliant position (40%) detected")
    
    def test_wash_sale_validation(self):
        """Test IRS wash sale rule validation."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        checker = ComplianceChecker(store)
        
        warnings, violations = checker.validate_wash_sale("buy", "taxable")
        assert len(warnings) > 0 or len(violations) > 0
        print("✅ Wash sale validation working")
    
    def test_pattern_day_trader_check(self):
        """Test FINRA pattern day trader rule."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        checker = ComplianceChecker(store)
        
        # Account under $25K should trigger warning
        warnings, violations = checker.validate_pattern_day_trader(20000, "individual")
        assert len(warnings) > 0 or len(violations) > 0
        print("✅ Pattern day trader rule working (under $25K)")
        
        # Account over $25K should be clean
        warnings, violations = checker.validate_pattern_day_trader(30000, "individual")
        assert len(warnings) == 0 and len(violations) == 0
        print("✅ Pattern day trader rule working (over $25K)")
    
    def test_penny_stock_validation(self):
        """Test SEC penny stock rule (< $5)."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        checker = ComplianceChecker(store)
        
        # Stock under $5 should trigger violation
        violations = checker.validate_penny_stock(4.50)
        assert len(violations) == 1
        assert violations[0].rule_id == "PENNY-001"
        print("✅ Penny stock detection working ($4.50)")
        
        # Stock over $5 should be clean
        violations = checker.validate_penny_stock(10.00)
        assert len(violations) == 0
        print("✅ Penny stock validation working ($10.00)")


class TestTradeComplianceCheck:
    """Test trade-level compliance checking."""
    
    def test_compliant_trade(self):
        """Test a fully compliant trade."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        checker = ComplianceChecker(store)
        
        result = checker.check_trade_compliance(
            trade_type="buy",
            symbol="AAPL",
            quantity=50,
            price=150.0,
            portfolio_value=100000,
            client_type="individual",
            account_type="taxable"
        )
        
        assert isinstance(result, TradeComplianceCheck)
        assert result.trade_approved is not None
        assert result.compliance_score >= 0 and result.compliance_score <= 100
        assert isinstance(result.violations, list)
        assert isinstance(result.warnings, list)
        
        print(f"✅ Compliant trade check passed")
        print(f"   Trade Approved: {result.trade_approved}")
        print(f"   Compliance Score: {result.compliance_score}/100")
        print(f"   Violations: {len(result.violations)}")
    
    def test_concentrated_position_trade(self):
        """Test trade that creates concentration risk."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        checker = ComplianceChecker(store)
        
        # Trade that creates 40% position
        result = checker.check_trade_compliance(
            trade_type="buy",
            symbol="TSLA",
            quantity=200,
            price=200.0,
            portfolio_value=100000,
            client_type="individual",
            account_type="taxable"
        )
        
        # Should have CONC-001 violation
        concentration_violations = [v for v in result.violations if v.rule_id == "CONC-001"]
        assert len(concentration_violations) > 0
        assert result.compliance_score < 100
        
        print(f"✅ Concentration risk detected")
        print(f"   Violations: {len(result.violations)}")
        print(f"   Score: {result.compliance_score}/100")
    
    def test_penny_stock_trade(self):
        """Test penny stock trade."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        checker = ComplianceChecker(store)
        
        result = checker.check_trade_compliance(
            trade_type="buy",
            symbol="PENNY",
            quantity=1000,
            price=3.50,
            portfolio_value=20000,
            client_type="individual",
            account_type="taxable"
        )
        
        # Should have PENNY-001 violation
        penny_violations = [v for v in result.violations if v.rule_id == "PENNY-001"]
        assert len(penny_violations) > 0
        assert result.requires_disclosure
        
        print(f"✅ Penny stock trade detected")
        print(f"   Requires Disclosure: {result.requires_disclosure}")


class TestPortfolioComplianceCheck:
    """Test portfolio-level compliance checking."""
    
    def test_balanced_portfolio(self):
        """Test a well-balanced compliant portfolio."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        checker = ComplianceChecker(store)
        
        assets = [
            {"symbol": "AAPL", "allocation": 20, "sector": "Technology"},
            {"symbol": "MSFT", "allocation": 20, "sector": "Technology"},
            {"symbol": "JPM", "allocation": 20, "sector": "Financial"},
            {"symbol": "JNJ", "allocation": 20, "sector": "Healthcare"},
            {"symbol": "SPY", "allocation": 20, "sector": "ETF"}
        ]
        
        result = checker.check_portfolio_compliance(
            assets=assets,
            portfolio_value=100000,
            client_profile={
                "client_id": "test_001",
                "risk_tolerance": "moderate",
                "target_risk": "moderate"
            }
        )
        
        assert isinstance(result, PortfolioComplianceCheck)
        assert result.compliance_score >= 0 and result.compliance_score <= 100
        
        print(f"✅ Balanced portfolio check passed")
        print(f"   Overall Compliant: {result.overall_compliant}")
        print(f"   Score: {result.compliance_score}/100")
    
    def test_concentrated_sector_portfolio(self):
        """Test portfolio with sector concentration."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        checker = ComplianceChecker(store)
        
        # 70% in technology sector
        assets = [
            {"symbol": "AAPL", "allocation": 30, "sector": "Technology"},
            {"symbol": "MSFT", "allocation": 25, "sector": "Technology"},
            {"symbol": "GOOGL", "allocation": 15, "sector": "Technology"},
            {"symbol": "SPY", "allocation": 30, "sector": "ETF"}
        ]
        
        result = checker.check_portfolio_compliance(
            assets=assets,
            portfolio_value=100000,
            client_profile={
                "client_id": "test_002",
                "risk_tolerance": "moderate",
                "target_risk": "moderate"
            }
        )
        
        # Should have CONC-002 violation (sector concentration)
        sector_violations = [v for v in result.violations if v.rule_id == "CONC-002"]
        assert len(sector_violations) > 0
        
        print(f"✅ Sector concentration detected")
        print(f"   Violations: {len(result.violations)}")


class TestComplianceAdapter:
    """Test the compliance adapter API."""
    
    def test_adapter_initialization(self):
        """Test ComplianceAdapter initialization."""
        adapter = ComplianceAdapter(
            policy_path='myfalconadvisor/core/compliance_policies.json',
            watch=False  # Don't start file watcher in tests
        )
        
        assert adapter.checker is not None
        assert adapter.store is not None
        
        print("✅ ComplianceAdapter initialized successfully")
    
    def test_check_trade_method(self):
        """Test adapter's check_trade method."""
        adapter = ComplianceAdapter(
            policy_path='myfalconadvisor/core/compliance_policies.json',
            watch=False
        )
        
        result = adapter.check_trade(
            trade_type="buy",
            symbol="AAPL",
            quantity=100,
            price=150.0,
            portfolio_value=100000
        )
        
        assert isinstance(result, dict)
        assert "trade_approved" in result
        assert "compliance_score" in result
        assert "violations" in result
        assert "warnings" in result
        
        print(f"✅ check_trade method working")
        print(f"   Score: {result['compliance_score']}/100")
    
    def test_check_portfolio_method(self):
        """Test adapter's check_portfolio method."""
        adapter = ComplianceAdapter(
            policy_path='myfalconadvisor/core/compliance_policies.json',
            watch=False
        )
        
        result = adapter.check_portfolio(
            assets=[
                {"symbol": "AAPL", "allocation": 30, "sector": "Technology"},
                {"symbol": "SPY", "allocation": 70, "sector": "ETF"}
            ],
            portfolio_value=100000,
            client_profile={
                "client_id": "test_003",
                "risk_tolerance": "moderate"
            }
        )
        
        assert isinstance(result, dict)
        assert "overall_compliant" in result
        assert "compliance_score" in result
        
        print(f"✅ check_portfolio method working")
        print(f"   Score: {result['compliance_score']}/100")
    
    def test_get_policies(self):
        """Test retrieving current policies."""
        adapter = ComplianceAdapter(
            policy_path='myfalconadvisor/core/compliance_policies.json',
            watch=False
        )
        
        policies = adapter.get_policies()
        
        assert "version" in policies
        assert "checksum" in policies
        assert "rules" in policies
        assert len(policies["rules"]) >= 8
        
        print(f"✅ get_policies working")
        print(f"   Version: {policies['version']}")
        print(f"   Rules: {len(policies['rules'])}")


class TestComplianceScoring:
    """Test compliance scoring algorithm."""
    
    def test_perfect_score(self):
        """Test that compliant trade gets high score."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        checker = ComplianceChecker(store)
        
        result = checker.check_trade_compliance(
            trade_type="buy",
            symbol="AAPL",
            quantity=50,
            price=150.0,
            portfolio_value=100000,
            client_type="individual",
            account_type="retirement"  # Avoid wash sale warning
        )
        
        # Should have high score with few/no violations
        assert result.compliance_score >= 70, f"Expected high score, got {result.compliance_score}"
        
        print(f"✅ Perfect score test passed: {result.compliance_score}/100")
    
    def test_degraded_score(self):
        """Test that violations reduce score."""
        store = PolicyStore()
        store.load_from_dict(default_rules("v1"))
        checker = ComplianceChecker(store)
        
        # Multiple violations: concentration + penny stock + PDT
        result = checker.check_trade_compliance(
            trade_type="buy",
            symbol="PENNY",
            quantity=1000,
            price=3.50,
            portfolio_value=15000,  # Under $25K
            client_type="individual",
            account_type="taxable"
        )
        
        # Should have lower score due to multiple violations
        assert result.compliance_score < 70, f"Expected low score, got {result.compliance_score}"
        assert len(result.violations) >= 2
        
        print(f"✅ Degraded score test passed: {result.compliance_score}/100")
        print(f"   Violations: {len(result.violations)}")


def run_compliance_agent_tests():
    """Run all compliance agent tests."""
    print("=" * 80)
    print("🧪 MyFalconAdvisor Enhanced Compliance Agent Test Suite")
    print("=" * 80)
    print()
    
    test_classes = [
        TestPolicyStore,
        TestComplianceChecker,
        TestTradeComplianceCheck,
        TestPortfolioComplianceCheck,
        TestComplianceAdapter,
        TestComplianceScoring
    ]
    
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        print(f"\n📋 Testing {test_class.__name__}")
        print("-" * 80)
        
        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
        
        for method_name in test_methods:
            try:
                method = getattr(test_instance, method_name)
                method()
                passed += 1
            except Exception as e:
                print(f"❌ {method_name} failed: {e}")
                failed += 1
    
    print()
    print("=" * 80)
    print("🏁 COMPLIANCE AGENT TEST RESULTS")
    print("=" * 80)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    print()
    
    if failed == 0:
        print("🎉 All compliance agent tests passed!")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_compliance_agent_tests()
    exit(0 if success else 1)

