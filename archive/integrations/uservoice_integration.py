"""
UserVoice Integration
Priority Score: 12
ICP Adoption: 25-35% of product teams

Customer feedback and feature request management platform providing:
- Feedback Collection
- Feature Requests
- User Voting
- Forums and Categories
- Admin Responses
- Roadmap Management
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from .auth.oauth2_base import OAuth2Integration
from .base import ConnectionTestResult, IntegrationStatus, ValidationError, APIError

logger = structlog.get_logger(__name__)


class UserVoiceIntegration(OAuth2Integration):
    """
    UserVoice API integration with OAuth2 authentication.

    Authentication:
    - OAuth2 with client credentials
    - Requires client_id, client_secret, access_token, refresh_token
    - API Key alternative available for simpler use cases

    Rate Limits:
    - 500 requests per hour per API key/token
    - Burst: 10 requests per second

    Documentation: https://developer.uservoice.com/docs/api/v2/reference/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ):
        """
        Initialize UserVoice integration.

        Args:
            credentials: OAuth2 credentials
                - client_id: UserVoice OAuth client ID
                - client_secret: UserVoice OAuth client secret
                - access_token: Current access token
                - refresh_token: Refresh token
                - subdomain: UserVoice subdomain (e.g., 'acme' for acme.uservoice.com)
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="uservoice",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.subdomain = credentials.get('subdomain', '')
        if not self.subdomain:
            raise ValidationError("UserVoice subdomain is required")

        logger.info(
            "uservoice_initialized",
            subdomain=self.subdomain,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    def get_oauth_config(self) -> Dict[str, Any]:
        """Get UserVoice OAuth2 configuration."""
        return {
            'auth_url': f'https://{self.subdomain}.uservoice.com/oauth/authorize',
            'token_url': f'https://{self.subdomain}.uservoice.com/oauth/token',
            'api_base_url': f'https://{self.subdomain}.uservoice.com/api/v2',
            'scopes': []  # UserVoice uses implicit scopes based on client
        }

    async def test_connection(self) -> ConnectionTestResult:
        """Test connection to UserVoice API."""
        try:
            start_time = datetime.now()

            # Test with current user info
            response = await self._make_request(
                method='GET',
                endpoint='/users/current.json'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            user = response.get('user', {})

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to UserVoice",
                response_time_ms=duration_ms,
                metadata={
                    'user_id': user.get('id'),
                    'user_email': user.get('email'),
                    'user_name': user.get('name'),
                    'subdomain': self.subdomain,
                    'integration_name': 'uservoice'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"UserVoice connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # SUGGESTIONS (FEATURE REQUESTS) API
    # ===================================================================

    async def list_suggestions(
        self,
        forum_id: Optional[int] = None,
        status: Optional[str] = None,
        sort: str = "popular",
        per_page: int = 50,
        page: int = 1,
        filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List feature suggestions/requests.

        Args:
            forum_id: Filter by forum ID
            status: Filter by status (under_review, planned, completed, declined)
            sort: Sort order (popular, hot, new, top, trending)
            per_page: Results per page (max: 100)
            page: Page number
            filter: Search filter query

        Returns:
            List of suggestions with pagination info

        Example:
            >>> suggestions = await uservoice.list_suggestions(
            ...     forum_id=12345,
            ...     status="planned",
            ...     sort="popular",
            ...     per_page=25
            ... )
        """
        params = {
            'sort': sort,
            'per_page': min(per_page, 100),
            'page': page
        }

        if forum_id:
            params['forum_id'] = forum_id
        if status:
            params['status'] = status
        if filter:
            params['filter'] = filter

        result = await self._make_request(
            method='GET',
            endpoint='/suggestions.json',
            params=params
        )

        logger.info(
            "uservoice_suggestions_listed",
            count=len(result.get('suggestions', [])),
            forum_id=forum_id,
            status=status
        )

        return result

    async def get_suggestion(self, suggestion_id: int) -> Dict[str, Any]:
        """
        Get suggestion by ID.

        Args:
            suggestion_id: Suggestion ID

        Returns:
            Suggestion details including votes, comments, status
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/suggestions/{suggestion_id}.json'
        )

        return result.get('suggestion', {})

    async def create_suggestion(
        self,
        forum_id: int,
        title: str,
        text: str,
        user_email: Optional[str] = None,
        category_id: Optional[int] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new suggestion/feature request.

        Args:
            forum_id: Forum ID to post in
            title: Suggestion title
            text: Suggestion description
            user_email: Email of user creating suggestion
            category_id: Category ID
            labels: List of label names

        Returns:
            Created suggestion data

        Example:
            >>> suggestion = await uservoice.create_suggestion(
            ...     forum_id=12345,
            ...     title="Add dark mode support",
            ...     text="Would love to have a dark theme option for the app.",
            ...     category_id=100,
            ...     labels=["ui", "accessibility"]
            ... )
        """
        data = {
            'suggestion': {
                'forum_id': forum_id,
                'title': title,
                'text': text
            }
        }

        if user_email:
            data['suggestion']['user_email'] = user_email
        if category_id:
            data['suggestion']['category_id'] = category_id
        if labels:
            data['suggestion']['labels'] = labels

        result = await self._make_request(
            method='POST',
            endpoint='/suggestions.json',
            data=data
        )

        logger.info(
            "uservoice_suggestion_created",
            suggestion_id=result.get('suggestion', {}).get('id'),
            title=title,
            forum_id=forum_id
        )

        return result.get('suggestion', {})

    async def update_suggestion(
        self,
        suggestion_id: int,
        status: Optional[str] = None,
        category_id: Optional[int] = None,
        labels: Optional[List[str]] = None,
        response_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a suggestion.

        Args:
            suggestion_id: Suggestion ID
            status: New status (under_review, planned, completed, declined)
            category_id: New category ID
            labels: New label list
            response_text: Admin response to add

        Returns:
            Updated suggestion data
        """
        data = {'suggestion': {}}

        if status:
            data['suggestion']['status'] = status
        if category_id:
            data['suggestion']['category_id'] = category_id
        if labels:
            data['suggestion']['labels'] = labels
        if response_text:
            data['suggestion']['response_text'] = response_text

        result = await self._make_request(
            method='PUT',
            endpoint=f'/suggestions/{suggestion_id}.json',
            data=data
        )

        logger.info(
            "uservoice_suggestion_updated",
            suggestion_id=suggestion_id,
            status=status
        )

        return result.get('suggestion', {})

    async def delete_suggestion(self, suggestion_id: int) -> Dict[str, Any]:
        """
        Delete a suggestion.

        Args:
            suggestion_id: Suggestion ID

        Returns:
            Deletion confirmation
        """
        await self._make_request(
            method='DELETE',
            endpoint=f'/suggestions/{suggestion_id}.json'
        )

        logger.info("uservoice_suggestion_deleted", suggestion_id=suggestion_id)
        return {'status': 'deleted', 'suggestion_id': suggestion_id}

    # ===================================================================
    # VOTES API
    # ===================================================================

    async def list_votes(
        self,
        suggestion_id: Optional[int] = None,
        user_id: Optional[int] = None,
        per_page: int = 50,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        List votes.

        Args:
            suggestion_id: Filter by suggestion ID
            user_id: Filter by user ID
            per_page: Results per page
            page: Page number

        Returns:
            List of votes
        """
        params = {
            'per_page': min(per_page, 100),
            'page': page
        }

        if suggestion_id:
            params['suggestion_id'] = suggestion_id
        if user_id:
            params['user_id'] = user_id

        return await self._make_request(
            method='GET',
            endpoint='/votes.json',
            params=params
        )

    async def add_vote(
        self,
        suggestion_id: int,
        user_email: Optional[str] = None,
        votes: int = 1
    ) -> Dict[str, Any]:
        """
        Add vote(s) to a suggestion.

        Args:
            suggestion_id: Suggestion ID to vote on
            user_email: Email of voting user
            votes: Number of votes to add (default: 1)

        Returns:
            Vote confirmation

        Example:
            >>> await uservoice.add_vote(
            ...     suggestion_id=98765,
            ...     user_email="user@example.com",
            ...     votes=3
            ... )
        """
        data = {
            'vote': {
                'suggestion_id': suggestion_id,
                'votes': votes
            }
        }

        if user_email:
            data['vote']['user_email'] = user_email

        result = await self._make_request(
            method='POST',
            endpoint='/votes.json',
            data=data
        )

        logger.info(
            "uservoice_vote_added",
            suggestion_id=suggestion_id,
            votes=votes
        )

        return result.get('vote', {})

    async def remove_vote(
        self,
        suggestion_id: int,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Remove vote from a suggestion.

        Args:
            suggestion_id: Suggestion ID
            user_email: Email of user removing vote

        Returns:
            Removal confirmation
        """
        params = {'suggestion_id': suggestion_id}
        if user_email:
            params['user_email'] = user_email

        await self._make_request(
            method='DELETE',
            endpoint='/votes.json',
            params=params
        )

        logger.info(
            "uservoice_vote_removed",
            suggestion_id=suggestion_id
        )

        return {'status': 'removed', 'suggestion_id': suggestion_id}

    # ===================================================================
    # FORUMS API
    # ===================================================================

    async def list_forums(self) -> Dict[str, Any]:
        """
        List all forums.

        Returns:
            List of forums with categories
        """
        return await self._make_request(
            method='GET',
            endpoint='/forums.json'
        )

    async def get_forum(self, forum_id: int) -> Dict[str, Any]:
        """
        Get forum by ID.

        Args:
            forum_id: Forum ID

        Returns:
            Forum details with categories and settings
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/forums/{forum_id}.json'
        )

        return result.get('forum', {})

    async def create_forum(
        self,
        name: str,
        welcome_message: Optional[str] = None,
        private: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new forum.

        Args:
            name: Forum name
            welcome_message: Welcome message for forum
            private: Whether forum is private

        Returns:
            Created forum data
        """
        data = {
            'forum': {
                'name': name,
                'private': private
            }
        }

        if welcome_message:
            data['forum']['welcome_message'] = welcome_message

        result = await self._make_request(
            method='POST',
            endpoint='/forums.json',
            data=data
        )

        logger.info(
            "uservoice_forum_created",
            forum_id=result.get('forum', {}).get('id'),
            name=name
        )

        return result.get('forum', {})

    # ===================================================================
    # CATEGORIES API
    # ===================================================================

    async def list_categories(self, forum_id: int) -> Dict[str, Any]:
        """
        List categories in a forum.

        Args:
            forum_id: Forum ID

        Returns:
            List of categories
        """
        params = {'forum_id': forum_id}

        return await self._make_request(
            method='GET',
            endpoint='/categories.json',
            params=params
        )

    async def create_category(
        self,
        forum_id: int,
        name: str,
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a category.

        Args:
            forum_id: Forum ID
            name: Category name
            color: Hex color code (e.g., '#FF5733')

        Returns:
            Created category data
        """
        data = {
            'category': {
                'forum_id': forum_id,
                'name': name
            }
        }

        if color:
            data['category']['color'] = color

        result = await self._make_request(
            method='POST',
            endpoint='/categories.json',
            data=data
        )

        logger.info(
            "uservoice_category_created",
            category_id=result.get('category', {}).get('id'),
            name=name,
            forum_id=forum_id
        )

        return result.get('category', {})

    # ===================================================================
    # COMMENTS API
    # ===================================================================

    async def list_comments(
        self,
        suggestion_id: int,
        per_page: int = 50,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        List comments on a suggestion.

        Args:
            suggestion_id: Suggestion ID
            per_page: Results per page
            page: Page number

        Returns:
            List of comments
        """
        params = {
            'suggestion_id': suggestion_id,
            'per_page': min(per_page, 100),
            'page': page
        }

        return await self._make_request(
            method='GET',
            endpoint='/comments.json',
            params=params
        )

    async def create_comment(
        self,
        suggestion_id: int,
        text: str,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a comment on a suggestion.

        Args:
            suggestion_id: Suggestion ID
            text: Comment text
            user_email: Email of commenting user

        Returns:
            Created comment data

        Example:
            >>> comment = await uservoice.create_comment(
            ...     suggestion_id=98765,
            ...     text="Great idea! We're planning this for Q2.",
            ...     user_email="admin@example.com"
            ... )
        """
        data = {
            'comment': {
                'suggestion_id': suggestion_id,
                'text': text
            }
        }

        if user_email:
            data['comment']['user_email'] = user_email

        result = await self._make_request(
            method='POST',
            endpoint='/comments.json',
            data=data
        )

        logger.info(
            "uservoice_comment_created",
            comment_id=result.get('comment', {}).get('id'),
            suggestion_id=suggestion_id
        )

        return result.get('comment', {})

    # ===================================================================
    # USERS API
    # ===================================================================

    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User details
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/users/{user_id}.json'
        )

        return result.get('user', {})

    async def get_current_user(self) -> Dict[str, Any]:
        """
        Get current authenticated user.

        Returns:
            Current user details
        """
        result = await self._make_request(
            method='GET',
            endpoint='/users/current.json'
        )

        return result.get('user', {})

    async def search_users(
        self,
        query: str,
        per_page: int = 50,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Search users.

        Args:
            query: Search query (name or email)
            per_page: Results per page
            page: Page number

        Returns:
            Matching users
        """
        params = {
            'query': query,
            'per_page': min(per_page, 100),
            'page': page
        }

        return await self._make_request(
            method='GET',
            endpoint='/users/search.json',
            params=params
        )

    # ===================================================================
    # ANALYTICS API
    # ===================================================================

    async def get_suggestion_analytics(
        self,
        suggestion_id: int
    ) -> Dict[str, Any]:
        """
        Get analytics for a suggestion.

        Args:
            suggestion_id: Suggestion ID

        Returns:
            Analytics data with vote trends, view counts, etc.
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/suggestions/{suggestion_id}/analytics.json'
        )

        return result

    async def get_forum_analytics(
        self,
        forum_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a forum.

        Args:
            forum_id: Forum ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Forum analytics with suggestion counts, vote trends, etc.

        Example:
            >>> analytics = await uservoice.get_forum_analytics(
            ...     forum_id=12345,
            ...     start_date="2024-01-01",
            ...     end_date="2024-12-31"
            ... )
        """
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        result = await self._make_request(
            method='GET',
            endpoint=f'/forums/{forum_id}/analytics.json',
            params=params
        )

        return result
