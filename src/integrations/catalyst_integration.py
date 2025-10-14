"""
Catalyst Integration
Priority Score: 10
ICP Adoption: 20-30% of B2B SaaS companies

Customer success platform providing:
- Companies and Contacts
- Health Scores
- Tasks and Notes
- Playbooks
- Segments
- Team Collaboration
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


class CatalystIntegration(BaseIntegration):
    """
    Catalyst API integration with API key authentication.

    Authentication:
    - API Key in header (X-Api-Key)

    Rate Limits:
    - 100 requests per minute
    - Burst: 20 requests per second

    Documentation: https://docs.catalyst.io/api/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 90,
        rate_limit_window: int = 60
    ):
        """
        Initialize Catalyst integration.

        Args:
            credentials: Catalyst credentials
                - api_key: Catalyst API key
            rate_limit_calls: Max API calls per window (default: 90)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="catalyst",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')

        if not self.api_key:
            raise ValidationError("Catalyst api_key is required")

        self.base_url = "https://api.catalyst.io/v1"

        logger.info(
            "catalyst_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Catalyst (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("catalyst_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Catalyst authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make authenticated HTTP request to Catalyst API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            'X-Api-Key': self.api_key,
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
                        f"Catalyst API error ({response.status}): {error_text}",
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
        """Test connection to Catalyst API."""
        try:
            start_time = datetime.now()

            # Test with companies list request
            response = await self._make_request(
                method='GET',
                endpoint='/companies',
                params={'limit': 1}
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Catalyst",
                response_time_ms=duration_ms,
                metadata={'integration_name': 'catalyst'}
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Catalyst connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # COMPANIES API
    # ===================================================================

    async def list_companies(
        self,
        limit: int = 100,
        offset: int = 0,
        segment_id: Optional[str] = None,
        health_score_min: Optional[float] = None,
        health_score_max: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        List companies.

        Args:
            limit: Max results (max: 100)
            offset: Pagination offset
            segment_id: Filter by segment ID
            health_score_min: Minimum health score filter
            health_score_max: Maximum health score filter

        Returns:
            Paginated list of companies

        Example:
            >>> companies = await catalyst.list_companies(
            ...     health_score_min=70,
            ...     limit=50
            ... )
            >>> for company in companies['data']:
            ...     print(f"{company['name']}: {company['health_score']}")
        """
        params = {
            'limit': min(limit, 100),
            'offset': offset
        }

        if segment_id:
            params['segment_id'] = segment_id
        if health_score_min is not None:
            params['health_score_min'] = health_score_min
        if health_score_max is not None:
            params['health_score_max'] = health_score_max

        result = await self._make_request(
            method='GET',
            endpoint='/companies',
            params=params
        )

        logger.info(
            "catalyst_companies_listed",
            count=len(result.get('data', [])) if isinstance(result, dict) else 0
        )

        return result

    async def get_company(self, company_id: str) -> Dict[str, Any]:
        """
        Get company by ID.

        Args:
            company_id: Company ID

        Returns:
            Company details with health score and metadata

        Example:
            >>> company = await catalyst.get_company("comp_123")
            >>> print(f"Health: {company['health_score']}")
            >>> print(f"ARR: {company['arr']}")
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/companies/{company_id}'
        )

    async def create_company(
        self,
        name: str,
        domain: Optional[str] = None,
        arr: Optional[float] = None,
        plan: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a company.

        Args:
            name: Company name
            domain: Company domain
            arr: Annual recurring revenue
            plan: Subscription plan
            custom_fields: Custom field values

        Returns:
            Created company

        Example:
            >>> company = await catalyst.create_company(
            ...     name="Acme Corp",
            ...     domain="acme.com",
            ...     arr=120000,
            ...     plan="Enterprise",
            ...     custom_fields={
            ...         "industry": "Technology",
            ...         "employee_count": 250
            ...     }
            ... )
        """
        data = {'name': name}

        if domain:
            data['domain'] = domain
        if arr is not None:
            data['arr'] = arr
        if plan:
            data['plan'] = plan
        if custom_fields:
            data['custom_fields'] = custom_fields

        result = await self._make_request(
            method='POST',
            endpoint='/companies',
            data=data
        )

        logger.info(
            "catalyst_company_created",
            company_id=result.get('id'),
            name=name
        )

        return result

    async def update_company(
        self,
        company_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update company fields.

        Args:
            company_id: Company ID
            data: Fields to update

        Returns:
            Updated company data

        Example:
            >>> await catalyst.update_company(
            ...     company_id="comp_123",
            ...     data={"arr": 150000, "plan": "Enterprise Plus"}
            ... )
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/companies/{company_id}',
            data=data
        )

        logger.info(
            "catalyst_company_updated",
            company_id=company_id
        )

        return result

    async def delete_company(self, company_id: str) -> Dict[str, Any]:
        """
        Delete a company.

        Args:
            company_id: Company ID

        Returns:
            Deletion confirmation
        """
        result = await self._make_request(
            method='DELETE',
            endpoint=f'/companies/{company_id}'
        )

        logger.info(
            "catalyst_company_deleted",
            company_id=company_id
        )

        return result

    # ===================================================================
    # CONTACTS API
    # ===================================================================

    async def list_contacts(
        self,
        company_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List contacts.

        Args:
            company_id: Filter by company ID
            limit: Max results (max: 100)
            offset: Pagination offset

        Returns:
            Paginated list of contacts
        """
        params = {
            'limit': min(limit, 100),
            'offset': offset
        }

        if company_id:
            params['company_id'] = company_id

        result = await self._make_request(
            method='GET',
            endpoint='/contacts',
            params=params
        )

        logger.info(
            "catalyst_contacts_listed",
            count=len(result.get('data', [])) if isinstance(result, dict) else 0
        )

        return result

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
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
        company_id: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        title: Optional[str] = None,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a contact.

        Args:
            company_id: Company ID
            email: Contact email
            first_name: First name
            last_name: Last name
            title: Job title
            role: Contact role (champion, decision_maker, user, etc.)

        Returns:
            Created contact

        Example:
            >>> contact = await catalyst.create_contact(
            ...     company_id="comp_123",
            ...     email="jane@acme.com",
            ...     first_name="Jane",
            ...     last_name="Doe",
            ...     title="VP of Operations",
            ...     role="champion"
            ... )
        """
        data = {
            'company_id': company_id,
            'email': email
        }

        if first_name:
            data['first_name'] = first_name
        if last_name:
            data['last_name'] = last_name
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
            "catalyst_contact_created",
            contact_id=result.get('id'),
            email=email,
            company_id=company_id
        )

        return result

    async def update_contact(
        self,
        contact_id: str,
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
            "catalyst_contact_updated",
            contact_id=contact_id
        )

        return result

    # ===================================================================
    # HEALTH SCORES API
    # ===================================================================

    async def get_health_score(self, company_id: str) -> Dict[str, Any]:
        """
        Get company health score with component breakdown.

        Args:
            company_id: Company ID

        Returns:
            Health score with components and trend

        Example:
            >>> health = await catalyst.get_health_score("comp_123")
            >>> print(f"Overall: {health['score']}")
            >>> for component in health['components']:
            ...     print(f"{component['name']}: {component['score']}")
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/companies/{company_id}/health'
        )

    async def update_health_score(
        self,
        company_id: str,
        component_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Update health score components.

        Args:
            company_id: Company ID
            component_scores: Component scores (e.g., {"product_usage": 85, "support": 90})

        Returns:
            Updated health score

        Example:
            >>> await catalyst.update_health_score(
            ...     company_id="comp_123",
            ...     component_scores={
            ...         "product_usage": 85,
            ...         "support_satisfaction": 90,
            ...         "engagement": 75
            ...     }
            ... )
        """
        data = {'components': component_scores}

        result = await self._make_request(
            method='PUT',
            endpoint=f'/companies/{company_id}/health',
            data=data
        )

        logger.info(
            "catalyst_health_score_updated",
            company_id=company_id
        )

        return result

    async def get_health_history(
        self,
        company_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get health score history.

        Args:
            company_id: Company ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Time series health score data
        """
        params = {}

        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint=f'/companies/{company_id}/health/history',
            params=params
        )

    # ===================================================================
    # TASKS API
    # ===================================================================

    async def list_tasks(
        self,
        company_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List tasks.

        Args:
            company_id: Filter by company ID
            assigned_to: Filter by assigned user ID
            status: Filter by status (open, completed, overdue)
            limit: Max results

        Returns:
            List of tasks

        Example:
            >>> tasks = await catalyst.list_tasks(
            ...     company_id="comp_123",
            ...     status="open"
            ... )
        """
        params = {'limit': limit}

        if company_id:
            params['company_id'] = company_id
        if assigned_to:
            params['assigned_to'] = assigned_to
        if status:
            params['status'] = status

        result = await self._make_request(
            method='GET',
            endpoint='/tasks',
            params=params
        )

        logger.info(
            "catalyst_tasks_listed",
            count=len(result.get('data', [])) if isinstance(result, dict) else 0
        )

        return result

    async def create_task(
        self,
        company_id: str,
        title: str,
        description: Optional[str] = None,
        assigned_to: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Create a task.

        Args:
            company_id: Company ID
            title: Task title
            description: Task description
            assigned_to: Assigned user ID
            due_date: Due date (ISO format)
            priority: Priority level (low, medium, high)

        Returns:
            Created task

        Example:
            >>> task = await catalyst.create_task(
            ...     company_id="comp_123",
            ...     title="Schedule QBR",
            ...     description="Schedule Q4 quarterly business review",
            ...     assigned_to="user_456",
            ...     due_date="2024-12-15T00:00:00Z",
            ...     priority="high"
            ... )
        """
        data = {
            'company_id': company_id,
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
            "catalyst_task_created",
            task_id=result.get('id'),
            company_id=company_id,
            title=title
        )

        return result

    async def update_task(
        self,
        task_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update task fields.

        Args:
            task_id: Task ID
            data: Fields to update

        Returns:
            Updated task data
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/tasks/{task_id}',
            data=data
        )

        logger.info(
            "catalyst_task_updated",
            task_id=task_id
        )

        return result

    async def complete_task(self, task_id: str) -> Dict[str, Any]:
        """
        Mark task as completed.

        Args:
            task_id: Task ID

        Returns:
            Updated task data
        """
        return await self.update_task(
            task_id=task_id,
            data={'status': 'completed'}
        )

    # ===================================================================
    # NOTES API
    # ===================================================================

    async def list_notes(
        self,
        company_id: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List notes for a company.

        Args:
            company_id: Company ID
            limit: Max results

        Returns:
            List of notes
        """
        params = {
            'company_id': company_id,
            'limit': limit
        }

        result = await self._make_request(
            method='GET',
            endpoint='/notes',
            params=params
        )

        logger.info(
            "catalyst_notes_listed",
            company_id=company_id,
            count=len(result.get('data', [])) if isinstance(result, dict) else 0
        )

        return result

    async def create_note(
        self,
        company_id: str,
        content: str,
        author_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a note.

        Args:
            company_id: Company ID
            content: Note content
            author_id: Author user ID

        Returns:
            Created note

        Example:
            >>> note = await catalyst.create_note(
            ...     company_id="comp_123",
            ...     content="Great call with the team. They're excited about new features.",
            ...     author_id="user_456"
            ... )
        """
        data = {
            'company_id': company_id,
            'content': content
        }

        if author_id:
            data['author_id'] = author_id

        result = await self._make_request(
            method='POST',
            endpoint='/notes',
            data=data
        )

        logger.info(
            "catalyst_note_created",
            note_id=result.get('id'),
            company_id=company_id
        )

        return result

    # ===================================================================
    # PLAYBOOKS API
    # ===================================================================

    async def list_playbooks(self) -> List[Dict[str, Any]]:
        """
        List available playbooks.

        Returns:
            List of playbooks

        Example:
            >>> playbooks = await catalyst.list_playbooks()
            >>> for playbook in playbooks:
            ...     print(f"{playbook['name']}: {playbook['trigger']}")
        """
        result = await self._make_request(
            method='GET',
            endpoint='/playbooks'
        )

        return result if isinstance(result, list) else []

    async def trigger_playbook(
        self,
        playbook_id: str,
        company_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger a playbook for a company.

        Args:
            playbook_id: Playbook ID
            company_id: Company ID
            context: Additional context data

        Returns:
            Playbook execution result

        Example:
            >>> await catalyst.trigger_playbook(
            ...     playbook_id="pb_onboarding",
            ...     company_id="comp_123",
            ...     context={"plan": "Enterprise"}
            ... )
        """
        data = {
            'company_id': company_id,
            'context': context or {}
        }

        result = await self._make_request(
            method='POST',
            endpoint=f'/playbooks/{playbook_id}/trigger',
            data=data
        )

        logger.info(
            "catalyst_playbook_triggered",
            playbook_id=playbook_id,
            company_id=company_id
        )

        return result

    # ===================================================================
    # SEGMENTS API
    # ===================================================================

    async def list_segments(self) -> List[Dict[str, Any]]:
        """
        List customer segments.

        Returns:
            List of segments with criteria

        Example:
            >>> segments = await catalyst.list_segments()
            >>> for segment in segments:
            ...     print(f"{segment['name']}: {segment['company_count']}")
        """
        result = await self._make_request(
            method='GET',
            endpoint='/segments'
        )

        return result if isinstance(result, list) else []

    async def create_segment(
        self,
        name: str,
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a customer segment.

        Args:
            name: Segment name
            criteria: Segment criteria and filters

        Returns:
            Created segment

        Example:
            >>> segment = await catalyst.create_segment(
            ...     name="At-Risk Enterprise Accounts",
            ...     criteria={
            ...         "plan": "Enterprise",
            ...         "health_score": {"max": 60},
            ...         "arr": {"min": 100000}
            ...     }
            ... )
        """
        data = {
            'name': name,
            'criteria': criteria
        }

        result = await self._make_request(
            method='POST',
            endpoint='/segments',
            data=data
        )

        logger.info(
            "catalyst_segment_created",
            segment_id=result.get('id'),
            name=name
        )

        return result

    async def get_segment_companies(
        self,
        segment_id: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get companies in a segment.

        Args:
            segment_id: Segment ID
            limit: Max results

        Returns:
            List of companies in segment
        """
        return await self.list_companies(
            segment_id=segment_id,
            limit=limit
        )

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("catalyst_session_closed")
