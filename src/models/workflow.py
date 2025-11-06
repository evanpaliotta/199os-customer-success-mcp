"""
Workflow Domain Models

Consolidated from: automation_models.py, orchestration_models.py, integration_models.py, crm_models.py

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


