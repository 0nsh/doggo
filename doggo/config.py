"""Configuration management for Doggo CLI."""

import json
from pathlib import Path
from typing import Dict, Any


def get_config_dir() -> Path:
    """Get the Doggo configuration directory path."""
    return Path.home() / ".doggo"


def get_config_file() -> Path:
    """Get the Doggo configuration file path."""
    return get_config_dir() / "config.json"


def create_config_dir() -> None:
    """Create the Doggo configuration directory if it doesn't exist."""
    config_dir = get_config_dir()
    config_dir.mkdir(exist_ok=True)


def get_default_config() -> Dict[str, Any]:
    """Get the default configuration dictionary."""
    return {
        "openai_api_key": "",
        "indexed_paths": [],
        "last_reindex": None,
        "version": "0.1.0"
    }


def create_default_config() -> None:
    """Create the default configuration file if it doesn't exist."""
    config_file = get_config_file()
    if not config_file.exists():
        default_config = get_default_config()
        save_config(default_config)


def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    config_file = get_config_file()
    if not config_file.exists():
        return get_default_config()
    
    with open(config_file, 'r') as f:
        return json.load(f)


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    config_file = get_config_file()
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


def initialize_doggo() -> None:
    """Initialize Doggo configuration and directories."""
    create_config_dir()
    create_default_config() 


def validate_api_key(key: str) -> bool:
    """Validate the OpenAI API key format (basic check)."""
    return isinstance(key, str) and key.startswith("sk-") and len(key) > 10


def set_api_key(key: str) -> None:
    """Set the OpenAI API key in the config file."""
    if not validate_api_key(key):
        raise ValueError("Invalid OpenAI API key format.")
    config = load_config()
    config["openai_api_key"] = key
    save_config(config)


def get_config_summary() -> dict:
    """Get a summary of the config for display purposes (mask API key)."""
    config = load_config()
    masked_key = (
        config["openai_api_key"][:6] + "..." + config["openai_api_key"][-4:]
        if config["openai_api_key"] else "(not set)"
    )
    return {
        "OpenAI API Key": masked_key,
        "Indexed Paths": len(config.get("indexed_paths", [])),
        "Last Reindex": config.get("last_reindex") or "Never",
        "Version": config.get("version", "?")
    } 