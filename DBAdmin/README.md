# MyFalconAdvisor Database Administration

This directory contains all database setup, configuration, and administration files for MyFalconAdvisor.

## 📁 Directory Contents

### Configuration Files
- **`database_config.py`** - Database configuration and connection management
- **`all_ddls.sql`** - Complete database schema with all tables and relationships

### Setup Scripts
- **`setup_database.sh`** - Shell script to initialize the database
- **`configure_aiven_db.py`** - Interactive script to configure Aiven PostgreSQL connection
- **`update_aiven_config.py`** - Script to update .env file with Aiven credentials

## 🚀 Quick Start

### 1. Configure Database Connection

For **Aiven PostgreSQL** (recommended):
```bash
# Interactive configuration
python DBAdmin/configure_aiven_db.py

# Or update with provided credentials
python DBAdmin/update_aiven_config.py
```

### 2. Setup Database Schema

```bash
# Run the setup script
./DBAdmin/setup_database.sh

# Or manually with psql
psql -h your-host -p your-port -U your-user -d your-db -f DBAdmin/all_ddls.sql
```

### 3. Test Connection

```bash
# Quick test
python tests/test_database_connection.py

# Or full health check
python tests/quick_health_check.py
```

## 🗄️ Database Schema Overview

The MyFalconAdvisor database includes:

### Core Tables
- **`users`** - Client and user information
- **`portfolios`** - Portfolio management and allocation
- **`portfolio_assets`** - Individual holdings and positions
- **`transactions`** - Trade history and order tracking
- **`audit_trail`** - Compliance and audit logging

### Market Data Tables
- **`market_data`** - Historical and real-time market data
- **`securities`** - Security master data
- **`fundamental_data`** - Company fundamentals
- **`economic_indicators`** - Economic and macro data

### AI & Analytics Tables
- **`ai_sessions`** - AI agent conversation history
- **`ai_messages`** - Individual AI interactions
- **`recommendations`** - Investment recommendations
- **`compliance_checks`** - Compliance review results
- **`risk_profiles`** - Client risk assessments

## ⚙️ Configuration

### Environment Variables Required

```bash
# Database Connection (Aiven PostgreSQL)
DB_HOST=your-aiven-host.aivencloud.com
DB_PORT=24382
DB_NAME=myfalconadvisor_db
DB_USER=avnadmin
DB_PASSWORD=your-password
DB_SSLMODE=require

# Optional Database Settings
DB_ECHO=false                    # Set to true for SQL query logging
```

### Connection String Format
```
postgresql://user:password@host:port/database?sslmode=require
```

## 🛠️ Administration Tasks

### Database Backup
```bash
# Create backup
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < backup_file.sql
```

### Schema Updates
```bash
# Apply schema changes
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f schema_update.sql
```

### Data Migration
```bash
# Export data
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME --data-only > data_export.sql

# Import data
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < data_export.sql
```

## 🔧 Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if host/port are correct
   telnet $DB_HOST $DB_PORT
   
   # Verify SSL requirements
   psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require"
   ```

2. **Permission Denied**
   ```bash
   # Check user permissions
   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\du"
   ```

3. **SSL Certificate Issues**
   ```bash
   # Download Aiven CA certificate
   wget https://console.aiven.io/static/ca.pem
   
   # Use with connection
   psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require&sslcert=client-cert.pem&sslkey=client-key.pem&sslrootcert=ca.pem"
   ```

### Diagnostic Commands

```bash
# Test basic connectivity
python -c "
from DBAdmin.database_config import get_database_connection
conn = get_database_connection()
print('✅ Connection successful' if conn else '❌ Connection failed')
"

# Check table existence
python -c "
import psycopg2
import os
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'), 
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    sslmode=os.getenv('DB_SSLMODE', 'require')
)
cur = conn.cursor()
cur.execute(\"SELECT tablename FROM pg_tables WHERE schemaname = 'public'\")
tables = cur.fetchall()
print(f'Found {len(tables)} tables: {[t[0] for t in tables]}')
"
```

## 📊 Monitoring

### Database Health Checks
- **Connection pooling** - Monitor active connections
- **Query performance** - Track slow queries
- **Storage usage** - Monitor disk space
- **Backup status** - Verify regular backups

### Performance Metrics
- Query execution times
- Index usage statistics
- Lock contention
- Connection counts

## 🔒 Security

### Best Practices
1. **Use SSL/TLS** for all connections
2. **Rotate passwords** regularly
3. **Limit user permissions** to minimum required
4. **Monitor access logs** for suspicious activity
5. **Keep backups encrypted** and secure

### Access Control
- Production database access should be limited
- Use read-only users for reporting
- Implement IP whitelisting when possible
- Use connection pooling for application access

## 📈 Scaling Considerations

### Performance Optimization
- **Indexing strategy** - Create appropriate indexes
- **Query optimization** - Use EXPLAIN ANALYZE
- **Connection pooling** - Use pgbouncer or similar
- **Read replicas** - For read-heavy workloads

### Capacity Planning
- Monitor storage growth
- Plan for increased connection counts
- Consider partitioning for large tables
- Implement archiving for old data
