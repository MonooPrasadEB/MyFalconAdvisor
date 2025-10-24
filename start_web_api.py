#!/usr/bin/env python3
"""
Startup script for MyFalconAdvisor Web API

This script starts the integrated web API that connects the MyFalconAdvisor backend
with the React frontend.
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def main():
    """Start the web API server"""
    print("🚀 Starting MyFalconAdvisor Web API Integration")
    print("=" * 60)
    
    # Load environment variables from .env file
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Loaded environment variables from .env")
    else:
        print("⚠️  No .env file found, using environment defaults")
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    print(f"📁 Working directory: {current_dir}")
    print(f"🐍 Python path: {sys.path[0]}")
    
    # Start the web API
    try:
        import uvicorn
        print("\n🌐 Starting FastAPI server on http://127.0.0.1:8000")
        print("📚 API Documentation: http://127.0.0.1:8000/docs")
        print("🔄 Frontend should connect to: http://127.0.0.1:8000")
        print("\n" + "=" * 60)
        
        uvicorn.run(
            "web_api:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError:
        print("❌ uvicorn not found. Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "python-multipart"])
        
        print("🔄 Retrying server start...")
        import uvicorn
        uvicorn.run(
            "web_api:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
