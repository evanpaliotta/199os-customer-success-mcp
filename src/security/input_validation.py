"""
Production-Grade Input Validation System
Comprehensive Pydantic validators with SQL injection prevention and security hardening
"""

import re
import uuid
from typing import Optional, Any, List, Dict, Union
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ValidationError,
    EmailStr,
    HttpUrl,
    constr,
    conint,
    confloat
)
import structlog

logger = structlog.get_logger(__name__)


# SQL Injection Prevention Patterns
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|DECLARE)\b)",
    r"(--|;|\/\*|\*\/|xp_|sp_)",
    r"('(\s)*(OR|AND)(\s)*')",
    r"(\bOR\b\s+\d+\s*=\s*\d+)",
    r"(\bAND\b\s+\d+\s*=\s*\d+)",
    r"((\%27)|(\'))\s*((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
    r"(WAITFOR\s+DELAY)",
    r"(BENCHMARK\s*\()",
    r"(SLEEP\s*\()",
]

# XSS Prevention Patterns
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe",
    r"<object",
    r"<embed",
]

# Path Traversal Patterns
PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.",
    r"%2e%2e",
    r"\.\.\\",
    r"\\\.\.\\",
    r"/\.\./",
]

# Command Injection Patterns
COMMAND_INJECTION_PATTERNS = [
    r"[;&|`$\(\)]",
    r">\s*/dev",
    r"<\s*/dev",
]

# Allowed platforms (whitelist)
ALLOWED_PLATFORMS = {
    'salesforce', 'hubspot', 'pipedrive', 'outreach',
    'gmail', 'outlook', 'apollo', 'zoominfo', 'linkedin',
    'slack', 'teams', 'zendesk', 'intercom'
}


class SecurityValidator:
    """Collection of security validation utilities."""

    @staticmethod
    def validate_no_sql_injection(value: str) -> str:
        """
        Validate that input doesn't contain SQL injection patterns.

        Args:
            value: Input string to validate

        Returns:
            Original value if safe

        Raises:
            ValueError: If SQL injection pattern detected
        """
        if not isinstance(value, str):
            return value

        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(
                    "sql_injection_attempt_blocked",
                    pattern=pattern,
                    input_length=len(value)
                )
                raise ValueError("Input contains potentially malicious SQL patterns")

        return value

    @staticmethod
    def validate_no_xss(value: str) -> str:
        """
        Validate that input doesn't contain XSS patterns.

        Args:
            value: Input string to validate

        Returns:
            Original value if safe

        Raises:
            ValueError: If XSS pattern detected
        """
        if not isinstance(value, str):
            return value

        for pattern in XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(
                    "xss_attempt_blocked",
                    pattern=pattern,
                    input_length=len(value)
                )
                raise ValueError("Input contains potentially malicious XSS patterns")

        return value

    @staticmethod
    def validate_no_path_traversal(value: str) -> str:
        """
        Validate that input doesn't contain path traversal patterns.

        Args:
            value: Input string to validate

        Returns:
            Original value if safe

        Raises:
            ValueError: If path traversal pattern detected
        """
        if not isinstance(value, str):
            return value

        for pattern in PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(
                    "path_traversal_attempt_blocked",
                    pattern=pattern,
                    input_length=len(value)
                )
                raise ValueError("Input contains potentially malicious path traversal patterns")

        return value

    @staticmethod
    def sanitize_identifier(value: str, max_length: int = 64) -> str:
        """
        Sanitize string for use as identifier (table names, column names, etc.).

        Args:
            value: Input string
            max_length: Maximum allowed length

        Returns:
            Sanitized identifier

        Raises:
            ValueError: If input is invalid
        """
        if not value:
            raise ValueError("Identifier cannot be empty")

        # Allow only alphanumeric and underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', value)

        # Must start with letter or underscore
        if not re.match(r'^[a-zA-Z_]', sanitized):
            raise ValueError("Identifier must start with letter or underscore")

        # Check length
        if len(sanitized) > max_length:
            raise ValueError(f"Identifier exceeds maximum length of {max_length}")

        if not sanitized:
            raise ValueError("Identifier contains only invalid characters")

        return sanitized


# Base Validators

class SafeString(BaseModel):
    """Base model for validated strings with security checks."""
    value: constr(min_length=1, max_length=1000)

    @field_validator('value')
    @classmethod
    def validate_security(cls, v: str) -> str:
        """Apply security validations."""
        SecurityValidator.validate_no_sql_injection(v)
        SecurityValidator.validate_no_xss(v)
        return v


class ClientIdentifier(BaseModel):
    """Validated client identifier."""
    client_id: constr(min_length=1, max_length=128, pattern=r'^[a-zA-Z0-9_\-]+$')

    @field_validator('client_id')
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Ensure client ID is alphanumeric with hyphens/underscores only."""
        if not re.match(r'^[a-zA-Z0-9_\-]+$', v):
            raise ValueError("Client ID must contain only alphanumeric characters, hyphens, and underscores")
        return v


class UserIdentifier(BaseModel):
    """Validated user identifier."""
    user_id: constr(min_length=1, max_length=128)

    @field_validator('user_id')
    @classmethod
    def validate_security(cls, v: str) -> str:
        """Apply security validations."""
        SecurityValidator.validate_no_sql_injection(v)
        return v


class DatabaseIdentifier(BaseModel):
    """Validated database identifier (table/column names)."""
    identifier: constr(min_length=1, max_length=64)

    @field_validator('identifier')
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        """Validate as safe database identifier."""
        return SecurityValidator.sanitize_identifier(v)


class EmailAddress(BaseModel):
    """Validated email address."""
    email: EmailStr

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Additional email validation."""
        if len(v) > 254:  # RFC 5321
            raise ValueError("Email address too long")
        return v.lower()


class PhoneNumber(BaseModel):
    """Validated phone number."""
    phone: constr(min_length=10, max_length=20, pattern=r'^\+?[1-9]\d{1,14}$')

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate E.164 format."""
        # Remove formatting characters
        cleaned = re.sub(r'[\s\-\(\)\.]+', '', v)

        if not re.match(r'^\+?[1-9]\d{1,14}$', cleaned):
            raise ValueError("Invalid phone number format (use E.164 format)")

        return cleaned


class URLValidator(BaseModel):
    """Validated URL."""
    url: HttpUrl

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: HttpUrl) -> HttpUrl:
        """Additional URL validation."""
        url_str = str(v)

        # Check for suspicious patterns
        if re.search(r'(javascript|data|vbscript):', url_str, re.IGNORECASE):
            raise ValueError("Suspicious URL scheme detected")

        return v


# Domain-Specific Validators

class CredentialKey(BaseModel):
    """Validated credential key."""
    key: constr(min_length=1, max_length=128, pattern=r'^[a-zA-Z0-9_\.]+$')

    @field_validator('key')
    @classmethod
    def validate_key(cls, v: str) -> str:
        """Ensure key is safe."""
        if v.startswith('.') or v.endswith('.'):
            raise ValueError("Key cannot start or end with period")
        return v


class ToolType(str, Enum):
    """Enumeration of valid tool types."""
    SALESFORCE = "salesforce"
    GMAIL = "gmail"
    HUBSPOT = "hubspot"
    SLACK = "slack"
    CALENDAR = "calendar"
    ANALYTICS = "analytics"
    DATABASE = "database"


class ToolExecutionInput(BaseModel):
    """Validated input for tool execution."""
    client_id: str = Field(..., min_length=1, max_length=128)
    tool_type: ToolType
    action: str = Field(..., min_length=1, max_length=64)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = Field(None, max_length=128)

    @field_validator('client_id', 'action')
    @classmethod
    def validate_security(cls, v: str) -> str:
        """Apply security validations."""
        SecurityValidator.validate_no_sql_injection(v)
        SecurityValidator.validate_no_xss(v)
        return v

    @field_validator('parameters')
    @classmethod
    def validate_parameters(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameter keys and values."""
        # Check parameter count
        if len(v) > 100:
            raise ValueError("Too many parameters (max 100)")

        # Validate each parameter
        for key, value in v.items():
            # Validate key
            if not re.match(r'^[a-zA-Z0-9_]+$', key):
                raise ValueError(f"Invalid parameter key: {key}")

            # Validate value if string
            if isinstance(value, str):
                SecurityValidator.validate_no_sql_injection(value)

                if len(value) > 10000:
                    raise ValueError(f"Parameter value too long: {key}")

        return v


class QueryFilter(BaseModel):
    """Validated query filter."""
    field: str = Field(..., min_length=1, max_length=64)
    operator: str = Field(..., pattern=r'^(eq|ne|gt|gte|lt|lte|in|like|between)$')
    value: Union[str, int, float, bool, List[Union[str, int, float]]]

    @field_validator('field')
    @classmethod
    def validate_field(cls, v: str) -> str:
        """Validate field name."""
        return SecurityValidator.sanitize_identifier(v)

    @field_validator('value')
    @classmethod
    def validate_value(cls, v: Any) -> Any:
        """Validate filter value."""
        if isinstance(v, str):
            SecurityValidator.validate_no_sql_injection(v)

            if len(v) > 1000:
                raise ValueError("Filter value too long")

        elif isinstance(v, list):
            if len(v) > 100:
                raise ValueError("Too many values in filter (max 100)")

            for item in v:
                if isinstance(item, str):
                    SecurityValidator.validate_no_sql_injection(item)

        return v


class PaginationInput(BaseModel):
    """Validated pagination parameters."""
    page: conint(ge=1, le=10000) = 1
    page_size: conint(ge=1, le=1000) = 100
    sort_by: Optional[str] = Field(None, max_length=64)
    sort_order: Optional[str] = Field(None, pattern=r'^(asc|desc)$')

    @field_validator('sort_by')
    @classmethod
    def validate_sort_field(cls, v: Optional[str]) -> Optional[str]:
        """Validate sort field."""
        if v is not None:
            return SecurityValidator.sanitize_identifier(v)
        return v


class DateRangeInput(BaseModel):
    """Validated date range."""
    start_date: date
    end_date: date

    @model_validator(mode='after')
    def validate_date_range(self) -> 'DateRangeInput':
        """Ensure end date is after start date."""
        if self.end_date < self.start_date:
            raise ValueError("End date must be after start date")

        # Check range is not too large
        delta = self.end_date - self.start_date
        if delta.days > 3650:  # 10 years
            raise ValueError("Date range too large (max 10 years)")

        return self


class MoneyAmount(BaseModel):
    """Validated monetary amount."""
    amount: Decimal = Field(..., decimal_places=2, max_digits=15)
    currency: str = Field(..., pattern=r'^[A-Z]{3}$')

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount is positive."""
        if v < 0:
            raise ValueError("Amount cannot be negative")

        if v > Decimal('999999999999.99'):
            raise ValueError("Amount too large")

        return v

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate ISO 4217 currency code."""
        # Common currencies (extend as needed)
        valid_currencies = {
            'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD',
            'CHF', 'CNY', 'INR', 'BRL', 'MXN'
        }

        if v not in valid_currencies:
            raise ValueError(f"Unsupported currency: {v}")

        return v


class ConfigurationInput(BaseModel):
    """Validated configuration input."""
    client_id: str = Field(..., min_length=1, max_length=128)
    config_key: str = Field(..., min_length=1, max_length=128)
    config_value: Any
    description: Optional[str] = Field(None, max_length=500)

    @field_validator('client_id', 'config_key')
    @classmethod
    def validate_identifiers(cls, v: str) -> str:
        """Validate identifiers."""
        SecurityValidator.validate_no_sql_injection(v)
        return v

    @field_validator('config_value')
    @classmethod
    def validate_config_value(cls, v: Any) -> Any:
        """Validate configuration value."""
        # Check JSON serializable
        import json
        try:
            json.dumps(v)
        except (TypeError, ValueError):
            raise ValueError("Configuration value must be JSON serializable")

        # Check size
        serialized = json.dumps(v)
        if len(serialized) > 100000:  # 100KB
            raise ValueError("Configuration value too large")

        return v


class SearchQuery(BaseModel):
    """Validated search query."""
    query: str = Field(..., min_length=1, max_length=500)
    filters: List[QueryFilter] = Field(default_factory=list)
    pagination: PaginationInput = Field(default_factory=PaginationInput)

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate search query."""
        SecurityValidator.validate_no_sql_injection(v)
        SecurityValidator.validate_no_xss(v)

        # Remove excessive whitespace
        v = ' '.join(v.split())

        return v

    @field_validator('filters')
    @classmethod
    def validate_filters(cls, v: List[QueryFilter]) -> List[QueryFilter]:
        """Validate filter count."""
        if len(v) > 50:
            raise ValueError("Too many filters (max 50)")
        return v


class BulkOperationInput(BaseModel):
    """Validated bulk operation input."""
    client_id: str = Field(..., min_length=1, max_length=128)
    operation_type: str = Field(..., pattern=r'^(create|update|delete)$')
    records: List[Dict[str, Any]] = Field(..., min_items=1, max_items=1000)

    @field_validator('client_id')
    @classmethod
    def validate_client(cls, v: str) -> str:
        """Validate client ID."""
        SecurityValidator.validate_no_sql_injection(v)
        return v

    @field_validator('records')
    @classmethod
    def validate_records(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate record data."""
        for idx, record in enumerate(v):
            # Check field count
            if len(record) > 100:
                raise ValueError(f"Record {idx} has too many fields (max 100)")

            # Validate each field
            for key, value in record.items():
                # Validate key
                if not re.match(r'^[a-zA-Z0-9_]+$', key):
                    raise ValueError(f"Invalid field name in record {idx}: {key}")

                # Validate value if string
                if isinstance(value, str):
                    SecurityValidator.validate_no_sql_injection(value)

                    if len(value) > 10000:
                        raise ValueError(f"Field value too long in record {idx}: {key}")

        return v


def validate_input(data: Dict[str, Any], model_class: type[BaseModel]) -> BaseModel:
    """
    Validate input data against a Pydantic model.

    Args:
        data: Input data dictionary
        model_class: Pydantic model class to validate against

    Returns:
        Validated model instance

    Raises:
        ValidationError: If validation fails
    """
    try:
        validated = model_class(**data)
        logger.debug(
            "input_validation_success",
            model=model_class.__name__
        )
        return validated

    except ValidationError as e:
        logger.warning(
            "input_validation_failed",
            model=model_class.__name__,
            errors=e.errors()
        )
        raise


def test_input_validation() -> Any:
    """Test input validation system."""
    print("Test 1: Valid client ID...")
    try:
        validated = ClientIdentifier(client_id="test_client_123")
        print(f"✓ Valid: {validated.client_id}")
    except ValidationError as e:
        print(f"✗ Failed: {e}")

    print("\nTest 2: SQL injection prevention...")
    try:
        SafeString(value="'; DROP TABLE users; --")
        print("✗ SQL injection not detected!")
    except ValidationError:
        print("✓ SQL injection blocked")

    print("\nTest 3: XSS prevention...")
    try:
        SafeString(value="<script>alert('xss')</script>")
        print("✗ XSS not detected!")
    except ValidationError:
        print("✓ XSS blocked")

    print("\nTest 4: Valid email...")
    try:
        validated = EmailAddress(email="test@example.com")
        print(f"✓ Valid email: {validated.email}")
    except ValidationError as e:
        print(f"✗ Failed: {e}")

    print("\nTest 5: Valid tool execution input...")
    try:
        validated = ToolExecutionInput(
            client_id="test_client",
            tool_type=ToolType.SALESFORCE,
            action="query_accounts",
            parameters={"limit": 10}
        )
        print(f"✓ Valid tool input: {validated.tool_type}")
    except ValidationError as e:
        print(f"✗ Failed: {e}")

    print("\nTest 6: Invalid date range...")
    try:
        DateRangeInput(
            start_date=date(2024, 1, 1),
            end_date=date(2023, 1, 1)
        )
        print("✗ Invalid date range not detected!")
    except ValidationError:
        print("✓ Invalid date range blocked")

    print("\nTest 7: Valid money amount...")
    try:
        validated = MoneyAmount(amount=Decimal("1234.56"), currency="USD")
        print(f"✓ Valid amount: {validated.amount} {validated.currency}")
    except ValidationError as e:
        print(f"✗ Failed: {e}")

    print("\nTest 8: Path traversal prevention...")
    try:
        SecurityValidator.validate_no_path_traversal("../../etc/passwd")
        print("✗ Path traversal not detected!")
    except ValueError:
        print("✓ Path traversal blocked")

    print("\n✅ All tests completed!")


# ============================================================================
# Convenient Standalone Validators for MCP Tools
# ============================================================================

class ValidationError(Exception):
    """Raised when validation fails"""
    pass


def validate_client_id(client_id: str) -> str:
    """
    Validate client identifier to prevent injection attacks.

    Args:
        client_id: Client identifier to validate

    Returns:
        Validated client_id

    Raises:
        ValidationError: If validation fails
    """
    if not client_id or not isinstance(client_id, str):
        raise ValidationError("client_id must be non-empty string")

    if len(client_id) > 100:
        raise ValidationError(f"client_id too long (max 100 chars)")

    # Check path traversal FIRST (before other checks)
    if '..' in client_id or '/' in client_id or '\\' in client_id:
        raise ValidationError("client_id cannot contain path traversal characters (..  / \\)")

    # Only allow safe characters
    if not re.match(r'^[a-zA-Z0-9_-]+$', client_id):
        raise ValidationError("client_id can only contain alphanumeric, underscore, hyphen")

    return client_id


def validate_platform_name(platform: str) -> str:
    """
    Validate platform against whitelist.

    Args:
        platform: Platform name to validate

    Returns:
        Lowercased platform name

    Raises:
        ValidationError: If platform not in whitelist
    """
    if not platform or not isinstance(platform, str):
        raise ValidationError("platform must be non-empty string")

    platform_lower = platform.lower()

    if platform_lower not in ALLOWED_PLATFORMS:
        raise ValidationError(
            f"Unknown platform: {platform}. "
            f"Allowed: {', '.join(sorted(ALLOWED_PLATFORMS))}"
        )

    return platform_lower


def validate_pagination(limit: Optional[int] = None,
                       offset: Optional[int] = None,
                       max_limit: int = 1000) -> Dict[str, int]:
    """
    Validate pagination parameters to prevent excessive data retrieval.

    Args:
        limit: Maximum number of results to return
        offset: Number of results to skip
        max_limit: Maximum allowed limit

    Returns:
        Dict with validated limit and offset

    Raises:
        ValidationError: If parameters are invalid
    """
    # Default values
    if limit is None:
        limit = 100

    if offset is None:
        offset = 0

    # Validate limit
    if not isinstance(limit, int):
        raise ValidationError(f"limit must be integer, got {type(limit).__name__}")

    if limit < 0:
        raise ValidationError("limit must be non-negative")

    if limit > max_limit:
        raise ValidationError(f"limit exceeds maximum of {max_limit}")

    # Validate offset
    if not isinstance(offset, int):
        raise ValidationError(f"offset must be integer, got {type(offset).__name__}")

    if offset < 0:
        raise ValidationError("offset must be non-negative")

    return {"limit": limit, "offset": offset}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal.

    Args:
        filename: Filename to sanitize

    Returns:
        Safe filename (basename only)

    Raises:
        ValidationError: If filename is invalid
    """
    if not filename or not isinstance(filename, str):
        raise ValidationError("filename must be non-empty string")

    # Check path traversal patterns FIRST
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, filename, re.IGNORECASE):
            raise ValidationError(f"filename contains path traversal pattern")

    # Get basename (remove path components)
    from pathlib import Path
    filename = Path(filename).name

    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)

    # Prevent hidden files or current/parent directory
    if filename.startswith('.') or filename in ('.', '..'):
        raise ValidationError("Invalid filename (hidden or directory reference)")

    if not filename or filename == '_':
        raise ValidationError("filename contains only invalid characters")

    if len(filename) > 255:
        raise ValidationError("filename too long (max 255 chars)")

    return filename


def validate_email(email: str) -> str:
    """
    Basic email validation.

    Args:
        email: Email address to validate

    Returns:
        Lowercased email

    Raises:
        ValidationError: If email is invalid
    """
    if not email or not isinstance(email, str):
        raise ValidationError("email must be non-empty string")

    # Basic pattern matching
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError("Invalid email format")

    if len(email) > 254:  # RFC 5321
        raise ValidationError("email too long (max 254 chars)")

    return email.lower()


def validate_url(url: str) -> str:
    """
    Basic URL validation.

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        ValidationError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ValidationError("url must be non-empty string")

    # Must start with http:// or https://
    if not url.startswith(('http://', 'https://')):
        raise ValidationError("url must start with http:// or https://")

    # Check for common XSS patterns
    try:
        SecurityValidator.validate_no_xss(url)
    except ValueError as e:
        raise ValidationError(str(e))

    if len(url) > 2048:
        raise ValidationError("url too long (max 2048 chars)")

    return url


if __name__ == '__main__':
    test_input_validation()
