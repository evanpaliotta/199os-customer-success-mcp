"""
199OS Sales MCP Server - Security Module
Production-ready security infrastructure with GDPR compliance
"""

from .credential_manager import SecureCredentialManager
from .audit_logger import (
    AuditLogger,
    AuditLog,
    AuditEventType,
    AuditSeverity,
)
from .gdpr_compliance import (
    GDPRComplianceManager,
    GDPRRequest,
    GDPRRequestType,
    GDPRRequestStatus,
    DataCategory,
)
from .input_validation import (
    SecurityValidator,
    SafeString,
    ClientIdentifier,
    UserIdentifier,
    DatabaseIdentifier,
    EmailAddress,
    PhoneNumber,
    URLValidator,
    CredentialKey,
    ToolType,
    ToolExecutionInput,
    QueryFilter,
    PaginationInput,
    DateRangeInput,
    MoneyAmount,
    ConfigurationInput,
    SearchQuery,
    BulkOperationInput,
    validate_input,
)

__all__ = [
    # Credential management
    "SecureCredentialManager",
    # Audit logging
    "AuditLogger",
    "AuditLog",
    "AuditEventType",
    "AuditSeverity",
    # GDPR compliance
    "GDPRComplianceManager",
    "GDPRRequest",
    "GDPRRequestType",
    "GDPRRequestStatus",
    "DataCategory",
    # Input validation
    "SecurityValidator",
    "SafeString",
    "ClientIdentifier",
    "UserIdentifier",
    "DatabaseIdentifier",
    "EmailAddress",
    "PhoneNumber",
    "URLValidator",
    "CredentialKey",
    "ToolType",
    "ToolExecutionInput",
    "QueryFilter",
    "PaginationInput",
    "DateRangeInput",
    "MoneyAmount",
    "ConfigurationInput",
    "SearchQuery",
    "BulkOperationInput",
    "validate_input",
]
