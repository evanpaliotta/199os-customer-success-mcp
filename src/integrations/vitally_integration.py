"""
Vitally Integration
Priority Score: 17
ICP Adoption: 20-30% of B2B SaaS companies

Modern customer success platform providing:
- Customer Health Scoring
- Product Usage Analytics
- Collaboration & Communication
- Playbooks & Automation
- Account Management
- Customer Timeline
- Notes & Tasks
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


class VitallyIntegration(BaseIntegration):
    """
    Vitally API integration with API key authentication.

    Authentication:
    - API Key in Authorization header (Bearer token)

    Rate Limits:
    - 1000 requests per minute
    - 10,000 requests per hour

    Documentation: https://docs.vitally.io/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ):
        """
        Initialize Vitally integration.

        Args:
            credentials: Vitally credentials
                - api_key: Vitally API key
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="vitally",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        if not self.api_key:
            raise ValidationError("Vitally api_key is required")

        self.base_url = "https://rest.vitally.io/resources"

        logger.info(
            "vitally_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Vitally (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("vitally_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Vitally authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Vitally API."""
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
                        f"Vitally API error ({response.status}): {error_text}",
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
        """Test connection to Vitally API."""
        try:
            start_time = datetime.now()

            # Test with accounts query
            response = await self._make_request(
                method='GET',
                endpoint='/accounts',
                params={'limit': 1}
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Vitally",
                response_time_ms=duration_ms,
                metadata={'integration_name': 'vitally'}
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Vitally connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # ACCOUNTS API
    # ===================================================================

    async def create_account(
        self,
        account_id: str,
        name: str,
        traits: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or update an account.

        Args:
            account_id: External account ID
            name: Account name
            traits: Account traits/properties

        Returns:
            Created/updated account data

        Example:
            >>> account = await vitally.create_account(
            ...     account_id="acme_corp",
            ...     name="Acme Corporation",
            ...     traits={
            ...         "arr": 50000,
            ...         "plan": "Enterprise",
            ...         "industry": "Technology"
            ...     }
            ... )
        """
        data = {
            'accountId': account_id,
            'name': name
        }

        if traits:
            data['traits'] = traits

        result = await self._make_request(
            method='POST',
            endpoint='/accounts',
            data=data
        )

        logger.info(
            "vitally_account_created",
            account_id=account_id,
            name=name
        )

        return result

    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """
        Get account details.

        Args:
            account_id: External account ID

        Returns:
            Account data
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/accounts/{account_id}'
        )

    async def update_account(
        self,
        account_id: str,
        traits: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update account traits.

        Args:
            account_id: External account ID
            traits: Account traits to update

        Returns:
            Updated account data

        Example:
            >>> await vitally.update_account(
            ...     account_id="acme_corp",
            ...     traits={"arr": 75000, "plan": "Enterprise Plus"}
            ... )
        """
        data = {
            'accountId': account_id,
            'traits': traits
        }

        result = await self._make_request(
            method='PATCH',
            endpoint=f'/accounts/{account_id}',
            data=data
        )

        logger.info(
            "vitally_account_updated",
            account_id=account_id
        )

        return result

    async def list_accounts(
        self,
        limit: int = 100,
        sort_by: str = 'createdAt',
        sort_direction: str = 'desc'
    ) -> Dict[str, Any]:
        """
        List accounts.

        Args:
            limit: Max results
            sort_by: Sort field
            sort_direction: Sort direction ('asc' or 'desc')

        Returns:
            List of accounts
        """
        params = {
            'limit': limit,
            'sortBy': sort_by,
            'sortDirection': sort_direction
        }

        return await self._make_request(
            method='GET',
            endpoint='/accounts',
            params=params
        )

    # ===================================================================
    # USERS API
    # ===================================================================

    async def create_user(
        self,
        user_id: str,
        account_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        traits: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or update a user.

        Args:
            user_id: External user ID
            account_id: External account ID
            name: User name
            email: User email
            traits: User traits/properties

        Returns:
            Created/updated user data

        Example:
            >>> user = await vitally.create_user(
            ...     user_id="john.doe@acme.com",
            ...     account_id="acme_corp",
            ...     name="John Doe",
            ...     email="john.doe@acme.com",
            ...     traits={"role": "Admin", "department": "Engineering"}
            ... )
        """
        data = {
            'userId': user_id,
            'accountId': account_id
        }

        if name:
            data['name'] = name
        if email:
            data['email'] = email
        if traits:
            data['traits'] = traits

        result = await self._make_request(
            method='POST',
            endpoint='/users',
            data=data
        )

        logger.info(
            "vitally_user_created",
            user_id=user_id,
            account_id=account_id
        )

        return result

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user details.

        Args:
            user_id: External user ID

        Returns:
            User data
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/users/{user_id}'
        )

    # ===================================================================
    # EVENTS API (PRODUCT USAGE)
    # ===================================================================

    async def track_event(
        self,
        event_name: str,
        account_id: Optional[str] = None,
        user_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track a product usage event.

        Args:
            event_name: Event name
            account_id: External account ID (optional)
            user_id: External user ID (optional)
            properties: Event properties
            timestamp: Event timestamp (ISO format, defaults to now)

        Returns:
            Track confirmation

        Example:
            >>> await vitally.track_event(
            ...     event_name="feature_used",
            ...     account_id="acme_corp",
            ...     user_id="john.doe@acme.com",
            ...     properties={
            ...         "feature_name": "advanced_reporting",
            ...         "duration_seconds": 120
            ...     }
            ... )
        """
        data = {
            'event': event_name,
            'timestamp': timestamp or datetime.utcnow().isoformat() + 'Z'
        }

        if account_id:
            data['accountId'] = account_id
        if user_id:
            data['userId'] = user_id
        if properties:
            data['properties'] = properties

        result = await self._make_request(
            method='POST',
            endpoint='/events',
            data=data
        )

        logger.info(
            "vitally_event_tracked",
            event_name=event_name,
            account_id=account_id,
            user_id=user_id
        )

        return result

    # ===================================================================
    # NOTES API
    # ===================================================================

    async def create_note(
        self,
        account_id: str,
        content: str,
        author_id: Optional[str] = None,
        note_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Create a note on an account.

        Args:
            account_id: External account ID
            content: Note content
            author_id: User ID of note author (optional)
            note_type: Note type (e.g., "general", "call", "meeting")

        Returns:
            Created note data

        Example:
            >>> note = await vitally.create_note(
            ...     account_id="acme_corp",
            ...     content="Had great QBR discussion. Customer is very happy with new features.",
            ...     author_id="csm@company.com",
            ...     note_type="meeting"
            ... )
        """
        data = {
            'accountId': account_id,
            'content': content,
            'type': note_type
        }

        if author_id:
            data['authorId'] = author_id

        result = await self._make_request(
            method='POST',
            endpoint='/notes',
            data=data
        )

        logger.info(
            "vitally_note_created",
            account_id=account_id,
            note_type=note_type
        )

        return result

    async def list_notes(
        self,
        account_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List notes for an account.

        Args:
            account_id: External account ID
            limit: Max results

        Returns:
            List of notes
        """
        params = {
            'accountId': account_id,
            'limit': limit
        }

        return await self._make_request(
            method='GET',
            endpoint='/notes',
            params=params
        )

    # ===================================================================
    # TASKS API
    # ===================================================================

    async def create_task(
        self,
        account_id: str,
        title: str,
        assignee_id: Optional[str] = None,
        due_date: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a task.

        Args:
            account_id: External account ID
            title: Task title
            assignee_id: User ID to assign to (optional)
            due_date: Due date (ISO format)
            description: Task description

        Returns:
            Created task data

        Example:
            >>> task = await vitally.create_task(
            ...     account_id="acme_corp",
            ...     title="Follow up on renewal discussion",
            ...     assignee_id="csm@company.com",
            ...     due_date="2024-12-31T23:59:59Z",
            ...     description="Discuss contract renewal and pricing for next year"
            ... )
        """
        data = {
            'accountId': account_id,
            'title': title
        }

        if assignee_id:
            data['assigneeId'] = assignee_id
        if due_date:
            data['dueDate'] = due_date
        if description:
            data['description'] = description

        result = await self._make_request(
            method='POST',
            endpoint='/tasks',
            data=data
        )

        logger.info(
            "vitally_task_created",
            account_id=account_id,
            title=title
        )

        return result

    async def list_tasks(
        self,
        account_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List tasks.

        Args:
            account_id: Filter by account (optional)
            assignee_id: Filter by assignee (optional)
            status: Filter by status (e.g., "open", "completed")
            limit: Max results

        Returns:
            List of tasks
        """
        params = {'limit': limit}

        if account_id:
            params['accountId'] = account_id
        if assignee_id:
            params['assigneeId'] = assignee_id
        if status:
            params['status'] = status

        return await self._make_request(
            method='GET',
            endpoint='/tasks',
            params=params
        )

    # ===================================================================
    # CONVERSATIONS API
    # ===================================================================

    async def create_conversation(
        self,
        account_id: str,
        user_id: Optional[str] = None,
        subject: Optional[str] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a conversation.

        Args:
            account_id: External account ID
            user_id: External user ID (optional)
            subject: Conversation subject
            content: Conversation content

        Returns:
            Created conversation data
        """
        data = {
            'accountId': account_id
        }

        if user_id:
            data['userId'] = user_id
        if subject:
            data['subject'] = subject
        if content:
            data['content'] = content

        result = await self._make_request(
            method='POST',
            endpoint='/conversations',
            data=data
        )

        logger.info(
            "vitally_conversation_created",
            account_id=account_id
        )

        return result

    # ===================================================================
    # NPS API
    # ===================================================================

    async def record_nps_response(
        self,
        account_id: str,
        user_id: str,
        score: int,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record an NPS survey response.

        Args:
            account_id: External account ID
            user_id: External user ID
            score: NPS score (0-10)
            comment: Survey comment (optional)

        Returns:
            NPS response data

        Example:
            >>> await vitally.record_nps_response(
            ...     account_id="acme_corp",
            ...     user_id="john.doe@acme.com",
            ...     score=9,
            ...     comment="Love the new features!"
            ... )
        """
        if not 0 <= score <= 10:
            raise ValidationError("NPS score must be between 0 and 10")

        data = {
            'accountId': account_id,
            'userId': user_id,
            'score': score
        }

        if comment:
            data['comment'] = comment

        result = await self._make_request(
            method='POST',
            endpoint='/nps',
            data=data
        )

        logger.info(
            "vitally_nps_recorded",
            account_id=account_id,
            score=score
        )

        return result

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("vitally_session_closed")
