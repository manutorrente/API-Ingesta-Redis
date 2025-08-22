"""
Configuration management module for Redis Ingestion API.

Simple JSON configuration loader with error handling.
The config is loaded once when the module is imported and can be used
as a regular dictionary throughout the application.

Usage:
    host = config["api"]["host"]
    port = config["api"]["port"]
    

"""

import os
import json


def load_config():
    """
    Load configuration from JSON file.
    
    Returns:
        dict: The loaded configuration
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        ValueError: If the JSON file is invalid
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")




# Load configuration once when module is imported
config = load_config()
