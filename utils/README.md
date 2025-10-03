# MyFalconAdvisor Utility Scripts

This directory contains utility scripts for managing and monitoring the MyFalconAdvisor system.

## Scripts

### Portfolio Sync Management
- `start_sync.sh.disabled` - Original background sync script (disabled due to process multiplication issues)

### System Monitoring  
- `log_commands.sh` - Quick commands for monitoring log files in `/tmp/falcon/`
- `env_loader.py` - Load environment variables consistently

### Root Directory Scripts
- `../sync_now.sh` - Manual portfolio sync (recommended method)

## Portfolio Sync Usage

### Manual Sync (Recommended)
```bash
# Run manual portfolio sync anytime
cd /Users/monooprasad/Documents/MyFalconAdvisorv1
./sync_now.sh
```

### Daily Automatic Sync
- **Automatic**: Runs every weekday at 10:00 AM via cron job
- **Logs**: Check `/tmp/falcon/daily_sync.log`
- **Status**: View with `crontab -l`

### Log Monitoring
```bash
# View available log monitoring commands
./utils/log_commands.sh

# Monitor daily sync logs
tail -f /tmp/falcon/daily_sync.log
```

## Database Configuration

- **Database User**: `myfalcon_app` (secure, non-superuser)
- **Database Host**: `pg-2e1b40a1-falcon-horizon-5e1b-falccon.i.aivencloud.com`  
- **Database Name**: `defaultdb`
- **Connection**: Configured in `.env` file