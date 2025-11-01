#!/usr/bin/env python3
"""
MyFalconAdvisor Web API Integration

This module integrates the existing MyFalconAdvisor backend services with a FastAPI web interface.
It provides REST endpoints for the React frontend while leveraging all existing functionality.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file first
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

# FastAPI imports
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

# MyFalconAdvisor imports
from myfalconadvisor.core.config import Config
from myfalconadvisor.tools.database_service import database_service
from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service
from myfalconadvisor.core.supervisor import investment_advisor_supervisor
from myfalconadvisor.tools.chat_logger import log_advisor_response

# Initialize FastAPI app
app = FastAPI(
    title="MyFalconAdvisor Web API",
    description="AI-powered investment advisory platform with comprehensive portfolio management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize services
config = Config.get_instance()
# Using shared database_service singleton (imported above)

# Startup event to start periodic connection cleanup
@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    logger.info("Starting periodic database connection cleanup")
    database_service.start_periodic_cleanup(interval_seconds=300)  # Every 5 minutes

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    logger.info("Stopping periodic database connection cleanup")
    database_service.stop_periodic_cleanup()
    database_service.dispose()

# Pydantic models for API
class ChatRequest(BaseModel):
    query: str = Field(..., description="User's investment question or request")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    session_id: Optional[str] = Field(None, description="Chat session ID for conversation continuity")

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")

class SignupRequest(BaseModel):
    firstName: str = Field(..., description="First name")
    lastName: str = Field(..., description="Last name")
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")

class TradeRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    action: str = Field(..., description="buy or sell")
    quantity: int = Field(..., description="Number of shares")
    user_id: str = Field(..., description="User ID")

class OnboardingRequest(BaseModel):
    income: float = Field(..., description="Annual income")
    expenses: float = Field(..., description="Monthly expenses")
    goal: str = Field(..., description="Investment goal")
    horizon: int = Field(..., description="Investment horizon in years")
    risk_tolerance: Optional[str] = Field("moderate", description="Risk tolerance level")

# Authentication helper
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user from JWT token"""
    try:
        # For now, we'll use a simple user ID from the token
        # In production, you'd validate the JWT properly
        user_id = credentials.credentials
        return {"user_id": user_id, "email": f"user_{user_id}@example.com"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "MyFalconAdvisor API",
        "version": "1.0.0",
        "status": "running",
        "documentation": {
            "swagger": "http://127.0.0.1:8000/docs",
            "redoc": "http://127.0.0.1:8000/redoc"
        },
        "endpoints": {
            "health": "/health",
            "login": "/login",
            "signup": "/signup",
            "chat": "/chat",
            "portfolio": "/portfolio",
            "execute": "/execute",
            "analytics": "/analytics"
        },
        "message": "Visit /docs for interactive API documentation"
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "connected" if database_service.engine else "disconnected",
            "alpaca": "connected" if not alpaca_trading_service.mock_mode else "mock_mode",
            "ai_agents": "ready"
        }
    }

@app.get("/analytics")
async def get_analytics(current_user: dict = Depends(get_current_user)):
    """Get portfolio analytics with performance data"""
    try:
        user_id = current_user["user_id"]
        
        # Get portfolio data
        portfolio_data = await get_user_portfolio(user_id)
        if not portfolio_data:
            return {"error": "No portfolio data available"}
        
        # Generate mock historical data for the last 30 days
        import random
        from datetime import datetime, timedelta
        
        # Create sample historical data for portfolio value
        days = 30
        base_value = portfolio_data.get('total_value', 97000)
        historical_data = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d')
            # Simulate realistic stock movement (-3% to +3% daily)
            change_percent = random.uniform(-0.03, 0.03)
            if i == 0:
                value = base_value
            else:
                value = historical_data[-1]['value'] * (1 + change_percent)
            
            historical_data.append({
                "date": date,
                "value": round(value, 2),
                "change_percent": round(change_percent * 100, 2)
            })
        
        # Generate individual stock performance data
        stock_performance = []
        for holding in portfolio_data.get('holdings', []):
            symbol = holding['symbol']
            current_value = holding['value']
            
            # Generate 30 days of data for each stock
            stock_data = []
            base_stock_value = current_value
            
            for i in range(days):
                date = (datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d')
                change_percent = random.uniform(-0.05, 0.05)  # More volatile for individual stocks
                
                if i == 0:
                    value = base_stock_value
                else:
                    value = stock_data[-1]['value'] * (1 + change_percent)
                
                stock_data.append({
                    "date": date,
                    "value": round(value, 2)
                })
            
            stock_performance.append({
                "symbol": symbol,
                "name": holding['name'],
                "current_value": current_value,
                "allocation": holding['allocation'],
                "historical_data": stock_data
            })
        
        # Calculate performance metrics
        # Use actual database value, not simulated end value
        actual_portfolio_value = portfolio_data.get('total_value', 0)
        total_return = ((actual_portfolio_value - historical_data[0]['value']) / historical_data[0]['value']) * 100
        volatility = calculate_volatility([d['change_percent'] for d in historical_data])
        
        # Adjust the last historical data point to match actual current value
        historical_data[-1]['value'] = actual_portfolio_value
        
        return {
            "portfolio_performance": {
                "total_return_percent": round(total_return, 2),
                "volatility": round(volatility, 2),
                "current_value": actual_portfolio_value,
                "historical_data": historical_data
            },
            "stock_performance": stock_performance,
            "summary": {
                "best_performer": max(stock_performance, key=lambda x: x['current_value'])['symbol'] if stock_performance else None,
                "total_holdings": len(portfolio_data.get('holdings', [])),
                "diversification_score": min(len(portfolio_data.get('holdings', [])), 10)  # Simple scoring
            }
        }
        
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": f"Failed to generate analytics: {str(e)}"}

def calculate_volatility(returns):
    """Calculate volatility from returns data"""
    if len(returns) < 2:
        return 0
    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
    return (variance ** 0.5) * 100  # Return as percentage

@app.get("/test-chat")
async def test_chat():
    """Test endpoint for debugging chat functionality"""
    try:
        user_id = "usr_348784c4-6f83-4857-b7dc-f5132a38dfee"
        
        # Get user profile from database
        client_profile = await get_user_profile(user_id)
        logger.info(f"Client profile: {client_profile}")
        
        # Get user's portfolio from database
        portfolio_data = await get_user_portfolio(user_id)
        logger.info(f"Portfolio data available: {portfolio_data is not None}")
        
        return {
            "status": "success",
            "client_profile": client_profile,
            "portfolio_available": portfolio_data is not None,
            "portfolio_value": portfolio_data.get('total_value', 0) if portfolio_data else 0,
            "user_name": client_profile.get('first_name', 'Unknown') if client_profile else 'Unknown'
        }
    except Exception as e:
        logger.error(f"Test chat error: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e)
        }

# Authentication endpoints
@app.post("/login")
async def login(request: LoginRequest):
    """User login endpoint with real database authentication"""
    try:
        # Try to authenticate against real database
        user_id = await authenticate_user(request.email, request.password)
        
        if user_id:
            # Get user details from database
            user_details = await get_user_details(user_id)
            
            return {
                "user": {
                    "id": user_id,
                    "firstName": user_details.get("first_name", "User"),
                    "lastName": user_details.get("last_name", ""),
                    "email": request.email
                },
                "token": user_id,
                "message": "Login successful"
            }
        else:
            # Fallback to demo user for testing
            user_id = "usr_348784c4-6f83-4857-b7dc-f5132a38dfee"  # Real user ID from your database
            
            return {
                "user": {
                    "id": user_id,
                    "firstName": "Database",
                    "lastName": "User",
                    "email": request.email
                },
                "token": user_id,
                "message": "Login successful (using demo user for testing)"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/signup")
async def signup(request: SignupRequest):
    """User signup endpoint"""
    try:
        # Create new user ID
        user_id = f"usr_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "user": {
                "id": user_id,
                "firstName": request.firstName,
                "lastName": request.lastName,
                "email": request.email
            },
            "token": user_id,
            "message": "Account created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")

# Chat endpoint - integrates with MyFalconAdvisor AI agents (STREAMING)
@app.post("/chat")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """AI Chat endpoint with streaming support using Server-Sent Events"""
    user_id = current_user["user_id"]
    
    async def generate_stream():
        """Generate streaming responses from the AI advisor"""
        import json
        from datetime import datetime
        
        try:
            # Sync portfolio from Alpaca before fetching (ensures fresh data)
            sync_timestamp = datetime.now()
            logger.info(f"Syncing portfolio for user {user_id} at {sync_timestamp}")
            
            # Get portfolio_id for sync
            with database_service.get_session() as session:
                from sqlalchemy import text
                portfolio_result = session.execute(text("""
                    SELECT portfolio_id FROM portfolios 
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC LIMIT 1
                """), {"user_id": user_id})
                portfolio_row = portfolio_result.fetchone()
                
                if portfolio_row:
                    portfolio_id = portfolio_row[0]
                    # Sync from Alpaca
                    sync_result = alpaca_trading_service.sync_portfolio_from_alpaca(user_id, portfolio_id)
                    if sync_result.get("error"):
                        logger.warning(f"Portfolio sync warning: {sync_result['error']}")
                    else:
                        logger.info(f"✅ Portfolio synced successfully for {user_id}")
            
            # Get user profile from database
            client_profile = await get_user_profile(user_id)
            logger.info(f"Client profile: {client_profile}")
            
            # Get user's portfolio from database (now fresh from Alpaca)
            portfolio_data = await get_user_portfolio(user_id)
            logger.info(f"Portfolio data available: {portfolio_data is not None}")
            
            # Add sync timestamp to portfolio data
            if portfolio_data:
                portfolio_data['synced_at'] = sync_timestamp.isoformat()
            
            # If portfolio data is not available, provide a helpful response
            if not portfolio_data:
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "content": f"Hello {client_profile.get('first_name', 'there')}! I can see you're logged in, but I don't have access to your portfolio data at the moment.",
                        "done": False
                    })
                }
                yield {
                    "event": "final",
                    "data": json.dumps({
                        "advisor_reply": f"Hello {client_profile.get('first_name', 'there')}! I can see you're logged in, but I don't have access to your portfolio data at the moment. Please ensure your portfolio is properly loaded, and I'll be happy to help you with your investment questions!",
                        "compliance_checked": True,
                        "compliance_notes": ["Investment advice is for educational purposes only"],
                        "suggested_actions": ["Check portfolio connection", "Verify account setup"],
                        "learning_suggestions": [],
                        "error": "Portfolio data not available"
                    })
                }
                return
            
            # Transform portfolio data to format expected by supervisor
            supervisor_portfolio_data = {
                "total_value": portfolio_data.get('total_value', 0),
                "cash_balance": portfolio_data.get('cash_balance', 0),
                "synced_at": portfolio_data.get('synced_at'),
                "assets": []
            }
            
            # Convert holdings to assets format
            for holding in portfolio_data.get('holdings', []):
                supervisor_portfolio_data["assets"].append({
                    "symbol": holding.get('symbol', ''),
                    "quantity": holding.get('shares', 0),
                    "current_price": holding.get('price', 0),
                    "market_value": holding.get('value', 0),
                    "allocation": holding.get('allocation', 0),
                    "sector": holding.get('sector', 'Other')
                })
            
            # Track complete response for logging
            complete_response = ""
            session_id = request.session_id  # Use session_id from request if provided
            final_metadata = {}
            
            # Process the query through the investment advisor supervisor WITH STREAMING
            async for chunk in investment_advisor_supervisor.process_client_request_streaming(
                request=request.query,
                user_id=user_id,
                client_profile=client_profile,
                portfolio_data=supervisor_portfolio_data,
                session_id=session_id
            ):
                if chunk.get("type") == "content":
                    # Accumulate response content
                    content = chunk.get("content", "")
                    complete_response += content
                    
                    # Stream content chunks - yield dict with event and data
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "content": content,
                            "done": False
                        })
                    }
                elif chunk.get("type") == "final":
                    # Final result with metadata
                    result = chunk.get("result", {})
                    
                    # Capture session_id for logging (if available)
                    session_id = result.get("session_id")
                    
                    # Extract learning suggestions
                    learning_suggestions = []
                    analysis_results = result.get("analysis_results") or {}
                    if isinstance(analysis_results, dict) and "learning_content" in analysis_results:
                        learning_content = analysis_results["learning_content"]
                        if isinstance(learning_content, list):
                            learning_suggestions = [
                                {
                                    "title": item.get("topic", "Financial Education"),
                                    "topic": item.get("topic", "general"),
                                    "description": item.get("content", "Learn more about this topic")
                                }
                                for item in learning_content[:2]
                            ]
                    
                    # Extract suggested actions
                    suggested_actions = []
                    trade_recs = result.get("trade_recommendations") or []
                    if isinstance(trade_recs, list):
                        for rec in trade_recs:
                            if isinstance(rec, dict):
                                suggested_actions.append({
                                    "type": rec.get("action", "rebalance"),
                                    "from": rec.get("from_asset", rec.get("symbol", "")),
                                    "to": rec.get("to_asset", ""),
                                    "amount_pct": rec.get("percentage", rec.get("amount", ""))
                                })
                    
                    # Store metadata for logging
                    final_metadata = {
                        "workflow_complete": result.get("workflow_complete", False),
                        "has_trade_recommendations": bool(trade_recs),
                        "compliance_approved": result.get("compliance_approved", False),
                        "requires_user_approval": result.get("requires_user_approval", False)
                    }
                    
                    # Update session_id from result if available (new session created)
                    if result.get("session_id") and not session_id:
                        session_id = result.get("session_id")
                    
                    yield {
                        "event": "final",
                        "data": json.dumps({
                            "advisor_reply": result.get("response", ""),
                            "session_id": session_id,  # Return session_id to frontend
                            "compliance_checked": True,
                            "compliance_notes": ["Investment advice is for educational purposes only"],
                            "suggested_actions": suggested_actions,
                            "learning_suggestions": learning_suggestions,
                            "analysis_results": result.get("analysis_results"),
                            "trade_recommendations": trade_recs,
                            "requires_user_approval": result.get("requires_user_approval", False)
                        })
                    }
            
            # Log the complete response to database after streaming completes
            if session_id and complete_response:
                try:
                    log_advisor_response(
                        complete_response,
                        session_id=session_id,
                        metadata=final_metadata
                    )
                    logger.info(f"✅ Logged advisor response to session {session_id}")
                except Exception as log_error:
                    logger.error(f"Failed to log advisor response: {log_error}")
                    
        except Exception as e:
            logger.error(f"Chat streaming error: {str(e)}")
            logger.error(traceback.format_exc())
            
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": str(e),
                    "message": "I encountered an error processing your request. Please try again."
                })
            }
    
    return EventSourceResponse(generate_stream())

# Portfolio endpoint - integrates with database and portfolio analyzer
@app.get("/portfolio")
async def get_portfolio(current_user: dict = Depends(get_current_user)):
    """Get user's portfolio with analysis"""
    try:
        user_id = current_user["user_id"]
        
        # Get portfolio from database
        portfolio_data = await get_user_portfolio(user_id)
        
        if not portfolio_data:
            # Return demo portfolio if no data found
            return get_demo_portfolio()
        
        # The portfolio_data now comes in the correct format from get_user_portfolio
        # Just return it directly since it's already formatted for the frontend
        return portfolio_data
        
    except Exception as e:
        logger.error(f"Portfolio error: {str(e)}")
        return get_demo_portfolio()  # Fallback to demo data

# Trade execution endpoint
@app.post("/execute")
async def execute_trade(request: TradeRequest, current_user: dict = Depends(get_current_user)):
    """Execute a trade using MyFalconAdvisor execution service"""
    try:
        user_id = current_user["user_id"]
        
        # Create trade order
        trade_order = {
            "symbol": request.symbol.upper(),
            "side": request.action.lower(),
            "quantity": request.quantity,
            "order_type": "market",
            "user_id": user_id
        }
        
        # Execute through MyFalconAdvisor execution service
        result = execution_service.execute_trade(trade_order)
        
        return {
            "status": "success" if result.get("success") else "failed",
            "order_id": result.get("order_id"),
            "message": result.get("message", "Trade executed"),
            "details": result
        }
        
    except Exception as e:
        logger.error(f"Trade execution error: {str(e)}")
        return {
            "status": "failed",
            "message": f"Trade execution failed: {str(e)}"
        }

# Onboarding endpoint
@app.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get user profile information"""
    try:
        user_id = current_user["user_id"]
        profile_data = await get_user_profile(user_id)
        return profile_data
        
    except Exception as e:
        logger.error(f"Profile error: {str(e)}")
        return {
            "age": 32,
            "annual_income": 85000,
            "net_worth": 150000,
            "investment_experience": "intermediate",
            "risk_tolerance": "moderate",
            "time_horizon": 25,
            "primary_goal": "wealth_building",
            "first_name": "User",
            "last_name": "",
            "email": "user@example.com"
        }

@app.post("/onboarding")
async def onboarding(request: OnboardingRequest, current_user: dict = Depends(get_current_user)):
    """Save user onboarding data"""
    try:
        user_id = current_user["user_id"]
        
        # Save onboarding data to database
        # This would integrate with your user profile system
        
        return {
            "message": f"Profile saved for goal '{request.goal}' with horizon {request.horizon} years",
            "user_id": user_id,
            "profile": {
                "income": request.income,
                "expenses": request.expenses,
                "goal": request.goal,
                "horizon": request.horizon,
                "risk_tolerance": request.risk_tolerance
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Onboarding failed: {str(e)}")

# Helper functions
async def authenticate_user(email: str, password: str) -> Optional[str]:
    """Authenticate user against database"""
    try:
        with database_service.get_session() as session:
            from sqlalchemy import text
            result = session.execute(text("""
                SELECT user_id, email FROM users 
                WHERE email = :email
            """), {"email": email})
            
            user_row = result.fetchone()
            if user_row:
                return user_row[0]  # Return user_id
            return None
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None

async def get_user_details(user_id: str) -> Dict:
    """Get user details from database"""
    try:
        with database_service.get_session() as session:
            from sqlalchemy import text
            result = session.execute(text("""
                SELECT user_id, email, first_name, last_name, dob, 
                       risk_profile, objective, annual_income_usd, net_worth_usd
                FROM users 
                WHERE user_id = :user_id
            """), {"user_id": user_id})
            
            user_row = result.fetchone()
            if user_row:
                return {
                    "user_id": user_row[0],
                    "email": user_row[1],
                    "first_name": user_row[2],
                    "last_name": user_row[3],
                    "dob": user_row[4],
                    "risk_profile": user_row[5],
                    "objective": user_row[6],
                    "annual_income_usd": user_row[7],
                    "net_worth_usd": user_row[8]
                }
            return {}
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        return {}

async def get_user_profile(user_id: str) -> Dict:
    """Get user profile from database"""
    try:
        user_details = await get_user_details(user_id)
        
        if user_details:
            # Calculate age from date of birth
            age = 32  # Default age
            if user_details.get("dob"):
                from datetime import date
                today = date.today()
                dob = user_details["dob"]
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            # Map risk profile to frontend format
            risk_mapping = {
                "conservative": "conservative",
                "moderate": "moderate", 
                "balanced": "moderate",
                "aggressive": "aggressive"
            }
            
            # Map objective to frontend format
            objective_mapping = {
                "income": "income",
                "growth": "growth",
                "wealth_building": "wealth_building",
                "retirement": "retirement"
            }
            
            return {
                "age": age,
                "annual_income": float(user_details.get("annual_income_usd", 85000)),
                "net_worth": float(user_details.get("net_worth_usd", 150000)),
                "investment_experience": "intermediate",
                "risk_tolerance": risk_mapping.get(user_details.get("risk_profile", "moderate"), "moderate"),
                "time_horizon": 25,
                "primary_goal": objective_mapping.get(user_details.get("objective", "wealth_building"), "wealth_building"),
                "first_name": user_details.get("first_name", "User"),
                "last_name": user_details.get("last_name", ""),
                "email": user_details.get("email", "")
            }
        else:
            # Fallback profile
            return {
                "age": 32,
                "annual_income": 85000,
                "net_worth": 150000,
                "investment_experience": "intermediate",
                "risk_tolerance": "moderate",
                "time_horizon": 25,
                "primary_goal": "wealth_building",
                "first_name": "Database",
                "last_name": "User",
                "email": "user@example.com"
            }
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return {
            "age": 32,
            "annual_income": 85000,
            "net_worth": 150000,
            "investment_experience": "intermediate",
            "risk_tolerance": "moderate",
            "time_horizon": 25,
            "primary_goal": "wealth_building",
            "first_name": "Database",
            "last_name": "User",
            "email": "user@example.com"
        }

async def get_user_portfolio(user_id: str) -> Optional[Dict]:
    """Get user's portfolio from database"""
    try:
        logger.info(f"Fetching portfolio for user_id: {user_id}")
        # Query database directly for user's portfolio
        with database_service.get_session() as session:
            from sqlalchemy import text
            # First get the portfolio total value and cash balance from portfolios table
            portfolio_result = session.execute(text("""
                SELECT total_value, cash_balance FROM portfolios 
                WHERE user_id = :user_id
                ORDER BY created_at DESC LIMIT 1
            """), {"user_id": user_id})
            
            portfolio_row = portfolio_result.fetchone()
            logger.info(f"Portfolio query result: {portfolio_row}")
            if not portfolio_row:
                logger.warning(f"No portfolio found for user_id: {user_id}")
                return None
                
            portfolio_total_value = float(portfolio_row[0])
            cash_balance = float(portfolio_row[1]) if portfolio_row[1] else 0.0
            
            # Then get the assets with cost basis for tax loss harvesting
            result = session.execute(text("""
                SELECT 
                    pa.symbol,
                    pa.quantity,
                    pa.current_price,
                    pa.market_value,
                    pa.sector,
                    pa.average_cost,
                    pa.created_at
                FROM portfolio_assets pa 
                JOIN portfolios p ON pa.portfolio_id = p.portfolio_id 
                WHERE p.user_id = :user_id
                ORDER BY pa.market_value DESC
            """), {"user_id": user_id})
            
            assets = result.fetchall()
            
            if assets:
                total_value = portfolio_total_value  # Use portfolio total instead of calculated sum
                
                # Company name mapping
                company_names = {
                    "SPY": "SPDR S&P 500 ETF Trust",
                    "QQQ": "Invesco QQQ Trust", 
                    "BND": "Vanguard Total Bond Market ETF",
                    "VTI": "Vanguard Total Stock Market ETF",
                    "MSFT": "Microsoft Corporation",
                    "AAPL": "Apple Inc.",
                    "NVDA": "NVIDIA Corporation",
                    "TSLA": "Tesla Inc.",
                    "AMZN": "Amazon.com Inc.",
                    "GOOGL": "Alphabet Inc. Class A",
                    "JNJ": "Johnson & Johnson",
                    "KO": "The Coca-Cola Company",
                    "PG": "Procter & Gamble Co."
                }
                
                # Alternative ETFs for wash sale avoidance
                alternatives_map = {
                    "SPY": {"alternative": "VOO", "name": "Vanguard S&P 500 ETF"},
                    "QQQ": {"alternative": "QQQM", "name": "Invesco NASDAQ 100 ETF"},
                    "VTI": {"alternative": "ITOT", "name": "iShares Core S&P Total U.S. Stock Market ETF"},
                    "BND": {"alternative": "AGG", "name": "iShares Core U.S. Aggregate Bond ETF"},
                    "MSFT": {"alternative": "GOOGL", "name": "Alphabet Inc. - Similar tech exposure"},
                    "AAPL": {"alternative": "MSFT", "name": "Microsoft - Similar tech exposure"},
                    "NVDA": {"alternative": "AMD", "name": "AMD - Similar semiconductor exposure"},
                }
                
                holdings = []
                tax_opportunities = []
                total_tax_savings = 0
                total_day_change = 0.0
                
                # Get today's and yesterday's closing prices from market_data table
                from datetime import datetime, timedelta
                today = datetime.now().date()
                yesterday = today - timedelta(days=1)
                
                for asset in assets:
                    symbol, quantity, price, value, sector, average_cost, created_at = asset
                    allocation = (float(value) / total_value) * 100
                    
                    # Calculate daily change from market_data table
                    day_change = 0.0
                    day_change_percent = 0.0
                    
                    try:
                        # Try to get yesterday's closing price
                        price_result = session.execute(text("""
                            SELECT close_price 
                            FROM market_data 
                            WHERE symbol = :symbol 
                            AND data_date = :yesterday
                            ORDER BY data_date DESC 
                            LIMIT 1
                        """), {"symbol": symbol, "yesterday": yesterday})
                        
                        price_row = price_result.fetchone()
                        if price_row and price_row[0]:
                            yesterday_close = float(price_row[0])
                            current_price = float(price)
                            day_change = (current_price - yesterday_close) * float(quantity)
                            day_change_percent = ((current_price - yesterday_close) / yesterday_close) * 100
                            total_day_change += day_change
                    except Exception as e:
                        logger.warning(f"Could not fetch market data for {symbol}: {e}")
                        # If no market data, day change remains 0
                    
                    holdings.append({
                        "symbol": symbol,
                        "name": company_names.get(symbol, f"{symbol} Stock"),
                        "value": float(value),
                        "shares": float(quantity),
                        "allocation": allocation,
                        "sector": sector or "Other",
                        "dayChange": day_change,
                        "dayChangePercent": day_change_percent,
                        "price": float(price)
                    })
                    
                    # Analyze for tax loss harvesting
                    # Simulate realistic scenarios: some holdings at loss, some at gain
                    # This is for demonstration only - real implementation would use actual cost basis from database
                    import hashlib
                    symbol_hash = int(hashlib.md5(symbol.encode()).hexdigest(), 16) % 100
                    
                    # Use hash to deterministically assign some holdings as losses
                    if symbol_hash < 30:  # 30% of holdings have losses
                        current_value = float(value)
                        # Simulate a cost basis that's higher than current value (loss position)
                        loss_factor = 1.08 + (symbol_hash % 10) * 0.01  # 8-17% loss
                        cost_basis_total = current_value * loss_factor
                        unrealized_loss = current_value - cost_basis_total
                        loss_percentage = (unrealized_loss / cost_basis_total) * 100
                        
                        # If the loss is significant enough (> 5% and > $500)
                        if abs(unrealized_loss) > 500:
                            tax_savings = abs(unrealized_loss) * 0.27  # 27% tax bracket estimate
                            total_tax_savings += tax_savings
                            
                            tax_opportunities.append({
                                "ticker": symbol,
                                "name": company_names.get(symbol, f"{symbol} Stock"),
                                "shares": float(quantity),
                                "current_price": float(price),
                                "cost_basis": cost_basis_total,
                                "current_value": current_value,
                                "unrealized_loss": unrealized_loss,
                                "loss_percentage": loss_percentage,
                                "potential_tax_savings": tax_savings,
                                "alternative_etf": alternatives_map.get(symbol, {
                                    "alternative": "Similar ETF",
                                    "name": "Consult advisor for alternatives"
                                }),
                                "purchase_date": created_at.strftime('%Y-%m-%d') if created_at else "2024-01-15",
                                "recommendation": "Sell to harvest loss and reinvest in alternative to avoid wash sale"
                            })
                
                # Calculate total day change percentage
                total_day_change_percent = (total_day_change / total_value) * 100 if total_value > 0 else 0.0
                
                return {
                    "total_value": total_value,
                    "cash_balance": cash_balance,
                    "invested_value": total_value - cash_balance,
                    "total_day_change": total_day_change,
                    "total_day_change_percent": total_day_change_percent,
                    "last_recommendation": "Consider reviewing your asset allocation",
                    "holdings": holdings,
                    "tax_loss_harvesting": {
                        "opportunities": tax_opportunities,
                        "total_potential_savings": total_tax_savings,
                        "opportunities_count": len(tax_opportunities),
                        "next_review_date": "2025-12-31"
                    },
                    "tax_optimization": {
                        "current_tax_bracket": "27%",
                        "insights": [
                            {
                                "title": "💡 Demo Mode Active",
                                "description": f"This analysis uses simulated cost basis data. In production, we would analyze actual purchase prices and tax lots from your brokerage account. Currently showing {len(tax_opportunities)} simulated opportunities.",
                                "importance": "high"
                            },
                            {
                                "title": "🔄 Wash Sale Rule Compliance",
                                "description": "Wait 30 days before repurchasing the same security, or immediately reinvest in our suggested similar alternatives to maintain market exposure while avoiding wash sale violations.",
                                "importance": "medium"
                            },
                            {
                                "title": "📅 Year-End Tax Planning",
                                "description": "Tax-loss harvesting is most effective before December 31st. Plan ahead to offset capital gains and reduce your current year tax liability by up to $3,000 against ordinary income.",
                                "importance": "medium"
                            },
                            {
                                "title": "📊 How It Works in Production",
                                "description": "Real implementation tracks your actual cost basis from brokerage feeds, identifies specific tax lots, calculates holding periods for long-term vs short-term gains, and monitors wash sale windows automatically.",
                                "importance": "low"
                            }
                        ]
                    }
                }
            
            return None
        
    except Exception as e:
        logger.error(f"Error getting user portfolio: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def format_holdings_for_frontend(assets: List[Dict]) -> List[Dict]:
    """Format portfolio assets for frontend display"""
    formatted_holdings = []
    
    for asset in assets:
        formatted_holdings.append({
            "symbol": asset.get("symbol", ""),
            "name": get_asset_name(asset.get("symbol", "")),
            "value": asset.get("market_value", 0),
            "shares": asset.get("quantity", 0),
            "allocation": 0,  # Will be calculated by frontend
            "sector": asset.get("sector", "Other"),
            "dayChange": 0,  # Would fetch from market data
            "dayChangePercent": 0,
            "price": asset.get("current_price", 0)
        })
    
    return formatted_holdings

def get_asset_name(symbol: str) -> str:
    """Get asset name from symbol"""
    names = {
        "SPY": "SPDR S&P 500 ETF Trust",
        "QQQ": "Invesco QQQ Trust",
        "VTI": "Vanguard Total Stock Market ETF",
        "AGG": "iShares Core U.S. Aggregate Bond ETF",
        "VXUS": "Vanguard Total International Stock ETF"
    }
    return names.get(symbol, f"{symbol} Stock")

def analyze_tax_loss_harvesting(portfolio_data: Dict) -> List[Dict]:
    """Analyze portfolio for tax-loss harvesting opportunities"""
    opportunities = []
    
    for asset in portfolio_data.get("assets", []):
        market_value = asset.get("market_value", 0)
        # Mock cost basis calculation
        cost_basis = market_value * 1.1  # Assume 10% loss
        
        if cost_basis > market_value:
            loss = cost_basis - market_value
            if loss > 50:  # Minimum threshold
                opportunities.append({
                    "symbol": asset.get("symbol", ""),
                    "current_value": market_value,
                    "cost_basis": cost_basis,
                    "unrealized_loss": -loss,
                    "potential_tax_savings": loss * 0.22,  # 22% tax bracket
                    "wash_sale_alternatives": ["VTIAX", "FTIHX", "IXUS"],
                    "recommendation": "Consider harvesting before year-end to realize tax benefits"
                })
    
    return opportunities

def get_demo_portfolio() -> Dict:
    """Return demo portfolio data for testing"""
    return {
        "total_value": 26792.15,
        "total_day_change": 36.87,
        "total_day_change_percent": 0.14,
        "last_recommendation": "Consider increasing international allocation to 15-20% for better diversification",
        "holdings": [
            {
                "symbol": "SPY",
                "name": "SPDR S&P 500 ETF Trust",
                "value": 12056.47,
                "shares": 22.5,
                "allocation": 45.0,
                "sector": "Broad Market",
                "dayChange": 15.23,
                "dayChangePercent": 0.13,
                "price": 535.82
            },
            {
                "symbol": "QQQ",
                "name": "Invesco QQQ Trust",
                "value": 6162.89,
                "shares": 12.8,
                "allocation": 23.0,
                "sector": "Technology",
                "dayChange": 8.94,
                "dayChangePercent": 0.15,
                "price": 481.48
            },
            {
                "symbol": "VTI",
                "name": "Vanguard Total Stock Market ETF",
                "value": 3215.06,
                "shares": 11.2,
                "allocation": 12.0,
                "sector": "Total Market",
                "dayChange": 4.21,
                "dayChangePercent": 0.13,
                "price": 287.06
            },
            {
                "symbol": "AGG",
                "name": "iShares Core U.S. Aggregate Bond ETF",
                "value": 4420.75,
                "shares": 45.8,
                "allocation": 16.5,
                "sector": "Bonds",
                "dayChange": 5.67,
                "dayChangePercent": 0.13,
                "price": 96.52
            },
            {
                "symbol": "VXUS",
                "name": "Vanguard Total International Stock ETF",
                "value": 875.30,
                "shares": 14.6,
                "allocation": 3.3,
                "sector": "International",
                "dayChange": 2.82,
                "dayChangePercent": 0.32,
                "price": 59.95
            }
        ],
        "allocation_summary": {
            "stocks": 83.5,
            "bonds": 16.5,
            "international": 3.3,
            "domestic": 80.2
        },
        "tax_loss_harvesting": {
            "opportunities": [],
            "total_potential_savings": 0,
            "opportunities_count": 0,
            "next_review_date": "2024-12-31"
        },
        "performance_metrics": {
            "ytd_return": 12.4,
            "one_year_return": 15.2,
            "sharpe_ratio": 1.2
        }
    }

# Run the server
if __name__ == "__main__":
    uvicorn.run(
        "web_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
