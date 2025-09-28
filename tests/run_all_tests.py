#!/usr/bin/env python3
"""
MyFalconAdvisor Master Test Runner

Runs all test suites and provides a comprehensive system health report.
"""

import os
import sys
import warnings
import subprocess
from pathlib import Path
from datetime import datetime
import traceback

# Add the parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Suppress known warnings
warnings.filterwarnings('ignore', message='empyrical not available')
warnings.filterwarnings('ignore', message='arch package not available')
warnings.filterwarnings('ignore', message=".*'dict' object has no attribute 'lower'.*")

# Rest of the file remains unchanged...