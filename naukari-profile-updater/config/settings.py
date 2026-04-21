"""
Configuration management for Naukari Profile Updater
Supports environment variables and config files
"""

import os
import json
from pathlib import Path
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / 'config'
ENV_FILE = CONFIG_DIR / '.env'
CONFIG_FILE = CONFIG_DIR / 'config.json'


def get_credentials() -> Tuple[str, str]:
    """
    Get Naukari credentials from environment or config file
    Priority: Environment variables > Config file
    
    Returns:
        Tuple[str, str]: (username, password)
        
    Raises:
        ValueError: If credentials not found
    """
    # Try environment variables first (better for production/GCP)
    username = os.getenv('NAUKARI_USERNAME') or os.getenv('NAUKARI_EMAIL')
    password = os.getenv('NAUKARI_PASSWORD')
    
    if username and password:
        logger.info("Credentials loaded from environment variables")
        return username, password
    
    # Try config file
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                username = config.get('username') or config.get('email')
                password = config.get('password')
                
                if username and password:
                    logger.info("Credentials loaded from config file")
                    return username, password
    except Exception as e:
        logger.warning(f"Failed to load config file: {e}")
    
    # Try .env file format
    if ENV_FILE.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(ENV_FILE)
            username = os.getenv('NAUKARI_USERNAME') or os.getenv('NAUKARI_EMAIL')
            password = os.getenv('NAUKARI_PASSWORD')
            
            if username and password:
                logger.info("Credentials loaded from .env file")
                return username, password
        except ImportError:
            logger.debug("python-dotenv not installed, skipping .env parsing")
        except Exception as e:
            logger.warning(f"Failed to load .env file: {e}")
    
    raise ValueError(
        "Naukari credentials not found! Please provide credentials via:\n"
        "1. Environment variables: NAUKARI_USERNAME/NAUKARI_EMAIL and NAUKARI_PASSWORD\n"
        "2. config.json file in config directory\n"
        "3. .env file in config directory"
    )


def get_config() -> Dict:
    """
    Get application configuration
    
    Returns:
        Dict: Configuration dictionary with defaults
    """
    config = {
        'headless': True,
        'debug': False,
        'timeout': 30000,
        'log_level': 'INFO',
        'notify_on_success': False,
        'notify_on_failure': False,
    }
    
    # Override with environment variables
    if os.getenv('DEBUG'):
        config['debug'] = os.getenv('DEBUG').lower() in ['true', '1', 'yes']
    
    if os.getenv('HEADLESS'):
        config['headless'] = os.getenv('HEADLESS').lower() in ['true', '1', 'yes']
    
    if os.getenv('LOG_LEVEL'):
        config['log_level'] = os.getenv('LOG_LEVEL')
    
    # Load from config file if exists
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                file_config = json.load(f)
                config.update({k: v for k, v in file_config.items() if k != 'password'})
    except Exception as e:
        logger.warning(f"Failed to load config from file: {e}")
    
    logger.debug(f"Configuration loaded: {config}")
    return config


def validate_credentials(username: str, password: str) -> bool:
    """
    Basic validation of credentials
    
    Args:
        username: Username/email
        password: Password
        
    Returns:
        bool: True if credentials look valid
    """
    if not username or not password:
        return False
    
    if len(username) < 3:
        return False
    
    if len(password) < 4:  # Minimum password length
        return False
    
    if '@' in username and not username.count('@') == 1:
        return False
    
    return True


def save_config(config_dict: Dict):
    """
    Save configuration to config.json file
    
    Args:
        config_dict: Configuration dictionary
    """
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_dict, f, indent=2)
        logger.info(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")


if __name__ == "__main__":
    # Test configuration loading
    print("Testing configuration loading...")
    try:
        username, password = get_credentials()
        print(f"✓ Credentials found - username: {username[:3]}***")
    except ValueError as e:
        print(f"✗ Credentials error: {e}")
    
    config = get_config()
    print(f"✓ Configuration loaded: {config}")
