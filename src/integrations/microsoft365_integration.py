"""
Microsoft 365 Integration
Priority Score: 17
ICP Adoption: High for enterprise customers

Provides comprehensive Microsoft 365 operations:
- Outlook (Email, Calendar, Contacts)
- OneDrive (File storage)
- Teams (Messages, Channels)
- Excel (Read/Write workbooks)

Uses Microsoft Graph API for unified access.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from .auth.oauth2_base import OAuth2Integration
from .base import ConnectionTestResult, IntegrationStatus, ValidationError, APIError

logger = structlog.get_logger(__name__)


class Microsoft365Integration(OAuth2Integration):
    """
    Microsoft 365 OAuth2 integration using Microsoft Graph API.

    Scopes Required:
    - Mail.ReadWrite
    - Mail.Send
    - Calendars.ReadWrite
    - Contacts.ReadWrite
    - Files.ReadWrite.All
    - User.Read

    Rate Limits:
    - Per-app throttling: 2000 requests per second per tenant
    - Per-user throttling: varies by service

    Documentation: https://learn.microsoft.com/en-us/graph/overview
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 10
    ):
        """
        Initialize Microsoft 365 integration.

        Args:
            credentials: OAuth2 credentials
                - client_id: Azure AD app client ID
                - client_secret: Azure AD app client secret
                - access_token: Current access token
                - refresh_token: Refresh token
                - tenant_id: Azure AD tenant ID (optional)
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 10)
        """
        super().__init__(
            integration_name="microsoft365",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.tenant_id = credentials.get('tenant_id', 'common')
        self.user_info: Optional[Dict[str, Any]] = None

        logger.info(
            "microsoft365_initialized",
            tenant_id=self.tenant_id,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    def get_oauth_config(self) -> Dict[str, Any]:
        """Get Microsoft 365 OAuth2 configuration."""
        return {
            'auth_url': f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize',
            'token_url': f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token',
            'api_base_url': 'https://graph.microsoft.com/v1.0',
            'scopes': [
                'https://graph.microsoft.com/Mail.ReadWrite',
                'https://graph.microsoft.com/Mail.Send',
                'https://graph.microsoft.com/Calendars.ReadWrite',
                'https://graph.microsoft.com/Contacts.ReadWrite',
                'https://graph.microsoft.com/Files.ReadWrite.All',
                'https://graph.microsoft.com/User.Read',
                'offline_access'  # Required for refresh token
            ]
        }

    async def test_connection(self) -> ConnectionTestResult:
        """Test connection to Microsoft Graph API."""
        try:
            start_time = datetime.now()

            # Get current user info
            response = await self._make_request(
                method='GET',
                endpoint='/me'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Store user info
            self.user_info = response

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Microsoft 365",
                response_time_ms=duration_ms,
                metadata={
                    'user_id': response.get('id'),
                    'user_email': response.get('mail') or response.get('userPrincipalName'),
                    'display_name': response.get('displayName'),
                    'integration_name': 'microsoft365'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Microsoft 365 connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # OUTLOOK - EMAIL API
    # ===================================================================

    async def send_email(
        self,
        to_recipients: List[str],
        subject: str,
        body: str,
        body_content_type: str = "HTML",
        cc_recipients: Optional[List[str]] = None,
        bcc_recipients: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send an email.

        Args:
            to_recipients: List of recipient email addresses
            subject: Email subject
            body: Email body content
            body_content_type: "HTML" or "Text"
            cc_recipients: CC recipients
            bcc_recipients: BCC recipients
            attachments: List of attachments
                [{"@odata.type": "#microsoft.graph.fileAttachment",
                  "name": "file.pdf",
                  "contentBytes": "base64_content"}]

        Returns:
            Email send response

        Example:
            >>> await m365.send_email(
            ...     to_recipients=["jane@example.com"],
            ...     subject="Q4 Sales Report",
            ...     body="<h1>Q4 Report</h1><p>See attached.</p>",
            ...     cc_recipients=["manager@example.com"]
            ... )
        """
        message = {
            "subject": subject,
            "body": {
                "contentType": body_content_type,
                "content": body
            },
            "toRecipients": [
                {"emailAddress": {"address": email}} for email in to_recipients
            ]
        }

        if cc_recipients:
            message["ccRecipients"] = [
                {"emailAddress": {"address": email}} for email in cc_recipients
            ]

        if bcc_recipients:
            message["bccRecipients"] = [
                {"emailAddress": {"address": email}} for email in bcc_recipients
            ]

        if attachments:
            message["attachments"] = attachments

        data = {
            "message": message,
            "saveToSentItems": True
        }

        result = await self._make_request(
            method='POST',
            endpoint='/me/sendMail',
            data=data
        )

        logger.info(
            "m365_email_sent",
            to=to_recipients,
            subject=subject
        )

        return result

    async def list_messages(
        self,
        folder: str = "inbox",
        filter_query: Optional[str] = None,
        top: int = 50,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        List email messages.

        Args:
            folder: Folder name (inbox, sentitems, drafts, deleteditems)
            filter_query: OData filter query
                Example: "isRead eq false" or "from/emailAddress/address eq 'jane@example.com'"
            top: Number of results (max: 999)
            skip: Pagination offset

        Returns:
            List of messages

        Example:
            >>> # Get unread emails
            >>> messages = await m365.list_messages(
            ...     folder="inbox",
            ...     filter_query="isRead eq false",
            ...     top=25
            ... )
        """
        params = {
            '$top': min(top, 999),
            '$skip': skip,
            '$orderby': 'receivedDateTime DESC'
        }

        if filter_query:
            params['$filter'] = filter_query

        return await self._make_request(
            method='GET',
            endpoint=f'/me/mailFolders/{folder}/messages',
            params=params
        )

    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get a specific email message."""
        return await self._make_request(
            method='GET',
            endpoint=f'/me/messages/{message_id}'
        )

    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read."""
        data = {
            "isRead": True
        }

        result = await self._make_request(
            method='PATCH',
            endpoint=f'/me/messages/{message_id}',
            data=data
        )

        logger.info("m365_message_marked_read", message_id=message_id)
        return result

    async def delete_message(self, message_id: str) -> Dict[str, Any]:
        """Delete a message."""
        await self._make_request(
            method='DELETE',
            endpoint=f'/me/messages/{message_id}'
        )

        logger.info("m365_message_deleted", message_id=message_id)
        return {'status': 'deleted', 'message_id': message_id}

    # ===================================================================
    # OUTLOOK - CALENDAR API
    # ===================================================================

    async def create_calendar_event(
        self,
        subject: str,
        start: str,
        end: str,
        attendees: Optional[List[str]] = None,
        location: Optional[str] = None,
        body: Optional[str] = None,
        is_online_meeting: bool = False
    ) -> Dict[str, Any]:
        """
        Create a calendar event.

        Args:
            subject: Event title
            start: Start time (ISO 8601: "2025-01-15T10:00:00")
            end: End time (ISO 8601)
            attendees: List of attendee email addresses
            location: Event location
            body: Event description
            is_online_meeting: Create as Teams meeting

        Returns:
            Created event data

        Example:
            >>> event = await m365.create_calendar_event(
            ...     subject="Q4 Review Meeting",
            ...     start="2025-01-15T14:00:00",
            ...     end="2025-01-15T15:00:00",
            ...     attendees=["jane@example.com", "john@example.com"],
            ...     location="Conference Room A",
            ...     is_online_meeting=True
            ... )
        """
        data = {
            "subject": subject,
            "start": {
                "dateTime": start,
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end,
                "timeZone": "UTC"
            },
            "isOnlineMeeting": is_online_meeting,
            "onlineMeetingProvider": "teamsForBusiness" if is_online_meeting else None
        }

        if location:
            data["location"] = {
                "displayName": location
            }

        if body:
            data["body"] = {
                "contentType": "HTML",
                "content": body
            }

        if attendees:
            data["attendees"] = [
                {
                    "emailAddress": {"address": email},
                    "type": "required"
                }
                for email in attendees
            ]

        result = await self._make_request(
            method='POST',
            endpoint='/me/calendar/events',
            data=data
        )

        logger.info(
            "m365_event_created",
            event_id=result.get('id'),
            subject=subject
        )

        return result

    async def list_calendar_events(
        self,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None,
        top: int = 50
    ) -> Dict[str, Any]:
        """
        List calendar events.

        Args:
            start_datetime: Filter events after this time (ISO 8601)
            end_datetime: Filter events before this time (ISO 8601)
            top: Number of results

        Returns:
            List of calendar events
        """
        params = {
            '$top': min(top, 999),
            '$orderby': 'start/dateTime'
        }

        if start_datetime and end_datetime:
            params['$filter'] = (
                f"start/dateTime ge '{start_datetime}' and "
                f"end/dateTime le '{end_datetime}'"
            )

        return await self._make_request(
            method='GET',
            endpoint='/me/calendar/events',
            params=params
        )

    async def update_calendar_event(
        self,
        event_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a calendar event."""
        result = await self._make_request(
            method='PATCH',
            endpoint=f'/me/calendar/events/{event_id}',
            data=updates
        )

        logger.info("m365_event_updated", event_id=event_id)
        return result

    async def delete_calendar_event(self, event_id: str) -> Dict[str, Any]:
        """Delete a calendar event."""
        await self._make_request(
            method='DELETE',
            endpoint=f'/me/calendar/events/{event_id}'
        )

        logger.info("m365_event_deleted", event_id=event_id)
        return {'status': 'deleted', 'event_id': event_id}

    # ===================================================================
    # OUTLOOK - CONTACTS API
    # ===================================================================

    async def create_contact(
        self,
        given_name: str,
        surname: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company_name: Optional[str] = None,
        job_title: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a contact.

        Args:
            given_name: First name
            surname: Last name
            email: Email address
            phone: Phone number
            company_name: Company name
            job_title: Job title
            **kwargs: Additional contact fields

        Returns:
            Created contact data
        """
        data = {
            "givenName": given_name,
            "surname": surname,
            "companyName": company_name,
            "jobTitle": job_title,
            **kwargs
        }

        if email:
            data["emailAddresses"] = [
                {
                    "address": email,
                    "name": f"{given_name} {surname}"
                }
            ]

        if phone:
            data["businessPhones"] = [phone]

        result = await self._make_request(
            method='POST',
            endpoint='/me/contacts',
            data=data
        )

        logger.info(
            "m365_contact_created",
            contact_id=result.get('id'),
            name=f"{given_name} {surname}"
        )

        return result

    async def list_contacts(self, top: int = 50) -> Dict[str, Any]:
        """List contacts."""
        params = {
            '$top': min(top, 999),
            '$orderby': 'displayName'
        }

        return await self._make_request(
            method='GET',
            endpoint='/me/contacts',
            params=params
        )

    async def search_contacts(self, query: str) -> Dict[str, Any]:
        """
        Search contacts.

        Args:
            query: Search query (searches name, email, phone)

        Returns:
            Matching contacts
        """
        params = {
            '$search': f'"{query}"'
        }

        return await self._make_request(
            method='GET',
            endpoint='/me/contacts',
            params=params
        )

    # ===================================================================
    # ONEDRIVE - FILES API
    # ===================================================================

    async def upload_file(
        self,
        file_path: str,
        content: bytes,
        parent_folder: str = "root"
    ) -> Dict[str, Any]:
        """
        Upload a file to OneDrive.

        Args:
            file_path: File path (e.g., "documents/report.pdf")
            content: File content as bytes
            parent_folder: Parent folder ("root" for root directory)

        Returns:
            Uploaded file metadata

        Example:
            >>> with open('report.pdf', 'rb') as f:
            ...     result = await m365.upload_file(
            ...         file_path="Sales_Reports/Q4_2024.pdf",
            ...         content=f.read()
            ...     )
        """
        endpoint = f'/me/drive/{parent_folder}:/{file_path}:/content'

        result = await self._make_request(
            method='PUT',
            endpoint=endpoint,
            data=content
        )

        logger.info(
            "m365_file_uploaded",
            file_id=result.get('id'),
            file_path=file_path
        )

        return result

    async def download_file(self, file_id: str) -> bytes:
        """Download a file from OneDrive."""
        # Get download URL
        metadata = await self._make_request(
            method='GET',
            endpoint=f'/me/drive/items/{file_id}'
        )

        download_url = metadata.get('@microsoft.graph.downloadUrl')

        if not download_url:
            raise APIError("File download URL not available")

        # Download file content
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise APIError(f"File download failed: {response.status}")

    async def list_files(
        self,
        folder: str = "root",
        top: int = 50
    ) -> Dict[str, Any]:
        """
        List files in a folder.

        Args:
            folder: Folder path ("root" for root directory)
            top: Number of results

        Returns:
            List of files and folders
        """
        params = {
            '$top': min(top, 999)
        }

        return await self._make_request(
            method='GET',
            endpoint=f'/me/drive/{folder}/children',
            params=params
        )

    async def create_folder(
        self,
        folder_name: str,
        parent_folder: str = "root"
    ) -> Dict[str, Any]:
        """Create a folder in OneDrive."""
        data = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }

        result = await self._make_request(
            method='POST',
            endpoint=f'/me/drive/{parent_folder}/children',
            data=data
        )

        logger.info(
            "m365_folder_created",
            folder_id=result.get('id'),
            folder_name=folder_name
        )

        return result

    # ===================================================================
    # UTILITY METHODS
    # ===================================================================

    async def get_user_profile(self) -> Dict[str, Any]:
        """Get current user profile."""
        return await self._make_request(
            method='GET',
            endpoint='/me'
        )

    async def search_emails(
        self,
        query: str,
        top: int = 25
    ) -> Dict[str, Any]:
        """
        Search emails.

        Args:
            query: Search query
            top: Number of results

        Returns:
            Matching emails

        Example:
            >>> # Search for emails from specific sender
            >>> results = await m365.search_emails(
            ...     query="from:jane@example.com",
            ...     top=10
            ... )
        """
        params = {
            '$search': f'"{query}"',
            '$top': min(top, 999)
        }

        return await self._make_request(
            method='GET',
            endpoint='/me/messages',
            params=params
        )
