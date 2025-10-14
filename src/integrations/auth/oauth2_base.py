"""
OAuth2 Base Integration
Provides reusable OAuth2 authentication for 70% of integrations
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import aiohttp
import structlog
from abc import abstractmethod

from ..base import (
    BaseIntegration,
    IntegrationStatus,
    ConnectionTestResult,
    AuthenticationError,
    APIError,
)

logger = structlog.get_logger(__name__)


class OAuth2Integration(BaseIntegration):
    """
    Base class for OAuth2-based integrations.

    Handles:
    - Token refresh logic
    - Authorization code flow
    - Token storage and encryption
    - Automatic token renewal

    Subclasses only need to implement:
    - get_oauth_config() - OAuth endpoints and scopes
    - test_connection() - Connection test specific to service
    - Service-specific API methods

    Usage:
        class HubSpotIntegration(OAuth2Integration):
            def get_oauth_config(self) -> Dict[str, Any]:
                return {
                    'auth_url': 'https://app.hubspot.com/oauth/authorize',
                    'token_url': 'https://api.hubapi.com/oauth/v1/token',
                    'scopes': ['crm.objects.contacts.read', 'crm.objects.deals.read']
                }
    """

    def __init__(
        self,
        integration_name: str,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize OAuth2 integration.

        Args:
            integration_name: Name of the integration
            credentials: Dict with OAuth2 credentials:
                - client_id: OAuth client ID
                - client_secret: OAuth client secret
                - access_token: Current access token (optional)
                - refresh_token: Refresh token
                - token_expires_at: Token expiration timestamp (optional)
            rate_limit_calls: Max API calls per window
            rate_limit_window: Rate limit window in seconds
            max_retries: Maximum retry attempts
        """
        super().__init__(
            integration_name=integration_name,
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=max_retries
        )

        self.session: Optional[aiohttp.ClientSession] = None
        self.token_expires_at: Optional[datetime] = None

        # Parse token expiration if provided
        if 'token_expires_at' in credentials:
            try:
                self.token_expires_at = datetime.fromisoformat(
                    credentials['token_expires_at']
                )
            except (ValueError, TypeError):
                self.token_expires_at = None

        logger.info(
            "oauth2_integration_initialized",
            integration=integration_name
        )

    @abstractmethod
    def get_oauth_config(self) -> Dict[str, Any]:
        """
        Get OAuth2 configuration for this integration.

        Returns:
            Dict with:
                - auth_url: Authorization endpoint
                - token_url: Token endpoint
                - scopes: List of OAuth scopes
                - redirect_uri: Redirect URI (optional)
                - extra_params: Extra params for auth (optional)

        Example:
            return {
                'auth_url': 'https://api.example.com/oauth/authorize',
                'token_url': 'https://api.example.com/oauth/token',
                'scopes': ['read', 'write'],
                'extra_params': {'response_type': 'code'}
            }
        """
        pass

    async def authenticate(self) -> bool:
        """
        Authenticate with OAuth2.

        If we have a valid access token, use it.
        If token is expired, refresh it.

        Returns:
            True if authentication successful

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Validate required credentials
            required_fields = ['client_id', 'client_secret']
            valid, error = self.validate_required_fields(
                self.credentials,
                required_fields
            )

            if not valid:
                raise AuthenticationError(error)

            # Create session if needed
            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            # Check if we need to refresh token
            if self._is_token_expired():
                await self._refresh_access_token()
            elif 'access_token' not in self.credentials:
                raise AuthenticationError(
                    "No access token available. Please authorize the integration first."
                )

            logger.info(
                "oauth2_authenticated",
                integration=self.integration_name
            )

            return True

        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(
                f"OAuth2 authentication failed: {str(e)}"
            )

    def _is_token_expired(self) -> bool:
        """Check if access token is expired or about to expire."""
        if not self.token_expires_at:
            # No expiration info, assume it might be expired
            return 'access_token' not in self.credentials

        # Refresh if token expires within 5 minutes
        return datetime.utcnow() >= self.token_expires_at - timedelta(minutes=5)

    async def _refresh_access_token(self) -> None:
        """
        Refresh the access token using refresh token.

        Raises:
            AuthenticationError: If refresh fails
        """
        if 'refresh_token' not in self.credentials:
            raise AuthenticationError(
                "No refresh token available. Please re-authorize."
            )

        config = self.get_oauth_config()
        token_url = config.get('token_url')

        if not token_url:
            raise AuthenticationError(
                "Token URL not configured for this integration"
            )

        try:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.credentials['refresh_token'],
                'client_id': self.credentials['client_id'],
                'client_secret': self.credentials['client_secret']
            }

            async with self.session.post(token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()

                    # Update credentials
                    self.credentials['access_token'] = token_data['access_token']

                    # Update refresh token if provided
                    if 'refresh_token' in token_data:
                        self.credentials['refresh_token'] = token_data['refresh_token']

                    # Calculate expiration
                    if 'expires_in' in token_data:
                        self.token_expires_at = datetime.utcnow() + timedelta(
                            seconds=token_data['expires_in']
                        )
                        self.credentials['token_expires_at'] = (
                            self.token_expires_at.isoformat()
                        )

                    logger.info(
                        "oauth2_token_refreshed",
                        integration=self.integration_name,
                        expires_at=self.token_expires_at.isoformat() if self.token_expires_at else None
                    )

                elif response.status == 401:
                    raise AuthenticationError(
                        "Refresh token is invalid or expired. Please re-authorize."
                    )
                else:
                    error_text = await response.text()
                    raise AuthenticationError(
                        f"Token refresh failed ({response.status}): {error_text}"
                    )

        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(
                f"Failed to refresh OAuth2 token: {str(e)}"
            )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        base_url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint path
            base_url: Base URL (if different from default)
            data: Request body (for POST/PUT/PATCH)
            params: Query parameters
            headers: Additional headers

        Returns:
            Response data as dictionary

        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
        """
        # Ensure we're authenticated
        await self.ensure_authenticated()

        # Prepare URL
        if base_url:
            url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        else:
            config = self.get_oauth_config()
            api_base = config.get('api_base_url', '')
            url = f"{api_base.rstrip('/')}/{endpoint.lstrip('/')}"

        # Prepare headers
        request_headers = {
            'Authorization': f"Bearer {self.credentials['access_token']}",
            'Content-Type': 'application/json',
        }
        if headers:
            request_headers.update(headers)

        # Make request with circuit breaker
        try:
            # Check circuit breaker
            if hasattr(self.circuit_breaker, 'state'):
                from ...core.circuit_breaker import CircuitState, CircuitBreakerError
                if self.circuit_breaker.state == CircuitState.OPEN:
                    if not self.circuit_breaker._should_attempt_reset():
                        raise CircuitBreakerError(
                            f"Circuit breaker '{self.circuit_breaker.name}' is OPEN"
                        )
                    else:
                        self.circuit_breaker._transition_to_half_open()

            async with self.session.request(
                method,
                url,
                json=data,
                params=params,
                headers=request_headers
            ) as response:
                # Handle response
                if response.status in (200, 201, 202, 204):
                    # Success
                    self.circuit_breaker._record_success(0.1)

                    if response.status == 204:
                        return {}

                    return await response.json()

                elif response.status == 401:
                    # Token might be expired, try refresh
                    await self._refresh_access_token()
                    raise AuthenticationError("Token expired, please retry")

                elif response.status == 429:
                    # Rate limited
                    retry_after = response.headers.get('Retry-After', 60)
                    error = APIError(
                        f"Rate limited. Retry after {retry_after}s",
                        429
                    )
                    self.circuit_breaker._record_failure(error)
                    raise error

                else:
                    # Other error
                    error_text = await response.text()
                    error = APIError(
                        f"API request failed ({response.status}): {error_text}",
                        response.status
                    )
                    self.circuit_breaker._record_failure(error)
                    raise error

        except (AuthenticationError, APIError):
            raise
        except Exception as e:
            self.circuit_breaker._record_failure(e)
            raise APIError(f"Request failed: {str(e)}")

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> str:
        """
        Generate OAuth2 authorization URL for user consent.

        Args:
            redirect_uri: Where to redirect after authorization
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL

        Example:
            >>> auth_url = integration.get_authorization_url(
            ...     redirect_uri='https://myapp.com/oauth/callback',
            ...     state='random_state_string'
            ... )
            >>> print(f"Please visit: {auth_url}")
        """
        config = self.get_oauth_config()

        params = {
            'client_id': self.credentials['client_id'],
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(config.get('scopes', []))
        }

        if state:
            params['state'] = state

        # Add extra params from config
        extra_params = config.get('extra_params', {})
        params.update(extra_params)

        # Build URL
        auth_url = config['auth_url']
        query_string = '&'.join(f"{k}={v}" for k, v in params.items())

        return f"{auth_url}?{query_string}"

    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str
    ) -> Dict[str, str]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Same redirect URI used in authorization

        Returns:
            Token data including access_token, refresh_token, expires_in

        Raises:
            AuthenticationError: If exchange fails
        """
        config = self.get_oauth_config()
        token_url = config['token_url']

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': self.credentials['client_id'],
            'client_secret': self.credentials['client_secret']
        }

        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.post(token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()

                    # Update credentials
                    self.credentials['access_token'] = token_data['access_token']
                    self.credentials['refresh_token'] = token_data.get('refresh_token', '')

                    # Calculate expiration
                    if 'expires_in' in token_data:
                        self.token_expires_at = datetime.utcnow() + timedelta(
                            seconds=token_data['expires_in']
                        )
                        self.credentials['token_expires_at'] = (
                            self.token_expires_at.isoformat()
                        )

                    logger.info(
                        "oauth2_code_exchanged",
                        integration=self.integration_name
                    )

                    return token_data
                else:
                    error_text = await response.text()
                    raise AuthenticationError(
                        f"Failed to exchange code for token ({response.status}): {error_text}"
                    )

        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(
                f"Code exchange failed: {str(e)}"
            )

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info(
                "oauth2_session_closed",
                integration=self.integration_name
            )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False
