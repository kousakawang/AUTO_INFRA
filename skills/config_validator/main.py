"""
Config Validator Skill - Main implementation.
Validates user configs and expands them to full execution configs.
"""
import os
import sys
import importlib.util
from typing import Dict, Optional, Tuple

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.config import validate_user_config, get_default_pipeline_config
from src.config_generator import ConfigExpander, FullConfig
from src.templates import TemplateLoader


def load_config_from_file(filepath: str) -> Dict:
    """
    Load configuration from a Python file.

    Args:
        filepath: Path to config file defining 'config_dict'

    Returns:
        The config_dict from the file
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Config file not found: {filepath}")

    spec = importlib.util.spec_from_file_location("config_module", filepath)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load config from: {filepath}")

    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    if not hasattr(config_module, "config_dict"):
        raise AttributeError("Config file must define 'config_dict' variable")

    return config_module.config_dict


def validate_config(config_dict: Dict) -> Tuple[bool, list]:
    """
    Validate a configuration dictionary.

    Args:
        config_dict: Configuration with user_config and optional pipeline_config

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    user_config = config_dict.get("user_config", {})
    errors = validate_user_config(user_config)
    return len(errors) == 0, errors


def expand_config(config_dict: Dict) -> FullConfig:
    """
    Expand a user config to a full execution config.

    Args:
        config_dict: Configuration with user_config and pipeline_config

    Returns:
        Expanded FullConfig object
    """
    user_config = config_dict.get("user_config", {})
    pipeline_config = config_dict.get("pipeline_config", {})

    # Merge with defaults
    default_pipeline = get_default_pipeline_config()
    merged_pipeline = {**default_pipeline, **pipeline_config}

    expander = ConfigExpander(user_config, merged_pipeline)
    return expander.expand()


def load_and_validate_config(filepath: str) -> Tuple[FullConfig, TemplateLoader, Dict]:
    """
    Load config from file, validate it, expand it, and load templates.

    Args:
        filepath: Path to config file

    Returns:
        Tuple of (full_config, template_loader, original_config_dict)
    """
    config_dict = load_config_from_file(filepath)

    # Validate
    is_valid, errors = validate_config(config_dict)
    if not is_valid:
        raise ValueError(f"Config validation failed: {errors}")

    # Expand
    full_config = expand_config(config_dict)

    # Load templates
    template_loader = TemplateLoader(project_root)
    template_loader.load_all()

    return full_config, template_loader, config_dict
