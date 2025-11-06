"""SendGrid Email Integration - Production-ready implementation"""
import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content, Personalization,
    Attachment, FileContent, FileName, FileType, Disposition
)
from python_http_client.exceptions import HTTPError
import base64
import time

logger = structlog.get_logger(__name__)


class SendGridClient:
    """Production-ready SendGrid API client for email delivery

    Features:
    - HTML/text email sending
    - Dynamic template support
    - Bulk email sending with batch processing
    - Email webhook event tracking
    - Email validation
    - Retry logic with exponential backoff
    - Rate limit handling
    """

    def __init__(self):
        """Initialize SendGrid client with API credentials from environment"""
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@yourcompany.com")
        self.from_name = os.getenv("SENDGRID_FROM_NAME", "Your Company")

        if not self.api_key:
            logger.warning("SendGrid API key not configured - client will operate in mock mode")
            self.client = None
            self.mock_mode = True
        else:
            try:
                self.client = SendGridAPIClient(self.api_key)
                self.mock_mode = False
                logger.info("SendGrid client initialized successfully", from_email=self.from_email)
            except Exception as e:
                logger.error("Failed to initialize SendGrid client", error=str(e))
                self.client = None
                self.mock_mode = True

        # Configuration
        self.max_retries = int(os.getenv("SENDGRID_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("SENDGRID_RETRY_DELAY", "1"))  # seconds
        self.batch_size = int(os.getenv("SENDGRID_BATCH_SIZE", "1000"))  # SendGrid limit

    def validate_email(self, email: str) -> bool:
        """Validate email address format

        Args:
            email: Email address to validate

        Returns:
            True if email is valid, False otherwise
        """
        if not email or not isinstance(email, str):
            return False

        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _retry_with_backoff(self, func, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry logic

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except HTTPError as e:
                last_exception = e

                # Check if error is retryable
                status_code = e.status_code if hasattr(e, 'status_code') else 0

                # Don't retry on client errors (4xx except 429)
                if 400 <= status_code < 500 and status_code != 429:
                    logger.error(
                        "SendGrid client error - not retrying",
                        status_code=status_code,
                        error=str(e)
                    )
                    raise

                # Retry on server errors (5xx) or rate limits (429)
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        "SendGrid request failed - retrying",
                        attempt=attempt + 1,
                        max_retries=self.max_retries,
                        delay=delay,
                        status_code=status_code,
                        error=str(e)
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "SendGrid request failed - all retries exhausted",
                        attempts=self.max_retries,
                        error=str(e)
                    )
            except Exception as e:
                last_exception = e
                logger.error("Unexpected error in SendGrid request", error=str(e))
                raise

        # If we get here, all retries failed
        raise last_exception

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        custom_args: Optional[Dict[str, str]] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send a single email via SendGrid

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML email body (optional)
            text_content: Plain text email body (optional)
            from_email: Sender email (uses default if not provided)
            from_name: Sender name (uses default if not provided)
            reply_to: Reply-to email address (optional)
            cc: List of CC email addresses (optional)
            bcc: List of BCC email addresses (optional)
            attachments: List of attachment dicts with 'content', 'filename', 'type' (optional)
            custom_args: Custom arguments for tracking (optional)
            categories: Categories for analytics (optional, max 10)

        Returns:
            Dict with status and message_id or error details
        """
        try:
            # Validate required fields
            if not to_email:
                return {"error": "to_email is required"}

            if not subject:
                return {"error": "subject is required"}

            if not html_content and not text_content:
                return {"error": "Either html_content or text_content is required"}

            # Validate email addresses
            if not self.validate_email(to_email):
                return {"error": f"Invalid to_email address: {to_email}"}

            if from_email and not self.validate_email(from_email):
                return {"error": f"Invalid from_email address: {from_email}"}

            # Mock mode
            if self.mock_mode:
                logger.info(
                    "SendGrid mock mode - email not sent",
                    to_email=to_email,
                    subject=subject
                )
                return {
                    "status": "success",
                    "message": "Email sent (mock mode)",
                    "mock": True,
                    "message_id": f"mock_{int(datetime.now().timestamp())}",
                    "to_email": to_email,
                    "subject": subject
                }

            # Build email message
            sender = Email(from_email or self.from_email, from_name or self.from_name)
            recipient = To(to_email)

            # Create Mail object
            mail = Mail()
            mail.from_email = sender
            mail.subject = subject

            # Add recipient
            personalization = Personalization()
            personalization.add_to(recipient)

            # Add CC recipients
            if cc:
                for cc_email in cc:
                    if self.validate_email(cc_email):
                        personalization.add_cc(To(cc_email))

            # Add BCC recipients
            if bcc:
                for bcc_email in bcc:
                    if self.validate_email(bcc_email):
                        personalization.add_bcc(To(bcc_email))

            mail.add_personalization(personalization)

            # Add content
            if text_content:
                mail.add_content(Content("text/plain", text_content))
            if html_content:
                mail.add_content(Content("text/html", html_content))

            # Add reply-to
            if reply_to and self.validate_email(reply_to):
                mail.reply_to = Email(reply_to)

            # Add attachments
            if attachments:
                for attachment_data in attachments:
                    attachment = Attachment()
                    attachment.file_content = FileContent(attachment_data.get('content', ''))
                    attachment.file_name = FileName(attachment_data.get('filename', 'file'))
                    attachment.file_type = FileType(attachment_data.get('type', 'application/octet-stream'))
                    attachment.disposition = Disposition('attachment')
                    mail.add_attachment(attachment)

            # Add custom args
            if custom_args:
                for key, value in custom_args.items():
                    mail.add_custom_arg(key, str(value))

            # Add categories
            if categories:
                for category in categories[:10]:  # Max 10 categories
                    mail.add_category(category)

            # Send email with retry logic
            def _send():
                return self.client.send(mail)

            response = self._retry_with_backoff(_send)

            logger.info(
                "SendGrid email sent successfully",
                to_email=to_email,
                subject=subject,
                status_code=response.status_code
            )

            return {
                "status": "success",
                "message": "Email sent successfully",
                "message_id": response.headers.get('X-Message-Id'),
                "to_email": to_email,
                "subject": subject,
                "status_code": response.status_code
            }

        except HTTPError as e:
            logger.error(
                "SendGrid API error",
                to_email=to_email,
                error=str(e),
                status_code=e.status_code if hasattr(e, 'status_code') else None
            )
            return {
                "error": f"SendGrid API error: {str(e)}",
                "status_code": e.status_code if hasattr(e, 'status_code') else None
            }
        except Exception as e:
            logger.error("Failed to send email via SendGrid", error=str(e))
            return {"error": f"Failed to send email: {str(e)}"}

    def send_template_email(
        self,
        to_email: str,
        template_id: str,
        dynamic_data: Dict[str, Any],
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        custom_args: Optional[Dict[str, str]] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Send email using SendGrid dynamic template

        Args:
            to_email: Recipient email address
            template_id: SendGrid template ID
            dynamic_data: Data to populate template variables
            from_email: Sender email (uses default if not provided)
            from_name: Sender name (uses default if not provided)
            reply_to: Reply-to email address (optional)
            custom_args: Custom arguments for tracking (optional)
            categories: Categories for analytics (optional)

        Returns:
            Dict with status and message_id or error details
        """
        try:
            # Validate required fields
            if not to_email:
                return {"error": "to_email is required"}

            if not template_id:
                return {"error": "template_id is required"}

            if not self.validate_email(to_email):
                return {"error": f"Invalid to_email address: {to_email}"}

            # Mock mode
            if self.mock_mode:
                logger.info(
                    "SendGrid mock mode - template email not sent",
                    to_email=to_email,
                    template_id=template_id
                )
                return {
                    "status": "success",
                    "message": "Template email sent (mock mode)",
                    "mock": True,
                    "message_id": f"mock_{int(datetime.now().timestamp())}",
                    "to_email": to_email,
                    "template_id": template_id
                }

            # Build email message
            sender = Email(from_email or self.from_email, from_name or self.from_name)
            recipient = To(to_email)

            mail = Mail(from_email=sender, to_emails=recipient)
            mail.template_id = template_id

            # Add dynamic template data
            if dynamic_data:
                mail.dynamic_template_data = dynamic_data

            # Add reply-to
            if reply_to and self.validate_email(reply_to):
                mail.reply_to = Email(reply_to)

            # Add custom args
            if custom_args:
                for key, value in custom_args.items():
                    mail.add_custom_arg(key, str(value))

            # Add categories
            if categories:
                for category in categories[:10]:
                    mail.add_category(category)

            # Send email with retry logic
            def _send():
                return self.client.send(mail)

            response = self._retry_with_backoff(_send)

            logger.info(
                "SendGrid template email sent successfully",
                to_email=to_email,
                template_id=template_id,
                status_code=response.status_code
            )

            return {
                "status": "success",
                "message": "Template email sent successfully",
                "message_id": response.headers.get('X-Message-Id'),
                "to_email": to_email,
                "template_id": template_id,
                "status_code": response.status_code
            }

        except HTTPError as e:
            logger.error(
                "SendGrid API error",
                to_email=to_email,
                template_id=template_id,
                error=str(e),
                status_code=e.status_code if hasattr(e, 'status_code') else None
            )
            return {
                "error": f"SendGrid API error: {str(e)}",
                "status_code": e.status_code if hasattr(e, 'status_code') else None
            }
        except Exception as e:
            logger.error("Failed to send template email", error=str(e))
            return {"error": f"Failed to send template email: {str(e)}"}

    def send_bulk_emails(
        self,
        emails: List[Dict[str, Any]],
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send multiple emails in batches

        Each email dict should contain:
        - to_email (required)
        - subject (required)
        - html_content or text_content (required)
        - Optional: reply_to, custom_args, categories

        Args:
            emails: List of email dictionaries
            from_email: Default sender email
            from_name: Default sender name

        Returns:
            Dict with batch results and statistics
        """
        try:
            if not emails:
                return {"error": "emails list is required"}

            # Mock mode
            if self.mock_mode:
                logger.info(
                    "SendGrid mock mode - bulk emails not sent",
                    count=len(emails)
                )
                return {
                    "status": "success",
                    "message": f"Bulk emails sent (mock mode)",
                    "mock": True,
                    "total_emails": len(emails),
                    "successful": len(emails),
                    "failed": 0
                }

            # Process emails in batches
            total = len(emails)
            successful = 0
            failed = 0
            errors = []

            for i in range(0, total, self.batch_size):
                batch = emails[i:i + self.batch_size]

                for email_data in batch:
                    result = self.send_email(
                        to_email=email_data.get('to_email'),
                        subject=email_data.get('subject'),
                        html_content=email_data.get('html_content'),
                        text_content=email_data.get('text_content'),
                        from_email=email_data.get('from_email') or from_email,
                        from_name=email_data.get('from_name') or from_name,
                        reply_to=email_data.get('reply_to'),
                        custom_args=email_data.get('custom_args'),
                        categories=email_data.get('categories')
                    )

                    if result.get('status') == 'success':
                        successful += 1
                    else:
                        failed += 1
                        errors.append({
                            'to_email': email_data.get('to_email'),
                            'error': result.get('error')
                        })

                # Small delay between batches to avoid rate limits
                if i + self.batch_size < total:
                    time.sleep(0.1)

            logger.info(
                "Bulk emails sent",
                total=total,
                successful=successful,
                failed=failed
            )

            return {
                "status": "success" if failed == 0 else "partial_success",
                "message": f"Sent {successful}/{total} emails successfully",
                "total_emails": total,
                "successful": successful,
                "failed": failed,
                "errors": errors if errors else None
            }

        except Exception as e:
            logger.error("Failed to send bulk emails", error=str(e))
            return {"error": f"Failed to send bulk emails: {str(e)}"}

    def track_email_events(
        self,
        webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process SendGrid webhook events

        SendGrid webhook events include:
        - delivered: Email delivered successfully
        - open: Email opened by recipient
        - click: Link clicked in email
        - bounce: Email bounced
        - dropped: Email dropped (invalid, spam, etc.)
        - deferred: Email deferred (temporary issue)
        - unsubscribe: Recipient unsubscribed
        - spam_report: Email marked as spam

        Args:
            webhook_data: Webhook payload from SendGrid

        Returns:
            Dict with processed event details
        """
        try:
            if not webhook_data:
                return {"error": "webhook_data is required"}

            # SendGrid sends events as a list
            events = webhook_data if isinstance(webhook_data, list) else [webhook_data]

            processed_events = []

            for event in events:
                event_type = event.get('event')
                email = event.get('email')
                timestamp = event.get('timestamp')

                processed_event = {
                    'event_type': event_type,
                    'email': email,
                    'timestamp': timestamp,
                    'message_id': event.get('sg_message_id'),
                    'category': event.get('category', []),
                    'custom_args': event.get('custom_args', {})
                }

                # Add event-specific data
                if event_type == 'click':
                    processed_event['url'] = event.get('url')
                elif event_type == 'bounce':
                    processed_event['reason'] = event.get('reason')
                    processed_event['bounce_type'] = event.get('type')
                elif event_type == 'dropped':
                    processed_event['reason'] = event.get('reason')
                elif event_type == 'spam_report':
                    processed_event['reason'] = event.get('reason')

                processed_events.append(processed_event)

                logger.info(
                    "SendGrid webhook event processed",
                    event_type=event_type,
                    email=email,
                    message_id=processed_event['message_id']
                )

            return {
                "status": "success",
                "message": f"Processed {len(processed_events)} events",
                "events": processed_events,
                "count": len(processed_events)
            }

        except Exception as e:
            logger.error("Failed to process webhook events", error=str(e))
            return {"error": f"Failed to process webhook events: {str(e)}"}

    def get_stats(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        aggregated_by: str = "day"
    ) -> Dict[str, Any]:
        """Get email statistics from SendGrid

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (optional, defaults to today)
            aggregated_by: Aggregation period (day, week, month)

        Returns:
            Dict with email statistics
        """
        try:
            if self.mock_mode:
                return {
                    "status": "success",
                    "mock": True,
                    "stats": {
                        "requests": 1250,
                        "delivered": 1198,
                        "opens": 456,
                        "unique_opens": 389,
                        "clicks": 234,
                        "unique_clicks": 189,
                        "bounces": 12,
                        "spam_reports": 2
                    }
                }

            # Build query parameters
            params = {
                'start_date': start_date,
                'aggregated_by': aggregated_by
            }

            if end_date:
                params['end_date'] = end_date

            # Get stats from SendGrid
            def _get_stats():
                return self.client.client.stats.get(query_params=params)

            response = self._retry_with_backoff(_get_stats)

            logger.info(
                "Retrieved SendGrid statistics",
                start_date=start_date,
                end_date=end_date
            )

            return {
                "status": "success",
                "stats": response.to_dict if hasattr(response, 'to_dict') else response
            }

        except Exception as e:
            logger.error("Failed to retrieve statistics", error=str(e))
            return {"error": f"Failed to retrieve statistics: {str(e)}"}
