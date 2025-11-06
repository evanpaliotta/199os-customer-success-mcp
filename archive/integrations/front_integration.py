"""
Front Integration
Priority Score: 13
ICP Adoption: 25-35% of companies using shared inbox/team collaboration

Modern customer communication platform providing:
- Conversations and Messages
- Contacts
- Inboxes and Channels
- Tags and Comments
- Analytics and Insights
- Team Collaboration
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from .auth.oauth2_base import OAuth2Integration
from .base import ConnectionTestResult, IntegrationStatus, ValidationError, APIError

logger = structlog.get_logger(__name__)


class FrontIntegration(OAuth2Integration):
    """
    Front OAuth2 integration for team inbox and customer communication.

    Authentication:
    - OAuth2 with authorization code flow
    - Requires: client_id, client_secret
    - Access token format: Bearer token

    Rate Limits:
    - 600 requests per minute
    - 50 requests per second

    Documentation: https://dev.frontapp.com/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ):
        """
        Initialize Front integration.

        Args:
            credentials: OAuth2 credentials
                - client_id: Front OAuth client ID
                - client_secret: Front OAuth client secret
                - access_token: Current access token (optional)
                - refresh_token: Refresh token (optional)
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="front",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        logger.info(
            "front_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    def get_oauth_config(self) -> Dict[str, Any]:
        """Get Front OAuth2 configuration."""
        return {
            'auth_url': 'https://app.frontapp.com/oauth/authorize',
            'token_url': 'https://app.frontapp.com/oauth/token',
            'api_base_url': 'https://api2.frontapp.com',
            'scopes': ['shared:inbox', 'private:messages']
        }

    async def test_connection(self) -> ConnectionTestResult:
        """Test connection to Front API."""
        try:
            start_time = datetime.now()

            # Test with teammates endpoint
            response = await self._make_request(
                method='GET',
                endpoint='/teammates'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            teammates = response.get('_results', [])
            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Front",
                response_time_ms=duration_ms,
                metadata={
                    'teammates_count': len(teammates),
                    'integration_name': 'front'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Front connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # CONVERSATIONS API
    # ===================================================================

    async def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation by ID.

        Args:
            conversation_id: Front conversation ID

        Returns:
            Conversation data
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/conversations/{conversation_id}'
        )

    async def list_conversations(
        self,
        inbox_id: Optional[str] = None,
        tag_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List conversations with filters.

        Args:
            inbox_id: Filter by inbox ID
            tag_id: Filter by tag ID
            status: Filter by status (archived, deleted, unassigned, assigned)
            limit: Results limit (max 100)

        Returns:
            Paginated conversation results
        """
        params = {'limit': limit}

        endpoint = '/conversations'
        if inbox_id:
            endpoint = f'/inboxes/{inbox_id}/conversations'
        elif tag_id:
            endpoint = f'/tags/{tag_id}/conversations'

        if status:
            params['q[statuses][]'] = status

        return await self._make_request(
            method='GET',
            endpoint=endpoint,
            params=params
        )

    async def update_conversation(
        self,
        conversation_id: str,
        assignee_id: Optional[str] = None,
        inbox_id: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update conversation.

        Args:
            conversation_id: Front conversation ID
            assignee_id: Teammate ID to assign
            inbox_id: Inbox ID to move to
            status: Status (archived, deleted, open)
            tags: Tag names to add

        Returns:
            Update confirmation
        """
        update_data = {}

        if assignee_id:
            update_data['assignee_id'] = assignee_id
        if inbox_id:
            update_data['inbox_id'] = inbox_id
        if status:
            update_data['status'] = status
        if tags:
            update_data['tags'] = tags

        result = await self._make_request(
            method='PATCH',
            endpoint=f'/conversations/{conversation_id}',
            data=update_data
        )

        logger.info(
            "front_conversation_updated",
            conversation_id=conversation_id,
            status=status
        )

        return result

    # ===================================================================
    # MESSAGES API
    # ===================================================================

    async def send_message(
        self,
        channel_id: str,
        to: List[str],
        subject: Optional[str] = None,
        body: str = "",
        author_id: Optional[str] = None,
        sender_name: Optional[str] = None,
        attachments: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Send a new message.

        Args:
            channel_id: Channel ID to send from
            to: List of recipient email addresses
            subject: Email subject (for email channels)
            body: Message body (text or HTML)
            author_id: Teammate ID (author)
            sender_name: Sender name
            attachments: List of attachments [{filename: "file.pdf", url: "..."}]

        Returns:
            Created message data

        Example:
            >>> msg = await front.send_message(
            ...     channel_id="cha_123",
            ...     to=["customer@example.com"],
            ...     subject="Re: Your inquiry",
            ...     body="Thanks for reaching out!",
            ...     author_id="tea_456"
            ... )
        """
        message_data = {
            'to': to,
            'body': body
        }

        if subject:
            message_data['subject'] = subject
        if author_id:
            message_data['author_id'] = author_id
        if sender_name:
            message_data['sender_name'] = sender_name
        if attachments:
            message_data['attachments'] = attachments

        result = await self._make_request(
            method='POST',
            endpoint=f'/channels/{channel_id}/messages',
            data=message_data
        )

        logger.info(
            "front_message_sent",
            channel_id=channel_id,
            recipients=len(to)
        )

        return result

    async def reply_to_conversation(
        self,
        conversation_id: str,
        body: str,
        author_id: str,
        message_type: str = "email",
        channel_id: Optional[str] = None,
        attachments: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Reply to conversation.

        Args:
            conversation_id: Front conversation ID
            body: Reply body (text or HTML)
            author_id: Teammate ID (author)
            message_type: Message type (email, tweet, sms, etc.)
            channel_id: Channel ID to reply from
            attachments: List of attachments

        Returns:
            Created reply data
        """
        reply_data = {
            'body': body,
            'author_id': author_id,
            'type': message_type
        }

        if channel_id:
            reply_data['channel_id'] = channel_id
        if attachments:
            reply_data['attachments'] = attachments

        result = await self._make_request(
            method='POST',
            endpoint=f'/conversations/{conversation_id}/messages',
            data=reply_data
        )

        logger.info(
            "front_reply_sent",
            conversation_id=conversation_id
        )

        return result

    async def list_messages(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List messages in conversation.

        Args:
            conversation_id: Front conversation ID
            limit: Results limit

        Returns:
            List of messages
        """
        params = {'limit': limit}

        return await self._make_request(
            method='GET',
            endpoint=f'/conversations/{conversation_id}/messages',
            params=params
        )

    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get message by ID."""
        return await self._make_request(
            method='GET',
            endpoint=f'/messages/{message_id}'
        )

    # ===================================================================
    # CONTACTS API
    # ===================================================================

    async def create_contact(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        handles: Optional[List[Dict[str, str]]] = None,
        group_names: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a contact.

        Args:
            name: Contact name
            description: Contact description/notes
            handles: Contact handles [{"handle": "email@example.com", "source": "email"}]
            group_names: Contact group names
            custom_fields: Custom field values

        Returns:
            Created contact data

        Example:
            >>> contact = await front.create_contact(
            ...     name="John Doe",
            ...     handles=[{"handle": "john@example.com", "source": "email"}],
            ...     group_names=["Customers"],
            ...     custom_fields={"company": "Acme Corp"}
            ... )
        """
        contact_data = {}

        if name:
            contact_data['name'] = name
        if description:
            contact_data['description'] = description
        if handles:
            contact_data['handles'] = handles
        if group_names:
            contact_data['group_names'] = group_names
        if custom_fields:
            contact_data['custom_fields'] = custom_fields

        result = await self._make_request(
            method='POST',
            endpoint='/contacts',
            data=contact_data
        )

        logger.info(
            "front_contact_created",
            contact_id=result.get('id')
        )

        return result

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Get contact by ID."""
        return await self._make_request(
            method='GET',
            endpoint=f'/contacts/{contact_id}'
        )

    async def list_contacts(
        self,
        page_token: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List contacts.

        Args:
            page_token: Pagination token
            limit: Results limit

        Returns:
            Paginated contact results
        """
        params = {'limit': limit}

        if page_token:
            params['page_token'] = page_token

        return await self._make_request(
            method='GET',
            endpoint='/contacts',
            params=params
        )

    async def update_contact(
        self,
        contact_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update contact.

        Args:
            contact_id: Front contact ID
            name: Contact name
            description: Contact description
            custom_fields: Custom field values

        Returns:
            Update confirmation
        """
        update_data = {}

        if name:
            update_data['name'] = name
        if description:
            update_data['description'] = description
        if custom_fields:
            update_data['custom_fields'] = custom_fields

        result = await self._make_request(
            method='PATCH',
            endpoint=f'/contacts/{contact_id}',
            data=update_data
        )

        logger.info(
            "front_contact_updated",
            contact_id=contact_id
        )

        return result

    # ===================================================================
    # INBOXES API
    # ===================================================================

    async def list_inboxes(self) -> Dict[str, Any]:
        """
        List all inboxes.

        Returns:
            List of inboxes
        """
        return await self._make_request(
            method='GET',
            endpoint='/inboxes'
        )

    async def get_inbox(self, inbox_id: str) -> Dict[str, Any]:
        """Get inbox by ID."""
        return await self._make_request(
            method='GET',
            endpoint=f'/inboxes/{inbox_id}'
        )

    # ===================================================================
    # CHANNELS API
    # ===================================================================

    async def list_channels(self) -> Dict[str, Any]:
        """
        List all channels.

        Returns:
            List of channels
        """
        return await self._make_request(
            method='GET',
            endpoint='/channels'
        )

    async def get_channel(self, channel_id: str) -> Dict[str, Any]:
        """Get channel by ID."""
        return await self._make_request(
            method='GET',
            endpoint=f'/channels/{channel_id}'
        )

    # ===================================================================
    # TAGS API
    # ===================================================================

    async def list_tags(self) -> Dict[str, Any]:
        """
        List all tags.

        Returns:
            List of tags
        """
        return await self._make_request(
            method='GET',
            endpoint='/tags'
        )

    async def create_tag(
        self,
        name: str,
        highlight: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a tag.

        Args:
            name: Tag name
            highlight: Highlight color (grey, pink, red, orange, yellow, green, light-blue, blue, purple)

        Returns:
            Created tag data
        """
        tag_data = {'name': name}

        if highlight:
            tag_data['highlight'] = highlight

        result = await self._make_request(
            method='POST',
            endpoint='/tags',
            data=tag_data
        )

        logger.info(
            "front_tag_created",
            tag_id=result.get('id'),
            name=name
        )

        return result

    # ===================================================================
    # COMMENTS API
    # ===================================================================

    async def add_comment(
        self,
        conversation_id: str,
        body: str,
        author_id: str
    ) -> Dict[str, Any]:
        """
        Add comment to conversation.

        Args:
            conversation_id: Front conversation ID
            body: Comment body
            author_id: Teammate ID (author)

        Returns:
            Created comment data
        """
        comment_data = {
            'body': body,
            'author_id': author_id
        }

        result = await self._make_request(
            method='POST',
            endpoint=f'/conversations/{conversation_id}/comments',
            data=comment_data
        )

        logger.info(
            "front_comment_added",
            conversation_id=conversation_id
        )

        return result

    async def list_comments(
        self,
        conversation_id: str
    ) -> Dict[str, Any]:
        """
        List comments in conversation.

        Args:
            conversation_id: Front conversation ID

        Returns:
            List of comments
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/conversations/{conversation_id}/comments'
        )

    # ===================================================================
    # TEAMMATES API
    # ===================================================================

    async def list_teammates(self) -> Dict[str, Any]:
        """
        List all teammates.

        Returns:
            List of teammates
        """
        return await self._make_request(
            method='GET',
            endpoint='/teammates'
        )

    async def get_teammate(self, teammate_id: str) -> Dict[str, Any]:
        """Get teammate by ID."""
        return await self._make_request(
            method='GET',
            endpoint=f'/teammates/{teammate_id}'
        )

    # ===================================================================
    # ANALYTICS API
    # ===================================================================

    async def get_analytics(
        self,
        start: int,
        end: int,
        metric_type: str = "team",
        inbox_ids: Optional[List[str]] = None,
        tag_ids: Optional[List[str]] = None,
        teammate_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get analytics data.

        Args:
            start: Start timestamp (Unix)
            end: End timestamp (Unix)
            metric_type: Metric type (team, teammate, inbox, tag)
            inbox_ids: Filter by inbox IDs
            tag_ids: Filter by tag IDs
            teammate_ids: Filter by teammate IDs

        Returns:
            Analytics data

        Example:
            >>> analytics = await front.get_analytics(
            ...     start=1609459200,  # 2021-01-01
            ...     end=1640995199,    # 2021-12-31
            ...     metric_type="team"
            ... )
        """
        params = {
            'start': start,
            'end': end,
            'metric_type': metric_type
        }

        if inbox_ids:
            params['inbox_ids'] = inbox_ids
        if tag_ids:
            params['tag_ids'] = tag_ids
        if teammate_ids:
            params['teammate_ids'] = teammate_ids

        return await self._make_request(
            method='GET',
            endpoint='/analytics',
            params=params
        )
