"""
LLM Integration Service for StreamForge.

This package provides AI-powered component planning using AWS Bedrock.
Phase 6: LLM-Driven Dynamic Component Generation.
"""

from .llm_planner_service import LLMPlannerService

# Global instance for use across the application
llm_planner_service = LLMPlannerService()

__all__ = [
    "LLMPlannerService",
    "llm_planner_service",
]

__version__ = "0.6.0"
