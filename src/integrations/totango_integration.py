"""
Totango Integration
Priority Score: 10
ICP Adoption: 30-40% of B2B SaaS companies

Customer success and product analytics platform providing:
- Accounts and Users
- Health and Engagement Scores
- Touchpoints (Activities)
- Campaigns
- Segments
- Success Plans
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


class TotangoIntegration(BaseIntegration):
    """
    Totango API integration with API token authentication.

    Authentication:
    - API Token in header (app-token)
    - Service ID for authentication

    Rate Limits:
    - 100 requests per minute
    - 10000 requests per day

    Documentation: https://support.totango.com/hc/en-us/articles/360042750592
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 90,
        rate_limit_window: int = 60
    ) -> Any:
        """
        Initialize Totango integration.

        Args:
            credentials: Totango credentials
                - api_token: Totango API token
                - service_id: Totango service ID
            rate_limit_calls: Max API calls per window (default: 90)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="totango",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_token = credentials.get('api_token', '')
        self.service_id = credentials.get('service_id', '')

        if not self.api_token:
            raise ValidationError("Totango api_token is required")
        if not self.service_id:
            raise ValidationError("Totango service_id is required")

        self.base_url = "https://api.totango.com/api/v1"

        logger.info(
            "totango_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Totango (API token validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("totango_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Totango authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make authenticated HTTP request to Totango API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            'app-token': self.api_token,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
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
                        f"Totango API error ({response.status}): {error_text}",
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
        """Test connection to Totango API."""
        try:
            start_time = datetime.now()

            # Test with search accounts request
            response = await self._make_request(
                method='POST',
                endpoint='/search/accounts',
                data={
                    'terms': [],
                    'count': 1,
                    'offset': 0
                }
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Totango",
                response_time_ms=duration_ms,
                metadata={
                    'integration_name': 'totango',
                    'service_id': self.service_id
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Totango connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # ACCOUNTS API
    # ===================================================================

    async def search_accounts(
        self,
        terms: Optional[List[Dict[str, Any]]] = None,
        count: int = 100,
        offset: int = 0,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search accounts with filters.

        Args:
            terms: Search terms and filters
            count: Max results (max: 1000)
            offset: Pagination offset
            fields: Fields to return

        Returns:
            Search results with accounts

        Example:
            >>> # Search for healthy accounts
            >>> accounts = await totango.search_accounts(
            ...     terms=[{
            ...         "type": "number",
            ...         "term": "health_score",
            ...         "gte": 70
            ...     }],
            ...     count=50
            ... )
        """
        data = {
            'terms': terms or [],
            'count': min(count, 1000),
            'offset': offset
        }

        if fields:
            data['fields'] = fields

        result = await self._make_request(
            method='POST',
            endpoint='/search/accounts',
            data=data
        )

        logger.info(
            "totango_accounts_searched",
            count=result.get('total_results', 0)
        )

        return result

    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """
        Get account by ID.

        Args:
            account_id: Account ID

        Returns:
            Account details with health, engagement, and metadata

        Example:
            >>> account = await totango.get_account("acc_123")
            >>> print(f"Health: {account['health']}")
            >>> print(f"Last activity: {account['last_activity_time']}")
        """
        result = await self.search_accounts(
            terms=[{
                'type': 'string',
                'term': 'account_id',
                'eq': account_id
            }],
            count=1
        )

        accounts = result.get('accounts', [])
        if not accounts:
            raise APIError(f"Account {account_id} not found", 404)

        return accounts[0]

    async def create_account(
        self,
        account_id: str,
        name: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or update an account.

        Args:
            account_id: Unique account identifier
            name: Account name
            attributes: Account attributes (mrr, plan, industry, etc.)

        Returns:
            Created/updated account

        Example:
            >>> account = await totango.create_account(
            ...     account_id="acme_corp",
            ...     name="Acme Corporation",
            ...     attributes={
            ...         "mrr": 999,
            ...         "plan": "Enterprise",
            ...         "industry": "Technology"
            ...     }
            ... )
        """
        data = {
            'service_id': self.service_id,
            'account_id': account_id,
            'account_name': name
        }

        if attributes:
            for key, value in attributes.items():
                data[key] = value

        result = await self._make_request(
            method='POST',
            endpoint='/accounts',
            data=data
        )

        logger.info(
            "totango_account_created",
            account_id=account_id,
            name=name
        )

        return result

    async def update_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update account attributes.

        Args:
            account_id: Account ID
            attributes: Attributes to update

        Returns:
            Update confirmation

        Example:
            >>> await totango.update_account(
            ...     account_id="acme_corp",
            ...     attributes={"mrr": 1299, "plan": "Enterprise Plus"}
            ... )
        """
        data = {
            'service_id': self.service_id,
            'account_id': account_id
        }
        data.update(attributes)

        result = await self._make_request(
            method='POST',
            endpoint='/accounts',
            data=data
        )

        logger.info(
            "totango_account_updated",
            account_id=account_id
        )

        return result

    # ===================================================================
    # USERS API
    # ===================================================================

    async def search_users(
        self,
        account_id: Optional[str] = None,
        terms: Optional[List[Dict[str, Any]]] = None,
        count: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Search users with filters.

        Args:
            account_id: Filter by account ID
            terms: Search terms and filters
            count: Max results
            offset: Pagination offset

        Returns:
            Search results with users
        """
        search_terms = terms or []

        if account_id:
            search_terms.append({
                'type': 'string',
                'term': 'account_id',
                'eq': account_id
            })

        data = {
            'terms': search_terms,
            'count': count,
            'offset': offset
        }

        result = await self._make_request(
            method='POST',
            endpoint='/search/users',
            data=data
        )

        logger.info(
            "totango_users_searched",
            count=result.get('total_results', 0),
            account_id=account_id
        )

        return result

    async def create_user(
        self,
        account_id: str,
        user_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or update a user.

        Args:
            account_id: Account ID
            user_id: Unique user identifier
            email: User email
            name: User name
            attributes: User attributes

        Returns:
            Created/updated user

        Example:
            >>> user = await totango.create_user(
            ...     account_id="acme_corp",
            ...     user_id="jane_doe",
            ...     email="jane@acme.com",
            ...     name="Jane Doe",
            ...     attributes={"role": "admin", "department": "Operations"}
            ... )
        """
        data = {
            'service_id': self.service_id,
            'account_id': account_id,
            'user_id': user_id
        }

        if email:
            data['email'] = email
        if name:
            data['user_name'] = name
        if attributes:
            for key, value in attributes.items():
                data[key] = value

        result = await self._make_request(
            method='POST',
            endpoint='/users',
            data=data
        )

        logger.info(
            "totango_user_created",
            account_id=account_id,
            user_id=user_id
        )

        return result

    # ===================================================================
    # HEALTH & ENGAGEMENT API
    # ===================================================================

    async def get_health_score(self, account_id: str) -> Dict[str, Any]:
        """
        Get account health score.

        Args:
            account_id: Account ID

        Returns:
            Health score with components

        Example:
            >>> health = await totango.get_health_score("acme_corp")
            >>> print(f"Score: {health['score']}")
            >>> print(f"Trend: {health['trend']}")
        """
        account = await self.get_account(account_id)

        return {
            'account_id': account_id,
            'score': account.get('health'),
            'color': account.get('health_color'),
            'trend': account.get('health_trend'),
            'last_updated': account.get('health_last_modified')
        }

    async def update_health_score(
        self,
        account_id: str,
        score: int,
        components: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update account health score.

        Args:
            account_id: Account ID
            score: Health score (0-100)
            components: Health score components

        Returns:
            Update confirmation

        Example:
            >>> await totango.update_health_score(
            ...     account_id="acme_corp",
            ...     score=85,
            ...     components={
            ...         "product_usage": 90,
            ...         "support_satisfaction": 80
            ...     }
            ... )
        """
        attributes = {'health': score}

        if components:
            attributes.update(components)

        return await self.update_account(
            account_id=account_id,
            attributes=attributes
        )

    async def get_engagement_score(self, account_id: str) -> Dict[str, Any]:
        """
        Get account engagement score.

        Args:
            account_id: Account ID

        Returns:
            Engagement score and metrics
        """
        account = await self.get_account(account_id)

        return {
            'account_id': account_id,
            'score': account.get('engagement'),
            'last_activity': account.get('last_activity_time'),
            'active_users': account.get('active_users')
        }

    # ===================================================================
    # TOUCHPOINTS (ACTIVITIES) API
    # ===================================================================

    async def track_activity(
        self,
        account_id: str,
        user_id: Optional[str],
        activity_type: str,
        module: str,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track user activity/event.

        Args:
            account_id: Account ID
            user_id: User ID (optional for account-level events)
            activity_type: Activity type (e.g., "login", "feature_used", "report_generated")
            module: Module/feature name
            timestamp: Activity timestamp (ISO format, defaults to now)
            metadata: Additional activity metadata

        Returns:
            Track confirmation

        Example:
            >>> await totango.track_activity(
            ...     account_id="acme_corp",
            ...     user_id="jane_doe",
            ...     activity_type="feature_used",
            ...     module="dashboard",
            ...     metadata={"feature": "advanced_analytics"}
            ... )
        """
        data = {
            'service_id': self.service_id,
            'account_id': account_id,
            'activity': activity_type,
            'module': module
        }

        if user_id:
            data['user_id'] = user_id

        if timestamp:
            data['timestamp'] = timestamp

        if metadata:
            for key, value in metadata.items():
                data[key] = value

        result = await self._make_request(
            method='POST',
            endpoint='/activities',
            data=data
        )

        logger.info(
            "totango_activity_tracked",
            account_id=account_id,
            user_id=user_id,
            activity_type=activity_type
        )

        return result

    async def create_touchpoint(
        self,
        account_id: str,
        touchpoint_type: str,
        title: str,
        description: Optional[str] = None,
        date: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a touchpoint (customer interaction record).

        Args:
            account_id: Account ID
            touchpoint_type: Type (call, email, meeting, note, etc.)
            title: Touchpoint title
            description: Touchpoint description
            date: Touchpoint date (ISO format)
            created_by: Created by user ID

        Returns:
            Created touchpoint

        Example:
            >>> touchpoint = await totango.create_touchpoint(
            ...     account_id="acme_corp",
            ...     touchpoint_type="meeting",
            ...     title="Quarterly Business Review",
            ...     description="Discussed Q4 performance and 2025 goals",
            ...     date="2024-12-15T14:00:00Z"
            ... )
        """
        data = {
            'account_id': account_id,
            'type': touchpoint_type,
            'title': title,
            'date': date or datetime.utcnow().isoformat()
        }

        if description:
            data['description'] = description
        if created_by:
            data['created_by'] = created_by

        result = await self._make_request(
            method='POST',
            endpoint='/touchpoints',
            data=data
        )

        logger.info(
            "totango_touchpoint_created",
            account_id=account_id,
            type=touchpoint_type
        )

        return result

    # ===================================================================
    # CAMPAIGNS API
    # ===================================================================

    async def list_campaigns(
        self,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List campaigns.

        Args:
            status: Filter by status (active, paused, completed)

        Returns:
            List of campaigns

        Example:
            >>> campaigns = await totango.list_campaigns(status="active")
            >>> for campaign in campaigns:
            ...     print(f"{campaign['name']}: {campaign['account_count']}")
        """
        params = {}
        if status:
            params['status'] = status

        result = await self._make_request(
            method='GET',
            endpoint='/campaigns',
            params=params
        )

        return result if isinstance(result, list) else []

    async def add_account_to_campaign(
        self,
        campaign_id: str,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Add account to a campaign.

        Args:
            campaign_id: Campaign ID
            account_id: Account ID

        Returns:
            Add confirmation

        Example:
            >>> await totango.add_account_to_campaign(
            ...     campaign_id="camp_onboarding",
            ...     account_id="acme_corp"
            ... )
        """
        data = {
            'campaign_id': campaign_id,
            'account_id': account_id
        }

        result = await self._make_request(
            method='POST',
            endpoint='/campaigns/accounts',
            data=data
        )

        logger.info(
            "totango_account_added_to_campaign",
            campaign_id=campaign_id,
            account_id=account_id
        )

        return result

    async def remove_account_from_campaign(
        self,
        campaign_id: str,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Remove account from a campaign.

        Args:
            campaign_id: Campaign ID
            account_id: Account ID

        Returns:
            Remove confirmation
        """
        result = await self._make_request(
            method='DELETE',
            endpoint=f'/campaigns/{campaign_id}/accounts/{account_id}'
        )

        logger.info(
            "totango_account_removed_from_campaign",
            campaign_id=campaign_id,
            account_id=account_id
        )

        return result

    # ===================================================================
    # SEGMENTS API
    # ===================================================================

    async def list_segments(self) -> List[Dict[str, Any]]:
        """
        List account segments.

        Returns:
            List of segments

        Example:
            >>> segments = await totango.list_segments()
            >>> for segment in segments:
            ...     print(f"{segment['name']}: {segment['account_count']}")
        """
        result = await self._make_request(
            method='GET',
            endpoint='/segments'
        )

        return result if isinstance(result, list) else []

    async def get_segment_accounts(
        self,
        segment_id: str,
        count: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get accounts in a segment.

        Args:
            segment_id: Segment ID
            count: Max results
            offset: Pagination offset

        Returns:
            Accounts in segment
        """
        return await self.search_accounts(
            terms=[{
                'type': 'string',
                'term': 'segment_id',
                'eq': segment_id
            }],
            count=count,
            offset=offset
        )

    # ===================================================================
    # TASKS API
    # ===================================================================

    async def create_task(
        self,
        account_id: str,
        title: str,
        description: Optional[str] = None,
        assigned_to: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Create a task.

        Args:
            account_id: Account ID
            title: Task title
            description: Task description
            assigned_to: Assigned user email
            due_date: Due date (ISO format)
            priority: Priority level (low, medium, high)

        Returns:
            Created task

        Example:
            >>> task = await totango.create_task(
            ...     account_id="acme_corp",
            ...     title="Follow up on feature request",
            ...     assigned_to="csm@company.com",
            ...     due_date="2024-12-20T00:00:00Z",
            ...     priority="high"
            ... )
        """
        data = {
            'account_id': account_id,
            'title': title,
            'priority': priority
        }

        if description:
            data['description'] = description
        if assigned_to:
            data['assigned_to'] = assigned_to
        if due_date:
            data['due_date'] = due_date

        result = await self._make_request(
            method='POST',
            endpoint='/tasks',
            data=data
        )

        logger.info(
            "totango_task_created",
            account_id=account_id,
            title=title
        )

        return result

    async def close(self) -> Any:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("totango_session_closed")
