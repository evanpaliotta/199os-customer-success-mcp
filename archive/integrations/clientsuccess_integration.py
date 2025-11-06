"""
ClientSuccess Integration
Priority Score: 9
ICP Adoption: 25-35% of SMB/Mid-market SaaS companies

Customer success management platform providing:
- Clients and Contacts
- Subscriptions
- Pulse (Health Checks)
- Success Cycles
- To-dos and Interactions
- Renewals
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


class ClientSuccessIntegration(BaseIntegration):
    """
    ClientSuccess API integration with API key authentication.

    Authentication:
    - Username and Password in HTTP Basic Auth
    - API Key alternative

    Rate Limits:
    - 120 requests per minute
    - 10000 requests per day

    Documentation: https://docs.clientsuccess.com/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ) -> Any:
        """
        Initialize ClientSuccess integration.

        Args:
            credentials: ClientSuccess credentials
                - username: ClientSuccess username
                - password: ClientSuccess password
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="clientsuccess",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.username = credentials.get('username', '')
        self.password = credentials.get('password', '')

        if not self.username:
            raise ValidationError("ClientSuccess username is required")
        if not self.password:
            raise ValidationError("ClientSuccess password is required")

        self.base_url = "https://api.clientsuccess.com/v1"

        logger.info(
            "clientsuccess_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with ClientSuccess (basic auth)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("clientsuccess_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"ClientSuccess authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make authenticated HTTP request to ClientSuccess API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        import aiohttp
        auth = aiohttp.BasicAuth(login=self.username, password=self.password)

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        try:
            async with self.session.request(
                method,
                url,
                json=data,
                params=params,
                auth=auth,
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
                        f"ClientSuccess API error ({response.status}): {error_text}",
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
        """Test connection to ClientSuccess API."""
        try:
            start_time = datetime.now()

            # Test with clients list request
            response = await self._make_request(
                method='GET',
                endpoint='/clients',
                params={'page': 1, 'rows': 1}
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to ClientSuccess",
                response_time_ms=duration_ms,
                metadata={'integration_name': 'clientsuccess'}
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"ClientSuccess connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # CLIENTS API
    # ===================================================================

    async def list_clients(
        self,
        page: int = 1,
        rows: int = 100,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List clients.

        Args:
            page: Page number
            rows: Results per page (max: 1000)
            status: Filter by status (active, churned, lost)

        Returns:
            Paginated list of clients

        Example:
            >>> clients = await clientsuccess.list_clients(
            ...     page=1,
            ...     rows=50,
            ...     status="active"
            ... )
            >>> for client in clients['data']:
            ...     print(f"{client['name']}: {client['pulse_score']}")
        """
        params = {
            'page': page,
            'rows': min(rows, 1000)
        }

        if status:
            params['status'] = status

        result = await self._make_request(
            method='GET',
            endpoint='/clients',
            params=params
        )

        logger.info(
            "clientsuccess_clients_listed",
            count=len(result.get('data', [])) if isinstance(result, dict) else 0
        )

        return result

    async def get_client(self, client_id: int) -> Dict[str, Any]:
        """
        Get client by ID.

        Args:
            client_id: Client ID

        Returns:
            Client details with subscriptions and pulse score

        Example:
            >>> client = await clientsuccess.get_client(12345)
            >>> print(f"Pulse: {client['pulse_score']}")
            >>> print(f"Status: {client['status']}")
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/clients/{client_id}'
        )

    async def create_client(
        self,
        name: str,
        status: str = "active",
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a client.

        Args:
            name: Client name
            status: Client status (active, churned, lost)
            custom_fields: Custom field values

        Returns:
            Created client

        Example:
            >>> client = await clientsuccess.create_client(
            ...     name="Acme Corporation",
            ...     status="active",
            ...     custom_fields={
            ...         "industry": "Technology",
            ...         "employees": 250,
            ...         "arr": 120000
            ...     }
            ... )
        """
        data = {
            'name': name,
            'status': status
        }

        if custom_fields:
            for key, value in custom_fields.items():
                data[key] = value

        result = await self._make_request(
            method='POST',
            endpoint='/clients',
            data=data
        )

        logger.info(
            "clientsuccess_client_created",
            client_id=result.get('id'),
            name=name
        )

        return result

    async def update_client(
        self,
        client_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update client fields.

        Args:
            client_id: Client ID
            data: Fields to update

        Returns:
            Updated client data

        Example:
            >>> await clientsuccess.update_client(
            ...     client_id=12345,
            ...     data={"status": "active", "arr": 150000}
            ... )
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/clients/{client_id}',
            data=data
        )

        logger.info(
            "clientsuccess_client_updated",
            client_id=client_id
        )

        return result

    async def delete_client(self, client_id: int) -> Dict[str, Any]:
        """
        Delete a client.

        Args:
            client_id: Client ID

        Returns:
            Deletion confirmation
        """
        result = await self._make_request(
            method='DELETE',
            endpoint=f'/clients/{client_id}'
        )

        logger.info(
            "clientsuccess_client_deleted",
            client_id=client_id
        )

        return result

    # ===================================================================
    # CONTACTS API
    # ===================================================================

    async def list_contacts(
        self,
        client_id: Optional[int] = None,
        page: int = 1,
        rows: int = 100
    ) -> Dict[str, Any]:
        """
        List contacts.

        Args:
            client_id: Filter by client ID
            page: Page number
            rows: Results per page

        Returns:
            Paginated list of contacts
        """
        params = {
            'page': page,
            'rows': min(rows, 1000)
        }

        if client_id:
            params['clientId'] = client_id

        result = await self._make_request(
            method='GET',
            endpoint='/contacts',
            params=params
        )

        logger.info(
            "clientsuccess_contacts_listed",
            count=len(result.get('data', [])) if isinstance(result, dict) else 0,
            client_id=client_id
        )

        return result

    async def get_contact(self, contact_id: int) -> Dict[str, Any]:
        """
        Get contact by ID.

        Args:
            contact_id: Contact ID

        Returns:
            Contact details
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/contacts/{contact_id}'
        )

    async def create_contact(
        self,
        client_id: int,
        first_name: str,
        last_name: str,
        email: str,
        title: Optional[str] = None,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a contact.

        Args:
            client_id: Client ID
            first_name: First name
            last_name: Last name
            email: Email address
            title: Job title
            role: Contact role (champion, decision_maker, user)

        Returns:
            Created contact

        Example:
            >>> contact = await clientsuccess.create_contact(
            ...     client_id=12345,
            ...     first_name="Jane",
            ...     last_name="Doe",
            ...     email="jane@acme.com",
            ...     title="VP of Operations",
            ...     role="champion"
            ... )
        """
        data = {
            'clientId': client_id,
            'firstName': first_name,
            'lastName': last_name,
            'email': email
        }

        if title:
            data['title'] = title
        if role:
            data['role'] = role

        result = await self._make_request(
            method='POST',
            endpoint='/contacts',
            data=data
        )

        logger.info(
            "clientsuccess_contact_created",
            contact_id=result.get('id'),
            email=email,
            client_id=client_id
        )

        return result

    async def update_contact(
        self,
        contact_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update contact fields.

        Args:
            contact_id: Contact ID
            data: Fields to update

        Returns:
            Updated contact data
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/contacts/{contact_id}',
            data=data
        )

        logger.info(
            "clientsuccess_contact_updated",
            contact_id=contact_id
        )

        return result

    # ===================================================================
    # SUBSCRIPTIONS API
    # ===================================================================

    async def list_subscriptions(
        self,
        client_id: Optional[int] = None,
        page: int = 1,
        rows: int = 100
    ) -> Dict[str, Any]:
        """
        List subscriptions.

        Args:
            client_id: Filter by client ID
            page: Page number
            rows: Results per page

        Returns:
            Paginated list of subscriptions
        """
        params = {
            'page': page,
            'rows': min(rows, 1000)
        }

        if client_id:
            params['clientId'] = client_id

        result = await self._make_request(
            method='GET',
            endpoint='/subscriptions',
            params=params
        )

        logger.info(
            "clientsuccess_subscriptions_listed",
            count=len(result.get('data', [])) if isinstance(result, dict) else 0,
            client_id=client_id
        )

        return result

    async def get_subscription(self, subscription_id: int) -> Dict[str, Any]:
        """
        Get subscription by ID.

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription details with products and billing
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/subscriptions/{subscription_id}'
        )

    async def create_subscription(
        self,
        client_id: int,
        name: str,
        mrr: float,
        billing_cycle: str = "monthly",
        start_date: Optional[str] = None,
        renewal_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription.

        Args:
            client_id: Client ID
            name: Subscription name
            mrr: Monthly recurring revenue
            billing_cycle: Billing cycle (monthly, quarterly, annual)
            start_date: Start date (ISO format)
            renewal_date: Renewal date (ISO format)

        Returns:
            Created subscription

        Example:
            >>> subscription = await clientsuccess.create_subscription(
            ...     client_id=12345,
            ...     name="Enterprise Plan",
            ...     mrr=999,
            ...     billing_cycle="monthly",
            ...     renewal_date="2025-12-31T00:00:00Z"
            ... )
        """
        data = {
            'clientId': client_id,
            'name': name,
            'mrr': mrr,
            'billingCycle': billing_cycle
        }

        if start_date:
            data['startDate'] = start_date
        if renewal_date:
            data['renewalDate'] = renewal_date

        result = await self._make_request(
            method='POST',
            endpoint='/subscriptions',
            data=data
        )

        logger.info(
            "clientsuccess_subscription_created",
            subscription_id=result.get('id'),
            client_id=client_id,
            mrr=mrr
        )

        return result

    async def update_subscription(
        self,
        subscription_id: int,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update subscription fields.

        Args:
            subscription_id: Subscription ID
            data: Fields to update

        Returns:
            Updated subscription data
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/subscriptions/{subscription_id}',
            data=data
        )

        logger.info(
            "clientsuccess_subscription_updated",
            subscription_id=subscription_id
        )

        return result

    # ===================================================================
    # PULSE (HEALTH CHECKS) API
    # ===================================================================

    async def get_pulse_score(self, client_id: int) -> Dict[str, Any]:
        """
        Get client pulse (health) score.

        Args:
            client_id: Client ID

        Returns:
            Pulse score with components

        Example:
            >>> pulse = await clientsuccess.get_pulse_score(12345)
            >>> print(f"Score: {pulse['score']}")
            >>> print(f"Status: {pulse['status']}")
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/clients/{client_id}/pulse'
        )

    async def update_pulse_score(
        self,
        client_id: int,
        score: float,
        components: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update client pulse score.

        Args:
            client_id: Client ID
            score: Pulse score (0-100)
            components: Score components

        Returns:
            Updated pulse score

        Example:
            >>> await clientsuccess.update_pulse_score(
            ...     client_id=12345,
            ...     score=85,
            ...     components={
            ...         "product_usage": 90,
            ...         "support_satisfaction": 80,
            ...         "engagement": 85
            ...     }
            ... )
        """
        data = {'score': score}

        if components:
            data['components'] = components

        result = await self._make_request(
            method='PUT',
            endpoint=f'/clients/{client_id}/pulse',
            data=data
        )

        logger.info(
            "clientsuccess_pulse_updated",
            client_id=client_id,
            score=score
        )

        return result

    async def get_pulse_history(
        self,
        client_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pulse score history.

        Args:
            client_id: Client ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Time series pulse score data
        """
        params = {}

        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date

        result = await self._make_request(
            method='GET',
            endpoint=f'/clients/{client_id}/pulse/history',
            params=params
        )

        return result if isinstance(result, list) else []

    # ===================================================================
    # SUCCESS CYCLES API
    # ===================================================================

    async def list_success_cycles(
        self,
        client_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List success cycles.

        Args:
            client_id: Filter by client ID
            status: Filter by status (active, completed)

        Returns:
            List of success cycles

        Example:
            >>> cycles = await clientsuccess.list_success_cycles(
            ...     client_id=12345,
            ...     status="active"
            ... )
        """
        params = {}

        if client_id:
            params['clientId'] = client_id
        if status:
            params['status'] = status

        result = await self._make_request(
            method='GET',
            endpoint='/success-cycles',
            params=params
        )

        return result if isinstance(result, list) else []

    async def create_success_cycle(
        self,
        client_id: int,
        name: str,
        start_date: str,
        end_date: str,
        objectives: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a success cycle.

        Args:
            client_id: Client ID
            name: Success cycle name
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            objectives: List of objectives

        Returns:
            Created success cycle

        Example:
            >>> cycle = await clientsuccess.create_success_cycle(
            ...     client_id=12345,
            ...     name="Q4 2024 Onboarding",
            ...     start_date="2024-10-01",
            ...     end_date="2024-12-31",
            ...     objectives=[
            ...         "Complete product training",
            ...         "Achieve 80% feature adoption"
            ...     ]
            ... )
        """
        data = {
            'clientId': client_id,
            'name': name,
            'startDate': start_date,
            'endDate': end_date
        }

        if objectives:
            data['objectives'] = objectives

        result = await self._make_request(
            method='POST',
            endpoint='/success-cycles',
            data=data
        )

        logger.info(
            "clientsuccess_success_cycle_created",
            cycle_id=result.get('id'),
            client_id=client_id,
            name=name
        )

        return result

    # ===================================================================
    # TO-DOS API
    # ===================================================================

    async def list_todos(
        self,
        client_id: Optional[int] = None,
        assigned_to: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List to-dos.

        Args:
            client_id: Filter by client ID
            assigned_to: Filter by assigned user ID
            status: Filter by status (open, completed, overdue)

        Returns:
            List of to-dos
        """
        params = {}

        if client_id:
            params['clientId'] = client_id
        if assigned_to:
            params['assignedTo'] = assigned_to
        if status:
            params['status'] = status

        result = await self._make_request(
            method='GET',
            endpoint='/todos',
            params=params
        )

        return result if isinstance(result, list) else []

    async def create_todo(
        self,
        client_id: int,
        title: str,
        description: Optional[str] = None,
        assigned_to: Optional[int] = None,
        due_date: Optional[str] = None,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Create a to-do.

        Args:
            client_id: Client ID
            title: To-do title
            description: To-do description
            assigned_to: Assigned user ID
            due_date: Due date (ISO format)
            priority: Priority level (low, medium, high)

        Returns:
            Created to-do

        Example:
            >>> todo = await clientsuccess.create_todo(
            ...     client_id=12345,
            ...     title="Schedule QBR",
            ...     description="Schedule Q4 quarterly business review",
            ...     assigned_to=67890,
            ...     due_date="2024-12-15T00:00:00Z",
            ...     priority="high"
            ... )
        """
        data = {
            'clientId': client_id,
            'title': title,
            'priority': priority
        }

        if description:
            data['description'] = description
        if assigned_to:
            data['assignedTo'] = assigned_to
        if due_date:
            data['dueDate'] = due_date

        result = await self._make_request(
            method='POST',
            endpoint='/todos',
            data=data
        )

        logger.info(
            "clientsuccess_todo_created",
            todo_id=result.get('id'),
            client_id=client_id,
            title=title
        )

        return result

    async def complete_todo(self, todo_id: int) -> Dict[str, Any]:
        """
        Mark to-do as completed.

        Args:
            todo_id: To-do ID

        Returns:
            Updated to-do data
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/todos/{todo_id}',
            data={'status': 'completed'}
        )

        logger.info(
            "clientsuccess_todo_completed",
            todo_id=todo_id
        )

        return result

    # ===================================================================
    # INTERACTIONS API
    # ===================================================================

    async def list_interactions(
        self,
        client_id: Optional[int] = None,
        page: int = 1,
        rows: int = 100
    ) -> Dict[str, Any]:
        """
        List interactions (customer touchpoints).

        Args:
            client_id: Filter by client ID
            page: Page number
            rows: Results per page

        Returns:
            Paginated list of interactions
        """
        params = {
            'page': page,
            'rows': min(rows, 1000)
        }

        if client_id:
            params['clientId'] = client_id

        result = await self._make_request(
            method='GET',
            endpoint='/interactions',
            params=params
        )

        logger.info(
            "clientsuccess_interactions_listed",
            count=len(result.get('data', [])) if isinstance(result, dict) else 0,
            client_id=client_id
        )

        return result

    async def create_interaction(
        self,
        client_id: int,
        type: str,
        title: str,
        description: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an interaction.

        Args:
            client_id: Client ID
            type: Interaction type (call, email, meeting, note)
            title: Interaction title
            description: Interaction description
            date: Interaction date (ISO format)

        Returns:
            Created interaction

        Example:
            >>> interaction = await clientsuccess.create_interaction(
            ...     client_id=12345,
            ...     type="meeting",
            ...     title="Quarterly Business Review",
            ...     description="Reviewed Q4 performance and 2025 roadmap",
            ...     date="2024-12-15T14:00:00Z"
            ... )
        """
        data = {
            'clientId': client_id,
            'type': type,
            'title': title,
            'date': date or datetime.utcnow().isoformat()
        }

        if description:
            data['description'] = description

        result = await self._make_request(
            method='POST',
            endpoint='/interactions',
            data=data
        )

        logger.info(
            "clientsuccess_interaction_created",
            interaction_id=result.get('id'),
            client_id=client_id,
            type=type
        )

        return result

    async def close(self) -> Any:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("clientsuccess_session_closed")
