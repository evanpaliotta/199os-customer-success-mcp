"""
Activity Domain Models

Consolidated from: meeting_models.py, conversation_models.py, discovery_meeting_models.py, presentation_models.py, virtual_meeting_models.py

This file combines related models for better organization and maintainability.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from .base import (
    BaseModel as RevOpsBaseModel,
    TimestampedModel,
    ClientScopedModel,
    NamedModel,
    IdentifiedModel,
    ClientNamedModel,
)


