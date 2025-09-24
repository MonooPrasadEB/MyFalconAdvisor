#!/usr/bin/env python3
"""
Database Backup Utility

Creates backups of the MyFalconAdvisor database with proper naming and compression.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import gzip
import shutil

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

def create_backup(backup_type="full", compress=True):
    """Create database backup."""
    print(f"🗄️  Creating {backup_type} database backup...")
    
    # Get database connection info
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    
    if not all([db_host, db_port, db_name, db_user, db_password]):
        print("❌ Missing database configuration. Check your .env file.")
        return False
    
    # Create backup directory
    backup_dir = Path(__file__).parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    # Generate backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"myfalconadvisor_{backup_type}_{timestamp}.sql"
    backup_path = backup_dir / backup_filename
    
    try:
        # Set environment for pg_dump
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        # Build pg_dump command
        cmd = [
            'pg_dump',
            '-h', db_host,
            '-p', str(db_port),
            '-U', db_user,
            '-d', db_name,
            '--verbose',
            '--no-password'
        ]
        
        # Add backup type specific options
        if backup_type == "schema":
            cmd.extend(['--schema-only'])
        elif backup_type == "data":
            cmd.extend(['--data-only'])
        # 'full' backup uses default (schema + data)
        
        print(f"🔄 Running: {' '.join(cmd[:-2])} [password hidden]")
        print(f"📁 Output: {backup_path}")
        
        # Run pg_dump
        with open(backup_path, 'w') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                timeout=300  # 5 minute timeout
            )
        
        if result.returncode == 0:
            print(f"✅ Backup created successfully: {backup_path}")
            
            # Get file size
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            print(f"📊 Backup size: {size_mb:.2f} MB")
            
            # Compress if requested
            if compress:
                compressed_path = backup_path.with_suffix(backup_path.suffix + '.gz')
                print(f"🗜️  Compressing backup...")
                
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove uncompressed file
                backup_path.unlink()
                
                # Get compressed size
                compressed_size_mb = compressed_path.stat().st_size / (1024 * 1024)
                compression_ratio = (1 - compressed_size_mb / size_mb) * 100
                
                print(f"✅ Backup compressed: {compressed_path}")
                print(f"📊 Compressed size: {compressed_size_mb:.2f} MB ({compression_ratio:.1f}% reduction)")
                
                return compressed_path
            else:
                return backup_path
                
        else:
            print(f"❌ Backup failed with return code {result.returncode}")
            print(f"🔍 Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Backup timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def list_backups():
    """List existing backups."""
    backup_dir = Path(__file__).parent / "backups"
    
    if not backup_dir.exists():
        print("📁 No backup directory found")
        return
    
    backups = list(backup_dir.glob("myfalconadvisor_*.sql*"))
    
    if not backups:
        print("📁 No backups found")
        return
    
    print(f"📋 Found {len(backups)} backup(s):")
    print("=" * 70)
    
    # Sort by creation time (newest first)
    backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    for backup in backups:
        stat = backup.stat()
        size_mb = stat.st_size / (1024 * 1024)
        created = datetime.fromtimestamp(stat.st_mtime)
        
        # Parse backup type from filename
        name_parts = backup.stem.replace('.sql', '').split('_')
        backup_type = name_parts[1] if len(name_parts) > 2 else 'unknown'
        
        print(f"📄 {backup.name}")
        print(f"   📊 Size: {size_mb:.2f} MB")
        print(f"   📅 Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   🏷️  Type: {backup_type}")
        print()

def cleanup_old_backups(keep_days=30):
    """Remove backups older than specified days."""
    backup_dir = Path(__file__).parent / "backups"
    
    if not backup_dir.exists():
        return
    
    cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
    backups = list(backup_dir.glob("myfalconadvisor_*.sql*"))
    
    removed_count = 0
    for backup in backups:
        if backup.stat().st_mtime < cutoff_time:
            print(f"🗑️  Removing old backup: {backup.name}")
            backup.unlink()
            removed_count += 1
    
    if removed_count > 0:
        print(f"✅ Removed {removed_count} old backup(s)")
    else:
        print(f"✅ No backups older than {keep_days} days found")

def main():
    """Main backup utility."""
    print("🗄️  MyFalconAdvisor Database Backup Utility")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment
    load_env()
    
    # Show current configuration
    db_host = os.getenv('DB_HOST', 'Not set')
    db_name = os.getenv('DB_NAME', 'Not set')
    print(f"🌐 Database: {db_host}/{db_name}")
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "list":
            list_backups()
        elif command == "cleanup":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            cleanup_old_backups(days)
        elif command in ["full", "schema", "data"]:
            compress = "--no-compress" not in sys.argv
            result = create_backup(command, compress)
            if result:
                print(f"🎉 Backup completed successfully!")
            else:
                print(f"❌ Backup failed!")
                sys.exit(1)
        else:
            print(f"❌ Unknown command: {command}")
            print_usage()
            sys.exit(1)
    else:
        # Default: create full backup
        result = create_backup("full", True)
        if result:
            print(f"🎉 Full backup completed successfully!")
        else:
            print(f"❌ Backup failed!")
            sys.exit(1)

def print_usage():
    """Print usage information."""
    print("\n💡 Usage:")
    print("  python DBAdmin/backup_database.py [command] [options]")
    print("\n📋 Commands:")
    print("  full      - Create full backup (schema + data) [default]")
    print("  schema    - Create schema-only backup")
    print("  data      - Create data-only backup")
    print("  list      - List existing backups")
    print("  cleanup   - Remove old backups (default: 30 days)")
    print("\n🔧 Options:")
    print("  --no-compress  - Skip compression")
    print("\n📝 Examples:")
    print("  python DBAdmin/backup_database.py full")
    print("  python DBAdmin/backup_database.py schema --no-compress")
    print("  python DBAdmin/backup_database.py list")
    print("  python DBAdmin/backup_database.py cleanup 7")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help", "help"]:
        print_usage()
    else:
        main()
