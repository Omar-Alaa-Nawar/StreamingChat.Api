"""
Core utilities shared by all component types.

Provides common tracking, validation, and helper functions used across
all streaming service modules.
"""

import json
import logging
import uuid
from typing import Dict
from datetime import datetime

from .constants import COMPONENT_DELIMITER, COMPONENT_TYPES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streaming")


def track_component(component_id: str, data: dict, active_components: Dict[str, dict]):
    """
    Track component state during streaming.
    
    Args:
        component_id: UUID of the component
        data: Current data state of the component
        active_components: Request-scoped component tracking dictionary
    """
    active_components[component_id] = data
    logger.info(f"Tracking component: {component_id}")


def get_component_state(component_id: str, active_components: Dict[str, dict]) -> dict:
    """
    Get current state of tracked component.
    
    Args:
        component_id: UUID of the component
        active_components: Request-scoped component tracking dictionary
        
    Returns:
        dict: Component data or empty dict if not found
    """
    return active_components.get(component_id, {})


def validate_component_update(component_id: str, data: dict, active_components: Dict[str, dict]) -> bool:
    """
    Validate component update before sending (Phase 2).
    
    Args:
        component_id: UUID of the component
        data: Data to validate
        active_components: Request-scoped component tracking dictionary
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Check if component was initialized
    if component_id not in active_components:
        logger.warning(f"Update for unknown component: {component_id}")
        return False
    
    # Validate data structure
    if not isinstance(data, dict):
        logger.error(f"Invalid data type for component {component_id}")
        return False
    
    return True


def validate_component(component: dict) -> bool:
    """
    Validate a component dictionary structure.

    Checks:
    - Has required fields (type, id, data)
    - Type is in allowed list
    - ID is valid UUID7 format
    - Data is a dictionary (can be empty for Phase 2)

    Args:
        component: Component dictionary to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check required fields
        if not all(key in component for key in ["type", "id", "data"]):
            return False

        # Check type is allowed
        if component["type"] not in COMPONENT_TYPES:
            return False

        # Check ID format (robust UUID validation)
        if not isinstance(component["id"], str):
            return False
        try:
            uuid.UUID(component["id"])
        except (ValueError, AttributeError):
            return False

        # Check data is dict (Phase 2: can be empty {})
        if not isinstance(component["data"], dict):
            return False

        return True

    except Exception:
        return False


def format_component(component: dict) -> str:
    """
    Format a component dictionary with delimiters for streaming.
    
    Args:
        component: Component dictionary to format
        
    Returns:
        str: Formatted component string with delimiters
    """
    component_json = json.dumps(component, separators=(',', ':'))
    return f"{COMPONENT_DELIMITER}{component_json}{COMPONENT_DELIMITER}"
