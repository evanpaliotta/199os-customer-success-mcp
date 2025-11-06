"""
Zendesk Integration (UPGRADED to OAuth2)
Priority Score: 15
ICP Adoption: 80%+ of companies using support/ticketing

Leading customer support platform providing:
- Ticket Management (create, update, search)
- User and Organization Management
- Custom Ticket Fields and Forms
- Macros and Automations
- SLA Policies and Monitoring
- CSAT/Satisfaction Ratings
- Support Analytics and Reporting
- Multi-channel Support (email, chat, phone, social)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from .auth.oauth2_base import OAuth2Integration
from .base import ConnectionTestResult, IntegrationStatus, ValidationError, APIError

logger = structlog.get_logger(__name__)


class ZendeskIntegration(OAuth2Integration):
    """
    Zendesk OAuth2 integration for customer support operations.

    Authentication:
    - OAuth2 with authorization code flow
    - Requires: client_id, client_secret, subdomain
    - Access token format: Bearer token

    Rate Limits:
    - 700 requests per minute (API v2)
    - 200 requests per minute for search
    - 100 requests per minute for incremental exports

    Documentation: https://developer.zendesk.com/api-reference/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ):
        """
        Initialize Zendesk integration.

        Args:
            credentials: OAuth2 credentials
                - client_id: Zendesk OAuth client ID
                - client_secret: Zendesk OAuth client secret
                - subdomain: Zendesk subdomain (e.g., "company")
                - access_token: Current access token (optional)
                - refresh_token: Refresh token (optional)
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        self.subdomain = credentials.get('subdomain', '')
        if not self.subdomain:
            raise ValidationError("Zendesk subdomain is required")

        super().__init__(
            integration_name="zendesk",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        logger.info(
            "zendesk_initialized",
            subdomain=self.subdomain,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    def get_oauth_config(self) -> Dict[str, Any]:
        """Get Zendesk OAuth2 configuration."""
        return {
            'auth_url': f'https://{self.subdomain}.zendesk.com/oauth/authorizations/new',
            'token_url': f'https://{self.subdomain}.zendesk.com/oauth/tokens',
            'api_base_url': f'https://{self.subdomain}.zendesk.com/api/v2',
            'scopes': ['read', 'write']  # Zendesk OAuth scopes
        }

    async def test_connection(self) -> ConnectionTestResult:
        """Test connection to Zendesk API."""
        try:
            start_time = datetime.now()

            # Test with current user info
            response = await self._make_request(
                method='GET',
                endpoint='/users/me.json'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            user = response.get('user', {})
            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Zendesk",
                response_time_ms=duration_ms,
                metadata={
                    'user_id': user.get('id'),
                    'email': user.get('email'),
                    'role': user.get('role'),
                    'subdomain': self.subdomain,
                    'integration_name': 'zendesk'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Zendesk connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # TICKETS API
    # ===================================================================

    async def create_ticket(
        self,
        subject: str,
        description: str,
        requester_id: Optional[int] = None,
        requester_email: Optional[str] = None,
        priority: str = "normal",
        status: str = "new",
        tags: Optional[List[str]] = None,
        custom_fields: Optional[List[Dict[str, Any]]] = None,
        assignee_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new support ticket.

        Args:
            subject: Ticket subject/title
            description: Ticket description/body
            requester_id: Zendesk user ID of requester
            requester_email: Email of requester (alternative to ID)
            priority: Ticket priority (low, normal, high, urgent)
            status: Ticket status (new, open, pending, hold, solved, closed)
            tags: List of tags
            custom_fields: Custom field values [{id: 123, value: "foo"}]
            assignee_id: User ID to assign ticket to

        Returns:
            Created ticket data

        Example:
            >>> ticket = await zendesk.create_ticket(
            ...     subject="Login issues",
            ...     description="User cannot log in",
            ...     requester_email="user@example.com",
            ...     priority="high",
            ...     tags=["login", "urgent"]
            ... )
        """
        ticket_data = {
            'subject': subject,
            'description': description,
            'priority': priority,
            'status': status
        }

        if requester_id:
            ticket_data['requester_id'] = requester_id
        elif requester_email:
            ticket_data['requester'] = {'email': requester_email}

        if tags:
            ticket_data['tags'] = tags
        if custom_fields:
            ticket_data['custom_fields'] = custom_fields
        if assignee_id:
            ticket_data['assignee_id'] = assignee_id

        result = await self._make_request(
            method='POST',
            endpoint='/tickets.json',
            data={'ticket': ticket_data}
        )

        ticket = result.get('ticket', {})
        logger.info(
            "zendesk_ticket_created",
            ticket_id=ticket.get('id'),
            subject=subject,
            priority=priority
        )

        return ticket

    async def get_ticket(self, ticket_id: int) -> Dict[str, Any]:
        """
        Get ticket by ID.

        Args:
            ticket_id: Zendesk ticket ID

        Returns:
            Ticket data
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/tickets/{ticket_id}.json'
        )
        return result.get('ticket', {})

    async def update_ticket(
        self,
        ticket_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        comment: Optional[str] = None,
        public_comment: bool = True,
        custom_fields: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing ticket.

        Args:
            ticket_id: Zendesk ticket ID
            status: New status (new, open, pending, hold, solved, closed)
            priority: New priority (low, normal, high, urgent)
            assignee_id: User ID to assign ticket to
            tags: Tags to add
            comment: Comment to add with update
            public_comment: Whether comment is visible to requester
            custom_fields: Custom field updates [{id: 123, value: "foo"}]

        Returns:
            Updated ticket data
        """
        ticket_data = {}

        if status:
            ticket_data['status'] = status
        if priority:
            ticket_data['priority'] = priority
        if assignee_id:
            ticket_data['assignee_id'] = assignee_id
        if tags:
            ticket_data['tags'] = tags
        if custom_fields:
            ticket_data['custom_fields'] = custom_fields

        if comment:
            ticket_data['comment'] = {
                'body': comment,
                'public': public_comment
            }

        result = await self._make_request(
            method='PUT',
            endpoint=f'/tickets/{ticket_id}.json',
            data={'ticket': ticket_data}
        )

        logger.info(
            "zendesk_ticket_updated",
            ticket_id=ticket_id,
            status=status,
            comment_added=bool(comment)
        )

        return result.get('ticket', {})

    async def search_tickets(
        self,
        query: str,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        per_page: int = 100
    ) -> Dict[str, Any]:
        """
        Search tickets using Zendesk search syntax.

        Args:
            query: Search query (e.g., "status:open priority:high")
            sort_by: Sort field
            sort_order: Sort order (asc or desc)
            per_page: Results per page (max 100)

        Returns:
            Search results with tickets

        Example:
            >>> results = await zendesk.search_tickets(
            ...     query="status:open priority:high",
            ...     sort_by="updated_at"
            ... )
        """
        params = {
            'query': f"type:ticket {query}",
            'sort_by': sort_by,
            'sort_order': sort_order,
            'per_page': per_page
        }

        result = await self._make_request(
            method='GET',
            endpoint='/search.json',
            params=params
        )

        logger.info(
            "zendesk_tickets_searched",
            query=query,
            results_count=len(result.get('results', []))
        )

        return result

    async def add_comment(
        self,
        ticket_id: int,
        body: str,
        public: bool = True,
        author_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add comment to ticket.

        Args:
            ticket_id: Zendesk ticket ID
            body: Comment text
            public: Whether comment is public (visible to requester)
            author_id: User ID of comment author

        Returns:
            Updated ticket data
        """
        comment_data = {
            'body': body,
            'public': public
        }

        if author_id:
            comment_data['author_id'] = author_id

        result = await self._make_request(
            method='PUT',
            endpoint=f'/tickets/{ticket_id}.json',
            data={'ticket': {'comment': comment_data}}
        )

        logger.info(
            "zendesk_comment_added",
            ticket_id=ticket_id,
            public=public
        )

        return result.get('ticket', {})

    # ===================================================================
    # USERS API
    # ===================================================================

    async def create_user(
        self,
        name: str,
        email: str,
        role: str = "end-user",
        organization_id: Optional[int] = None,
        phone: Optional[str] = None,
        tags: Optional[List[str]] = None,
        user_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new user.

        Args:
            name: User's full name
            email: User's email address
            role: User role (end-user, agent, admin)
            organization_id: Organization ID
            phone: Phone number
            tags: User tags
            user_fields: Custom user fields

        Returns:
            Created user data
        """
        user_data = {
            'name': name,
            'email': email,
            'role': role
        }

        if organization_id:
            user_data['organization_id'] = organization_id
        if phone:
            user_data['phone'] = phone
        if tags:
            user_data['tags'] = tags
        if user_fields:
            user_data['user_fields'] = user_fields

        result = await self._make_request(
            method='POST',
            endpoint='/users.json',
            data={'user': user_data}
        )

        user = result.get('user', {})
        logger.info(
            "zendesk_user_created",
            user_id=user.get('id'),
            email=email,
            role=role
        )

        return user

    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID."""
        result = await self._make_request(
            method='GET',
            endpoint=f'/users/{user_id}.json'
        )
        return result.get('user', {})

    async def search_users(self, query: str) -> Dict[str, Any]:
        """
        Search users.

        Args:
            query: Search query (e.g., "email:user@example.com")

        Returns:
            Search results with users
        """
        params = {'query': query}
        result = await self._make_request(
            method='GET',
            endpoint='/users/search.json',
            params=params
        )
        return result

    # ===================================================================
    # ORGANIZATIONS API
    # ===================================================================

    async def create_organization(
        self,
        name: str,
        domain_names: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        organization_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an organization.

        Args:
            name: Organization name
            domain_names: Associated domain names
            tags: Organization tags
            organization_fields: Custom organization fields

        Returns:
            Created organization data
        """
        org_data = {'name': name}

        if domain_names:
            org_data['domain_names'] = domain_names
        if tags:
            org_data['tags'] = tags
        if organization_fields:
            org_data['organization_fields'] = organization_fields

        result = await self._make_request(
            method='POST',
            endpoint='/organizations.json',
            data={'organization': org_data}
        )

        org = result.get('organization', {})
        logger.info(
            "zendesk_organization_created",
            org_id=org.get('id'),
            name=name
        )

        return org

    async def get_organization(self, org_id: int) -> Dict[str, Any]:
        """Get organization by ID."""
        result = await self._make_request(
            method='GET',
            endpoint=f'/organizations/{org_id}.json'
        )
        return result.get('organization', {})

    # ===================================================================
    # TICKET FIELDS API
    # ===================================================================

    async def list_ticket_fields(self) -> List[Dict[str, Any]]:
        """
        List all ticket fields.

        Returns:
            List of ticket fields
        """
        result = await self._make_request(
            method='GET',
            endpoint='/ticket_fields.json'
        )
        return result.get('ticket_fields', [])

    async def create_ticket_field(
        self,
        type: str,
        title: str,
        description: Optional[str] = None,
        custom_field_options: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Create a custom ticket field.

        Args:
            type: Field type (text, textarea, checkbox, dropdown, etc.)
            title: Field title
            description: Field description
            custom_field_options: Options for dropdown/multiselect [{name: "Option", value: "opt"}]

        Returns:
            Created field data
        """
        field_data = {
            'type': type,
            'title': title
        }

        if description:
            field_data['description'] = description
        if custom_field_options:
            field_data['custom_field_options'] = custom_field_options

        result = await self._make_request(
            method='POST',
            endpoint='/ticket_fields.json',
            data={'ticket_field': field_data}
        )

        return result.get('ticket_field', {})

    # ===================================================================
    # MACROS API
    # ===================================================================

    async def list_macros(self, active: bool = True) -> List[Dict[str, Any]]:
        """
        List macros.

        Args:
            active: Filter by active status

        Returns:
            List of macros
        """
        params = {}
        if active:
            params['active'] = 'true'

        result = await self._make_request(
            method='GET',
            endpoint='/macros.json',
            params=params
        )
        return result.get('macros', [])

    async def apply_macro(
        self,
        ticket_id: int,
        macro_id: int
    ) -> Dict[str, Any]:
        """
        Apply macro to ticket.

        Args:
            ticket_id: Zendesk ticket ID
            macro_id: Zendesk macro ID

        Returns:
            Result with macro changes
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/tickets/{ticket_id}/macros/{macro_id}/apply.json'
        )

        logger.info(
            "zendesk_macro_applied",
            ticket_id=ticket_id,
            macro_id=macro_id
        )

        return result.get('result', {})

    # ===================================================================
    # SLA POLICIES API
    # ===================================================================

    async def list_sla_policies(self) -> List[Dict[str, Any]]:
        """
        List SLA policies.

        Returns:
            List of SLA policies
        """
        result = await self._make_request(
            method='GET',
            endpoint='/slas/policies.json'
        )
        return result.get('sla_policies', [])

    async def get_sla_policy(self, policy_id: int) -> Dict[str, Any]:
        """Get SLA policy by ID."""
        result = await self._make_request(
            method='GET',
            endpoint=f'/slas/policies/{policy_id}.json'
        )
        return result.get('sla_policy', {})

    # ===================================================================
    # SATISFACTION RATINGS API
    # ===================================================================

    async def list_satisfaction_ratings(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        score: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List satisfaction ratings.

        Args:
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            score: Filter by score (good, bad)

        Returns:
            List of satisfaction ratings
        """
        params = {}
        if start_time:
            params['start_time'] = start_time
        if end_time:
            params['end_time'] = end_time
        if score:
            params['score'] = score

        result = await self._make_request(
            method='GET',
            endpoint='/satisfaction_ratings.json',
            params=params
        )
        return result.get('satisfaction_ratings', [])

    async def create_satisfaction_rating(
        self,
        ticket_id: int,
        score: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create satisfaction rating.

        Args:
            ticket_id: Zendesk ticket ID
            score: Rating score (good, bad)
            comment: Rating comment

        Returns:
            Created rating data
        """
        rating_data = {
            'ticket_id': ticket_id,
            'score': score
        }

        if comment:
            rating_data['comment'] = comment

        result = await self._make_request(
            method='POST',
            endpoint='/satisfaction_ratings.json',
            data={'satisfaction_rating': rating_data}
        )

        return result.get('satisfaction_rating', {})

    # ===================================================================
    # ANALYTICS API
    # ===================================================================

    async def get_ticket_metrics(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get ticket metrics for date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Ticket metrics data
        """
        params = {
            'start_date': start_date,
            'end_date': end_date
        }

        result = await self._make_request(
            method='GET',
            endpoint='/ticket_metrics.json',
            params=params
        )

        return result

    async def get_incremental_tickets(
        self,
        start_time: int,
        include: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get incremental ticket exports (for sync).

        Args:
            start_time: Unix timestamp to start from
            include: Additional data to include (users, groups, etc.)

        Returns:
            Incremental ticket data with cursor for next page
        """
        params = {'start_time': start_time}
        if include:
            params['include'] = include

        result = await self._make_request(
            method='GET',
            endpoint='/incremental/tickets.json',
            params=params
        )

        return result
