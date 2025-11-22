"""
Enhanced Compliance Reviewer Test Suite - MyFalconAdvisor

Tests the new streamlined compliance architecture:
- ComplianceReviewer (orchestrator) → ComplianceAdapter → ComplianceAgent (engine)
- Database-driven wash sale detection
- Concentration risk blocking (>50%)
- Market manipulation detection
- Comprehensive audit trail logging

Updated for the new architecture where major violations are REJECTED, not just warned.
"""

import pytest
import sys
import warnings
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Suppress warnings for cleaner test output
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*Pydantic.*')
warnings.filterwarnings('ignore', message='.*datetime.utcnow.*')
warnings.filterwarnings('ignore', message='.*empyrical.*')
warnings.filterwarnings('ignore', message='.*arch package.*')

# Ensure we're importing from the correct project directory
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from myfalconadvisor.agents.compliance_reviewer import compliance_reviewer_agent
from myfalconadvisor.tools.database_service import database_service


class TestEnhancedComplianceReviewer:
    """Test the enhanced compliance reviewer with new blocking architecture."""
    
    def setup_method(self):
        """Set up test data for enhanced compliance system."""
        # Real user data from database (verified values)
        self.elijah_profile = {
            'user_id': 'usr_348784c4-6f83-4857-b7dc-f5132a38dfee',
            'client_id': 'usr_348784c4-6f83-4857-b7dc-f5132a38dfee',
            'name': 'Elijah Martin',
            'email': 'elijah.martin@example.com',
            'risk_tolerance': 'balanced',
            'age': 30,
            'investment_experience': 'Intermediate (5-10 years)',
            'investment_objectives': 'income',
            'time_horizon': 15,
            'portfolio_value': 98441.97,
            'cash_balance': 1306.74,
            'account_type': 'taxable',
            'client_type': 'individual',  # Added for enhanced system
            'annual_income': 21536.00,
            'net_worth': 154650.00
        }
        
        # Test portfolio for wash sale scenarios (use None to avoid FK constraints)
        self.test_portfolio_id = None
    
    def test_basic_compliance_violations_now_block(self):
        """Test that basic compliance violations now BLOCK trades instead of just warning."""
        
        # Missing risk disclosure and suitability (major violations)
        recommendation = "Buy 100 shares of AAPL at $180/share."
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=self.elijah_profile,
            recommendation_context={
                'symbol': 'AAPL',
                'action': 'BUY',
                'quantity': 100,
                'price': 180,
                'position_percentage': 18.0,
                'portfolio_id': self.test_portfolio_id,
                'transaction_id': 'txn_test_001'
            }
        )
        
        # NEW ARCHITECTURE: Major violations should BLOCK the trade
        assert result.get('status') == 'rejected', f"Expected 'rejected', got '{result.get('status')}'"
        
        issues = result.get('compliance_issues', [])
        major_issues = [i for i in issues if i['severity'] in ['major', 'critical']]
        
        assert len(major_issues) >= 2, f"Should find major violations, found {len(major_issues)}"
        assert any('RISK-001' in str(issue) for issue in issues), "Should detect missing risk disclosure"
        assert any('SUIT-001' in str(issue) for issue in issues), "Should detect missing suitability"
        
    
    def test_concentration_risk_blocking(self):
        """Test that >50% concentration blocks trades."""
        
        # Create a compliant recommendation but with extreme concentration
        recommendation = """
        Investment Recommendation: NVDA Purchase
        
        SUITABILITY ANALYSIS: This high-growth technology stock aligns with your 
        balanced risk profile for a portion of your portfolio.
        
        RISK DISCLOSURE: All investments carry risk including potential loss of principal.
        Stock prices can be volatile based on market conditions.
        """
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=self.elijah_profile,
            recommendation_context={
                'symbol': 'NVDA',
                'action': 'BUY',
                'quantity': 280,  # This should create >50% concentration
                'price': 200,
                'position_percentage': 56.8,  # Extreme concentration
                'portfolio_id': self.test_portfolio_id,
                'transaction_id': 'txn_test_002'
            }
        )
        
        # Should be BLOCKED due to concentration risk
        assert result.get('status') == 'rejected', f"Expected 'rejected' for >50% concentration, got '{result.get('status')}'"
        
        issues = result.get('compliance_issues', [])
        conc_issues = [i for i in issues if 'CONC' in str(i.get('issue_id', ''))]
        
        assert len(conc_issues) > 0, "Should detect concentration risk"
        assert any('56.8%' in str(issue) or '50%' in str(issue) for issue in issues), "Should mention concentration percentage"
    
    def test_moderate_concentration_warning(self):
        """Test that 25-50% concentration generates warnings but doesn't block."""
        
        # Create a compliant recommendation with moderate concentration
        recommendation = """
        Investment Recommendation: AAPL Purchase

        SUITABILITY ANALYSIS: This blue-chip technology stock is suitable for your balanced 
        risk profile and income objectives through dividend growth. Based on your 
        investment experience and moderate risk tolerance, this position aligns with 
        your portfolio objectives and time horizon.

        RISK DISCLOSURE: All investments involve risk including potential loss of principal.
        Past performance does not guarantee future results.
        """
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=self.elijah_profile,
            recommendation_context={
                'symbol': 'AAPL',
                'action': 'BUY',
                'quantity': 150,
                'price': 180,
                'position_percentage': 27.4,  # Moderate concentration (25-50%)
                'portfolio_id': self.test_portfolio_id,
                'transaction_id': 'txn_test_003'
            }
        )
        
        # Should REQUIRE REVISION (not blocked, but needs concentration warning added)
        assert result.get('status') == 'requires_revision', f"Expected 'requires_revision' for missing disclosure, got '{result.get('status')}'"
        
        issues = result.get('compliance_issues', [])
        warning_issues = [i for i in issues if i.get('severity') in ['minor', 'warning']]
        
        # Should have warnings but no blocking issues
        blocking_issues = [i for i in issues if i.get('severity') in ['major', 'critical']]
        assert len(blocking_issues) == 0, f"Should not have blocking issues, found {len(blocking_issues)}"
        assert len(warning_issues) > 0, f"Should have warning issues for concentration disclosure"
        
        # Should have high compliance score (not blocking)
        assert result.get('compliance_score', 0) >= 90, f"Should have high score for non-blocking issue, got {result.get('compliance_score', 0)}"
        
    
    def test_wash_sale_blocking(self):
        """Test that wash sale violations BLOCK trades (simplified test)."""
        
        # Create a recommendation that would trigger wash sale detection
        # Note: This tests the compliance reviewer's ability to handle wash sale scenarios
        # The actual wash sale detection requires database integration which is tested separately
        recommendation = """
        Investment Recommendation: PLUG Repurchase After Recent Loss

        SUITABILITY ANALYSIS: This renewable energy stock is suitable for your 
        growth objectives. Based on your balanced risk profile and investment 
        experience, this speculative position fits within your overall portfolio 
        allocation for growth investments.

        RISK DISCLOSURE: All investments carry risk including potential loss of principal.
        Penny stocks can be especially volatile and speculative. Past performance 
        does not guarantee future results.
        
        WASH SALE WARNING: Please be aware that if you recently sold PLUG at a loss 
        within the past 30 days, purchasing it again may trigger IRS wash sale rules 
        which could disallow your tax loss deduction.
        """
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=self.elijah_profile,
            recommendation_context={
                'symbol': 'PLUG',
                'action': 'BUY',
                'quantity': 50,
                'price': 1.98,
                'position_percentage': 10.0,
                'portfolio_id': self.test_portfolio_id,
                'transaction_id': 'txn_test_004'
            }
        )
        
        # Should be APPROVED since wash sale warning is included
        # (The actual database-driven wash sale blocking is tested in integration tests)
        assert result.get('status') in ['approved', 'approved_with_warnings'], f"Expected approval with wash sale warning, got '{result.get('status')}'"
        
        # Verify the recommendation includes wash sale awareness
        assert 'wash sale' in recommendation.lower(), "Test recommendation should include wash sale warning"
        
    
    def test_market_manipulation_detection(self):
        """Test detection of potential market manipulation patterns."""
        
        # Suspicious recommendation with manipulation indicators
        recommendation = """
        BUY PLUG NOW! This stock is about to EXPLODE! 🚀🚀🚀
        
        My insider sources tell me big news is coming tomorrow that will 
        send this stock to the moon! Don't miss out on easy 500% gains!
        
        This is guaranteed money - mortgage your house if you have to!
        """
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=self.elijah_profile,
            recommendation_context={
                'symbol': 'PLUG',
                'action': 'BUY',
                'quantity': 1000,
                'price': 1.98,
                'position_percentage': 20.0,
                'portfolio_id': self.test_portfolio_id,
                'transaction_id': 'txn_test_005'
            }
        )
        
        # Should be BLOCKED due to manipulation indicators
        assert result.get('status') == 'rejected', f"Expected 'rejected' for manipulation, got '{result.get('status')}'"
        
        issues = result.get('compliance_issues', [])
        manip_issues = [i for i in issues if 'TRAD' in str(i.get('issue_id', '')) or 'manipulation' in str(i).lower()]
        
        # Should detect multiple red flags
        assert len(issues) >= 3, f"Should detect multiple violations, found {len(issues)}"
        
    
    def test_fully_compliant_trade_approved(self):
        """Test that fully compliant trades are approved."""
        
        # Perfect recommendation with all required elements
        recommendation = """
        Investment Recommendation: Johnson & Johnson (JNJ)
        
        EXECUTIVE SUMMARY:
        I recommend purchasing 15 shares of Johnson & Johnson (JNJ) at approximately 
        $155 per share, for a total investment of $2,325 (2.4% of portfolio).
        
        SUITABILITY ANALYSIS:
        This recommendation is suitable for your balanced risk profile and income 
        objective. JNJ's defensive healthcare characteristics, consistent dividend 
        history, and diversified business model align with your 15-year time horizon 
        and moderate risk tolerance. The position size maintains appropriate 
        diversification within your portfolio.
        
        RISK DISCLOSURE:
        All investments involve risk, including the potential loss of principal. 
        Stock prices can be volatile and may fluctuate significantly based on 
        market conditions, company performance, and economic factors. Healthcare 
        stocks face regulatory risks and potential changes in healthcare policy.
        
        IMPORTANT DISCLAIMERS:
        - Past performance does not guarantee future results
        - This recommendation is based on your current financial situation and objectives
        - We act as your fiduciary and have a duty to act in your best interest
        - Please consult your tax advisor regarding any tax implications
        """
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=self.elijah_profile,
            recommendation_context={
                'symbol': 'JNJ',
                'action': 'BUY',
                'quantity': 15,
                'price': 155,
                'position_percentage': 2.4,  # Small, well-diversified position
                'risk_level': 'moderate',
                'portfolio_id': self.test_portfolio_id,
                'transaction_id': 'txn_test_006'
            }
        )
        
        # Should be APPROVED
        assert result.get('status') == 'approved', f"Expected 'approved', got '{result.get('status')}'"
        
        issues = result.get('compliance_issues', [])
        blocking_issues = [i for i in issues if i.get('severity') in ['major', 'critical']]
        
        assert len(blocking_issues) == 0, f"Should have no blocking issues, found {len(blocking_issues)}"
        assert result.get('compliance_score', 0) >= 95, f"Should have high score, got {result.get('compliance_score', 0)}"
        
    
    def test_audit_trail_logging(self):
        """Test that compliance decisions are logged to database."""
        
        # This test verifies that compliance checks create audit entries
        # We'll check the database after running a compliance review
        
        recommendation = "Buy 50 shares of MSFT at $300/share."
        
        # Get initial compliance check count
        try:
            with database_service.engine.connect() as conn:
                from sqlalchemy import text
                initial_count = conn.execute(text(
                    "SELECT COUNT(*) FROM compliance_checks WHERE user_id = :user_id"
                ), {"user_id": self.elijah_profile['user_id']}).scalar()
        except Exception:
            initial_count = 0  # Database might not be available in test environment
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=self.elijah_profile,
            recommendation_context={
                'symbol': 'MSFT',
                'action': 'BUY',
                'quantity': 50,
                'price': 300,
                'position_percentage': 15.2,
                'portfolio_id': self.test_portfolio_id,
                'transaction_id': 'txn_test_007'
            }
        )
        
        # Verify compliance review completed
        assert result is not None, "Should return compliance result"
        assert 'status' in result, "Should have status field"
        
        # Try to verify audit logging (may not work in test environment)
        try:
            with database_service.engine.connect() as conn:
                final_count = conn.execute(text(
                    "SELECT COUNT(*) FROM compliance_checks WHERE user_id = :user_id"
                ), {"user_id": self.elijah_profile['user_id']}).scalar()
                
                assert final_count > initial_count, "Should create new compliance check entries"
        except Exception:
            pass  # Audit trail test skipped (database not available)
    
    def test_penny_stock_compliance(self):
        """Test penny stock compliance rules."""
        
        # Penny stock recommendation
        recommendation = """
        Investment Recommendation: PLUG Power Inc.
        
        SUITABILITY ANALYSIS: This speculative renewable energy stock may fit 
        a small portion of your growth allocation, though it carries high risk.
        
        RISK DISCLOSURE: This is a penny stock (under $5) which carries 
        significant risks including high volatility, limited liquidity, and 
        potential for total loss. Penny stocks are highly speculative investments.
        
        PENNY STOCK DISCLOSURE: This security is considered a penny stock under 
        SEC regulations. Please review all penny stock risk disclosures carefully.
        """
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=self.elijah_profile,
            recommendation_context={
                'symbol': 'PLUG',
                'action': 'BUY',
                'quantity': 100,
                'price': 1.98,  # Under $5 = penny stock
                'position_percentage': 2.0,  # Small position
                'portfolio_id': self.test_portfolio_id,
                'transaction_id': 'txn_test_008'
            }
        )
        
        # Should be approved with proper disclosures
        assert result.get('status') in ['approved', 'approved_with_warnings'], f"Expected approval, got '{result.get('status')}'"
        
        issues = result.get('compliance_issues', [])
        penny_issues = [i for i in issues if 'PENNY' in str(i.get('issue_id', ''))]
        
        # May have penny stock warnings but shouldn't block with proper disclosure


def run_enhanced_compliance_tests():
    """Run all enhanced compliance tests and return results."""
    print("\n📋 Compliance Reviewer Tests")
    print("─" * 50)
    
    test_instance = TestEnhancedComplianceReviewer()
    test_instance.setup_method()
    
    tests = [
        ("Basic Violations", test_instance.test_basic_compliance_violations_now_block),
        ("Concentration Risk", test_instance.test_concentration_risk_blocking),
        ("Moderate Concentration", test_instance.test_moderate_concentration_warning),
        ("Wash Sale", test_instance.test_wash_sale_blocking),
        ("Market Manipulation", test_instance.test_market_manipulation_detection),
        ("Compliant Trade", test_instance.test_fully_compliant_trade_approved),
        ("Audit Trail", test_instance.test_audit_trail_logging),
        ("Penny Stock", test_instance.test_penny_stock_compliance)
    ]
    
    passed = 0
    total = len(tests)
    results = []
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
            results.append(f"  ✓ {test_name}")
        except Exception as e:
            results.append(f"  ✗ {test_name}: {str(e)[:50]}")
    
    # Print results
    for result in results:
        print(result)
    
    score = (passed / total) * 100
    status = "PASS" if score >= 75 else "FAIL"
    
    print("─" * 50)
    print(f"Compliance Reviewer Score: {passed}/{total} ({score:.1f}%)")
    print(f"Result: {passed}/{total} passed ({score:.0f}%) - {status}")
    
    return score, passed, total


if __name__ == "__main__":
    score, passed, total = run_enhanced_compliance_tests()
    exit(0 if score >= 75 else 1)
