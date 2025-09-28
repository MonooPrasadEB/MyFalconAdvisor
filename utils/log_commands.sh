#!/bin/bash
# MyFalconAdvisor Log Monitoring Commands
# Simple manual commands to monitor service logs

echo "📊 MyFalconAdvisor Log Monitoring Commands"
echo "=========================================="
echo ""

# Check if logs directory exists
if [ ! -d "/tmp/falcon" ]; then
    echo "📁 Creating logs directory..."
    mkdir -p /tmp/falcon
fi

echo "🔍 Individual Service Logs:"
echo "  tail -f /tmp/falcon/multi_task_agent.log     # AI recommendations & analysis"
echo "  tail -f /tmp/falcon/execution_agent.log      # Trade execution & validation"
echo "  tail -f /tmp/falcon/portfolio_sync.log       # Background sync service"
echo "  tail -f /tmp/falcon/alpaca_trading.log       # Alpaca API interactions"
echo "  tail -f /tmp/falcon/database_service.log     # Database operations"
echo "  tail -f /tmp/falcon/chat_logger.log          # User interactions"
echo "  tail -f /tmp/falcon/compliance_checker.log   # Compliance checks"
echo "  tail -f /tmp/falcon/system.log               # System events"
echo ""

echo "📊 Monitor All Logs Together:"
echo "  tail -f /tmp/falcon/*.log"
echo ""

echo "🔍 Search Logs:"
echo "  grep -r 'ERROR' /tmp/falcon/                 # Find all errors"
echo "  grep -r 'trade' /tmp/falcon/                 # Find trade-related logs"
echo "  grep -r 'user_id' /tmp/falcon/               # Find user activity"
echo "  grep -r 'recommendation' /tmp/falcon/        # Find AI recommendations"
echo ""

echo "📈 Log Statistics:"
echo "  ls -lh /tmp/falcon/                          # Show log file sizes"
echo "  wc -l /tmp/falcon/*.log                      # Count lines in each log"
echo "  du -sh /tmp/falcon/                          # Total log directory size"
echo ""

echo "🧹 Clear Logs (if needed):"
echo "  > /tmp/falcon/multi_task_agent.log           # Clear specific log"
echo "  rm /tmp/falcon/*.log                         # Remove all logs"
echo ""

echo "💡 Most Useful Commands:"
echo "  # Monitor execution agent (trade activity)"
echo "  tail -f /tmp/falcon/execution_agent.log"
echo ""
echo "  # Monitor portfolio sync (background updates)"
echo "  tail -f /tmp/falcon/portfolio_sync.log"
echo ""
echo "  # Monitor all critical services"
echo "  tail -f /tmp/falcon/execution_agent.log /tmp/falcon/portfolio_sync.log /tmp/falcon/alpaca_trading.log"
echo ""

echo "🚀 To start monitoring now:"
echo "  tail -f /tmp/falcon/execution_agent.log"
