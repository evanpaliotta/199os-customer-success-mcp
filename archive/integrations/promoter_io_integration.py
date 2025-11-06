"""
Promoter.io Integration
Priority Score: 9
ICP Adoption: 25-35% of customer-centric companies

Modern NPS platform providing:
- NPS Campaigns
- Contacts Management
- Survey Responses
- Metrics and Reporting
- Automated Workflows
- Integrations
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


class PromoterIoIntegration(BaseIntegration):
    """
    Promoter.io API integration with API key authentication.

    Authentication:
    - API Key in header (X-API-KEY)

    Rate Limits:
    - 120 requests per minute
    - 5000 requests per day

    Documentation: https://developer.promoter.io/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ) -> Any:
        """
        Initialize Promoter.io integration.

        Args:
            credentials: Promoter.io credentials
                - api_key: Promoter.io API key
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="promoter_io",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')

        if not self.api_key:
            raise ValidationError("Promoter.io api_key is required")

        self.base_url = "https://app.promoter.io/api/v2"

        logger.info(
            "promoter_io_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Promoter.io (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("promoter_io_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Promoter.io authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make authenticated HTTP request to Promoter.io API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            'X-API-KEY': self.api_key,
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
                        f"Promoter.io API error ({response.status}): {error_text}",
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
        """Test connection to Promoter.io API."""
        try:
            start_time = datetime.now()

            # Test with account info request
            response = await self._make_request(
                method='GET',
                endpoint='/account'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Promoter.io",
                response_time_ms=duration_ms,
                metadata={
                    'integration_name': 'promoter_io',
                    'account_name': response.get('name')
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Promoter.io connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # CONTACTS API
    # ===================================================================

    async def list_contacts(
        self,
        page: int = 1,
        per_page: int = 100,
        campaign_id: Optional[str] = None,
        segment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List contacts.

        Args:
            page: Page number
            per_page: Results per page (max: 100)
            campaign_id: Filter by campaign ID
            segment_id: Filter by segment ID

        Returns:
            Paginated list of contacts

        Example:
            >>> contacts = await promoter.list_contacts(
            ...     page=1,
            ...     per_page=50
            ... )
            >>> for contact in contacts['data']:
            ...     print(contact['email'], contact['nps_score'])
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }

        if campaign_id:
            params['campaign_id'] = campaign_id
        if segment_id:
            params['segment_id'] = segment_id

        result = await self._make_request(
            method='GET',
            endpoint='/contacts',
            params=params
        )

        logger.info(
            "promoter_io_contacts_listed",
            count=len(result.get('data', [])) if isinstance(result, dict) else 0
        )

        return result

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """
        Get contact by ID.

        Args:
            contact_id: Contact ID

        Returns:
            Contact details with response history
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/contacts/{contact_id}'
        )

    async def create_contact(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        send_survey: bool = False,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a contact.

        Args:
            email: Contact email
            first_name: First name
            last_name: Last name
            properties: Custom properties (company, plan, signup_date, etc.)
            send_survey: Send survey immediately
            campaign_id: Campaign ID to send survey from

        Returns:
            Created contact data

        Example:
            >>> contact = await promoter.create_contact(
            ...     email="jane@acme.com",
            ...     first_name="Jane",
            ...     last_name="Doe",
            ...     properties={
            ...         "company": "Acme Corp",
            ...         "plan": "Enterprise",
            ...         "mrr": 999
            ...     },
            ...     send_survey=True,
            ...     campaign_id="camp_123"
            ... )
        """
        data = {'email': email}

        if first_name:
            data['first_name'] = first_name
        if last_name:
            data['last_name'] = last_name
        if properties:
            data['properties'] = properties
        if send_survey:
            data['send_survey'] = send_survey
        if campaign_id:
            data['campaign_id'] = campaign_id

        result = await self._make_request(
            method='POST',
            endpoint='/contacts',
            data=data
        )

        logger.info(
            "promoter_io_contact_created",
            contact_id=result.get('id'),
            email=email,
            send_survey=send_survey
        )

        return result

    async def update_contact(
        self,
        contact_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update contact properties.

        Args:
            contact_id: Contact ID
            properties: Properties to update

        Returns:
            Updated contact data

        Example:
            >>> await promoter.update_contact(
            ...     contact_id="cont_123",
            ...     properties={"plan": "Growth", "mrr": 499}
            ... )
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/contacts/{contact_id}',
            data=properties
        )

        logger.info(
            "promoter_io_contact_updated",
            contact_id=contact_id
        )

        return result

    async def delete_contact(self, contact_id: str) -> Dict[str, Any]:
        """
        Delete a contact.

        Args:
            contact_id: Contact ID

        Returns:
            Deletion confirmation
        """
        result = await self._make_request(
            method='DELETE',
            endpoint=f'/contacts/{contact_id}'
        )

        logger.info(
            "promoter_io_contact_deleted",
            contact_id=contact_id
        )

        return result

    # ===================================================================
    # CAMPAIGNS API
    # ===================================================================

    async def list_campaigns(
        self,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List NPS campaigns.

        Args:
            status: Filter by status (active, paused, draft)

        Returns:
            List of campaigns

        Example:
            >>> campaigns = await promoter.list_campaigns(status="active")
            >>> for campaign in campaigns:
            ...     print(f"{campaign['name']}: {campaign['nps']}")
        """
        params = {}
        if status:
            params['status'] = status

        result = await self._make_request(
            method='GET',
            endpoint='/campaigns',
            params=params
        )

        return result if isinstance(result, list) else []

    async def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get campaign by ID.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign details with settings and metrics
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/campaigns/{campaign_id}'
        )

    async def create_campaign(
        self,
        name: str,
        survey_type: str = "nps",
        send_from_name: Optional[str] = None,
        send_from_email: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new campaign.

        Args:
            name: Campaign name
            survey_type: Survey type (nps, csat, ces)
            send_from_name: Sender name
            send_from_email: Sender email
            settings: Campaign settings (frequency, throttling, etc.)

        Returns:
            Created campaign

        Example:
            >>> campaign = await promoter.create_campaign(
            ...     name="Quarterly NPS - Q4 2024",
            ...     survey_type="nps",
            ...     send_from_name="Customer Success Team",
            ...     send_from_email="success@company.com",
            ...     settings={"frequency_days": 90}
            ... )
        """
        data = {
            'name': name,
            'survey_type': survey_type
        }

        if send_from_name:
            data['send_from_name'] = send_from_name
        if send_from_email:
            data['send_from_email'] = send_from_email
        if settings:
            data['settings'] = settings

        result = await self._make_request(
            method='POST',
            endpoint='/campaigns',
            data=data
        )

        logger.info(
            "promoter_io_campaign_created",
            campaign_id=result.get('id'),
            name=name
        )

        return result

    async def update_campaign(
        self,
        campaign_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update campaign settings.

        Args:
            campaign_id: Campaign ID
            data: Fields to update

        Returns:
            Updated campaign data
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/campaigns/{campaign_id}',
            data=data
        )

        logger.info(
            "promoter_io_campaign_updated",
            campaign_id=campaign_id
        )

        return result

    async def send_campaign(
        self,
        campaign_id: str,
        contact_ids: Optional[List[str]] = None,
        segment_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send campaign to contacts.

        Args:
            campaign_id: Campaign ID
            contact_ids: Specific contact IDs to send to
            segment_id: Segment ID to send to

        Returns:
            Send confirmation with count

        Example:
            >>> result = await promoter.send_campaign(
            ...     campaign_id="camp_123",
            ...     segment_id="seg_456"
            ... )
            >>> print(f"Sent to {result['sent_count']} contacts")
        """
        data = {}

        if contact_ids:
            data['contact_ids'] = contact_ids
        if segment_id:
            data['segment_id'] = segment_id

        result = await self._make_request(
            method='POST',
            endpoint=f'/campaigns/{campaign_id}/send',
            data=data
        )

        logger.info(
            "promoter_io_campaign_sent",
            campaign_id=campaign_id,
            sent_count=result.get('sent_count')
        )

        return result

    # ===================================================================
    # RESPONSES API
    # ===================================================================

    async def list_responses(
        self,
        page: int = 1,
        per_page: int = 100,
        campaign_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        score_min: Optional[int] = None,
        score_max: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        List survey responses.

        Args:
            page: Page number
            per_page: Results per page (max: 100)
            campaign_id: Filter by campaign ID
            start_date: Filter by response date (ISO format)
            end_date: Filter by response date (ISO format)
            score_min: Minimum score filter
            score_max: Maximum score filter

        Returns:
            Paginated list of responses

        Example:
            >>> # Get detractor responses
            >>> responses = await promoter.list_responses(
            ...     score_min=0,
            ...     score_max=6,
            ...     per_page=100
            ... )
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }

        if campaign_id:
            params['campaign_id'] = campaign_id
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if score_min is not None:
            params['score_min'] = score_min
        if score_max is not None:
            params['score_max'] = score_max

        result = await self._make_request(
            method='GET',
            endpoint='/responses',
            params=params
        )

        logger.info(
            "promoter_io_responses_listed",
            count=len(result.get('data', [])) if isinstance(result, dict) else 0
        )

        return result

    async def get_response(self, response_id: str) -> Dict[str, Any]:
        """
        Get response by ID.

        Args:
            response_id: Response ID

        Returns:
            Response details with score and feedback
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/responses/{response_id}'
        )

    async def create_response(
        self,
        contact_id: str,
        campaign_id: str,
        score: int,
        comment: Optional[str] = None,
        responded_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a response (for importing historical data).

        Args:
            contact_id: Contact ID
            campaign_id: Campaign ID
            score: NPS score (0-10)
            comment: Response comment
            responded_at: Response timestamp (ISO format)

        Returns:
            Created response

        Example:
            >>> response = await promoter.create_response(
            ...     contact_id="cont_123",
            ...     campaign_id="camp_456",
            ...     score=9,
            ...     comment="Great product, very intuitive!",
            ...     responded_at="2024-10-15T10:30:00Z"
            ... )
        """
        data = {
            'contact_id': contact_id,
            'campaign_id': campaign_id,
            'score': score
        }

        if comment:
            data['comment'] = comment
        if responded_at:
            data['responded_at'] = responded_at

        result = await self._make_request(
            method='POST',
            endpoint='/responses',
            data=data
        )

        logger.info(
            "promoter_io_response_created",
            response_id=result.get('id'),
            score=score
        )

        return result

    async def update_response(
        self,
        response_id: str,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update response metadata.

        Args:
            response_id: Response ID
            tags: Tags for categorization
            notes: Internal notes

        Returns:
            Updated response data
        """
        data = {}

        if tags is not None:
            data['tags'] = tags
        if notes is not None:
            data['notes'] = notes

        result = await self._make_request(
            method='PUT',
            endpoint=f'/responses/{response_id}',
            data=data
        )

        logger.info(
            "promoter_io_response_updated",
            response_id=response_id
        )

        return result

    # ===================================================================
    # METRICS API
    # ===================================================================

    async def get_metrics(
        self,
        campaign_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get NPS metrics and breakdown.

        Args:
            campaign_id: Filter by campaign ID
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            NPS metrics with score and segmentation

        Example:
            >>> metrics = await promoter.get_metrics(
            ...     start_date="2024-01-01",
            ...     end_date="2024-12-31"
            ... )
            >>> print(f"NPS: {metrics['nps']}")
            >>> print(f"Promoters: {metrics['promoters_percentage']}%")
            >>> print(f"Responses: {metrics['response_count']}")
        """
        params = {}

        if campaign_id:
            params['campaign_id'] = campaign_id
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint='/metrics',
            params=params
        )

    async def get_nps_score(
        self,
        campaign_id: Optional[str] = None
    ) -> int:
        """
        Get current NPS score.

        Args:
            campaign_id: Filter by campaign ID

        Returns:
            NPS score (-100 to 100)

        Example:
            >>> nps = await promoter.get_nps_score()
            >>> print(f"Current NPS: {nps}")
        """
        metrics = await self.get_metrics(campaign_id=campaign_id)
        return metrics.get('nps', 0)

    async def get_trends(
        self,
        campaign_id: Optional[str] = None,
        period: str = "month",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get NPS trends over time.

        Args:
            campaign_id: Filter by campaign ID
            period: Trend period (day, week, month, quarter)
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            Time series NPS data

        Example:
            >>> trends = await promoter.get_trends(
            ...     period="month",
            ...     start_date="2024-01-01"
            ... )
            >>> for point in trends['data']:
            ...     print(f"{point['period']}: {point['nps']}")
        """
        params = {'period': period}

        if campaign_id:
            params['campaign_id'] = campaign_id
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint='/metrics/trends',
            params=params
        )

    # ===================================================================
    # SEGMENTS API
    # ===================================================================

    async def list_segments(self) -> List[Dict[str, Any]]:
        """
        List contact segments.

        Returns:
            List of segments with criteria

        Example:
            >>> segments = await promoter.list_segments()
            >>> for segment in segments:
            ...     print(f"{segment['name']}: {segment['contact_count']}")
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
        Create a contact segment.

        Args:
            name: Segment name
            criteria: Segment criteria (filters and conditions)

        Returns:
            Created segment

        Example:
            >>> segment = await promoter.create_segment(
            ...     name="Enterprise Promoters",
            ...     criteria={
            ...         "score_min": 9,
            ...         "properties": {"plan": "Enterprise"}
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
            "promoter_io_segment_created",
            segment_id=result.get('id'),
            name=name
        )

        return result

    # ===================================================================
    # REPORTS API
    # ===================================================================

    async def get_report(
        self,
        report_type: str,
        campaign_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get custom report.

        Args:
            report_type: Report type (overview, distribution, trends, segments)
            campaign_id: Filter by campaign ID
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            Report data

        Example:
            >>> report = await promoter.get_report(
            ...     report_type="distribution",
            ...     start_date="2024-01-01"
            ... )
        """
        params = {'type': report_type}

        if campaign_id:
            params['campaign_id'] = campaign_id
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint='/reports',
            params=params
        )

    async def get_response_rate(
        self,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get survey response rate.

        Args:
            campaign_id: Filter by campaign ID

        Returns:
            Response rate statistics

        Example:
            >>> stats = await promoter.get_response_rate(
            ...     campaign_id="camp_123"
            ... )
            >>> print(f"Response rate: {stats['rate']}%")
        """
        params = {}
        if campaign_id:
            params['campaign_id'] = campaign_id

        return await self._make_request(
            method='GET',
            endpoint='/metrics/response_rate',
            params=params
        )

    async def close(self) -> Any:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("promoter_io_session_closed")
