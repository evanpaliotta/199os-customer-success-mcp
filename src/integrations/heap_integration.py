"""
Heap Integration
Priority Score: 13
ICP Adoption: 30-40% of product analytics users

Digital insights platform providing:
- Event Tracking (automatic and custom)
- User Properties
- Account Properties
- Segments
- SQL Queries
- Funnel Analysis
- Session Replay
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from .base import (
    BaseIntegration,
    ConnectionTestResult,
    IntegrationStatus,
    ValidationError,
    APIError,
    AuthenticationError
)

logger = structlog.get_logger(__name__)


class HeapIntegration(BaseIntegration):
    """
    Heap API integration with API key authentication.

    Authentication:
    - API Key in Authorization header (Bearer token)
    - App ID for environment identification

    Rate Limits:
    - 120 requests per minute per app
    - Burst: 20 requests per second

    Documentation: https://developers.heap.io/reference/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ) -> Any:
        """
        Initialize Heap integration.

        Args:
            credentials: Heap credentials
                - api_key: Heap API key
                - app_id: Heap app ID
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="heap",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        self.app_id = credentials.get('app_id', '')

        if not self.api_key:
            raise ValidationError("Heap api_key is required")
        if not self.app_id:
            raise ValidationError("Heap app_id is required")

        self.base_url = "https://heapanalytics.com/api"

        logger.info(
            "heap_initialized",
            app_id=self.app_id,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Heap (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("heap_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Heap authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Heap API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            async with self.session.request(
                method,
                url,
                json=data,
                params=params,
                headers=headers
            ) as response:
                if response.status in (200, 201, 202, 204):
                    self.circuit_breaker._record_success(0.1)
                    if response.status == 204:
                        return {}
                    return await response.json()
                else:
                    error_text = await response.text()
                    error = APIError(
                        f"Heap API error ({response.status}): {error_text}",
                        response.status
                    )
                    self.circuit_breaker._record_failure(error)
                    raise error

        except APIError:
            raise
        except Exception as e:
            self.circuit_breaker._record_failure(e)
            raise APIError(f"Request failed: {str(e)}")

    async def test_connection(self) -> ConnectionTestResult:
        """Test connection to Heap API."""
        try:
            start_time = datetime.now()

            # Test with account info
            response = await self._make_request(
                method='GET',
                endpoint=f'/account/{self.app_id}'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Heap",
                response_time_ms=duration_ms,
                metadata={
                    'app_id': self.app_id,
                    'app_name': response.get('name'),
                    'integration_name': 'heap'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Heap connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # EVENT TRACKING API
    # ===================================================================

    async def track_event(
        self,
        identity: str,
        event: str,
        properties: Optional[Dict[str, Any]] = None,
        timestamp: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track a custom event.

        Args:
            identity: User identity (user ID or email)
            event: Event name
            properties: Event properties
            timestamp: Event timestamp (Unix seconds)
            idempotency_key: Idempotency key for deduplication

        Returns:
            Track confirmation

        Example:
            >>> await heap.track_event(
            ...     identity="user123",
            ...     event="Feature Adopted",
            ...     properties={
            ...         "feature_name": "advanced_reporting",
            ...         "plan": "Enterprise"
            ...     }
            ... )
        """
        event_data = {
            'app_id': self.app_id,
            'identity': identity,
            'event': event
        }

        if properties:
            event_data['properties'] = properties
        if timestamp:
            event_data['timestamp'] = timestamp
        if idempotency_key:
            event_data['idempotency_key'] = idempotency_key

        result = await self._make_request(
            method='POST',
            endpoint='/track',
            data=event_data
        )

        logger.info(
            "heap_event_tracked",
            identity=identity,
            event=event
        )

        return result

    async def track_batch_events(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Track multiple events in batch.

        Args:
            events: List of event objects with identity, event, properties

        Returns:
            Batch tracking confirmation

        Example:
            >>> events = [
            ...     {"identity": "user1", "event": "Page View", "properties": {"page": "/home"}},
            ...     {"identity": "user2", "event": "Button Click", "properties": {"button": "signup"}}
            ... ]
            >>> await heap.track_batch_events(events)
        """
        # Add app_id to each event
        for event in events:
            event['app_id'] = self.app_id

        result = await self._make_request(
            method='POST',
            endpoint='/track/batch',
            data={'events': events}
        )

        logger.info(
            "heap_batch_events_tracked",
            event_count=len(events)
        )

        return result

    # ===================================================================
    # USER PROPERTIES API
    # ===================================================================

    async def add_user_properties(
        self,
        identity: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add or update user properties.

        Args:
            identity: User identity (user ID or email)
            properties: User properties to set

        Returns:
            Update confirmation

        Example:
            >>> await heap.add_user_properties(
            ...     identity="user123",
            ...     properties={
            ...         "name": "John Doe",
            ...         "email": "john@example.com",
            ...         "plan": "Enterprise",
            ...         "role": "Admin",
            ...         "signup_date": "2024-01-15"
            ...     }
            ... )
        """
        data = {
            'app_id': self.app_id,
            'identity': identity,
            'properties': properties
        }

        result = await self._make_request(
            method='POST',
            endpoint='/add_user_properties',
            data=data
        )

        logger.info(
            "heap_user_properties_added",
            identity=identity,
            property_count=len(properties)
        )

        return result

    async def get_user_properties(
        self,
        identity: str
    ) -> Dict[str, Any]:
        """
        Get user properties.

        Args:
            identity: User identity (user ID or email)

        Returns:
            User properties
        """
        params = {
            'app_id': self.app_id,
            'identity': identity
        }

        return await self._make_request(
            method='GET',
            endpoint='/user_properties',
            params=params
        )

    # ===================================================================
    # ACCOUNT PROPERTIES API
    # ===================================================================

    async def add_account_properties(
        self,
        account_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add or update account properties.

        Args:
            account_id: Account ID
            properties: Account properties to set

        Returns:
            Update confirmation

        Example:
            >>> await heap.add_account_properties(
            ...     account_id="acme_corp",
            ...     properties={
            ...         "name": "Acme Corporation",
            ...         "plan": "Enterprise",
            ...         "arr": 50000,
            ...         "industry": "Technology",
            ...         "employees": 250
            ...     }
            ... )
        """
        data = {
            'app_id': self.app_id,
            'account_id': account_id,
            'properties': properties
        }

        result = await self._make_request(
            method='POST',
            endpoint='/add_account_properties',
            data=data
        )

        logger.info(
            "heap_account_properties_added",
            account_id=account_id,
            property_count=len(properties)
        )

        return result

    async def assign_user_to_account(
        self,
        identity: str,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Assign user to account.

        Args:
            identity: User identity
            account_id: Account ID

        Returns:
            Assignment confirmation
        """
        data = {
            'app_id': self.app_id,
            'identity': identity,
            'account_id': account_id
        }

        result = await self._make_request(
            method='POST',
            endpoint='/assign_user_to_account',
            data=data
        )

        logger.info(
            "heap_user_assigned_to_account",
            identity=identity,
            account_id=account_id
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
        """
        params = {'app_id': self.app_id}

        result = await self._make_request(
            method='GET',
            endpoint='/segments',
            params=params
        )

        return result.get('segments', [])

    async def get_segment(self, segment_id: str) -> Dict[str, Any]:
        """
        Get segment by ID.

        Args:
            segment_id: Heap segment ID

        Returns:
            Segment data
        """
        params = {
            'app_id': self.app_id,
            'segment_id': segment_id
        }

        return await self._make_request(
            method='GET',
            endpoint='/segment',
            params=params
        )

    async def get_segment_users(
        self,
        segment_id: str,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Get users in segment.

        Args:
            segment_id: Heap segment ID
            limit: Results limit

        Returns:
            List of users in segment
        """
        params = {
            'app_id': self.app_id,
            'segment_id': segment_id,
            'limit': limit
        }

        return await self._make_request(
            method='GET',
            endpoint='/segment_users',
            params=params
        )

    # ===================================================================
    # SQL QUERIES API
    # ===================================================================

    async def execute_sql_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute SQL query against Heap data.

        Args:
            query: SQL query string
            parameters: Query parameters for parameterized queries

        Returns:
            Query results

        Example:
            >>> query = '''
            ...     SELECT user_id, COUNT(*) as event_count
            ...     FROM events
            ...     WHERE event_name = 'Feature Used'
            ...     AND time > NOW() - INTERVAL '30 days'
            ...     GROUP BY user_id
            ...     ORDER BY event_count DESC
            ...     LIMIT 100
            ... '''
            >>> results = await heap.execute_sql_query(query)
        """
        data = {
            'app_id': self.app_id,
            'query': query
        }

        if parameters:
            data['parameters'] = parameters

        result = await self._make_request(
            method='POST',
            endpoint='/sql',
            data=data
        )

        logger.info(
            "heap_sql_query_executed",
            row_count=len(result.get('results', []))
        )

        return result

    async def get_query_status(self, query_id: str) -> Dict[str, Any]:
        """
        Get SQL query execution status.

        Args:
            query_id: Query execution ID

        Returns:
            Query status and results if complete
        """
        params = {
            'app_id': self.app_id,
            'query_id': query_id
        }

        return await self._make_request(
            method='GET',
            endpoint='/sql/status',
            params=params
        )

    # ===================================================================
    # REPORTS API
    # ===================================================================

    async def get_event_report(
        self,
        event_name: str,
        start_date: str,
        end_date: str,
        breakdown_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get event report.

        Args:
            event_name: Event name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            breakdown_by: Property to breakdown by

        Returns:
            Event report data

        Example:
            >>> report = await heap.get_event_report(
            ...     event_name="Feature Used",
            ...     start_date="2024-01-01",
            ...     end_date="2024-12-31",
            ...     breakdown_by="plan"
            ... )
        """
        params = {
            'app_id': self.app_id,
            'event': event_name,
            'start_date': start_date,
            'end_date': end_date
        }

        if breakdown_by:
            params['breakdown_by'] = breakdown_by

        return await self._make_request(
            method='GET',
            endpoint='/reports/event',
            params=params
        )

    async def get_funnel_report(
        self,
        funnel_id: str,
        start_date: str,
        end_date: str,
        segment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get funnel report.

        Args:
            funnel_id: Heap funnel ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            segment_id: Filter by segment ID

        Returns:
            Funnel report data with conversion rates
        """
        params = {
            'app_id': self.app_id,
            'funnel_id': funnel_id,
            'start_date': start_date,
            'end_date': end_date
        }

        if segment_id:
            params['segment_id'] = segment_id

        return await self._make_request(
            method='GET',
            endpoint='/reports/funnel',
            params=params
        )

    async def get_retention_report(
        self,
        initial_event: str,
        return_event: str,
        start_date: str,
        end_date: str,
        cohort_period: str = "day"
    ) -> Dict[str, Any]:
        """
        Get retention report.

        Args:
            initial_event: Initial event name
            return_event: Return event name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            cohort_period: Cohort period (day, week, month)

        Returns:
            Retention report data
        """
        params = {
            'app_id': self.app_id,
            'initial_event': initial_event,
            'return_event': return_event,
            'start_date': start_date,
            'end_date': end_date,
            'cohort_period': cohort_period
        }

        return await self._make_request(
            method='GET',
            endpoint='/reports/retention',
            params=params
        )

    # ===================================================================
    # SESSION REPLAY API
    # ===================================================================

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get session replay data.

        Args:
            session_id: Heap session ID

        Returns:
            Session replay data with events
        """
        params = {
            'app_id': self.app_id,
            'session_id': session_id
        }

        return await self._make_request(
            method='GET',
            endpoint='/session',
            params=params
        )

    async def list_user_sessions(
        self,
        identity: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List user sessions.

        Args:
            identity: User identity
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Results limit

        Returns:
            List of user sessions
        """
        params = {
            'app_id': self.app_id,
            'identity': identity,
            'limit': limit
        }

        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        result = await self._make_request(
            method='GET',
            endpoint='/sessions',
            params=params
        )

        return result.get('sessions', [])

    async def close(self) -> Any:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("heap_session_closed")
