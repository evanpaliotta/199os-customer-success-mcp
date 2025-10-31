"""
Wootric Integration
Priority Score: 10
ICP Adoption: 30-40% of customer-centric SaaS companies

Customer experience management platform providing:
- NPS/CSAT/CES Surveys
- Response Management
- End Users
- Survey Settings
- Metrics and Analytics
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


class WootricIntegration(BaseIntegration):
    """
    Wootric API integration with API key authentication.

    Authentication:
    - API Token in header (Authorization: Bearer <token>)
    - Client ID and Secret for OAuth flows

    Rate Limits:
    - 100 requests per minute
    - Burst: 20 requests per second

    Documentation: https://docs.wootric.com/api/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 90,
        rate_limit_window: int = 60
    ) -> Any:
        """
        Initialize Wootric integration.

        Args:
            credentials: Wootric credentials
                - api_token: Wootric API token
                - account_token: Wootric account token
            rate_limit_calls: Max API calls per window (default: 90)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="wootric",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_token = credentials.get('api_token', '')
        self.account_token = credentials.get('account_token', '')

        if not self.api_token:
            raise ValidationError("Wootric api_token is required")
        if not self.account_token:
            raise ValidationError("Wootric account_token is required")

        self.base_url = "https://api.wootric.com/v1"

        logger.info(
            "wootric_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Wootric (API token validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("wootric_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Wootric authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make authenticated HTTP request to Wootric API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Add account token to params
        if params is None:
            params = {}
        params['account_token'] = self.account_token

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
                        f"Wootric API error ({response.status}): {error_text}",
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
        """Test connection to Wootric API."""
        try:
            start_time = datetime.now()

            # Test with end users list request
            response = await self._make_request(
                method='GET',
                endpoint='/end_users',
                params={'per_page': 1}
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Wootric",
                response_time_ms=duration_ms,
                metadata={
                    'integration_name': 'wootric',
                    'account_token': self.account_token[:8] + '...'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Wootric connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # END USERS API
    # ===================================================================

    async def list_end_users(
        self,
        page: int = 1,
        per_page: int = 50,
        created_after: Optional[int] = None,
        updated_after: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List end users (contacts/customers).

        Args:
            page: Page number
            per_page: Results per page (max: 100)
            created_after: Filter by created timestamp (Unix)
            updated_after: Filter by updated timestamp (Unix)

        Returns:
            List of end users

        Example:
            >>> users = await wootric.list_end_users(
            ...     page=1,
            ...     per_page=50
            ... )
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }

        if created_after:
            params['created[gt]'] = created_after
        if updated_after:
            params['updated[gt]'] = updated_after

        result = await self._make_request(
            method='GET',
            endpoint='/end_users',
            params=params
        )

        logger.info(
            "wootric_end_users_listed",
            count=len(result) if isinstance(result, list) else 0
        )

        return result if isinstance(result, list) else []

    async def get_end_user(self, user_id: int) -> Dict[str, Any]:
        """
        Get end user by ID.

        Args:
            user_id: End user ID

        Returns:
            End user details
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/end_users/{user_id}'
        )

    async def create_end_user(
        self,
        email: str,
        created_at: Optional[int] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an end user.

        Args:
            email: User email
            created_at: User creation timestamp (Unix, defaults to now)
            properties: Custom properties (e.g., name, plan, company)

        Returns:
            Created end user data

        Example:
            >>> user = await wootric.create_end_user(
            ...     email="jane@acme.com",
            ...     properties={
            ...         "first_name": "Jane",
            ...         "last_name": "Doe",
            ...         "company": "Acme Corp",
            ...         "plan": "Enterprise"
            ...     }
            ... )
        """
        data = {'email': email}

        if created_at:
            data['created_at'] = created_at
        if properties:
            data['properties'] = properties

        result = await self._make_request(
            method='POST',
            endpoint='/end_users',
            data=data
        )

        logger.info(
            "wootric_end_user_created",
            user_id=result.get('id'),
            email=email
        )

        return result

    async def update_end_user(
        self,
        user_id: int,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update end user properties.

        Args:
            user_id: End user ID
            properties: Properties to update

        Returns:
            Updated end user data

        Example:
            >>> await wootric.update_end_user(
            ...     user_id=12345,
            ...     properties={"plan": "Growth", "mrr": 499}
            ... )
        """
        data = {'properties': properties}

        result = await self._make_request(
            method='PUT',
            endpoint=f'/end_users/{user_id}',
            data=data
        )

        logger.info(
            "wootric_end_user_updated",
            user_id=user_id
        )

        return result

    async def delete_end_user(self, user_id: int) -> Dict[str, Any]:
        """
        Delete an end user.

        Args:
            user_id: End user ID

        Returns:
            Deletion confirmation
        """
        result = await self._make_request(
            method='DELETE',
            endpoint=f'/end_users/{user_id}'
        )

        logger.info(
            "wootric_end_user_deleted",
            user_id=user_id
        )

        return result

    # ===================================================================
    # RESPONSES API
    # ===================================================================

    async def list_responses(
        self,
        page: int = 1,
        per_page: int = 50,
        created_after: Optional[int] = None,
        updated_after: Optional[int] = None,
        survey_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List survey responses.

        Args:
            page: Page number
            per_page: Results per page (max: 100)
            created_after: Filter by created timestamp (Unix)
            updated_after: Filter by updated timestamp (Unix)
            survey_type: Filter by survey type (nps, csat, ces)

        Returns:
            List of survey responses

        Example:
            >>> responses = await wootric.list_responses(
            ...     survey_type="nps",
            ...     per_page=100
            ... )
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100)
        }

        if created_after:
            params['created[gt]'] = created_after
        if updated_after:
            params['updated[gt]'] = updated_after
        if survey_type:
            params['survey_type'] = survey_type

        result = await self._make_request(
            method='GET',
            endpoint='/responses',
            params=params
        )

        logger.info(
            "wootric_responses_listed",
            count=len(result) if isinstance(result, list) else 0,
            survey_type=survey_type
        )

        return result if isinstance(result, list) else []

    async def get_response(self, response_id: int) -> Dict[str, Any]:
        """
        Get survey response by ID.

        Args:
            response_id: Response ID

        Returns:
            Survey response details with score, text, and metadata
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/responses/{response_id}'
        )

    async def create_response(
        self,
        end_user_id: int,
        score: int,
        survey_type: str = "nps",
        text: Optional[str] = None,
        created_at: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a survey response (for importing historical data).

        Args:
            end_user_id: End user ID
            score: Survey score (NPS: 0-10, CSAT: 1-5, CES: 1-7)
            survey_type: Survey type (nps, csat, ces)
            text: Response text/comment
            created_at: Response timestamp (Unix, defaults to now)
            tags: Response tags for categorization

        Returns:
            Created survey response

        Example:
            >>> response = await wootric.create_response(
            ...     end_user_id=12345,
            ...     score=9,
            ...     survey_type="nps",
            ...     text="Great product, love the new features!",
            ...     tags=["feature_request", "positive"]
            ... )
        """
        data = {
            'end_user_id': end_user_id,
            'score': score,
            'survey_type': survey_type
        }

        if text:
            data['text'] = text
        if created_at:
            data['created_at'] = created_at
        if tags:
            data['tags'] = tags

        result = await self._make_request(
            method='POST',
            endpoint='/responses',
            data=data
        )

        logger.info(
            "wootric_response_created",
            response_id=result.get('id'),
            score=score,
            survey_type=survey_type
        )

        return result

    async def update_response(
        self,
        response_id: int,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update survey response (tags and notes only).

        Args:
            response_id: Response ID
            tags: Updated tags
            notes: Internal notes about the response

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
            "wootric_response_updated",
            response_id=response_id
        )

        return result

    # ===================================================================
    # METRICS API
    # ===================================================================

    async def get_metrics(
        self,
        survey_type: str = "nps",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get survey metrics and scores.

        Args:
            survey_type: Survey type (nps, csat, ces)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Metrics with scores, trends, and breakdowns

        Example:
            >>> metrics = await wootric.get_metrics(
            ...     survey_type="nps",
            ...     start_date="2024-01-01",
            ...     end_date="2024-12-31"
            ... )
            >>> print(f"NPS: {metrics['score']}")
            >>> print(f"Promoters: {metrics['promoters_percentage']}%")
        """
        params = {'survey_type': survey_type}

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
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get NPS score and breakdown.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            NPS score with promoters, passives, detractors breakdown

        Example:
            >>> nps = await wootric.get_nps_score()
            >>> print(f"Score: {nps['score']}")
            >>> print(f"Responses: {nps['response_count']}")
        """
        return await self.get_metrics(
            survey_type="nps",
            start_date=start_date,
            end_date=end_date
        )

    async def get_csat_score(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get CSAT score and breakdown.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            CSAT score with satisfaction breakdown
        """
        return await self.get_metrics(
            survey_type="csat",
            start_date=start_date,
            end_date=end_date
        )

    async def get_ces_score(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get CES (Customer Effort Score) and breakdown.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            CES score with effort breakdown
        """
        return await self.get_metrics(
            survey_type="ces",
            start_date=start_date,
            end_date=end_date
        )

    # ===================================================================
    # SURVEY SETTINGS API
    # ===================================================================

    async def list_surveys(self) -> List[Dict[str, Any]]:
        """
        List all survey configurations.

        Returns:
            List of survey settings

        Example:
            >>> surveys = await wootric.list_surveys()
            >>> for survey in surveys:
            ...     print(f"{survey['name']}: {survey['survey_type']}")
        """
        result = await self._make_request(
            method='GET',
            endpoint='/settings/surveys'
        )

        return result if isinstance(result, list) else []

    async def get_survey_settings(self, survey_id: int) -> Dict[str, Any]:
        """
        Get survey settings by ID.

        Args:
            survey_id: Survey ID

        Returns:
            Survey configuration settings
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/settings/surveys/{survey_id}'
        )

    async def update_survey_settings(
        self,
        survey_id: int,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update survey settings.

        Args:
            survey_id: Survey ID
            settings: Settings to update (e.g., threshold, language, frequency)

        Returns:
            Updated survey settings

        Example:
            >>> await wootric.update_survey_settings(
            ...     survey_id=123,
            ...     settings={
            ...         "language": "en",
            ...         "first_survey_delay": 30,
            ...         "time_between_surveys": 90
            ...     }
            ... )
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/settings/surveys/{survey_id}',
            data=settings
        )

        logger.info(
            "wootric_survey_settings_updated",
            survey_id=survey_id
        )

        return result

    # ===================================================================
    # ANALYTICS API
    # ===================================================================

    async def get_trends(
        self,
        survey_type: str = "nps",
        period: str = "month",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get score trends over time.

        Args:
            survey_type: Survey type (nps, csat, ces)
            period: Trend period (day, week, month, quarter)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Time series trend data

        Example:
            >>> trends = await wootric.get_trends(
            ...     survey_type="nps",
            ...     period="month",
            ...     start_date="2024-01-01",
            ...     end_date="2024-12-31"
            ... )
            >>> for point in trends['data']:
            ...     print(f"{point['date']}: {point['score']}")
        """
        params = {
            'survey_type': survey_type,
            'period': period
        }

        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint='/analytics/trends',
            params=params
        )

    async def get_segment_analysis(
        self,
        survey_type: str = "nps",
        segment_by: str = "plan",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get score breakdown by segment.

        Args:
            survey_type: Survey type (nps, csat, ces)
            segment_by: Segment property (plan, company, country, etc.)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Segmented score analysis

        Example:
            >>> segments = await wootric.get_segment_analysis(
            ...     survey_type="nps",
            ...     segment_by="plan"
            ... )
            >>> for segment in segments['segments']:
            ...     print(f"{segment['value']}: {segment['score']}")
        """
        params = {
            'survey_type': survey_type,
            'segment_by': segment_by
        }

        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint='/analytics/segments',
            params=params
        )

    async def get_response_rate(
        self,
        survey_type: str = "nps",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get survey response rate statistics.

        Args:
            survey_type: Survey type (nps, csat, ces)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Response rate metrics

        Example:
            >>> stats = await wootric.get_response_rate(
            ...     survey_type="nps"
            ... )
            >>> print(f"Response rate: {stats['rate']}%")
            >>> print(f"Surveys sent: {stats['sent']}")
            >>> print(f"Responses: {stats['responses']}")
        """
        params = {'survey_type': survey_type}

        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint='/analytics/response_rate',
            params=params
        )

    # ===================================================================
    # SENTIMENT ANALYSIS
    # ===================================================================

    async def get_sentiment_analysis(
        self,
        survey_type: str = "nps",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get sentiment analysis from response text.

        Args:
            survey_type: Survey type (nps, csat, ces)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Sentiment analysis with themes and keywords

        Example:
            >>> sentiment = await wootric.get_sentiment_analysis(
            ...     survey_type="nps"
            ... )
            >>> print(f"Positive: {sentiment['positive_percentage']}%")
            >>> print(f"Top themes: {sentiment['themes']}")
        """
        params = {'survey_type': survey_type}

        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint='/analytics/sentiment',
            params=params
        )

    async def get_text_themes(
        self,
        survey_type: str = "nps",
        min_responses: int = 5
    ) -> Dict[str, Any]:
        """
        Get common themes from response text.

        Args:
            survey_type: Survey type (nps, csat, ces)
            min_responses: Minimum responses to form a theme

        Returns:
            Common themes with frequency and examples

        Example:
            >>> themes = await wootric.get_text_themes(
            ...     survey_type="nps",
            ...     min_responses=10
            ... )
            >>> for theme in themes['themes']:
            ...     print(f"{theme['name']}: {theme['count']} mentions")
        """
        params = {
            'survey_type': survey_type,
            'min_responses': min_responses
        }

        return await self._make_request(
            method='GET',
            endpoint='/analytics/themes',
            params=params
        )

    async def close(self) -> Any:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("wootric_session_closed")
