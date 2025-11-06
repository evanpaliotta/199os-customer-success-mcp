"""
Help Scout Integration
Priority Score: 13
ICP Adoption: 30-40% of companies using email-based support

Customer support platform focused on email/conversations:
- Conversations and Threads
- Customers
- Mailboxes
- Tags and Workflows
- Reports and Analytics
- Teams and Users
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from .auth.oauth2_base import OAuth2Integration
from .base import ConnectionTestResult, IntegrationStatus, ValidationError, APIError

logger = structlog.get_logger(__name__)


class HelpScoutIntegration(OAuth2Integration):
    """
    Help Scout OAuth2 integration for customer support operations.

    Authentication:
    - OAuth2 with authorization code flow
    - Requires: client_id, client_secret
    - Access token format: Bearer token

    Rate Limits:
    - 400 requests per minute per app
    - 200 requests per 10 seconds per app

    Documentation: https://developer.helpscout.com/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ):
        """
        Initialize Help Scout integration.

        Args:
            credentials: OAuth2 credentials
                - client_id: Help Scout OAuth client ID
                - client_secret: Help Scout OAuth client secret
                - access_token: Current access token (optional)
                - refresh_token: Refresh token (optional)
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="helpscout",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        logger.info(
            "helpscout_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    def get_oauth_config(self) -> Dict[str, Any]:
        """Get Help Scout OAuth2 configuration."""
        return {
            'auth_url': 'https://secure.helpscout.net/authentication/authorizeClientApplication',
            'token_url': 'https://api.helpscout.net/v2/oauth2/token',
            'api_base_url': 'https://api.helpscout.net/v2',
            'scopes': []  # Help Scout doesn't use scopes
        }

    async def test_connection(self) -> ConnectionTestResult:
        """Test connection to Help Scout API."""
        try:
            start_time = datetime.now()

            # Test with mailboxes endpoint
            response = await self._make_request(
                method='GET',
                endpoint='/mailboxes'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            mailboxes = response.get('_embedded', {}).get('mailboxes', [])
            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Help Scout",
                response_time_ms=duration_ms,
                metadata={
                    'mailboxes_count': len(mailboxes),
                    'integration_name': 'helpscout'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Help Scout connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # CONVERSATIONS API
    # ===================================================================

    async def create_conversation(
        self,
        mailbox_id: int,
        subject: str,
        customer_email: str,
        thread_body: str,
        thread_type: str = "customer",
        status: str = "active",
        tags: Optional[List[str]] = None,
        assigned_to: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new conversation.

        Args:
            mailbox_id: Mailbox ID
            subject: Conversation subject
            customer_email: Customer email address
            thread_body: Initial thread body (HTML)
            thread_type: Thread type (customer, message, note)
            status: Conversation status (active, pending, closed)
            tags: List of tags
            assigned_to: User ID to assign to

        Returns:
            Created conversation data

        Example:
            >>> convo = await helpscout.create_conversation(
            ...     mailbox_id=12345,
            ...     subject="Need help with account",
            ...     customer_email="user@example.com",
            ...     thread_body="<p>How do I reset my password?</p>",
            ...     tags=["account", "password"]
            ... )
        """
        conversation_data = {
            'subject': subject,
            'mailboxId': mailbox_id,
            'type': 'email',
            'status': status,
            'customer': {
                'email': customer_email
            },
            'threads': [
                {
                    'type': thread_type,
                    'customer': {
                        'email': customer_email
                    },
                    'text': thread_body
                }
            ]
        }

        if tags:
            conversation_data['tags'] = tags
        if assigned_to:
            conversation_data['assignTo'] = assigned_to

        result = await self._make_request(
            method='POST',
            endpoint='/conversations',
            data=conversation_data
        )

        # Extract conversation ID from Location header
        conversation_id = result.get('id') or result.get('resourceId')

        logger.info(
            "helpscout_conversation_created",
            conversation_id=conversation_id,
            subject=subject
        )

        return {'id': conversation_id, 'status': 'created'}

    async def get_conversation(self, conversation_id: int) -> Dict[str, Any]:
        """
        Get conversation by ID.

        Args:
            conversation_id: Help Scout conversation ID

        Returns:
            Conversation data
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/conversations/{conversation_id}'
        )

    async def list_conversations(
        self,
        mailbox_id: Optional[int] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        assigned_to: Optional[int] = None,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        List conversations with filters.

        Args:
            mailbox_id: Filter by mailbox
            status: Filter by status (active, pending, closed, spam)
            tag: Filter by tag
            assigned_to: Filter by assigned user ID
            page: Page number

        Returns:
            Paginated conversation results
        """
        params = {'page': page}

        if mailbox_id:
            params['mailbox'] = mailbox_id
        if status:
            params['status'] = status
        if tag:
            params['tag'] = tag
        if assigned_to:
            params['assignedTo'] = assigned_to

        return await self._make_request(
            method='GET',
            endpoint='/conversations',
            params=params
        )

    async def update_conversation(
        self,
        conversation_id: int,
        status: Optional[str] = None,
        assigned_to: Optional[int] = None,
        tags: Optional[List[str]] = None,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update conversation.

        Args:
            conversation_id: Help Scout conversation ID
            status: New status (active, pending, closed)
            assigned_to: User ID to assign to
            tags: Tags to set
            subject: New subject

        Returns:
            Update confirmation
        """
        update_data = {}

        if status:
            update_data['status'] = status
        if assigned_to:
            update_data['assignTo'] = assigned_to
        if tags:
            update_data['tags'] = tags
        if subject:
            update_data['subject'] = subject

        result = await self._make_request(
            method='PATCH',
            endpoint=f'/conversations/{conversation_id}',
            data=update_data
        )

        logger.info(
            "helpscout_conversation_updated",
            conversation_id=conversation_id,
            status=status
        )

        return result

    # ===================================================================
    # THREADS API
    # ===================================================================

    async def create_thread(
        self,
        conversation_id: int,
        thread_type: str,
        text: str,
        customer_email: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create thread (reply/note) in conversation.

        Args:
            conversation_id: Help Scout conversation ID
            thread_type: Thread type (customer, message, note, reply)
            text: Thread body (HTML)
            customer_email: Customer email (for customer threads)
            user_id: User ID (for agent threads)

        Returns:
            Created thread data

        Example:
            >>> # Add agent reply
            >>> thread = await helpscout.create_thread(
            ...     conversation_id=12345,
            ...     thread_type="reply",
            ...     text="<p>Thanks for contacting us!</p>",
            ...     user_id=67890
            ... )
        """
        thread_data = {
            'type': thread_type,
            'text': text
        }

        if customer_email:
            thread_data['customer'] = {'email': customer_email}
        if user_id:
            thread_data['user'] = user_id

        result = await self._make_request(
            method='POST',
            endpoint=f'/conversations/{conversation_id}/threads',
            data=thread_data
        )

        logger.info(
            "helpscout_thread_created",
            conversation_id=conversation_id,
            thread_type=thread_type
        )

        return result

    async def list_threads(
        self,
        conversation_id: int
    ) -> List[Dict[str, Any]]:
        """
        List all threads in conversation.

        Args:
            conversation_id: Help Scout conversation ID

        Returns:
            List of threads
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/conversations/{conversation_id}/threads'
        )

        return result.get('_embedded', {}).get('threads', [])

    # ===================================================================
    # CUSTOMERS API
    # ===================================================================

    async def create_customer(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: Optional[str] = None,
        organization: Optional[str] = None,
        job_title: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a customer.

        Args:
            first_name: First name
            last_name: Last name
            email: Email address
            phone: Phone number
            organization: Organization/company name
            job_title: Job title
            properties: Custom properties

        Returns:
            Created customer data
        """
        customer_data = {
            'firstName': first_name,
            'lastName': last_name,
            'emails': [{'value': email, 'type': 'work'}]
        }

        if phone:
            customer_data['phones'] = [{'value': phone, 'type': 'work'}]
        if organization:
            customer_data['organization'] = organization
        if job_title:
            customer_data['jobTitle'] = job_title
        if properties:
            customer_data['properties'] = properties

        result = await self._make_request(
            method='POST',
            endpoint='/customers',
            data=customer_data
        )

        customer_id = result.get('id') or result.get('resourceId')

        logger.info(
            "helpscout_customer_created",
            customer_id=customer_id,
            email=email
        )

        return {'id': customer_id}

    async def get_customer(self, customer_id: int) -> Dict[str, Any]:
        """Get customer by ID."""
        return await self._make_request(
            method='GET',
            endpoint=f'/customers/{customer_id}'
        )

    async def list_customers(
        self,
        email: Optional[str] = None,
        mailbox_id: Optional[int] = None,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        List/search customers.

        Args:
            email: Filter by email
            mailbox_id: Filter by mailbox
            page: Page number

        Returns:
            Paginated customer results
        """
        params = {'page': page}

        if email:
            params['email'] = email
        if mailbox_id:
            params['mailbox'] = mailbox_id

        return await self._make_request(
            method='GET',
            endpoint='/customers',
            params=params
        )

    async def update_customer(
        self,
        customer_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        organization: Optional[str] = None,
        job_title: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update customer.

        Args:
            customer_id: Help Scout customer ID
            first_name: First name
            last_name: Last name
            organization: Organization name
            job_title: Job title
            properties: Custom properties

        Returns:
            Update confirmation
        """
        update_data = {}

        if first_name:
            update_data['firstName'] = first_name
        if last_name:
            update_data['lastName'] = last_name
        if organization:
            update_data['organization'] = organization
        if job_title:
            update_data['jobTitle'] = job_title
        if properties:
            update_data['properties'] = properties

        result = await self._make_request(
            method='PATCH',
            endpoint=f'/customers/{customer_id}',
            data=update_data
        )

        logger.info(
            "helpscout_customer_updated",
            customer_id=customer_id
        )

        return result

    # ===================================================================
    # MAILBOXES API
    # ===================================================================

    async def list_mailboxes(self) -> List[Dict[str, Any]]:
        """
        List all mailboxes.

        Returns:
            List of mailboxes
        """
        result = await self._make_request(
            method='GET',
            endpoint='/mailboxes'
        )

        return result.get('_embedded', {}).get('mailboxes', [])

    async def get_mailbox(self, mailbox_id: int) -> Dict[str, Any]:
        """Get mailbox by ID."""
        return await self._make_request(
            method='GET',
            endpoint=f'/mailboxes/{mailbox_id}'
        )

    # ===================================================================
    # TAGS API
    # ===================================================================

    async def list_tags(self) -> List[Dict[str, Any]]:
        """
        List all tags.

        Returns:
            List of tags
        """
        result = await self._make_request(
            method='GET',
            endpoint='/tags'
        )

        return result.get('_embedded', {}).get('tags', [])

    # ===================================================================
    # WORKFLOWS API
    # ===================================================================

    async def list_workflows(
        self,
        mailbox_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List workflows.

        Args:
            mailbox_id: Filter by mailbox (optional)

        Returns:
            List of workflows
        """
        params = {}
        if mailbox_id:
            params['mailboxId'] = mailbox_id

        result = await self._make_request(
            method='GET',
            endpoint='/workflows',
            params=params
        )

        return result.get('_embedded', {}).get('workflows', [])

    async def run_workflow(
        self,
        workflow_id: int,
        conversation_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Run workflow on conversations.

        Args:
            workflow_id: Workflow ID
            conversation_ids: List of conversation IDs

        Returns:
            Execution result
        """
        result = await self._make_request(
            method='POST',
            endpoint=f'/workflows/{workflow_id}/run',
            data={'conversationIds': conversation_ids}
        )

        logger.info(
            "helpscout_workflow_executed",
            workflow_id=workflow_id,
            conversation_count=len(conversation_ids)
        )

        return result

    # ===================================================================
    # REPORTS API
    # ===================================================================

    async def get_company_report(
        self,
        start_date: str,
        end_date: str,
        mailboxes: Optional[List[int]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get company-wide report.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            mailboxes: Filter by mailbox IDs
            tags: Filter by tags

        Returns:
            Report data
        """
        params = {
            'start': start_date,
            'end': end_date
        }

        if mailboxes:
            params['mailboxes'] = ','.join(map(str, mailboxes))
        if tags:
            params['tags'] = ','.join(tags)

        return await self._make_request(
            method='GET',
            endpoint='/reports/company',
            params=params
        )

    async def get_conversations_report(
        self,
        start_date: str,
        end_date: str,
        mailboxes: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get conversations report.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            mailboxes: Filter by mailbox IDs

        Returns:
            Conversations report data
        """
        params = {
            'start': start_date,
            'end': end_date
        }

        if mailboxes:
            params['mailboxes'] = ','.join(map(str, mailboxes))

        return await self._make_request(
            method='GET',
            endpoint='/reports/conversations',
            params=params
        )

    async def get_happiness_report(
        self,
        start_date: str,
        end_date: str,
        mailboxes: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get happiness (CSAT) report.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            mailboxes: Filter by mailbox IDs

        Returns:
            Happiness report data with ratings
        """
        params = {
            'start': start_date,
            'end': end_date
        }

        if mailboxes:
            params['mailboxes'] = ','.join(map(str, mailboxes))

        return await self._make_request(
            method='GET',
            endpoint='/reports/happiness',
            params=params
        )
