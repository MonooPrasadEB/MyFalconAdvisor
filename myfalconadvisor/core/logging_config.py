"""
Centralized Logging Configuration for MyFalconAdvisor

This module sets up dedicated log files for each critical service:
- Multi-Task Agent (AI recommendations and analysis)
- Execution Agent (trade execution and validation)
- Portfolio Sync Service (background synchronization)
- Alpaca Trading Service (API interactions)
- Database Service (database operations)
- Chat Logger (user interactions)
- Compliance Checker (compliance validations)

Each service gets its own log file with rotation and proper formatting.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from .config import Config

config = Config.get_instance()

class ServiceLogger:
    """Centralized logging configuration for all MyFalconAdvisor services."""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration for all services."""
        # Base logging configuration
        log_level = getattr(logging, config.log_level.upper(), logging.INFO)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Service configurations
        services = {
            'multi_task_agent': {
                'filename': 'multi_task_agent.log',
                'description': 'AI recommendations, portfolio analysis, risk assessment',
                'formatter': detailed_formatter,
                'level': log_level
            },
            'execution_agent': {
                'filename': 'execution_agent.log', 
                'description': 'Trade execution, validation, order management',
                'formatter': detailed_formatter,
                'level': log_level
            },
            'portfolio_sync': {
                'filename': 'portfolio_sync.log',
                'description': 'Background sync, Alpaca monitoring, portfolio updates',
                'formatter': detailed_formatter,
                'level': log_level
            },
            'alpaca_trading': {
                'filename': 'alpaca_trading.log',
                'description': 'Alpaca API calls, market data, order placement',
                'formatter': detailed_formatter,
                'level': log_level
            },
            'database_service': {
                'filename': 'database_service.log',
                'description': 'Database operations, transactions, portfolio data',
                'formatter': detailed_formatter,
                'level': log_level
            },
            'chat_logger': {
                'filename': 'chat_logger.log',
                'description': 'User interactions, AI sessions, chat history',
                'formatter': simple_formatter,
                'level': log_level
            },
            'compliance_checker': {
                'filename': 'compliance_checker.log',
                'description': 'Compliance validations, risk checks, regulatory',
                'formatter': detailed_formatter,
                'level': log_level
            },
            'system': {
                'filename': 'system.log',
                'description': 'System-wide events, startup, configuration',
                'formatter': detailed_formatter,
                'level': log_level
            }
        }
        
        # Create loggers for each service
        for service_name, config_dict in services.items():
            logger = self._create_service_logger(
                service_name,
                config_dict['filename'],
                config_dict['formatter'],
                config_dict['level']
            )
            self.loggers[service_name] = logger
            
        # Log startup information
        system_logger = self.get_logger('system')
        system_logger.info("=" * 80)
        system_logger.info("MyFalconAdvisor Logging System Initialized")
        system_logger.info(f"Log Directory: {self.log_dir.absolute()}")
        system_logger.info(f"Log Level: {config.log_level}")
        system_logger.info("Service Log Files:")
        for service_name, config_dict in services.items():
            system_logger.info(f"  • {service_name}: {config_dict['filename']} - {config_dict['description']}")
        system_logger.info("=" * 80)
    
    def _create_service_logger(self, service_name: str, filename: str, 
                             formatter: logging.Formatter, level: int) -> logging.Logger:
        """Create a logger for a specific service with file rotation."""
        logger = logging.getLogger(f"myfalconadvisor.{service_name}")
        logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # File handler with rotation (10MB max, keep 5 files)
        log_file = self.log_dir / filename
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
        
        # Console handler for errors and warnings
        if level <= logging.WARNING:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.WARNING)
            logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        return logger
    
    def get_logger(self, service_name: str) -> logging.Logger:
        """Get logger for a specific service."""
        if service_name not in self.loggers:
            # Create a default logger if service not configured
            return self._create_service_logger(
                service_name,
                f"{service_name}.log",
                logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s'),
                logging.INFO
            )
        return self.loggers[service_name]
    
    def log_service_startup(self, service_name: str, details: Optional[Dict] = None):
        """Log service startup with optional details."""
        logger = self.get_logger(service_name)
        logger.info(f"🚀 {service_name.replace('_', ' ').title()} Service Starting")
        if details:
            for key, value in details.items():
                logger.info(f"   {key}: {value}")
        logger.info(f"📝 Logging to: logs/{service_name}.log")
    
    def log_service_shutdown(self, service_name: str):
        """Log service shutdown."""
        logger = self.get_logger(service_name)
        logger.info(f"🛑 {service_name.replace('_', ' ').title()} Service Shutting Down")
    
    def log_error_with_context(self, service_name: str, error: Exception, 
                              context: Optional[Dict] = None):
        """Log error with additional context."""
        logger = self.get_logger(service_name)
        logger.error(f"❌ Error in {service_name}: {str(error)}")
        if context:
            logger.error(f"Context: {context}")
        logger.exception("Full traceback:")
    
    def create_tail_command(self, service_name: str) -> str:
        """Generate tail command for monitoring a specific service log."""
        log_file = self.log_dir / f"{service_name}.log"
        return f"tail -f {log_file.absolute()}"
    
    def create_tail_all_command(self) -> str:
        """Generate command to tail all service logs."""
        log_files = [str(self.log_dir / f"{service}.log") for service in self.loggers.keys()]
        return f"tail -f {' '.join(log_files)}"
    
    def get_log_status(self) -> Dict[str, Dict]:
        """Get status of all log files."""
        status = {}
        for service_name in self.loggers.keys():
            log_file = self.log_dir / f"{service_name}.log"
            if log_file.exists():
                stat = log_file.stat()
                status[service_name] = {
                    'file': str(log_file),
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                status[service_name] = {
                    'file': str(log_file),
                    'size_mb': 0,
                    'modified': 'Not created yet'
                }
        return status


# Global logging service instance
logging_service = ServiceLogger()

# Convenience functions for getting service loggers
def get_multi_task_logger() -> logging.Logger:
    """Get Multi-Task Agent logger."""
    return logging_service.get_logger('multi_task_agent')

def get_execution_logger() -> logging.Logger:
    """Get Execution Agent logger."""
    return logging_service.get_logger('execution_agent')

def get_portfolio_sync_logger() -> logging.Logger:
    """Get Portfolio Sync Service logger."""
    return logging_service.get_logger('portfolio_sync')

def get_alpaca_logger() -> logging.Logger:
    """Get Alpaca Trading Service logger."""
    return logging_service.get_logger('alpaca_trading')

def get_database_logger() -> logging.Logger:
    """Get Database Service logger."""
    return logging_service.get_logger('database_service')

def get_chat_logger() -> logging.Logger:
    """Get Chat Logger service logger."""
    return logging_service.get_logger('chat_logger')

def get_compliance_logger() -> logging.Logger:
    """Get Compliance Checker logger."""
    return logging_service.get_logger('compliance_checker')

def get_system_logger() -> logging.Logger:
    """Get System logger."""
    return logging_service.get_logger('system')
