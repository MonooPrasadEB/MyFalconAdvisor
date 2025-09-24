#!/usr/bin/env python3
"""
Simple Chat Functionality Test

Tests the MyFalconAdvisor chat/conversation capabilities with sample questions.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

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

def test_basic_chat():
    """Test basic chat functionality."""
    print("💬 Testing Basic Chat Functionality")
    print("=" * 50)
    
    try:
        from myfalconadvisor.core.supervisor import investment_advisor_supervisor
        
        # Test questions
        test_questions = [
            "What are the current market trends?",
            "Should I invest in technology stocks?",
            "How should I diversify my portfolio?",
            "What's your opinion on Apple stock?",
            "Is now a good time to buy bonds?"
        ]
        
        # Sample client profile
        client_profile = {
            "age": 35,
            "risk_tolerance": "moderate",
            "investment_experience": "intermediate",
            "time_horizon": "long_term",
            "annual_income": 100000
        }
        
        print(f"🤖 Testing {len(test_questions)} sample questions...")
        print(f"👤 Client Profile: {client_profile['age']} years old, {client_profile['risk_tolerance']} risk tolerance")
        print()
        
        successful_responses = 0
        
        for i, question in enumerate(test_questions, 1):
            print(f"❓ Question {i}: {question}")
            
            try:
                # Process the request
                result = investment_advisor_supervisor.process_client_request(
                    request=question,
                    client_profile=client_profile
                )
                
                if result and "response" in result:
                    response = result["response"]
                    print(f"✅ Response received ({len(response)} characters)")
                    print(f"📝 Preview: {response[:100]}...")
                    successful_responses += 1
                else:
                    print(f"❌ No response received: {result}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("-" * 50)
        
        success_rate = (successful_responses / len(test_questions)) * 100
        print(f"\n📊 Chat Test Results:")
        print(f"✅ Successful responses: {successful_responses}/{len(test_questions)}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        return successful_responses > 0
        
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        return False

def test_portfolio_chat():
    """Test chat with portfolio context."""
    print("\n💼 Testing Portfolio-Specific Chat")
    print("=" * 50)
    
    try:
        from myfalconadvisor.core.supervisor import investment_advisor_supervisor
        
        # Sample portfolio
        portfolio_data = {
            "AAPL": {"quantity": 10, "current_price": 250.0, "market_value": 2500.0},
            "MSFT": {"quantity": 5, "current_price": 500.0, "market_value": 2500.0},
            "SPY": {"quantity": 20, "current_price": 660.0, "market_value": 13200.0},
            "total_value": 18200.0
        }
        
        client_profile = {
            "age": 40,
            "risk_tolerance": "moderate",
            "investment_experience": "advanced"
        }
        
        # Portfolio-specific questions
        portfolio_questions = [
            "How is my portfolio performing?",
            "Should I rebalance my holdings?",
            "Is my Apple position too large?",
            "What do you think about my SPY allocation?"
        ]
        
        print(f"💼 Portfolio: AAPL (10 shares), MSFT (5 shares), SPY (20 shares)")
        print(f"💰 Total Value: ${portfolio_data['total_value']:,.2f}")
        print()
        
        successful_responses = 0
        
        for i, question in enumerate(portfolio_questions, 1):
            print(f"❓ Question {i}: {question}")
            
            try:
                result = investment_advisor_supervisor.process_client_request(
                    request=question,
                    client_profile=client_profile,
                    portfolio_data=portfolio_data
                )
                
                if result and "response" in result:
                    response = result["response"]
                    print(f"✅ Response received ({len(response)} characters)")
                    print(f"📝 Preview: {response[:100]}...")
                    successful_responses += 1
                else:
                    print(f"❌ No response: {result}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("-" * 50)
        
        success_rate = (successful_responses / len(portfolio_questions)) * 100
        print(f"\n📊 Portfolio Chat Results:")
        print(f"✅ Successful responses: {successful_responses}/{len(portfolio_questions)}")
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        return successful_responses > 0
        
    except Exception as e:
        print(f"❌ Portfolio chat test failed: {e}")
        return False

def main():
    """Run chat functionality tests."""
    print("🧪 MyFalconAdvisor Chat Functionality Test")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment
    load_env()
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OpenAI API key not found. Chat functionality requires OpenAI API access.")
        return False
    
    print(f"🤖 OpenAI API Key: {'Configured' if openai_key else 'Missing'}")
    
    # Run tests
    tests = [
        ("Basic Chat", test_basic_chat),
        ("Portfolio Chat", test_portfolio_chat)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("🏁 CHAT FUNCTIONALITY TEST RESULTS")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n🎯 Chat Score: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 Chat functionality is fully operational!")
        print("💬 MyFalconAdvisor is ready for client conversations!")
    elif passed > 0:
        print("👍 Chat functionality is mostly working.")
        print("🔧 Some features may need fine-tuning.")
    else:
        print("❌ Chat functionality needs attention.")
        print("🔍 Check API keys and configuration.")
    
    print(f"\n🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
