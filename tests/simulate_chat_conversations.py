#!/usr/bin/env python3
"""
Chat Conversation Simulator

Simulates realistic client conversations with MyFalconAdvisor to populate
the database with sample chat data for testing and demonstration.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import time
import random

# Add the parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    try:
                        key, value = line.strip().split("=", 1)
                        os.environ[key] = value
                    except ValueError:
                        continue

def simulate_client_conversation(client_name, client_type, questions):
    """Simulate a complete client conversation."""
    print(f"\n🤖 Simulating conversation with {client_name} ({client_type})")
    print("=" * 60)
    
    try:
        from myfalconadvisor.core.supervisor import investment_advisor_supervisor
        
        # Create client profile based on type
        client_profiles = {
            "conservative": {
                "age": 55,
                "risk_tolerance": "conservative", 
                "investment_experience": "beginner",
                "time_horizon": "short_term",
                "annual_income": 75000
            },
            "moderate": {
                "age": 35,
                "risk_tolerance": "moderate",
                "investment_experience": "intermediate", 
                "time_horizon": "long_term",
                "annual_income": 100000
            },
            "aggressive": {
                "age": 28,
                "risk_tolerance": "aggressive",
                "investment_experience": "advanced",
                "time_horizon": "long_term", 
                "annual_income": 150000
            }
        }
        
        client_profile = client_profiles.get(client_type, client_profiles["moderate"])
        
        # Sample portfolios based on risk type
        portfolios = {
            "conservative": {
                "BND": {"quantity": 100, "current_price": 75.50, "market_value": 7550.0},
                "VTI": {"quantity": 50, "current_price": 280.0, "market_value": 14000.0},
                "SPY": {"quantity": 20, "current_price": 660.0, "market_value": 13200.0},
                "total_value": 34750.0
            },
            "moderate": {
                "AAPL": {"quantity": 10, "current_price": 250.0, "market_value": 2500.0},
                "MSFT": {"quantity": 8, "current_price": 500.0, "market_value": 4000.0},
                "SPY": {"quantity": 30, "current_price": 660.0, "market_value": 19800.0},
                "VTI": {"quantity": 25, "current_price": 280.0, "market_value": 7000.0},
                "total_value": 33300.0
            },
            "aggressive": {
                "NVDA": {"quantity": 15, "current_price": 800.0, "market_value": 12000.0},
                "TSLA": {"quantity": 20, "current_price": 300.0, "market_value": 6000.0},
                "AAPL": {"quantity": 25, "current_price": 250.0, "market_value": 6250.0},
                "QQQ": {"quantity": 40, "current_price": 450.0, "market_value": 18000.0},
                "total_value": 42250.0
            }
        }
        
        portfolio_data = portfolios.get(client_type, portfolios["moderate"])
        
        successful_interactions = 0
        
        for i, question in enumerate(questions, 1):
            print(f"\n💬 Question {i}: {question}")
            
            try:
                # Add small delay to simulate realistic conversation timing
                time.sleep(random.uniform(1, 3))
                
                # Process the client request
                result = investment_advisor_supervisor.process_client_request(
                    request=question,
                    client_profile=client_profile,
                    portfolio_data=portfolio_data
                )
                
                if result and "response" in result:
                    response = result["response"]
                    print(f"✅ Response generated ({len(response)} characters)")
                    print(f"📝 Preview: {response[:120]}...")
                    successful_interactions += 1
                    
                    # Add delay before next question
                    time.sleep(random.uniform(0.5, 2))
                    
                else:
                    print(f"❌ No response received: {result}")
                
            except Exception as e:
                print(f"❌ Error processing question: {e}")
        
        success_rate = (successful_interactions / len(questions)) * 100
        print(f"\n📊 Conversation Summary for {client_name}:")
        print(f"   ✅ Successful interactions: {successful_interactions}/{len(questions)}")
        print(f"   📈 Success rate: {success_rate:.1f}%")
        print(f"   👤 Client Type: {client_type}")
        print(f"   💼 Portfolio Value: ${portfolio_data['total_value']:,.2f}")
        
        return successful_interactions > 0
        
    except Exception as e:
        print(f"❌ Conversation simulation failed: {e}")
        return False

def main():
    """Run chat conversation simulations."""
    print("🎭 MyFalconAdvisor Chat Conversation Simulator")
    print("=" * 70)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment
    load_env()
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OpenAI API key not found. Chat simulation requires OpenAI API access.")
        return False
    
    print(f"🤖 OpenAI API Key: {'Configured' if openai_key else 'Missing'}")
    
    # Define different client scenarios
    client_scenarios = [
        {
            "name": "Sarah Johnson",
            "type": "conservative", 
            "questions": [
                "I'm 55 and nearing retirement. How should I protect my savings?",
                "Is my portfolio too risky for someone my age?",
                "Should I move more money into bonds?",
                "What's a safe withdrawal rate for retirement?",
                "How do I protect against inflation in retirement?"
            ]
        },
        {
            "name": "Mike Chen", 
            "type": "moderate",
            "questions": [
                "I'm 35 with a moderate risk tolerance. How's my portfolio balance?",
                "Should I increase my tech allocation?", 
                "What's your opinion on my Apple and Microsoft holdings?",
                "How should I prepare for my kids' college expenses?",
                "Is now a good time to rebalance my portfolio?"
            ]
        },
        {
            "name": "Alex Rodriguez",
            "type": "aggressive", 
            "questions": [
                "I'm young and want aggressive growth. How's my portfolio?",
                "Should I buy more NVIDIA with the AI boom?",
                "What do you think about Tesla's future prospects?",
                "I want to maximize returns - any suggestions?",
                "Should I consider options trading with my risk tolerance?"
            ]
        },
        {
            "name": "Jennifer Liu",
            "type": "moderate",
            "questions": [
                "I just got a promotion and have extra income to invest.",
                "How should I diversify beyond just US stocks?",
                "What's your take on international markets?",
                "Should I consider ESG investing?",
                "How do I balance growth and income in my portfolio?"
            ]
        },
        {
            "name": "Robert Taylor",
            "type": "conservative",
            "questions": [
                "I'm worried about market volatility. What should I do?",
                "Are my bond investments safe in rising rate environment?",
                "Should I keep more cash on the sidelines?",
                "How do I prepare for the next market downturn?",
                "What's your outlook on dividend stocks?"
            ]
        }
    ]
    
    # Run simulations
    results = []
    total_interactions = 0
    
    for scenario in client_scenarios:
        try:
            print(f"\n{'='*70}")
            result = simulate_client_conversation(
                scenario["name"], 
                scenario["type"], 
                scenario["questions"]
            )
            results.append((scenario["name"], result))
            total_interactions += len(scenario["questions"])
            
            # Pause between clients
            time.sleep(random.uniform(2, 5))
            
        except Exception as e:
            print(f"💥 Simulation crashed for {scenario['name']}: {e}")
            results.append((scenario["name"], False))
    
    # Final Summary
    print(f"\n{'='*70}")
    print("🏁 CHAT SIMULATION RESULTS")
    print(f"{'='*70}")
    
    passed = sum(1 for _, result in results if result)
    total_clients = len(results)
    
    for client_name, result in results:
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{client_name:.<35} {status}")
    
    print(f"\n🎯 Simulation Summary:")
    print(f"   👥 Clients simulated: {passed}/{total_clients}")
    print(f"   💬 Total questions asked: {total_interactions}")
    print(f"   📈 Success rate: {passed/total_clients*100:.1f}%")
    
    if passed == total_clients:
        print("🎉 All client conversations simulated successfully!")
        print("💾 Check your database for the new chat interaction data!")
    elif passed > 0:
        print("👍 Most conversations simulated successfully.")
        print("🔍 Check failed simulations above.")
    else:
        print("❌ All simulations failed. Check configuration.")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n💡 To review the chat data in your database:")
    print(f"   python DBAdmin/db_admin.py")
    print(f"   # Or run: psql -f DBAdmin/review_chat_interactions.sql")
    
    return passed == total_clients

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
