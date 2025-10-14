"""
Base Integration Classes and Types
Shared types and base classes for all integrations
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum
import asyncio
import aiohttp
import structlog
from abc import ABC, abstractmethod

logger = structlog.get_logger(__name__)


class IntegrationStatus(str, Enum):
    """Integration connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    AUTHENTICATING = "authenticating"


class ConnectionTestResult:
    """Result of connection test."""

    def __init__(
        self,
        success: bool,
        status: IntegrationStatus,
        message: str,
        response_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.status = status
        self.message = message
        self.response_time_ms = response_time_ms
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'status': self.status.value,
            'message': self.message,
            'response_time_ms': self.response_time_ms,
            'metadata': self.metadata
        }


class ValidationError(Exception):
    """Raised when credential validation fails."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class APIError(Exception):
    """Raised when API request fails."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class CircuitBreaker:
    """Simple circuit breaker for fault tolerance."""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half_open

    def _record_success(self, response_time: float):
        """Record successful request."""
        if self.state == "half_open":
            self.state = "closed"
            self.failure_count = 0
            logger.info("circuit_breaker_closed", message="Service recovered")

    def _record_failure(self, error: Exception):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.error(
                "circuit_breaker_open",
                failure_count=self.failure_count,
                message="Circuit breaker opened due to failures"
            )


class BaseIntegration(ABC):
    """Base class for all integrations."""

    def __init__(
        self,
        integration_name: str,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize base integration.

        Args:
            integration_name: Name of the integration
            credentials: Authentication credentials
            rate_limit_calls: Max API calls per window
            rate_limit_window: Rate limit window in seconds
            max_retries: Maximum retry attempts
        """
        self.integration_name = integration_name
        self.credentials = credentials
        self.rate_limit_calls = rate_limit_calls
        self.rate_limit_window = rate_limit_window
        self.max_retries = max_retries

        self.session: Optional[aiohttp.ClientSession] = None
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        self._authenticated = False

        logger.info(
            "integration_initialized",
            integration=integration_name
        )

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the integration.

        Returns:
            True if authentication successful

        Raises:
            AuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult:
        """
        Test connection to the integration.

        Returns:
            ConnectionTestResult with test details
        """
        pass

    async def ensure_authenticated(self):
        """Ensure we're authenticated before making requests."""
        if not self._authenticated:
            self._authenticated = await self.authenticate()

    def validate_required_fields(
        self,
        data: Dict[str, Any],
        required_fields: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate that required fields are present.

        Args:
            data: Data dictionary to validate
            required_fields: List of required field names

        Returns:
            Tuple of (is_valid, error_message)
        """
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"
        return True, ""

    async def close(self):
        """Close HTTP session and cleanup resources."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info(
                "integration_session_closed",
                integration=self.integration_name
            )
