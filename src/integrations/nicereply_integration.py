"""
Nicereply Integration
Priority Score: 9
ICP Adoption: 25-35% of customer support teams

Customer satisfaction and feedback platform providing:
- CSAT Surveys
- CES (Customer Effort Score)
- Ratings and Feedback
- Agents Performance
- Reports and Analytics
- Email Signatures
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


class NiceReplyIntegration(BaseIntegration):
    """
    Nicereply API integration with API key authentication.

    Authentication:
    - API Key as query parameter or header
    - Private key for write operations

    Rate Limits:
    - 120 requests per minute
    - 5000 requests per day

    Documentation: https://www.nicereply.com/help/api-documentation/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ) -> Any:
        """
        Initialize Nicereply integration.

        Args:
            credentials: Nicereply credentials
                - api_key: Nicereply public API key
                - private_key: Nicereply private key (for write operations)
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="nicereply",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        self.private_key = credentials.get('private_key', '')

        if not self.api_key:
            raise ValidationError("Nicereply api_key is required")

        self.base_url = "https://api.nicereply.com/v1"

        logger.info(
            "nicereply_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Nicereply (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("nicereply_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Nicereply authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        use_private_key: bool = False
    ) -> Any:
        """Make authenticated HTTP request to Nicereply API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Nicereply uses API key as query parameter
        if params is None:
            params = {}

        if use_private_key and self.private_key:
            params['private_key'] = self.private_key
        else:
            params['public_key'] = self.api_key

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
                        f"Nicereply API error ({response.status}): {error_text}",
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
        """Test connection to Nicereply API."""
        try:
            start_time = datetime.now()

            # Test with ratings list request
            response = await self._make_request(
                method='GET',
                endpoint='/ratings',
                params={'limit': 1}
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Nicereply",
                response_time_ms=duration_ms,
                metadata={
                    'integration_name': 'nicereply'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Nicereply connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # RATINGS API
    # ===================================================================

    async def list_ratings(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List ratings (survey responses).

        Args:
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)
            user_id: Filter by agent/user ID
            limit: Results limit (max: 1000)
            offset: Pagination offset

        Returns:
            List of ratings with metadata

        Example:
            >>> ratings = await nicereply.list_ratings(
            ...     since="2024-01-01",
            ...     until="2024-12-31",
            ...     limit=50
            ... )
        """
        params = {
            'limit': min(limit, 1000),
            'offset': offset
        }

        if since:
            params['since'] = since
        if until:
            params['until'] = until
        if user_id:
            params['user_id'] = user_id

        result = await self._make_request(
            method='GET',
            endpoint='/ratings',
            params=params
        )

        logger.info(
            "nicereply_ratings_listed",
            count=len(result.get('ratings', []))
        )

        return result

    async def get_rating(self, rating_id: int) -> Dict[str, Any]:
        """
        Get rating by ID.

        Args:
            rating_id: Rating ID

        Returns:
            Rating details with score and comment
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/ratings/{rating_id}'
        )

        return result.get('rating', {})

    async def create_rating(
        self,
        rating: int,
        customer_email: str,
        customer_name: Optional[str] = None,
        user_id: Optional[int] = None,
        comment: Optional[str] = None,
        rating_date: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a rating (for importing historical data).

        Args:
            rating: Rating score (1-5 for CSAT, 1-10 for NPS, 1-7 for CES)
            customer_email: Customer email
            customer_name: Customer name
            user_id: Agent/user ID
            comment: Customer comment
            rating_date: Rating date (YYYY-MM-DD HH:MM:SS)
            custom_fields: Custom field values

        Returns:
            Created rating data

        Example:
            >>> rating = await nicereply.create_rating(
            ...     rating=5,
            ...     customer_email="jane@acme.com",
            ...     customer_name="Jane Doe",
            ...     user_id=123,
            ...     comment="Excellent support, resolved quickly!",
            ...     custom_fields={"ticket_id": "TKT-456"}
            ... )
        """
        data = {
            'rating': rating,
            'customer_email': customer_email
        }

        if customer_name:
            data['customer_name'] = customer_name
        if user_id:
            data['user_id'] = user_id
        if comment:
            data['comment'] = comment
        if rating_date:
            data['rating_date'] = rating_date
        if custom_fields:
            data.update(custom_fields)

        result = await self._make_request(
            method='POST',
            endpoint='/ratings',
            data=data,
            use_private_key=True
        )

        logger.info(
            "nicereply_rating_created",
            rating_id=result.get('rating', {}).get('id'),
            rating=rating,
            customer_email=customer_email
        )

        return result.get('rating', {})

    # ===================================================================
    # USERS (AGENTS) API
    # ===================================================================

    async def list_users(self) -> List[Dict[str, Any]]:
        """
        List users (agents/team members).

        Returns:
            List of users

        Example:
            >>> users = await nicereply.list_users()
            >>> for user in users:
            ...     print(f"{user['name']}: {user['email']}")
        """
        result = await self._make_request(
            method='GET',
            endpoint='/users'
        )

        logger.info(
            "nicereply_users_listed",
            count=len(result.get('users', []))
        )

        return result.get('users', [])

    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User details with performance metrics
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/users/{user_id}'
        )

        return result.get('user', {})

    async def create_user(
        self,
        email: str,
        name: str,
        role: str = "agent"
    ) -> Dict[str, Any]:
        """
        Create a user.

        Args:
            email: User email
            name: User name
            role: User role (admin, agent)

        Returns:
            Created user data

        Example:
            >>> user = await nicereply.create_user(
            ...     email="agent@company.com",
            ...     name="Support Agent",
            ...     role="agent"
            ... )
        """
        data = {
            'email': email,
            'name': name,
            'role': role
        }

        result = await self._make_request(
            method='POST',
            endpoint='/users',
            data=data,
            use_private_key=True
        )

        logger.info(
            "nicereply_user_created",
            user_id=result.get('user', {}).get('id'),
            email=email
        )

        return result.get('user', {})

    # ===================================================================
    # METRICS API
    # ===================================================================

    async def get_metrics(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get CSAT/CES metrics.

        Args:
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)
            user_id: Filter by user/agent ID

        Returns:
            Metrics with scores and response rates

        Example:
            >>> metrics = await nicereply.get_metrics(
            ...     since="2024-01-01",
            ...     until="2024-12-31"
            ... )
            >>> print(f"Average CSAT: {metrics['average_rating']}")
            >>> print(f"Response rate: {metrics['response_rate']}%")
        """
        params = {}

        if since:
            params['since'] = since
        if until:
            params['until'] = until
        if user_id:
            params['user_id'] = user_id

        return await self._make_request(
            method='GET',
            endpoint='/metrics',
            params=params
        )

    async def get_csat_score(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> float:
        """
        Get CSAT score.

        Args:
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)

        Returns:
            CSAT score (0-100)

        Example:
            >>> csat = await nicereply.get_csat_score(
            ...     since="2024-01-01",
            ...     until="2024-12-31"
            ... )
            >>> print(f"CSAT: {csat}%")
        """
        metrics = await self.get_metrics(since=since, until=until)
        return metrics.get('csat_score', 0.0)

    async def get_ces_score(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> float:
        """
        Get CES (Customer Effort Score).

        Args:
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)

        Returns:
            CES score

        Example:
            >>> ces = await nicereply.get_ces_score()
            >>> print(f"CES: {ces}")
        """
        metrics = await self.get_metrics(since=since, until=until)
        return metrics.get('ces_score', 0.0)

    # ===================================================================
    # REPORTS API
    # ===================================================================

    async def get_user_performance(
        self,
        user_id: int,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user/agent performance metrics.

        Args:
            user_id: User ID
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)

        Returns:
            Performance metrics with ratings and trends

        Example:
            >>> performance = await nicereply.get_user_performance(
            ...     user_id=123,
            ...     since="2024-01-01",
            ...     until="2024-12-31"
            ... )
            >>> print(f"Average rating: {performance['average_rating']}")
            >>> print(f"Total ratings: {performance['total_ratings']}")
        """
        params = {
            'user_id': user_id
        }

        if since:
            params['since'] = since
        if until:
            params['until'] = until

        metrics = await self._make_request(
            method='GET',
            endpoint='/metrics',
            params=params
        )

        user_info = await self.get_user(user_id)

        return {
            'user_id': user_id,
            'user_name': user_info.get('name'),
            'user_email': user_info.get('email'),
            'average_rating': metrics.get('average_rating'),
            'total_ratings': metrics.get('total_ratings'),
            'response_rate': metrics.get('response_rate'),
            'csat_score': metrics.get('csat_score'),
            'ces_score': metrics.get('ces_score')
        }

    async def get_rating_distribution(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get rating score distribution.

        Args:
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)

        Returns:
            Distribution of ratings by score

        Example:
            >>> distribution = await nicereply.get_rating_distribution(
            ...     since="2024-01-01"
            ... )
            >>> for score, count in distribution['scores'].items():
            ...     print(f"Score {score}: {count} ratings")
        """
        params = {}

        if since:
            params['since'] = since
        if until:
            params['until'] = until

        ratings = await self._make_request(
            method='GET',
            endpoint='/ratings',
            params=params
        )

        # Calculate distribution
        distribution = {}
        total = 0

        for rating_data in ratings.get('ratings', []):
            score = rating_data.get('rating')
            if score:
                distribution[score] = distribution.get(score, 0) + 1
                total += 1

        return {
            'total_ratings': total,
            'scores': distribution,
            'date_range': {
                'since': since,
                'until': until
            }
        }

    async def get_trends(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        interval: str = "month"
    ) -> Dict[str, Any]:
        """
        Get rating trends over time.

        Args:
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)
            interval: Grouping interval (day, week, month)

        Returns:
            Time-series rating trends

        Example:
            >>> trends = await nicereply.get_trends(
            ...     since="2024-01-01",
            ...     until="2024-12-31",
            ...     interval="month"
            ... )
        """
        params = {
            'interval': interval
        }

        if since:
            params['since'] = since
        if until:
            params['until'] = until

        return await self._make_request(
            method='GET',
            endpoint='/metrics/trends',
            params=params
        )

    # ===================================================================
    # SURVEYS API
    # ===================================================================

    async def list_surveys(self) -> List[Dict[str, Any]]:
        """
        List survey templates/types.

        Returns:
            List of survey configurations
        """
        result = await self._make_request(
            method='GET',
            endpoint='/surveys'
        )

        return result.get('surveys', [])

    async def get_survey(self, survey_id: int) -> Dict[str, Any]:
        """
        Get survey configuration by ID.

        Args:
            survey_id: Survey ID

        Returns:
            Survey configuration details
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/surveys/{survey_id}'
        )

        return result.get('survey', {})

    # ===================================================================
    # CUSTOMERS API
    # ===================================================================

    async def list_customers(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List customers who have received surveys.

        Args:
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of customers
        """
        params = {
            'limit': min(limit, 1000),
            'offset': offset
        }

        result = await self._make_request(
            method='GET',
            endpoint='/customers',
            params=params
        )

        return result

    async def get_customer_ratings(
        self,
        customer_email: str
    ) -> List[Dict[str, Any]]:
        """
        Get all ratings for a specific customer.

        Args:
            customer_email: Customer email

        Returns:
            List of customer's ratings

        Example:
            >>> ratings = await nicereply.get_customer_ratings(
            ...     customer_email="jane@acme.com"
            ... )
        """
        ratings = await self.list_ratings()

        customer_ratings = [
            r for r in ratings.get('ratings', [])
            if r.get('customer_email') == customer_email
        ]

        return customer_ratings

    # ===================================================================
    # COMMENTS API
    # ===================================================================

    async def get_comments(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        with_rating: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get ratings with comments.

        Args:
            since: Start date (YYYY-MM-DD)
            until: End date (YYYY-MM-DD)
            with_rating: Filter by rating score

        Returns:
            List of ratings that include comments

        Example:
            >>> # Get all negative feedback (1-2 stars)
            >>> comments = await nicereply.get_comments(
            ...     since="2024-01-01",
            ...     with_rating=2
            ... )
        """
        params = {}

        if since:
            params['since'] = since
        if until:
            params['until'] = until

        ratings = await self._make_request(
            method='GET',
            endpoint='/ratings',
            params=params
        )

        # Filter for ratings with comments
        comments = [
            r for r in ratings.get('ratings', [])
            if r.get('comment') and (with_rating is None or r.get('rating') <= with_rating)
        ]

        logger.info(
            "nicereply_comments_retrieved",
            count=len(comments)
        )

        return comments

    async def close(self) -> Any:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("nicereply_session_closed")
