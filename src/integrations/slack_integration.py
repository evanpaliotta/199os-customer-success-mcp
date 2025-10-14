"""
Slack Integration
Priority Score: 18
ICP Adoption: 96% penetration rate

Provides comprehensive Slack operations:
- Messages (Send, Update, Delete)
- Channels (List, Create, Join, Archive)
- Users (List, Get Info)
- Reactions (Add, Remove)
- Files (Upload, Share)
- Webhooks (Incoming webhooks for notifications)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from .auth.oauth2_base import OAuth2Integration
from .base import ConnectionTestResult, IntegrationStatus, ValidationError, APIError

logger = structlog.get_logger(__name__)


class SlackIntegration(OAuth2Integration):
    """
    Slack OAuth2 integration.

    Scopes Required (Bot Token):
    - channels:read
    - channels:write
    - chat:write
    - files:write
    - users:read
    - reactions:write
    - groups:read (for private channels)

    Rate Limits:
    - Tier 1: 1+ request per minute
    - Tier 2: 20+ requests per minute
    - Tier 3: 50+ requests per minute
    - Tier 4: 100+ requests per minute

    Documentation: https://api.slack.com/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 50,
        rate_limit_window: int = 60
    ):
        """
        Initialize Slack integration.

        Args:
            credentials: OAuth2 credentials or webhook URL
                OAuth2 mode:
                    - client_id: Slack app client ID
                    - client_secret: Slack app client secret
                    - access_token: Bot user OAuth token (xoxb-...)
                Webhook mode:
                    - webhook_url: Incoming webhook URL
            rate_limit_calls: Max API calls per window (default: 50)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        # Check if webhook mode
        self.webhook_mode = 'webhook_url' in credentials

        super().__init__(
            integration_name="slack",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.workspace_info: Optional[Dict[str, Any]] = None
        self.bot_user_id: Optional[str] = None

        logger.info(
            "slack_initialized",
            mode="webhook" if self.webhook_mode else "oauth2",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    def get_oauth_config(self) -> Dict[str, Any]:
        """Get Slack OAuth2 configuration."""
        return {
            'auth_url': 'https://slack.com/oauth/v2/authorize',
            'token_url': 'https://slack.com/api/oauth.v2.access',
            'api_base_url': 'https://slack.com/api',
            'scopes': [
                'channels:read',
                'channels:write',
                'chat:write',
                'files:write',
                'users:read',
                'reactions:write',
                'groups:read'
            ]
        }

    async def test_connection(self) -> ConnectionTestResult:
        """Test connection to Slack API."""
        try:
            if self.webhook_mode:
                # For webhook mode, just verify the webhook URL format
                webhook_url = self.credentials.get('webhook_url', '')
                if not webhook_url.startswith('https://hooks.slack.com/services/'):
                    raise ValidationError("Invalid Slack webhook URL format")

                return ConnectionTestResult(
                    success=True,
                    status=IntegrationStatus.CONNECTED,
                    message="Slack webhook URL configured",
                    metadata={
                        'mode': 'webhook',
                        'integration_name': 'slack'
                    }
                )

            # OAuth2 mode - test auth
            start_time = datetime.now()

            response = await self._make_request(
                method='POST',
                endpoint='/auth.test'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Store workspace info
            self.workspace_info = response
            self.bot_user_id = response.get('user_id')

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Slack",
                response_time_ms=duration_ms,
                metadata={
                    'team_id': response.get('team_id'),
                    'team': response.get('team'),
                    'user_id': response.get('user_id'),
                    'bot_id': response.get('bot_id'),
                    'integration_name': 'slack'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Slack connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # MESSAGES API
    # ===================================================================

    async def send_message(
        self,
        channel: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a message to a channel.

        Args:
            channel: Channel ID or name (e.g., "#general" or "C1234567890")
            text: Message text (required if blocks not provided)
            blocks: Block Kit blocks for rich formatting
            thread_ts: Parent message timestamp (for threaded replies)
            **kwargs: Additional options
                - attachments: Legacy attachments
                - unfurl_links: Unfurl links (default: True)
                - unfurl_media: Unfurl media (default: True)

        Returns:
            Message response with timestamp

        Example:
            >>> # Simple text message
            >>> msg = await slack.send_message(
            ...     channel="#sales",
            ...     text="New lead created: John Doe at Acme Corp"
            ... )
            >>>
            >>> # Rich message with blocks
            >>> msg = await slack.send_message(
            ...     channel="C1234567890",
            ...     blocks=[
            ...         {
            ...             "type": "section",
            ...             "text": {
            ...                 "type": "mrkdwn",
            ...                 "text": "*New Deal Alert!*\\nDeal: Q4 Enterprise\\nAmount: $50,000"
            ...             }
            ...         }
            ...     ]
            ... )
        """
        if self.webhook_mode:
            return await self._send_webhook_message(text, blocks)

        if not text and not blocks:
            raise ValidationError("Either 'text' or 'blocks' must be provided")

        data = {
            'channel': channel,
            'text': text,
            'blocks': blocks,
            'thread_ts': thread_ts,
            **kwargs
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        result = await self._make_request(
            method='POST',
            endpoint='/chat.postMessage',
            data=data
        )

        logger.info(
            "slack_message_sent",
            channel=channel,
            ts=result.get('ts')
        )

        return result

    async def _send_webhook_message(
        self,
        text: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send message via webhook (webhook mode only)."""
        import aiohttp

        webhook_url = self.credentials.get('webhook_url')
        if not webhook_url:
            raise ValidationError("No webhook URL configured")

        data = {}
        if text:
            data['text'] = text
        if blocks:
            data['blocks'] = blocks

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=data) as response:
                if response.status == 200:
                    return {'ok': True, 'mode': 'webhook'}
                else:
                    error_text = await response.text()
                    raise APIError(f"Webhook failed ({response.status}): {error_text}", response.status)

    async def update_message(
        self,
        channel: str,
        ts: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing message.

        Args:
            channel: Channel ID
            ts: Message timestamp
            text: New message text
            blocks: New blocks

        Returns:
            Updated message response
        """
        data = {
            'channel': channel,
            'ts': ts,
            'text': text,
            'blocks': blocks
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        result = await self._make_request(
            method='POST',
            endpoint='/chat.update',
            data=data
        )

        logger.info("slack_message_updated", channel=channel, ts=ts)
        return result

    async def delete_message(self, channel: str, ts: str) -> Dict[str, Any]:
        """
        Delete a message.

        Args:
            channel: Channel ID
            ts: Message timestamp

        Returns:
            Deletion response
        """
        data = {
            'channel': channel,
            'ts': ts
        }

        result = await self._make_request(
            method='POST',
            endpoint='/chat.delete',
            data=data
        )

        logger.info("slack_message_deleted", channel=channel, ts=ts)
        return result

    # ===================================================================
    # CHANNELS API
    # ===================================================================

    async def list_channels(
        self,
        exclude_archived: bool = True,
        types: str = "public_channel"
    ) -> Dict[str, Any]:
        """
        List channels.

        Args:
            exclude_archived: Exclude archived channels
            types: Channel types (comma-separated)
                - public_channel
                - private_channel
                - mpim (group messages)
                - im (direct messages)

        Returns:
            List of channels

        Example:
            >>> channels = await slack.list_channels(
            ...     types="public_channel,private_channel"
            ... )
        """
        params = {
            'exclude_archived': exclude_archived,
            'types': types
        }

        return await self._make_request(
            method='GET',
            endpoint='/conversations.list',
            params=params
        )

    async def create_channel(
        self,
        name: str,
        is_private: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new channel.

        Args:
            name: Channel name (lowercase, no spaces)
            is_private: Create private channel

        Returns:
            Created channel data
        """
        data = {
            'name': name,
            'is_private': is_private
        }

        result = await self._make_request(
            method='POST',
            endpoint='/conversations.create',
            data=data
        )

        logger.info(
            "slack_channel_created",
            channel_id=result.get('channel', {}).get('id'),
            name=name
        )

        return result

    async def join_channel(self, channel_id: str) -> Dict[str, Any]:
        """Join a channel."""
        data = {
            'channel': channel_id
        }

        result = await self._make_request(
            method='POST',
            endpoint='/conversations.join',
            data=data
        )

        logger.info("slack_channel_joined", channel_id=channel_id)
        return result

    async def archive_channel(self, channel_id: str) -> Dict[str, Any]:
        """Archive a channel."""
        data = {
            'channel': channel_id
        }

        result = await self._make_request(
            method='POST',
            endpoint='/conversations.archive',
            data=data
        )

        logger.info("slack_channel_archived", channel_id=channel_id)
        return result

    async def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Get channel information."""
        params = {
            'channel': channel_id
        }

        return await self._make_request(
            method='GET',
            endpoint='/conversations.info',
            params=params
        )

    # ===================================================================
    # USERS API
    # ===================================================================

    async def list_users(self) -> Dict[str, Any]:
        """List all users in workspace."""
        return await self._make_request(
            method='GET',
            endpoint='/users.list'
        )

    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information.

        Args:
            user_id: Slack user ID

        Returns:
            User profile data
        """
        params = {
            'user': user_id
        }

        return await self._make_request(
            method='GET',
            endpoint='/users.info',
            params=params
        )

    async def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """
        Look up a user by email.

        Args:
            email: User email address

        Returns:
            User data
        """
        params = {
            'email': email
        }

        return await self._make_request(
            method='GET',
            endpoint='/users.lookupByEmail',
            params=params
        )

    # ===================================================================
    # REACTIONS API
    # ===================================================================

    async def add_reaction(
        self,
        channel: str,
        timestamp: str,
        name: str
    ) -> Dict[str, Any]:
        """
        Add a reaction to a message.

        Args:
            channel: Channel ID
            timestamp: Message timestamp
            name: Emoji name (without colons, e.g., "thumbsup", "eyes")

        Returns:
            Reaction response

        Example:
            >>> await slack.add_reaction(
            ...     channel="C1234567890",
            ...     timestamp="1234567890.123456",
            ...     name="thumbsup"
            ... )
        """
        data = {
            'channel': channel,
            'timestamp': timestamp,
            'name': name
        }

        result = await self._make_request(
            method='POST',
            endpoint='/reactions.add',
            data=data
        )

        logger.info(
            "slack_reaction_added",
            channel=channel,
            ts=timestamp,
            emoji=name
        )

        return result

    async def remove_reaction(
        self,
        channel: str,
        timestamp: str,
        name: str
    ) -> Dict[str, Any]:
        """Remove a reaction from a message."""
        data = {
            'channel': channel,
            'timestamp': timestamp,
            'name': name
        }

        result = await self._make_request(
            method='POST',
            endpoint='/reactions.remove',
            data=data
        )

        logger.info("slack_reaction_removed", channel=channel, ts=timestamp, emoji=name)
        return result

    # ===================================================================
    # FILES API
    # ===================================================================

    async def upload_file(
        self,
        channels: str,
        file: bytes,
        filename: str,
        title: Optional[str] = None,
        initial_comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Slack.

        Args:
            channels: Comma-separated channel IDs
            file: File content as bytes
            filename: Filename
            title: File title
            initial_comment: Comment to add with file

        Returns:
            File upload response

        Example:
            >>> with open('report.pdf', 'rb') as f:
            ...     result = await slack.upload_file(
            ...         channels="C1234567890",
            ...         file=f.read(),
            ...         filename="Q4_Sales_Report.pdf",
            ...         title="Q4 Sales Report",
            ...         initial_comment="Here's the Q4 sales report"
            ...     )
        """
        data = {
            'channels': channels,
            'filename': filename,
            'title': title,
            'initial_comment': initial_comment,
            'content': file
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        result = await self._make_request(
            method='POST',
            endpoint='/files.upload',
            data=data
        )

        logger.info(
            "slack_file_uploaded",
            filename=filename,
            channels=channels
        )

        return result

    # ===================================================================
    # UTILITY METHODS
    # ===================================================================

    async def send_notification(
        self,
        channel: str,
        title: str,
        message: str,
        color: str = "good",
        fields: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Send a formatted notification (convenience method).

        Args:
            channel: Channel ID or name
            title: Notification title
            message: Notification message
            color: Sidebar color (good, warning, danger, or hex)
            fields: Optional list of fields
                [{"title": "Field", "value": "Value", "short": True}]

        Returns:
            Message response

        Example:
            >>> await slack.send_notification(
            ...     channel="#sales-alerts",
            ...     title="New Deal Created",
            ...     message="Q4 Enterprise deal worth $50,000",
            ...     color="good",
            ...     fields=[
            ...         {"title": "Account", "value": "Acme Corp", "short": True},
            ...         {"title": "Owner", "value": "John Doe", "short": True}
            ...     ]
            ... )
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]

        if fields:
            for field in fields:
                blocks.append({
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*{field['title']}:*\n{field['value']}"
                        }
                    ]
                })

        return await self.send_message(channel=channel, blocks=blocks)

    def _override_make_request_for_slack_api_format(self):
        """
        Slack uses slightly different response format.
        Override to handle Slack's {"ok": true/false} response format.
        """
        pass
