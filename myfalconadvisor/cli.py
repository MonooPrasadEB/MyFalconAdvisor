#!/usr/bin/env python3
"""
MyFalconAdvisor CLI Demo

A command-line interface to demonstrate the multi-agent investment advisory system
with real financial data integration and comprehensive compliance checking.
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel  
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.text import Text

from .core.supervisor import investment_advisor_supervisor
from .core.config import Config
from .tools.database_service import DatabaseService
from .tools.portfolio_sync_service import portfolio_sync_service
from .agents.execution_agent import ExecutionService
from sqlalchemy import text

console = Console()
config = Config.get_instance()


class InvestmentAdvisorCLI:
    """Command-line interface for MyFalconAdvisor."""
    
    def __init__(self):
        self.supervisor = investment_advisor_supervisor
        self.session_id = None
        self.client_profile = None
        self.db_service = DatabaseService()
        self.current_user_id = "usr_348784c4-6f83-4857-b7dc-f5132a38dfee"  # Default user
        self.current_portfolio_id = None
        self.current_user_name = None
        self.config = Config.get_instance()
        
    def run(self):
        """Main CLI entry point."""
        parser = self._create_parser()
        args = parser.parse_args()
        
        if args.command == "demo":
            self.run_demo(args.query)
        elif args.command == "interactive":
            self.run_interactive()
        elif args.command == "portfolio":
            self.analyze_database_portfolio_interactive()
        elif args.command == "risk":
            self.assess_risk_interactive()
        elif args.command == "validate":
            self.validate_config()
        elif args.command == "rebalance":
            self.generate_database_rebalancing_plan()
        elif args.command == "simulate":
            self.simulate_database_trade(args.symbol, args.action, args.quantity)
        elif args.command == "transactions":
            self.show_my_transactions(args.limit)
        elif args.command == "sync":
            self.handle_sync_command(args)
        else:
            parser.print_help()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create command line argument parser."""
        parser = argparse.ArgumentParser(
            description="MyFalconAdvisor - Multi-Agent Financial Advisory System",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s demo "How is my portfolio performing?"
  %(prog)s interactive
  %(prog)s portfolio
  %(prog)s risk
  %(prog)s rebalance
  %(prog)s simulate --symbol AAPL --action buy --quantity 10
  %(prog)s transactions --limit 20
  %(prog)s sync pending
  %(prog)s sync now
  %(prog)s sync start
  %(prog)s validate
            """
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Demo command
        demo_parser = subparsers.add_parser("demo", help="Quick demo with sample query")
        demo_parser.add_argument("query", help="Investment question or request")
        
        # Interactive command
        subparsers.add_parser("interactive", help="Interactive conversation mode")
        
        # Portfolio analysis command
        subparsers.add_parser("portfolio", help="Analyze portfolio from database")
        
        # Risk assessment command
        subparsers.add_parser("risk", help="Assess risk profile from database")
        
        # Validate configuration
        subparsers.add_parser("validate", help="Validate API keys and configuration")
        
        # Rebalancing command
        subparsers.add_parser("rebalance", help="Generate rebalancing recommendations from database portfolio")
        
        # Trade simulation command  
        simulate_parser = subparsers.add_parser("simulate", help="Simulate buying or selling specific stocks from database portfolio")
        simulate_parser.add_argument("--symbol", required=True, help="Stock symbol (e.g., NVDA, AAPL)")
        simulate_parser.add_argument("--action", required=True, choices=["buy", "sell"], help="Trade action")
        simulate_parser.add_argument("--quantity", required=True, type=int, help="Number of shares")
        
        # User-specific commands
        transactions_parser = subparsers.add_parser("transactions", help="Show your recent transactions")
        transactions_parser.add_argument("--limit", type=int, default=20, help="Number of transactions to show (default: 20)")
        
        # Portfolio sync commands
        sync_parser = subparsers.add_parser("sync", help="Portfolio synchronization commands")
        sync_subparsers = sync_parser.add_subparsers(dest="sync_action", help="Sync actions")
        
        sync_subparsers.add_parser("now", help="Sync your portfolio immediately")
        sync_subparsers.add_parser("status", help="Check sync service status")
        sync_subparsers.add_parser("start", help="Start background sync service")
        sync_subparsers.add_parser("stop", help="Stop background sync service")
        sync_subparsers.add_parser("pending", help="Check pending orders")
        
        return parser
    
    def run_demo(self, query: str):
        """Run a quick demo with the provided query."""
        console.print(Panel.fit("🤖 MyFalconAdvisor - Demo Mode", style="bold blue"))
        console.print(f"📝 Query: {query}\n")
        
        # Load real user profile and portfolio from database
        client_profile = self._get_sample_client_profile()  # This now loads from DB
        portfolio_data = self._load_database_portfolio_auto()
        
        if not portfolio_data:
            console.print("[yellow]⚠️ No portfolio found. Demo will use general investment advice.[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing request...", total=None)
            
            try:
                result = self.supervisor.process_client_request(
                    request=query,
                    client_profile=client_profile,
                    portfolio_data=portfolio_data,
                    user_id=self.current_user_id
                )
                
                progress.stop()
                self._display_results(result)
                
            except Exception as e:
                progress.stop()
                console.print(f"[red]❌ Error: {str(e)}[/red]")
                console.print("\n💡 Make sure you have configured your API keys in .env file")
    
    def run_interactive(self):
        """Run interactive conversation mode."""
        console.print(Panel.fit("🤖 MyFalconAdvisor - Interactive Mode", style="bold green"))
        
        # Get user information and provide personalized greeting
        try:
            user_info = self._get_current_user_info()
        except Exception as e:
            console.print(f"⚠️ Could not fetch user info: {e}")
            user_info = None
            
        if user_info:
            user_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
            if not user_name:
                user_name = user_info.get('email', 'User')
            self.current_user_name = user_name
            
            console.print(f"👋 Hi {user_name}! How are you and how may I help you today?")
            console.print(f"💡 Connected as: {self.current_user_id[:8]}...")
        else:
            console.print(f"👋 Hi! How are you and how may I help you today?")
            console.print(f"💡 Connected as: {self.current_user_id[:8]}...")
        
        console.print("Type 'exit' to quit, 'help' for commands, or ask any investment question.\n")
        
        # Automatically load user's data from database (simulating authenticated web app)
        console.print("🔄 Loading your data from database...")
        
        # Auto-load client profile from database
        try:
            self.client_profile = self._get_sample_client_profile()  # Now loads from database
        except Exception as e:
            console.print(f"Error loading user profile: {e}")
            console.print("💡 Using sample profile (in real app, this would come from your account)")
            self.client_profile = {
                "age": 35,
                "risk_tolerance": "moderate",
                "investment_goals": ["growth", "income"],
                "time_horizon": "long_term"
            }
        
        # Auto-load user's portfolio
        try:
            self.portfolio_data = self._load_database_portfolio_auto()
        except Exception as e:
            console.print(f"Error loading portfolio: {e}")
            self.portfolio_data = None
        
        if self.portfolio_data:
            console.print(f"✅ Portfolio loaded: {len(self.portfolio_data.get('assets', []))} holdings, ${self.portfolio_data.get('total_value', 0):,.2f} total value")
        else:
            console.print("💡 No portfolio found - you can create one or ask general investment questions")
        
        console.print()
        
        while True:
            try:
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    console.print("👋 Thank you for using MyFalconAdvisor!")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'profile':
                    profile_result = self._collect_client_profile()
                    if profile_result is not None:
                        self.client_profile = profile_result
                        console.print("✅ Client profile updated")
                    else:
                        console.print("💡 Profile setup cancelled")
                    continue
                elif user_input.lower() == 'portfolio':
                    # Refresh portfolio data from database
                    self.portfolio_data = self._load_database_portfolio_auto()
                    if self.portfolio_data:
                        console.print(f"✅ Portfolio refreshed: {len(self.portfolio_data.get('assets', []))} holdings, ${self.portfolio_data.get('total_value', 0):,.2f} total value")
                    else:
                        console.print("❌ No portfolio found")
                    continue
                elif user_input.lower() == 'transactions':
                    # Show user's recent transactions
                    self.show_my_transactions()
                    continue
                
                # Process the request
                with console.status("[bold green]AI Advisor is thinking..."):
                    try:
                        result = self.supervisor.process_client_request(
                            request=user_input,
                            client_profile=self.client_profile,
                            portfolio_data=self.portfolio_data,
                            session_id=self.session_id
                        )
                    
                        # Capture session_id for subsequent requests
                        if not self.session_id and result.get("session_id"):
                            self.session_id = result["session_id"]
                            
                    except Exception as e:
                        console.print(f"Database error with params: {e}")
                        console.print("Failed to start chat session")
                        console.print("Failed to start chat session - continuing without logging")
                        
                        # Provide a fallback response
                        result = {
                            "response": "I don't see any portfolio data loaded. Please load your portfolio file first using the 'portfolio' command, then I can help answer your question: \"" + user_input + "\"",
                            "session_id": None,
                            "workflow_complete": True
                        }
                
                # Display response
                self._display_interactive_response(result)
                
            except KeyboardInterrupt:
                console.print("\n👋 Thank you for using MyFalconAdvisor! (Ctrl+C)")
                break
            except EOFError:
                console.print("\n👋 Thank you for using MyFalconAdvisor!")
                break
            except Exception as e:
                console.print(f"[red]❌ Error: {str(e)}[/red]")
                console.print("Please try again or type 'help' for assistance.")
    
    def analyze_database_portfolio_interactive(self):
        """Automatic portfolio analysis from database."""
        console.print(Panel.fit("📊 Your Portfolio Analysis", style="bold green"))
        
        # Auto-load user's portfolio from database
        portfolio_data = self._load_database_portfolio_auto()
        if not portfolio_data:
            console.print("[red]❌ No portfolio found for your account[/red]")
            return
        
        console.print(f"✅ Analyzing portfolio: {len(portfolio_data.get('assets', []))} holdings, ${portfolio_data.get('total_value', 0):,.2f} total value")
        
        # Use sample client profile for now
        client_data = self._get_sample_client_profile()
        
        query = "Please provide a comprehensive analysis of my portfolio including risk assessment and rebalancing recommendations."
        
        with console.status("[bold green]AI Advisor analyzing portfolio..."):
            result = self.supervisor.process_client_request(
                request=query,
                client_profile=client_data,
                portfolio_data=portfolio_data,
                user_id=self.current_user_id
            )
        
        self._display_results(result)
    
    def assess_risk_interactive(self):
        """Assess client risk profile using existing profile."""
        console.print(Panel.fit("⚖️ Your Risk Assessment", style="bold red"))
        
        # Use existing client profile (in web app, this would come from user account)
        client_data = self._get_sample_client_profile()
        console.print(f"✅ Using your profile: {client_data.get('age', 'N/A')} years old, {client_data.get('risk_tolerance', 'N/A')} risk tolerance")
        
        # Auto-load portfolio if available
        portfolio_data = self._load_database_portfolio_auto()
        if portfolio_data:
            console.print(f"✅ Including portfolio: {len(portfolio_data.get('assets', []))} holdings, ${portfolio_data.get('total_value', 0):,.2f} total value")
        
        query = "Please assess my risk tolerance and recommend an appropriate asset allocation based on my profile and current portfolio."
        
        with console.status("[bold green]Assessing risk profile..."):
            result = self.supervisor.process_client_request(
                request=query,
                client_profile=client_data,
                portfolio_data=portfolio_data,
                user_id=self.current_user_id
            )
        
        self._display_results(result)
    
    def validate_config(self):
        """Validate API keys and configuration."""
        console.print(Panel.fit("🔧 Configuration Validation", style="bold magenta"))
        
        # Check API keys
        api_keys = config.validate_api_keys()
        
        table = Table(title="API Key Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Required", style="yellow")
        
        for service, configured in api_keys.items():
            status = "✅ Configured" if configured else "❌ Missing"
            required = "Yes" if service == "openai" else "Optional"
            table.add_row(service.title(), status, required)
        
        console.print(table)
        
        # Check market data configuration
        market_config = config.get_market_data_config()
        console.print(f"\n📈 Market Data Provider: {market_config['provider']}")
        
        # Provide guidance
        if not api_keys["openai"]:
            console.print("\n[red]⚠️ OpenAI API key is required for the system to function.[/red]")
            console.print("Add OPENAI_API_KEY to your .env file")
        else:
            console.print("\n[green]✅ Configuration looks good![/green]")
    
    def _display_results(self, result: Dict):
        """Display comprehensive results from the investment advisor."""
        if "error" in result:
            console.print(f"[red]❌ Error: {result['error']}[/red]")
            return
        
        # Main response
        console.print(Panel(result["response"], title="🤖 MyFalconAdvisor", border_style="blue"))
        
        # Analysis results
        if result.get("analysis_results"):
            analysis = result["analysis_results"]
            
            # Portfolio metrics table
            metrics_table = Table(title="📊 Portfolio Metrics")
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="green")
            
            portfolio_metrics = analysis.get("portfolio_metrics", {})
            for metric, value in portfolio_metrics.items():
                metrics_table.add_row(metric.replace('_', ' ').title(), f"{value}")
            
            console.print(metrics_table)
            
            # Recommendations
            if analysis.get("recommendations"):
                console.print("\n💡 Recommendations:")
                for i, rec in enumerate(analysis["recommendations"], 1):
                    console.print(f"   {i}. {rec}")
        
        # Trade recommendations
        if result.get("trade_recommendations"):
            trades_table = Table(title="📈 Trade Recommendations")
            trades_table.add_column("Symbol", style="cyan")
            trades_table.add_column("Action", style="yellow")
            trades_table.add_column("Quantity", style="green")
            trades_table.add_column("Rationale", style="white")
            
            for trade in result["trade_recommendations"]:
                trades_table.add_row(
                    trade["symbol"],
                    trade["action"].upper(),
                    str(trade["quantity"]),
                    trade["rationale"]
                )
            
            console.print(trades_table)
        
        # Approval required
        if result.get("requires_user_approval"):
            console.print("\n[yellow]⚠️ User approval required before trade execution[/yellow]")
        
        # Compliance status
        if result.get("compliance_approved"):
            console.print("\n[green]✅ Compliance approved[/green]")
    
    def _display_interactive_response(self, result: Dict):
        """Display response in interactive mode."""
        if "error" in result:
            console.print(f"[red]❌ {result['error']}[/red]")
            return
        
        # AI response
        ai_text = Text("AI Advisor: ", style="bold blue")
        response_md = Markdown(result["response"])
        console.print(ai_text)
        console.print(response_md)
        
        # Show additional info if available
        if result.get("requires_user_approval"):
            console.print("\n[yellow]💬 This requires your approval. Type 'approve' to proceed.[/yellow]")
    
    def _collect_client_profile(self) -> Optional[Dict]:
        """Collect client profile information interactively."""
        console.print("📋 Client Profile Setup")
        
        try:
            age_response = Prompt.ask("Age", default="35")
            if age_response.lower() in ['exit', 'quit']:
                console.print("👋 Cancelled profile setup")
                return None
            age = int(age_response)
            
            income_response = Prompt.ask("Annual income (USD)", default="75000")
            if income_response.lower() in ['exit', 'quit']:
                console.print("👋 Cancelled profile setup")
                return None
            income = float(income_response)
            
            net_worth_response = Prompt.ask("Net worth (USD)", default="250000")
            if net_worth_response.lower() in ['exit', 'quit']:
                console.print("👋 Cancelled profile setup")
                return None
            net_worth = float(net_worth_response)
        except ValueError as e:
            console.print(f"❌ Invalid input: {e}")
            console.print("Using default values...")
            age, income, net_worth = 35, 75000, 250000
        
        experience = Prompt.ask(
            "Investment experience",
            choices=["beginner", "intermediate", "advanced", "expert", "exit", "quit"],
            default="intermediate"
        )
        if experience.lower() in ['exit', 'quit']:
            console.print("👋 Cancelled profile setup")
            return None
        
        risk_tolerance = Prompt.ask(
            "Risk tolerance",
            choices=["conservative", "moderate", "aggressive", "exit", "quit"],
            default="moderate"
        )
        if risk_tolerance.lower() in ['exit', 'quit']:
            console.print("👋 Cancelled profile setup")
            return None
        
        try:
            horizon_response = Prompt.ask("Investment time horizon (years)", default="20")
            if horizon_response.lower() in ['exit', 'quit']:
                console.print("👋 Cancelled profile setup")
                return None
            time_horizon = int(horizon_response)
        except ValueError:
            console.print("❌ Invalid time horizon, using default (20 years)")
            time_horizon = 20
        
        primary_goal = Prompt.ask(
            "Primary investment goal",
            choices=["retirement", "wealth_building", "income", "preservation", "exit", "quit"],
            default="wealth_building"
        )
        if primary_goal.lower() in ['exit', 'quit']:
            console.print("👋 Cancelled profile setup")
            return None
        
        profile = {
            "age": age,
            "annual_income": income,
            "net_worth": net_worth,
            "investment_experience": experience,
            "risk_tolerance": risk_tolerance,
            "time_horizon": time_horizon,
            "primary_goal": primary_goal
        }
        
        console.print("[green]✅ Profile created successfully![/green]\n")
        return profile
    
    def _show_help(self):
        """Show help information."""
        help_text = """
## Available Commands:
- **help** - Show this help message
- **profile** - Set up or update client profile  
- **portfolio** - Refresh your portfolio data from database
- **transactions** - View your recent transaction history
- **exit/quit/bye** - Exit the program
- **Ctrl+C** - Quick exit

## CLI Commands:
- `myfalcon portfolio` - Analyze your portfolio
- `myfalcon risk` - Assess portfolio risk
- `myfalcon rebalance` - Get rebalancing recommendations
- `myfalcon simulate --symbol AAPL --action buy --quantity 10` - Simulate trades
- `myfalcon transactions --limit 50` - View transaction history

## Example Questions:
- "How is my portfolio performing?"
- "Should I rebalance my holdings?"
- "What's your opinion on my Apple position?"
- "Should I invest more in tech stocks?"
- "How risky is my current portfolio?"
- "I want to buy 100 shares of AAPL, is that a good idea?"
- "What's the best asset allocation for my age?"

## Tips:
- Your portfolio data is automatically loaded from the database
- Be specific about your investment goals and timeframe
- Ask about your specific holdings or general investment strategies
- The AI knows your current positions and can give personalized advice
"""
        console.print(Markdown(help_text))
    
    def _get_sample_client_profile(self) -> Dict:
        """Get client profile from database or fallback to sample."""
        try:
            # Try to load real user profile from database
            user_profile = self._load_user_profile_from_database()
            if user_profile:
                return user_profile
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not load user profile from database: {str(e)}[/yellow]")
        
        # Fallback to sample profile for demo
        console.print("[yellow]💡 Using sample profile (in real app, this would come from your account)[/yellow]")
        return {
            "age": 32,
            "annual_income": 85000,
            "net_worth": 150000,
            "investment_experience": "intermediate",
            "risk_tolerance": "moderate",
            "time_horizon": 25,
            "primary_goal": "wealth_building"
        }
    
    def _load_user_profile_from_database(self) -> Optional[Dict]:
        """Load user profile from database."""
        try:
            with self.db_service.get_session() as session:
                result = session.execute(text("""
                    SELECT user_id, email, first_name, last_name, dob, 
                           risk_profile, objective, annual_income_usd, net_worth_usd
                    FROM users 
                    WHERE user_id = :user_id
                """), {"user_id": self.current_user_id})
                
                user_row = result.fetchone()
                if not user_row:
                    return None
                
                # Calculate age from date of birth
                age = None
                if user_row[4]:  # dob
                    from datetime import date
                    today = date.today()
                    dob = user_row[4]
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                
                # Map database fields to expected profile format
                return {
                    "age": age or 32,  # fallback age
                    "annual_income": float(user_row[7]) if user_row[7] else 85000,
                    "net_worth": float(user_row[8]) if user_row[8] else 150000,
                    "investment_experience": "intermediate",  # could be derived from risk_profile
                    "risk_tolerance": user_row[5] or "moderate",  # risk_profile
                    "time_horizon": 25,  # could be calculated from age and retirement goals
                    "primary_goal": user_row[6] or "wealth_building"  # objective
                }
                
        except Exception as e:
            console.print(f"[red]Error loading user profile: {str(e)}[/red]")
            return None
    
    
    
    def generate_rebalancing_plan_legacy(self, portfolio_file: str, client_profile_file: Optional[str] = None, output_file: Optional[str] = None):
        """Generate and display specific rebalancing trade recommendations."""
        console.print(Panel.fit("📊 Portfolio Rebalancing Analysis", style="bold green"))
        
        # Load portfolio data
        portfolio_data = self._load_json_file(portfolio_file)
        if not portfolio_data:
            console.print(f"[red]❌ Could not load portfolio from {portfolio_file}[/red]")
            return
        
        # Load client profile if provided
        client_profile = None
        if client_profile_file:
            client_profile = self._load_json_file(client_profile_file)
            if client_profile:
                risk_tolerance = client_profile.get('risk_tolerance', 'unknown')
                console.print(f"👤 Client Profile: {risk_tolerance.title()} risk tolerance")
            else:
                console.print("[yellow]⚠️ Could not load client profile - using default analysis[/yellow]")
        else:
            console.print("[yellow]💡 No client profile provided - using general rebalancing logic[/yellow]")
        
        console.print(f"📁 Portfolio: {len(portfolio_data.get('assets', []))} holdings, ${portfolio_data.get('total_value', 0):,.2f} total value\n")
                
                # Generate rebalancing plan (with user profile if available)
        console.print("[yellow]⚠️ Rebalancing feature not yet implemented[/yellow]")
        return
    
    def simulate_trade_legacy(self, portfolio_file: str, symbol: str, action: str, quantity: int):
        """Simulate a specific buy or sell trade."""
        console.print(Panel.fit(f"🎯 Trade Simulation: {action.upper()} {quantity} shares of {symbol.upper()}", style="bold yellow"))
        
        # Load portfolio data
        portfolio_data = self._load_json_file(portfolio_file)
        if not portfolio_data:
            console.print(f"[red]❌ Could not load portfolio from {portfolio_file}[/red]")
            return
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Fetching market data and simulating trade...", total=None)
                
                # Simulate the trade
                console.print("[yellow]⚠️ Trade simulation not yet implemented - use ExecutionService instead[/yellow]")
                return
                
                progress.update(task, description="Simulation complete!")
            
            if "error" in result:
                console.print(f"[red]❌ {result['error']}[/red]")
                return
            
            # Display results
            trade_details = result["trade_details"]
            position_impact = result["position_impact"]
            portfolio_impact = result["portfolio_impact"]
            market_data = result["market_data"]
            
            console.print("\n" + "="*50)
            console.print("[bold blue]TRADE SIMULATION RESULTS[/bold blue]")
            console.print("="*50)
            
            # Trade Details
            console.print("[bold green]💼 TRADE DETAILS[/bold green]")
            action_color = "green" if action == "buy" else "red"
            console.print(f"• Action: [{action_color}]{trade_details['action']}[/{action_color}]")
            console.print(f"• Symbol: [bold]{trade_details['symbol']}[/bold]")
            console.print(f"• Quantity: [bold]{trade_details['quantity']:,}[/bold] shares")
            console.print(f"• Price: [bold]${trade_details['price']:.2f}[/bold] per share")
            console.print(f"• Trade Value: [bold]${trade_details['trade_value']:,.2f}[/bold]")
            console.print(f"• Commission: [bold]${trade_details['commission']:.2f}[/bold]")
            console.print(f"• Total Cost: [bold]${trade_details['total_cost']:,.2f}[/bold]")
            
            if trade_details['cash_impact'] < 0:
                console.print(f"• Cash Required: [red]${abs(trade_details['cash_impact']):,.2f}[/red]")
            else:
                console.print(f"• Cash Generated: [green]${trade_details['cash_impact']:,.2f}[/green]")
            
            console.print()
            
            # Position Impact
            console.print("[bold yellow]📊 POSITION IMPACT[/bold yellow]")
            console.print(f"• Current Shares: [bold]{position_impact['current_shares']:,}[/bold]")
            console.print(f"• New Shares: [bold]{position_impact['new_shares']:,}[/bold]")
            console.print(f"• Current Value: [bold]${position_impact['current_value']:,.2f}[/bold]")
            console.print(f"• New Value: [bold]${position_impact['new_value']:,.2f}[/bold]")
            console.print(f"• Current Allocation: [bold]{position_impact['current_allocation']:.2f}%[/bold]")
            console.print(f"• New Allocation: [bold]{position_impact['new_allocation']:.2f}%[/bold]")
            
            change_color = "green" if position_impact['allocation_change'] > 0 else "red"
            console.print(f"• Allocation Change: [{change_color}]{position_impact['allocation_change']:+.2f}%[/{change_color}]")
            console.print()
            
            # Market Data
            console.print("[bold cyan]📈 MARKET DATA[/bold cyan]")
            console.print(f"• Current Price: [bold]${market_data['current_price']:.2f}[/bold]")
            if market_data['market_cap']:
                console.print(f"• Market Cap: [bold]${market_data['market_cap']/1e9:.1f}B[/bold]")
            if market_data['sector']:
                console.print(f"• Sector: [bold]{market_data['sector']}[/bold]")
            if market_data['pe_ratio']:
                console.print(f"• P/E Ratio: [bold]{market_data['pe_ratio']:.1f}[/bold]")
            
            console.print()
            
            # User approval for trade simulation
            console.print("[bold yellow]💭 SIMULATION COMPLETE[/bold yellow]")
            console.print("This simulation shows the expected impact of your proposed trade.")
            console.print()
            
            # Auto-complete simulation (in web app, user would review and confirm via UI)
            console.print(f"\n[green]✅ Trade simulation completed successfully![/green]")
            console.print(f"[yellow]⚠️ Note: This is a simulation based on your portfolio.[/yellow]")
            console.print("Next steps:")
            console.print(f"• Expected total cost: ${trade_details['total_cost']:,.2f}")
            console.print("• Use interactive mode to discuss this trade with AI advisor")
            console.print("• In a real app, you'd review and confirm via the web interface")
            
        except Exception as e:
            console.print(f"[red]❌ Error simulating trade: {str(e)}[/red]")
    
    def show_my_transactions(self, limit: int = 20):
        """Show current user's recent transactions."""
        console.print(Panel.fit("💳 Your Recent Transactions", style="bold blue"))
        
        try:
            with self.db_service.get_session() as session:
                query = """
                    SELECT t.transaction_id, t.portfolio_id, t.symbol, t.transaction_type, 
                           t.quantity, t.price, t.total_amount, t.created_at,
                           p.portfolio_name
                    FROM transactions t
                    LEFT JOIN portfolios p ON t.portfolio_id = p.portfolio_id
                    WHERE p.user_id = :user_id
                    ORDER BY t.created_at DESC 
                    LIMIT :limit
                """
                
                result = session.execute(text(query), {
                    "user_id": self.current_user_id,
                    "limit": limit
                })
                transactions = result.fetchall()
                
                if not transactions:
                    console.print("[yellow]No transactions found for your account[/yellow]")
                    return
                
                table = Table(title="Your Transaction History")
                table.add_column("Date", style="cyan")
                table.add_column("Portfolio", style="green")
                table.add_column("Symbol", style="yellow")
                table.add_column("Type", style="magenta")
                table.add_column("Quantity", style="blue", justify="right")
                table.add_column("Price", style="white", justify="right")
                table.add_column("Total", style="red", justify="right")
                
                for txn in transactions:
                    # Format date (created_at is at index 7)
                    date_str = txn[7].strftime("%Y-%m-%d %H:%M") if txn[7] else "N/A"
                    
                    # Portfolio name
                    portfolio_name = txn[8] or "N/A"
                    
                    table.add_row(
                        date_str,
                        portfolio_name,
                        txn[2] or "N/A",  # symbol
                        txn[3] or "N/A",  # transaction_type
                        f"{float(txn[4] or 0):.2f}",  # quantity
                        f"${float(txn[5] or 0):.2f}",  # price
                        f"${float(txn[6] or 0):,.2f}"  # total_amount
                    )
                
                console.print(table)
                console.print(f"\n[green]✅ Showing {len(transactions)} of your transactions[/green]")
                
        except Exception as e:
            console.print(f"[red]❌ Error fetching your transactions: {str(e)}[/red]")
    
    
    def _load_database_portfolio(self) -> Optional[Dict]:
        """Interactive database portfolio loading for current user."""
        try:
            # Use current user - no need to select
            console.print(f"📋 Loading portfolios for current user: {self.current_user_name or self.current_user_id[:8]}...")
            
            with console.status("Fetching portfolios..."):
                portfolios = self.db_service.get_user_portfolios(self.current_user_id)
            
            if not portfolios:
                console.print(f"[yellow]No portfolios found for user {self.current_user_id[:8]}...[/yellow]")
                return None
            
            # Show portfolios table
            portfolios_table = Table()
            portfolios_table.add_column("Index", style="cyan")
            portfolios_table.add_column("Portfolio ID", style="blue")
            portfolios_table.add_column("Name", style="white")
            portfolios_table.add_column("Value", style="green")
            
            for i, portfolio in enumerate(portfolios, 1):
                portfolio_id = str(portfolio['portfolio_id'])[:8] + "..."
                name = portfolio.get('portfolio_name', 'N/A')
                value = f"${portfolio.get('total_value', 0):,.2f}"
                portfolios_table.add_row(str(i), portfolio_id, name, value)
            
            console.print(portfolios_table)
            
            # Let user select portfolio
            portfolio_choice = Prompt.ask("Select portfolio by index", default="1")
            
            try:
                portfolio_index = int(portfolio_choice) - 1
                
                if 0 <= portfolio_index < len(portfolios):
                    selected_portfolio = portfolios[portfolio_index]
                    self.current_portfolio_id = selected_portfolio['portfolio_id']
                    
                    # Get portfolio assets
                    assets = self.db_service.get_portfolio_assets(self.current_portfolio_id)
                    
                    # Convert to expected format (convert Decimal to float)
                    portfolio_data = {
                        "total_value": float(selected_portfolio.get('total_value', 0)) if selected_portfolio.get('total_value') else 0,
                        "cash_balance": float(selected_portfolio.get('cash_balance', 0)) if selected_portfolio.get('cash_balance') else 0,
                        "assets": []
                    }
                    
                    for asset in assets:
                        # Convert Decimal types to float for JSON serialization
                        quantity = float(asset.get('quantity', 0)) if asset.get('quantity') else 0
                        current_price = float(asset.get('current_price', 0)) if asset.get('current_price') else 0
                        market_value = float(asset.get('market_value', 0)) if asset.get('market_value') else 0
                        
                        portfolio_data["assets"].append({
                            "symbol": asset.get('symbol', ''),
                            "quantity": quantity,
                            "current_price": current_price,
                            "market_value": market_value,
                            "allocation": (market_value / float(portfolio_data["total_value"]) * 100) if portfolio_data["total_value"] > 0 else 0,
                            "sector": asset.get('sector', 'Unknown')
                        })
                    
                    console.print(f"✅ Loaded portfolio: {len(portfolio_data['assets'])} holdings, ${portfolio_data['total_value']:,.2f} total value")
                    return portfolio_data
                else:
                    console.print("[red]Invalid selection[/red]")
                    return None
                    
            except ValueError:
                console.print("[red]Invalid selection[/red]")
                return None
                
        except Exception as e:
            console.print(f"[red]❌ Error loading database portfolio: {str(e)}[/red]")
            return None
    
    def _load_database_portfolio_auto(self) -> Optional[Dict]:
        """Automatically load user's first portfolio from database (simulating web app behavior)."""
        try:
            # Get user's portfolios
            portfolios = self.db_service.get_user_portfolios(self.current_user_id)
            
            if not portfolios:
                return None
            
            # Auto-select first portfolio (in real app, might be user's primary/default portfolio)
            selected_portfolio = portfolios[0]
            self.current_portfolio_id = selected_portfolio['portfolio_id']
            
            # Get portfolio assets
            assets = self.db_service.get_portfolio_assets(self.current_portfolio_id)
            
            # Convert to expected format (convert Decimal to float)
            portfolio_data = {
                "total_value": float(selected_portfolio.get('total_value', 0)) if selected_portfolio.get('total_value') else 0,
                "cash_balance": float(selected_portfolio.get('cash_balance', 0)) if selected_portfolio.get('cash_balance') else 0,
                "assets": []
            }
            
            for asset in assets:
                # Convert Decimal types to float for JSON serialization
                quantity = float(asset.get('quantity', 0)) if asset.get('quantity') else 0
                current_price = float(asset.get('current_price', 0)) if asset.get('current_price') else 0
                market_value = float(asset.get('market_value', 0)) if asset.get('market_value') else 0
                symbol = asset.get('symbol', '')
                
                # Use sector from database, or 'Other' if not available (skip AI classification during startup for speed)
                sector = asset.get('sector') or 'Other'
                
                portfolio_data["assets"].append({
                    "symbol": symbol,
                    "quantity": quantity,
                    "current_price": current_price,
                    "market_value": market_value,
                    "allocation": (market_value / float(portfolio_data["total_value"]) * 100) if portfolio_data["total_value"] > 0 else 0,
                    "sector": sector
                })
            
            return portfolio_data
                
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not auto-load portfolio: {str(e)}[/yellow]")
            return None
    
    def _classify_stock_sector(self, symbol: str) -> str:
        """Use AI to classify stock sector in real-time."""
        try:
            from langchain_openai import ChatOpenAI
            
            llm = ChatOpenAI(
                model=self.config.default_model,
                temperature=0.0,  # Deterministic for classification
                api_key=self.config.openai_api_key
            )
            
            # Simple sector classification prompt
            prompt = f"""
            Classify the stock symbol '{symbol}' into ONE of these sectors:
            - Technology
            - Healthcare  
            - Financial Services
            - Consumer Discretionary
            - Consumer Staples
            - Energy
            - Utilities
            - Real Estate
            - Materials
            - Industrials
            - Communication Services
            - Other
            
            For ETFs, classify by primary focus (e.g., SPY=Other, QQQ=Technology, VTI=Other).
            
            Respond with ONLY the sector name, nothing else.
            """
            
            response = llm.invoke(prompt)
            sector = response.content.strip()
            
            # Validate response is one of our expected sectors
            valid_sectors = {
                'Technology', 'Healthcare', 'Financial Services', 'Consumer Discretionary',
                'Consumer Staples', 'Energy', 'Utilities', 'Real Estate', 'Materials',
                'Industrials', 'Communication Services', 'Other'
            }
            
            return sector if sector in valid_sectors else 'Other'
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not classify {symbol}: {str(e)}[/yellow]")
            return 'Other'
    
    def generate_database_rebalancing_plan(self):
        """Generate rebalancing plan from database portfolio."""
        console.print(Panel.fit("📊 Your Portfolio Rebalancing Plan", style="bold green"))
        
        # Auto-load user's portfolio from database
        portfolio_data = self._load_database_portfolio_auto()
        if not portfolio_data:
            console.print("[red]❌ No portfolio found for your account[/red]")
            return
        
        console.print(f"✅ Analyzing portfolio: {len(portfolio_data.get('assets', []))} holdings, ${portfolio_data.get('total_value', 0):,.2f} total value")
        
        # Use sample client profile for now
        client_profile = self._get_sample_client_profile()
        
        # Generate rebalancing plan
        console.print("[yellow]⚠️ Rebalancing feature not yet implemented[/yellow]")
    
    def simulate_database_trade(self, symbol: str, action: str, quantity: int):
        """Simulate a trade using database portfolio."""
        console.print(Panel.fit(f"🎯 Trade Simulation: {action.upper()} {quantity} shares of {symbol.upper()}", style="bold yellow"))
        
        # Auto-load user's portfolio from database
        portfolio_data = self._load_database_portfolio_auto()
        if not portfolio_data:
            console.print("[red]❌ No portfolio found for your account[/red]")
            return
        
        console.print(f"✅ Using portfolio: {len(portfolio_data.get('assets', []))} holdings, ${portfolio_data.get('total_value', 0):,.2f} total value")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Fetching market data and simulating trade...", total=None)
                
                # Simulate the trade
                console.print("[yellow]⚠️ Trade simulation not yet implemented - use ExecutionService instead[/yellow]")
                return
                
                progress.update(task, description="Simulation complete!")
            
            if "error" in result:
                console.print(f"[red]❌ {result['error']}[/red]")
                return
            
            # Display results
            trade_details = result["trade_details"]
            
            console.print("\n" + "="*50)
            console.print("[bold blue]TRADE SIMULATION RESULTS[/bold blue]")
            console.print("="*50)
            
            # Trade Details
            console.print("[bold green]💼 TRADE DETAILS[/bold green]")
            action_color = "green" if action == "buy" else "red"
            console.print(f"• Action: [{action_color}]{trade_details['action']}[/{action_color}]")
            console.print(f"• Symbol: [bold]{trade_details['symbol']}[/bold]")
            console.print(f"• Quantity: [bold]{trade_details['quantity']:,}[/bold] shares")
            console.print(f"• Price: [bold]${trade_details['price']:.2f}[/bold] per share")
            console.print(f"• Total Cost: [bold]${trade_details['total_cost']:,.2f}[/bold]")
            
            # Auto-approve simulation (in web app, this would be handled by UI)
            console.print(f"\n[green]✅ Trade simulation completed successfully![/green]")
            console.print(f"[yellow]⚠️ Note: This is a simulation based on your database portfolio.[/yellow]")
            console.print("• Use interactive mode to discuss this trade with the AI advisor")
            
        except Exception as e:
            console.print(f"[red]❌ Error simulating trade: {str(e)}[/red]")
    
    def _get_current_user_info(self) -> Optional[Dict]:
        """Get information about the current user from database."""
        try:
            with self.db_service.get_session() as session:
                result = session.execute(text("""
                    SELECT user_id, email, first_name, last_name 
                    FROM users 
                    WHERE user_id = :user_id
                """), {"user_id": self.current_user_id})
                user_row = result.fetchone()
                
                if user_row:
                    return {
                        "user_id": user_row[0],
                        "email": user_row[1],
                        "first_name": user_row[2],
                        "last_name": user_row[3]
                    }
                return None
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not fetch user info: {str(e)}[/yellow]")
            return None
    
    def handle_sync_command(self, args):
        """Handle portfolio sync commands."""
        if not hasattr(args, 'sync_action') or args.sync_action is None:
            console.print("[yellow]Please specify a sync action: now, status, start, stop, or pending[/yellow]")
            return
            
        if args.sync_action == "now":
            self.sync_portfolio_now()
        elif args.sync_action == "status":
            self.show_sync_status()
        elif args.sync_action == "start":
            self.start_sync_service()
        elif args.sync_action == "stop":
            self.stop_sync_service()
        elif args.sync_action == "pending":
            self.show_pending_orders()
        else:
            console.print(f"[red]Unknown sync action: {args.sync_action}[/red]")
    
    def sync_portfolio_now(self):
        """Manually sync portfolio immediately."""
        console.print("🔄 Syncing your portfolio with Alpaca...")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Synchronizing portfolio...", total=None)
                
                result = portfolio_sync_service.sync_user_now(self.current_user_id)
                
                progress.update(task, completed=True)
            
            if result.get("success"):
                console.print(f"✅ {result['message']}")
                
                # Show synced portfolios
                if result.get("portfolios"):
                    table = Table(title="Synced Portfolios")
                    table.add_column("Portfolio ID", style="cyan")
                    table.add_column("Name", style="green")
                    table.add_column("Status", style="yellow")
                    
                    for portfolio in result["portfolios"]:
                        table.add_row(
                            portfolio["portfolio_id"][:8] + "...",
                            portfolio["portfolio_name"],
                            portfolio["status"]
                        )
                    
                    console.print(table)
            else:
                console.print(f"❌ Sync failed: {result.get('error')}")
                
        except Exception as e:
            console.print(f"[red]❌ Error syncing portfolio: {str(e)}[/red]")
    
    def show_sync_status(self):
        """Show current sync service status."""
        try:
            status = portfolio_sync_service.get_sync_status()
            
            # Create status panel
            status_text = f"""
🔄 **Service Status:** {'🟢 Running' if status['is_running'] else '🔴 Stopped'}
📈 **Market Hours:** {'🟢 Yes' if status['market_hours'] else '🔴 No'}
📅 **Weekend:** {'🟢 Yes' if status['is_weekend'] else '🔴 No'}
⏰ **Next Sync:** {status['next_sync']}
📋 **Scheduled Jobs:** {status['scheduled_jobs']}
            """
            
            console.print(Panel(status_text, title="Portfolio Sync Status", border_style="blue"))
            
        except Exception as e:
            console.print(f"[red]❌ Error getting sync status: {str(e)}[/red]")
    
    def start_sync_service(self):
        """Start the background sync service."""
        console.print("ℹ️  Simple sync service doesn't run in background")
        console.print("💡 Use 'myfalcon sync now' to manually sync your portfolio")
        console.print("💡 Use 'myfalcon sync pending' to check pending orders")
    
    def stop_sync_service(self):
        """Stop the background sync service."""
        console.print("ℹ️  Simple sync service doesn't run in background")
        console.print("💡 No background service to stop")
    
    def show_pending_orders(self):
        """Show pending orders that will be processed when market opens."""
        try:
            # Get pending orders from database instead
            pending_orders = self._get_pending_orders_from_db()
            
            if not pending_orders:
                console.print("✅ No pending orders found")
                return
            
            # Create pending orders table
            table = Table(title=f"Your Pending Orders ({len(pending_orders)} total)")
            table.add_column("Symbol", style="cyan")
            table.add_column("Action", style="green")
            table.add_column("Quantity", style="yellow")
            table.add_column("Price", style="magenta")
            table.add_column("Status", style="blue")
            table.add_column("Submitted", style="dim")
            table.add_column("Broker Ref", style="dim")
            
            total_value = 0
            for order in pending_orders:
                price = float(order["price"]) if order["price"] else 0
                quantity = int(order["quantity"])
                order_value = price * quantity
                total_value += order_value
                
                table.add_row(
                    order["symbol"],
                    order["transaction_type"].upper(),
                    str(quantity),
                    f"${price:.2f}" if price > 0 else "Market",
                    order["status"].upper(),
                    order["created_at"].strftime("%m/%d %H:%M") if order["created_at"] else "N/A",
                    order["broker_reference"][:8] + "..." if order["broker_reference"] else "N/A"
                )
            
            console.print(table)
            
            if total_value > 0:
                console.print(f"\n💰 Total pending order value: ${total_value:,.2f}")
            
            # Show market status
            from datetime import datetime, time as dt_time
            now = datetime.now()
            market_open = dt_time(9, 30)
            market_close = dt_time(16, 0)
            is_market_hours = (market_open <= now.time() <= market_close and now.weekday() < 5)
            
            if is_market_hours:
                console.print("\n🟢 Market is currently OPEN - orders should execute soon!")
            else:
                console.print("\n🔴 Market is currently CLOSED - orders will execute when market opens Monday 9:30 AM ET")
                
        except Exception as e:
            console.print(f"[red]❌ Error showing pending orders: {str(e)}[/red]")
    
    def _get_pending_orders_from_db(self):
        """Get pending orders from database."""
        try:
            with self.db_service.get_session() as session:
                result = session.execute(text("""
                    SELECT symbol, transaction_type, quantity, price, created_at
                    FROM transactions 
                    WHERE user_id = :user_id AND status = 'pending'
                    ORDER BY created_at DESC
                """), {"user_id": self.current_user_id})
                
                orders = []
                for row in result.fetchall():
                    orders.append({
                        "symbol": row[0],
                        "action": row[1],
                        "quantity": float(row[2]),
                        "price": float(row[3]) if row[3] else None,
                        "created_at": row[4]
                    })
                return orders
        except Exception as e:
            console.print(f"[red]Error fetching orders: {e}[/red]")
            return []


def main():
    """Main entry point for CLI."""
    try:
        cli = InvestmentAdvisorCLI()
        cli.run()
    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
