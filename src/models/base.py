"""
Base Model Classes for Sales MCP

Provides reusable base classes with common fields and behavior to reduce
code duplication across domain models.

Base Classes:
- BaseModel: Minimal Pydantic base
- TimestampedModel: Adds created_at/updated_at
- ClientScopedModel: Adds client_id + timestamps
- NamedModel: Adds name + timestamps
- IdentifiedModel: Adds generic ID field + timestamps

Usage:
    from src.models.base import ClientScopedModel

    class Deal(ClientScopedModel):
        deal_name: str
        value: float
        # created_at, updated_at, client_id inherited
"""

from pydantic import BaseModel as PydanticBaseModel, Field
from datetime import datetime
from typing import Optional


class BaseModel(PydanticBaseModel):
    """
    Base Pydantic model with common configuration.

    All RevOps models should inherit from this or one of its subclasses.
    """

    class Config:
        # Allow extra fields for flexibility
        extra = "allow"
        # Use enum values instead of enum objects
        use_enum_values = True
        # Validate on assignment
        validate_assignment = True
        # JSON schema extras
        json_schema_extra = {
            "description": "RevOps MCP Model"
        }


class TimestampedModel(BaseModel):
    """
    Base model with automatic timestamp tracking.

    Fields:
        created_at: Record creation timestamp (auto-generated)
        updated_at: Last update timestamp (auto-updated)

    Example:
        class Campaign(TimestampedModel):
            name: str
            budget: float
    """

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when record was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when record was last updated"
    )


class ClientScopedModel(TimestampedModel):
    """
    Base model for client-specific data with timestamps.

    All data is scoped to a specific client for multi-tenancy.

    Fields:
        client_id: Client identifier (required)
        created_at: Record creation timestamp
        updated_at: Last update timestamp

    Example:
        class Deal(ClientScopedModel):
            deal_name: str
            value: float
            stage: str
    """

    client_id: str = Field(
        ...,
        description="Client identifier for multi-tenant data isolation"
    )


class NamedModel(TimestampedModel):
    """
    Base model for entities with a name field.

    Common for business entities like campaigns, projects, etc.

    Fields:
        name: Entity name (required)
        description: Optional description
        created_at: Record creation timestamp
        updated_at: Last update timestamp

    Example:
        class Campaign(NamedModel):
            budget: float
            status: CampaignStatus
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Entity name"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional description"
    )


class IdentifiedModel(TimestampedModel):
    """
    Base model for entities with a generic ID field.

    Use when entities need a specific identifier pattern.

    Fields:
        id: Entity identifier (required)
        created_at: Record creation timestamp
        updated_at: Last update timestamp

    Example:
        class ExecutionLog(IdentifiedModel):
            execution_id: str  # Add specific ID
            status: str
            result: Dict
    """

    id: str = Field(
        ...,
        description="Unique identifier for this entity"
    )


class ClientNamedModel(ClientScopedModel):
    """
    Base model combining client scoping with name field.

    Most common pattern for business entities.

    Fields:
        client_id: Client identifier (required)
        name: Entity name (required)
        description: Optional description
        created_at: Record creation timestamp
        updated_at: Last update timestamp

    Example:
        class Pipeline(ClientNamedModel):
            stages: List[str]
            default_probability: Dict[str, float]
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Entity name"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional description"
    )


# Export all base classes
__all__ = [
    "BaseModel",
    "TimestampedModel",
    "ClientScopedModel",
    "NamedModel",
    "IdentifiedModel",
    "ClientNamedModel",
]
