#!/usr/bin/env python3
"""
Quick utility functions for database connection management.
Run these functions directly when needed - no background processes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from myfalconadvisor.tools.database_service import database_service


def check_pool_status():
    """Check current pool status."""
    status = database_service.get_pool_status()
    print(f"Pool Status: {status}")
    return status


def cleanup_idle():
    """Close idle connections now."""
    database_service.close_idle_connections()
    print("✓ Idle connections closed")


def dispose_pool():
    """Dispose entire connection pool."""
    database_service.dispose()
    print("✓ Connection pool disposed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database connection utilities")
    parser.add_argument("action", choices=["status", "cleanup", "dispose"])
    args = parser.parse_args()
    
    if args.action == "status":
        check_pool_status()
    elif args.action == "cleanup":
        cleanup_idle()
    elif args.action == "dispose":
        dispose_pool()

