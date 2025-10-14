"""
Canny Integration
Priority Score: 11
ICP Adoption: 30-40% of product teams

User feedback and feature request platform providing:
- Posts (Feature Requests)
- Votes and Voting
- Comments
- Boards
- Users and Companies
- Roadmap Management
- Changelogs
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


class CannyIntegration(BaseIntegration):
    """
    Canny API integration with API key authentication.

    Authentication:
    - API Key in Authorization header (format: apiKey YOUR_API_KEY)
    - API keys are per-board or account-wide

    Rate Limits:
    - 100 requests per minute per API key
    - Burst: 10 requests per second

    Documentation: https://developers.canny.io/api-reference
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 80,
        rate_limit_window: int = 60
    ):
        """
        Initialize Canny integration.

        Args:
            credentials: Canny credentials
                - api_key: Canny API key
            rate_limit_calls: Max API calls per window (default: 80)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="canny",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        if not self.api_key:
            raise ValidationError("Canny api_key is required")

        self.base_url = "https://canny.io/api/v1"

        logger.info(
            "canny_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Canny (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("canny_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Canny authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Canny API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Canny uses POST for most endpoints with data in body
        # API key is always in the body
        request_data = data.copy() if data else {}
        request_data['apiKey'] = self.api_key

        headers = {
            'Content-Type': 'application/json'
        }

        try:
            async with self.session.request(
                method,
                url,
                json=request_data if method != 'GET' else None,
                params=params if method == 'GET' else None,
                headers=headers
            ) as response:
                if response.status in (200, 201, 202):
                    self.circuit_breaker._record_success(0.1)
                    result = await response.json()

                    # Check for Canny-specific error in response
                    if result.get('error'):
                        error = APIError(
                            f"Canny API error: {result.get('error')}",
                            response.status
                        )
                        self.circuit_breaker._record_failure(error)
                        raise error

                    return result
                else:
                    error_text = await response.text()
                    error = APIError(
                        f"Canny API error ({response.status}): {error_text}",
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
        """Test connection to Canny API."""
        try:
            start_time = datetime.now()

            # Test with boards list
            response = await self._make_request(
                method='POST',
                endpoint='/boards/list',
                data={}
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            boards = response.get('boards', [])

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Canny",
                response_time_ms=duration_ms,
                metadata={
                    'board_count': len(boards),
                    'integration_name': 'canny'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Canny connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # POSTS API (FEATURE REQUESTS)
    # ===================================================================

    async def list_posts(
        self,
        board_id: Optional[str] = None,
        category_id: Optional[str] = None,
        sort: str = "created",
        status: Optional[str] = None,
        tag_ids: Optional[List[str]] = None,
        limit: int = 50,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        List posts (feature requests).

        Args:
            board_id: Filter by board ID
            category_id: Filter by category ID
            sort: Sort by (created, score, statusChanged, trending)
            status: Filter by status (open, under_review, planned, in_progress, complete, closed)
            tag_ids: Filter by tag IDs
            limit: Results limit (max: 100)
            skip: Pagination offset

        Returns:
            List of posts with pagination

        Example:
            >>> posts = await canny.list_posts(
            ...     board_id="abc123",
            ...     status="planned",
            ...     sort="score",
            ...     limit=25
            ... )
        """
        data = {
            'sort': sort,
            'limit': min(limit, 100),
            'skip': skip
        }

        if board_id:
            data['boardID'] = board_id
        if category_id:
            data['categoryID'] = category_id
        if status:
            data['status'] = status
        if tag_ids:
            data['tagIDs'] = tag_ids

        result = await self._make_request(
            method='POST',
            endpoint='/posts/list',
            data=data
        )

        logger.info(
            "canny_posts_listed",
            count=len(result.get('posts', [])),
            board_id=board_id,
            status=status
        )

        return result

    async def get_post(self, post_id: str) -> Dict[str, Any]:
        """
        Get post by ID.

        Args:
            post_id: Post ID

        Returns:
            Post details with votes, comments, and status
        """
        result = await self._make_request(
            method='POST',
            endpoint='/posts/retrieve',
            data={'id': post_id}
        )

        return result

    async def create_post(
        self,
        board_id: str,
        author_id: str,
        title: str,
        details: str,
        category_id: Optional[str] = None,
        eta: Optional[str] = None,
        image_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new post.

        Args:
            board_id: Board ID
            author_id: Author user ID
            title: Post title
            details: Post description/details
            category_id: Category ID
            eta: Estimated completion date (ISO 8601)
            image_urls: List of image URLs

        Returns:
            Created post data

        Example:
            >>> post = await canny.create_post(
            ...     board_id="abc123",
            ...     author_id="user_456",
            ...     title="Add dark mode",
            ...     details="Please add a dark theme option for better usability at night.",
            ...     category_id="cat_789"
            ... )
        """
        data = {
            'boardID': board_id,
            'authorID': author_id,
            'title': title,
            'details': details
        }

        if category_id:
            data['categoryID'] = category_id
        if eta:
            data['eta'] = eta
        if image_urls:
            data['imageURLs'] = image_urls

        result = await self._make_request(
            method='POST',
            endpoint='/posts/create',
            data=data
        )

        logger.info(
            "canny_post_created",
            post_id=result.get('id'),
            title=title,
            board_id=board_id
        )

        return result

    async def update_post(
        self,
        post_id: str,
        status: Optional[str] = None,
        category_id: Optional[str] = None,
        eta: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a post.

        Args:
            post_id: Post ID
            status: New status (open, under_review, planned, in_progress, complete, closed)
            category_id: New category ID
            eta: New ETA (ISO 8601)
            owner_id: New owner user ID

        Returns:
            Updated post data
        """
        data = {'postID': post_id}

        if status:
            data['status'] = status
        if category_id:
            data['categoryID'] = category_id
        if eta:
            data['eta'] = eta
        if owner_id:
            data['ownerID'] = owner_id

        result = await self._make_request(
            method='POST',
            endpoint='/posts/update',
            data=data
        )

        logger.info(
            "canny_post_updated",
            post_id=post_id,
            status=status
        )

        return result

    async def delete_post(self, post_id: str) -> Dict[str, Any]:
        """
        Delete a post.

        Args:
            post_id: Post ID

        Returns:
            Deletion confirmation
        """
        result = await self._make_request(
            method='POST',
            endpoint='/posts/delete',
            data={'postID': post_id}
        )

        logger.info("canny_post_deleted", post_id=post_id)
        return result

    # ===================================================================
    # VOTES API
    # ===================================================================

    async def list_votes(
        self,
        post_id: Optional[str] = None,
        board_id: Optional[str] = None,
        voter_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        List votes.

        Args:
            post_id: Filter by post ID
            board_id: Filter by board ID
            voter_id: Filter by voter user ID
            limit: Results limit
            skip: Pagination offset

        Returns:
            List of votes
        """
        data = {
            'limit': min(limit, 100),
            'skip': skip
        }

        if post_id:
            data['postID'] = post_id
        if board_id:
            data['boardID'] = board_id
        if voter_id:
            data['voterID'] = voter_id

        return await self._make_request(
            method='POST',
            endpoint='/votes/list',
            data=data
        )

    async def create_vote(
        self,
        post_id: str,
        voter_id: str
    ) -> Dict[str, Any]:
        """
        Create a vote on a post.

        Args:
            post_id: Post ID to vote on
            voter_id: User ID of voter

        Returns:
            Vote confirmation

        Example:
            >>> await canny.create_vote(
            ...     post_id="post_123",
            ...     voter_id="user_456"
            ... )
        """
        data = {
            'postID': post_id,
            'voterID': voter_id
        }

        result = await self._make_request(
            method='POST',
            endpoint='/votes/create',
            data=data
        )

        logger.info(
            "canny_vote_created",
            post_id=post_id,
            voter_id=voter_id
        )

        return result

    async def delete_vote(
        self,
        post_id: str,
        voter_id: str
    ) -> Dict[str, Any]:
        """
        Delete a vote.

        Args:
            post_id: Post ID
            voter_id: User ID of voter

        Returns:
            Deletion confirmation
        """
        data = {
            'postID': post_id,
            'voterID': voter_id
        }

        result = await self._make_request(
            method='POST',
            endpoint='/votes/delete',
            data=data
        )

        logger.info(
            "canny_vote_deleted",
            post_id=post_id,
            voter_id=voter_id
        )

        return result

    # ===================================================================
    # COMMENTS API
    # ===================================================================

    async def list_comments(
        self,
        post_id: Optional[str] = None,
        board_id: Optional[str] = None,
        author_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        List comments.

        Args:
            post_id: Filter by post ID
            board_id: Filter by board ID
            author_id: Filter by author user ID
            limit: Results limit
            skip: Pagination offset

        Returns:
            List of comments
        """
        data = {
            'limit': min(limit, 100),
            'skip': skip
        }

        if post_id:
            data['postID'] = post_id
        if board_id:
            data['boardID'] = board_id
        if author_id:
            data['authorID'] = author_id

        return await self._make_request(
            method='POST',
            endpoint='/comments/list',
            data=data
        )

    async def get_comment(self, comment_id: str) -> Dict[str, Any]:
        """
        Get comment by ID.

        Args:
            comment_id: Comment ID

        Returns:
            Comment details
        """
        return await self._make_request(
            method='POST',
            endpoint='/comments/retrieve',
            data={'id': comment_id}
        )

    async def create_comment(
        self,
        post_id: str,
        author_id: str,
        value: str,
        parent_id: Optional[str] = None,
        image_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a comment on a post.

        Args:
            post_id: Post ID
            author_id: Author user ID
            value: Comment text
            parent_id: Parent comment ID (for replies)
            image_urls: List of image URLs

        Returns:
            Created comment data

        Example:
            >>> comment = await canny.create_comment(
            ...     post_id="post_123",
            ...     author_id="user_456",
            ...     value="Great idea! We're working on this for Q2."
            ... )
        """
        data = {
            'postID': post_id,
            'authorID': author_id,
            'value': value
        }

        if parent_id:
            data['parentID'] = parent_id
        if image_urls:
            data['imageURLs'] = image_urls

        result = await self._make_request(
            method='POST',
            endpoint='/comments/create',
            data=data
        )

        logger.info(
            "canny_comment_created",
            comment_id=result.get('id'),
            post_id=post_id
        )

        return result

    async def delete_comment(self, comment_id: str) -> Dict[str, Any]:
        """
        Delete a comment.

        Args:
            comment_id: Comment ID

        Returns:
            Deletion confirmation
        """
        result = await self._make_request(
            method='POST',
            endpoint='/comments/delete',
            data={'commentID': comment_id}
        )

        logger.info("canny_comment_deleted", comment_id=comment_id)
        return result

    # ===================================================================
    # BOARDS API
    # ===================================================================

    async def list_boards(self) -> Dict[str, Any]:
        """
        List all boards.

        Returns:
            List of boards
        """
        return await self._make_request(
            method='POST',
            endpoint='/boards/list',
            data={}
        )

    async def get_board(self, board_id: str) -> Dict[str, Any]:
        """
        Get board by ID.

        Args:
            board_id: Board ID

        Returns:
            Board details with categories and settings
        """
        return await self._make_request(
            method='POST',
            endpoint='/boards/retrieve',
            data={'id': board_id}
        )

    # ===================================================================
    # CATEGORIES API
    # ===================================================================

    async def list_categories(self, board_id: str) -> Dict[str, Any]:
        """
        List categories in a board.

        Args:
            board_id: Board ID

        Returns:
            List of categories
        """
        return await self._make_request(
            method='POST',
            endpoint='/categories/list',
            data={'boardID': board_id}
        )

    async def create_category(
        self,
        board_id: str,
        name: str
    ) -> Dict[str, Any]:
        """
        Create a category.

        Args:
            board_id: Board ID
            name: Category name

        Returns:
            Created category data
        """
        data = {
            'boardID': board_id,
            'name': name
        }

        result = await self._make_request(
            method='POST',
            endpoint='/categories/create',
            data=data
        )

        logger.info(
            "canny_category_created",
            category_id=result.get('id'),
            name=name,
            board_id=board_id
        )

        return result

    async def delete_category(self, category_id: str) -> Dict[str, Any]:
        """
        Delete a category.

        Args:
            category_id: Category ID

        Returns:
            Deletion confirmation
        """
        result = await self._make_request(
            method='POST',
            endpoint='/categories/delete',
            data={'categoryID': category_id}
        )

        logger.info("canny_category_deleted", category_id=category_id)
        return result

    # ===================================================================
    # USERS API
    # ===================================================================

    async def list_users(
        self,
        limit: int = 50,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        List users.

        Args:
            limit: Results limit
            skip: Pagination offset

        Returns:
            List of users
        """
        data = {
            'limit': min(limit, 100),
            'skip': skip
        }

        return await self._make_request(
            method='POST',
            endpoint='/users/list',
            data=data
        )

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User details
        """
        return await self._make_request(
            method='POST',
            endpoint='/users/retrieve',
            data={'id': user_id}
        )

    async def create_user(
        self,
        email: str,
        name: str,
        user_id: Optional[str] = None,
        avatar_url: Optional[str] = None,
        created: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or update a user.

        Args:
            email: User email
            name: User name
            user_id: Custom user ID
            avatar_url: Avatar image URL
            created: User creation date (ISO 8601)
            custom_fields: Custom field values

        Returns:
            Created/updated user data

        Example:
            >>> user = await canny.create_user(
            ...     email="jane@example.com",
            ...     name="Jane Doe",
            ...     user_id="user_external_123",
            ...     custom_fields={"company": "Acme Corp", "plan": "Enterprise"}
            ... )
        """
        data = {
            'email': email,
            'name': name
        }

        if user_id:
            data['userID'] = user_id
        if avatar_url:
            data['avatarURL'] = avatar_url
        if created:
            data['created'] = created
        if custom_fields:
            data['customFields'] = custom_fields

        result = await self._make_request(
            method='POST',
            endpoint='/users/create_or_update',
            data=data
        )

        logger.info(
            "canny_user_created",
            user_id=result.get('id'),
            email=email
        )

        return result

    # ===================================================================
    # COMPANIES API
    # ===================================================================

    async def list_companies(
        self,
        limit: int = 50,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        List companies.

        Args:
            limit: Results limit
            skip: Pagination offset

        Returns:
            List of companies
        """
        data = {
            'limit': min(limit, 100),
            'skip': skip
        }

        return await self._make_request(
            method='POST',
            endpoint='/companies/list',
            data=data
        )

    async def create_company(
        self,
        company_id: str,
        name: str,
        monthly_spend: Optional[float] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create or update a company.

        Args:
            company_id: Company ID
            name: Company name
            monthly_spend: Monthly revenue/spend
            custom_fields: Custom field values

        Returns:
            Created/updated company data

        Example:
            >>> company = await canny.create_company(
            ...     company_id="acme_corp",
            ...     name="Acme Corporation",
            ...     monthly_spend=5000.00,
            ...     custom_fields={"industry": "Technology", "employees": 250}
            ... )
        """
        data = {
            'id': company_id,
            'name': name
        }

        if monthly_spend is not None:
            data['monthlySpend'] = monthly_spend
        if custom_fields:
            data['customFields'] = custom_fields

        result = await self._make_request(
            method='POST',
            endpoint='/companies/create_or_update',
            data=data
        )

        logger.info(
            "canny_company_created",
            company_id=company_id,
            name=name
        )

        return result

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("canny_session_closed")
