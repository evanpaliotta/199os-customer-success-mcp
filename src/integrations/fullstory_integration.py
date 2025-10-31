"""
FullStory Integration
Priority Score: 11
ICP Adoption: 35-45% of digital experience teams

Digital experience intelligence platform providing:
- Session Replay Retrieval
- User Events Tracking
- Segments Management
- Funnels Analysis
- Search and Filters
- User Properties
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


class FullStoryIntegration(BaseIntegration):
    """
    FullStory API integration with API key authentication.

    Authentication:
    - API Key in Authorization header (Bearer token)
    - Account ID required for some operations

    Rate Limits:
    - 1000 requests per hour
    - Burst: 10 requests per second

    Documentation: https://developer.fullstory.com/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 360
    ) -> Any:
        """
        Initialize FullStory integration.

        Args:
            credentials: FullStory credentials
                - api_key: FullStory API key
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 360 = 6 min)
        """
        super().__init__(
            integration_name="fullstory",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        if not self.api_key:
            raise ValidationError("FullStory api_key is required")

        self.base_url = "https://api.fullstory.com"

        logger.info(
            "fullstory_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with FullStory (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("fullstory_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"FullStory authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to FullStory API."""
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
                        f"FullStory API error ({response.status}): {error_text}",
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
        """Test connection to FullStory API."""
        try:
            start_time = datetime.now()

            # Test with segments list
            response = await self._make_request(
                method='GET',
                endpoint='/segments/v1'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to FullStory",
                response_time_ms=duration_ms,
                metadata={
                    'segment_count': len(response.get('segments', [])),
                    'integration_name': 'fullstory'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"FullStory connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # SESSIONS API
    # ===================================================================

    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List sessions with filters.

        Args:
            user_id: Filter by user ID
            email: Filter by user email
            start_time: Start time (ISO 8601)
            end_time: End time (ISO 8601)
            limit: Results limit (max: 100)

        Returns:
            List of sessions

        Example:
            >>> sessions = await fullstory.list_sessions(
            ...     email="user@example.com",
            ...     start_time="2024-01-01T00:00:00Z",
            ...     end_time="2024-12-31T23:59:59Z",
            ...     limit=25
            ... )
        """
        params = {
            'limit': min(limit, 100)
        }

        if user_id:
            params['uid'] = user_id
        if email:
            params['email'] = email
        if start_time:
            params['start'] = start_time
        if end_time:
            params['end'] = end_time

        result = await self._make_request(
            method='GET',
            endpoint='/sessions/v1',
            params=params
        )

        logger.info(
            "fullstory_sessions_listed",
            count=len(result.get('sessions', [])),
            user_id=user_id
        )

        return result

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get session by ID.

        Args:
            session_id: FullStory session ID

        Returns:
            Session details with events and metadata
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/sessions/v1/{session_id}'
        )

        return result

    async def get_session_url(self, session_id: str) -> str:
        """
        Get session replay URL.

        Args:
            session_id: FullStory session ID

        Returns:
            Session replay URL

        Example:
            >>> url = await fullstory.get_session_url("abc123xyz")
            >>> print(f"Watch session: {url}")
        """
        session = await self.get_session(session_id)
        return session.get('FsUrl', '')

    # ===================================================================
    # EVENTS API
    # ===================================================================

    async def list_events(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        event_name: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List events.

        Args:
            session_id: Filter by session ID
            user_id: Filter by user ID
            event_name: Filter by event name
            start_time: Start time (ISO 8601)
            end_time: End time (ISO 8601)
            limit: Results limit

        Returns:
            List of events

        Example:
            >>> events = await fullstory.list_events(
            ...     event_name="Button Clicked",
            ...     start_time="2024-01-01T00:00:00Z",
            ...     limit=50
            ... )
        """
        params = {
            'limit': min(limit, 1000)
        }

        if session_id:
            params['sessionId'] = session_id
        if user_id:
            params['uid'] = user_id
        if event_name:
            params['name'] = event_name
        if start_time:
            params['start'] = start_time
        if end_time:
            params['end'] = end_time

        result = await self._make_request(
            method='GET',
            endpoint='/events/v1',
            params=params
        )

        logger.info(
            "fullstory_events_listed",
            count=len(result.get('events', [])),
            event_name=event_name
        )

        return result

    async def track_event(
        self,
        user_id: str,
        session_id: str,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track a custom event.

        Args:
            user_id: User ID
            session_id: Session ID
            event_name: Event name
            properties: Event properties

        Returns:
            Event tracking confirmation

        Example:
            >>> await fullstory.track_event(
            ...     user_id="user123",
            ...     session_id="session_abc",
            ...     event_name="Feature Adopted",
            ...     properties={"feature": "advanced_reporting", "plan": "Enterprise"}
            ... )
        """
        data = {
            'uid': user_id,
            'sessionId': session_id,
            'name': event_name
        }

        if properties:
            data['properties'] = properties

        result = await self._make_request(
            method='POST',
            endpoint='/events/v1',
            data=data
        )

        logger.info(
            "fullstory_event_tracked",
            event_name=event_name,
            user_id=user_id
        )

        return result

    # ===================================================================
    # USERS API
    # ===================================================================

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user by ID.

        Args:
            user_id: FullStory user ID

        Returns:
            User details with properties and sessions
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/users/v1/{user_id}'
        )

        return result

    async def update_user(
        self,
        user_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user properties.

        Args:
            user_id: User ID
            properties: User properties to set

        Returns:
            Update confirmation

        Example:
            >>> await fullstory.update_user(
            ...     user_id="user123",
            ...     properties={
            ...         "displayName": "Jane Doe",
            ...         "email": "jane@example.com",
            ...         "plan": "Enterprise",
            ...         "role": "Admin"
            ...     }
            ... )
        """
        data = {
            'uid': user_id,
            'properties': properties
        }

        result = await self._make_request(
            method='POST',
            endpoint='/users/v1',
            data=data
        )

        logger.info(
            "fullstory_user_updated",
            user_id=user_id,
            property_count=len(properties)
        )

        return result

    async def search_users(
        self,
        query: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search users.

        Args:
            query: Search query (email, displayName, or custom properties)
            limit: Results limit

        Returns:
            Matching users
        """
        params = {
            'query': query,
            'limit': min(limit, 100)
        }

        return await self._make_request(
            method='GET',
            endpoint='/users/v1/search',
            params=params
        )

    # ===================================================================
    # SEGMENTS API
    # ===================================================================

    async def list_segments(self) -> Dict[str, Any]:
        """
        List all segments.

        Returns:
            List of segments
        """
        return await self._make_request(
            method='GET',
            endpoint='/segments/v1'
        )

    async def get_segment(self, segment_id: str) -> Dict[str, Any]:
        """
        Get segment by ID.

        Args:
            segment_id: Segment ID

        Returns:
            Segment details with rules and user count
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/segments/v1/{segment_id}'
        )

        return result

    async def create_segment(
        self,
        name: str,
        rules: List[Dict[str, Any]],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a segment.

        Args:
            name: Segment name
            rules: Segment rules/filters
            description: Segment description

        Returns:
            Created segment data

        Example:
            >>> segment = await fullstory.create_segment(
            ...     name="High Value Users",
            ...     rules=[
            ...         {"property": "plan", "operator": "equals", "value": "Enterprise"},
            ...         {"property": "sessions", "operator": "greater_than", "value": 10}
            ...     ],
            ...     description="Enterprise users with 10+ sessions"
            ... )
        """
        data = {
            'name': name,
            'rules': rules
        }

        if description:
            data['description'] = description

        result = await self._make_request(
            method='POST',
            endpoint='/segments/v1',
            data=data
        )

        logger.info(
            "fullstory_segment_created",
            segment_id=result.get('id'),
            name=name
        )

        return result

    async def get_segment_users(
        self,
        segment_id: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get users in a segment.

        Args:
            segment_id: Segment ID
            limit: Results limit

        Returns:
            List of users in segment
        """
        params = {
            'limit': min(limit, 1000)
        }

        return await self._make_request(
            method='GET',
            endpoint=f'/segments/v1/{segment_id}/users',
            params=params
        )

    # ===================================================================
    # FUNNELS API
    # ===================================================================

    async def list_funnels(self) -> Dict[str, Any]:
        """
        List all funnels.

        Returns:
            List of funnels
        """
        return await self._make_request(
            method='GET',
            endpoint='/funnels/v1'
        )

    async def get_funnel(self, funnel_id: str) -> Dict[str, Any]:
        """
        Get funnel by ID.

        Args:
            funnel_id: Funnel ID

        Returns:
            Funnel details with steps and conversion rates
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/funnels/v1/{funnel_id}'
        )

        return result

    async def create_funnel(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a funnel.

        Args:
            name: Funnel name
            steps: Funnel steps with event definitions
            description: Funnel description

        Returns:
            Created funnel data

        Example:
            >>> funnel = await fullstory.create_funnel(
            ...     name="Signup Funnel",
            ...     steps=[
            ...         {"name": "Visit Homepage", "event": "pageview", "url": "/"},
            ...         {"name": "Click Signup", "event": "click", "selector": "#signup-btn"},
            ...         {"name": "Complete Form", "event": "submit", "form": "signup-form"}
            ...     ],
            ...     description="Track user signup conversion"
            ... )
        """
        data = {
            'name': name,
            'steps': steps
        }

        if description:
            data['description'] = description

        result = await self._make_request(
            method='POST',
            endpoint='/funnels/v1',
            data=data
        )

        logger.info(
            "fullstory_funnel_created",
            funnel_id=result.get('id'),
            name=name
        )

        return result

    async def get_funnel_data(
        self,
        funnel_id: str,
        start_time: str,
        end_time: str,
        segment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get funnel conversion data.

        Args:
            funnel_id: Funnel ID
            start_time: Start time (ISO 8601)
            end_time: End time (ISO 8601)
            segment_id: Filter by segment ID

        Returns:
            Funnel data with conversion rates by step

        Example:
            >>> data = await fullstory.get_funnel_data(
            ...     funnel_id="funnel_123",
            ...     start_time="2024-01-01T00:00:00Z",
            ...     end_time="2024-12-31T23:59:59Z"
            ... )
        """
        params = {
            'start': start_time,
            'end': end_time
        }

        if segment_id:
            params['segmentId'] = segment_id

        return await self._make_request(
            method='GET',
            endpoint=f'/funnels/v1/{funnel_id}/data',
            params=params
        )

    # ===================================================================
    # SEARCH API
    # ===================================================================

    async def search_sessions(
        self,
        query: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search sessions using FullStory query language.

        Args:
            query: Search query (FullStory query syntax)
            start_time: Start time (ISO 8601)
            end_time: End time (ISO 8601)
            limit: Results limit

        Returns:
            Matching sessions

        Example:
            >>> sessions = await fullstory.search_sessions(
            ...     query='user.plan:"Enterprise" AND clicked("signup-button")',
            ...     start_time="2024-01-01T00:00:00Z",
            ...     limit=25
            ... )
        """
        params = {
            'query': query,
            'limit': min(limit, 100)
        }

        if start_time:
            params['start'] = start_time
        if end_time:
            params['end'] = end_time

        result = await self._make_request(
            method='GET',
            endpoint='/sessions/v1/search',
            params=params
        )

        logger.info(
            "fullstory_sessions_searched",
            count=len(result.get('sessions', [])),
            query=query
        )

        return result

    async def search_events(
        self,
        query: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Search events using FullStory query language.

        Args:
            query: Search query (FullStory query syntax)
            start_time: Start time (ISO 8601)
            end_time: End time (ISO 8601)
            limit: Results limit

        Returns:
            Matching events
        """
        params = {
            'query': query,
            'limit': min(limit, 1000)
        }

        if start_time:
            params['start'] = start_time
        if end_time:
            params['end'] = end_time

        result = await self._make_request(
            method='GET',
            endpoint='/events/v1/search',
            params=params
        )

        logger.info(
            "fullstory_events_searched",
            count=len(result.get('events', [])),
            query=query
        )

        return result

    # ===================================================================
    # EXPORTS API
    # ===================================================================

    async def create_export(
        self,
        start_time: str,
        end_time: str,
        segment_id: Optional[str] = None,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Create a data export.

        Args:
            start_time: Start time (ISO 8601)
            end_time: End time (ISO 8601)
            segment_id: Filter by segment ID
            format: Export format (json, csv)

        Returns:
            Export job data with job ID

        Example:
            >>> export = await fullstory.create_export(
            ...     start_time="2024-01-01T00:00:00Z",
            ...     end_time="2024-01-31T23:59:59Z",
            ...     format="csv"
            ... )
            >>> job_id = export['id']
        """
        data = {
            'start': start_time,
            'end': end_time,
            'format': format
        }

        if segment_id:
            data['segmentId'] = segment_id

        result = await self._make_request(
            method='POST',
            endpoint='/exports/v1',
            data=data
        )

        logger.info(
            "fullstory_export_created",
            export_id=result.get('id'),
            start_time=start_time,
            end_time=end_time
        )

        return result

    async def get_export_status(self, export_id: str) -> Dict[str, Any]:
        """
        Get export job status.

        Args:
            export_id: Export job ID

        Returns:
            Export status and download URL if complete
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/exports/v1/{export_id}'
        )

        return result

    async def close(self) -> Any:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("fullstory_session_closed")
