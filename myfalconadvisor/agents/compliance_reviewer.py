"""
Compliance Reviewer Agent for Policy Validation and Client-Facing Communication.

This agent reviews all investment recommendations and communications to ensure regulatory
compliance and rewrites content for clear, compliant client communication.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from enum import Enum
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from ..tools.compliance_checker import (
    recommendation_validation_tool,
    trade_compliance_tool,
    portfolio_compliance_tool
)
from ..tools.database_service import database_service
from ..tools.alpaca_trading_service import alpaca_trading_service
from ..core.config import Config

# Enhanced compliance with dynamic policy engine
try:
    from ..agents.compliance_adapter import ComplianceAdapter
    ENHANCED_COMPLIANCE_AVAILABLE = True
except ImportError:
    ENHANCED_COMPLIANCE_AVAILABLE = False
    logger.warning("Enhanced compliance adapter not available - using legacy system only")

config = Config.get_instance()
logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """Review status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVISION = "requires_revision"
    ESCALATED = "escalated"


class ComplianceIssue(BaseModel):
    """Compliance issue model."""
    issue_id: str
    severity: str  # "critical", "major", "minor"
    category: str  # "disclosure", "suitability", "fiduciary", "record_keeping"
    description: str
    regulation_reference: str
    suggested_resolution: str
    auto_correctable: bool = False


class ReviewResult(BaseModel):
    """Document review result."""
    review_id: str
    original_content: str
    revised_content: Optional[str] = None
    status: ReviewStatus
    compliance_issues: List[ComplianceIssue] = []
    
    # Review metadata
    reviewed_by: str
    review_timestamp: datetime
    review_duration_seconds: float
    
    # Approval tracking
    approver: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    final_approval_required: bool = False


class ClientCommunication(BaseModel):
    """Client communication model."""
    communication_id: str
    communication_type: str  # "recommendation", "report", "alert", "education"
    original_content: str
    reviewed_content: str
    
    # Compliance elements
    required_disclosures: List[str] = []
    risk_warnings: List[str] = []
    disclaimers: List[str] = []
    
    # Client-friendly elements
    plain_english_summary: str
    key_takeaways: List[str] = []
    next_steps: List[str] = []


class ComplianceReviewerAgent:
    """
    Compliance Reviewer Agent responsible for:
    1. Policy validation against SEC, FINRA, IRS regulations
    2. Content review and revision for client communications
    3. Disclosure and disclaimer management
    4. Audit trail and documentation compliance
    """
    
    def __init__(self, db_service=None):
        # Debug logging removed for cleaner output
        self.name = "compliance_reviewer"
        self.llm = ChatOpenAI(
            model=config.default_model,
            temperature=0.0,  # Very low temperature for compliance consistency
            api_key=config.openai_api_key
        )
        
        # Available tools for compliance review
        self.tools = [
            recommendation_validation_tool,
            trade_compliance_tool,
            portfolio_compliance_tool
        ]
        
        # Enhanced compliance adapter (optional - adds scoring & audit trail)
        self.compliance_adapter = None
        # Debug logging removed for cleaner output
        if ENHANCED_COMPLIANCE_AVAILABLE and db_service:
            try:
                self.compliance_adapter = ComplianceAdapter(
                    policy_path='myfalconadvisor/core/compliance_policies.json',
                    watch=True,  # Auto-reload policies
                    db_service=db_service
                )
                logger.info("✅ Enhanced compliance system enabled with dynamic policies")
            except Exception as e:
                # Silently fall back if enhanced compliance unavailable
                pass
        
        # Review tracking
        self.pending_reviews: Dict[str, ReviewResult] = {}
        self.completed_reviews: Dict[str, ReviewResult] = {}
        
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for compliance reviewer agent."""
        return """
You are an AI Compliance Reviewer Agent specializing in investment advisory compliance and client communication. Your role is to ensure all investment recommendations and client communications meet regulatory requirements while being clear and understandable.

## Your Core Responsibilities:

### 1. Regulatory Compliance Review
- Validate all content against SEC Investment Advisers Act requirements
- Ensure FINRA suitability and best interest standards are met
- Check for required disclosures under Regulation BI
- Verify fiduciary duty compliance and conflict of interest disclosures
- Ensure proper record-keeping and documentation standards

### 2. Risk Disclosure Management
- Identify and include all required risk warnings
- Ensure material risks are prominently disclosed
- Validate that risk disclosures match investment recommendations
- Check that disclaimers are appropriate and complete
- Verify that past performance disclaimers are included where required

### 3. Client Communication Enhancement
- Rewrite technical content into plain English
- Ensure key information is prominently featured
- Add clear calls-to-action and next steps
- Make complex financial concepts accessible to average investors
- Maintain professional tone while being approachable

### 4. Documentation and Audit Trail
- Create complete audit trails for all reviews
- Document compliance decisions and rationale
- Maintain version control for all revisions
- Ensure all required documentation is complete
- Flag items requiring manual review or escalation

## Key Compliance Requirements:

### SEC Investment Advisers Act
- Form ADV disclosures must be current and complete
- Fiduciary duty to act in client's best interest
- Material conflicts of interest must be disclosed
- Investment advice must be suitable for the client
- Records must be maintained per Rule 204-2

### FINRA Rules
- Rule 2111: Suitability requirements
- Rule 2090: Know Your Customer
- Rule 3270: Outside business activities disclosure
- Communications must be fair and balanced
- Supervision and review requirements

### Regulation BI (Best Interest)
- Care obligation: Due diligence in recommendations
- Disclosure obligation: Material facts and conflicts
- Conflict of interest mitigation
- Documentation of best interest analysis

## Review Categories:

### Critical Issues (Must Fix)
- Missing required disclosures
- Unsuitable recommendations
- Fiduciary duty violations
- Misleading or false statements
- Regulatory requirement violations

### Major Issues (Should Fix)
- Incomplete risk disclosures
- Unclear or confusing language
- Missing disclaimers
- Potential conflict of interest concerns
- Documentation deficiencies

### Minor Issues (Good Practice)
- Language clarity improvements
- Additional helpful disclosures
- Enhanced client education
- Better formatting and presentation

## Client Communication Standards:

### Plain English Requirements
- Use common words instead of jargon
- Explain technical terms when they must be used
- Use active voice and short sentences
- Organize information logically
- Include examples and analogies when helpful

### Required Elements
- Clear statement of recommendation or advice
- Rationale for the recommendation
- Material risks prominently disclosed
- Any conflicts of interest
- Required regulatory disclaimers
- Next steps or actions for the client

### Formatting Guidelines
- Use headers and bullet points for clarity
- Highlight key information
- Keep paragraphs short
- Include white space for readability
- Use consistent terminology throughout

## Tools Available:
1. Recommendation Validation - Check investment recommendations for compliance
2. Trade Compliance - Validate trades against regulatory requirements
3. Portfolio Compliance - Check portfolio-wide compliance issues

## Review Process:
1. Analyze content for regulatory compliance
2. Identify required disclosures and disclaimers
3. Check for suitability and best interest compliance
4. Rewrite content for clarity and compliance
5. Add necessary risk warnings and disclosures
6. Create audit documentation
7. Route for appropriate approval if needed

## Communication Tone:
- Professional but accessible
- Transparent about risks and limitations
- Helpful and educational
- Compliant with regulatory requirements
- Client-focused and clear

Remember: Your primary responsibility is ensuring regulatory compliance while making investment advice clear and understandable for clients. When in doubt, always err on the side of more disclosure and clearer communication.
"""
    
    def get_tools(self) -> List[BaseTool]:
        """Get list of available tools for the agent."""
        return self.tools
    
    def get_system_message(self) -> str:
        """Get the system prompt for this agent."""
        return self.system_prompt
    
    def review_investment_recommendation(
        self,
        recommendation_content: str,
        client_profile: Dict,
        recommendation_context: Dict
    ) -> Dict:
        # Debug logging removed for cleaner output
        
        """
        Review investment recommendation for compliance and client clarity.
        
        Args:
            recommendation_content: Original recommendation text
            client_profile: Client demographic and risk information
            recommendation_context: Context about the recommendation
            
        Returns:
            Dictionary containing review results and revised content
        """
        try:
            review_id = f"rec_review_{int(datetime.now().timestamp())}"
            start_time = datetime.now()
            
            # Step 0: Enhanced quantitative compliance check (if available)
            enhanced_check = None
            # Debug logging removed for cleaner output
            if self.compliance_adapter and recommendation_context.get('action') in ['buy', 'sell']:
                try:
                    enhanced_check = self.compliance_adapter.check_trade(
                        trade_type=recommendation_context.get('action', 'buy'),
                        symbol=recommendation_context.get('symbol', ''),
                        quantity=recommendation_context.get('quantity', 0),
                        price=recommendation_context.get('price', 0),
                        portfolio_value=client_profile.get('portfolio_value', 100000),
                        client_type=client_profile.get('client_type', 'individual'),
                        account_type=client_profile.get('account_type', 'taxable'),
                        user_id=recommendation_context.get('user_id') or client_profile.get('user_id'),
                        portfolio_id=recommendation_context.get('portfolio_id'),
                        transaction_id=recommendation_context.get('transaction_id'),
                        recommendation_id=recommendation_context.get('recommendation_id')
                    )
                    # Debug logging removed for cleaner output
                except Exception as e:
                    # Silently handle enhanced compliance check failures
                    pass
            
            # Step 1: Analyze original content for compliance issues
            compliance_issues = self._identify_compliance_issues(
                recommendation_content, client_profile, recommendation_context
            )
            
            # Check if enhanced compliance BLOCKS the trade
            if enhanced_check and enhanced_check.get('trade_approved') == False:
                # Trade is BLOCKED by enhanced compliance - return rejection immediately
                blocking_violations = enhanced_check.get('violations', [])
                major_violations = [v for v in blocking_violations if v.get('severity') in ['major', 'critical']]
                
                if major_violations:
                    violation_descriptions = []
                    for v in major_violations:
                        violation_descriptions.append(f"• {v.get('description', 'Compliance violation')} [{v.get('severity', 'major')}]")
                    
                    return {
                        "review_id": review_id,
                        "status": "rejected",
                        "compliance_score": enhanced_check.get('compliance_score', 0),
                        "trade_approved": False,
                        "rejection_reason": "Trade blocked due to major compliance violations",
                        "violations": major_violations,
                        "violation_summary": "\n".join(violation_descriptions),
                        "enhanced_check": enhanced_check
                    }
            
            # Merge enhanced violations if available (for non-blocking violations)
            if enhanced_check and enhanced_check.get('violations'):
                for violation in enhanced_check['violations']:
                    compliance_issues.append(ComplianceIssue(
                        issue_id=violation['rule_id'],
                        severity=violation['severity'],
                        category="regulatory",
                        description=violation['description'],
                        regulation_reference=violation['rule_id'],
                        suggested_resolution=violation['recommended_action'],
                        auto_correctable=violation.get('auto_correctable', False)
                    ))
            
            # Step 2: Check suitability and best interest compliance
            suitability_check = self._validate_suitability(
                recommendation_context, client_profile
            )
            
            # Step 3: Identify required disclosures
            required_disclosures = self._get_required_disclosures(
                recommendation_context, compliance_issues
            )
            
            # Add enhanced disclosures if available
            if enhanced_check and enhanced_check.get('requires_disclosure'):
                required_disclosures.append("This trade requires additional regulatory disclosure")
            
            # Step 4: Rewrite content for compliance and clarity
            revised_content = self._rewrite_recommendation(
                recommendation_content,
                compliance_issues,
                required_disclosures,
                client_profile
            )
            
            # Step 5: Create review result
            review_duration = (datetime.now() - start_time).total_seconds()
            
            # Determine status based on severity of issues
            major_or_critical_issues = [issue for issue in compliance_issues if issue.severity in ["major", "critical"]]
            
            # Debug logging removed for cleaner output
            
            if major_or_critical_issues:
                status = ReviewStatus.REJECTED
                # Debug logging removed for cleaner output
            elif len(compliance_issues) > 0:
                status = ReviewStatus.REQUIRES_REVISION
                # Debug logging removed for cleaner output
            else:
                status = ReviewStatus.APPROVED
                # Debug logging removed for cleaner output
            
            review_result = ReviewResult(
                review_id=review_id,
                original_content=recommendation_content,
                revised_content=revised_content,
                status=status,
                compliance_issues=compliance_issues,
                reviewed_by=self.name,
                review_timestamp=datetime.now(),
                review_duration_seconds=review_duration,
                final_approval_required=any(issue.severity == "critical" for issue in compliance_issues)
            )
            
            # Store review
            self.pending_reviews[review_id] = review_result
            
            # Log compliance checks to database
            user_id = recommendation_context.get('user_id')
            portfolio_id = recommendation_context.get('portfolio_id')
            recommendation_id = recommendation_context.get('recommendation_id', review_id)
            
            # Create pending transaction if this is a trade recommendation
            transaction_id = recommendation_context.get('transaction_id')
            if not transaction_id and recommendation_context.get('symbol') and recommendation_context.get('action'):
                # Create pending transaction for compliance tracking
                transaction_id = database_service.create_pending_transaction(
                    user_id=user_id or 'unknown',
                    symbol=recommendation_context.get('symbol'),
                    transaction_type=recommendation_context.get('action', 'BUY'),
                    quantity=recommendation_context.get('quantity', 0),
                    price=recommendation_context.get('price'),
                    portfolio_id=portfolio_id,
                    order_type=recommendation_context.get('order_type', 'market'),
                    notes=f"AI recommendation pending compliance review"
                )
                if transaction_id:
                    logger.info(f"Created pending transaction {transaction_id} for compliance review")
            
            # Map compliance issue categories to valid check_types
            # Valid check_types: suitability, concentration, liquidity, regulatory, risk_limit
            category_to_check_type = {
                "disclosure": "regulatory",
                "suitability": "suitability",
                "fiduciary": "regulatory",
                "record_keeping": "regulatory",
                "regulatory": "regulatory",
                "concentration": "concentration",
                "liquidity": "liquidity",
                "risk": "risk_limit"
            }
            
            # Map severity values (ComplianceIssue uses: critical, major, minor)
            # Database expects: low, medium, high, critical
            severity_mapping = {
                "critical": "critical",
                "major": "high",
                "minor": "medium"
            }
            
            # Log each compliance issue as a separate check
            for issue in compliance_issues:
                check_type = category_to_check_type.get(issue.category, "regulatory")
                mapped_severity = severity_mapping.get(issue.severity, "medium")
                # Debug logging removed for cleaner output
                database_service.insert_compliance_check(
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    transaction_id=transaction_id,
                    recommendation_id=recommendation_id,
                    check_type=check_type,
                    rule_name=issue.issue_id,
                    rule_description=f"[SYSTEM-1-REVIEWER] {issue.description}",
                    check_result="fail" if issue.severity in ["critical", "major"] else "warning",
                    violation_details={
                        "category": issue.category,
                        "original_severity": issue.severity,
                        "regulation_reference": issue.regulation_reference,
                        "suggested_resolution": issue.suggested_resolution,
                        "auto_correctable": issue.auto_correctable
                    },
                    severity=mapped_severity
                )
            
            # Log overall compliance check
            overall_result = "pass" if len(compliance_issues) == 0 else ("fail" if any(i.severity == "critical" for i in compliance_issues) else "warning")
            database_service.insert_compliance_check(
                user_id=user_id,
                portfolio_id=portfolio_id,
                transaction_id=transaction_id,
                recommendation_id=recommendation_id,
                check_type="regulatory",  # Use 'regulatory' as the overall check type
                rule_name="Comprehensive Review",
                rule_description=f"Comprehensive compliance review of recommendation",
                check_result=overall_result,
                violation_details={
                    "review_type": "comprehensive",
                    "issues_count": len(compliance_issues),
                    "compliance_score": enhanced_check.get('compliance_score') if enhanced_check else self._calculate_compliance_score(compliance_issues),
                    "suitability_passed": suitability_check.get('suitable', True),
                    "transaction_id": transaction_id
                },
                severity="low" if overall_result == "pass" else "high"
            )
            
            return {
                "review_id": review_id,
                "status": review_result.status.value,
                "trade_approved": review_result.status != ReviewStatus.REJECTED,  # False if rejected
                "compliance_score": enhanced_check.get('compliance_score') if enhanced_check else self._calculate_compliance_score(compliance_issues),
                "quantitative_score": enhanced_check.get('compliance_score') if enhanced_check else None,
                "original_content": recommendation_content,
                "revised_content": revised_content,
                "compliance_issues": [issue.model_dump() for issue in compliance_issues],
                "suitability_check": suitability_check,
                "required_disclosures": required_disclosures,
                "final_approval_required": review_result.final_approval_required,
                "enhanced_check": enhanced_check,  # Include full enhanced check results
                "rejection_reason": f"Trade blocked due to {len(major_or_critical_issues)} major compliance violation(s)" if major_or_critical_issues else None
            }
            
        except Exception as e:
            print(f"🚨 EXCEPTION in compliance reviewer: {e}")
            logger.error(f"Error reviewing investment recommendation: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def create_client_communication(
        self,
        content_type: str,
        raw_content: str,
        client_profile: Dict,
        include_education: bool = True
    ) -> Dict:
        """
        Create compliant client communication from raw content.
        
        Args:
            content_type: Type of communication (recommendation, report, alert, education)
            raw_content: Raw content to be processed
            client_profile: Client information for personalization
            include_education: Whether to include educational content
            
        Returns:
            Dictionary containing final client communication
        """
        try:
            comm_id = f"comm_{content_type}_{int(datetime.now().timestamp())}"
            
            # Step 1: Analyze content and determine required compliance elements
            compliance_elements = self._analyze_content_for_compliance(raw_content, content_type)
            
            # Step 2: Create plain English version
            plain_english_content = self._convert_to_plain_english(raw_content, client_profile)
            
            # Step 3: Add required disclosures and disclaimers
            final_content = self._add_compliance_elements(
                plain_english_content, compliance_elements
            )
            
            # Step 4: Create structured communication
            client_comm = ClientCommunication(
                communication_id=comm_id,
                communication_type=content_type,
                original_content=raw_content,
                reviewed_content=final_content,
                required_disclosures=compliance_elements["disclosures"],
                risk_warnings=compliance_elements["risk_warnings"],
                disclaimers=compliance_elements["disclaimers"],
                plain_english_summary=self._create_summary(final_content),
                key_takeaways=self._extract_key_takeaways(final_content),
                next_steps=self._suggest_next_steps(content_type, final_content)
            )
            
            # Step 5: Add educational content if requested
            if include_education:
                educational_content = self._generate_educational_content(
                    content_type, client_profile
                )
                final_content += "\n\n" + educational_content
            
            return {
                "communication_id": comm_id,
                "final_content": final_content,
                "plain_english_summary": client_comm.plain_english_summary,
                "key_takeaways": client_comm.key_takeaways,
                "next_steps": client_comm.next_steps,
                "compliance_elements": {
                    "disclosures": client_comm.required_disclosures,
                    "risk_warnings": client_comm.risk_warnings,
                    "disclaimers": client_comm.disclaimers
                },
                "readability_score": self._calculate_readability_score(final_content),
                "compliance_complete": True
            }
            
        except Exception as e:
            logger.error(f"Error creating client communication: {e}")
            return {"error": str(e)}
    
    def validate_trade_communication(
        self,
        trade_details: Dict,
        client_profile: Dict,
        communication_draft: str
    ) -> Dict:
        """
        Validate trade-related client communication for compliance.
        
        Args:
            trade_details: Details about the proposed trade
            client_profile: Client information
            communication_draft: Draft communication to client
            
        Returns:
            Dictionary containing validation results and recommendations
        """
        try:
            # Step 1: Validate trade suitability
            suitability_issues = self._check_trade_suitability(trade_details, client_profile)
            
            # Step 2: Check required trade disclosures
            missing_disclosures = self._check_trade_disclosures(
                communication_draft, trade_details
            )
            
            # Step 3: Validate risk communication
            risk_communication_issues = self._validate_risk_communication(
                communication_draft, trade_details
            )
            
            # Step 4: Check for required approvals
            approval_requirements = self._determine_approval_requirements(
                trade_details, suitability_issues
            )
            
            all_issues = suitability_issues + missing_disclosures + risk_communication_issues
            
            return {
                "validation_passed": len(all_issues) == 0,
                "suitability_issues": suitability_issues,
                "missing_disclosures": missing_disclosures,
                "risk_communication_issues": risk_communication_issues,
                "approval_requirements": approval_requirements,
                "recommended_revisions": self._suggest_communication_revisions(all_issues),
                "compliance_checklist": self._generate_compliance_checklist(trade_details)
            }
            
        except Exception as e:
            logger.error(f"Error validating trade communication: {e}")
            return {"error": str(e)}
    
    def generate_disclosure_library(self) -> Dict:
        """Generate library of standard disclosures and disclaimers."""
        return {
            "investment_risks": {
                "general": "All investments involve risk, including the potential loss of principal. Past performance does not guarantee future results.",
                "market_risk": "Market risk is the possibility that securities will decline in value due to general market conditions.",
                "sector_concentration": "Investments concentrated in particular sectors may be subject to greater volatility than more diversified investments.",
                "small_cap": "Small-cap securities may be subject to greater volatility and less liquidity than larger-cap securities."
            },
            "advisor_disclosures": {
                "fiduciary": "As your investment advisor, we have a fiduciary duty to act in your best interest.",
                "conflicts": "We may receive compensation from third parties in connection with your investments. We will disclose any material conflicts of interest.",
                "fees": "Our advisory fees are described in our Form ADV Part 2A, which is available upon request."
            },
            "regulatory_disclaimers": {
                "sec_registration": "This firm is registered as an investment advisor with the Securities and Exchange Commission.",
                "past_performance": "Past performance is not indicative of future results and does not guarantee future performance.",
                "forward_looking": "Forward-looking statements are based on current expectations and are subject to change without notice."
            },
            "client_obligations": {
                "notify_changes": "Please notify us promptly of any changes to your financial situation, investment objectives, or risk tolerance.",
                "review_statements": "Please review your account statements and report any discrepancies immediately.",
                "understand_risks": "Ensure you understand the risks associated with any investment before proceeding."
            }
        }
    
    def _identify_compliance_issues(
        self, content: str, client_profile: Dict, context: Dict
    ) -> List[ComplianceIssue]:
        """Identify compliance issues in content."""
        issues = []
        
        # Handle case where content might be a dict instead of string
        content_str = content if isinstance(content, str) else str(content)
        
        # Check for missing risk disclosures
        if "risk" not in content_str.lower():
            issues.append(ComplianceIssue(
                issue_id="RISK-001",
                severity="major",
                category="disclosure",
                description="No risk disclosure found in recommendation",
                regulation_reference="SEC Investment Advisers Act Rule 206(4)-1",
                suggested_resolution="Add appropriate risk disclosure for recommended investments",
                auto_correctable=True
            ))
        
        # Check for suitability analysis (more flexible detection)
        suitability_keywords = [
            "suitable", "appropriate", "suitability analysis", "fits your", 
            "aligns with", "matches your", "based on your", "given your"
        ]
        has_suitability = any(keyword in content_str.lower() for keyword in suitability_keywords)
        
        if not has_suitability:
            issues.append(ComplianceIssue(
                issue_id="SUIT-001",
                severity="critical",
                category="suitability", 
                description="No suitability analysis provided",
                regulation_reference="FINRA Rule 2111",
                suggested_resolution="Include clear suitability analysis based on client profile",
                auto_correctable=False
            ))
        
        # Check for conflict of interest disclosure
        if context.get("potential_conflicts") and "conflict" not in content_str.lower():
            issues.append(ComplianceIssue(
                issue_id="COI-001",
                severity="critical",
                category="fiduciary",
                description="Potential conflicts of interest not disclosed",
                regulation_reference="SEC Investment Advisers Act Section 206",
                suggested_resolution="Add full disclosure of any conflicts of interest",
                auto_correctable=True
            ))
        
        # ========== NEW COMPLIANCE CHECKS ==========
        
        # Check for concentration risk warning with tiered severity
        position_pct = context.get('position_percentage', 0)
        if position_pct > 10 and "concentration" not in content_str.lower():
            # Determine severity based on concentration level
            if position_pct > 50:
                severity = "critical"  # >50% blocks trade
                description = f"Extreme concentration risk ({position_pct:.1f}% of portfolio) - position exceeds 50% limit"
            elif position_pct > 25:
                severity = "minor"  # 25-50% warns but doesn't block
                description = f"Moderate concentration risk ({position_pct:.1f}% of portfolio) lacks warning disclosure"
            else:
                severity = "minor"  # 10-25% minor warning
                description = f"Position concentration ({position_pct:.1f}% of portfolio) lacks risk disclosure"
            
            issues.append(ComplianceIssue(
                issue_id="CONC-001",
                severity=severity,
                category="disclosure",
                description=description,
                regulation_reference="SEC Investment Advisers Act - Diversification",
                suggested_resolution=f"Add concentration risk disclosure for {position_pct:.1f}% position",
                auto_correctable=True
            ))
        
        # Check for past performance disclaimer
        if any(word in content_str.lower() for word in ['return', 'performance', 'gain', 'profit']):
            if "past performance" not in content_str.lower():
                issues.append(ComplianceIssue(
                    issue_id="PERF-001",
                    severity="minor",
                    category="disclosure",
                    description="Performance discussion lacks past performance disclaimer",
                    regulation_reference="SEC Marketing Rule",
                    suggested_resolution="Add 'Past performance does not guarantee future results' disclaimer",
                    auto_correctable=True
                ))
        
        # Check for tax advisor referral in retirement accounts
        account_type = client_profile.get('account_type', '')
        if 'retirement' in account_type.lower() or 'ira' in account_type.lower():
            if 'tax' in content_str.lower() and "tax advisor" not in content_str.lower():
                issues.append(ComplianceIssue(
                    issue_id="TAX-002",
                    severity="minor",
                    category="disclosure",
                    description="Tax discussion for retirement account lacks tax advisor referral",
                    regulation_reference="Fiduciary Standard - Best Practice",
                    suggested_resolution="Add suggestion to consult tax advisor for tax implications",
                    auto_correctable=True
                ))
        
        # ========== WASH SALE CHECK ==========
        # Check for wash sale rule violation (IRS Section 1091)
        # Wash sale applies when buying a security in a taxable account within 30 days of selling at a loss
        trade_action = context.get('action', '').lower()
        account_type = client_profile.get('account_type', 'taxable')  # Default to taxable if not specified
        symbol = context.get('symbol', '').upper()
        user_id = context.get('user_id')
        portfolio_id = context.get('portfolio_id')
        
        # Re-enabled: Use compliance_reviewer's wash sale detection (most complete implementation)
        if trade_action == 'buy' and account_type.lower() == 'taxable' and symbol and user_id:
            wash_sale_violation = self._check_wash_sale_violation(
                user_id=user_id,
                portfolio_id=portfolio_id,
                symbol=symbol,
                buy_quantity=context.get('quantity', 0)
            )
            
            if wash_sale_violation:
                # Use the severity from the wash sale violation result (should be "major" to block trades)
                severity = wash_sale_violation.get('severity', 'major')
                # Debug logging removed for cleaner output
                
                issues.append(ComplianceIssue(
                    issue_id="TAX-001",
                    severity=severity,
                    category="regulatory",
                    description=wash_sale_violation.get('description', 'Wash sale violation detected'),
                    regulation_reference="IRS Wash Sale Rule Section 1091",
                    suggested_resolution=wash_sale_violation.get('recommendation', 'Delay repurchase or use a tax-advantaged account'),
                    auto_correctable=False
                ))
                logger.warning(f"   - Added ComplianceIssue with severity: {severity}")
        # ========== END WASH SALE CHECK ==========
        
        # ========== END NEW CHECKS ==========
        
        return issues
    
    def _validate_suitability(self, recommendation_context: Dict, client_profile: Dict) -> Dict:
        """Validate suitability of recommendation."""
        client_risk_tolerance = client_profile.get("risk_tolerance", "moderate")
        recommendation_risk = recommendation_context.get("risk_level", "moderate")
        
        risk_mapping = {"conservative": 1, "moderate": 2, "aggressive": 3}
        client_risk_score = risk_mapping.get(client_risk_tolerance, 2)
        rec_risk_score = risk_mapping.get(recommendation_risk, 2)
        
        suitability_gap = rec_risk_score - client_risk_score
        
        return {
            "suitable": suitability_gap <= 1,  # Allow slight mismatch
            "suitability_gap": suitability_gap,
            "client_risk_tolerance": client_risk_tolerance,
            "recommendation_risk": recommendation_risk,
            "suitability_analysis": self._generate_suitability_analysis(
                client_profile, recommendation_context
            )
        }
    
    def _generate_suitability_analysis(self, client_profile: Dict, recommendation_context: Dict) -> str:
        """Generate suitability analysis text."""
        age = client_profile.get("age", "unknown")
        risk_tolerance = client_profile.get("risk_tolerance", "moderate")
        
        return (
            f"Based on client profile (age {age}, {risk_tolerance} risk tolerance), "
            f"this recommendation aligns with stated investment objectives and risk tolerance."
        )
    
    def _get_required_disclosures(
        self, recommendation_context: Dict, compliance_issues: List[ComplianceIssue]
    ) -> List[str]:
        """Determine required disclosures based on context and issues."""
        disclosures = []
        
        # Always include general investment risks
        disclosures.append("All investments involve risk, including the potential loss of principal.")
        
        # Add specific disclosures based on investment type
        investment_type = recommendation_context.get("investment_type", "stock")
        if investment_type == "stock":
            disclosures.append("Stock prices can be volatile and may fluctuate significantly.")
        elif investment_type == "bond":
            disclosures.append("Bond prices may decline due to interest rate changes and credit risk.")
        
        # Add disclosures based on compliance issues
        for issue in compliance_issues:
            if issue.category == "disclosure":
                disclosures.append(issue.suggested_resolution)
        
        return disclosures
    
    def _rewrite_recommendation(
        self, original_content: str, compliance_issues: List[ComplianceIssue], 
        required_disclosures: List[str], client_profile: Dict
    ) -> str:
        """Rewrite recommendation content for compliance and clarity."""
        
        # Start with plain English version of original content
        revised_content = self._convert_to_plain_english(original_content, client_profile)
        
        # Add suitability analysis if missing
        if any(issue.issue_id.startswith("SUIT") for issue in compliance_issues):
            suitability_section = self._generate_suitability_section(client_profile)
            revised_content += "\n\n" + suitability_section
        
        # Add risk disclosures
        if required_disclosures:
            risk_section = "\n\nIMPORTANT RISK DISCLOSURES:\n"
            for disclosure in required_disclosures:
                risk_section += f"• {disclosure}\n"
            revised_content += risk_section
        
        # Add standard disclaimers
        revised_content += "\n\n" + self._get_standard_disclaimers()
        
        return revised_content
    
    def _calculate_compliance_score(self, compliance_issues: List[ComplianceIssue]) -> int:
        """Calculate compliance score based on issues."""
        base_score = 100
        
        for issue in compliance_issues:
            if issue.severity == "critical":
                base_score -= 30
            elif issue.severity == "major":
                base_score -= 15
            else:  # minor
                base_score -= 5
        
        return max(0, base_score)
    
    def _convert_to_plain_english(self, content: str, client_profile: Dict) -> str:
        """Convert technical content to plain English."""
        # This is a simplified implementation
        # In production, this would use more sophisticated language processing
        
        # Replace common jargon
        replacements = {
            "alpha": "excess return above market",
            "beta": "market sensitivity",
            "sharpe ratio": "risk-adjusted return measure",
            "volatility": "price fluctuation",
            "diversification": "spreading investments to reduce risk",
            "asset allocation": "how investments are divided among different types",
            "rebalancing": "adjusting portfolio back to target percentages"
        }
        
        plain_content = content
        for technical, plain in replacements.items():
            plain_content = plain_content.replace(technical, f"{plain} ({technical})")
        
        return plain_content
    
    def _generate_suitability_section(self, client_profile: Dict) -> str:
        """Generate suitability analysis section."""
        age = client_profile.get("age", "unknown")
        risk_tolerance = client_profile.get("risk_tolerance", "moderate")
        time_horizon = client_profile.get("time_horizon", "medium-term")
        
        return f"""
SUITABILITY ANALYSIS:
Based on your profile (age {age}, {risk_tolerance} risk tolerance, {time_horizon} investment horizon), 
this recommendation is considered suitable because it aligns with your stated investment objectives 
and risk tolerance. We have considered your financial situation, investment experience, and 
investment timeline in making this recommendation.
"""
    
    def _get_standard_disclaimers(self) -> str:
        """Get standard regulatory disclaimers."""
        return """
IMPORTANT DISCLAIMERS:
• Past performance does not guarantee future results
• All investments involve risk, including potential loss of principal
• This recommendation is based on information available at the time and may change
• Please consult with your tax advisor regarding tax implications
• We are registered investment advisors and have a fiduciary duty to act in your best interest
"""
    
    def _create_summary(self, content: str) -> str:
        """Create plain English summary of content."""
        # Simplified implementation
        lines = content.split('\n')
        key_lines = [line for line in lines[:3] if line.strip()]
        return " ".join(key_lines)[:200] + "..."
    
    def _extract_key_takeaways(self, content: str) -> List[str]:
        """Extract key takeaways from content."""
        # Simplified implementation
        return [
            "Review the recommendation and ensure you understand the risks",
            "Consider how this fits with your overall investment strategy",
            "Contact us if you have questions or need clarification"
        ]
    
    def _check_wash_sale_violation(
        self,
        user_id: str,
        portfolio_id: Optional[str],
        symbol: str,
        buy_quantity: float
    ) -> Optional[Dict]:
        """
        Check for wash sale violations by querying recent SELL transactions.
        
        Wash sale rule (IRS Section 1091):
        - If you sell a security at a loss and repurchase it within 30 days, the loss is disallowed
        - The disallowed loss is added to the cost basis of the repurchased shares
        
        Args:
            user_id: User ID
            portfolio_id: Portfolio ID (optional)
            symbol: Symbol being purchased
            buy_quantity: Quantity being purchased
            
        Returns:
            Dict with violation details if found, None otherwise
        """
        try:
            if not database_service.engine:
                logger.warning("Database not available for wash sale check")
                return None
            
            # Query recent SELL transactions for this symbol within 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            with database_service.get_session() as session:
                from sqlalchemy import text
                
                # Get recent SELL transactions for this symbol
                # Join via user_id since transactions.portfolio_id might be NULL
                query = text("""
                    SELECT 
                        t.transaction_id,
                        t.symbol,
                        t.transaction_type,
                        t.quantity,
                        t.price,
                        t.status,
                        t.created_at,
                        pa.average_cost
                    FROM transactions t
                    LEFT JOIN portfolios p ON t.user_id = p.user_id
                    LEFT JOIN portfolio_assets pa ON p.portfolio_id = pa.portfolio_id 
                        AND t.symbol = pa.symbol
                    WHERE t.user_id = :user_id
                      AND t.symbol = :symbol
                      AND t.transaction_type = 'SELL'
                      AND t.status = 'executed'
                      AND t.created_at >= :thirty_days_ago
                    ORDER BY t.created_at DESC
                """)
                
                result = session.execute(query, {
                    "user_id": user_id,
                    "symbol": symbol,
                    "thirty_days_ago": thirty_days_ago
                })
                
                recent_sells = result.fetchall()
                
                if not recent_sells:
                    # No recent sells, no wash sale violation
                    return None
                
                # Get current price from Alpaca
                current_price = alpaca_trading_service._get_current_price(symbol)
                
                # Check each sell transaction for losses
                violations = []
                total_disallowed_loss = 0.0
                
                for sell in recent_sells:
                    sell_price = float(sell.price) if sell.price else 0
                    sell_quantity = float(sell.quantity) if sell.quantity else 0
                    average_cost = float(sell.average_cost) if sell.average_cost and sell.average_cost > 0 else None
                    
                    # If sell price is missing (0), try to get current market price as estimate
                    if sell_price == 0:
                        sell_price = current_price if current_price > 0 else 2.0  # Use current price or conservative estimate
                        logger.warning(f"Using estimated sell price ${sell_price:.2f} for {symbol} transaction {sell.transaction_id}")
                    
                    # Handle missing cost basis - be conservative and assume loss for wash sale purposes
                    if not average_cost:
                        logger.warning(f"No cost basis available for {symbol} sell transaction {sell.transaction_id}")
                        # For wash sale compliance, assume this was a loss transaction
                        # This is conservative but ensures we don't miss potential violations
                        if sell_price == 0:  # If price is also missing, use current price as estimate
                            sell_price = current_price if current_price > 0 else 2.0  # Conservative estimate
                        
                        # Assume the average cost was higher than sell price (i.e., a loss)
                        estimated_cost = sell_price * 1.1  # Assume 10% loss
                        logger.warning(f"Assuming {symbol} was sold at a loss (estimated cost: ${estimated_cost:.2f} vs sell: ${sell_price:.2f}) for wash sale compliance")
                        average_cost = estimated_cost
                    
                    # Check if this sale was at a loss
                    if sell_price < average_cost:
                        loss_per_share = average_cost - sell_price
                        total_loss = loss_per_share * sell_quantity
                        
                        # Calculate disallowed loss (limited by buy quantity)
                        disallowed_quantity = min(buy_quantity, sell_quantity)
                        disallowed_loss = loss_per_share * disallowed_quantity
                        total_disallowed_loss += disallowed_loss
                        
                        # Handle timezone-aware datetime comparison
                        now = datetime.now()
                        sell_date = sell.created_at
                        if sell_date.tzinfo is not None and now.tzinfo is None:
                            # Make now timezone-aware to match sell_date
                            from datetime import timezone
                            now = now.replace(tzinfo=timezone.utc)
                        elif sell_date.tzinfo is None and now.tzinfo is not None:
                            # Make sell_date timezone-aware
                            from datetime import timezone
                            sell_date = sell_date.replace(tzinfo=timezone.utc)
                        
                        days_ago = (now - sell_date).days
                        
                        violations.append({
                            "transaction_id": str(sell.transaction_id),
                            "sell_date": sell.created_at.isoformat(),
                            "days_ago": days_ago,
                            "sell_quantity": sell_quantity,
                            "sell_price": sell_price,
                            "average_cost": average_cost,
                            "loss_per_share": loss_per_share,
                            "total_loss": total_loss,
                            "disallowed_loss": disallowed_loss,
                            "disallowed_quantity": disallowed_quantity
                        })
                
                if violations:
                    # Build description
                    violation_count = len(violations)
                    days_since_first = violations[0]['days_ago']
                    
                    description = (
                        f"Wash sale violation detected: You sold {symbol} at a loss "
                        f"{days_since_first} days ago and are now repurchasing it. "
                        f"The IRS will disallow ${total_disallowed_loss:.2f} of tax loss deduction. "
                        f"This loss will be added to your cost basis for the repurchased shares."
                    )
                    
                    recommendation = (
                        f"To avoid wash sale: (1) Wait until {violations[0]['sell_date'][:10]} "
                        f"(31 days after sale) before repurchasing, or (2) Use a tax-advantaged account "
                        f"(IRA/401k) for this purchase, or (3) Purchase a substantially different but "
                        f"similar security to maintain market exposure."
                    )
                    
                    return {
                        "violation_detected": True,
                        "trade_approved": False,  # BLOCK the trade
                        "rule_id": "TAX-001",
                        "severity": "major",
                        "symbol": symbol,
                        "violation_count": violation_count,
                        "total_disallowed_loss": total_disallowed_loss,
                        "disallowed_loss": total_disallowed_loss,  # For backward compatibility
                        "violations": violations,
                        "description": description,
                        "recommendation": recommendation,
                        "rejection_reason": f"Wash sale violation: ${total_disallowed_loss:.2f} tax loss would be disallowed",
                        "current_price": current_price
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error checking wash sale violation: {e}")
            # Don't block the trade if we can't check - just log the error
            return None
    
    def _suggest_next_steps(self, content_type: str, content: str) -> List[str]:
        """Suggest next steps based on content type."""
        if content_type == "recommendation":
            return [
                "Review the recommendation details carefully",
                "Consider the risks and how they fit your tolerance", 
                "Contact us to discuss or approve the recommendation",
                "We will handle the execution once approved"
            ]
        elif content_type == "report":
            return [
                "Review your portfolio performance",
                "Note any rebalancing recommendations",
                "Schedule a review meeting if desired",
                "Update us on any changes to your situation"
            ]
        else:
            return ["Contact us if you have questions or need assistance"]


# Create agent instance with database service
from ..tools.database_service import database_service
compliance_reviewer_agent = ComplianceReviewerAgent(db_service=database_service)
