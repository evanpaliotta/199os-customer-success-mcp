"""
Appcues Integration
Priority Score: 10
ICP Adoption: 30-40% of product-led growth companies

User onboarding and product adoption platform providing:
- Flows (Onboarding Guides)
- Users and Accounts
- Events Tracking
- Flow Analytics
- Segments
- A/B Testing
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


class AppcuesIntegration(BaseIntegration):
    """
    Appcues API integration with API key authentication.

    Authentication:
    - API Key in Authorization header (Bearer token)
    - Account ID required for most operations

    Rate Limits:
    - 1000 requests per hour per account
    - Burst: 20 requests per second

    Documentation: https://docs.appcues.com/api
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 360
    ) -> Any:
        """
        Initialize Appcues integration.

        Args:
            credentials: Appcues credentials
                - api_key: Appcues API key
                - account_id: Appcues account ID
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 360 = 6 min)
        """
        super().__init__(
            integration_name="appcues",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        self.account_id = credentials.get('account_id', '')

        if not self.api_key:
            raise ValidationError("Appcues api_key is required")
        if not self.account_id:
            raise ValidationError("Appcues account_id is required")

        self.base_url = "https://api.appcues.com/v1"

        logger.info(
            "appcues_initialized",
            account_id=self.account_id,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Appcues (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("appcues_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Appcues authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Appcues API."""
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
                        f"Appcues API error ({response.status}): {error_text}",
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
        """Test connection to Appcues API."""
        try:
            start_time = datetime.now()

            # Test with flows list
            response = await self._make_request(
                method='GET',
                endpoint=f'/accounts/{self.account_id}/flows'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Appcues",
                response_time_ms=duration_ms,
                metadata={
                    'account_id': self.account_id,
                    'flow_count': len(response.get('flows', [])),
                    'integration_name': 'appcues'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Appcues connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # FLOWS API (ONBOARDING GUIDES)
    # ===================================================================

    async def list_flows(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List flows (onboarding guides, tooltips, modals).

        Args:
            status: Filter by status (draft, published, archived)
            limit: Results limit (max: 100)
            offset: Pagination offset

        Returns:
            List of flows

        Example:
            >>> flows = await appcues.list_flows(
            ...     status="published",
            ...     limit=25
            ... )
        """
        params = {
            'limit': min(limit, 100),
            'offset': offset
        }

        if status:
            params['status'] = status

        result = await self._make_request(
            method='GET',
            endpoint=f'/accounts/{self.account_id}/flows',
            params=params
        )

        logger.info(
            "appcues_flows_listed",
            count=len(result.get('flows', [])),
            status=status
        )

        return result

    async def get_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Get flow by ID.

        Args:
            flow_id: Flow ID

        Returns:
            Flow details with steps, targeting, and settings
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/accounts/{self.account_id}/flows/{flow_id}'
        )

        return result

    async def create_flow(
        self,
        name: str,
        flow_type: str,
        steps: List[Dict[str, Any]],
        targeting: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a flow.

        Args:
            name: Flow name
            flow_type: Flow type (modal, slideout, hotspot, tooltip, banner)
            steps: Flow steps configuration
            targeting: Targeting rules (segments, pages, etc.)
            settings: Flow settings (frequency, timing, etc.)

        Returns:
            Created flow data

        Example:
            >>> flow = await appcues.create_flow(
            ...     name="Welcome Tour",
            ...     flow_type="modal",
            ...     steps=[
            ...         {"type": "intro", "title": "Welcome!", "body": "Let's get started."},
            ...         {"type": "feature", "title": "Key Feature", "body": "Here's what you can do."}
            ...     ],
            ...     targeting={"segment": "new_users", "url": "/dashboard"},
            ...     settings={"frequency": "once", "trigger": "page_load"}
            ... )
        """
        data = {
            'name': name,
            'type': flow_type,
            'steps': steps
        }

        if targeting:
            data['targeting'] = targeting
        if settings:
            data['settings'] = settings

        result = await self._make_request(
            method='POST',
            endpoint=f'/accounts/{self.account_id}/flows',
            data=data
        )

        logger.info(
            "appcues_flow_created",
            flow_id=result.get('id'),
            name=name,
            flow_type=flow_type
        )

        return result

    async def update_flow(
        self,
        flow_id: str,
        name: Optional[str] = None,
        status: Optional[str] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
        targeting: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update a flow.

        Args:
            flow_id: Flow ID
            name: New flow name
            status: New status (draft, published, archived)
            steps: Updated steps
            targeting: Updated targeting rules

        Returns:
            Updated flow data
        """
        data = {}

        if name:
            data['name'] = name
        if status:
            data['status'] = status
        if steps:
            data['steps'] = steps
        if targeting:
            data['targeting'] = targeting

        result = await self._make_request(
            method='PUT',
            endpoint=f'/accounts/{self.account_id}/flows/{flow_id}',
            data=data
        )

        logger.info(
            "appcues_flow_updated",
            flow_id=flow_id,
            status=status
        )

        return result

    async def delete_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Delete a flow.

        Args:
            flow_id: Flow ID

        Returns:
            Deletion confirmation
        """
        await self._make_request(
            method='DELETE',
            endpoint=f'/accounts/{self.account_id}/flows/{flow_id}'
        )

        logger.info("appcues_flow_deleted", flow_id=flow_id)
        return {'status': 'deleted', 'flow_id': flow_id}

    # ===================================================================
    # FLOW ANALYTICS API
    # ===================================================================

    async def get_flow_analytics(
        self,
        flow_id: str,
        start_date: str,
        end_date: str,
        breakdown: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a flow.

        Args:
            flow_id: Flow ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            breakdown: Breakdown dimension (day, week, month)

        Returns:
            Flow analytics with views, completions, drop-offs

        Example:
            >>> analytics = await appcues.get_flow_analytics(
            ...     flow_id="flow_123",
            ...     start_date="2024-01-01",
            ...     end_date="2024-12-31",
            ...     breakdown="day"
            ... )
        """
        params = {
            'start_date': start_date,
            'end_date': end_date
        }

        if breakdown:
            params['breakdown'] = breakdown

        result = await self._make_request(
            method='GET',
            endpoint=f'/accounts/{self.account_id}/flows/{flow_id}/analytics',
            params=params
        )

        return result

    async def get_flow_completions(
        self,
        flow_id: str,
        start_date: str,
        end_date: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get flow completion events.

        Args:
            flow_id: Flow ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of completion events with user info
        """
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'limit': min(limit, 1000),
            'offset': offset
        }

        return await self._make_request(
            method='GET',
            endpoint=f'/accounts/{self.account_id}/flows/{flow_id}/completions',
            params=params
        )

    # ===================================================================
    # USERS API
    # ===================================================================

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User details with properties and flow history
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/accounts/{self.account_id}/users/{user_id}'
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
            >>> await appcues.update_user(
            ...     user_id="user123",
            ...     properties={
            ...         "name": "Jane Doe",
            ...         "email": "jane@example.com",
            ...         "plan": "Enterprise",
            ...         "role": "Admin",
            ...         "signup_date": "2024-01-15"
            ...     }
            ... )
        """
        data = {
            'user_id': user_id,
            'properties': properties
        }

        result = await self._make_request(
            method='POST',
            endpoint=f'/accounts/{self.account_id}/users',
            data=data
        )

        logger.info(
            "appcues_user_updated",
            user_id=user_id,
            property_count=len(properties)
        )

        return result

    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """
        Delete a user.

        Args:
            user_id: User ID

        Returns:
            Deletion confirmation
        """
        await self._make_request(
            method='DELETE',
            endpoint=f'/accounts/{self.account_id}/users/{user_id}'
        )

        logger.info("appcues_user_deleted", user_id=user_id)
        return {'status': 'deleted', 'user_id': user_id}

    async def get_user_activity(
        self,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get user activity history.

        Args:
            user_id: User ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Results limit

        Returns:
            User activity with flow interactions and events
        """
        params = {
            'limit': min(limit, 1000)
        }

        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint=f'/accounts/{self.account_id}/users/{user_id}/activity',
            params=params
        )

    # ===================================================================
    # ACCOUNTS (GROUPS) API
    # ===================================================================

    async def get_account(self, account_group_id: str) -> Dict[str, Any]:
        """
        Get account group by ID.

        Args:
            account_group_id: Account group ID (not the Appcues account ID)

        Returns:
            Account group details with properties
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/accounts/{self.account_id}/groups/{account_group_id}'
        )

        return result

    async def update_account(
        self,
        account_group_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update account group properties.

        Args:
            account_group_id: Account group ID
            properties: Account properties to set

        Returns:
            Update confirmation

        Example:
            >>> await appcues.update_account(
            ...     account_group_id="acme_corp",
            ...     properties={
            ...         "name": "Acme Corporation",
            ...         "plan": "Enterprise",
            ...         "arr": 50000,
            ...         "industry": "Technology"
            ...     }
            ... )
        """
        data = {
            'group_id': account_group_id,
            'properties': properties
        }

        result = await self._make_request(
            method='POST',
            endpoint=f'/accounts/{self.account_id}/groups',
            data=data
        )

        logger.info(
            "appcues_account_updated",
            account_group_id=account_group_id,
            property_count=len(properties)
        )

        return result

    async def assign_user_to_account(
        self,
        user_id: str,
        account_group_id: str
    ) -> Dict[str, Any]:
        """
        Assign user to account group.

        Args:
            user_id: User ID
            account_group_id: Account group ID

        Returns:
            Assignment confirmation
        """
        data = {
            'user_id': user_id,
            'group_id': account_group_id
        }

        result = await self._make_request(
            method='POST',
            endpoint=f'/accounts/{self.account_id}/group_memberships',
            data=data
        )

        logger.info(
            "appcues_user_assigned_to_account",
            user_id=user_id,
            account_group_id=account_group_id
        )

        return result

    # ===================================================================
    # EVENTS API
    # ===================================================================

    async def track_event(
        self,
        user_id: str,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track a custom event.

        Args:
            user_id: User ID
            event_name: Event name
            properties: Event properties

        Returns:
            Event tracking confirmation

        Example:
            >>> await appcues.track_event(
            ...     user_id="user123",
            ...     event_name="Feature Adopted",
            ...     properties={
            ...         "feature": "advanced_reporting",
            ...         "plan": "Enterprise"
            ...     }
            ... )
        """
        data = {
            'user_id': user_id,
            'event_name': event_name
        }

        if properties:
            data['properties'] = properties

        result = await self._make_request(
            method='POST',
            endpoint=f'/accounts/{self.account_id}/events',
            data=data
        )

        logger.info(
            "appcues_event_tracked",
            event_name=event_name,
            user_id=user_id
        )

        return result

    async def list_events(
        self,
        user_id: Optional[str] = None,
        event_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List events.

        Args:
            user_id: Filter by user ID
            event_name: Filter by event name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of events
        """
        params = {
            'limit': min(limit, 1000),
            'offset': offset
        }

        if user_id:
            params['user_id'] = user_id
        if event_name:
            params['event_name'] = event_name
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint=f'/accounts/{self.account_id}/events',
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
            endpoint=f'/accounts/{self.account_id}/segments'
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
            endpoint=f'/accounts/{self.account_id}/segments/{segment_id}'
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
            >>> segment = await appcues.create_segment(
            ...     name="Enterprise Users",
            ...     rules=[
            ...         {"property": "plan", "operator": "equals", "value": "Enterprise"},
            ...         {"property": "role", "operator": "equals", "value": "Admin"}
            ...     ],
            ...     description="Enterprise plan administrators"
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
            endpoint=f'/accounts/{self.account_id}/segments',
            data=data
        )

        logger.info(
            "appcues_segment_created",
            segment_id=result.get('id'),
            name=name
        )

        return result

    async def get_segment_users(
        self,
        segment_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get users in a segment.

        Args:
            segment_id: Segment ID
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of users in segment
        """
        params = {
            'limit': min(limit, 1000),
            'offset': offset
        }

        return await self._make_request(
            method='GET',
            endpoint=f'/accounts/{self.account_id}/segments/{segment_id}/users',
            params=params
        )

    # ===================================================================
    # ANALYTICS API
    # ===================================================================

    async def get_overview_analytics(
        self,
        start_date: str,
        end_date: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get overview analytics.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            metrics: List of metrics to include (flows_started, flows_completed, etc.)

        Returns:
            Overview analytics data

        Example:
            >>> analytics = await appcues.get_overview_analytics(
            ...     start_date="2024-01-01",
            ...     end_date="2024-12-31",
            ...     metrics=["flows_started", "flows_completed", "unique_users"]
            ... )
        """
        params = {
            'start_date': start_date,
            'end_date': end_date
        }

        if metrics:
            params['metrics'] = ','.join(metrics)

        return await self._make_request(
            method='GET',
            endpoint=f'/accounts/{self.account_id}/analytics/overview',
            params=params
        )

    async def close(self) -> Any:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("appcues_session_closed")
