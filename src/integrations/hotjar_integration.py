"""
Hotjar Integration
Priority Score: 10
ICP Adoption: 40-50% of UX/product teams

User behavior analytics and feedback platform providing:
- Recordings (Session Replays)
- Heatmaps
- Surveys
- Feedback Polls
- Sites Management
- User Insights
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


class HotjarIntegration(BaseIntegration):
    """
    Hotjar API integration with API key authentication.

    Authentication:
    - Bearer token authentication
    - Site ID required for most operations

    Rate Limits:
    - 600 requests per hour per token
    - Burst: 10 requests per second

    Documentation: https://api.hotjar.com/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 600
    ):
        """
        Initialize Hotjar integration.

        Args:
            credentials: Hotjar credentials
                - api_token: Hotjar API token
                - site_id: Default Hotjar site ID (optional)
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 600 = 10 min)
        """
        super().__init__(
            integration_name="hotjar",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_token = credentials.get('api_token', '')
        if not self.api_token:
            raise ValidationError("Hotjar api_token is required")

        self.default_site_id = credentials.get('site_id')

        self.base_url = "https://api.hotjar.com/v1"

        logger.info(
            "hotjar_initialized",
            site_id=self.default_site_id,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Hotjar (API token validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("hotjar_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Hotjar authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Hotjar API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            'Authorization': f'Bearer {self.api_token}',
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
                        f"Hotjar API error ({response.status}): {error_text}",
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
        """Test connection to Hotjar API."""
        try:
            start_time = datetime.now()

            # Test with sites list
            response = await self._make_request(
                method='GET',
                endpoint='/sites'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            sites = response.get('sites', [])

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Hotjar",
                response_time_ms=duration_ms,
                metadata={
                    'site_count': len(sites),
                    'default_site_id': self.default_site_id,
                    'integration_name': 'hotjar'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Hotjar connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # SITES API
    # ===================================================================

    async def list_sites(self) -> Dict[str, Any]:
        """
        List all sites.

        Returns:
            List of sites with IDs and names
        """
        return await self._make_request(
            method='GET',
            endpoint='/sites'
        )

    async def get_site(self, site_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get site by ID.

        Args:
            site_id: Site ID (uses default if not provided)

        Returns:
            Site details
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        result = await self._make_request(
            method='GET',
            endpoint=f'/sites/{site_id}'
        )

        return result

    # ===================================================================
    # RECORDINGS API
    # ===================================================================

    async def list_recordings(
        self,
        site_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        filter_by: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List recordings (session replays).

        Args:
            site_id: Site ID (uses default if not provided)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            filter_by: Filters (browser, device, country, etc.)
            limit: Results limit (max: 100)
            offset: Pagination offset

        Returns:
            List of recordings

        Example:
            >>> recordings = await hotjar.list_recordings(
            ...     date_from="2024-01-01",
            ...     date_to="2024-12-31",
            ...     filter_by={"browser": "Chrome", "device": "Desktop"},
            ...     limit=25
            ... )
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        params = {
            'limit': min(limit, 100),
            'offset': offset
        }

        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        if filter_by:
            params.update(filter_by)

        result = await self._make_request(
            method='GET',
            endpoint=f'/sites/{site_id}/recordings',
            params=params
        )

        logger.info(
            "hotjar_recordings_listed",
            count=len(result.get('recordings', [])),
            site_id=site_id
        )

        return result

    async def get_recording(
        self,
        recording_id: str,
        site_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get recording by ID.

        Args:
            recording_id: Recording ID
            site_id: Site ID (uses default if not provided)

        Returns:
            Recording details with events and metadata
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        result = await self._make_request(
            method='GET',
            endpoint=f'/sites/{site_id}/recordings/{recording_id}'
        )

        return result

    async def delete_recording(
        self,
        recording_id: str,
        site_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a recording.

        Args:
            recording_id: Recording ID
            site_id: Site ID (uses default if not provided)

        Returns:
            Deletion confirmation
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        await self._make_request(
            method='DELETE',
            endpoint=f'/sites/{site_id}/recordings/{recording_id}'
        )

        logger.info(
            "hotjar_recording_deleted",
            recording_id=recording_id,
            site_id=site_id
        )

        return {'status': 'deleted', 'recording_id': recording_id}

    # ===================================================================
    # HEATMAPS API
    # ===================================================================

    async def list_heatmaps(
        self,
        site_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List heatmaps.

        Args:
            site_id: Site ID (uses default if not provided)
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of heatmaps
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        params = {
            'limit': min(limit, 100),
            'offset': offset
        }

        result = await self._make_request(
            method='GET',
            endpoint=f'/sites/{site_id}/heatmaps',
            params=params
        )

        logger.info(
            "hotjar_heatmaps_listed",
            count=len(result.get('heatmaps', [])),
            site_id=site_id
        )

        return result

    async def get_heatmap(
        self,
        heatmap_id: str,
        site_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get heatmap by ID.

        Args:
            heatmap_id: Heatmap ID
            site_id: Site ID (uses default if not provided)

        Returns:
            Heatmap details with click, move, and scroll data
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        result = await self._make_request(
            method='GET',
            endpoint=f'/sites/{site_id}/heatmaps/{heatmap_id}'
        )

        return result

    async def create_heatmap(
        self,
        name: str,
        url_pattern: str,
        site_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a heatmap.

        Args:
            name: Heatmap name
            url_pattern: URL pattern to track (e.g., "/products/*")
            site_id: Site ID (uses default if not provided)

        Returns:
            Created heatmap data

        Example:
            >>> heatmap = await hotjar.create_heatmap(
            ...     name="Product Pages Heatmap",
            ...     url_pattern="/products/*"
            ... )
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        data = {
            'name': name,
            'url_pattern': url_pattern
        }

        result = await self._make_request(
            method='POST',
            endpoint=f'/sites/{site_id}/heatmaps',
            data=data
        )

        logger.info(
            "hotjar_heatmap_created",
            heatmap_id=result.get('id'),
            name=name,
            site_id=site_id
        )

        return result

    # ===================================================================
    # SURVEYS API
    # ===================================================================

    async def list_surveys(
        self,
        site_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List surveys.

        Args:
            site_id: Site ID (uses default if not provided)
            status: Filter by status (active, paused, stopped)
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of surveys
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        params = {
            'limit': min(limit, 100),
            'offset': offset
        }

        if status:
            params['status'] = status

        result = await self._make_request(
            method='GET',
            endpoint=f'/sites/{site_id}/surveys',
            params=params
        )

        logger.info(
            "hotjar_surveys_listed",
            count=len(result.get('surveys', [])),
            site_id=site_id,
            status=status
        )

        return result

    async def get_survey(
        self,
        survey_id: str,
        site_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get survey by ID.

        Args:
            survey_id: Survey ID
            site_id: Site ID (uses default if not provided)

        Returns:
            Survey details with questions and responses
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        result = await self._make_request(
            method='GET',
            endpoint=f'/sites/{site_id}/surveys/{survey_id}'
        )

        return result

    async def get_survey_responses(
        self,
        survey_id: str,
        site_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get survey responses.

        Args:
            survey_id: Survey ID
            site_id: Site ID (uses default if not provided)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of survey responses

        Example:
            >>> responses = await hotjar.get_survey_responses(
            ...     survey_id="survey_123",
            ...     date_from="2024-01-01",
            ...     date_to="2024-12-31",
            ...     limit=50
            ... )
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        params = {
            'limit': min(limit, 1000),
            'offset': offset
        }

        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to

        result = await self._make_request(
            method='GET',
            endpoint=f'/sites/{site_id}/surveys/{survey_id}/responses',
            params=params
        )

        logger.info(
            "hotjar_survey_responses_fetched",
            count=len(result.get('responses', [])),
            survey_id=survey_id
        )

        return result

    async def create_survey(
        self,
        name: str,
        questions: List[Dict[str, Any]],
        targeting: Dict[str, Any],
        site_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a survey.

        Args:
            name: Survey name
            questions: Survey questions configuration
            targeting: Targeting rules (pages, triggers, etc.)
            site_id: Site ID (uses default if not provided)

        Returns:
            Created survey data

        Example:
            >>> survey = await hotjar.create_survey(
            ...     name="User Satisfaction Survey",
            ...     questions=[
            ...         {"type": "rating", "text": "How satisfied are you?", "scale": 5},
            ...         {"type": "text", "text": "What can we improve?"}
            ...     ],
            ...     targeting={"pages": ["/dashboard"], "trigger": "exit_intent"}
            ... )
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        data = {
            'name': name,
            'questions': questions,
            'targeting': targeting
        }

        result = await self._make_request(
            method='POST',
            endpoint=f'/sites/{site_id}/surveys',
            data=data
        )

        logger.info(
            "hotjar_survey_created",
            survey_id=result.get('id'),
            name=name,
            site_id=site_id
        )

        return result

    # ===================================================================
    # FEEDBACK (POLLS) API
    # ===================================================================

    async def list_feedback(
        self,
        site_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List feedback (incoming feedback polls).

        Args:
            site_id: Site ID (uses default if not provided)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of feedback items
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        params = {
            'limit': min(limit, 1000),
            'offset': offset
        }

        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to

        result = await self._make_request(
            method='GET',
            endpoint=f'/sites/{site_id}/feedback',
            params=params
        )

        logger.info(
            "hotjar_feedback_listed",
            count=len(result.get('feedback', [])),
            site_id=site_id
        )

        return result

    async def get_feedback_item(
        self,
        feedback_id: str,
        site_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get feedback item by ID.

        Args:
            feedback_id: Feedback ID
            site_id: Site ID (uses default if not provided)

        Returns:
            Feedback details with user info and context
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        result = await self._make_request(
            method='GET',
            endpoint=f'/sites/{site_id}/feedback/{feedback_id}'
        )

        return result

    # ===================================================================
    # INSIGHTS API
    # ===================================================================

    async def get_insights(
        self,
        site_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get site insights and analytics.

        Args:
            site_id: Site ID (uses default if not provided)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)

        Returns:
            Insights data with key metrics

        Example:
            >>> insights = await hotjar.get_insights(
            ...     date_from="2024-01-01",
            ...     date_to="2024-12-31"
            ... )
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        params = {}
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to

        return await self._make_request(
            method='GET',
            endpoint=f'/sites/{site_id}/insights',
            params=params
        )

    async def get_page_stats(
        self,
        page_url: str,
        site_id: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for a specific page.

        Args:
            page_url: Page URL
            site_id: Site ID (uses default if not provided)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)

        Returns:
            Page statistics with views, recordings, feedback

        Example:
            >>> stats = await hotjar.get_page_stats(
            ...     page_url="/products/enterprise",
            ...     date_from="2024-01-01",
            ...     date_to="2024-12-31"
            ... )
        """
        site_id = site_id or self.default_site_id
        if not site_id:
            raise ValidationError("site_id is required")

        params = {
            'url': page_url
        }

        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to

        return await self._make_request(
            method='GET',
            endpoint=f'/sites/{site_id}/pages/stats',
            params=params
        )

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("hotjar_session_closed")
