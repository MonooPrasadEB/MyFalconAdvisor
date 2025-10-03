#!/bin/bash

echo "🔄 MyFalconAdvisor Portfolio Sync"
echo "================================="

cd /Users/monooprasad/Documents/MyFalconAdvisorv1
source venv/bin/activate

python -c "
from myfalconadvisor.tools.portfolio_sync_service import portfolio_sync_service
import time

print('⏳ Running portfolio sync...')
result = portfolio_sync_service.sync_user_now('usr_348784c4-6f83-4857-b7dc-f5132a38dfee')

if result.get('success'):
    print('✅ Sync completed successfully!')
    print(f'📊 {result[\"message\"]}')
    for portfolio in result.get('portfolios', []):
        print(f'   • {portfolio[\"portfolio_name\"]}: {portfolio[\"status\"]}')
else:
    print('❌ Sync failed:', result.get('error', 'Unknown error'))

print(f'🕐 Completed at: {time.strftime(\"%Y-%m-%d %H:%M:%S\")}')
"

echo "✅ Manual sync complete!"
