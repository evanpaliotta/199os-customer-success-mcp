"""
Centralized Error Handling for Sales MCP
Provides comprehensive exception hierarchy and error handling mechanisms
"""

import functools
import traceback
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

# Type variable for generic functions
T = TypeVar('T')


# ============================================================================
# Base Exception Hierarchy
# ============================================================================

class SalesMCPError(Exception):
    """Base exception for all Sales MCP errors"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False
    ) -> Any:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.recoverable = recoverable
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp.isoformat()
        }


# ============================================================================
# Data & Integration Errors
# ============================================================================

class DataError(SalesMCPError):
    """Base class for data-related errors"""
    pass


class DatabaseError(DataError):
    """Database connection or query errors"""
    def __init__(self, message: str, query: Optional[str] = None, **kwargs) -> Any:
        super().__init__(message, **kwargs)
        if query:
            self.details["query"] = query


class CacheError(DataError):
    """Cache operation errors"""
    pass


class DataValidationError(DataError):
    """Data validation failures"""
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None, **kwargs) -> Any:
        super().__init__(message, **kwargs)
        if field:
            self.details["field"] = field
        if value is not None:
            self.details["invalid_value"] = str(value)


class DataNotFoundError(DataError):
    """Requested data not found"""
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None, **kwargs) -> Any:
        super().__init__(message, recoverable=True, **kwargs)
        if resource_type:
            self.details["resource_type"] = resource_type
        if resource_id:
            self.details["resource_id"] = resource_id


# ============================================================================
# CRM & External Integration Errors
# ============================================================================

class IntegrationError(SalesMCPError):
    """Base class for external integration errors"""
    pass


class CRMError(IntegrationError):
    """CRM-specific errors (Salesforce, HubSpot, etc.)"""
    def __init__(self, message: str, crm_system: Optional[str] = None, **kwargs) -> Any:
        super().__init__(message, recoverable=True, **kwargs)
        if crm_system:
            self.details["crm_system"] = crm_system


class APIError(IntegrationError):
    """External API errors"""
    def __init__(
        self,
        message: str,
        api_name: Optional[str] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        **kwargs
    ) -> Any:
        super().__init__(message, recoverable=True, **kwargs)
        if api_name:
            self.details["api_name"] = api_name
        if status_code:
            self.details["status_code"] = status_code
        if response_body:
            self.details["response_body"] = response_body[:500]  # Truncate


class RateLimitError(APIError):
    """API rate limit exceeded"""
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs) -> Any:
        super().__init__(message, recoverable=True, **kwargs)
        if retry_after:
            self.details["retry_after_seconds"] = retry_after


class AuthenticationError(IntegrationError):
    """Authentication/authorization failures"""
    def __init__(self, message: str, service: Optional[str] = None, **kwargs) -> Any:
        super().__init__(message, **kwargs)
        if service:
            self.details["service"] = service


# ============================================================================
# Business Logic Errors
# ============================================================================

class BusinessLogicError(SalesMCPError):
    """Base class for business logic errors"""
    pass


class InvalidOperationError(BusinessLogicError):
    """Operation not allowed in current state"""
    def __init__(self, message: str, operation: Optional[str] = None, current_state: Optional[str] = None, **kwargs) -> Any:
        super().__init__(message, **kwargs)
        if operation:
            self.details["operation"] = operation
        if current_state:
            self.details["current_state"] = current_state


class QuotaExceededError(BusinessLogicError):
    """Resource quota exceeded"""
    def __init__(self, message: str, quota_type: Optional[str] = None, current: Optional[int] = None, limit: Optional[int] = None, **kwargs) -> Any:
        super().__init__(message, recoverable=True, **kwargs)
        if quota_type:
            self.details["quota_type"] = quota_type
        if current is not None:
            self.details["current_usage"] = current
        if limit is not None:
            self.details["limit"] = limit


class InsufficientDataError(BusinessLogicError):
    """Insufficient data to perform operation"""
    def __init__(self, message: str, required_data: Optional[list] = None, **kwargs) -> Any:
        super().__init__(message, recoverable=True, **kwargs)
        if required_data:
            self.details["required_data"] = required_data


# ============================================================================
# Configuration & Security Errors
# ============================================================================

class ConfigurationError(SalesMCPError):
    """Configuration-related errors"""
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs) -> Any:
        super().__init__(message, **kwargs)
        if config_key:
            self.details["config_key"] = config_key


class CredentialError(SalesMCPError):
    """Credential management errors"""
    def __init__(self, message: str, credential_type: Optional[str] = None, **kwargs) -> Any:
        super().__init__(message, **kwargs)
        if credential_type:
            self.details["credential_type"] = credential_type


class EncryptionError(CredentialError):
    """Encryption/decryption errors"""
    pass


# ============================================================================
# ML & Intelligence Errors
# ============================================================================

class IntelligenceError(SalesMCPError):
    """Base class for ML/intelligence errors"""
    pass


class ModelLoadError(IntelligenceError):
    """ML model loading failures"""
    def __init__(self, message: str, model_name: Optional[str] = None, **kwargs) -> Any:
        super().__init__(message, **kwargs)
        if model_name:
            self.details["model_name"] = model_name


class PredictionError(IntelligenceError):
    """Prediction/inference errors"""
    def __init__(self, message: str, model_name: Optional[str] = None, **kwargs) -> Any:
        super().__init__(message, recoverable=True, **kwargs)
        if model_name:
            self.details["model_name"] = model_name


class InsufficientTrainingDataError(IntelligenceError):
    """Not enough training data for ML operation"""
    def __init__(self, message: str, required_samples: Optional[int] = None, actual_samples: Optional[int] = None, **kwargs) -> Any:
        super().__init__(message, recoverable=True, **kwargs)
        if required_samples:
            self.details["required_samples"] = required_samples
        if actual_samples:
            self.details["actual_samples"] = actual_samples


# ============================================================================
# Process & Workflow Errors
# ============================================================================

class ProcessError(SalesMCPError):
    """Base class for process execution errors"""
    pass


class ProcessExecutionError(ProcessError):
    """Process execution failures"""
    def __init__(self, message: str, process_id: Optional[str] = None, step: Optional[str] = None, **kwargs) -> Any:
        super().__init__(message, **kwargs)
        if process_id:
            self.details["process_id"] = process_id
        if step:
            self.details["failed_step"] = step


class WorkflowError(ProcessError):
    """Workflow orchestration errors"""
    def __init__(self, message: str, workflow_id: Optional[str] = None, **kwargs) -> Any:
        super().__init__(message, **kwargs)
        if workflow_id:
            self.details["workflow_id"] = workflow_id


# ============================================================================
# Error Handlers & Decorators
# ============================================================================

def handle_errors(
    error_message: str = "Operation failed",
    log_traceback: bool = True,
    return_on_error: Optional[Any] = None,
    recoverable_exceptions: Optional[tuple] = None
) -> Callable:
    """
    Decorator for handling errors in MCP tools and functions.

    Args:
        error_message: Custom error message prefix
        log_traceback: Whether to log full traceback
        return_on_error: Value to return on error (if None, re-raises)
        recoverable_exceptions: Tuple of exception types to treat as recoverable

    Usage:
        @handle_errors(error_message="Failed to fetch data", return_on_error={})
        async def my_tool(ctx, ...) -> Any:
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Union[T, Any]:
            try:
                return await func(*args, **kwargs)

            except SalesMCPError as e:
                # Log our custom errors with full context
                logger.error(
                    f"{error_message}: {e.message}",
                    error_type=e.__class__.__name__,
                    error_code=e.error_code,
                    details=e.details,
                    recoverable=e.recoverable,
                    function=func.__name__
                )

                if log_traceback:
                    logger.debug(event=f"Traceback: {traceback.format_exc()}")

                # If we have a context object, log to it too
                if args and hasattr(args[0], 'error'):
                    ctx = args[0]
                    await ctx.error(f"{error_message}: {e.message}")

                if return_on_error is not None:
                    return {
                        "status": "error",
                        "error": e.to_dict(),
                        "message": f"{error_message}: {e.message}"
                    }
                else:
                    raise

            except Exception as e:
                # Handle unexpected errors
                exception_type = type(e).__name__
                is_recoverable = (
                    recoverable_exceptions and
                    isinstance(e, recoverable_exceptions)
                )

                logger.error(
                    f"{error_message}: Unexpected error",
                    error_type=exception_type,
                    error_message=str(e),
                    recoverable=is_recoverable,
                    function=func.__name__
                )

                if log_traceback:
                    logger.error(event=f"Traceback: {traceback.format_exc()}")

                # If we have a context object, log to it too
                if args and hasattr(args[0], 'error'):
                    ctx = args[0]
                    await ctx.error(f"{error_message}: {str(e)}")

                if return_on_error is not None:
                    return {
                        "status": "error",
                        "error": {
                            "type": exception_type,
                            "message": str(e),
                            "recoverable": is_recoverable
                        },
                        "message": f"{error_message}: {str(e)}"
                    }
                else:
                    raise

        return wrapper
    return decorator


def handle_data_errors(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
    """Specialized error handler for data operations"""
    return handle_errors(
        error_message="Data operation failed",
        return_on_error={"status": "error", "data": None},
        recoverable_exceptions=(DataNotFoundError, DataValidationError)
    )(func)


def handle_crm_errors(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
    """Specialized error handler for CRM operations"""
    return handle_errors(
        error_message="CRM operation failed",
        return_on_error={"status": "error", "crm_data": None},
        recoverable_exceptions=(CRMError, APIError, RateLimitError, AuthenticationError)
    )(func)


def handle_prediction_errors(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
    """Specialized error handler for ML predictions"""
    return handle_errors(
        error_message="Prediction failed",
        return_on_error={"status": "error", "predictions": None},
        recoverable_exceptions=(PredictionError, InsufficientTrainingDataError)
    )(func)


def handle_process_errors(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
    """Specialized error handler for process execution"""
    return handle_errors(
        error_message="Process execution failed",
        return_on_error={"status": "error", "process_result": None},
        recoverable_exceptions=(ProcessExecutionError, WorkflowError)
    )(func)


# ============================================================================
# Error Recovery Utilities
# ============================================================================

class ErrorRecovery:
    """Utilities for error recovery and retry logic"""

    @staticmethod
    async def retry_with_backoff(
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential: bool = True,
        recoverable_exceptions: Optional[tuple] = None
    ) -> Any:
        """
        Retry a function with exponential backoff.

        Args:
            func: Async function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            exponential: Use exponential backoff if True, linear if False
            recoverable_exceptions: Tuple of exceptions to retry on

        Returns:
            Result of func if successful

        Raises:
            Last exception if all retries fail
        """
        import asyncio

        if recoverable_exceptions is None:
            recoverable_exceptions = (
                APIError, RateLimitError, CRMError,
                DatabaseError, CacheError
            )

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await func()

            except recoverable_exceptions as e:
                last_exception = e

                if attempt >= max_retries:
                    logger.error(
                        f"All retry attempts failed",
                        attempts=attempt + 1,
                        error=str(e)
                    )
                    raise

                # Calculate delay
                if exponential:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                else:
                    delay = min(base_delay * (attempt + 1), max_delay)

                logger.warning(
                    f"Retry attempt {attempt + 1}/{max_retries}",
                    error=str(e),
                    delay_seconds=delay
                )

                await asyncio.sleep(delay)

            except Exception as e:
                # Non-recoverable exception, fail immediately
                logger.error(event=f"Non-recoverable error during retry: {e}")
                raise

        # Should never reach here, but just in case
        if last_exception:
            raise last_exception


# ============================================================================
# Error Reporting Utilities
# ============================================================================

def format_error_for_user(error: Union[SalesMCPError, Exception]) -> Dict[str, Any]:
    """
    Format error for user-friendly display.

    Args:
        error: Exception to format

    Returns:
        Dictionary with user-friendly error information
    """
    if isinstance(error, SalesMCPError):
        return {
            "error": True,
            "message": error.message,
            "error_code": error.error_code,
            "recoverable": error.recoverable,
            "suggestions": _get_error_suggestions(error)
        }
    else:
        return {
            "error": True,
            "message": str(error),
            "error_code": type(error).__name__,
            "recoverable": False,
            "suggestions": ["Contact support if this error persists"]
        }


def _get_error_suggestions(error: SalesMCPError) -> list:
    """Get user-friendly suggestions for resolving an error"""
    suggestions = []

    if isinstance(error, DataNotFoundError):
        suggestions.append("Verify the resource ID is correct")
        suggestions.append("Check if the resource has been deleted")

    elif isinstance(error, AuthenticationError):
        suggestions.append("Verify your credentials are correct")
        suggestions.append("Check if your API key has expired")
        suggestions.append("Run health_check() to diagnose authentication issues")

    elif isinstance(error, RateLimitError):
        if "retry_after_seconds" in error.details:
            suggestions.append(f"Wait {error.details['retry_after_seconds']} seconds before retrying")
        else:
            suggestions.append("Wait a few minutes before retrying")
        suggestions.append("Consider implementing request throttling")

    elif isinstance(error, DatabaseError):
        suggestions.append("Check database connection")
        suggestions.append("Run health_check() to diagnose database issues")
        suggestions.append("Verify database file permissions")

    elif isinstance(error, ConfigurationError):
        suggestions.append("Check your environment variables")
        suggestions.append("Run health_check() to identify missing configuration")
        suggestions.append("Verify .env file is properly loaded")

    elif isinstance(error, InsufficientDataError):
        if "required_data" in error.details:
            required = ", ".join(error.details["required_data"])
            suggestions.append(f"Provide required data: {required}")

    elif isinstance(error, QuotaExceededError):
        if "limit" in error.details:
            suggestions.append(f"Current limit: {error.details['limit']}")
        suggestions.append("Contact administrator to increase quota")

    # Default suggestion
    if not suggestions:
        suggestions.append("Check the error details for more information")
        if error.recoverable:
            suggestions.append("This error is recoverable - you can retry the operation")

    return suggestions
