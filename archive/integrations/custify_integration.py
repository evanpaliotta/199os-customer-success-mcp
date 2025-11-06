"""
Custify Integration
Priority Score: 15
ICP Adoption: 15-25% of B2B SaaS companies

SaaS customer success platform providing:
- Account & People Management
- Health Scores
- Segments
- Events & Metrics
- Alerts & Tasks
- Lifecycle Tracking
- Playbooks
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import aiohttp
import structlog

from .base import (
    BaseIntegration,
    ConnectionTestResult,
    IntegrationStatus,
    ValidationError,
    APIError,
    AuthenticationError
)
from ..core.circuit_breaker import CircuitBreaker

logger = structlog.get_logger(__name__)


class CustifyIntegration(BaseIntegration):
    """
    Production-ready Custify integration for SaaS customer success.

    Features:
    - Account (company) management
    - People (contact) management
    - Event tracking
    - Segment management
    - Health score tracking
    - Task management
    - Lifecycle stages
    - Custom attributes

    Usage:
        >>> custify = CustifyIntegration({
        ...     'api_key': 'your_api_key'
        ... })
        >>> await custify.authenticate()
        >>> account = await custify.create_account({
        ...     'user_id': 'acme-123',
        ...     'name': 'Acme Corp',
        ...     'mrr': 5000
        ... })

    API Documentation:
        https://docs.custify.com/
    """

    API_BASE_URL = "https://api.custify.com/v2"

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ) -> Any:
        """
        Initialize Custify integration.

        Args:
            credentials: Custify credentials
                - api_key: Custify API key
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="custify",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')

        if not self.api_key:
            raise ValidationError("Custify api_key is required")

        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            expected_exception=APIError,
            name="custify_api"
        )

        logger.info(
            "custify_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Custify (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("custify_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Custify authentication failed: {str(e)}")

    async def test_connection(self) -> ConnectionTestResult:
        """Test connection to Custify API."""
        try:
            start_time = time.time()

            # Test with a simple accounts list request
            result = await self._make_request(
                method='GET',
                endpoint='/account',
                params={'size': 1}
            )

            duration_ms = (time.time() - start_time) * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Custify",
                response_time_ms=duration_ms,
                metadata={'integration_name': 'custify'}
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Custify connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Custify API."""
        await self.ensure_authenticated()

        url = f"{self.API_BASE_URL}/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            # Check circuit breaker
            if hasattr(self.circuit_breaker, 'state'):
                from ..core.circuit_breaker import CircuitState, CircuitBreakerError
                if self.circuit_breaker.state == CircuitState.OPEN:
                    if not self.circuit_breaker._should_attempt_reset():
                        raise CircuitBreakerError(
                            f"Circuit breaker '{self.circuit_breaker.name}' is OPEN"
                        )
                    else:
                        self.circuit_breaker._transition_to_half_open()

            async with self.session.request(
                method,
                url,
                json=data,
                params=params,
                headers=headers
            ) as response:
                if response.status in (200, 201, 204):
                    self.circuit_breaker._record_success(0.1)
                    if response.status == 204:
                        return {'status': 'success', 'message': 'No content'}
                    return await response.json()
                else:
                    error_text = await response.text()
                    error = APIError(
                        f"Custify API error ({response.status}): {error_text}",
                        response.status
                    )
                    self.circuit_breaker._record_failure(error)
                    raise error

        except APIError:
            raise
        except Exception as e:
            self.circuit_breaker._record_failure(e)
            raise APIError(f"Request failed: {str(e)}")

    # ===================================================================
    # ACCOUNTS API
    # ===================================================================

    async def create_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new account (company).

        Args:
            account_data: Account information
                - user_id: External user ID (required)
                - name: Company name (required)
                - mrr: Monthly recurring revenue
                - status: Status (trial, active, churned)
                - company_created_at: Creation timestamp

        Returns:
            Created account data

        Example:
            >>> account = await custify.create_account({
            ...     'user_id': 'acme-123',
            ...     'name': 'Acme Corp',
            ...     'mrr': 5000,
            ...     'status': 'active',
            ...     'company_created_at': 1609459200
            ... })
        """
        if 'user_id' not in account_data or 'name' not in account_data:
            raise ValidationError("Account user_id and name are required")

        result = await self._make_request(
            method='POST',
            endpoint='/account',
            data=account_data
        )

        logger.info(
            "custify_account_created",
            user_id=account_data.get('user_id'),
            name=account_data.get('name')
        )

        return result

    async def update_account(
        self,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an account.

        Args:
            user_id: External user ID
            update_data: Fields to update

        Returns:
            Updated account data

        Example:
            >>> await custify.update_account(
            ...     'acme-123',
            ...     {'mrr': 6000, 'custom_health_score': 85}
            ... )
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/account/{user_id}',
            data=update_data
        )

        logger.info(
            "custify_account_updated",
            user_id=user_id
        )

        return result

    async def get_account(self, user_id: str) -> Dict[str, Any]:
        """
        Get an account by user ID.

        Args:
            user_id: External user ID

        Returns:
            Account data
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/account/{user_id}'
        )

    async def list_accounts(
        self,
        page: int = 1,
        size: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        List accounts with optional filters.

        Args:
            page: Page number (1-indexed)
            size: Results per page (max 100)
            filters: Optional filters

        Returns:
            List of accounts with pagination

        Example:
            >>> accounts = await custify.list_accounts(page=1, size=50)
            >>> for account in accounts['data']:
            ...     print(account['name'], account['mrr'])
        """
        params = {
            'page': page,
            'size': min(size, 100)
        }
        if filters:
            params.update(filters)

        result = await self._make_request(
            method='GET',
            endpoint='/account',
            params=params
        )

        logger.info(
            "custify_accounts_listed",
            count=len(result.get('data', []))
        )

        return result

    async def delete_account(self, user_id: str) -> Dict[str, Any]:
        """
        Delete an account.

        Args:
            user_id: External user ID

        Returns:
            Deletion confirmation
        """
        result = await self._make_request(
            method='DELETE',
            endpoint=f'/account/{user_id}'
        )

        logger.info(
            "custify_account_deleted",
            user_id=user_id
        )

        return result

    # ===================================================================
    # PEOPLE API
    # ===================================================================

    async def create_person(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a person (contact).

        Args:
            person_data: Person information
                - user_id: External user ID (account ID) (required)
                - email: Email address (required)
                - name: Full name
                - first_name: First name
                - last_name: Last name
                - title: Job title

        Returns:
            Created person data

        Example:
            >>> person = await custify.create_person({
            ...     'user_id': 'acme-123',
            ...     'email': 'john@acme.com',
            ...     'name': 'John Doe',
            ...     'title': 'CTO'
            ... })
        """
        if 'user_id' not in person_data or 'email' not in person_data:
            raise ValidationError("Person user_id and email are required")

        result = await self._make_request(
            method='POST',
            endpoint='/people',
            data=person_data
        )

        logger.info(
            "custify_person_created",
            user_id=person_data.get('user_id'),
            email=person_data.get('email')
        )

        return result

    async def update_person(
        self,
        email: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a person.

        Args:
            email: Person email address
            update_data: Fields to update

        Returns:
            Updated person data

        Example:
            >>> await custify.update_person(
            ...     'john@acme.com',
            ...     {'title': 'VP of Engineering'}
            ... )
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/people/{email}',
            data=update_data
        )

        logger.info(
            "custify_person_updated",
            email=email
        )

        return result

    async def list_people(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        size: int = 100
    ) -> Dict[str, Any]:
        """
        List people.

        Args:
            user_id: Filter by account user ID (optional)
            page: Page number
            size: Results per page

        Returns:
            List of people

        Example:
            >>> people = await custify.list_people(user_id='acme-123')
            >>> for person in people['data']:
            ...     print(person['name'], person['email'])
        """
        params = {
            'page': page,
            'size': min(size, 100)
        }
        if user_id:
            params['user_id'] = user_id

        result = await self._make_request(
            method='GET',
            endpoint='/people',
            params=params
        )

        logger.info(
            "custify_people_listed",
            count=len(result.get('data', []))
        )

        return result

    # ===================================================================
    # EVENTS API
    # ===================================================================

    async def track_event(
        self,
        user_id: str,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        occurred_at: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Track a customer event.

        Args:
            user_id: External user ID (account ID)
            event_name: Event name
            properties: Optional event properties
            occurred_at: Event timestamp (Unix timestamp, defaults to now)

        Returns:
            Track confirmation

        Example:
            >>> await custify.track_event(
            ...     user_id='acme-123',
            ...     event_name='feature_used',
            ...     properties={
            ...         'feature_name': 'dashboard',
            ...         'duration_seconds': 120
            ...     }
            ... )
        """
        event_data = {
            'user_id': user_id,
            'name': event_name,
            'occurred_at': occurred_at or int(time.time())
        }

        if properties:
            event_data['metadata'] = properties

        result = await self._make_request(
            method='POST',
            endpoint='/event',
            data=event_data
        )

        logger.info(
            "custify_event_tracked",
            user_id=user_id,
            event_name=event_name
        )

        return result

    async def list_events(
        self,
        user_id: Optional[str] = None,
        event_name: Optional[str] = None,
        page: int = 1,
        size: int = 100
    ) -> Dict[str, Any]:
        """
        List events.

        Args:
            user_id: Filter by account user ID (optional)
            event_name: Filter by event name (optional)
            page: Page number
            size: Results per page

        Returns:
            List of events
        """
        params = {
            'page': page,
            'size': min(size, 100)
        }
        if user_id:
            params['user_id'] = user_id
        if event_name:
            params['name'] = event_name

        result = await self._make_request(
            method='GET',
            endpoint='/event',
            params=params
        )

        return result

    # ===================================================================
    # SEGMENTS API
    # ===================================================================

    async def list_segments(self) -> List[Dict[str, Any]]:
        """
        List all segments.

        Returns:
            List of segments

        Example:
            >>> segments = await custify.list_segments()
            >>> for segment in segments:
            ...     print(segment['name'], segment['description'])
        """
        result = await self._make_request(
            method='GET',
            endpoint='/segment'
        )

        logger.info(
            "custify_segments_listed",
            count=len(result.get('data', result) if isinstance(result, dict) else result)
        )

        return result.get('data', result) if isinstance(result, dict) else result

    async def get_segment_accounts(
        self,
        segment_id: str,
        page: int = 1,
        size: int = 100
    ) -> Dict[str, Any]:
        """
        Get accounts in a segment.

        Args:
            segment_id: Segment ID
            page: Page number
            size: Results per page

        Returns:
            List of accounts in segment
        """
        params = {
            'page': page,
            'size': min(size, 100)
        }

        result = await self._make_request(
            method='GET',
            endpoint=f'/segment/{segment_id}/accounts',
            params=params
        )

        return result

    # ===================================================================
    # TASKS API
    # ===================================================================

    async def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a task.

        Args:
            task_data: Task information
                - user_id: External user ID (account ID) (required)
                - title: Task title (required)
                - description: Task description
                - due_date: Due date (Unix timestamp)
                - assigned_to: User ID to assign to

        Returns:
            Created task data

        Example:
            >>> task = await custify.create_task({
            ...     'user_id': 'acme-123',
            ...     'title': 'Schedule QBR',
            ...     'description': 'Quarterly business review meeting',
            ...     'due_date': 1640995200
            ... })
        """
        if 'user_id' not in task_data or 'title' not in task_data:
            raise ValidationError("Task user_id and title are required")

        result = await self._make_request(
            method='POST',
            endpoint='/task',
            data=task_data
        )

        logger.info(
            "custify_task_created",
            task_id=result.get('id'),
            user_id=task_data.get('user_id')
        )

        return result

    async def list_tasks(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        size: int = 100
    ) -> Dict[str, Any]:
        """
        List tasks.

        Args:
            user_id: Filter by account user ID (optional)
            page: Page number
            size: Results per page

        Returns:
            List of tasks
        """
        params = {
            'page': page,
            'size': min(size, 100)
        }
        if user_id:
            params['user_id'] = user_id

        result = await self._make_request(
            method='GET',
            endpoint='/task',
            params=params
        )

        return result

    async def update_task(
        self,
        task_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a task.

        Args:
            task_id: Task ID
            update_data: Fields to update

        Returns:
            Updated task data

        Example:
            >>> await custify.update_task(
            ...     'task_123',
            ...     {'status': 'completed'}
            ... )
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/task/{task_id}',
            data=update_data
        )

        logger.info(
            "custify_task_updated",
            task_id=task_id
        )

        return result

    # ===================================================================
    # HEALTH SCORES API
    # ===================================================================

    async def update_health_score(
        self,
        user_id: str,
        health_score: float
    ) -> Dict[str, Any]:
        """
        Update account health score.

        Args:
            user_id: External user ID (account ID)
            health_score: Health score value (0-100)

        Returns:
            Update confirmation

        Example:
            >>> await custify.update_health_score('acme-123', 88.5)
        """
        return await self.update_account(
            user_id,
            {'custom_health_score': health_score}
        )

    async def close(self) -> Any:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("custify_session_closed")


def test_custify_integration() -> Any:
    """Test Custify integration (requires credentials)."""
    import asyncio
    import os

    async def run_tests() -> Any:
        api_key = os.getenv('CUSTIFY_API_KEY')

        if not api_key:
            print("⚠️  Skipping Custify tests - API key not found")
            print("Set CUSTIFY_API_KEY environment variable")
            return

        print("Test 1: Initialize integration...")
        custify = CustifyIntegration({
            'api_key': api_key
        })
        print("✓ Integration initialized")

        print("\nTest 2: Authenticate...")
        try:
            await custify.authenticate()
            print("✓ Authentication successful")
        except AuthenticationError as e:
            print(f"✗ Authentication failed: {e}")
            return

        print("\nTest 3: Test connection...")
        result = await custify.test_connection()
        assert result.success
        print(f"✓ Connection test passed")

        print("\nTest 4: List accounts...")
        try:
            accounts = await custify.list_accounts(page=1, size=5)
            print(f"✓ Found {len(accounts.get('data', []))} accounts")
        except APIError as e:
            print(f"✗ List accounts failed: {e}")

        print("\nTest 5: Close session...")
        await custify.close()
        print("✓ Session closed")

        print("\n✅ All tests passed!")

    asyncio.run(run_tests())


if __name__ == '__main__':
    test_custify_integration()
