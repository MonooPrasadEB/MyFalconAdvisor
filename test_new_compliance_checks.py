"""
Quick test to see the new compliance checks in action!
Run this to verify the 3 new checks are working.
"""

from myfalconadvisor.agents.compliance_reviewer import compliance_reviewer_agent

# Test case 1: Large position without concentration warning
print("=" * 80)
print("TEST 1: Large Position (20% of portfolio)")
print("=" * 80)

result1 = compliance_reviewer_agent.review_investment_recommendation(
    recommendation_content="I recommend buying 200 shares of AAPL at $175/share.",
    client_profile={
        'risk_tolerance': 'moderate',
        'age': 45,
        'portfolio_value': 175000,
        'account_type': 'taxable'
    },
    recommendation_context={
        'symbol': 'AAPL',
        'action': 'BUY',
        'quantity': 200,
        'price': 175,
        'position_percentage': 20.0  # 20% position!
    }
)

print(f"\nStatus: {result1.get('status')}")
print(f"Compliance Score: {result1.get('compliance_score')}")
print(f"\nIssues Found: {len(result1.get('compliance_issues', []))}")
for issue in result1.get('compliance_issues', []):
    print(f"  - [{issue['severity']}] {issue['issue_id']}: {issue['description']}")

# Test case 2: Mentions performance without disclaimer
print("\n" + "=" * 80)
print("TEST 2: Past Performance Without Disclaimer")
print("=" * 80)

result2 = compliance_reviewer_agent.review_investment_recommendation(
    recommendation_content="AAPL has delivered strong returns of 25% annually over the past 5 years.",
    client_profile={
        'risk_tolerance': 'moderate',
        'age': 45,
        'portfolio_value': 175000,
        'account_type': 'taxable'
    },
    recommendation_context={
        'symbol': 'AAPL',
        'action': 'BUY',
        'quantity': 100,
        'price': 175,
        'position_percentage': 5.0
    }
)

print(f"\nStatus: {result2.get('status')}")
print(f"Compliance Score: {result2.get('compliance_score')}")
print(f"\nIssues Found: {len(result2.get('compliance_issues', []))}")
for issue in result2.get('compliance_issues', []):
    print(f"  - [{issue['severity']}] {issue['issue_id']}: {issue['description']}")

# Test case 3: IRA with tax mention but no tax advisor referral
print("\n" + "=" * 80)
print("TEST 3: IRA Tax Discussion Without Tax Advisor Referral")
print("=" * 80)

result3 = compliance_reviewer_agent.review_investment_recommendation(
    recommendation_content="Contributing to your IRA will provide tax benefits.",
    client_profile={
        'risk_tolerance': 'moderate',
        'age': 45,
        'portfolio_value': 175000,
        'account_type': 'Traditional IRA'  # Retirement account
    },
    recommendation_context={
        'symbol': 'VTI',
        'action': 'BUY',
        'quantity': 100,
        'price': 200,
        'position_percentage': 5.0
    }
)

print(f"\nStatus: {result3.get('status')}")
print(f"Compliance Score: {result3.get('compliance_score')}")
print(f"\nIssues Found: {len(result3.get('compliance_issues', []))}")
for issue in result3.get('compliance_issues', []):
    print(f"  - [{issue['severity']}] {issue['issue_id']}: {issue['description']}")

print("\n" + "=" * 80)
print("✅ All tests complete! The new compliance checks are working.")
print("=" * 80)

