"""Intercom Customer Messaging Integration

Production-ready Intercom API client with:
- User management (create, update, retrieve)
- Messaging (send messages, create notes)
- Event tracking
- Tag management
- Retry logic with exponential backoff
- Circuit breaker pattern
- Rate limit handling
"""

import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import structlog
from intercom import Intercom
from intercom.errors import (
    UnauthorizedError as AuthenticationError,
    NotFoundError as ResourceNotFound,
    BadRequestError,
    ForbiddenError,
    UnprocessableEntityError
)

logger = structlog.get_logger(__name__)


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def call_failed(self):
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                "Circuit breaker opened",
                failure_count=self.failure_count,
                threshold=self.failure_threshold
            )

    def call_succeeded(self):
        """Record a successful call"""
        self.failure_count = 0
        self.state = "closed"

    def can_attempt(self) -> bool:
        """Check if we can attempt a call"""
        if self.state == "closed":
            return True

        if self.state == "open":
            # Check if timeout has passed
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
                self.state = "half_open"
                logger.info("Circuit breaker entering half-open state")
                return True
            return False

        # half_open state - allow one attempt
        return True


class IntercomClient:
    """Production-ready Intercom API client"""

    def __init__(self, access_token: Optional[str] = None):
        """Initialize Intercom client

        Args:
            access_token: Intercom access token (defaults to INTERCOM_ACCESS_TOKEN env var)
        """
        self.access_token = access_token or os.getenv("INTERCOM_ACCESS_TOKEN")

        if not self.access_token:
            logger.warning("Intercom credentials not configured")
            self.client = None
        else:
            try:
                self.client = Intercom(token=self.access_token)
                logger.info("Intercom client initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize Intercom client", error=str(e))
                self.client = None

        # Circuit breaker for fault tolerance
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

        # Rate limiting tracking
        self.rate_limit_remaining = None
        self.rate_limit_reset = None

    def _check_configured(self) -> Dict[str, Any]:
        """Check if client is configured"""
        if not self.client:
            return {
                "success": False,
                "error": "Intercom not configured. Set INTERCOM_ACCESS_TOKEN environment variable."
            }
        return None

    def _retry_with_backoff(self, func, *args, max_retries: int = 3, **kwargs) -> Any:
        """Execute function with exponential backoff retry logic

        Args:
            func: Function to execute
            max_retries: Maximum number of retry attempts
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result or error dict
        """
        # Check circuit breaker
        if not self.circuit_breaker.can_attempt():
            return {
                "success": False,
                "error": "Circuit breaker is open - Intercom API unavailable"
            }

        last_exception = None

        for attempt in range(max_retries):
            try:
                result = func(*args, **kwargs)
                self.circuit_breaker.call_succeeded()
                return result

            except (ForbiddenError, UnprocessableEntityError) as e:
                # Rate limit or forbidden - could be rate limiting
                retry_after = 60  # Default retry after
                logger.warning(
                    "Intercom rate limit or forbidden error",
                    error=str(e),
                    retry_after=retry_after,
                    attempt=attempt + 1
                )

                if attempt < max_retries - 1:
                    time.sleep(retry_after)
                    continue
                else:
                    self.circuit_breaker.call_failed()
                    return {
                        "success": False,
                        "error": f"Rate limit or forbidden error. Retry after {retry_after} seconds."
                    }

            except AuthenticationError as e:
                # Authentication errors are not retryable
                logger.error("Intercom authentication failed", error=str(e))
                return {
                    "success": False,
                    "error": "Authentication failed. Check your Intercom access token."
                }

            except ResourceNotFound as e:
                # Resource not found - don't retry
                logger.warning("Intercom resource not found", error=str(e))
                return {
                    "success": False,
                    "error": f"Resource not found: {str(e)}"
                }

            except Exception as e:
                # Unexpected error
                logger.error("Unexpected error calling Intercom API", error=str(e), attempt=attempt + 1)
                self.circuit_breaker.call_failed()
                last_exception = e
                break

        # All retries exhausted
        return {
            "success": False,
            "error": f"Failed after {max_retries} attempts: {str(last_exception)}"
        }

    def send_message(
        self,
        user_email: Optional[str] = None,
        user_id: Optional[str] = None,
        message_type: str = "inapp",
        subject: Optional[str] = None,
        body: str = None,
        from_admin_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send message to user via Intercom

        Args:
            user_email: User's email address (required if user_id not provided)
            user_id: Intercom user ID (required if user_email not provided)
            message_type: Type of message ('inapp', 'email')
            subject: Message subject (required for email)
            body: Message body (required)
            from_admin_id: Admin ID to send from (optional)

        Returns:
            Dict with success status and message details
        """
        error = self._check_configured()
        if error:
            return error

        if not user_email and not user_id:
            return {
                "success": False,
                "error": "Must provide either user_email or user_id"
            }

        if not body:
            return {
                "success": False,
                "error": "Message body is required"
            }

        if message_type == "email" and not subject:
            return {
                "success": False,
                "error": "Subject is required for email messages"
            }

        try:
            # Prepare message data
            message_data = {
                "message_type": message_type,
                "body": body
            }

            if subject:
                message_data["subject"] = subject

            if from_admin_id:
                message_data["from"] = {
                    "type": "admin",
                    "id": from_admin_id
                }

            # Identify user
            if user_email:
                message_data["to"] = {
                    "type": "user",
                    "email": user_email
                }
            else:
                message_data["to"] = {
                    "type": "user",
                    "id": user_id
                }

            # Send message with retry
            result = self._retry_with_backoff(
                self.client.messages.create,
                **message_data
            )

            if isinstance(result, dict) and not result.get("success", True):
                return result

            logger.info(
                "Message sent successfully",
                user_email=user_email,
                user_id=user_id,
                message_type=message_type
            )

            return {
                "success": True,
                "message_id": result.id if hasattr(result, 'id') else None,
                "message_type": message_type,
                "recipient": user_email or user_id
            }

        except Exception as e:
            logger.error("Error sending message", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def create_note(
        self,
        user_email: Optional[str] = None,
        user_id: Optional[str] = None,
        body: str = None,
        admin_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add note to user profile

        Args:
            user_email: User's email address (required if user_id not provided)
            user_id: Intercom user ID (required if user_email not provided)
            body: Note content (required)
            admin_id: Admin ID creating the note (optional)

        Returns:
            Dict with success status and note details
        """
        error = self._check_configured()
        if error:
            return error

        if not user_email and not user_id:
            return {
                "success": False,
                "error": "Must provide either user_email or user_id"
            }

        if not body:
            return {
                "success": False,
                "error": "Note body is required"
            }

        try:
            # Find user first
            user_data = self.get_user(user_email=user_email, user_id=user_id)
            if not user_data.get("success"):
                return user_data

            intercom_user_id = user_data.get("user", {}).get("id")
            if not intercom_user_id:
                return {
                    "success": False,
                    "error": "Could not find user ID"
                }

            # Prepare note data
            note_data = {
                "body": body,
                "user": {
                    "id": intercom_user_id
                }
            }

            if admin_id:
                note_data["admin_id"] = admin_id

            # Create note with retry
            result = self._retry_with_backoff(
                self.client.notes.create,
                **note_data
            )

            if isinstance(result, dict) and not result.get("success", True):
                return result

            logger.info(
                "Note created successfully",
                user_email=user_email,
                user_id=user_id
            )

            return {
                "success": True,
                "note_id": result.id if hasattr(result, 'id') else None,
                "user_id": intercom_user_id,
                "body": body
            }

        except Exception as e:
            logger.error("Error creating note", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def track_event(
        self,
        user_email: Optional[str] = None,
        user_id: Optional[str] = None,
        event_name: str = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[int] = None
    ) -> Dict[str, Any]:
        """Track custom event for user

        Args:
            user_email: User's email address (required if user_id not provided)
            user_id: Intercom user ID (required if user_email not provided)
            event_name: Name of the event (required)
            metadata: Optional event metadata
            created_at: Optional Unix timestamp (defaults to now)

        Returns:
            Dict with success status and event details
        """
        error = self._check_configured()
        if error:
            return error

        if not user_email and not user_id:
            return {
                "success": False,
                "error": "Must provide either user_email or user_id"
            }

        if not event_name:
            return {
                "success": False,
                "error": "Event name is required"
            }

        try:
            # Prepare event data
            event_data = {
                "event_name": event_name
            }

            if user_email:
                event_data["email"] = user_email
            else:
                event_data["user_id"] = user_id

            if metadata:
                event_data["metadata"] = metadata

            if created_at:
                event_data["created_at"] = created_at
            else:
                event_data["created_at"] = int(time.time())

            # Track event with retry
            result = self._retry_with_backoff(
                self.client.events.create,
                **event_data
            )

            if isinstance(result, dict) and not result.get("success", True):
                return result

            logger.info(
                "Event tracked successfully",
                event_name=event_name,
                user_email=user_email,
                user_id=user_id
            )

            return {
                "success": True,
                "event_name": event_name,
                "user": user_email or user_id,
                "metadata": metadata
            }

        except Exception as e:
            logger.error("Error tracking event", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def get_user(
        self,
        user_email: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Retrieve user by email or ID

        Args:
            user_email: User's email address (required if user_id not provided)
            user_id: Intercom user ID (required if user_email not provided)

        Returns:
            Dict with success status and user details
        """
        error = self._check_configured()
        if error:
            return error

        if not user_email and not user_id:
            return {
                "success": False,
                "error": "Must provide either user_email or user_id"
            }

        try:
            # Retrieve user with retry
            if user_email:
                result = self._retry_with_backoff(
                    self.client.users.find,
                    email=user_email
                )
            else:
                result = self._retry_with_backoff(
                    self.client.users.find,
                    id=user_id
                )

            if isinstance(result, dict) and not result.get("success", True):
                return result

            logger.info(
                "User retrieved successfully",
                user_email=user_email,
                user_id=user_id
            )

            # Extract relevant user data
            user_data = {
                "id": result.id if hasattr(result, 'id') else None,
                "email": result.email if hasattr(result, 'email') else None,
                "name": result.name if hasattr(result, 'name') else None,
                "user_id": result.user_id if hasattr(result, 'user_id') else None,
                "signed_up_at": result.signed_up_at if hasattr(result, 'signed_up_at') else None,
                "last_seen_at": result.last_seen_at if hasattr(result, 'last_seen_at') else None,
                "custom_attributes": result.custom_attributes if hasattr(result, 'custom_attributes') else {}
            }

            return {
                "success": True,
                "user": user_data
            }

        except Exception as e:
            logger.error("Error retrieving user", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def create_user(
        self,
        email: str,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        custom_attributes: Optional[Dict[str, Any]] = None,
        signed_up_at: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create or update user profile

        Args:
            email: User's email address (required)
            user_id: External user ID (optional)
            name: User's name (optional)
            phone: User's phone number (optional)
            custom_attributes: Custom attributes dict (optional)
            signed_up_at: Unix timestamp of signup (optional)

        Returns:
            Dict with success status and user details
        """
        error = self._check_configured()
        if error:
            return error

        if not email:
            return {
                "success": False,
                "error": "Email is required"
            }

        try:
            # Prepare user data
            user_data = {
                "email": email
            }

            if user_id:
                user_data["user_id"] = user_id
            if name:
                user_data["name"] = name
            if phone:
                user_data["phone"] = phone
            if custom_attributes:
                user_data["custom_attributes"] = custom_attributes
            if signed_up_at:
                user_data["signed_up_at"] = signed_up_at

            # Create/update user with retry
            result = self._retry_with_backoff(
                self.client.users.create,
                **user_data
            )

            if isinstance(result, dict) and not result.get("success", True):
                return result

            logger.info(
                "User created/updated successfully",
                email=email,
                user_id=user_id
            )

            return {
                "success": True,
                "user": {
                    "id": result.id if hasattr(result, 'id') else None,
                    "email": result.email if hasattr(result, 'email') else None,
                    "user_id": result.user_id if hasattr(result, 'user_id') else None,
                    "name": result.name if hasattr(result, 'name') else None
                }
            }

        except Exception as e:
            logger.error("Error creating user", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def add_tag(
        self,
        user_email: Optional[str] = None,
        user_id: Optional[str] = None,
        tag_name: str = None
    ) -> Dict[str, Any]:
        """Add tag to user for segmentation

        Args:
            user_email: User's email address (required if user_id not provided)
            user_id: Intercom user ID (required if user_email not provided)
            tag_name: Name of tag to add (required)

        Returns:
            Dict with success status and tag details
        """
        error = self._check_configured()
        if error:
            return error

        if not user_email and not user_id:
            return {
                "success": False,
                "error": "Must provide either user_email or user_id"
            }

        if not tag_name:
            return {
                "success": False,
                "error": "Tag name is required"
            }

        try:
            # Find user first
            user_data = self.get_user(user_email=user_email, user_id=user_id)
            if not user_data.get("success"):
                return user_data

            intercom_user_id = user_data.get("user", {}).get("id")
            if not intercom_user_id:
                return {
                    "success": False,
                    "error": "Could not find user ID"
                }

            # Create or find tag
            tag_data = {
                "name": tag_name,
                "users": [{"id": intercom_user_id}]
            }

            # Apply tag with retry
            result = self._retry_with_backoff(
                self.client.tags.tag,
                name=tag_name,
                users=[{"id": intercom_user_id}]
            )

            if isinstance(result, dict) and not result.get("success", True):
                return result

            logger.info(
                "Tag added successfully",
                tag_name=tag_name,
                user_email=user_email,
                user_id=user_id
            )

            return {
                "success": True,
                "tag_name": tag_name,
                "user_id": intercom_user_id
            }

        except Exception as e:
            logger.error("Error adding tag", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def remove_tag(
        self,
        user_email: Optional[str] = None,
        user_id: Optional[str] = None,
        tag_name: str = None
    ) -> Dict[str, Any]:
        """Remove tag from user

        Args:
            user_email: User's email address (required if user_id not provided)
            user_id: Intercom user ID (required if user_email not provided)
            tag_name: Name of tag to remove (required)

        Returns:
            Dict with success status
        """
        error = self._check_configured()
        if error:
            return error

        if not user_email and not user_id:
            return {
                "success": False,
                "error": "Must provide either user_email or user_id"
            }

        if not tag_name:
            return {
                "success": False,
                "error": "Tag name is required"
            }

        try:
            # Find user first
            user_data = self.get_user(user_email=user_email, user_id=user_id)
            if not user_data.get("success"):
                return user_data

            intercom_user_id = user_data.get("user", {}).get("id")
            if not intercom_user_id:
                return {
                    "success": False,
                    "error": "Could not find user ID"
                }

            # Remove tag with retry
            result = self._retry_with_backoff(
                self.client.tags.untag,
                name=tag_name,
                users=[{"id": intercom_user_id, "untag": True}]
            )

            if isinstance(result, dict) and not result.get("success", True):
                return result

            logger.info(
                "Tag removed successfully",
                tag_name=tag_name,
                user_email=user_email,
                user_id=user_id
            )

            return {
                "success": True,
                "tag_name": tag_name,
                "user_id": intercom_user_id
            }

        except Exception as e:
            logger.error("Error removing tag", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
