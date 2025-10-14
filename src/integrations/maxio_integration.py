"""
Maxio (formerly Chargify) Integration
Priority Score: 10
ICP Adoption: 30-40% of B2B SaaS companies

Subscription billing and revenue management platform providing:
- Customers and Subscriptions
- Products and Pricing
- Invoices
- Usage-based Billing
- Webhooks
- Dunning Management
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


class MaxioIntegration(BaseIntegration):
    """
    Maxio API integration with API key authentication.

    Authentication:
    - API Key in HTTP Basic Auth (username: API key, password: 'x')
    - Subdomain required for API URL

    Rate Limits:
    - 1000 requests per hour
    - Burst: 10 requests per second

    Documentation: https://maxio-chargify.zendesk.com/hc/en-us/sections/360008239754-API-Documentation
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ):
        """
        Initialize Maxio integration.

        Args:
            credentials: Maxio credentials
                - api_key: Maxio API key
                - subdomain: Maxio subdomain (e.g., 'acme')
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="maxio",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        self.subdomain = credentials.get('subdomain', '')

        if not self.api_key:
            raise ValidationError("Maxio api_key is required")
        if not self.subdomain:
            raise ValidationError("Maxio subdomain is required")

        self.base_url = f"https://{self.subdomain}.chargify.com"

        logger.info(
            "maxio_initialized",
            subdomain=self.subdomain,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Maxio (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("maxio_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Maxio authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Maxio API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Maxio uses HTTP Basic Auth with API key as username and 'x' as password
        import aiohttp
        auth = aiohttp.BasicAuth(login=self.api_key, password='x')

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
                        f"Maxio API error ({response.status}): {error_text}",
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
        """Test connection to Maxio API."""
        try:
            start_time = datetime.now()

            # Test with customers list request
            response = await self._make_request(
                method='GET',
                endpoint='/customers.json',
                params={'per_page': 1}
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Maxio",
                response_time_ms=duration_ms,
                metadata={
                    'subdomain': self.subdomain,
                    'integration_name': 'maxio'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Maxio connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # CUSTOMERS API
    # ===================================================================

    async def list_customers(
        self,
        page: int = 1,
        per_page: int = 50,
        direction: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        List customers.

        Args:
            page: Page number
            per_page: Results per page (max: 200)
            direction: Sort direction (asc, desc)

        Returns:
            List of customers

        Example:
            >>> customers = await maxio.list_customers(
            ...     page=1,
            ...     per_page=25
            ... )
        """
        params = {
            'page': page,
            'per_page': min(per_page, 200),
            'direction': direction
        }

        result = await self._make_request(
            method='GET',
            endpoint='/customers.json',
            params=params
        )

        logger.info(
            "maxio_customers_listed",
            count=len(result)
        )

        return result

    async def get_customer(self, customer_id: int) -> Dict[str, Any]:
        """
        Get customer by ID.

        Args:
            customer_id: Customer ID

        Returns:
            Customer details
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/customers/{customer_id}.json'
        )

        return result.get('customer', {})

    async def create_customer(
        self,
        first_name: str,
        last_name: str,
        email: str,
        organization: Optional[str] = None,
        reference: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip: Optional[str] = None,
        country: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a customer.

        Args:
            first_name: First name
            last_name: Last name
            email: Email address
            organization: Company/organization name
            reference: External reference ID
            address: Street address
            city: City
            state: State/province
            zip: Postal code
            country: Country code
            phone: Phone number

        Returns:
            Created customer data

        Example:
            >>> customer = await maxio.create_customer(
            ...     first_name="Jane",
            ...     last_name="Doe",
            ...     email="jane@acme.com",
            ...     organization="Acme Corp",
            ...     address="123 Main St",
            ...     city="San Francisco",
            ...     state="CA",
            ...     zip="94105",
            ...     country="US"
            ... )
        """
        data = {
            'customer': {
                'first_name': first_name,
                'last_name': last_name,
                'email': email
            }
        }

        if organization:
            data['customer']['organization'] = organization
        if reference:
            data['customer']['reference'] = reference
        if address:
            data['customer']['address'] = address
        if city:
            data['customer']['city'] = city
        if state:
            data['customer']['state'] = state
        if zip:
            data['customer']['zip'] = zip
        if country:
            data['customer']['country'] = country
        if phone:
            data['customer']['phone'] = phone

        result = await self._make_request(
            method='POST',
            endpoint='/customers.json',
            data=data
        )

        logger.info(
            "maxio_customer_created",
            customer_id=result.get('customer', {}).get('id'),
            email=email
        )

        return result.get('customer', {})

    async def update_customer(
        self,
        customer_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        organization: Optional[str] = None,
        reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a customer.

        Args:
            customer_id: Customer ID
            first_name: New first name
            last_name: New last name
            email: New email
            organization: New organization
            reference: New reference

        Returns:
            Updated customer data
        """
        data = {'customer': {}}

        if first_name:
            data['customer']['first_name'] = first_name
        if last_name:
            data['customer']['last_name'] = last_name
        if email:
            data['customer']['email'] = email
        if organization:
            data['customer']['organization'] = organization
        if reference:
            data['customer']['reference'] = reference

        result = await self._make_request(
            method='PUT',
            endpoint=f'/customers/{customer_id}.json',
            data=data
        )

        logger.info(
            "maxio_customer_updated",
            customer_id=customer_id
        )

        return result.get('customer', {})

    # ===================================================================
    # SUBSCRIPTIONS API
    # ===================================================================

    async def list_subscriptions(
        self,
        page: int = 1,
        per_page: int = 50,
        state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List subscriptions.

        Args:
            page: Page number
            per_page: Results per page
            state: Filter by state (active, canceled, expired, on_hold, past_due)

        Returns:
            List of subscriptions

        Example:
            >>> subs = await maxio.list_subscriptions(
            ...     state="active",
            ...     per_page=25
            ... )
        """
        params = {
            'page': page,
            'per_page': min(per_page, 200)
        }

        if state:
            params['state'] = state

        result = await self._make_request(
            method='GET',
            endpoint='/subscriptions.json',
            params=params
        )

        logger.info(
            "maxio_subscriptions_listed",
            count=len(result),
            state=state
        )

        return result

    async def get_subscription(self, subscription_id: int) -> Dict[str, Any]:
        """
        Get subscription by ID.

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription details with product and pricing info
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/subscriptions/{subscription_id}.json'
        )

        return result.get('subscription', {})

    async def create_subscription(
        self,
        customer_id: int,
        product_handle: str,
        credit_card_attributes: Optional[Dict[str, Any]] = None,
        next_billing_at: Optional[str] = None,
        components: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription.

        Args:
            customer_id: Customer ID
            product_handle: Product handle/identifier
            credit_card_attributes: Payment method details
            next_billing_at: Next billing date (ISO format)
            components: List of subscription components

        Returns:
            Created subscription data

        Example:
            >>> subscription = await maxio.create_subscription(
            ...     customer_id=123,
            ...     product_handle="enterprise-monthly",
            ...     components=[
            ...         {"component_id": 456, "allocated_quantity": 10}
            ...     ]
            ... )
        """
        data = {
            'subscription': {
                'customer_id': customer_id,
                'product_handle': product_handle
            }
        }

        if credit_card_attributes:
            data['subscription']['credit_card_attributes'] = credit_card_attributes
        if next_billing_at:
            data['subscription']['next_billing_at'] = next_billing_at
        if components:
            data['subscription']['components'] = components

        result = await self._make_request(
            method='POST',
            endpoint='/subscriptions.json',
            data=data
        )

        logger.info(
            "maxio_subscription_created",
            subscription_id=result.get('subscription', {}).get('id'),
            product_handle=product_handle
        )

        return result.get('subscription', {})

    async def update_subscription(
        self,
        subscription_id: int,
        next_billing_at: Optional[str] = None,
        custom_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Update a subscription.

        Args:
            subscription_id: Subscription ID
            next_billing_at: New next billing date
            custom_price: Custom price override

        Returns:
            Updated subscription data
        """
        data = {'subscription': {}}

        if next_billing_at:
            data['subscription']['next_billing_at'] = next_billing_at
        if custom_price is not None:
            data['subscription']['custom_price'] = custom_price

        result = await self._make_request(
            method='PUT',
            endpoint=f'/subscriptions/{subscription_id}.json',
            data=data
        )

        logger.info(
            "maxio_subscription_updated",
            subscription_id=subscription_id
        )

        return result.get('subscription', {})

    async def cancel_subscription(
        self,
        subscription_id: int,
        cancellation_message: Optional[str] = None,
        cancel_at_end_of_period: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            subscription_id: Subscription ID
            cancellation_message: Reason for cancellation
            cancel_at_end_of_period: Cancel at end of billing period

        Returns:
            Cancelled subscription data
        """
        data = {'subscription': {}}

        if cancellation_message:
            data['subscription']['cancellation_message'] = cancellation_message
        if cancel_at_end_of_period:
            data['subscription']['cancel_at_end_of_period'] = cancel_at_end_of_period

        result = await self._make_request(
            method='DELETE',
            endpoint=f'/subscriptions/{subscription_id}.json',
            data=data
        )

        logger.info(
            "maxio_subscription_cancelled",
            subscription_id=subscription_id,
            cancel_at_end_of_period=cancel_at_end_of_period
        )

        return result.get('subscription', {})

    # ===================================================================
    # PRODUCTS API
    # ===================================================================

    async def list_products(
        self,
        page: int = 1,
        per_page: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List products.

        Args:
            page: Page number
            per_page: Results per page

        Returns:
            List of products
        """
        params = {
            'page': page,
            'per_page': min(per_page, 200)
        }

        return await self._make_request(
            method='GET',
            endpoint='/products.json',
            params=params
        )

    async def get_product(self, product_id: int) -> Dict[str, Any]:
        """
        Get product by ID.

        Args:
            product_id: Product ID

        Returns:
            Product details with pricing
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/products/{product_id}.json'
        )

        return result.get('product', {})

    async def get_product_by_handle(self, handle: str) -> Dict[str, Any]:
        """
        Get product by handle.

        Args:
            handle: Product handle

        Returns:
            Product details
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/products/handle/{handle}.json'
        )

        return result.get('product', {})

    # ===================================================================
    # COMPONENTS (USAGE) API
    # ===================================================================

    async def list_components(
        self,
        subscription_id: int
    ) -> List[Dict[str, Any]]:
        """
        List subscription components.

        Args:
            subscription_id: Subscription ID

        Returns:
            List of components
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/subscriptions/{subscription_id}/components.json'
        )

    async def allocate_component(
        self,
        subscription_id: int,
        component_id: int,
        quantity: int,
        memo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Allocate component quantity (for usage-based billing).

        Args:
            subscription_id: Subscription ID
            component_id: Component ID
            quantity: Quantity to allocate
            memo: Allocation memo/note

        Returns:
            Allocation result

        Example:
            >>> await maxio.allocate_component(
            ...     subscription_id=123,
            ...     component_id=456,
            ...     quantity=1000,
            ...     memo="API calls usage for January"
            ... )
        """
        data = {
            'allocation': {
                'quantity': quantity
            }
        }

        if memo:
            data['allocation']['memo'] = memo

        result = await self._make_request(
            method='POST',
            endpoint=f'/subscriptions/{subscription_id}/components/{component_id}/allocations.json',
            data=data
        )

        logger.info(
            "maxio_component_allocated",
            subscription_id=subscription_id,
            component_id=component_id,
            quantity=quantity
        )

        return result

    async def create_usage(
        self,
        subscription_id: int,
        component_id: int,
        quantity: float,
        memo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create usage record.

        Args:
            subscription_id: Subscription ID
            component_id: Component ID
            quantity: Usage quantity
            memo: Usage memo/description

        Returns:
            Usage record

        Example:
            >>> await maxio.create_usage(
            ...     subscription_id=123,
            ...     component_id=456,
            ...     quantity=500,
            ...     memo="API calls for 2025-01-15"
            ... )
        """
        data = {
            'usage': {
                'quantity': quantity
            }
        }

        if memo:
            data['usage']['memo'] = memo

        result = await self._make_request(
            method='POST',
            endpoint=f'/subscriptions/{subscription_id}/components/{component_id}/usages.json',
            data=data
        )

        logger.info(
            "maxio_usage_created",
            subscription_id=subscription_id,
            component_id=component_id,
            quantity=quantity
        )

        return result

    # ===================================================================
    # INVOICES API
    # ===================================================================

    async def list_invoices(
        self,
        page: int = 1,
        per_page: int = 50,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List invoices.

        Args:
            page: Page number
            per_page: Results per page
            status: Filter by status (open, paid, voided)

        Returns:
            List of invoices
        """
        params = {
            'page': page,
            'per_page': min(per_page, 200)
        }

        if status:
            params['status'] = status

        result = await self._make_request(
            method='GET',
            endpoint='/invoices.json',
            params=params
        )

        logger.info(
            "maxio_invoices_listed",
            count=len(result),
            status=status
        )

        return result

    async def get_invoice(self, invoice_id: int) -> Dict[str, Any]:
        """
        Get invoice by ID.

        Args:
            invoice_id: Invoice ID

        Returns:
            Invoice details with line items
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/invoices/{invoice_id}.json'
        )

        return result.get('invoice', {})

    async def list_subscription_invoices(
        self,
        subscription_id: int
    ) -> List[Dict[str, Any]]:
        """
        List invoices for a subscription.

        Args:
            subscription_id: Subscription ID

        Returns:
            List of invoices
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/subscriptions/{subscription_id}/invoices.json'
        )

    # ===================================================================
    # WEBHOOKS API
    # ===================================================================

    async def list_webhooks(self) -> List[Dict[str, Any]]:
        """
        List webhook endpoints.

        Returns:
            List of webhook configurations
        """
        return await self._make_request(
            method='GET',
            endpoint='/webhooks.json'
        )

    async def create_webhook(
        self,
        url: str,
        events: List[str]
    ) -> Dict[str, Any]:
        """
        Create webhook endpoint.

        Args:
            url: Webhook URL
            events: List of event types to subscribe to

        Returns:
            Created webhook configuration

        Example:
            >>> webhook = await maxio.create_webhook(
            ...     url="https://example.com/webhooks/maxio",
            ...     events=[
            ...         "subscription_state_change",
            ...         "payment_success",
            ...         "payment_failure"
            ...     ]
            ... )
        """
        data = {
            'webhook': {
                'url': url,
                'events': events
            }
        }

        result = await self._make_request(
            method='POST',
            endpoint='/webhooks.json',
            data=data
        )

        logger.info(
            "maxio_webhook_created",
            url=url,
            event_count=len(events)
        )

        return result.get('webhook', {})

    async def delete_webhook(self, webhook_id: int) -> Dict[str, Any]:
        """
        Delete webhook endpoint.

        Args:
            webhook_id: Webhook ID

        Returns:
            Deletion confirmation
        """
        result = await self._make_request(
            method='DELETE',
            endpoint=f'/webhooks/{webhook_id}.json'
        )

        logger.info(
            "maxio_webhook_deleted",
            webhook_id=webhook_id
        )

        return result

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("maxio_session_closed")
