"""
Config Domain Models

Consolidated from: enablement_models.py, executive_models.py, optimization_models.py, revenue_ops_models.py, outreach_models.py, network_models.py

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


