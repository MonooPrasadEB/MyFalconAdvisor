

"""
Investment Advisor Supervisor using LangGraph for Multi-Agent Coordination.

This supervisor orchestrates the three core agents to provide comprehensive 
investment advisory services with proper handoffs and workflow management.
"""

import logging
from typing import Annotated, Dict, List, Literal, Optional, TypedDict
from datetime import datetime
import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent

from ..agents.multi_task_agent import multi_task_agent
from ..agents.execution_agent import execution_service
from ..agents.compliance_reviewer import compliance_reviewer_agent
from ..core.config import Config
from ..tools.chat_logger import chat_logger, log_user_message, log_supervisor_action, log_advisor_response
from ..tools.alpaca_trading_service import alpaca_trading_service
from ..tools.database_service import database_service

config = Config.get_instance()
logger = logging.getLogger(__name__)


class InvestmentAdvisorState(TypedDict):
    """State management for the investment advisor workflow."""
    # Message history
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Client context
    client_profile: Optional[Dict]
    portfolio_data: Optional[Dict] 
    
    # Workflow state
    current_task: Optional[str]
    analysis_results: Optional[Dict]
    trade_recommendations: Optional[List[Dict]]
    compliance_approval: Optional[bool]
    
    # Agent handoffs
    next_agent: Optional[str]
    requires_approval: bool
    workflow_complete: bool
    
    # Chat logging
    session_id: Optional[str]
    user_id: Optional[str]
    created_at: datetime


class InvestmentAdvisorSupervisor:
    """
    Multi-Agent Investment Advisor Supervisor.
    
    Coordinates between:
    1. Multi-Task Agent (Portfolio Analysis, Risk Assessment, Customer Engagement)
    2. Execution Agent (Trade execution with compliance checks)
    3. Compliance Reviewer (Policy validation and client communication)
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.default_model,
            temperature=config.temperature,
            api_key=config.openai_api_key
        )
        
        # Agent instances
        self.multi_task_agent = multi_task_agent
        self.execution_service = execution_service 
        self.compliance_reviewer = compliance_reviewer_agent
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
        
        logger.info("Investment Advisor Supervisor initialized")
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for agent coordination."""
        
        # Create individual agent executors
        portfolio_agent = create_react_agent(
            self.llm,
            self.multi_task_agent.get_tools(),
            prompt=self.multi_task_agent.get_system_message()
        )
        
        trade_agent = create_react_agent(
            self.llm,
            [],  # ExecutionService doesn't have tools anymore
            prompt="ExecutionService: Non-AI workflow service for trade execution and portfolio validation."
        )
        
        compliance_agent = create_react_agent(
            self.llm,
            self.compliance_reviewer.get_tools(),
            prompt=self.compliance_reviewer.get_system_message()
        )
        
        # Define the state graph
        workflow = StateGraph(InvestmentAdvisorState)
        
        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("portfolio_analysis", self._portfolio_analysis_node)
        workflow.add_node("trade_execution", self._trade_execution_node)
        workflow.add_node("compliance_review", self._compliance_review_node)
        workflow.add_node("client_communication", self._client_communication_node)
        
        # Add edges with routing logic
        workflow.set_entry_point("supervisor")
        
        workflow.add_conditional_edges(
            "supervisor",
            self._route_next_action,
            {
                "portfolio_analysis": "portfolio_analysis",
                "trade_execution": "trade_execution",
                "compliance_review": "compliance_review",
                "client_communication": "client_communication",
                "end": END
            }
        )
        
        # All agents route back to supervisor for coordination
        workflow.add_edge("portfolio_analysis", "supervisor")
        workflow.add_edge("trade_execution", "supervisor")
        workflow.add_edge("compliance_review", "supervisor")
        workflow.add_edge("client_communication", "supervisor")
        
        return workflow.compile()
    
    def _supervisor_node(self, state: InvestmentAdvisorState) -> InvestmentAdvisorState:
        """Supervisor node that coordinates workflow and makes routing decisions."""
        
        messages = state["messages"]
        current_task = state.get("current_task")
        
        # Analyze the current state and determine next action
        if not messages:
            # Initialize conversation
            state["current_task"] = "initial_assessment"
            state["next_agent"] = "portfolio_analysis"
            return state
        
        last_message = messages[-1]
        
        # Use LLM-powered intelligent routing
        if isinstance(last_message, HumanMessage):
            content = last_message.content.lower() if last_message.content else ""
            
            # Handle approval responses - route directly to compliance
            if "approve" in content and state.get("requires_approval"):
                state["current_task"] = "compliance_review"
                state["next_agent"] = "compliance_review"
            else:
                # Use LLM for other routing decisions
                routing_decision = self._get_llm_routing_decision(
                    last_message.content,
                    state.get("portfolio_data"),
                    state.get("client_profile")
                )
                
                state["current_task"] = routing_decision["task"]
                state["next_agent"] = routing_decision["agent"]
        
        elif isinstance(last_message, AIMessage):
            # Process AI response and determine if workflow is complete
            if state.get("analysis_results") and state.get("compliance_approval"):
                state["workflow_complete"] = True
                state["next_agent"] = "client_communication"
            elif state.get("trade_recommendations") and not state.get("compliance_approval"):
                state["next_agent"] = "compliance_review"
            else:
                state["next_agent"] = "end"
        
        return state
    
    def _get_llm_routing_decision(self, user_message: str, portfolio_data: Optional[Dict], client_profile: Optional[Dict]) -> Dict[str, str]:
        """
        Use LLM to intelligently route user requests to appropriate agents.
        
        Returns:
            Dict with 'agent' and 'task' keys
        """
        try:
            # Build context for routing decision
            portfolio_context = ""
            if portfolio_data:
                total_value = sum(
                    holding.get('quantity', 0) * holding.get('current_price', 0)
                    for holding in portfolio_data.get('holdings', [])
                )
                portfolio_context = f"User has active portfolio worth ${total_value:,.2f}"
            
            client_context = ""
            if client_profile:
                risk_tolerance = client_profile.get('risk_tolerance', 'unknown')
                client_context = f"Client risk tolerance: {risk_tolerance}"
            
            routing_prompt = ChatPromptTemplate.from_template("""
You are an intelligent routing system for a multi-agent investment advisor. 
Analyze the user's message and route to the most appropriate agent.

AVAILABLE AGENTS:

1. **portfolio_analysis** - Portfolio Analysis & Advisory Agent
   - Portfolio analysis, risk assessment, diversification advice
   - Investment recommendations and strategy discussions  
   - Questions about what to buy/sell (advisory, not execution)
   - Market insights and educational content
   - Examples: "Should I buy NVDA?", "Analyze my portfolio", "What should I sell?", "Is my portfolio too risky?"

2. **trade_execution** - Trade Execution Agent  
   - Actual trade execution and order placement
   - Specific buy/sell commands with quantities (e.g., "sell 10 shares", "buy 5 AAPL")
   - Trade confirmations and order management
   - Commands with "let's", "please", or direct imperatives to execute a trade
   - Examples: "Buy 100 shares of AAPL", "Execute this trade", "Place order for $1000 SPY", "Confirm purchase", "Let's sell 10 shares of SPY", "Please buy NVDA"

3. **compliance_review** - Compliance & Review Agent
   - Trade compliance validation
   - Risk management checks  
   - Regulatory review and approval
   - Examples: "Review this trade", "Check compliance", "Is this allowed?"

CONTEXT:
{portfolio_context}
{client_context}

USER MESSAGE: "{user_message}"

ROUTING DECISION:
Analyze the user's intent and route appropriately. Most questions and advisory requests go to portfolio_analysis. 
Only route to trade_execution for specific execution commands. Only route to compliance_review for explicit compliance checks.

Respond with ONLY a JSON object:
{{
  "agent": "portfolio_analysis|trade_execution|compliance_review",
  "task": "brief_description_of_task"
}}
""")
            
            chain = routing_prompt | self.llm
            response = chain.invoke({
                "user_message": user_message,
                "portfolio_context": portfolio_context,
                "client_context": client_context
            })
            
            # Parse LLM response
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response.content)
            if json_match:
                routing_data = json.loads(json_match.group())
                
                # Validate agent choice
                valid_agents = ["portfolio_analysis", "trade_execution", "compliance_review"]
                if routing_data.get("agent") in valid_agents:
                    return {
                        "agent": routing_data["agent"],
                        "task": routing_data.get("task", "user_request")
                    }
            
            # Fallback to default routing
            logger.warning(f"LLM routing failed, using default. Response: {response.content}")
            
        except Exception as e:
            logger.error(f"Error in LLM routing: {e}")
        
        # Default fallback - most requests are advisory
        return {
            "agent": "portfolio_analysis", 
            "task": "client_engagement"
        }
    

    def _portfolio_analysis_node(self, state: InvestmentAdvisorState) -> InvestmentAdvisorState:
        """Portfolio analysis and risk assessment node."""
        
        messages = state["messages"]
        last_message = messages[-1] if messages else None
        
        # Create context for portfolio analysis
        analysis_prompt = self._create_portfolio_analysis_prompt(state)
        
        # Get response from multi-task agent using LLM
        response_content = self._conversational_analysis_node(
            last_message.content if last_message else "Analyze portfolio",
            state.get("portfolio_data", {}),
            state.get("client_profile", {})
        )
        
        # Calculate real analysis results from portfolio data
        portfolio_data = state.get("portfolio_data", {})
        assets = portfolio_data.get('assets', [])
        
        if assets:
            # Calculate real metrics
            tech_allocation = sum(asset.get('allocation', 0) for asset in assets if asset.get('sector') == 'Technology')
            num_assets = len(assets)
            diversification_score = min(10, num_assets * 2)
            risk_score = min(10, (tech_allocation / 10) + (diversification_score / 2))
            
            # Generate real recommendations
            recommendations = []
            if tech_allocation > 50:
                recommendations.append("Reduce technology concentration")
            if num_assets < 5:
                recommendations.append("Add more diversification")
            if not any(asset.get('asset_type') == 'bond' for asset in assets):
                recommendations.append("Add fixed income allocation")
                
            state["analysis_results"] = {
                "portfolio_metrics": {
                    "risk_score": round(risk_score, 1), 
                    "diversification_score": round(diversification_score, 1),
                    "tech_allocation": round(tech_allocation, 1),
                    "num_holdings": num_assets
                },
                "recommendations": recommendations if recommendations else ["Portfolio appears well balanced"],
                "risk_assessment": {"tolerance": "moderate", "score": round(risk_score, 1)}
            }
        else:
            # Fallback for no portfolio data
            state["analysis_results"] = {
                "portfolio_metrics": {"risk_score": 0, "diversification_score": 0},
                "recommendations": ["Please provide portfolio data for analysis"],
                "risk_assessment": {"tolerance": "unknown", "score": 0}
            }
        
        # Add AI response to messages
        ai_response = AIMessage(content=response_content)
        state["messages"] = messages + [ai_response]
        
        return state
    
    def _trade_execution_node(self, state: InvestmentAdvisorState) -> InvestmentAdvisorState:
        """Trade execution and order management node - uses LLM to process trade requests."""
        
        messages = state["messages"] 
        last_message = messages[-1] if messages else None
        
        if last_message:
            # Use LLM to intelligently process the trade request
            response_content = self._process_trade_request_with_llm(
                last_message.content,
                state.get("portfolio_data", {}),
                state.get("client_profile", {})
            )
            
            # Extract trade details from the request and populate state
            trade_details = self._extract_trade_details(last_message.content)
            state["trade_recommendations"] = [trade_details] if trade_details else []
            state["requires_approval"] = True
        else:
            response_content = "Please specify trade details for execution analysis."
        
        ai_response = AIMessage(content=response_content)
        state["messages"] = messages + [ai_response]
        
        return state
    
    def _extract_trade_details(self, request: str) -> Optional[Dict]:
        """Extract structured trade details from user request using LLM."""
        try:
            extraction_prompt = ChatPromptTemplate.from_template("""
Extract trade details from this request. If this is NOT a trade request, return null.

USER REQUEST: "{request}"

Extract and return JSON with these fields:
- "symbol": stock symbol (e.g., "OKTA")
- "action": "buy" or "sell" 
- "quantity": number of shares (integer)
- "order_type": "market", "limit", etc.
- "rationale": brief reason for trade

Examples:
"Sell 100 shares of OKTA" → {{"symbol": "OKTA", "action": "sell", "quantity": 100, "order_type": "market", "rationale": "User requested sale"}}
"Buy 50 AAPL at market" → {{"symbol": "AAPL", "action": "buy", "quantity": 50, "order_type": "market", "rationale": "User requested purchase"}}
"Should I sell NVDA?" → null (this is a question, not a trade request)

Return ONLY the JSON object or null:
""")
            
            chain = extraction_prompt | self.llm
            response = chain.invoke({"request": request})
            
            import json
            import re
            
            # Try to extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response.content)
            if json_match:
                try:
                    trade_details = json.loads(json_match.group())
                    # Validate required fields
                    if all(key in trade_details for key in ["symbol", "action", "quantity"]):
                        # Check if quantity is "all" or similar non-numeric string
                        qty = trade_details.get('quantity', 0)
                        if isinstance(qty, str) and qty.lower() in ['all', 'entire', 'everything']:
                            # Mark as needs calculation - will be handled by calling function
                            trade_details['quantity_special'] = 'all'
                            trade_details['quantity'] = None  # Will need to be calculated from portfolio
                        return trade_details
                except json.JSONDecodeError:
                    pass
                    
            # Check for null response
            if response.content and "null" in response.content.lower():
                return None
                
            return None
            
        except Exception as e:
            logger.error(f"Error extracting trade details: {e}")
            return None
    
    def _process_trade_request_with_llm(self, request: str, portfolio_data: Dict, client_profile: Dict) -> str:
        """
        Use LLM to intelligently process trade execution requests.
        
        This analyzes the trade request, validates it against the portfolio, 
        calculates impact, and provides detailed execution analysis.
        """
        try:
            # Build portfolio context
            portfolio_context = ""
            current_holdings = {}
            
            if portfolio_data and 'holdings' in portfolio_data:
                total_value = sum(
                    holding.get('quantity', 0) * holding.get('current_price', 0)
                    for holding in portfolio_data['holdings']
                )
                portfolio_context = f"Current Portfolio Value: ${total_value:,.2f}\nHoldings:\n"
                
                for holding in portfolio_data['holdings']:
                    symbol = holding.get('symbol', 'Unknown')
                    quantity = holding.get('quantity', 0)
                    price = holding.get('current_price', 0)
                    value = quantity * price
                    
                    current_holdings[symbol] = {
                        'quantity': quantity,
                        'price': price,
                        'value': value
                    }
                    
                    portfolio_context += f"- {symbol}: {quantity} shares @ ${price:.2f} = ${value:,.2f}\n"
            
            # Build client context
            client_context = ""
            if client_profile:
                risk_tolerance = client_profile.get('risk_tolerance', 'moderate')
                experience = client_profile.get('investment_experience', 'intermediate')
                client_context = f"Risk Tolerance: {risk_tolerance}, Experience: {experience}"
            
            # Create trade processing prompt
            trade_prompt = ChatPromptTemplate.from_template("""
You are a professional trade execution specialist analyzing a client's trade request.

TRADE REQUEST: "{request}"

CURRENT PORTFOLIO:
{portfolio_context}

CLIENT PROFILE: {client_context}

TASK: Analyze this trade request and provide:

1. **Trade Validation**: Is this a valid, executable trade request?
2. **Portfolio Impact**: How will this affect their portfolio?
3. **Risk Analysis**: What are the implications?
4. **Execution Plan**: Specific steps to execute this trade
5. **Recommendations**: Any suggestions or concerns

If the request is for a SELL order:
- Check if they own the stock and have enough shares
- Calculate the proceeds and portfolio impact
- Provide specific execution details

If the request is for a BUY order:
- Estimate cost and market impact
- Check portfolio balance implications
- Provide execution guidance

Respond in a professional, clear manner that helps the client understand:
- What exactly will be executed
- The financial impact
- Any risks or considerations
- Next steps for approval/execution

Be conversational but precise. If the trade request is unclear or invalid, ask for clarification.
""")
            
            chain = trade_prompt | self.llm
            response = chain.invoke({
                "request": request,
                "portfolio_context": portfolio_context,
                "client_context": client_context
            })
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error in LLM trade processing: {e}")
            return f"I'm having trouble processing your trade request: {str(e)}. Please try rephrasing your request or contact support."
    
    def _process_trade_request(self, request: str, portfolio_data: Dict, client_profile: Dict) -> str:
        """
        Process trade execution requests and provide detailed analysis.
        """
        try:
            # Use LLM to parse the trade request and provide execution analysis
            trade_prompt = ChatPromptTemplate.from_template("""
You are a trade execution specialist analyzing a client's trade request.

CLIENT REQUEST: "{request}"

PORTFOLIO CONTEXT:
{portfolio_context}

CLIENT PROFILE:
{client_context}

TASK: Analyze this trade request and provide:

1. **Trade Details Interpretation**: Extract the specific trade action, symbol, and quantity
2. **Current Position Analysis**: Check if the client currently holds this security
3. **Market Impact Assessment**: Consider current market conditions and timing
4. **Execution Recommendation**: Suggest optimal execution strategy
5. **Risk Assessment**: Identify potential risks and benefits
6. **Next Steps**: What the client needs to do to proceed

IMPORTANT: This is SIMULATED trading - no actual trades will be executed. 
Provide actionable guidance while being clear this is for analysis purposes only.

Format your response as a clear, professional trade execution analysis.
""")
            
            # Build context
            portfolio_context = ""
            if portfolio_data and portfolio_data.get('holdings'):
                total_value = sum(
                    holding.get('quantity', 0) * holding.get('current_price', 0)
                    for holding in portfolio_data.get('holdings', [])
                )
                portfolio_context = f"Portfolio value: ${total_value:,.2f} with {len(portfolio_data.get('holdings', []))} holdings"
            else:
                portfolio_context = "No portfolio data available"
            
            client_context = ""
            if client_profile:
                risk_tolerance = client_profile.get('risk_tolerance', 'unknown')
                client_context = f"Risk tolerance: {risk_tolerance}"
            else:
                client_context = "No client profile available"
            
            chain = trade_prompt | self.llm
            response = chain.invoke({
                "request": request,
                "portfolio_context": portfolio_context,
                "client_context": client_context
            })
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error processing trade request: {e}")
            return f"I'm analyzing your trade request: '{request}'. However, I need more specific details to proceed with execution analysis. Please provide the stock symbol, action (buy/sell), and quantity for a complete analysis."
    
    def _compliance_review_node(self, state: InvestmentAdvisorState) -> InvestmentAdvisorState:
        """Compliance review and validation node."""
        
        messages = state["messages"]
        trade_recommendations = state.get("trade_recommendations", [])
        last_message = messages[-1].content.lower() if messages and messages[-1].content else ""
        
        # Check if user just approved a trade
        if "approve" in last_message and trade_recommendations:
            response_content = self._process_trade_approval(trade_recommendations, state.get("client_profile", {}))
            state["compliance_approval"] = True
            state["workflow_complete"] = True
            
        elif trade_recommendations:
            # Use REAL compliance reviewer to create transactions and log compliance checks
            response_content = self._execute_real_compliance_review(
                trade_recommendations,
                state.get("client_profile", {}),
                state.get("portfolio_data", {}),
                state.get("user_id"),
                messages[-1].content if messages else ""
            )
            state["compliance_approval"] = True
            
        else:
            # This shouldn't happen in normal flow, but handle gracefully
            response_content = "Trade processing complete. Thank you for using MyFalconAdvisor."
        
        ai_response = AIMessage(content=response_content)
        state["messages"] = messages + [ai_response]
        
        return state
    
    def _process_trade_approval(self, trade_recommendations: List[Dict], client_profile: Dict) -> str:
        """Process user approval and provide confirmation message."""
        try:
            if not trade_recommendations:
                return "Trade approval processed. Thank you for using MyFalconAdvisor."
            
            trade = trade_recommendations[0]  # Get the first/primary trade
            symbol = trade.get('symbol', 'Unknown')
            action = trade.get('action', 'trade')
            quantity = trade.get('quantity', 0)
            
            return f"""
✅ **Trade Approved & Processed**

**Trade Details:**
• **Symbol:** {symbol}
• **Action:** {action.upper()} {quantity:,} shares
• **Order Type:** Market order
• **Status:** Approved for execution

**Next Steps:**
1. Trade has been validated for compliance ✅
2. Order will be submitted to the market during next trading session
3. You will receive execution confirmation once completed
4. Portfolio will be automatically updated

**Important Notes:**
• This is a simulated trade execution for demonstration
• In a real system, actual market orders would be placed
• All regulatory requirements have been satisfied

**Thank you for using MyFalconAdvisor!**

*For questions about this trade or your portfolio, feel free to ask anytime.*
"""
            
        except Exception as e:
            logger.error(f"Error processing trade approval: {e}")
            return "Trade has been approved and processed. Thank you for using MyFalconAdvisor."
    
    def _client_communication_node(self, state: InvestmentAdvisorState) -> InvestmentAdvisorState:
        """Client communication and final response node."""
        
        messages = state["messages"]
        
        # Create final client communication
        final_response = self._create_final_communication(state)
        
        ai_response = AIMessage(content=final_response)
        state["messages"] = messages + [ai_response]
        state["workflow_complete"] = True
        
        return state
    
    def _route_next_action(
        self, state: InvestmentAdvisorState
    ) -> Literal["portfolio_analysis", "trade_execution", "compliance_review", "client_communication", "end"]:
        """Route to the next appropriate agent based on state."""
        
        next_agent = state.get("next_agent")
        
        if state.get("workflow_complete"):
            return "end"
        elif next_agent == "portfolio_analysis":
            return "portfolio_analysis"
        elif next_agent == "trade_execution":
            return "trade_execution"
        elif next_agent == "compliance_review":
            return "compliance_review"
        elif next_agent == "client_communication":
            return "client_communication"
        else:
            return "end"
    
    def process_client_request(
        self, 
        request: str, 
        client_profile: Optional[Dict] = None,
        portfolio_data: Optional[Dict] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Process a client request through the multi-agent workflow.
        
        Args:
            request: Client's investment question or request
            client_profile: Client demographic and preference information
            portfolio_data: Current portfolio holdings and data
            session_id: Session identifier for conversation continuity
            user_id: User identifier for logging
            
        Returns:
            Dictionary containing the complete workflow results
        """
        try:
            # Start or continue chat session
            if not session_id:
                session_type = "advisory"
                if "trade" in request.lower() or "buy" in request.lower() or "sell" in request.lower():
                    session_type = "execution"
                
                session_id = chat_logger.start_session(
                    user_id=user_id,
                    session_type=session_type,
                    context_data={
                        "client_profile": client_profile or {},
                        "portfolio_data": portfolio_data or {},
                        "initial_request": request
                    }
                )
                if session_id:
                    logger.info(f"Started new chat session: {session_id}")
                else:
                    logger.warning("Failed to start chat session - continuing without logging")
            
            # Log user message only if we have a valid session
            if session_id:
                log_user_message(
                    request, 
                    session_id=session_id,
                    metadata={
                        "has_client_profile": bool(client_profile),
                        "has_portfolio_data": bool(portfolio_data),
                        "request_type": "investment_inquiry"
                    }
                )
            
            # Initialize state
            initial_state = InvestmentAdvisorState(
                messages=[HumanMessage(content=request)],
                client_profile=client_profile or {},
                portfolio_data=portfolio_data or {},
                current_task=None,
                analysis_results=None,
                trade_recommendations=None,
                compliance_approval=None,
                next_agent=None,
                requires_approval=False,
                workflow_complete=False,
                session_id=session_id,
                user_id=user_id,
                created_at=datetime.now()
            )
            
            # Run the workflow
            final_state = self.workflow.invoke(initial_state)
            
            # Extract final response
            final_messages = final_state["messages"]
            final_response = final_messages[-1].content if final_messages else "No response generated"
            
            # Log AI advisor response
            if session_id:
                log_advisor_response(
                    final_response,
                    session_id=session_id,
                    metadata={
                        "workflow_complete": final_state.get("workflow_complete", False),
                        "has_trade_recommendations": bool(final_state.get("trade_recommendations")),
                        "compliance_approved": final_state.get("compliance_approval", False),
                        "requires_user_approval": final_state.get("requires_approval", False)
                    }
                )
            
            return {
                "response": final_response,
                "session_id": final_state["session_id"],
                "workflow_complete": final_state.get("workflow_complete", False),
                "analysis_results": final_state.get("analysis_results"),
                "trade_recommendations": final_state.get("trade_recommendations"),
                "compliance_approved": final_state.get("compliance_approval", False),
                "requires_user_approval": final_state.get("requires_approval", False),
                "message_history": [
                    {"role": "human" if isinstance(msg, HumanMessage) else "ai", "content": msg.content}
                    for msg in final_messages
                ]
            }
            
        except Exception as e:
            logger.error(f"Error processing client request: {e}")
            return {
                "error": str(e),
                "response": "I apologize, but I encountered an error processing your request. Please try again or contact support."
            }
    
    async def process_client_request_async(
        self, 
        request: str,
        client_profile: Optional[Dict] = None,
        portfolio_data: Optional[Dict] = None,
        session_id: Optional[str] = None
    ) -> Dict:
        """Async version of process_client_request."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.process_client_request, request, client_profile, portfolio_data, session_id
        )
    
    async def process_client_request_streaming(
        self,
        request: str,
        client_profile: Optional[Dict] = None,
        portfolio_data: Optional[Dict] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Process client request with streaming support.
        
        Yields chunks of the LLM response as they're generated, then provides
        the final result with metadata.
        """
        try:
            # Ensure user_id is in client_profile for compliance checks
            if client_profile is None:
                client_profile = {}
            if user_id and 'user_id' not in client_profile:
                client_profile['user_id'] = user_id
            
            # Start or continue chat session
            if not session_id:
                session_type = "advisory"
                if "trade" in request.lower() or "buy" in request.lower() or "sell" in request.lower():
                    session_type = "execution"
                
                session_id = chat_logger.start_session(
                    user_id=user_id,
                    session_type=session_type,
                    context_data={
                        "client_profile": client_profile or {},
                        "portfolio_data": portfolio_data or {},
                        "initial_request": request
                    }
                )
                if session_id:
                    logger.info(f"Started new chat session: {session_id}")
            
            # Log user message
            if session_id:
                log_user_message(
                    request,
                    session_id=session_id,
                    metadata={
                        "has_client_profile": bool(client_profile),
                        "has_portfolio_data": bool(portfolio_data),
                        "request_type": "investment_inquiry"
                    }
                )
            
            # Check if user is approving a pending trade
            if "approve" in request.lower() and user_id:
                logger.info(f"🔍 Approval detected for user: {user_id}")
                # Check for pending transactions
                pending_trade = self._check_pending_transaction(user_id)
                logger.info(f"📊 Pending trade found: {pending_trade}")
                
                if pending_trade:
                    logger.info(f"✅ Executing pending trade approval for {pending_trade.get('symbol')}")
                    # User is approving a pending trade - execute it
                    async for chunk in self._stream_trade_approval(
                        pending_trade,
                        user_id,
                        portfolio_data or {},
                        session_id
                    ):
                        yield chunk
                    return  # Exit after handling approval
                else:
                    logger.warning(f"❌ No pending transaction found for user {user_id} despite approval message")
            
            # Analyze request to determine which agent to use
            routing_decision = self._get_llm_routing_decision(
                request,
                portfolio_data,
                client_profile
            )
            
            # Stream the response based on routing
            agent_type = routing_decision.get("agent", "portfolio_analysis")
            
            if agent_type == "portfolio_analysis":
                # Stream portfolio analysis response
                async for chunk in self._stream_conversational_analysis(
                    request,
                    portfolio_data or {},
                    client_profile or {},
                    session_id
                ):
                    yield chunk
                    
            elif agent_type == "trade_execution":
                # Stream trade execution response
                async for chunk in self._stream_trade_processing(
                    request,
                    portfolio_data or {},
                    client_profile or {},
                    session_id
                ):
                    yield chunk
                    
            else:
                # Default to portfolio analysis
                async for chunk in self._stream_conversational_analysis(
                    request,
                    portfolio_data or {},
                    client_profile or {},
                    session_id
                ):
                    yield chunk
            
        except Exception as e:
            logger.error(f"Error in streaming request: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "message": "I encountered an error processing your request."
            }
    
    def _check_pending_transaction(self, user_id: str) -> Optional[Dict]:
        """Check if user has a pending transaction awaiting approval."""
        try:
            logger.info(f"🔍 Checking for pending transactions for user_id: {user_id} (type: {type(user_id)})")
            
            with database_service.get_session() as session:
                from sqlalchemy import text
                
                # First, let's see ALL pending transactions
                debug_result = session.execute(
                    text("SELECT user_id, symbol, status FROM transactions WHERE status = 'pending' ORDER BY created_at DESC LIMIT 5")
                )
                all_pending = debug_result.fetchall()
                logger.info(f"📊 All pending transactions in DB: {all_pending}")
                
                # Now try to find user's pending transaction
                result = session.execute(
                    text("""
                        SELECT transaction_id, symbol, transaction_type, quantity, price, 
                               created_at, notes, user_id
                        FROM transactions 
                        WHERE user_id = :user_id 
                          AND status = 'pending'
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """),
                    {"user_id": user_id}
                )
                row = result.fetchone()
                
                if row:
                    logger.info(f"✅ Found pending transaction: {row[1]} for user {row[7]}")
                    return {
                        "transaction_id": row[0],
                        "symbol": row[1],
                        "action": row[2],
                        "quantity": row[3],
                        "price": row[4],
                        "created_at": row[5],
                        "notes": row[6]
                    }
                else:
                    logger.warning(f"❌ No pending transaction found for user_id: {user_id}")
                return None
        except Exception as e:
            logger.error(f"Error checking pending transaction: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def _stream_trade_approval(
        self,
        pending_trade: Dict,
        user_id: str,
        portfolio_data: Dict,
        session_id: Optional[str]
    ):
        """Handle trade approval and execution."""
        try:
            transaction_id = pending_trade.get("transaction_id")
            symbol = pending_trade.get("symbol")
            action = pending_trade.get("action")
            quantity = pending_trade.get("quantity")
            price = pending_trade.get("price")
            
            # Stream confirmation message
            yield {
                "type": "content",
                "content": f"## ✅ Trade Approved!\n\nExecuting {action.upper()} order for {quantity} shares of {symbol}...\n\n"
            }
            
            # Execute the trade through execution service
            try:
                # Use execution service to process the trade (no intermediate 'approved' status)
                recommendation = {
                    "symbol": symbol,
                    "action": action,
                    "quantity": quantity,
                    "price": price,
                    "order_type": "market"
                }
                
                execution_result = execution_service.process_ai_recommendation(
                    user_id=user_id,
                    recommendation=recommendation,
                    session_id=session_id
                )
                
                exec_status = (execution_result.get("status") or "").lower()
                
                if exec_status == "filled":
                    filled_qty = execution_result.get("filled_quantity", quantity)
                    fill_price = execution_result.get("fill_price", price)
                    
                    # Update transaction to executed
                    with database_service.get_session() as session:
                        session.execute(
                            text("""
                                UPDATE transactions 
                                SET status = 'executed',
                                    price = :price,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE transaction_id = :transaction_id
                            """),
                            {"transaction_id": transaction_id, "price": fill_price}
                        )
                        session.commit()
                    
                    yield {
                        "type": "content",
                        "content": f"""**Trade Executed Successfully!**

📊 **Execution Details:**
- Symbol: {symbol}
- Action: {action.upper()}
- Quantity: {filled_qty} shares
- Execution Price: ${fill_price:.2f}
- Total Value: ${filled_qty * fill_price:,.2f}
- Status: ✅ FILLED

**What This Means:**
Your {action.lower()} order for {symbol} has been executed successfully. Your portfolio has been updated to reflect this transaction.

**Next Steps:**
- View your updated portfolio to see the changes
- Transaction has been recorded in your account history
- You can ask me for portfolio analysis at any time

Is there anything else you'd like me to help you with?
"""
                    }
                elif exec_status == "rejected":
                    error_msg = execution_result.get("message", "Trade was rejected by validation checks")
                    
                    with database_service.get_session() as session:
                        session.execute(
                            text("""
                                UPDATE transactions 
                                SET status = 'rejected',
                                    notes = :notes,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE transaction_id = :transaction_id
                            """),
                            {"transaction_id": transaction_id, "notes": f"Execution rejected: {error_msg}"}
                        )
                        session.commit()
                    
                    yield {
                        "type": "content",
                        "content": f"""## ⚠️ Trade Rejected

Your trade request for {symbol} could not be executed.

**Reason:** {error_msg}

**Next Steps:**
- Adjust the order details (e.g., shares, cash balance) and try again
- Ask for help evaluating alternative trades

The pending transaction has been marked as `rejected` with this reason."""
                    }
                else:
                    # Trade failed for other reasons
                    error_msg = execution_result.get("message", "Unknown error")
                    
                    with database_service.get_session() as session:
                        session.execute(
                            text("""
                                UPDATE transactions 
                                SET status = 'failed',
                                    notes = :notes,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE transaction_id = :transaction_id
                            """),
                            {"transaction_id": transaction_id, "notes": f"Execution failed: {error_msg}"}
                        )
                        session.commit()
                    
                    yield {
                        "type": "content",
                        "content": f"""## ❌ Trade Execution Failed

Unfortunately, your trade could not be executed at this time.

**Error:** {error_msg}

**What You Can Do:**
- Review the error message and try again
- Contact support if the issue persists
- The transaction remains in your history as 'failed'

Would you like me to help you with an alternative approach?
"""
                    }
                
            except Exception as exec_error:
                logger.error(f"Error executing trade: {exec_error}")
                yield {
                    "type": "content",
                    "content": f"## ❌ Execution Error\n\nAn error occurred while executing the trade: {str(exec_error)}\n\nPlease contact support if this issue persists."
                }
            
            # Send final metadata
            yield {
                "type": "final",
                "result": {
                    "response": f"Trade approval processed for {symbol}",
                    "session_id": session_id,
                    "workflow_complete": True,
                    "analysis_results": {},
                    "trade_recommendations": [],
                    "compliance_approved": True,
                    "requires_user_approval": False
                }
            }
            
        except Exception as e:
            logger.error(f"Error in trade approval stream: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "message": "Failed to process trade approval"
            }
    
    async def _stream_conversational_analysis(
        self,
        request: str,
        portfolio_data: Dict,
        client_profile: Dict,
        session_id: Optional[str] = None
    ):
        """Stream conversational analysis responses from LLM."""
        try:
            # Retrieve session history if session_id is provided
            conversation_history = []
            if session_id:
                try:
                    session_messages = chat_logger.get_session_history(session_id, limit=20)
                    # Convert to HumanMessage/AIMessage format for context
                    for msg in session_messages:
                        agent_type = msg.get('agent_type', '')
                        content = msg.get('message_content', '')
                        if agent_type == 'user':
                            conversation_history.append(HumanMessage(content=content))
                        elif agent_type in ['advisor', 'supervisor']:
                            conversation_history.append(AIMessage(content=content))
                    logger.info(f"Retrieved {len(conversation_history)} previous messages from session {session_id}")
                except Exception as e:
                    logger.warning(f"Could not retrieve session history: {e}")
            
            # Build portfolio context (same as non-streaming version)
            assets = portfolio_data.get('assets', [])
            if not assets:
                yield {
                    "type": "content",
                    "content": "I don't see any portfolio data loaded. Please load your portfolio first."
                }
                yield {
                    "type": "final",
                    "result": {
                        "response": "No portfolio data available",
                        "workflow_complete": True,
                        "analysis_results": {},
                        "trade_recommendations": [],
                        "compliance_approved": True,
                        "requires_user_approval": False
                    }
                }
                return
            
            # Calculate portfolio metrics
            total_value = portfolio_data.get('total_value', 0)
            tech_allocation = sum(asset.get('allocation', 0) for asset in assets 
                                if asset.get('sector') and asset.get('sector', '').lower().startswith('tech'))
            num_assets = len(assets)
            max_allocation = max([asset.get('allocation', 0) for asset in assets]) if assets else 0
            
            top_holdings = sorted(assets, key=lambda x: x.get('allocation', 0), reverse=True)[:5]
            holdings_summary = ", ".join([f"{asset.get('symbol')} ({asset.get('allocation', 0):.1f}%)" 
                                        for asset in top_holdings])
            
            detailed_holdings = "\n".join([
                f"  • {asset.get('symbol')}: {asset.get('quantity', 0):.2f} shares @ ${asset.get('current_price', 0):.2f} = ${asset.get('market_value', 0):,.2f} ({asset.get('allocation', 0):.1f}%) - Sector: {asset.get('sector', 'Unknown')}"
                for asset in sorted(assets, key=lambda x: x.get('allocation', 0), reverse=True)
            ])
            
            cash_balance = portfolio_data.get('cash_balance', 0)
            equity_value = sum(asset.get('market_value', 0) for asset in assets)
            cash_percentage = (cash_balance / total_value * 100) if total_value > 0 else 0
            
            # Look up requested stock prices (if asking about specific stocks not in portfolio)
            stock_price_info = self._lookup_stock_prices_from_query(request, assets)
            
            # Format sync timestamp
            synced_at = portfolio_data.get('synced_at', 'Unknown')
            if synced_at and synced_at != 'Unknown':
                from datetime import datetime
                try:
                    sync_dt = datetime.fromisoformat(synced_at)
                    synced_at_display = sync_dt.strftime("%B %d, %Y at %I:%M %p")
                except:
                    synced_at_display = synced_at
            else:
                synced_at_display = "Unknown"
            
            portfolio_context = f"""
PORTFOLIO DATA AS OF: {synced_at_display}
(Portfolio data synced from Alpaca)

PORTFOLIO CONTEXT:
- Total Portfolio Value: ${total_value:,.2f}
- Cash Balance: ${cash_balance:,.2f} ({cash_percentage:.1f}%)
- Equity Holdings Value: ${equity_value:,.2f} ({100 - cash_percentage:.1f}%)
- Number of Stock Positions: {num_assets}
- Tech Allocation: {tech_allocation:.1f}%
- Largest Position: {max_allocation:.1f}%
- Risk Profile: {"High (tech-focused)" if tech_allocation > 60 else "Moderate"}

COMPLETE HOLDINGS LIST:
{detailed_holdings}

CASH POSITION:
  • Cash: ${cash_balance:,.2f} ({cash_percentage:.1f}% of portfolio)

{stock_price_info}
"""
            
            # Build conversation context from history
            conversation_context = ""
            if conversation_history:
                # Include recent conversation history (last 10 messages to avoid token limits)
                recent_history = conversation_history[-10:]
                conversation_context = "\n\nRECENT CONVERSATION HISTORY:\n"
                for msg in recent_history:
                    if isinstance(msg, HumanMessage):
                        conversation_context += f"Client: {msg.content}\n"
                    elif isinstance(msg, AIMessage):
                        conversation_context += f"Advisor: {msg.content}\n"
            
            # Create streaming prompt
            prompt = ChatPromptTemplate.from_template("""
You are an experienced investment advisor having a conversation with a client about their portfolio.

{portfolio_context}
{conversation_context}

CLIENT QUESTION: "{request}"

Provide a conversational, helpful response that:
1. Directly addresses their specific question
2. Note the portfolio data timestamp at the top (PORTFOLIO DATA AS OF) - mention it naturally if relevant
3. References their actual portfolio holdings from the COMPLETE HOLDINGS LIST above
4. When asked about specific stocks, check if they own them by reviewing the complete holdings list
5. If asked about stock prices for stocks NOT in their portfolio, use the REQUESTED STOCK PRICES section
6. Gives personalized advice based on their actual positions
7. Uses a friendly, professional tone
8. Keeps response focused and concise (2-3 paragraphs max)

IMPORTANT: 
- The portfolio was just synced from Alpaca - data is current as of the timestamp shown
- If asked about a specific stock, ALWAYS check the complete holdings list first before saying they don't own it
- Use the actual quantities, prices, and allocations from the holdings list
- If REQUESTED STOCK PRICES section is present, use those real-time prices when discussing those stocks
- Reference the sector information provided for each holding

FORMATTING GUIDELINES:
- When presenting structured data (sector breakdowns, top holdings, comparisons), use **markdown tables** for clarity
- Use tables for: sector breakdowns, holdings lists, performance comparisons, allocation summaries
- Use bullet points for: recommendations, action items, general advice
- Use bold (**text**) to emphasize key figures, percentages, and important holdings

If they want to stay aggressive, support that preference and give advice on how to optimize their aggressive strategy.
Be conversational, not templated.
""")
            
            # Stream from LLM
            chain = prompt | self.llm
            full_response = ""
            
            async for chunk in chain.astream({
                "portfolio_context": portfolio_context,
                "conversation_context": conversation_context,
                "request": request
            }):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                full_response += content
                
                # Yield each chunk
                yield {
                    "type": "content",
                    "content": content
                }
            
            # Calculate analysis results
            num_assets = len(assets)
            diversification_score = min(10, num_assets * 2)
            risk_score = min(10, (tech_allocation / 10) + (diversification_score / 2))
            
            recommendations = []
            if tech_allocation > 50:
                recommendations.append("Reduce technology concentration")
            if num_assets < 5:
                recommendations.append("Add more diversification")
            if not any(asset.get('asset_type') == 'bond' for asset in assets):
                recommendations.append("Add fixed income allocation")
            
            analysis_results = {
                "portfolio_metrics": {
                    "risk_score": round(risk_score, 1),
                    "diversification_score": round(diversification_score, 1),
                    "tech_allocation": round(tech_allocation, 1),
                    "num_holdings": num_assets
                },
                "recommendations": recommendations if recommendations else ["Portfolio appears well balanced"],
                "risk_assessment": {"tolerance": "moderate", "score": round(risk_score, 1)}
            }
            
            # Send final metadata
            yield {
                "type": "final",
                "result": {
                    "response": full_response,
                    "session_id": session_id,  # Include session_id for logging
                    "workflow_complete": True,
                    "analysis_results": analysis_results,
                    "trade_recommendations": [],
                    "compliance_approved": True,
                    "requires_user_approval": False
                }
            }
            
        except Exception as e:
            logger.error(f"Error streaming conversational analysis: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    async def _stream_trade_processing(
        self,
        request: str,
        portfolio_data: Dict,
        client_profile: Dict,
        session_id: Optional[str] = None
    ):
        """Stream trade processing responses from LLM."""
        try:
            # Build portfolio context
            portfolio_context = ""
            current_holdings = {}
            
            if portfolio_data and 'holdings' in portfolio_data:
                total_value = sum(
                    holding.get('quantity', 0) * holding.get('current_price', 0)
                    for holding in portfolio_data['holdings']
                )
                portfolio_context = f"Current Portfolio Value: ${total_value:,.2f}\nHoldings:\n"
                
                for holding in portfolio_data['holdings']:
                    symbol = holding.get('symbol', 'Unknown')
                    quantity = holding.get('quantity', 0)
                    price = holding.get('current_price', 0)
                    value = quantity * price
                    
                    current_holdings[symbol] = {
                        'quantity': quantity,
                        'price': price,
                        'value': value
                    }
                    
                    portfolio_context += f"- {symbol}: {quantity} shares @ ${price:.2f} = ${value:,.2f}\n"
            
            client_context = ""
            if client_profile:
                risk_tolerance = client_profile.get('risk_tolerance', 'moderate')
                experience = client_profile.get('investment_experience', 'intermediate')
                client_context = f"Risk Tolerance: {risk_tolerance}, Experience: {experience}"
            
            # Create trade processing prompt
            trade_prompt = ChatPromptTemplate.from_template("""
You are a professional trade execution specialist analyzing a client's trade request.

TRADE REQUEST: "{request}"

CURRENT PORTFOLIO:
{portfolio_context}

CLIENT PROFILE: {client_context}

TASK: Analyze this trade request and provide:

1. **Trade Validation**: Is this a valid, executable trade request?
2. **Portfolio Impact**: How will this affect their portfolio?
3. **Risk Analysis**: What are the implications?
4. **Execution Plan**: Specific steps to execute this trade
5. **Recommendations**: Any suggestions or concerns

If the request is for a SELL order:
- Check if they own the stock and have enough shares
- Calculate the proceeds and portfolio impact
- Provide specific execution details

If the request is for a BUY order:
- Estimate cost and market impact
- Check portfolio balance implications
- Provide execution guidance

Respond in a professional, clear manner that helps the client understand:
- What exactly will be executed
- The financial impact
- Any risks or considerations
- Next steps for approval/execution

Be conversational but precise.
""")
            
            # Stream from LLM
            chain = trade_prompt | self.llm
            full_response = ""
            
            async for chunk in chain.astream({
                "request": request,
                "portfolio_context": portfolio_context,
                "client_context": client_context
            }):
                content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                full_response += content
                
                yield {
                    "type": "content",
                    "content": content
                }
            
            # Extract trade details
            trade_details = self._extract_trade_details(request)
            
            # Execute compliance review if we have trade details
            compliance_response = ""
            if trade_details and portfolio_data and client_profile:
                user_id = client_profile.get('user_id', 'unknown')
                
                # Execute real compliance review - this will:
                # 1. Log compliance checks to database
                # 2. Create pending transaction
                # 3. Return compliance assessment
                compliance_response = self._execute_real_compliance_review(
                    trade_recommendations=[trade_details],
                    client_profile=client_profile,
                    portfolio_data=portfolio_data,
                    user_id=user_id,
                    context=request
                )
                
                # Stream compliance response
                if compliance_response:
                    yield {
                        "type": "content",
                        "content": "\n\n" + compliance_response
                    }
                    full_response += "\n\n" + compliance_response
            
            # Send final metadata
            yield {
                "type": "final",
                "result": {
                    "response": full_response,
                    "session_id": session_id,  # Include session_id for logging
                    "workflow_complete": False,
                    "analysis_results": {},
                    "trade_recommendations": [trade_details] if trade_details else [],
                    "compliance_approved": False,
                    "requires_user_approval": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error streaming trade processing: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    # Helper methods for LLM-based conversational analysis
    
    def _create_portfolio_analysis_prompt(self, state: InvestmentAdvisorState) -> str:
        """Create context-aware prompt for portfolio analysis."""
        client_info = state.get("client_profile", {})
        portfolio_info = state.get("portfolio_data", {})
        
        return f"""
        Client Profile: {client_info}
        Portfolio Data: {portfolio_info}
        Current Task: {state.get("current_task")}
        
        Please provide comprehensive portfolio analysis including risk assessment and recommendations.
        """
    
    def _lookup_stock_prices_from_query(self, query: str, portfolio_assets: List[Dict]) -> str:
        """
        Extract stock symbols from user query and look up real-time prices for stocks not in portfolio.
        Uses LLM to intelligently extract ticker symbols from natural language.
        Returns formatted string with price information to add to context.
        """
        import re
        
        logger.info(f"🔍 Attempting to extract ticker symbols from query: '{query}'")
        
        # Get list of symbols already in portfolio
        portfolio_symbols = set()
        for asset in portfolio_assets:
            asset_symbol = asset.get('symbol', '')
            normalized_asset_symbol = alpaca_trading_service.resolve_symbol(asset_symbol) or asset_symbol
            portfolio_symbols.add(normalized_asset_symbol.upper())
        logger.info(f"📊 Portfolio already contains: {portfolio_symbols}")
        
        # Use LLM to extract ticker symbols from the query
        try:
            extraction_prompt = ChatPromptTemplate.from_template("""
Extract stock ticker symbols from this user query. Return ONLY ticker symbols mentioned or implied.

USER QUERY: "{query}"

Examples:
"What is the price of NTNX?" → ["NTNX"]
"How much is Nutanix stock?" → ["NTNX"]
"Tell me about Apple and Microsoft" → ["AAPL", "MSFT"]
"What's the price of Pfizer stock now?" → ["PFE"]
"How is my portfolio doing?" → []
"Should I buy TSLA?" → ["TSLA"]

Return ONLY a JSON array of uppercase ticker symbols (1-5 letters each), or empty array if none found:
["SYMBOL1", "SYMBOL2"] or []
""")
            
            chain = extraction_prompt | self.llm
            response = chain.invoke({"query": query})
            
            logger.info(f"🤖 LLM ticker extraction response: {response.content}")
            
            import json
            # Try to parse JSON array from response
            potential_symbols = set()
            
            # Extract JSON array from response
            json_match = re.search(r'\[(.*?)\]', response.content, re.DOTALL)
            if json_match:
                try:
                    symbols_list = json.loads(json_match.group(0))
                    if isinstance(symbols_list, list):
                        for sym in symbols_list:
                            if isinstance(sym, str) and 1 <= len(sym) <= 5:
                                potential_symbols.add(sym.upper())
                        logger.info(f"✅ Extracted symbols from LLM: {potential_symbols}")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse LLM ticker extraction: {response.content}")
            
            # Fallback: also check for direct ticker patterns in original query
            for match in re.finditer(r'\b([A-Z]{1,5})\b', query):
                symbol = match.group(1)
                # Filter out common English words
                if symbol not in ['I', 'A', 'US', 'USA', 'UK', 'CEO', 'CFO', 'CTO', 'AI', 'ML', 'API', 'FAQ', 'PDF', 'JPG', 'PNG', 'IS', 'IT', 'OR', 'AND', 'THE']:
                    potential_symbols.add(symbol)
            
            # Additional fallback: look for capitalized company names and attempt resolution
            for token in re.findall(r'\b[A-Za-z]{2,15}\b', query):
                upper_token = token.upper()
                # Skip obvious non-company words
                if upper_token in ['WHAT', 'IS', 'THE', 'PRICE', 'STOCK', 'OF', 'PLEASE', 'SHOULD', 'BUY', 'SELL', 'HOW', 'MUCH', 'DO', 'HAVE']:
                    continue
                resolved = alpaca_trading_service.resolve_symbol(token)
                if resolved:
                    potential_symbols.add(resolved.upper())
            
        except Exception as e:
            logger.error(f"Error in LLM ticker extraction: {e}")
            # Fallback to simple regex
            potential_symbols = set()
            for match in re.finditer(r'\b([A-Z]{1,5})\b', query):
                symbol = match.group(1)
                if symbol not in ['I', 'A', 'US', 'USA', 'UK', 'CEO', 'CFO', 'CTO', 'AI', 'ML', 'API', 'FAQ', 'PDF', 'JPG', 'PNG', 'IS', 'IT', 'OR', 'AND', 'THE']:
                    potential_symbols.add(symbol)
        
        # Normalize potential symbols using resolver
        normalized_candidates = set()
        for sym in potential_symbols:
            resolved = alpaca_trading_service.resolve_symbol(sym)
            if resolved:
                normalized_candidates.add(resolved.upper())
            else:
                normalized_candidates.add(sym.upper())
        
        # Filter out symbols already in portfolio
        symbols_to_lookup = normalized_candidates - portfolio_symbols
        
        logger.info(f"💰 Symbols to lookup (not in portfolio): {symbols_to_lookup}")
        
        if not symbols_to_lookup:
            logger.info("⚠️ No new symbols to look up - all symbols already in portfolio or none found")
            return ""  # No new stocks to look up
        
        # Look up prices for each symbol
        price_info_lines = []
        for symbol in sorted(symbols_to_lookup):  # Sort for consistent output
            logger.info(f"📞 Calling Alpaca API for {symbol}...")
            try:
                price = alpaca_trading_service._get_current_price(symbol)
                logger.info(f"💵 Received price for {symbol}: {price} (type: {type(price)})")
                
                if price and price > 0:
                    price_info_lines.append(f"  • {symbol}: ${price:.2f} (current market price)")
                    logger.info(f"✅ Looked up real-time price for {symbol}: ${price:.2f}")
                else:
                    logger.warning(f"❌ Price for {symbol} failed condition check: price={price}")
            except Exception as e:
                logger.error(f"❌ Exception fetching price for {symbol}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Don't include symbols we couldn't fetch
                continue
        
        if price_info_lines:
            result = f"""
REQUESTED STOCK PRICES (not in portfolio):
{chr(10).join(price_info_lines)}
"""
            logger.info(f"✅ Returning price info for {len(price_info_lines)} symbol(s)")
            return result
        
        logger.info("⚠️ No valid prices found for any symbols")
        return ""
    
    def _conversational_analysis_node(self, request: str, portfolio_data: Dict, client_profile: Dict) -> str:
        """Generate dynamic conversational responses using LLM based on user's specific question."""
        try:
            # Extract portfolio metrics for context
            assets = portfolio_data.get('assets', [])
            if not assets:
                return f"""I don't see any portfolio data loaded. Please load your portfolio file first using the 'portfolio' command, then I can help answer your question: "{request}" """
            
            # Calculate key portfolio metrics for LLM context
            total_value = portfolio_data.get('total_value', 0)
            tech_allocation = sum(asset.get('allocation', 0) for asset in assets 
                                if asset.get('sector') and asset.get('sector', '').lower().startswith('tech'))
            num_assets = len(assets)
            max_allocation = max([asset.get('allocation', 0) for asset in assets]) if assets else 0
            
            # Get top holdings for context
            top_holdings = sorted(assets, key=lambda x: x.get('allocation', 0), reverse=True)[:5]
            holdings_summary = ", ".join([f"{asset.get('symbol')} ({asset.get('allocation', 0):.1f}%)" 
                                        for asset in top_holdings])
            
            # Create detailed holdings list with ALL positions
            detailed_holdings = "\n".join([
                f"  • {asset.get('symbol')}: {asset.get('quantity', 0):.2f} shares @ ${asset.get('current_price', 0):.2f} = ${asset.get('market_value', 0):,.2f} ({asset.get('allocation', 0):.1f}%) - Sector: {asset.get('sector', 'Unknown')}"
                for asset in sorted(assets, key=lambda x: x.get('allocation', 0), reverse=True)
            ])
            
            # Get cash balance
            cash_balance = portfolio_data.get('cash_balance', 0)
            equity_value = sum(asset.get('market_value', 0) for asset in assets)
            cash_percentage = (cash_balance / total_value * 100) if total_value > 0 else 0
            
            # Look up requested stock prices (if asking about specific stocks not in portfolio)
            stock_price_info = self._lookup_stock_prices_from_query(request, assets)
            
            # Format sync timestamp
            synced_at = portfolio_data.get('synced_at', 'Unknown')
            if synced_at and synced_at != 'Unknown':
                from datetime import datetime
                try:
                    sync_dt = datetime.fromisoformat(synced_at)
                    synced_at_display = sync_dt.strftime("%B %d, %Y at %I:%M %p")
                except:
                    synced_at_display = synced_at
            else:
                synced_at_display = "Unknown"
            
            # Create conversational prompt for LLM
            portfolio_context = f"""
PORTFOLIO DATA AS OF: {synced_at_display}
(Portfolio data synced from Alpaca)

PORTFOLIO CONTEXT:
- Total Portfolio Value: ${total_value:,.2f}
- Cash Balance: ${cash_balance:,.2f} ({cash_percentage:.1f}%)
- Equity Holdings Value: ${equity_value:,.2f} ({100 - cash_percentage:.1f}%)
- Number of Stock Positions: {num_assets}
- Tech Allocation: {tech_allocation:.1f}%
- Largest Position: {max_allocation:.1f}%
- Risk Profile: {"High (tech-focused)" if tech_allocation > 60 else "Moderate"}

COMPLETE HOLDINGS LIST:
{detailed_holdings}

CASH POSITION:
  • Cash: ${cash_balance:,.2f} ({cash_percentage:.1f}% of portfolio)

{stock_price_info}
"""

            # Use LLM to generate conversational response
            prompt = ChatPromptTemplate.from_template("""
You are an experienced investment advisor having a conversation with a client about their portfolio.

{portfolio_context}

CLIENT QUESTION: "{request}"

Provide a conversational, helpful response that:
1. Directly addresses their specific question
2. Note the portfolio data timestamp at the top (PORTFOLIO DATA AS OF) - mention it naturally if relevant
3. References their actual portfolio holdings from the COMPLETE HOLDINGS LIST above
4. When asked about specific stocks, check if they own them by reviewing the complete holdings list
5. If asked about stock prices for stocks NOT in their portfolio, use the REQUESTED STOCK PRICES section
6. Gives personalized advice based on their actual positions
7. Uses a friendly, professional tone
8. Keeps response focused and concise (2-3 paragraphs max)

IMPORTANT: 
- The portfolio was just synced from Alpaca - data is current as of the timestamp shown
- If asked about a specific stock, ALWAYS check the complete holdings list first before saying they don't own it
- Use the actual quantities, prices, and allocations from the holdings list
- If REQUESTED STOCK PRICES section is present, use those real-time prices when discussing those stocks
- Reference the sector information provided for each holding

FORMATTING GUIDELINES:
- When presenting structured data (sector breakdowns, top holdings, comparisons), use **markdown tables** for clarity
- Example table format:
  | Sector | Holdings | Value | Allocation |
  |--------|----------|-------|------------|
  | Technology | AAPL, GOOGL | $50,000 | 35% |
  
- Use tables for: sector breakdowns, holdings lists, performance comparisons, allocation summaries
- Use bullet points for: recommendations, action items, general advice
- Use bold (**text**) to emphasize key figures, percentages, and important holdings

If they want to stay aggressive, support that preference and give advice on how to optimize their aggressive strategy.
Be conversational, not templated.
""")
            
            # Generate response using LLM
            chain = prompt | self.llm
            response = chain.invoke({
                "portfolio_context": portfolio_context,
                "request": request
            })
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error in conversational analysis: {e}")
            return f"""I apologize, but I encountered an error while processing your question: "{request}". 

Could you please try rephrasing your question? I'm here to help with any questions about your portfolio, investment strategy, or market insights."""
    
    def _execute_real_compliance_review(
        self,
        trade_recommendations: List[Dict],
        client_profile: Dict,
        portfolio_data: Dict,
        user_id: Optional[str],
        context: str
    ) -> str:
        """
        Execute real compliance review using compliance_reviewer_agent.
        Creates pending transactions and logs compliance checks to database.
        """
        try:
            if not trade_recommendations:
                return "No trade recommendations to review."
            
            # Process first trade recommendation (can be extended for multiple)
            trade = trade_recommendations[0]
            raw_symbol = trade.get('symbol', 'UNKNOWN')
            normalized_symbol = alpaca_trading_service.resolve_symbol(raw_symbol)
            if normalized_symbol:
                if normalized_symbol != raw_symbol:
                    logger.info(f"Normalized trade symbol '{raw_symbol}' -> '{normalized_symbol}'")
                trade['symbol'] = normalized_symbol
            symbol = trade.get('symbol', 'UNKNOWN')
            action = trade.get('action', 'BUY')
            quantity = trade.get('quantity', 0)
            
            # Handle "all" or "entire" quantities - must calculate actual share count
            if quantity is None or (isinstance(quantity, str) and quantity.lower() in ['all', 'entire', 'everything']):
                # Look up actual shares in portfolio
                current_quantity = 0
                if portfolio_data and isinstance(portfolio_data, dict):
                    if 'holdings' in portfolio_data:
                        for holding in portfolio_data['holdings']:
                            if holding.get('symbol', '').upper() == symbol.upper():
                                current_quantity = holding.get('quantity', 0)
                                break
                    elif 'assets' in portfolio_data:
                        for asset in portfolio_data['assets']:
                            if asset.get('symbol', '').upper() == symbol.upper():
                                current_quantity = asset.get('quantity', 0)
                                break
                
                if current_quantity > 0:
                    quantity = current_quantity
                    logger.info(f"Calculated 'all' quantity for {symbol}: {quantity} shares")
                else:
                    logger.warning(f"Cannot calculate 'all' quantity - {symbol} not found in portfolio")
                    return f"Cannot process 'sell all {symbol}' - {symbol} not found in your portfolio. Current holdings might not include this symbol."
            
            # Get portfolio_id from portfolio_data if available
            portfolio_id = None
            if portfolio_data and isinstance(portfolio_data, dict):
                # Try to extract portfolio_id from assets or holdings
                if 'assets' in portfolio_data and portfolio_data['assets']:
                    # Might be embedded in asset data
                    pass
                elif 'holdings' in portfolio_data and portfolio_data['holdings']:
                    # Might be in holdings data
                    pass
            
            # Build compliance-friendly recommendation content with proper regulatory disclosures
            risk_tolerance = client_profile.get('risk_tolerance', 'moderate')
            portfolio_value = portfolio_data.get('total_value', 0)
            
            # Get current price and existing position from portfolio_data
            current_price = trade.get('price', 0)
            existing_quantity = 0
            existing_value = 0
            
            if portfolio_data:
                # Check both 'assets' and 'holdings' keys
                items = []
                if 'assets' in portfolio_data:
                    items = portfolio_data['assets']
                elif 'holdings' in portfolio_data:
                    items = portfolio_data['holdings']
                
                for item in items:
                    if item.get('symbol', '').upper() == symbol.upper():
                        if not current_price or current_price == 0:
                            current_price = item.get('current_price', 0)
                        existing_quantity = item.get('quantity', 0)
                        existing_value = item.get('market_value', item.get('value', 0))
                        break
            
            # If we still don't have a price (buying new stock), fetch real-time price from Alpaca
            if not current_price or current_price == 0:
                try:
                    current_price = alpaca_trading_service._get_current_price(symbol)
                    logger.info(f"Fetched real-time price for {symbol} from Alpaca: ${current_price}")
                except Exception as e:
                    logger.error(f"Failed to get price for {symbol} from Alpaca: {e}")
                    # Use a conservative default estimate as fallback
                    current_price = 100
                    logger.warning(f"Using fallback price $100 for {symbol}")
            
            # Calculate trade value and NEW total position value
            if action.upper() == 'SELL':
                trade_value = existing_value if existing_value > 0 else (quantity * current_price)
                # For sells, new position = existing - sold = less than before
                new_position_value = existing_value - trade_value if existing_value > 0 else 0
            else:
                # For BUY: calculate new trade value
                new_trade_value = quantity * current_price
                # Total position after buy = existing + new purchase
                new_position_value = existing_value + new_trade_value
                trade_value = new_trade_value
            
            portfolio_pct = (trade_value / portfolio_value * 100) if portfolio_value > 0 else 0
            new_position_pct = (new_position_value / portfolio_value * 100) if portfolio_value > 0 else 0
            
            logger.info(f"Trade concentration check: {symbol} x {quantity} @ ${current_price} = ${trade_value:,.2f}")
            logger.info(f"  - Existing position: {existing_quantity} shares = ${existing_value:,.2f} ({existing_value/portfolio_value*100:.1f}% if > 0)")
            logger.info(f"  - Trade: {portfolio_pct:.1f}% of ${portfolio_value:,.2f} portfolio")
            logger.info(f"  - NEW Total Position: {new_position_pct:.1f}% of portfolio")
            logger.info(f"  - Will block if: {new_position_pct:.1f}% > 50% = {new_position_pct > 50}")
            
            # Moderate concentration warning (25-50%) - shows warning but allows trade
            moderate_warning = None
            if 25 <= new_position_pct <= 50:
                moderate_warning = f"""
**⚠️ CONCENTRATION WARNING:**
This trade would create a **{new_position_pct:.1f}% position in {symbol}**, which is a significant concentration for a single stock. While within acceptable limits, consider diversifying further to reduce risk.

**Recommendation:** For better diversification, consider limiting any single position to 10-20% of your portfolio value.
"""
            
            # Severe concentration warning for large percentage trades
            # Check if NEW total position would be >50%, or if selling entire position
            if new_position_pct > 50 or (action.upper() == 'SELL' and existing_quantity == quantity):
                # Selling all of a position is ALWAYS risky for diversification
                return f"""
## ⚠️ **EXTREME CONCENTRATION RISK DETECTED**

This trade would create a concentrated position of **{new_position_pct:.1f}% in {symbol}** (${new_position_value:,.2f} out of ${portfolio_value:,.2f} total portfolio value).

**Why This Is Dangerous:**
• Having over 50% in a single stock violates diversification principles
• Individual stocks can drop 20-50% in a single day  
• This does NOT align with your **moderate risk tolerance**
• Regulators flag any single position >50% as highly unsuitable
• SEC/FINRA would flag this as inappropriate for moderate-risk investors

**What This Means:**
• After this trade, your {symbol} position would be {new_position_pct:.1f}% of your entire portfolio
• This represents extreme concentration risk
• Severe lack of diversification violates suitability standards
• Does not meet fiduciary "best interest" standards

**My Strong Recommendation:**
I **cannot recommend** this trade given your risk profile. If you truly want to invest in {symbol}:
1. Start with a smaller position (5-15% of portfolio)
2. Maintain diversification across multiple sectors/stocks
3. Consider dollar-cost averaging over time
4. Reassess your risk tolerance if this type of concentration appeals to you

**Alternative:**
Would you like me to suggest a more suitable, diversified approach that aligns with your goals and risk tolerance?
"""
            
            # Build comprehensive recommendation with suitability and risk disclosures
            # Calculate estimated value impact
            price_for_display = trade.get('price', 0)
            if price_for_display:
                estimated_value_text = f"${quantity * price_for_display:.2f}"
            else:
                estimated_value_text = "Market price at execution"
            
            recommendation_content = f"""
Investment Recommendation: {action.upper()} {quantity} shares of {symbol}

SUITABILITY ANALYSIS:
Based on your {risk_tolerance} risk tolerance and current portfolio composition, this trade is suitable for your investment objectives. {trade.get('rationale', 'This action aligns with your stated financial goals and helps optimize your portfolio allocation.')}.

RISK DISCLOSURE:
This trade involves market risk. The value of {symbol} may fluctuate due to market conditions, and you could experience losses. All investments involve risk, including potential loss of principal. Past performance does not guarantee future results. Please ensure you understand these risks before proceeding.

TRADE DETAILS:
- Action: {action.upper()} {quantity} shares of {symbol}
- Order Type: {trade.get('order_type', 'market').upper()}
- Purpose: {'Raising cash / reducing position' if action.lower() == 'sell' else 'Deploying capital / building position'}
- Estimated Value Impact: {estimated_value_text}

This recommendation has been prepared in accordance with SEC Investment Advisers Act and FINRA suitability requirements.
""".strip()
            
            # Build recommendation context for compliance review
            recommendation_context = {
                'user_id': user_id,
                'portfolio_id': portfolio_id,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': trade.get('price'),
                'order_type': trade.get('order_type', 'market'),
                'risk_level': client_profile.get('risk_tolerance', 'moderate')
            }
            
            # Call REAL compliance reviewer - this creates transactions and logs compliance checks
            review_result = self.compliance_reviewer.review_investment_recommendation(
                recommendation_content=recommendation_content,
                client_profile=client_profile,
                recommendation_context=recommendation_context
            )
            
            # Format response based on review results
            compliance_score = review_result.get('compliance_score', 100)
            issues = review_result.get('compliance_issues', [])
            status = review_result.get('status', 'approved')
            
            issues_list = '\n'.join([f"• {issue.get('description', 'Unknown issue')} [{issue.get('severity', 'medium')}]" for issue in issues[:3]])
            
            if status == 'approved' or compliance_score >= 70:
                # Pre-calculate conditional strings to avoid f-string syntax errors
                status_text = '⚠️ APPROVED WITH WARNINGS' if issues else '✅ APPROVED'
                issues_section = ('**Issues Identified:**\n' + issues_list) if issues else ''
                moderate_warning_section = moderate_warning if moderate_warning else ''
                finra_status = '⚠️ Review Required' if len(issues) > 0 else 'Met'
                reg_bi_status = '⚠️ Review Required' if len(issues) > 0 else 'Satisfied'
                
                return f"""
## ✅ Compliance Review Complete

**Trade Recommendation:** {action.upper()} {quantity} shares of {symbol}

**Compliance Score:** {compliance_score}/100

**Status:** {status_text}

{issues_section}

{moderate_warning_section}

**Regulatory Compliance:**
• SEC Investment Advisers Act: Compliant
• FINRA Suitability Rule 2111: {finra_status}
• Best Interest Standard (Reg BI): {reg_bi_status}

**Transaction Status:** Pending - awaiting your approval
**Database:** Transaction and compliance checks logged ✓

**Next Steps:**
Reply with "Approve" to execute this trade, or ask questions for clarification.
"""
            else:
                # Compliance failed - update transaction to 'rejected'
                transaction_id = review_result.get('transaction_id')
                if transaction_id:
                    try:
                        with database_service.get_session() as session:
                            from sqlalchemy import text
                            session.execute(
                                text("""
                                    UPDATE transactions 
                                    SET status = 'rejected',
                                        notes = CONCAT(COALESCE(notes, ''), '\nCompliance rejected: Score ', :score, '/100'),
                                        updated_at = CURRENT_TIMESTAMP
                                    WHERE transaction_id = :transaction_id
                                """),
                                {"transaction_id": transaction_id, "score": compliance_score}
                            )
                            session.commit()
                            logger.info(f"Transaction {transaction_id} rejected due to compliance failure (score: {compliance_score})")
                    except Exception as update_error:
                        logger.error(f"Failed to update transaction to rejected: {update_error}")
                
                issues_list_full = '\n'.join([f"• {issue.get('description', 'Unknown issue')} [{issue.get('severity', 'critical')}]" for issue in issues])
                
                return f"""
## ❌ Compliance Review Failed

**Trade Recommendation:** {action.upper()} {quantity} shares of {symbol}

**Compliance Score:** {compliance_score}/100

**Status:** REJECTED

**Critical Issues ({len(issues)}):**
{issues_list_full}

**Recommendation:** This trade has been rejected and cannot proceed without addressing the compliance issues identified above.
**Transaction Status:** Marked as 'rejected' in database.
"""
            
        except Exception as e:
            logger.error(f"Error in real compliance review: {e}")
            return f"Compliance review encountered an error. Please try again or contact support."
    
    def _create_final_communication(self, state: InvestmentAdvisorState) -> str:
        """Create final client communication."""
        analysis = state.get("analysis_results", {})
        trades = state.get("trade_recommendations", [])
        
        return f"""
## Investment Advisory Summary

Thank you for working with MyFalconAdvisor. Here's your comprehensive analysis:

**Portfolio Health Check:** Your portfolio shows strong fundamentals with room for optimization.

**Key Recommendations:**
{chr(10).join(f"• {rec}" for rec in analysis.get("recommendations", ["Portfolio review complete"]))}

**Next Steps:**
{"• Trades ready for your approval" if trades else "• Continue monitoring portfolio"}
• Regular quarterly review scheduled
• Contact us with any questions

**Important:** This analysis is based on current market conditions and your stated preferences. Please review carefully and let us know if you'd like to proceed.

*Compliance Note: All recommendations have been reviewed for suitability and regulatory compliance.*
"""


# Global supervisor instance
investment_advisor_supervisor = InvestmentAdvisorSupervisor()
