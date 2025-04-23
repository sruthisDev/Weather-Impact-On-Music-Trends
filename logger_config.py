import logging
import os
import sys
from datetime import datetime

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Get the current date for the log filename
current_date = datetime.now().strftime('%Y-%m-%d')

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Set up a logger with the specified name and configuration.
    
    Args:
        name (str): The name of the logger
        log_file (str, optional): The path to the log file. If None, only console logging is used.
        level (int, optional): The logging level. Defaults to logging.INFO.
        
    Returns:
        logging.Logger: The configured logger
    """
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatters
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler with encoding that supports Unicode
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_script_logger(script_name, level=logging.INFO):
    """
    Get a logger for a specific script with both console and file output.
    
    Args:
        script_name (str): The name of the script (without .py extension)
        level (int, optional): The logging level. Defaults to logging.INFO.
            Common values:
            - logging.DEBUG: Detailed information for debugging
            - logging.INFO: General information about program execution
            - logging.WARNING: Indicate a potential problem
            - logging.ERROR: A more serious problem
            - logging.CRITICAL: A critical problem that may prevent the program from running
        
    Returns:
        logging.Logger: The configured logger
    """
    log_file = f'logs/{script_name}_{current_date}.log'
    return setup_logger(script_name, log_file, level) 