"""
AskNicely Integration
Priority Score: 9
ICP Adoption: 25-35% of service-focused companies

Customer experience platform providing:
- NPS Surveys
- People (Contacts) Management
- Survey Responses
- Metrics and Analytics
- Dashboard Data
- Automated Workflows
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


class AskNicelyIntegration(BaseIntegration):
    """
    AskNicely API integration with API key authentication.

    Authentication:
    - API Key in header (X-apikey)
    - Domain-specific base URL

    Rate Limits:
    - 100 requests per minute
    - 5000 requests per day

    Documentation: https://asknicely.asknice.ly/help/apidocs
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 90,
        rate_limit_window: int = 60
    ):
        """
        Initialize AskNicely integration.

        Args:
            credentials: AskNicely credentials
                - api_key: AskNicely API key
                - domain: AskNicely domain (e.g., "company.asknice.ly")
            rate_limit_calls: Max API calls per window (default: 90)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="asknicely",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        self.domain = credentials.get('domain', '')

        if not self.api_key:
            raise ValidationError("AskNicely api_key is required")
        if not self.domain:
            raise ValidationError("AskNicely domain is required")

        # Ensure domain has protocol
        if not self.domain.startswith('http'):
            self.domain = f'https://{self.domain}'

        self.base_url = f"{self.domain}/api/v1"

        logger.info(
            "asknicely_initialized",
            domain=self.domain,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with AskNicely (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("asknicely_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"AskNicely authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make authenticated HTTP request to AskNicely API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            'X-apikey': self.api_key,
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
                        f"AskNicely API error ({response.status}): {error_text}",
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
        """Test connection to AskNicely API."""
        try:
            start_time = datetime.now()

            # Test with dashboard metrics request
            response = await self._make_request(
                method='GET',
                endpoint='/dashboard'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to AskNicely",
                response_time_ms=duration_ms,
                metadata={
                    'integration_name': 'asknicely',
                    'domain': self.domain,
                    'nps': response.get('nps')
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"AskNicely connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # PEOPLE API
    # ===================================================================

    async def list_people(
        self,
        page: int = 1,
        per_page: int = 100,
        segment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List people (contacts).

        Args:
            page: Page number
            per_page: Results per page (max: 100)
            segment: Filter by segment (promoters, passives, detractors)

        Returns:
            Paginated list of people

        Example:
            >>> people = await asknicely.list_people(
            ...     page=1,
            ...     per_page=50,
            ...     segment="promoters"
            ... )
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }

        if segment:
            params['segment'] = segment

        result = await self._make_request(
            method='GET',
            endpoint='/people',
            params=params
        )

        logger.info(
            "asknicely_people_listed",
            count=len(result.get('people', [])) if isinstance(result, dict) else 0,
            segment=segment
        )

        return result

    async def get_person(self, person_id: str) -> Dict[str, Any]:
        """
        Get person by ID or email.

        Args:
            person_id: Person ID or email

        Returns:
            Person details with response history
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/people/{person_id}'
        )

    async def create_person(
        self,
        email: str,
        name: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        send_survey: bool = False
    ) -> Dict[str, Any]:
        """
        Create a person and optionally send survey.

        Args:
            email: Person email
            name: Person name
            custom_fields: Custom fields (company, plan, segment, etc.)
            send_survey: Send survey immediately

        Returns:
            Created person data

        Example:
            >>> person = await asknicely.create_person(
            ...     email="jane@acme.com",
            ...     name="Jane Doe",
            ...     custom_fields={
            ...         "company": "Acme Corp",
            ...         "plan": "Enterprise",
            ...         "industry": "Technology"
            ...     },
            ...     send_survey=True
            ... )
        """
        data = {'email': email}

        if name:
            data['name'] = name
        if custom_fields:
            # AskNicely uses flat structure for custom fields
            data.update(custom_fields)
        if send_survey:
            data['send'] = 'true'

        result = await self._make_request(
            method='POST',
            endpoint='/people',
            data=data
        )

        logger.info(
            "asknicely_person_created",
            person_id=result.get('id'),
            email=email,
            send_survey=send_survey
        )

        return result

    async def update_person(
        self,
        person_id: str,
        custom_fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update person custom fields.

        Args:
            person_id: Person ID or email
            custom_fields: Fields to update

        Returns:
            Updated person data

        Example:
            >>> await asknicely.update_person(
            ...     person_id="jane@acme.com",
            ...     custom_fields={"plan": "Growth", "mrr": 499}
            ... )
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/people/{person_id}',
            data=custom_fields
        )

        logger.info(
            "asknicely_person_updated",
            person_id=person_id
        )

        return result

    async def delete_person(self, person_id: str) -> Dict[str, Any]:
        """
        Delete a person.

        Args:
            person_id: Person ID or email

        Returns:
            Deletion confirmation
        """
        result = await self._make_request(
            method='DELETE',
            endpoint=f'/people/{person_id}'
        )

        logger.info(
            "asknicely_person_deleted",
            person_id=person_id
        )

        return result

    # ===================================================================
    # RESPONSES API
    # ===================================================================

    async def list_responses(
        self,
        page: int = 1,
        per_page: int = 100,
        since: Optional[str] = None,
        until: Optional[str] = None,
        score_min: Optional[int] = None,
        score_max: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        List survey responses.

        Args:
            page: Page number
            per_page: Results per page (max: 100)
            since: Filter by date (ISO format)
            until: Filter by date (ISO format)
            score_min: Minimum score filter
            score_max: Maximum score filter

        Returns:
            Paginated list of responses

        Example:
            >>> # Get detractor responses
            >>> responses = await asknicely.list_responses(
            ...     score_min=0,
            ...     score_max=6,
            ...     per_page=100
            ... )
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }

        if since:
            params['since'] = since
        if until:
            params['until'] = until
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
            "asknicely_responses_listed",
            count=len(result.get('responses', [])) if isinstance(result, dict) else 0
        )

        return result

    async def get_response(self, response_id: str) -> Dict[str, Any]:
        """
        Get response by ID.

        Args:
            response_id: Response ID

        Returns:
            Response details with score, comment, and metadata
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/responses/{response_id}'
        )

    async def create_response(
        self,
        email: str,
        score: int,
        comment: Optional[str] = None,
        sent_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a response (for importing historical data).

        Args:
            email: Person email
            score: NPS score (0-10)
            comment: Response comment
            sent_at: Survey sent timestamp (ISO format)

        Returns:
            Created response

        Example:
            >>> response = await asknicely.create_response(
            ...     email="jane@acme.com",
            ...     score=9,
            ...     comment="Great service, very responsive team!",
            ...     sent_at="2024-10-15T10:00:00Z"
            ... )
        """
        data = {
            'email': email,
            'score': score
        }

        if comment:
            data['comment'] = comment
        if sent_at:
            data['sent'] = sent_at

        result = await self._make_request(
            method='POST',
            endpoint='/responses',
            data=data
        )

        logger.info(
            "asknicely_response_created",
            response_id=result.get('id'),
            email=email,
            score=score
        )

        return result

    # ===================================================================
    # METRICS API
    # ===================================================================

    async def get_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        segment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get NPS metrics and breakdown.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            segment: Filter by segment

        Returns:
            NPS metrics with score and distribution

        Example:
            >>> metrics = await asknicely.get_metrics(
            ...     start_date="2024-01-01",
            ...     end_date="2024-12-31"
            ... )
            >>> print(f"NPS: {metrics['nps']}")
            >>> print(f"Promoters: {metrics['promoters']}%")
            >>> print(f"Responses: {metrics['response_count']}")
        """
        params = {}

        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if segment:
            params['segment'] = segment

        return await self._make_request(
            method='GET',
            endpoint='/metrics',
            params=params
        )

    async def get_nps_score(self) -> int:
        """
        Get current NPS score.

        Returns:
            NPS score (-100 to 100)

        Example:
            >>> nps = await asknicely.get_nps_score()
            >>> print(f"Current NPS: {nps}")
        """
        metrics = await self.get_metrics()
        return metrics.get('nps', 0)

    async def get_dashboard(self) -> Dict[str, Any]:
        """
        Get dashboard summary with key metrics.

        Returns:
            Dashboard data with NPS, response rate, trends

        Example:
            >>> dashboard = await asknicely.get_dashboard()
            >>> print(f"NPS: {dashboard['nps']}")
            >>> print(f"Response Rate: {dashboard['response_rate']}%")
            >>> print(f"Trend: {dashboard['trend']}")
        """
        return await self._make_request(
            method='GET',
            endpoint='/dashboard'
        )

    # ===================================================================
    # TRENDS API
    # ===================================================================

    async def get_trends(
        self,
        period: str = "month",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get NPS trends over time.

        Args:
            period: Trend period (day, week, month, quarter)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Time series NPS data

        Example:
            >>> trends = await asknicely.get_trends(
            ...     period="month",
            ...     start_date="2024-01-01"
            ... )
            >>> for point in trends['data']:
            ...     print(f"{point['date']}: {point['nps']}")
        """
        params = {'period': period}

        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint='/trends',
            params=params
        )

    # ===================================================================
    # SEGMENTS API
    # ===================================================================

    async def get_segment_scores(
        self,
        segment_by: str = "plan"
    ) -> Dict[str, Any]:
        """
        Get NPS scores by segment.

        Args:
            segment_by: Segment field (plan, company, industry, etc.)

        Returns:
            NPS scores grouped by segment

        Example:
            >>> segments = await asknicely.get_segment_scores(
            ...     segment_by="plan"
            ... )
            >>> for segment in segments['segments']:
            ...     print(f"{segment['name']}: {segment['nps']}")
        """
        params = {'segment_by': segment_by}

        return await self._make_request(
            method='GET',
            endpoint='/segments',
            params=params
        )

    # ===================================================================
    # SURVEYS API
    # ===================================================================

    async def send_survey(
        self,
        email: str,
        name: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send survey to a person.

        Args:
            email: Person email
            name: Person name
            custom_fields: Custom fields to include

        Returns:
            Send confirmation

        Example:
            >>> await asknicely.send_survey(
            ...     email="jane@acme.com",
            ...     name="Jane Doe",
            ...     custom_fields={"company": "Acme Corp"}
            ... )
        """
        data = {
            'email': email,
            'send': 'true'
        }

        if name:
            data['name'] = name
        if custom_fields:
            data.update(custom_fields)

        result = await self._make_request(
            method='POST',
            endpoint='/people',
            data=data
        )

        logger.info(
            "asknicely_survey_sent",
            email=email
        )

        return result

    async def send_bulk_surveys(
        self,
        people: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send surveys to multiple people.

        Args:
            people: List of people with email, name, and custom fields

        Returns:
            Bulk send confirmation

        Example:
            >>> await asknicely.send_bulk_surveys([
            ...     {
            ...         "email": "jane@acme.com",
            ...         "name": "Jane Doe",
            ...         "company": "Acme Corp"
            ...     },
            ...     {
            ...         "email": "john@acme.com",
            ...         "name": "John Smith",
            ...         "company": "Acme Corp"
            ...     }
            ... ])
        """
        data = {'people': people}

        result = await self._make_request(
            method='POST',
            endpoint='/people/bulk',
            data=data
        )

        logger.info(
            "asknicely_bulk_surveys_sent",
            count=len(people)
        )

        return result

    # ===================================================================
    # COMMENTS API
    # ===================================================================

    async def get_comments(
        self,
        page: int = 1,
        per_page: int = 100,
        score_min: Optional[int] = None,
        score_max: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get responses with comments.

        Args:
            page: Page number
            per_page: Results per page (max: 100)
            score_min: Minimum score filter
            score_max: Maximum score filter

        Returns:
            Responses with comments

        Example:
            >>> # Get detractor comments
            >>> comments = await asknicely.get_comments(
            ...     score_min=0,
            ...     score_max=6
            ... )
            >>> for comment in comments['responses']:
            ...     print(f"{comment['email']}: {comment['comment']}")
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100),
            'has_comment': 'true'
        }

        if score_min is not None:
            params['score_min'] = score_min
        if score_max is not None:
            params['score_max'] = score_max

        return await self._make_request(
            method='GET',
            endpoint='/responses',
            params=params
        )

    # ===================================================================
    # RESPONSE RATE API
    # ===================================================================

    async def get_response_rate(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get survey response rate statistics.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Response rate metrics

        Example:
            >>> stats = await asknicely.get_response_rate()
            >>> print(f"Response rate: {stats['rate']}%")
            >>> print(f"Sent: {stats['sent']}")
            >>> print(f"Responses: {stats['responses']}")
        """
        params = {}

        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint='/response_rate',
            params=params
        )

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("asknicely_session_closed")
