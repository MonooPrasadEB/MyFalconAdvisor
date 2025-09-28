#!/bin/bash
# MyFalconAdvisor Log Monitoring Commands
# Simple manual commands to monitor service logs

echo "📊 MyFalconAdvisor Log Monitoring Commands"
echo "=========================================="
echo ""

# Check if logs directory exists
if [ ! -d "../logs" ]; then
    echo "📁 Creating logs directory..."
    mkdir -p ../logs
fi

echo "🔍 Individual Service Logs:"
echo "  tail -f ../logs/multi_task_agent.log     # AI recommendations & analysis"
echo "  tail -f ../logs/execution_agent.log      # Trade execution & validation"
echo "  tail -f ../logs/portfolio_sync.log       # Background sync service"
echo "  tail -f ../logs/alpaca_trading.log       # Alpaca API interactions"
echo "  tail -f ../logs/database_service.log     # Database operations"
echo "  tail -f ../logs/chat_logger.log          # User interactions"
echo "  tail -f ../logs/compliance_checker.log   # Compliance checks"
echo "  tail -f ../logs/system.log               # System events"
echo ""

echo "📊 Monitor All Logs Together:"
echo "  tail -f ../logs/*.log"
echo ""

echo "🔍 Search Logs:"
echo "  grep -r 'ERROR' ../logs/                 # Find all errors"
echo "  grep -r 'trade' ../logs/                 # Find trade-related logs"
echo "  grep -r 'user_id' ../logs/               # Find user activity"
echo "  grep -r 'recommendation' ../logs/        # Find AI recommendations"
echo ""

echo "📈 Log Statistics:"
echo "  ls -lh ../logs/                          # Show log file sizes"
echo "  wc -l ../logs/*.log                      # Count lines in each log"
echo "  du -sh ../logs/                          # Total log directory size"
echo ""

echo "🧹 Clear Logs (if needed):"
echo "  > ../logs/multi_task_agent.log           # Clear specific log"
echo "  rm ../logs/*.log                         # Remove all logs"
echo ""

echo "💡 Most Useful Commands:"
echo "  # Monitor execution agent (trade activity)"
echo "  tail -f ../logs/execution_agent.log"
echo ""
echo "  # Monitor portfolio sync (background updates)"
echo "  tail -f ../logs/portfolio_sync.log"
echo ""
echo "  # Monitor all critical services"
echo "  tail -f ../logs/execution_agent.log ../logs/portfolio_sync.log ../logs/alpaca_trading.log"
echo ""

echo "🚀 To start monitoring now:"
echo "  cd /Users/monooprasad/Documents/MyFalconAdvisorv1"
echo "  tail -f logs/execution_agent.log"
