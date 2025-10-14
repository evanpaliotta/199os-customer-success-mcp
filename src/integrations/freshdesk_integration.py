"""
Freshdesk Integration
Priority Score: 14
ICP Adoption: 50-60% of SMB companies using support/ticketing

Popular customer support platform providing:
- Tickets and Conversations
- Contacts and Companies
- Groups and Agents
- Custom Ticket Fields
- Time Entries
- Satisfaction Surveys (CSAT)
- SLA Management
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


class FreshdeskIntegration(BaseIntegration):
    """
    Freshdesk API integration with API key authentication.

    Authentication:
    - API Key in Authorization header (Basic Auth)
    - Format: base64(api_key:X)

    Rate Limits:
    - Estate Plan: 3000 requests/hour
    - Forest Plan: 5000 requests/hour
    - Garden Plan: Unlimited with throttling

    Documentation: https://developers.freshdesk.com/api/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ):
        """
        Initialize Freshdesk integration.

        Args:
            credentials: Freshdesk credentials
                - api_key: Freshdesk API key
                - domain: Freshdesk domain (e.g., "company.freshdesk.com")
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="freshdesk",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        self.domain = credentials.get('domain', '')

        if not self.api_key:
            raise ValidationError("Freshdesk api_key is required")
        if not self.domain:
            raise ValidationError("Freshdesk domain is required")

        # Remove protocol if present
        self.domain = self.domain.replace('https://', '').replace('http://', '')
        self.base_url = f"https://{self.domain}/api/v2"

        logger.info(
            "freshdesk_initialized",
            domain=self.domain,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Freshdesk (API key validation)."""
        try:
            import aiohttp
            import base64

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            # Create Basic Auth header
            auth_string = f"{self.api_key}:X"
            self.auth_header = base64.b64encode(auth_string.encode()).decode()

            logger.info("freshdesk_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Freshdesk authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Freshdesk API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            'Authorization': f'Basic {self.auth_header}',
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
                        f"Freshdesk API error ({response.status}): {error_text}",
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
        """Test connection to Freshdesk API."""
        try:
            start_time = datetime.now()

            # Test with agents endpoint
            response = await self._make_request(
                method='GET',
                endpoint='/agents/me'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Freshdesk",
                response_time_ms=duration_ms,
                metadata={
                    'agent_id': response.get('id'),
                    'email': response.get('email'),
                    'domain': self.domain,
                    'integration_name': 'freshdesk'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Freshdesk connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # TICKETS API
    # ===================================================================

    async def create_ticket(
        self,
        subject: str,
        description: str,
        email: str,
        priority: int = 1,
        status: int = 2,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        type: Optional[str] = None,
        group_id: Optional[int] = None,
        responder_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new ticket.

        Args:
            subject: Ticket subject
            description: Ticket description (HTML or plain text)
            email: Requester email
            priority: Priority (1=Low, 2=Medium, 3=High, 4=Urgent)
            status: Status (2=Open, 3=Pending, 4=Resolved, 5=Closed)
            tags: List of tags
            custom_fields: Custom field values
            type: Ticket type
            group_id: Group ID to assign
            responder_id: Agent ID to assign

        Returns:
            Created ticket data

        Example:
            >>> ticket = await freshdesk.create_ticket(
            ...     subject="Login issue",
            ...     description="User cannot log in",
            ...     email="user@example.com",
            ...     priority=3,
            ...     tags=["login", "urgent"]
            ... )
        """
        ticket_data = {
            'subject': subject,
            'description': description,
            'email': email,
            'priority': priority,
            'status': status
        }

        if tags:
            ticket_data['tags'] = tags
        if custom_fields:
            ticket_data['custom_fields'] = custom_fields
        if type:
            ticket_data['type'] = type
        if group_id:
            ticket_data['group_id'] = group_id
        if responder_id:
            ticket_data['responder_id'] = responder_id

        result = await self._make_request(
            method='POST',
            endpoint='/tickets',
            data=ticket_data
        )

        logger.info(
            "freshdesk_ticket_created",
            ticket_id=result.get('id'),
            subject=subject,
            priority=priority
        )

        return result

    async def get_ticket(self, ticket_id: int) -> Dict[str, Any]:
        """
        Get ticket by ID.

        Args:
            ticket_id: Freshdesk ticket ID

        Returns:
            Ticket data
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/tickets/{ticket_id}'
        )

    async def update_ticket(
        self,
        ticket_id: int,
        status: Optional[int] = None,
        priority: Optional[int] = None,
        responder_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update ticket.

        Args:
            ticket_id: Freshdesk ticket ID
            status: New status (2=Open, 3=Pending, 4=Resolved, 5=Closed)
            priority: New priority (1=Low, 2=Medium, 3=High, 4=Urgent)
            responder_id: Agent ID to assign
            tags: Tags to add
            custom_fields: Custom field updates

        Returns:
            Updated ticket data
        """
        update_data = {}

        if status is not None:
            update_data['status'] = status
        if priority is not None:
            update_data['priority'] = priority
        if responder_id is not None:
            update_data['responder_id'] = responder_id
        if tags:
            update_data['tags'] = tags
        if custom_fields:
            update_data['custom_fields'] = custom_fields

        result = await self._make_request(
            method='PUT',
            endpoint=f'/tickets/{ticket_id}',
            data=update_data
        )

        logger.info(
            "freshdesk_ticket_updated",
            ticket_id=ticket_id,
            status=status
        )

        return result

    async def list_tickets(
        self,
        filter: Optional[str] = None,
        updated_since: Optional[str] = None,
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        List tickets with filters.

        Args:
            filter: Predefined filter (new_and_my_open, watching, spam, deleted)
            updated_since: ISO timestamp to filter by update time
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            List of tickets
        """
        params = {
            'page': page,
            'per_page': per_page
        }

        if filter:
            params['filter'] = filter
        if updated_since:
            params['updated_since'] = updated_since

        endpoint = '/tickets'
        if filter:
            endpoint = f'/tickets?filter={filter}'

        return await self._make_request(
            method='GET',
            endpoint=endpoint,
            params=params
        )

    # ===================================================================
    # CONVERSATIONS API
    # ===================================================================

    async def add_note(
        self,
        ticket_id: int,
        body: str,
        private: bool = True,
        notify_emails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Add note/reply to ticket.

        Args:
            ticket_id: Freshdesk ticket ID
            body: Note body (HTML or text)
            private: Whether note is private (internal)
            notify_emails: Emails to notify

        Returns:
            Created conversation/note data
        """
        note_data = {
            'body': body,
            'private': private
        }

        if notify_emails:
            note_data['notify_emails'] = notify_emails

        result = await self._make_request(
            method='POST',
            endpoint=f'/tickets/{ticket_id}/notes',
            data=note_data
        )

        logger.info(
            "freshdesk_note_added",
            ticket_id=ticket_id,
            private=private
        )

        return result

    async def add_reply(
        self,
        ticket_id: int,
        body: str,
        from_email: Optional[str] = None,
        cc_emails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Add public reply to ticket.

        Args:
            ticket_id: Freshdesk ticket ID
            body: Reply body (HTML or text)
            from_email: From email address
            cc_emails: CC email addresses

        Returns:
            Created reply data
        """
        reply_data = {'body': body}

        if from_email:
            reply_data['from_email'] = from_email
        if cc_emails:
            reply_data['cc_emails'] = cc_emails

        result = await self._make_request(
            method='POST',
            endpoint=f'/tickets/{ticket_id}/reply',
            data=reply_data
        )

        logger.info(
            "freshdesk_reply_added",
            ticket_id=ticket_id
        )

        return result

    async def list_conversations(
        self,
        ticket_id: int
    ) -> List[Dict[str, Any]]:
        """
        List all conversations for a ticket.

        Args:
            ticket_id: Freshdesk ticket ID

        Returns:
            List of conversations
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/tickets/{ticket_id}/conversations'
        )

    # ===================================================================
    # CONTACTS API
    # ===================================================================

    async def create_contact(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        mobile: Optional[str] = None,
        company_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a contact.

        Args:
            name: Contact name
            email: Contact email
            phone: Phone number
            mobile: Mobile number
            company_id: Company ID
            tags: Contact tags
            custom_fields: Custom field values

        Returns:
            Created contact data
        """
        contact_data = {'name': name}

        if email:
            contact_data['email'] = email
        if phone:
            contact_data['phone'] = phone
        if mobile:
            contact_data['mobile'] = mobile
        if company_id:
            contact_data['company_id'] = company_id
        if tags:
            contact_data['tags'] = tags
        if custom_fields:
            contact_data['custom_fields'] = custom_fields

        result = await self._make_request(
            method='POST',
            endpoint='/contacts',
            data=contact_data
        )

        logger.info(
            "freshdesk_contact_created",
            contact_id=result.get('id'),
            email=email
        )

        return result

    async def get_contact(self, contact_id: int) -> Dict[str, Any]:
        """Get contact by ID."""
        return await self._make_request(
            method='GET',
            endpoint=f'/contacts/{contact_id}'
        )

    async def list_contacts(
        self,
        email: Optional[str] = None,
        mobile: Optional[str] = None,
        phone: Optional[str] = None,
        company_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List/search contacts.

        Args:
            email: Filter by email
            mobile: Filter by mobile
            phone: Filter by phone
            company_id: Filter by company

        Returns:
            List of contacts
        """
        params = {}
        if email:
            params['email'] = email
        if mobile:
            params['mobile'] = mobile
        if phone:
            params['phone'] = phone
        if company_id:
            params['company_id'] = company_id

        return await self._make_request(
            method='GET',
            endpoint='/contacts',
            params=params
        )

    # ===================================================================
    # COMPANIES API
    # ===================================================================

    async def create_company(
        self,
        name: str,
        description: Optional[str] = None,
        domains: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a company.

        Args:
            name: Company name
            description: Company description
            domains: Associated domains
            custom_fields: Custom field values

        Returns:
            Created company data
        """
        company_data = {'name': name}

        if description:
            company_data['description'] = description
        if domains:
            company_data['domains'] = domains
        if custom_fields:
            company_data['custom_fields'] = custom_fields

        result = await self._make_request(
            method='POST',
            endpoint='/companies',
            data=company_data
        )

        logger.info(
            "freshdesk_company_created",
            company_id=result.get('id'),
            name=name
        )

        return result

    async def get_company(self, company_id: int) -> Dict[str, Any]:
        """Get company by ID."""
        return await self._make_request(
            method='GET',
            endpoint=f'/companies/{company_id}'
        )

    # ===================================================================
    # GROUPS API
    # ===================================================================

    async def list_groups(self) -> List[Dict[str, Any]]:
        """
        List all agent groups.

        Returns:
            List of groups
        """
        return await self._make_request(
            method='GET',
            endpoint='/groups'
        )

    async def get_group(self, group_id: int) -> Dict[str, Any]:
        """Get group by ID."""
        return await self._make_request(
            method='GET',
            endpoint=f'/groups/{group_id}'
        )

    # ===================================================================
    # AGENTS API
    # ===================================================================

    async def list_agents(
        self,
        email: Optional[str] = None,
        mobile: Optional[str] = None,
        phone: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List agents.

        Args:
            email: Filter by email
            mobile: Filter by mobile
            phone: Filter by phone

        Returns:
            List of agents
        """
        params = {}
        if email:
            params['email'] = email
        if mobile:
            params['mobile'] = mobile
        if phone:
            params['phone'] = phone

        return await self._make_request(
            method='GET',
            endpoint='/agents',
            params=params
        )

    async def get_agent(self, agent_id: int) -> Dict[str, Any]:
        """Get agent by ID."""
        return await self._make_request(
            method='GET',
            endpoint=f'/agents/{agent_id}'
        )

    # ===================================================================
    # TIME ENTRIES API
    # ===================================================================

    async def create_time_entry(
        self,
        ticket_id: int,
        time_spent: str,
        note: Optional[str] = None,
        billable: bool = True,
        agent_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create time entry on ticket.

        Args:
            ticket_id: Freshdesk ticket ID
            time_spent: Time in HH:MM format (e.g., "01:30")
            note: Time entry note
            billable: Whether time is billable
            agent_id: Agent ID (defaults to current agent)

        Returns:
            Created time entry data
        """
        time_data = {
            'time_spent': time_spent,
            'billable': billable
        }

        if note:
            time_data['note'] = note
        if agent_id:
            time_data['agent_id'] = agent_id

        result = await self._make_request(
            method='POST',
            endpoint=f'/tickets/{ticket_id}/time_entries',
            data=time_data
        )

        logger.info(
            "freshdesk_time_entry_created",
            ticket_id=ticket_id,
            time_spent=time_spent
        )

        return result

    async def list_time_entries(
        self,
        ticket_id: int
    ) -> List[Dict[str, Any]]:
        """
        List time entries for ticket.

        Args:
            ticket_id: Freshdesk ticket ID

        Returns:
            List of time entries
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/tickets/{ticket_id}/time_entries'
        )

    # ===================================================================
    # SATISFACTION SURVEYS API
    # ===================================================================

    async def get_satisfaction_ratings(
        self,
        created_since: Optional[str] = None,
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get satisfaction survey ratings.

        Args:
            created_since: ISO timestamp to filter by creation time
            page: Page number
            per_page: Results per page

        Returns:
            List of satisfaction ratings
        """
        params = {
            'page': page,
            'per_page': per_page
        }

        if created_since:
            params['created_since'] = created_since

        return await self._make_request(
            method='GET',
            endpoint='/surveys/satisfaction_ratings',
            params=params
        )

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("freshdesk_session_closed")
