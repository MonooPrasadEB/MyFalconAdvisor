#!/bin/bash

# MyFalconAdvisor Database Setup Script for Aiven PostgreSQL
# This script will:
# 1. Connect to your Aiven PostgreSQL instance
# 2. Create the myfalconadvisor_db database
# 3. Create a team user with appropriate permissions
# 4. Run the database schema

echo "🚀 MyFalconAdvisor Database Setup"
echo "=================================="

# Database connection details
DB_HOST="pg-2e1b40a1-falcon-horizon-5e1b-falccon.i.aivencloud.com"
DB_PORT="24382"
DB_USER="avnadmin"
DB_NAME="defaultdb"
SSL_MODE="require"

# New database and user details
NEW_DB_NAME="myfalconadvisor_db"
TEAM_USER="myfalcon_team"

echo "📋 Connection Details:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"
echo "  SSL Mode: $SSL_MODE"
echo ""

# Function to run SQL command
run_sql() {
    local sql_command="$1"
    local db_name="${2:-$DB_NAME}"
    
    echo "🔧 Executing: $sql_command"
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$db_name" \
        -c "$sql_command" \
        --set=sslmode="$SSL_MODE"
}

# Check if password is provided
if [ -z "$DB_PASSWORD" ]; then
    echo "❌ Please set the DB_PASSWORD environment variable"
    echo "   Example: export DB_PASSWORD='your_password_here'"
    echo "   Then run: ./setup_database.sh"
    exit 1
fi

echo "🔍 Testing connection to Aiven PostgreSQL..."
if ! PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -c "SELECT version();" \
    --set=sslmode="$SSL_MODE" > /dev/null 2>&1; then
    echo "❌ Failed to connect to PostgreSQL. Please check your credentials."
    exit 1
fi

echo "✅ Successfully connected to PostgreSQL!"
echo ""

# Step 1: Create the new database
echo "📊 Step 1: Creating database '$NEW_DB_NAME'..."
run_sql "CREATE DATABASE $NEW_DB_NAME;" || echo "⚠️  Database might already exist"

# Step 2: Create team user
echo "👥 Step 2: Creating team user '$TEAM_USER'..."
echo "Please enter a password for the team user:"
read -s TEAM_PASSWORD

if [ -z "$TEAM_PASSWORD" ]; then
    echo "❌ Team password cannot be empty"
    exit 1
fi

run_sql "CREATE USER $TEAM_USER WITH PASSWORD '$TEAM_PASSWORD';" || echo "⚠️  User might already exist"

# Step 3: Grant permissions to team user
echo "🔐 Step 3: Granting permissions to team user..."
run_sql "GRANT CONNECT ON DATABASE $NEW_DB_NAME TO $TEAM_USER;"
run_sql "GRANT USAGE ON SCHEMA public TO $TEAM_USER;" "$NEW_DB_NAME"
run_sql "GRANT CREATE ON SCHEMA public TO $TEAM_USER;" "$NEW_DB_NAME"

# Step 4: Run the database schema
echo "🏗️  Step 4: Creating database schema..."
if [ -f "database_schema.sql" ]; then
    echo "📄 Running database_schema.sql..."
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$NEW_DB_NAME" \
        -f "database_schema.sql" \
        --set=sslmode="$SSL_MODE"
    
    if [ $? -eq 0 ]; then
        echo "✅ Database schema created successfully!"
    else
        echo "❌ Failed to create database schema"
        exit 1
    fi
else
    echo "❌ database_schema.sql not found in current directory"
    exit 1
fi

# Step 5: Grant permissions on all tables to team user
echo "🔑 Step 5: Granting table permissions to team user..."
run_sql "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO $TEAM_USER;" "$NEW_DB_NAME"
run_sql "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO $TEAM_USER;" "$NEW_DB_NAME"

# Step 6: Set default privileges for future tables
echo "🔮 Step 6: Setting default privileges for future objects..."
run_sql "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $TEAM_USER;" "$NEW_DB_NAME"
run_sql "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO $TEAM_USER;" "$NEW_DB_NAME"

echo ""
echo "🎉 Database setup completed successfully!"
echo "=================================="
echo "📊 Database: $NEW_DB_NAME"
echo "👤 Team User: $TEAM_USER"
echo "🔗 Connection String for your app:"
echo "   postgres://$TEAM_USER:$TEAM_PASSWORD@$DB_HOST:$DB_PORT/$NEW_DB_NAME?sslmode=$SSL_MODE"
echo ""
echo "💡 Next steps:"
echo "   1. Update your .env file with the connection details"
echo "   2. Install required Python packages: pip install psycopg2-binary sqlalchemy"
echo "   3. Test the connection from your MyFalconAdvisor app"
echo ""
