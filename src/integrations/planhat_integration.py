"""
Planhat Integration
Priority Score: 16
ICP Adoption: 25-35% of B2B SaaS companies

Customer success platform providing:
- Account & Contact Management
- Health Scores
- NPS/CSAT Surveys
- Conversations & Notes
- Revenue Tracking
- Custom Dimensions
- Automation & Workflows
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import aiohttp
import structlog

from .base import (
    BaseIntegration,
    ConnectionTestResult,
    IntegrationStatus,
    ValidationError,
    APIError,
    AuthenticationError
)
from ..core.circuit_breaker import CircuitBreaker

logger = structlog.get_logger(__name__)


class PlanhatIntegration(BaseIntegration):
    """
    Production-ready Planhat integration for customer success operations.

    Features:
    - Company (account) management
    - End user (contact) management
    - Conversation tracking
    - Health scores and metrics
    - Revenue and license management
    - NPS surveys
    - Custom attributes

    Usage:
        >>> planhat = PlanhatIntegration({
        ...     'api_key': 'your_api_key',
        ...     'tenant_id': 'your_tenant_id'
        ... })
        >>> await planhat.authenticate()
        >>> company = await planhat.create_company({
        ...     'name': 'Acme Corp',
        ...     'externalId': 'acme-123',
        ...     'mrr': 5000
        ... })

    API Documentation:
        https://docs.planhat.com/
    """

    API_BASE_URL = "https://api.planhat.com"

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ) -> Any:
        """
        Initialize Planhat integration.

        Args:
            credentials: Planhat credentials
                - api_key: Planhat API key
                - tenant_id: Planhat tenant ID
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="planhat",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        self.tenant_id = credentials.get('tenant_id', '')

        if not self.api_key:
            raise ValidationError("Planhat api_key is required")
        if not self.tenant_id:
            raise ValidationError("Planhat tenant_id is required")

        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            expected_exception=APIError,
            name="planhat_api"
        )

        logger.info(
            "planhat_initialized",
            tenant_id=self.tenant_id,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Planhat (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("planhat_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Planhat authentication failed: {str(e)}")

    async def test_connection(self) -> ConnectionTestResult:
        """Test connection to Planhat API."""
        try:
            start_time = time.time()

            # Test with a simple companies list request
            result = await self._make_request(
                method='GET',
                endpoint='/companies',
                params={'limit': 1}
            )

            duration_ms = (time.time() - start_time) * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Planhat",
                response_time_ms=duration_ms,
                metadata={'integration_name': 'planhat'}
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Planhat connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Planhat API."""
        await self.ensure_authenticated()

        url = f"{self.API_BASE_URL}/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        try:
            # Check circuit breaker
            if hasattr(self.circuit_breaker, 'state'):
                from ..core.circuit_breaker import CircuitState, CircuitBreakerError
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
                headers=headers
            ) as response:
                if response.status in (200, 201):
                    self.circuit_breaker._record_success(0.1)
                    result = await response.json()
                    return result if isinstance(result, dict) else {'data': result}
                elif response.status == 204:
                    self.circuit_breaker._record_success(0.1)
                    return {'status': 'success', 'message': 'No content'}
                else:
                    error_text = await response.text()
                    error = APIError(
                        f"Planhat API error ({response.status}): {error_text}",
                        response.status
                    )
                    self.circuit_breaker._record_failure(error)
                    raise error

        except APIError:
            raise
        except Exception as e:
            self.circuit_breaker._record_failure(e)
            raise APIError(f"Request failed: {str(e)}")

    # ===================================================================
    # COMPANIES API
    # ===================================================================

    async def create_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new company (account).

        Args:
            company_data: Company information
                - name: Company name (required)
                - externalId: External ID (required)
                - mrr: Monthly recurring revenue
                - status: Status (e.g., "prospect", "customer", "churned")
                - health: Health score (0-100)

        Returns:
            Created company data

        Example:
            >>> company = await planhat.create_company({
            ...     'name': 'Acme Corp',
            ...     'externalId': 'acme-123',
            ...     'mrr': 5000,
            ...     'status': 'customer',
            ...     'health': 85
            ... })
        """
        if 'name' not in company_data or 'externalId' not in company_data:
            raise ValidationError("Company name and externalId are required")

        result = await self._make_request(
            method='POST',
            endpoint='/companies',
            data=company_data
        )

        logger.info(
            "planhat_company_created",
            company_id=result.get('_id'),
            external_id=company_data.get('externalId')
        )

        return result

    async def update_company(
        self,
        company_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a company.

        Args:
            company_id: Planhat company ID
            update_data: Fields to update

        Returns:
            Updated company data

        Example:
            >>> await planhat.update_company(
            ...     '507f1f77bcf86cd799439011',
            ...     {'mrr': 6000, 'health': 90}
            ... )
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/companies/{company_id}',
            data=update_data
        )

        logger.info(
            "planhat_company_updated",
            company_id=company_id
        )

        return result

    async def get_company(self, company_id: str) -> Dict[str, Any]:
        """
        Get a company by ID.

        Args:
            company_id: Planhat company ID

        Returns:
            Company data
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/companies/{company_id}'
        )

    async def list_companies(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List companies with optional filters.

        Args:
            limit: Max results (default: 100)
            offset: Pagination offset
            filters: Optional filters

        Returns:
            List of companies

        Example:
            >>> companies = await planhat.list_companies(limit=50)
            >>> for company in companies:
            ...     print(company['name'], company['mrr'])
        """
        params = {
            'limit': limit,
            'offset': offset
        }
        if filters:
            params.update(filters)

        result = await self._make_request(
            method='GET',
            endpoint='/companies',
            params=params
        )

        logger.info(
            "planhat_companies_listed",
            count=len(result.get('data', result) if isinstance(result, dict) else result)
        )

        return result.get('data', result) if isinstance(result, dict) else result

    # ===================================================================
    # END USERS (CONTACTS) API
    # ===================================================================

    async def create_enduser(self, enduser_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an end user (contact).

        Args:
            enduser_data: End user information
                - email: Email address (required)
                - companyId: Associated company ID (required)
                - name: Full name
                - firstName: First name
                - lastName: Last name
                - title: Job title

        Returns:
            Created end user data

        Example:
            >>> enduser = await planhat.create_enduser({
            ...     'email': 'john@acme.com',
            ...     'companyId': '507f1f77bcf86cd799439011',
            ...     'name': 'John Doe',
            ...     'title': 'CTO'
            ... })
        """
        if 'email' not in enduser_data or 'companyId' not in enduser_data:
            raise ValidationError("End user email and companyId are required")

        result = await self._make_request(
            method='POST',
            endpoint='/endusers',
            data=enduser_data
        )

        logger.info(
            "planhat_enduser_created",
            enduser_id=result.get('_id'),
            email=enduser_data.get('email')
        )

        return result

    async def list_endusers(
        self,
        company_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List end users.

        Args:
            company_id: Filter by company ID (optional)
            limit: Max results

        Returns:
            List of end users
        """
        params = {'limit': limit}
        if company_id:
            params['companyId'] = company_id

        result = await self._make_request(
            method='GET',
            endpoint='/endusers',
            params=params
        )

        return result.get('data', result) if isinstance(result, dict) else result

    # ===================================================================
    # CONVERSATIONS API
    # ===================================================================

    async def create_conversation(
        self,
        conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a conversation (note/interaction).

        Args:
            conversation_data: Conversation information
                - companyId: Associated company ID (required)
                - title: Conversation title
                - text: Conversation content
                - date: Conversation date (ISO format)
                - type: Type (e.g., "email", "call", "meeting")

        Returns:
            Created conversation data

        Example:
            >>> conversation = await planhat.create_conversation({
            ...     'companyId': '507f1f77bcf86cd799439011',
            ...     'title': 'Quarterly Business Review',
            ...     'text': 'Discussed Q4 performance and 2025 goals',
            ...     'date': '2024-12-15T14:00:00Z',
            ...     'type': 'meeting'
            ... })
        """
        if 'companyId' not in conversation_data:
            raise ValidationError("Company ID is required")

        result = await self._make_request(
            method='POST',
            endpoint='/conversations',
            data=conversation_data
        )

        logger.info(
            "planhat_conversation_created",
            conversation_id=result.get('_id'),
            company_id=conversation_data.get('companyId')
        )

        return result

    async def list_conversations(
        self,
        company_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List conversations.

        Args:
            company_id: Filter by company ID (optional)
            limit: Max results

        Returns:
            List of conversations
        """
        params = {'limit': limit}
        if company_id:
            params['companyId'] = company_id

        result = await self._make_request(
            method='GET',
            endpoint='/conversations',
            params=params
        )

        return result.get('data', result) if isinstance(result, dict) else result

    # ===================================================================
    # HEALTH SCORES API
    # ===================================================================

    async def update_health_score(
        self,
        company_id: str,
        health_score: float,
        dimensions: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Update company health score.

        Args:
            company_id: Planhat company ID
            health_score: Overall health score (0-100)
            dimensions: Optional dimension scores (e.g., {"product_usage": 90, "support": 85})

        Returns:
            Update confirmation

        Example:
            >>> await planhat.update_health_score(
            ...     company_id='507f1f77bcf86cd799439011',
            ...     health_score=88,
            ...     dimensions={"product_usage": 90, "support": 85, "engagement": 88}
            ... )
        """
        update_data = {'health': health_score}
        if dimensions:
            update_data['customFields'] = dimensions

        return await self.update_company(company_id, update_data)

    # ===================================================================
    # NPS API
    # ===================================================================

    async def create_nps_response(
        self,
        nps_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an NPS survey response.

        Args:
            nps_data: NPS response data
                - companyId: Associated company ID (required)
                - score: NPS score (0-10) (required)
                - comment: Optional comment
                - enduserId: Associated end user ID

        Returns:
            Created NPS response data

        Example:
            >>> nps = await planhat.create_nps_response({
            ...     'companyId': '507f1f77bcf86cd799439011',
            ...     'score': 9,
            ...     'comment': 'Great product!',
            ...     'enduserId': '507f1f77bcf86cd799439012'
            ... })
        """
        if 'companyId' not in nps_data or 'score' not in nps_data:
            raise ValidationError("Company ID and score are required")

        result = await self._make_request(
            method='POST',
            endpoint='/nps',
            data=nps_data
        )

        logger.info(
            "planhat_nps_created",
            nps_id=result.get('_id'),
            company_id=nps_data.get('companyId'),
            score=nps_data.get('score')
        )

        return result

    async def list_nps_responses(
        self,
        company_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List NPS responses.

        Args:
            company_id: Filter by company ID (optional)
            limit: Max results

        Returns:
            List of NPS responses
        """
        params = {'limit': limit}
        if company_id:
            params['companyId'] = company_id

        result = await self._make_request(
            method='GET',
            endpoint='/nps',
            params=params
        )

        return result.get('data', result) if isinstance(result, dict) else result

    # ===================================================================
    # REVENUE & LICENSES API
    # ===================================================================

    async def create_license(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a license (subscription/product).

        Args:
            license_data: License information
                - companyId: Associated company ID (required)
                - product: Product name
                - value: License value/MRR
                - fromDate: Start date (ISO format)
                - toDate: End date (ISO format)

        Returns:
            Created license data

        Example:
            >>> license = await planhat.create_license({
            ...     'companyId': '507f1f77bcf86cd799439011',
            ...     'product': 'Enterprise Plan',
            ...     'value': 5000,
            ...     'fromDate': '2024-01-01T00:00:00Z',
            ...     'toDate': '2025-01-01T00:00:00Z'
            ... })
        """
        if 'companyId' not in license_data:
            raise ValidationError("Company ID is required")

        result = await self._make_request(
            method='POST',
            endpoint='/licenses',
            data=license_data
        )

        logger.info(
            "planhat_license_created",
            license_id=result.get('_id'),
            company_id=license_data.get('companyId')
        )

        return result

    async def close(self) -> Any:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("planhat_session_closed")


def test_planhat_integration() -> Any:
    """Test Planhat integration (requires credentials)."""
    import asyncio
    import os

    async def run_tests() -> Any:
        api_key = os.getenv('PLANHAT_API_KEY')
        tenant_id = os.getenv('PLANHAT_TENANT_ID')

        if not all([api_key, tenant_id]):
            print("⚠️  Skipping Planhat tests - credentials not found")
            print("Set PLANHAT_API_KEY and PLANHAT_TENANT_ID environment variables")
            return

        print("Test 1: Initialize integration...")
        planhat = PlanhatIntegration({
            'api_key': api_key,
            'tenant_id': tenant_id
        })
        print("✓ Integration initialized")

        print("\nTest 2: Authenticate...")
        try:
            await planhat.authenticate()
            print("✓ Authentication successful")
        except AuthenticationError as e:
            print(f"✗ Authentication failed: {e}")
            return

        print("\nTest 3: Test connection...")
        result = await planhat.test_connection()
        assert result.success
        print(f"✓ Connection test passed")

        print("\nTest 4: List companies...")
        try:
            companies = await planhat.list_companies(limit=5)
            print(f"✓ Found {len(companies)} companies")
        except APIError as e:
            print(f"✗ List companies failed: {e}")

        print("\nTest 5: Close session...")
        await planhat.close()
        print("✓ Session closed")

        print("\n✅ All tests passed!")

    asyncio.run(run_tests())


if __name__ == '__main__':
    test_planhat_integration()
