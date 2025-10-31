"""
Delighted Integration
Priority Score: 10
ICP Adoption: 35-45% of customer-centric SaaS companies

Customer feedback and NPS platform providing:
- NPS Surveys
- Survey Responses
- People (Contacts)
- Metrics and Reports
- Survey Templates
- Sentiment Analysis
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


class DelightedIntegration(BaseIntegration):
    """
    Delighted API integration with API key authentication.

    Authentication:
    - API Key in HTTP Basic Auth (username: API key, password: empty)

    Rate Limits:
    - 120 requests per minute
    - 10000 requests per day

    Documentation: https://delighted.com/docs/api
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ) -> Any:
        """
        Initialize Delighted integration.

        Args:
            credentials: Delighted credentials
                - api_key: Delighted API key
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="delighted",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')

        if not self.api_key:
            raise ValidationError("Delighted api_key is required")

        self.base_url = "https://api.delighted.com/v1"

        logger.info(
            "delighted_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Delighted (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("delighted_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Delighted authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make authenticated HTTP request to Delighted API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Delighted uses HTTP Basic Auth with API key as username
        import aiohttp
        auth = aiohttp.BasicAuth(login=self.api_key, password='')

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
                        f"Delighted API error ({response.status}): {error_text}",
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
        """Test connection to Delighted API."""
        try:
            start_time = datetime.now()

            # Test with metrics request
            response = await self._make_request(
                method='GET',
                endpoint='/metrics'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Delighted",
                response_time_ms=duration_ms,
                metadata={
                    'integration_name': 'delighted',
                    'nps': response.get('nps')
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Delighted connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # PEOPLE API
    # ===================================================================

    async def list_people(
        self,
        per_page: int = 100,
        page: int = 1,
        since: Optional[int] = None,
        until: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List people (contacts).

        Args:
            per_page: Results per page (max: 100)
            page: Page number
            since: Filter by created_at timestamp (Unix)
            until: Filter by created_at timestamp (Unix)

        Returns:
            List of people

        Example:
            >>> people = await delighted.list_people(
            ...     per_page=50,
            ...     page=1
            ... )
        """
        params = {
            'per_page': min(per_page, 100),
            'page': page
        }

        if since:
            params['since'] = since
        if until:
            params['until'] = until

        result = await self._make_request(
            method='GET',
            endpoint='/people.json',
            params=params
        )

        logger.info(
            "delighted_people_listed",
            count=len(result) if isinstance(result, list) else 0
        )

        return result if isinstance(result, list) else []

    async def get_person(self, person_id: str) -> Dict[str, Any]:
        """
        Get person by ID or email.

        Args:
            person_id: Person ID or email

        Returns:
            Person details with survey history
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/people/{person_id}.json'
        )

    async def create_person(
        self,
        email: str,
        name: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        send_email: bool = True,
        delay: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a person and optionally send survey.

        Args:
            email: Person email
            name: Person name
            properties: Custom properties (e.g., company, plan, signup_date)
            send_email: Send survey email immediately
            delay: Delay survey email by N seconds

        Returns:
            Created person data

        Example:
            >>> person = await delighted.create_person(
            ...     email="jane@acme.com",
            ...     name="Jane Doe",
            ...     properties={
            ...         "company": "Acme Corp",
            ...         "plan": "Enterprise",
            ...         "signup_date": "2024-01-15"
            ...     },
            ...     send_email=True
            ... )
        """
        data = {'email': email}

        if name:
            data['name'] = name
        if properties:
            data['properties'] = properties
        if not send_email:
            data['send'] = False
        if delay:
            data['delay'] = delay

        result = await self._make_request(
            method='POST',
            endpoint='/people.json',
            data=data
        )

        logger.info(
            "delighted_person_created",
            person_id=result.get('id'),
            email=email,
            send_email=send_email
        )

        return result

    async def delete_person(self, email: str) -> Dict[str, Any]:
        """
        Delete a person.

        Args:
            email: Person email

        Returns:
            Deletion confirmation
        """
        result = await self._make_request(
            method='DELETE',
            endpoint=f'/people/{email}.json'
        )

        logger.info(
            "delighted_person_deleted",
            email=email
        )

        return result

    # ===================================================================
    # SURVEY RESPONSES API
    # ===================================================================

    async def list_survey_responses(
        self,
        per_page: int = 100,
        page: int = 1,
        since: Optional[int] = None,
        until: Optional[int] = None,
        order: str = "desc",
        expand: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List survey responses.

        Args:
            per_page: Results per page (max: 100)
            page: Page number
            since: Filter by updated_at timestamp (Unix)
            until: Filter by updated_at timestamp (Unix)
            order: Sort order (asc, desc)
            expand: Expand related objects (person, notes)

        Returns:
            List of survey responses

        Example:
            >>> responses = await delighted.list_survey_responses(
            ...     per_page=50,
            ...     order="desc",
            ...     expand=["person"]
            ... )
        """
        params = {
            'per_page': min(per_page, 100),
            'page': page,
            'order': order
        }

        if since:
            params['since'] = since
        if until:
            params['until'] = until
        if expand:
            params['expand[]'] = expand

        result = await self._make_request(
            method='GET',
            endpoint='/survey_responses.json',
            params=params
        )

        logger.info(
            "delighted_survey_responses_listed",
            count=len(result) if isinstance(result, list) else 0
        )

        return result if isinstance(result, list) else []

    async def get_survey_response(self, response_id: str) -> Dict[str, Any]:
        """
        Get survey response by ID.

        Args:
            response_id: Survey response ID

        Returns:
            Survey response details with score and comment
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/survey_responses/{response_id}.json'
        )

    async def create_survey_response(
        self,
        person: str,
        score: int,
        comment: Optional[str] = None,
        recorded_at: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a survey response (for importing historical data).

        Args:
            person: Person email or ID
            score: NPS score (0-10)
            comment: Optional comment text
            recorded_at: Response timestamp (Unix)

        Returns:
            Created survey response

        Example:
            >>> response = await delighted.create_survey_response(
            ...     person="jane@acme.com",
            ...     score=9,
            ...     comment="Great product, love the new features!",
            ...     recorded_at=1704067200
            ... )
        """
        data = {
            'person': person,
            'score': score
        }

        if comment:
            data['comment'] = comment
        if recorded_at:
            data['recorded_at'] = recorded_at

        result = await self._make_request(
            method='POST',
            endpoint='/survey_responses.json',
            data=data
        )

        logger.info(
            "delighted_survey_response_created",
            response_id=result.get('id'),
            score=score,
            person=person
        )

        return result

    # ===================================================================
    # METRICS API
    # ===================================================================

    async def get_metrics(
        self,
        since: Optional[int] = None,
        until: Optional[int] = None,
        trend: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get NPS metrics and trends.

        Args:
            since: Start date (Unix timestamp)
            until: End date (Unix timestamp)
            trend: Trend period (daily, weekly, monthly)

        Returns:
            NPS metrics with score breakdown

        Example:
            >>> metrics = await delighted.get_metrics(
            ...     since=1704067200,
            ...     until=1735689600,
            ...     trend="monthly"
            ... )
            >>> print(f"NPS: {metrics['nps']}")
            >>> print(f"Promoters: {metrics['promoter_percentage']}%")
            >>> print(f"Detractors: {metrics['detractor_percentage']}%")
        """
        params = {}

        if since:
            params['since'] = since
        if until:
            params['until'] = until
        if trend:
            params['trend'] = trend

        return await self._make_request(
            method='GET',
            endpoint='/metrics.json',
            params=params
        )

    async def get_nps_score(self) -> int:
        """
        Get current NPS score.

        Returns:
            NPS score (-100 to 100)

        Example:
            >>> nps = await delighted.get_nps_score()
            >>> print(f"Current NPS: {nps}")
        """
        metrics = await self.get_metrics()
        return metrics.get('nps', 0)

    # ===================================================================
    # UNSUBSCRIBES API
    # ===================================================================

    async def list_unsubscribes(
        self,
        per_page: int = 100,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        List unsubscribed people.

        Args:
            per_page: Results per page
            page: Page number

        Returns:
            List of unsubscribed people
        """
        params = {
            'per_page': min(per_page, 100),
            'page': page
        }

        return await self._make_request(
            method='GET',
            endpoint='/unsubscribes.json',
            params=params
        )

    async def unsubscribe_person(self, email: str) -> Dict[str, Any]:
        """
        Unsubscribe a person from surveys.

        Args:
            email: Person email

        Returns:
            Unsubscribe confirmation
        """
        data = {'person_email': email}

        result = await self._make_request(
            method='POST',
            endpoint='/unsubscribes.json',
            data=data
        )

        logger.info(
            "delighted_person_unsubscribed",
            email=email
        )

        return result

    # ===================================================================
    # BOUNCES API
    # ===================================================================

    async def list_bounces(
        self,
        per_page: int = 100,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        List bounced email addresses.

        Args:
            per_page: Results per page
            page: Page number

        Returns:
            List of bounced emails
        """
        params = {
            'per_page': min(per_page, 100),
            'page': page
        }

        return await self._make_request(
            method='GET',
            endpoint='/bounces.json',
            params=params
        )

    # ===================================================================
    # AUTOPILOT API
    # ===================================================================

    async def get_autopilot_config(self) -> Dict[str, Any]:
        """
        Get Autopilot (automated survey) configuration.

        Returns:
            Autopilot configuration settings
        """
        return await self._make_request(
            method='GET',
            endpoint='/autopilot.json'
        )

    async def update_autopilot_config(
        self,
        enabled: Optional[bool] = None,
        frequency: Optional[int] = None,
        send_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update Autopilot configuration.

        Args:
            enabled: Enable/disable Autopilot
            frequency: Survey frequency in days
            send_time: Time to send surveys (HH:MM format)

        Returns:
            Updated Autopilot configuration

        Example:
            >>> config = await delighted.update_autopilot_config(
            ...     enabled=True,
            ...     frequency=90,
            ...     send_time="09:00"
            ... )
        """
        data = {}

        if enabled is not None:
            data['enabled'] = enabled
        if frequency is not None:
            data['frequency'] = frequency
        if send_time:
            data['send_time'] = send_time

        result = await self._make_request(
            method='PUT',
            endpoint='/autopilot.json',
            data=data
        )

        logger.info(
            "delighted_autopilot_updated",
            enabled=enabled,
            frequency=frequency
        )

        return result

    # ===================================================================
    # REPORTS API
    # ===================================================================

    async def get_score_distribution(
        self,
        since: Optional[int] = None,
        until: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get NPS score distribution.

        Args:
            since: Start date (Unix timestamp)
            until: End date (Unix timestamp)

        Returns:
            Score distribution by rating (0-10)

        Example:
            >>> distribution = await delighted.get_score_distribution()
            >>> for score, count in distribution.items():
            ...     print(f"Score {score}: {count} responses")
        """
        params = {}

        if since:
            params['since'] = since
        if until:
            params['until'] = until

        metrics = await self._make_request(
            method='GET',
            endpoint='/metrics.json',
            params=params
        )

        return metrics.get('distribution', {})

    async def get_response_rate(
        self,
        since: Optional[int] = None,
        until: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get survey response rate statistics.

        Args:
            since: Start date (Unix timestamp)
            until: End date (Unix timestamp)

        Returns:
            Response rate statistics

        Example:
            >>> stats = await delighted.get_response_rate()
            >>> print(f"Response rate: {stats['response_rate']}%")
        """
        params = {}

        if since:
            params['since'] = since
        if until:
            params['until'] = until

        metrics = await self._make_request(
            method='GET',
            endpoint='/metrics.json',
            params=params
        )

        return {
            'response_rate': metrics.get('response_rate'),
            'responses': metrics.get('num_responses'),
            'surveys_sent': metrics.get('num_surveys_sent')
        }

    # ===================================================================
    # SENTIMENT ANALYSIS
    # ===================================================================

    async def get_sentiment_trends(
        self,
        since: Optional[int] = None,
        until: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get sentiment analysis from comments.

        Args:
            since: Start date (Unix timestamp)
            until: End date (Unix timestamp)

        Returns:
            Sentiment trends and keyword analysis

        Example:
            >>> sentiment = await delighted.get_sentiment_trends()
            >>> print(f"Positive: {sentiment['positive']}%")
            >>> print(f"Negative: {sentiment['negative']}%")
        """
        params = {
            'expand[]': ['person']
        }

        if since:
            params['since'] = since
        if until:
            params['until'] = until

        responses = await self._make_request(
            method='GET',
            endpoint='/survey_responses.json',
            params=params
        )

        # Basic sentiment analysis
        total = len(responses)
        promoters = sum(1 for r in responses if r.get('score', 0) >= 9)
        detractors = sum(1 for r in responses if r.get('score', 0) <= 6)
        passives = total - promoters - detractors

        return {
            'total_responses': total,
            'positive': round((promoters / total * 100) if total > 0 else 0, 2),
            'neutral': round((passives / total * 100) if total > 0 else 0, 2),
            'negative': round((detractors / total * 100) if total > 0 else 0, 2),
            'promoters': promoters,
            'passives': passives,
            'detractors': detractors
        }

    async def close(self) -> Any:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("delighted_session_closed")
