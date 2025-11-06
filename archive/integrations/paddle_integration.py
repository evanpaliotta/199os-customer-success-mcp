"""
Paddle Integration
Priority Score: 10
ICP Adoption: 30-40% of SaaS companies (especially European)

Payment and subscription platform providing:
- Products and Pricing
- Subscriptions
- Transactions
- Webhooks
- Customer Management
- Tax Compliance
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


class PaddleIntegration(BaseIntegration):
    """
    Paddle API integration with API key authentication.

    Authentication:
    - API Key Bearer token
    - Vendor ID required for classic API
    - Separate Sandbox environment

    Rate Limits:
    - 300 requests per minute
    - Burst: 10 requests per second

    Documentation: https://developer.paddle.com/api-reference/overview
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ) -> Any:
        """
        Initialize Paddle integration.

        Args:
            credentials: Paddle credentials
                - api_key: Paddle API key
                - vendor_id: Paddle vendor ID (for classic API)
                - sandbox: Use sandbox environment (default: false)
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="paddle",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        self.vendor_id = credentials.get('vendor_id', '')
        self.sandbox = credentials.get('sandbox', 'false').lower() == 'true'

        if not self.api_key:
            raise ValidationError("Paddle api_key is required")

        # Paddle Billing API (new)
        if self.sandbox:
            self.base_url = "https://sandbox-api.paddle.com"
        else:
            self.base_url = "https://api.paddle.com"

        logger.info(
            "paddle_initialized",
            sandbox=self.sandbox,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Paddle (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("paddle_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Paddle authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Paddle API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
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
                        f"Paddle API error ({response.status}): {error_text}",
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
        """Test connection to Paddle API."""
        try:
            start_time = datetime.now()

            # Test with products list request
            response = await self._make_request(
                method='GET',
                endpoint='/products',
                params={'per_page': 1}
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Paddle",
                response_time_ms=duration_ms,
                metadata={
                    'integration_name': 'paddle',
                    'sandbox': self.sandbox
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Paddle connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # CUSTOMERS API
    # ===================================================================

    async def list_customers(
        self,
        email: Optional[str] = None,
        per_page: int = 50,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List customers.

        Args:
            email: Filter by email
            per_page: Results per page (max: 200)
            after: Pagination cursor

        Returns:
            List of customers with pagination

        Example:
            >>> customers = await paddle.list_customers(
            ...     per_page=25
            ... )
        """
        params = {
            'per_page': min(per_page, 200)
        }

        if email:
            params['email'] = email
        if after:
            params['after'] = after

        result = await self._make_request(
            method='GET',
            endpoint='/customers',
            params=params
        )

        logger.info(
            "paddle_customers_listed",
            count=len(result.get('data', []))
        )

        return result

    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """
        Get customer by ID.

        Args:
            customer_id: Customer ID

        Returns:
            Customer details
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/customers/{customer_id}'
        )

        return result.get('data', {})

    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        locale: Optional[str] = None,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a customer.

        Args:
            email: Customer email
            name: Customer name
            locale: Locale code (e.g., 'en', 'de')
            custom_data: Custom metadata

        Returns:
            Created customer data

        Example:
            >>> customer = await paddle.create_customer(
            ...     email="jane@acme.com",
            ...     name="Jane Doe",
            ...     locale="en",
            ...     custom_data={"company": "Acme Corp", "plan": "enterprise"}
            ... )
        """
        data = {'email': email}

        if name:
            data['name'] = name
        if locale:
            data['locale'] = locale
        if custom_data:
            data['custom_data'] = custom_data

        result = await self._make_request(
            method='POST',
            endpoint='/customers',
            data=data
        )

        logger.info(
            "paddle_customer_created",
            customer_id=result.get('data', {}).get('id'),
            email=email
        )

        return result.get('data', {})

    async def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update a customer.

        Args:
            customer_id: Customer ID
            email: New email
            name: New name
            custom_data: Updated custom data

        Returns:
            Updated customer data
        """
        data = {}

        if email:
            data['email'] = email
        if name:
            data['name'] = name
        if custom_data:
            data['custom_data'] = custom_data

        result = await self._make_request(
            method='PATCH',
            endpoint=f'/customers/{customer_id}',
            data=data
        )

        logger.info(
            "paddle_customer_updated",
            customer_id=customer_id
        )

        return result.get('data', {})

    # ===================================================================
    # PRODUCTS API
    # ===================================================================

    async def list_products(
        self,
        status: Optional[str] = None,
        per_page: int = 50,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List products.

        Args:
            status: Filter by status (active, archived)
            per_page: Results per page
            after: Pagination cursor

        Returns:
            List of products
        """
        params = {
            'per_page': min(per_page, 200)
        }

        if status:
            params['status'] = status
        if after:
            params['after'] = after

        return await self._make_request(
            method='GET',
            endpoint='/products',
            params=params
        )

    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """
        Get product by ID.

        Args:
            product_id: Product ID

        Returns:
            Product details with pricing
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/products/{product_id}'
        )

        return result.get('data', {})

    async def create_product(
        self,
        name: str,
        description: Optional[str] = None,
        tax_category: str = "standard",
        custom_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a product.

        Args:
            name: Product name
            description: Product description
            tax_category: Tax category (standard, digital-goods, etc.)
            custom_data: Custom metadata

        Returns:
            Created product data

        Example:
            >>> product = await paddle.create_product(
            ...     name="Enterprise Plan",
            ...     description="Enterprise subscription with premium features",
            ...     tax_category="digital-goods"
            ... )
        """
        data = {
            'name': name,
            'tax_category': tax_category
        }

        if description:
            data['description'] = description
        if custom_data:
            data['custom_data'] = custom_data

        result = await self._make_request(
            method='POST',
            endpoint='/products',
            data=data
        )

        logger.info(
            "paddle_product_created",
            product_id=result.get('data', {}).get('id'),
            name=name
        )

        return result.get('data', {})

    # ===================================================================
    # PRICES API
    # ===================================================================

    async def list_prices(
        self,
        product_id: Optional[str] = None,
        per_page: int = 50,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List prices.

        Args:
            product_id: Filter by product ID
            per_page: Results per page
            after: Pagination cursor

        Returns:
            List of prices
        """
        params = {
            'per_page': min(per_page, 200)
        }

        if product_id:
            params['product_id'] = product_id
        if after:
            params['after'] = after

        return await self._make_request(
            method='GET',
            endpoint='/prices',
            params=params
        )

    async def get_price(self, price_id: str) -> Dict[str, Any]:
        """
        Get price by ID.

        Args:
            price_id: Price ID

        Returns:
            Price details
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/prices/{price_id}'
        )

        return result.get('data', {})

    async def create_price(
        self,
        product_id: str,
        description: str,
        unit_price: Dict[str, str],
        billing_cycle: Optional[Dict[str, int]] = None,
        quantity: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Create a price.

        Args:
            product_id: Product ID
            description: Price description
            unit_price: Unit price dict with amount and currency_code
            billing_cycle: Billing cycle (interval and frequency)
            quantity: Quantity constraints (minimum, maximum)

        Returns:
            Created price data

        Example:
            >>> price = await paddle.create_price(
            ...     product_id="prod_123",
            ...     description="Monthly subscription",
            ...     unit_price={"amount": "5000", "currency_code": "USD"},
            ...     billing_cycle={"interval": "month", "frequency": 1}
            ... )
        """
        data = {
            'product_id': product_id,
            'description': description,
            'unit_price': unit_price
        }

        if billing_cycle:
            data['billing_cycle'] = billing_cycle
        if quantity:
            data['quantity'] = quantity

        result = await self._make_request(
            method='POST',
            endpoint='/prices',
            data=data
        )

        logger.info(
            "paddle_price_created",
            price_id=result.get('data', {}).get('id'),
            product_id=product_id
        )

        return result.get('data', {})

    # ===================================================================
    # SUBSCRIPTIONS API
    # ===================================================================

    async def list_subscriptions(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        per_page: int = 50,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List subscriptions.

        Args:
            customer_id: Filter by customer ID
            status: Filter by status (active, canceled, past_due, paused, trialing)
            per_page: Results per page
            after: Pagination cursor

        Returns:
            List of subscriptions

        Example:
            >>> subs = await paddle.list_subscriptions(
            ...     customer_id="ctm_123",
            ...     status="active"
            ... )
        """
        params = {
            'per_page': min(per_page, 200)
        }

        if customer_id:
            params['customer_id'] = customer_id
        if status:
            params['status'] = status
        if after:
            params['after'] = after

        result = await self._make_request(
            method='GET',
            endpoint='/subscriptions',
            params=params
        )

        logger.info(
            "paddle_subscriptions_listed",
            count=len(result.get('data', []))
        )

        return result

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get subscription by ID.

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription details with items and billing info
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/subscriptions/{subscription_id}'
        )

        return result.get('data', {})

    async def create_subscription(
        self,
        customer_id: str,
        items: List[Dict[str, Any]],
        billing_cycle: Optional[Dict[str, int]] = None,
        collection_mode: str = "automatic"
    ) -> Dict[str, Any]:
        """
        Create a subscription.

        Args:
            customer_id: Customer ID
            items: List of subscription items with price_id and quantity
            billing_cycle: Override billing cycle
            collection_mode: Payment collection mode (automatic, manual)

        Returns:
            Created subscription data

        Example:
            >>> subscription = await paddle.create_subscription(
            ...     customer_id="ctm_123",
            ...     items=[
            ...         {"price_id": "pri_456", "quantity": 1}
            ...     ],
            ...     collection_mode="automatic"
            ... )
        """
        data = {
            'customer_id': customer_id,
            'items': items,
            'collection_mode': collection_mode
        }

        if billing_cycle:
            data['billing_cycle'] = billing_cycle

        result = await self._make_request(
            method='POST',
            endpoint='/subscriptions',
            data=data
        )

        logger.info(
            "paddle_subscription_created",
            subscription_id=result.get('data', {}).get('id'),
            customer_id=customer_id
        )

        return result.get('data', {})

    async def update_subscription(
        self,
        subscription_id: str,
        items: Optional[List[Dict[str, Any]]] = None,
        proration_billing_mode: str = "prorated_immediately"
    ) -> Dict[str, Any]:
        """
        Update a subscription.

        Args:
            subscription_id: Subscription ID
            items: Updated subscription items
            proration_billing_mode: How to handle proration

        Returns:
            Updated subscription data
        """
        data = {
            'proration_billing_mode': proration_billing_mode
        }

        if items:
            data['items'] = items

        result = await self._make_request(
            method='PATCH',
            endpoint=f'/subscriptions/{subscription_id}',
            data=data
        )

        logger.info(
            "paddle_subscription_updated",
            subscription_id=subscription_id
        )

        return result.get('data', {})

    async def cancel_subscription(
        self,
        subscription_id: str,
        effective_from: str = "next_billing_period"
    ) -> Dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            subscription_id: Subscription ID
            effective_from: When to cancel (next_billing_period, immediately)

        Returns:
            Cancelled subscription data
        """
        data = {
            'effective_from': effective_from
        }

        result = await self._make_request(
            method='POST',
            endpoint=f'/subscriptions/{subscription_id}/cancel',
            data=data
        )

        logger.info(
            "paddle_subscription_cancelled",
            subscription_id=subscription_id,
            effective_from=effective_from
        )

        return result.get('data', {})

    async def pause_subscription(
        self,
        subscription_id: str,
        effective_from: str = "next_billing_period",
        resume_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pause a subscription.

        Args:
            subscription_id: Subscription ID
            effective_from: When to pause
            resume_at: When to resume (ISO date)

        Returns:
            Paused subscription data
        """
        data = {
            'effective_from': effective_from
        }

        if resume_at:
            data['resume_at'] = resume_at

        result = await self._make_request(
            method='POST',
            endpoint=f'/subscriptions/{subscription_id}/pause',
            data=data
        )

        logger.info(
            "paddle_subscription_paused",
            subscription_id=subscription_id
        )

        return result.get('data', {})

    # ===================================================================
    # TRANSACTIONS API
    # ===================================================================

    async def list_transactions(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        per_page: int = 50,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List transactions.

        Args:
            customer_id: Filter by customer ID
            status: Filter by status (draft, ready, billed, paid, completed, canceled)
            per_page: Results per page
            after: Pagination cursor

        Returns:
            List of transactions
        """
        params = {
            'per_page': min(per_page, 200)
        }

        if customer_id:
            params['customer_id'] = customer_id
        if status:
            params['status'] = status
        if after:
            params['after'] = after

        return await self._make_request(
            method='GET',
            endpoint='/transactions',
            params=params
        )

    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get transaction by ID.

        Args:
            transaction_id: Transaction ID

        Returns:
            Transaction details with items and payments
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/transactions/{transaction_id}'
        )

        return result.get('data', {})

    async def create_transaction(
        self,
        items: List[Dict[str, Any]],
        customer_id: Optional[str] = None,
        collection_mode: str = "automatic"
    ) -> Dict[str, Any]:
        """
        Create a transaction.

        Args:
            items: Transaction items with price_id and quantity
            customer_id: Customer ID (optional)
            collection_mode: Payment collection mode

        Returns:
            Created transaction data

        Example:
            >>> transaction = await paddle.create_transaction(
            ...     items=[
            ...         {"price_id": "pri_123", "quantity": 1}
            ...     ],
            ...     customer_id="ctm_456",
            ...     collection_mode="automatic"
            ... )
        """
        data = {
            'items': items,
            'collection_mode': collection_mode
        }

        if customer_id:
            data['customer_id'] = customer_id

        result = await self._make_request(
            method='POST',
            endpoint='/transactions',
            data=data
        )

        logger.info(
            "paddle_transaction_created",
            transaction_id=result.get('data', {}).get('id')
        )

        return result.get('data', {})

    # ===================================================================
    # WEBHOOKS API
    # ===================================================================

    async def list_notification_settings(self) -> Dict[str, Any]:
        """
        List webhook notification settings.

        Returns:
            List of notification settings
        """
        return await self._make_request(
            method='GET',
            endpoint='/notification-settings'
        )

    async def create_notification_setting(
        self,
        description: str,
        destination: str,
        subscribed_events: List[str],
        active: bool = True
    ) -> Dict[str, Any]:
        """
        Create webhook notification setting.

        Args:
            description: Setting description
            destination: Webhook URL
            subscribed_events: List of event types
            active: Whether setting is active

        Returns:
            Created notification setting

        Example:
            >>> webhook = await paddle.create_notification_setting(
            ...     description="Production webhook",
            ...     destination="https://example.com/webhooks/paddle",
            ...     subscribed_events=[
            ...         "subscription.created",
            ...         "subscription.updated",
            ...         "transaction.completed"
            ...     ],
            ...     active=True
            ... )
        """
        data = {
            'description': description,
            'destination': destination,
            'subscribed_events': [{'name': event} for event in subscribed_events],
            'active': active
        }

        result = await self._make_request(
            method='POST',
            endpoint='/notification-settings',
            data=data
        )

        logger.info(
            "paddle_notification_setting_created",
            destination=destination,
            event_count=len(subscribed_events)
        )

        return result.get('data', {})

    async def close(self) -> Any:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("paddle_session_closed")
