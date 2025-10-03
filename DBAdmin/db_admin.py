#!/usr/bin/env python3
"""
MyFalconAdvisor Database Administration Tool

Master script for all database administration tasks.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def print_banner():
    """Print the admin tool banner."""
    print("🦅 MyFalconAdvisor Database Administration Tool")
    print("=" * 60)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def print_menu():
    """Print the main menu."""
    print("📋 Available Commands:")
    print()
    print("🔧 Configuration & Setup:")
    print("  1. configure    - Configure Aiven database connection")
    print("  2. test         - Test database connection")
    print("  3. setup        - Setup database schema")
    print()
    print("📊 Monitoring & Health:")
    print("  4. health       - Run database health monitor")
    print("  5. status       - Quick database status")
    print()
    print("💾 Backup & Maintenance:")
    print("  6. backup       - Create database backup")
    print("  7. list-backups - List existing backups")
    print("  8. cleanup      - Clean old backups")
    print()
    print("🔍 Information:")
    print("  9. tables       - List all tables")
    print("  10. size        - Show database size info")
    print("  11. help        - Show this menu")
    print()
    print("❌ Exit:")
    print("  0. exit         - Exit admin tool")
    print()

def run_script(script_name, args=None):
    """Run a database admin script."""
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_name}")
        return False
    
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Script failed with return code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Error running script: {e}")
        return False

def quick_status():
    """Show quick database status."""
    print("⚡ Quick Database Status")
    print("=" * 30)
    
    # Load environment
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
    
    # Show config
    db_host = os.getenv('DB_HOST', 'Not configured')
    db_name = os.getenv('DB_NAME', 'Not configured')
    print(f"🌐 Host: {db_host}")
    print(f"🗄️  Database: {db_name}")
    
    # Quick connection test
    try:
        import psycopg2
        
        conn_params = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'sslmode': os.getenv('DB_SSLMODE', 'require')
        }
        
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Quick checks
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
        db_size = cursor.fetchone()[0]
        
        print(f"✅ Connection: OK")
        print(f"📋 Tables: {table_count}")
        print(f"💾 Size: {db_size}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Connection: Failed ({str(e)[:50]}...)")

def list_tables():
    """List all database tables."""
    print("📋 Database Tables")
    print("=" * 30)
    
    try:
        # Load environment
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
        
        import psycopg2
        
        conn_params = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'sslmode': os.getenv('DB_SSLMODE', 'require')
        }
        
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size('public.'||tablename)) as size
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        tables = cursor.fetchall()
        
        print(f"{'Table Name':<25} {'Size':<10}")
        print("-" * 40)
        
        for table_name, size in tables:
            print(f"{table_name:<25} {size:<10}")
        
        print(f"\n📊 Total: {len(tables)} tables")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Failed to list tables: {e}")

def show_size_info():
    """Show database size information."""
    print("💾 Database Size Information")
    print("=" * 35)
    
    try:
        # Load environment
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
        
        import psycopg2
        
        conn_params = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'sslmode': os.getenv('DB_SSLMODE', 'require')
        }
        
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Database size
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
        db_size = cursor.fetchone()[0]
        print(f"🗄️  Total Database Size: {db_size}")
        
        # Top 5 largest tables
        cursor.execute("""
            SELECT 
                tablename,
                pg_size_pretty(pg_total_relation_size('public.'||tablename)) as size,
                pg_total_relation_size('public.'||tablename) as bytes
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size('public.'||tablename) DESC
            LIMIT 5
        """)
        
        tables = cursor.fetchall()
        
        print(f"\n📊 Top 5 Largest Tables:")
        print(f"{'Table':<20} {'Size':<10}")
        print("-" * 35)
        
        for table_name, size, _ in tables:
            print(f"{table_name:<20} {size:<10}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Failed to get size info: {e}")

def interactive_mode():
    """Run in interactive mode."""
    while True:
        print_menu()
        
        try:
            choice = input("👉 Enter your choice (0-11): ").strip().lower()
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        
        print()
        
        if choice in ['0', 'exit', 'quit']:
            print("👋 Goodbye!")
            break
        elif choice in ['1', 'configure']:
            run_script("configure_aiven_db.py")
        elif choice in ['2', 'test']:
            run_script("test_connection.py")
        elif choice in ['3', 'setup']:
            run_script("setup_database.sh")
        elif choice in ['4', 'health']:
            run_script("db_health_monitor.py")
        elif choice in ['5', 'status']:
            quick_status()
        elif choice in ['6', 'backup']:
            run_script("backup_database.py", ["full"])
        elif choice in ['7', 'list-backups']:
            run_script("backup_database.py", ["list"])
        elif choice in ['8', 'cleanup']:
            run_script("backup_database.py", ["cleanup"])
        elif choice in ['9', 'tables']:
            list_tables()
        elif choice in ['10', 'size']:
            show_size_info()
        elif choice in ['11', 'help']:
            continue  # Menu will be shown again
        else:
            print("❌ Invalid choice. Please try again.")
        
        print("\n" + "="*60)
        input("Press Enter to continue...")
        print()

def main():
    """Main function."""
    print_banner()
    
    if len(sys.argv) > 1:
        # Command line mode
        command = sys.argv[1].lower()
        args = sys.argv[2:] if len(sys.argv) > 2 else None
        
        if command == "configure":
            run_script("configure_aiven_db.py", args)
        elif command == "test":
            run_script("test_connection.py", args)
        elif command == "setup":
            run_script("setup_database.sh", args)
        elif command == "health":
            run_script("db_health_monitor.py", args)
        elif command == "status":
            quick_status()
        elif command == "backup":
            backup_type = args[0] if args else "full"
            run_script("backup_database.py", [backup_type])
        elif command == "list-backups":
            run_script("backup_database.py", ["list"])
        elif command == "cleanup":
            days = args[0] if args else "30"
            run_script("backup_database.py", ["cleanup", days])
        elif command == "tables":
            list_tables()
        elif command == "size":
            show_size_info()
        elif command in ["help", "-h", "--help"]:
            print_menu()
        else:
            print(f"❌ Unknown command: {command}")
            print("\n💡 Available commands:")
            print("configure, test, setup, health, status, backup, list-backups, cleanup, tables, size, help")
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
