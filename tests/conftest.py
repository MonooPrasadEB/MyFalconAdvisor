"""
Pytest configuration for MyFalconAdvisor test suite.

This file is automatically loaded by pytest and applies global configurations
including warning suppression for cleaner test output.
"""

import warnings

# Suppress all common warnings for cleaner test output
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*Pydantic.*')
warnings.filterwarnings('ignore', message='.*datetime.utcnow.*')
warnings.filterwarnings('ignore', message='.*empyrical.*')
warnings.filterwarnings('ignore', message='.*arch package.*')
warnings.filterwarnings('ignore', message='.*Field.*')
warnings.filterwarnings('ignore', message=".*'dict' object has no attribute 'lower'.*")

