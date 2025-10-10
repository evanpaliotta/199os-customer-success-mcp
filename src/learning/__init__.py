"""
199OS Sales MCP Server - Learning Module
AI learning and intelligence system for preference learning and personalization
"""

from .question_generator import (
    LearningQuestionGenerator,
    LearningQuestion,
    QuestionType,
    ConfidenceLevel,
)

from .preference_manager import (
    PreferenceManager,
    Preference,
    PreferenceType,
    LearningEvent,
)

__all__ = [
    # Question generator
    "LearningQuestionGenerator",
    "LearningQuestion",
    "QuestionType",
    "ConfidenceLevel",
    # Preference manager
    "PreferenceManager",
    "Preference",
    "PreferenceType",
    "LearningEvent",
]
