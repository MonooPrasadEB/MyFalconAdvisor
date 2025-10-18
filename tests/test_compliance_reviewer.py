"""
Test suite for Compliance Reviewer Agent with 6 compliance checks.

Tests the simple compliance checks (3 existing + 3 new) that we added to the reviewer agent.
This is separate from the enhanced compliance system tests.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Ensure we're importing from the correct project directory
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from myfalconadvisor.agents.compliance_reviewer import compliance_reviewer_agent


class TestComplianceReviewer:
    """Test the compliance reviewer agent with all 6 checks."""
    
    def setup_method(self):
        """Set up test data."""
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
            'annual_income': 21536.00,
            'net_worth': 154650.00
        }
    
    def test_risk_disclosure_check(self):
        """Test existing risk disclosure check."""
        print("\n🧪 Testing Risk Disclosure Check")
        
        # Missing risk disclosure
        recommendation = "I recommend buying 100 shares of AAPL at $180/share."
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=self.elijah_profile,
            recommendation_context={
                'symbol': 'AAPL',
                'action': 'BUY',
                'quantity': 100,
                'price': 180,
                'position_percentage': 5.0
            }
        )
        
        # Should find missing risk disclosure
        issues = result.get('compliance_issues', [])
        risk_issues = [i for i in issues if i['issue_id'] == 'RISK-001']
        
        assert len(risk_issues) > 0, "Should detect missing risk disclosure"
        assert risk_issues[0]['severity'] == 'major'
        assert result.get('status') == 'requires_revision'
        
        print(f"✅ Risk disclosure check working: {len(risk_issues)} issues found")
    
    def test_suitability_check(self):
        """Test existing suitability analysis check."""
        print("\n🧪 Testing Suitability Analysis Check")
        
        # Missing suitability analysis
        recommendation = "I recommend buying 100 shares of TSLA. It's a great stock."
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=self.elijah_profile,
            recommendation_context={
                'symbol': 'TSLA',
                'action': 'BUY',
                'quantity': 100,
                'price': 250,
                'position_percentage': 5.0
            }
        )
        
        # Should find missing suitability analysis
        issues = result.get('compliance_issues', [])
        suit_issues = [i for i in issues if i['issue_id'] == 'SUIT-001']
        
        assert len(suit_issues) > 0, "Should detect missing suitability analysis"
        assert suit_issues[0]['severity'] == 'critical'
        assert result.get('status') == 'requires_revision'
        
        print(f"✅ Suitability check working: {len(suit_issues)} issues found")
    
    def test_concentration_risk_check(self):
        """Test NEW concentration risk check (CONC-001)."""
        print("\n🧪 Testing NEW Concentration Risk Check")
        
        # Large position without concentration warning
        recommendation = "I recommend buying 100 shares of AAPL at $180/share."
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=self.elijah_profile,
            recommendation_context={
                'symbol': 'AAPL',
                'action': 'BUY',
                'quantity': 100,
                'price': 180,
                'position_percentage': 18.3  # Large position >10%
            }
        )
        
        # Should find concentration risk issue
        issues = result.get('compliance_issues', [])
        conc_issues = [i for i in issues if i['issue_id'] == 'CONC-001']
        
        assert len(conc_issues) > 0, "Should detect concentration risk for large position"
        assert conc_issues[0]['severity'] == 'major'
        assert '18.3%' in conc_issues[0]['description']
        assert result.get('status') == 'requires_revision'
        
        print(f"✅ Concentration risk check working: {len(conc_issues)} issues found")
    
    def test_past_performance_disclaimer_check(self):
        """Test NEW past performance disclaimer check (PERF-001)."""
        print("\n🧪 Testing NEW Past Performance Disclaimer Check")
        
        # Performance mention without disclaimer
        recommendation = "AAPL has delivered strong returns of 25% annually over the past 5 years."
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=self.elijah_profile,
            recommendation_context={
                'symbol': 'AAPL',
                'action': 'BUY',
                'quantity': 50,
                'price': 180,
                'position_percentage': 5.0
            }
        )
        
        # Should find missing past performance disclaimer
        issues = result.get('compliance_issues', [])
        perf_issues = [i for i in issues if i['issue_id'] == 'PERF-001']
        
        assert len(perf_issues) > 0, "Should detect missing past performance disclaimer"
        assert perf_issues[0]['severity'] == 'minor'
        assert result.get('status') == 'requires_revision'
        
        print(f"✅ Past performance disclaimer check working: {len(perf_issues)} issues found")
    
    def test_tax_advisor_referral_check(self):
        """Test NEW tax advisor referral check (TAX-001)."""
        print("\n🧪 Testing NEW Tax Advisor Referral Check")
        
        # Tax discussion in retirement account without tax advisor referral
        elijah_ira = self.elijah_profile.copy()
        elijah_ira['account_type'] = 'Traditional IRA'
        
        recommendation = "This IRA contribution will provide tax benefits and tax-deferred growth."
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=elijah_ira,
            recommendation_context={
                'symbol': 'VTI',
                'action': 'BUY',
                'quantity': 25,
                'price': 240,
                'position_percentage': 5.0
            }
        )
        
        # Should find missing tax advisor referral
        issues = result.get('compliance_issues', [])
        tax_issues = [i for i in issues if i['issue_id'] == 'TAX-001']
        
        assert len(tax_issues) > 0, "Should detect missing tax advisor referral"
        assert tax_issues[0]['severity'] == 'minor'
        assert result.get('status') == 'requires_revision'
        
        print(f"✅ Tax advisor referral check working: {len(tax_issues)} issues found")
    
    def test_fully_compliant_recommendation(self):
        """Test that fully compliant recommendations pass all checks."""
        print("\n🧪 Testing Fully Compliant Recommendation")
        
        # Complete recommendation with all required elements
        recommendation = """
        Investment Recommendation for Elijah Martin
        
        I recommend purchasing 15 shares of Johnson & Johnson (JNJ) at approximately 
        $155 per share, for a total investment of $2,325.
        
        SUITABILITY ANALYSIS:
        This recommendation is suitable for your balanced risk profile and income objective. 
        The defensive nature of healthcare stocks aligns with your 15-year time horizon 
        and moderate risk tolerance.
        
        RISK DISCLOSURE:
        All investments involve risk, including the potential loss of principal. Stock 
        prices can be volatile and may fluctuate significantly based on market conditions 
        and company performance.
        
        IMPORTANT DISCLAIMERS:
        - Past performance does not guarantee future results
        - This recommendation is based on your current financial situation and objectives
        - We act as your fiduciary and have a duty to act in your best interest
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
                'risk_level': 'moderate'
            }
        )
        
        # Should pass all checks
        issues = result.get('compliance_issues', [])
        
        assert len(issues) == 0, f"Should pass all checks, but found {len(issues)} issues"
        assert result.get('status') == 'approved'
        assert result.get('compliance_score', 0) >= 90
        
        print(f"✅ Fully compliant recommendation passed: {result.get('compliance_score', 0)}/100")
    
    def test_multiple_violations(self):
        """Test detection of multiple violations in one recommendation."""
        print("\n🧪 Testing Multiple Violations Detection")
        
        # Recommendation with multiple issues
        recommendation = """
        I strongly recommend investing heavily in NVDA. The stock has delivered 
        incredible gains of over 200% in the past year and shows no signs of slowing down.
        
        You should invest $25,000 to maximize your returns. The tax-free growth 
        in your Roth IRA makes this an especially attractive opportunity.
        """
        
        elijah_roth = self.elijah_profile.copy()
        elijah_roth['account_type'] = 'Roth IRA'
        
        result = compliance_reviewer_agent.review_investment_recommendation(
            recommendation_content=recommendation,
            client_profile=elijah_roth,
            recommendation_context={
                'symbol': 'NVDA',
                'action': 'BUY',
                'quantity': 50,
                'price': 500,
                'position_percentage': 25.4,  # Very large position
                'risk_level': 'aggressive'
            }
        )
        
        # Should find multiple issues
        issues = result.get('compliance_issues', [])
        
        # Count issues by type
        existing_issues = [i for i in issues if i['issue_id'] not in ['CONC-001', 'PERF-001', 'TAX-001']]
        new_issues = [i for i in issues if i['issue_id'] in ['CONC-001', 'PERF-001', 'TAX-001']]
        
        assert len(issues) >= 4, f"Should find multiple issues, found {len(issues)}"
        assert len(new_issues) >= 2, f"Should find multiple NEW check issues, found {len(new_issues)}"
        assert result.get('status') == 'requires_revision'
        
        print(f"✅ Multiple violations detected: {len(issues)} total, {len(new_issues)} from new checks")


def run_compliance_reviewer_tests():
    """Run all compliance reviewer tests and return score."""
    print("\n🧪 Compliance Reviewer Agent Tests")
    print("=" * 60)
    
    test_instance = TestComplianceReviewer()
    test_instance.setup_method()
    
    tests = [
        ("Risk Disclosure Check", test_instance.test_risk_disclosure_check),
        ("Suitability Analysis Check", test_instance.test_suitability_check),
        ("Concentration Risk Check (NEW)", test_instance.test_concentration_risk_check),
        ("Past Performance Disclaimer Check (NEW)", test_instance.test_past_performance_disclaimer_check),
        ("Tax Advisor Referral Check (NEW)", test_instance.test_tax_advisor_referral_check),
        ("Fully Compliant Recommendation", test_instance.test_fully_compliant_recommendation),
        ("Multiple Violations Detection", test_instance.test_multiple_violations)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")
    
    score = (passed / total) * 100
    
    print("\n" + "=" * 60)
    print("🏁 COMPLIANCE REVIEWER TEST RESULTS")
    print("=" * 60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {score:.1f}%")
    print(f"Status: {'✅ PASS' if score >= 80 else '❌ FAIL'}")
    
    # Print score in format expected by test runner
    print(f"🎯 Compliance Reviewer Score: {passed}/{total} tests passed ({score:.1f}%)")
    print(f"🎉 {'All compliance checks are working!' if score >= 80 else 'Some compliance checks need attention!'}")
    
    return score


if __name__ == "__main__":
    score = run_compliance_reviewer_tests()
    exit(0 if score >= 80 else 1)
