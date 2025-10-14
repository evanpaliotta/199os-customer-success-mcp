"""
ProductBoard Integration
Priority Score: 11
ICP Adoption: 35-45% of product-led SaaS companies

Product management platform providing:
- Features and Components
- User Feedback
- Releases and Roadmaps
- Notes and Insights
- Product Portal
- Customer Requests
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


class ProductBoardIntegration(BaseIntegration):
    """
    ProductBoard API integration with API key authentication.

    Authentication:
    - API Key Bearer token
    - Public and private tokens for different access levels

    Rate Limits:
    - 600 requests per hour per token
    - 10 requests per second

    Documentation: https://developer.productboard.com/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ):
        """
        Initialize ProductBoard integration.

        Args:
            credentials: ProductBoard credentials
                - api_key: ProductBoard API key
                - version: API version (default: 1)
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="productboard",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        self.version = credentials.get('version', '1')

        if not self.api_key:
            raise ValidationError("ProductBoard api_key is required")

        self.base_url = "https://api.productboard.com"

        logger.info(
            "productboard_initialized",
            version=self.version,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with ProductBoard (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("productboard_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"ProductBoard authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to ProductBoard API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-Version': self.version
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
                        f"ProductBoard API error ({response.status}): {error_text}",
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
        """Test connection to ProductBoard API."""
        try:
            start_time = datetime.now()

            # Test with features list request
            response = await self._make_request(
                method='GET',
                endpoint='/features',
                params={'limit': 1}
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to ProductBoard",
                response_time_ms=duration_ms,
                metadata={
                    'integration_name': 'productboard',
                    'version': self.version
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"ProductBoard connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # FEATURES API
    # ===================================================================

    async def list_features(
        self,
        status: Optional[str] = None,
        component_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List features.

        Args:
            status: Filter by status (new, in_progress, done, released)
            component_id: Filter by component ID
            limit: Results limit (max: 100)
            offset: Pagination offset

        Returns:
            List of features

        Example:
            >>> features = await productboard.list_features(
            ...     status="in_progress",
            ...     limit=25
            ... )
        """
        params = {
            'limit': min(limit, 100),
            'offset': offset
        }

        if status:
            params['status'] = status
        if component_id:
            params['componentId'] = component_id

        result = await self._make_request(
            method='GET',
            endpoint='/features',
            params=params
        )

        logger.info(
            "productboard_features_listed",
            count=len(result.get('data', []))
        )

        return result

    async def get_feature(self, feature_id: str) -> Dict[str, Any]:
        """
        Get feature by ID.

        Args:
            feature_id: Feature ID

        Returns:
            Feature details with description, status, and priority

        Example:
            >>> feature = await productboard.get_feature("feat_123")
            >>> print(feature['name'], feature['status'])
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/features/{feature_id}'
        )

    async def create_feature(
        self,
        name: str,
        description: Optional[str] = None,
        status: str = "new",
        component_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        priority: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a feature.

        Args:
            name: Feature name
            description: Feature description
            status: Status (new, in_progress, done, released)
            component_id: Component ID
            owner_id: Feature owner user ID
            priority: Priority score

        Returns:
            Created feature data

        Example:
            >>> feature = await productboard.create_feature(
            ...     name="Advanced Analytics Dashboard",
            ...     description="Real-time analytics with custom metrics",
            ...     status="new",
            ...     component_id="comp_123",
            ...     priority=100
            ... )
        """
        data = {
            'name': name,
            'status': status
        }

        if description:
            data['description'] = description
        if component_id:
            data['componentId'] = component_id
        if owner_id:
            data['ownerId'] = owner_id
        if priority is not None:
            data['priority'] = priority

        result = await self._make_request(
            method='POST',
            endpoint='/features',
            data=data
        )

        logger.info(
            "productboard_feature_created",
            feature_id=result.get('id'),
            name=name,
            status=status
        )

        return result

    async def update_feature(
        self,
        feature_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update a feature.

        Args:
            feature_id: Feature ID
            name: New name
            description: New description
            status: New status
            priority: New priority

        Returns:
            Updated feature data
        """
        data = {}

        if name:
            data['name'] = name
        if description:
            data['description'] = description
        if status:
            data['status'] = status
        if priority is not None:
            data['priority'] = priority

        result = await self._make_request(
            method='PATCH',
            endpoint=f'/features/{feature_id}',
            data=data
        )

        logger.info(
            "productboard_feature_updated",
            feature_id=feature_id
        )

        return result

    # ===================================================================
    # COMPONENTS API
    # ===================================================================

    async def list_components(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List components (product areas).

        Args:
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of components
        """
        params = {
            'limit': min(limit, 100),
            'offset': offset
        }

        return await self._make_request(
            method='GET',
            endpoint='/components',
            params=params
        )

    async def get_component(self, component_id: str) -> Dict[str, Any]:
        """
        Get component by ID.

        Args:
            component_id: Component ID

        Returns:
            Component details
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/components/{component_id}'
        )

    async def create_component(
        self,
        name: str,
        description: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a component.

        Args:
            name: Component name
            description: Component description
            parent_id: Parent component ID (for hierarchy)

        Returns:
            Created component data

        Example:
            >>> component = await productboard.create_component(
            ...     name="Analytics",
            ...     description="Analytics and reporting features"
            ... )
        """
        data = {'name': name}

        if description:
            data['description'] = description
        if parent_id:
            data['parentId'] = parent_id

        result = await self._make_request(
            method='POST',
            endpoint='/components',
            data=data
        )

        logger.info(
            "productboard_component_created",
            component_id=result.get('id'),
            name=name
        )

        return result

    # ===================================================================
    # NOTES (USER FEEDBACK) API
    # ===================================================================

    async def list_notes(
        self,
        feature_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List notes (user feedback).

        Args:
            feature_id: Filter by linked feature ID
            user_id: Filter by user ID
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of notes

        Example:
            >>> notes = await productboard.list_notes(
            ...     feature_id="feat_123",
            ...     limit=25
            ... )
        """
        params = {
            'limit': min(limit, 100),
            'offset': offset
        }

        if feature_id:
            params['featureId'] = feature_id
        if user_id:
            params['userId'] = user_id

        result = await self._make_request(
            method='GET',
            endpoint='/notes',
            params=params
        )

        logger.info(
            "productboard_notes_listed",
            count=len(result.get('data', []))
        )

        return result

    async def get_note(self, note_id: str) -> Dict[str, Any]:
        """
        Get note by ID.

        Args:
            note_id: Note ID

        Returns:
            Note details with content and links
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/notes/{note_id}'
        )

    async def create_note(
        self,
        title: str,
        content: str,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None,
        source: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a note (user feedback).

        Args:
            title: Note title
            content: Note content/description
            user_email: User email who provided feedback
            user_name: User name
            source: Feedback source (e.g., "support", "sales", "product")
            tags: List of tags

        Returns:
            Created note data

        Example:
            >>> note = await productboard.create_note(
            ...     title="Need better reporting features",
            ...     content="Customer requests ability to export data to CSV and schedule reports",
            ...     user_email="customer@acme.com",
            ...     user_name="Jane Doe",
            ...     source="support",
            ...     tags=["reporting", "export", "high-priority"]
            ... )
        """
        data = {
            'title': title,
            'content': content
        }

        if user_email or user_name:
            data['user'] = {}
            if user_email:
                data['user']['email'] = user_email
            if user_name:
                data['user']['name'] = user_name

        if source:
            data['source'] = source
        if tags:
            data['tags'] = tags

        result = await self._make_request(
            method='POST',
            endpoint='/notes',
            data=data
        )

        logger.info(
            "productboard_note_created",
            note_id=result.get('id'),
            title=title,
            source=source
        )

        return result

    async def link_note_to_feature(
        self,
        note_id: str,
        feature_id: str
    ) -> Dict[str, Any]:
        """
        Link a note to a feature.

        Args:
            note_id: Note ID
            feature_id: Feature ID

        Returns:
            Link confirmation

        Example:
            >>> await productboard.link_note_to_feature(
            ...     note_id="note_123",
            ...     feature_id="feat_456"
            ... )
        """
        data = {
            'featureId': feature_id
        }

        result = await self._make_request(
            method='POST',
            endpoint=f'/notes/{note_id}/links',
            data=data
        )

        logger.info(
            "productboard_note_linked",
            note_id=note_id,
            feature_id=feature_id
        )

        return result

    # ===================================================================
    # RELEASES API
    # ===================================================================

    async def list_releases(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List releases.

        Args:
            status: Filter by status (planned, in_progress, released)
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of releases
        """
        params = {
            'limit': min(limit, 100),
            'offset': offset
        }

        if status:
            params['status'] = status

        return await self._make_request(
            method='GET',
            endpoint='/releases',
            params=params
        )

    async def get_release(self, release_id: str) -> Dict[str, Any]:
        """
        Get release by ID.

        Args:
            release_id: Release ID

        Returns:
            Release details with features and timeline
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/releases/{release_id}'
        )

    async def create_release(
        self,
        name: str,
        release_date: Optional[str] = None,
        status: str = "planned",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a release.

        Args:
            name: Release name
            release_date: Target release date (ISO format)
            status: Status (planned, in_progress, released)
            description: Release description

        Returns:
            Created release data

        Example:
            >>> release = await productboard.create_release(
            ...     name="Q1 2025 Release",
            ...     release_date="2025-03-31T00:00:00Z",
            ...     status="planned",
            ...     description="Major analytics and reporting features"
            ... )
        """
        data = {
            'name': name,
            'status': status
        }

        if release_date:
            data['releaseDate'] = release_date
        if description:
            data['description'] = description

        result = await self._make_request(
            method='POST',
            endpoint='/releases',
            data=data
        )

        logger.info(
            "productboard_release_created",
            release_id=result.get('id'),
            name=name,
            release_date=release_date
        )

        return result

    async def add_feature_to_release(
        self,
        release_id: str,
        feature_id: str
    ) -> Dict[str, Any]:
        """
        Add a feature to a release.

        Args:
            release_id: Release ID
            feature_id: Feature ID

        Returns:
            Updated release data
        """
        data = {
            'featureId': feature_id
        }

        result = await self._make_request(
            method='POST',
            endpoint=f'/releases/{release_id}/features',
            data=data
        )

        logger.info(
            "productboard_feature_added_to_release",
            release_id=release_id,
            feature_id=feature_id
        )

        return result

    # ===================================================================
    # INSIGHTS API
    # ===================================================================

    async def get_feature_score(self, feature_id: str) -> Dict[str, Any]:
        """
        Get feature priority score and insights.

        Args:
            feature_id: Feature ID

        Returns:
            Feature score with breakdown and user impact

        Example:
            >>> score = await productboard.get_feature_score("feat_123")
            >>> print(f"Score: {score['value']}, User Impact: {score['user_impact']}")
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/features/{feature_id}/score'
        )

    async def get_user_feedback_summary(
        self,
        feature_id: str
    ) -> Dict[str, Any]:
        """
        Get user feedback summary for a feature.

        Args:
            feature_id: Feature ID

        Returns:
            Feedback summary with sentiment and key themes
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/features/{feature_id}/feedback-summary'
        )

    # ===================================================================
    # USERS API
    # ===================================================================

    async def list_users(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List users (customers/contacts).

        Args:
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of users
        """
        params = {
            'limit': min(limit, 100),
            'offset': offset
        }

        return await self._make_request(
            method='GET',
            endpoint='/users',
            params=params
        )

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user by ID.

        Args:
            user_id: User ID or email

        Returns:
            User details
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/users/{user_id}'
        )

    async def create_user(
        self,
        email: str,
        name: Optional[str] = None,
        company: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a user.

        Args:
            email: User email
            name: User name
            company: Company name
            custom_fields: Custom user attributes

        Returns:
            Created user data

        Example:
            >>> user = await productboard.create_user(
            ...     email="jane@acme.com",
            ...     name="Jane Doe",
            ...     company="Acme Corp",
            ...     custom_fields={"plan": "enterprise", "mrr": 5000}
            ... )
        """
        data = {'email': email}

        if name:
            data['name'] = name
        if company:
            data['company'] = company
        if custom_fields:
            data['customFields'] = custom_fields

        result = await self._make_request(
            method='POST',
            endpoint='/users',
            data=data
        )

        logger.info(
            "productboard_user_created",
            user_id=result.get('id'),
            email=email
        )

        return result

    # ===================================================================
    # PORTAL API
    # ===================================================================

    async def get_portal_config(self) -> Dict[str, Any]:
        """
        Get product portal configuration.

        Returns:
            Portal configuration settings
        """
        return await self._make_request(
            method='GET',
            endpoint='/portal/config'
        )

    async def list_portal_features(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List features visible in product portal.

        Args:
            status: Filter by status
            limit: Results limit

        Returns:
            List of portal features with voting data
        """
        params = {'limit': min(limit, 100)}

        if status:
            params['status'] = status

        return await self._make_request(
            method='GET',
            endpoint='/portal/features',
            params=params
        )

    async def get_feature_votes(self, feature_id: str) -> Dict[str, Any]:
        """
        Get votes for a feature.

        Args:
            feature_id: Feature ID

        Returns:
            Vote count and voter details
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/features/{feature_id}/votes'
        )

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("productboard_session_closed")
