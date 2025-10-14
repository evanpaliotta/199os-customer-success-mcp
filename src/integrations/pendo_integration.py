"""
Pendo Integration
Priority Score: 14
ICP Adoption: 40-50% of product-led growth companies

Product experience platform providing:
- Feature Usage Tracking
- Guide Management (in-app messages, walkthroughs)
- Page Views and Events
- Visitor Metadata
- Account Metadata
- Product Analytics
- Feature Adoption Metrics
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


class PendoIntegration(BaseIntegration):
    """
    Pendo API integration with API key authentication.

    Authentication:
    - Integration Key in X-Pendo-Integration-Key header
    - API Key format: Long hexadecimal string

    Rate Limits:
    - 10,000 requests per hour per subscription
    - Burst: 100 requests per second

    Documentation: https://developers.pendo.io/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ):
        """
        Initialize Pendo integration.

        Args:
            credentials: Pendo credentials
                - integration_key: Pendo integration key (API key)
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="pendo",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.integration_key = credentials.get('integration_key', '')
        if not self.integration_key:
            raise ValidationError("Pendo integration_key is required")

        self.base_url = "https://app.pendo.io/api/v1"

        logger.info(
            "pendo_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Pendo (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("pendo_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Pendo authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Pendo API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            'X-Pendo-Integration-Key': self.integration_key,
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
                        f"Pendo API error ({response.status}): {error_text}",
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
        """Test connection to Pendo API."""
        try:
            start_time = datetime.now()

            # Test with subscription info
            response = await self._make_request(
                method='GET',
                endpoint='/subscription'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Pendo",
                response_time_ms=duration_ms,
                metadata={
                    'subscription_id': response.get('id'),
                    'name': response.get('name'),
                    'integration_name': 'pendo'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Pendo connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # FEATURE USAGE API
    # ===================================================================

    async def get_feature(self, feature_id: str) -> Dict[str, Any]:
        """
        Get feature by ID.

        Args:
            feature_id: Pendo feature ID

        Returns:
            Feature data including metadata and usage
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/feature/{feature_id}'
        )

    async def list_features(
        self,
        page_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List features.

        Args:
            page_id: Filter by page ID
            limit: Results limit

        Returns:
            List of features

        Example:
            >>> features = await pendo.list_features(limit=50)
            >>> for feature in features:
            ...     print(feature['name'], feature['numEvents'])
        """
        params = {'limit': limit}

        if page_id:
            params['pageId'] = page_id

        return await self._make_request(
            method='GET',
            endpoint='/feature',
            params=params
        )

    async def create_feature(
        self,
        name: str,
        page_id: str,
        element_path: str,
        color: Optional[str] = None,
        stable: bool = True
    ) -> Dict[str, Any]:
        """
        Create a feature.

        Args:
            name: Feature name
            page_id: Page ID where feature exists
            element_path: CSS selector path to element
            color: Feature color (hex)
            stable: Whether feature is stable

        Returns:
            Created feature data
        """
        feature_data = {
            'name': name,
            'pageId': page_id,
            'elementPath': element_path,
            'stable': stable
        }

        if color:
            feature_data['color'] = color

        result = await self._make_request(
            method='POST',
            endpoint='/feature',
            data=feature_data
        )

        logger.info(
            "pendo_feature_created",
            feature_id=result.get('id'),
            name=name
        )

        return result

    async def get_feature_usage(
        self,
        feature_id: str,
        start_time: int,
        end_time: int,
        account_id: Optional[str] = None,
        visitor_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get feature usage data.

        Args:
            feature_id: Pendo feature ID
            start_time: Start timestamp (Unix milliseconds)
            end_time: End timestamp (Unix milliseconds)
            account_id: Filter by account ID
            visitor_id: Filter by visitor ID

        Returns:
            Feature usage data with event counts
        """
        params = {
            'featureId': feature_id,
            'first': start_time,
            'last': end_time
        }

        if account_id:
            params['accountId'] = account_id
        if visitor_id:
            params['visitorId'] = visitor_id

        return await self._make_request(
            method='GET',
            endpoint='/aggregation/feature/events',
            params=params
        )

    # ===================================================================
    # GUIDES API (IN-APP MESSAGES)
    # ===================================================================

    async def get_guide(self, guide_id: str) -> Dict[str, Any]:
        """
        Get guide by ID.

        Args:
            guide_id: Pendo guide ID

        Returns:
            Guide data
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/guide/{guide_id}'
        )

    async def list_guides(
        self,
        state: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List guides.

        Args:
            state: Filter by state (draft, published, disabled)
            limit: Results limit

        Returns:
            List of guides
        """
        params = {'limit': limit}

        if state:
            params['state'] = state

        return await self._make_request(
            method='GET',
            endpoint='/guide',
            params=params
        )

    async def create_guide(
        self,
        name: str,
        launch_method: str = "automatic",
        steps: Optional[List[Dict[str, Any]]] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a guide (in-app message/walkthrough).

        Args:
            name: Guide name
            launch_method: Launch method (automatic, badge, api)
            steps: Guide steps configuration
            attributes: Guide attributes (activation rules, etc.)

        Returns:
            Created guide data

        Example:
            >>> guide = await pendo.create_guide(
            ...     name="New Feature Announcement",
            ...     launch_method="automatic",
            ...     steps=[{
            ...         "type": "tooltip",
            ...         "elementPathRule": "#new-feature-button",
            ...         "content": "<h1>Check out our new feature!</h1>"
            ...     }]
            ... )
        """
        guide_data = {
            'name': name,
            'launchMethod': launch_method
        }

        if steps:
            guide_data['steps'] = steps
        if attributes:
            guide_data['attributes'] = attributes

        result = await self._make_request(
            method='POST',
            endpoint='/guide',
            data=guide_data
        )

        logger.info(
            "pendo_guide_created",
            guide_id=result.get('id'),
            name=name
        )

        return result

    async def update_guide(
        self,
        guide_id: str,
        name: Optional[str] = None,
        state: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update guide.

        Args:
            guide_id: Pendo guide ID
            name: Guide name
            state: Guide state (draft, published, disabled)
            attributes: Guide attributes

        Returns:
            Updated guide data
        """
        update_data = {}

        if name:
            update_data['name'] = name
        if state:
            update_data['state'] = state
        if attributes:
            update_data['attributes'] = attributes

        result = await self._make_request(
            method='PUT',
            endpoint=f'/guide/{guide_id}',
            data=update_data
        )

        logger.info(
            "pendo_guide_updated",
            guide_id=guide_id,
            state=state
        )

        return result

    async def get_guide_analytics(
        self,
        guide_id: str,
        start_time: int,
        end_time: int
    ) -> Dict[str, Any]:
        """
        Get guide analytics.

        Args:
            guide_id: Pendo guide ID
            start_time: Start timestamp (Unix milliseconds)
            end_time: End timestamp (Unix milliseconds)

        Returns:
            Guide analytics data with views, dismissals, etc.
        """
        params = {
            'guideId': guide_id,
            'first': start_time,
            'last': end_time
        }

        return await self._make_request(
            method='GET',
            endpoint='/aggregation/guide',
            params=params
        )

    # ===================================================================
    # PAGES API
    # ===================================================================

    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Get page by ID.

        Args:
            page_id: Pendo page ID

        Returns:
            Page data
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/page/{page_id}'
        )

    async def list_pages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List pages.

        Args:
            limit: Results limit

        Returns:
            List of pages
        """
        params = {'limit': limit}

        return await self._make_request(
            method='GET',
            endpoint='/page',
            params=params
        )

    async def get_page_views(
        self,
        page_id: str,
        start_time: int,
        end_time: int,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get page view data.

        Args:
            page_id: Pendo page ID
            start_time: Start timestamp (Unix milliseconds)
            end_time: End timestamp (Unix milliseconds)
            account_id: Filter by account ID

        Returns:
            Page view data
        """
        params = {
            'pageId': page_id,
            'first': start_time,
            'last': end_time
        }

        if account_id:
            params['accountId'] = account_id

        return await self._make_request(
            method='GET',
            endpoint='/aggregation/page/events',
            params=params
        )

    # ===================================================================
    # VISITORS API (USER TRACKING)
    # ===================================================================

    async def get_visitor(self, visitor_id: str) -> Dict[str, Any]:
        """
        Get visitor (user) by ID.

        Args:
            visitor_id: Pendo visitor ID

        Returns:
            Visitor data with metadata
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/visitor/{visitor_id}'
        )

    async def update_visitor_metadata(
        self,
        visitor_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update visitor metadata.

        Args:
            visitor_id: Pendo visitor ID
            metadata: Metadata key-value pairs

        Returns:
            Update confirmation

        Example:
            >>> await pendo.update_visitor_metadata(
            ...     visitor_id="user123",
            ...     metadata={
            ...         "role": "admin",
            ...         "department": "Engineering",
            ...         "plan": "Enterprise"
            ...     }
            ... )
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/visitor/{visitor_id}/metadata',
            data={'values': metadata}
        )

        logger.info(
            "pendo_visitor_metadata_updated",
            visitor_id=visitor_id,
            metadata_keys=list(metadata.keys())
        )

        return result

    async def get_visitor_history(
        self,
        visitor_id: str,
        start_time: int,
        end_time: int
    ) -> Dict[str, Any]:
        """
        Get visitor activity history.

        Args:
            visitor_id: Pendo visitor ID
            start_time: Start timestamp (Unix milliseconds)
            end_time: End timestamp (Unix milliseconds)

        Returns:
            Visitor activity data
        """
        params = {
            'visitorId': visitor_id,
            'first': start_time,
            'last': end_time
        }

        return await self._make_request(
            method='GET',
            endpoint='/aggregation/visitor/events',
            params=params
        )

    # ===================================================================
    # ACCOUNTS API
    # ===================================================================

    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """
        Get account by ID.

        Args:
            account_id: Pendo account ID

        Returns:
            Account data with metadata
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/account/{account_id}'
        )

    async def update_account_metadata(
        self,
        account_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update account metadata.

        Args:
            account_id: Pendo account ID
            metadata: Metadata key-value pairs

        Returns:
            Update confirmation

        Example:
            >>> await pendo.update_account_metadata(
            ...     account_id="acme_corp",
            ...     metadata={
            ...         "plan": "Enterprise",
            ...         "arr": 50000,
            ...         "industry": "Technology",
            ...         "health_score": 85
            ...     }
            ... )
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/account/{account_id}/metadata',
            data={'values': metadata}
        )

        logger.info(
            "pendo_account_metadata_updated",
            account_id=account_id,
            metadata_keys=list(metadata.keys())
        )

        return result

    async def get_account_history(
        self,
        account_id: str,
        start_time: int,
        end_time: int
    ) -> Dict[str, Any]:
        """
        Get account activity history.

        Args:
            account_id: Pendo account ID
            start_time: Start timestamp (Unix milliseconds)
            end_time: End timestamp (Unix milliseconds)

        Returns:
            Account activity data
        """
        params = {
            'accountId': account_id,
            'first': start_time,
            'last': end_time
        }

        return await self._make_request(
            method='GET',
            endpoint='/aggregation/account/events',
            params=params
        )

    # ===================================================================
    # EVENTS API
    # ===================================================================

    async def track_event(
        self,
        event_type: str,
        visitor_id: str,
        account_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track custom event.

        Args:
            event_type: Event type/name
            visitor_id: Pendo visitor ID
            account_id: Pendo account ID (optional)
            properties: Event properties

        Returns:
            Track confirmation

        Example:
            >>> await pendo.track_event(
            ...     event_type="feature_adopted",
            ...     visitor_id="user123",
            ...     account_id="acme_corp",
            ...     properties={"feature": "advanced_reporting"}
            ... )
        """
        event_data = {
            'type': event_type,
            'visitorId': visitor_id
        }

        if account_id:
            event_data['accountId'] = account_id
        if properties:
            event_data['properties'] = properties

        result = await self._make_request(
            method='POST',
            endpoint='/event',
            data=event_data
        )

        logger.info(
            "pendo_event_tracked",
            event_type=event_type,
            visitor_id=visitor_id,
            account_id=account_id
        )

        return result

    # ===================================================================
    # AGGREGATION/ANALYTICS API
    # ===================================================================

    async def get_aggregated_data(
        self,
        metric: str,
        start_time: int,
        end_time: int,
        group_by: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated analytics data.

        Args:
            metric: Metric to aggregate (accounts, visitors, events, etc.)
            start_time: Start timestamp (Unix milliseconds)
            end_time: End timestamp (Unix milliseconds)
            group_by: Group by dimension (day, week, month)
            filters: Additional filters

        Returns:
            Aggregated data
        """
        params = {
            'first': start_time,
            'last': end_time
        }

        if group_by:
            params['groupBy'] = group_by
        if filters:
            params.update(filters)

        return await self._make_request(
            method='GET',
            endpoint=f'/aggregation/{metric}',
            params=params
        )

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("pendo_session_closed")
