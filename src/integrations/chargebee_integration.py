"""
Chargebee Integration
Priority Score: 12
ICP Adoption: 45-55% of subscription businesses

Subscription billing and revenue management platform providing:
- Customers and Subscriptions
- Plans and Addons
- Invoices and Payments
- Usage Tracking
- Dunning Management
- Revenue Recognition
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


class ChargebeeIntegration(BaseIntegration):
    """
    Chargebee API integration with API key authentication.

    Authentication:
    - API Key in HTTP Basic Auth (username: API key, password: empty)
    - Site name required for API URL

    Rate Limits:
    - 160 requests per minute per site
    - Burst: 40 requests per 10 seconds

    Documentation: https://apidocs.chargebee.com/docs/api
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ):
        """
        Initialize Chargebee integration.

        Args:
            credentials: Chargebee credentials
                - api_key: Chargebee API key
                - site: Chargebee site name (e.g., 'acme' for acme.chargebee.com)
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="chargebee",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        self.site = credentials.get('site', '')

        if not self.api_key:
            raise ValidationError("Chargebee api_key is required")
        if not self.site:
            raise ValidationError("Chargebee site is required")

        self.base_url = f"https://{self.site}.chargebee.com/api/v2"

        logger.info(
            "chargebee_initialized",
            site=self.site,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Chargebee (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("chargebee_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Chargebee authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Chargebee API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Chargebee uses HTTP Basic Auth with API key as username
        import aiohttp
        auth = aiohttp.BasicAuth(login=self.api_key, password='')

        headers = {
            'Content-Type': 'application/json'
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
                if response.status in (200, 201, 202):
                    self.circuit_breaker._record_success(0.1)
                    return await response.json()
                else:
                    error_text = await response.text()
                    error = APIError(
                        f"Chargebee API error ({response.status}): {error_text}",
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
        """Test connection to Chargebee API."""
        try:
            start_time = datetime.now()

            # Test with customers list (limit 1)
            response = await self._make_request(
                method='GET',
                endpoint='/customers',
                params={'limit': 1}
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Chargebee",
                response_time_ms=duration_ms,
                metadata={
                    'site': self.site,
                    'integration_name': 'chargebee'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Chargebee connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # CUSTOMERS API
    # ===================================================================

    async def list_customers(
        self,
        limit: int = 50,
        offset: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List customers.

        Args:
            limit: Results limit (max: 100)
            offset: Pagination offset (Chargebee uses offset strings)
            sort_by: Sort field (created_at, updated_at)

        Returns:
            List of customers with pagination

        Example:
            >>> customers = await chargebee.list_customers(
            ...     limit=25,
            ...     sort_by="created_at"
            ... )
        """
        params = {
            'limit': min(limit, 100)
        }

        if offset:
            params['offset'] = offset
        if sort_by:
            params['sort_by[asc]'] = sort_by

        result = await self._make_request(
            method='GET',
            endpoint='/customers',
            params=params
        )

        logger.info(
            "chargebee_customers_listed",
            count=len(result.get('list', []))
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

        return result.get('customer', {})

    async def create_customer(
        self,
        customer_id: Optional[str] = None,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        phone: Optional[str] = None,
        billing_address: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a customer.

        Args:
            customer_id: Custom customer ID (auto-generated if not provided)
            email: Customer email
            first_name: First name
            last_name: Last name
            company: Company name
            phone: Phone number
            billing_address: Billing address dict
            metadata: Custom metadata

        Returns:
            Created customer data

        Example:
            >>> customer = await chargebee.create_customer(
            ...     email="jane@example.com",
            ...     first_name="Jane",
            ...     last_name="Doe",
            ...     company="Acme Corp",
            ...     billing_address={
            ...         "line1": "123 Main St",
            ...         "city": "San Francisco",
            ...         "state": "CA",
            ...         "zip": "94105",
            ...         "country": "US"
            ...     }
            ... )
        """
        data = {}

        if customer_id:
            data['id'] = customer_id
        if email:
            data['email'] = email
        if first_name:
            data['first_name'] = first_name
        if last_name:
            data['last_name'] = last_name
        if company:
            data['company'] = company
        if phone:
            data['phone'] = phone
        if billing_address:
            data['billing_address'] = billing_address
        if metadata:
            data['meta_data'] = metadata

        result = await self._make_request(
            method='POST',
            endpoint='/customers',
            data=data
        )

        logger.info(
            "chargebee_customer_created",
            customer_id=result.get('customer', {}).get('id'),
            email=email
        )

        return result.get('customer', {})

    async def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Update a customer.

        Args:
            customer_id: Customer ID
            email: New email
            first_name: New first name
            last_name: New last name
            company: New company name
            metadata: Updated metadata

        Returns:
            Updated customer data
        """
        data = {}

        if email:
            data['email'] = email
        if first_name:
            data['first_name'] = first_name
        if last_name:
            data['last_name'] = last_name
        if company:
            data['company'] = company
        if metadata:
            data['meta_data'] = metadata

        result = await self._make_request(
            method='POST',
            endpoint=f'/customers/{customer_id}',
            data=data
        )

        logger.info(
            "chargebee_customer_updated",
            customer_id=customer_id
        )

        return result.get('customer', {})

    # ===================================================================
    # SUBSCRIPTIONS API
    # ===================================================================

    async def list_subscriptions(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List subscriptions.

        Args:
            customer_id: Filter by customer ID
            status: Filter by status (active, cancelled, non_renewing, etc.)
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of subscriptions

        Example:
            >>> subs = await chargebee.list_subscriptions(
            ...     status="active",
            ...     limit=25
            ... )
        """
        params = {
            'limit': min(limit, 100)
        }

        if customer_id:
            params['customer_id[is]'] = customer_id
        if status:
            params['status[is]'] = status
        if offset:
            params['offset'] = offset

        result = await self._make_request(
            method='GET',
            endpoint='/subscriptions',
            params=params
        )

        logger.info(
            "chargebee_subscriptions_listed",
            count=len(result.get('list', [])),
            status=status
        )

        return result

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get subscription by ID.

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription details with plan and billing info
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/subscriptions/{subscription_id}'
        )

        return result.get('subscription', {})

    async def create_subscription(
        self,
        plan_id: str,
        customer_id: Optional[str] = None,
        customer_email: Optional[str] = None,
        billing_cycles: Optional[int] = None,
        trial_end: Optional[int] = None,
        addons: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription.

        Args:
            plan_id: Plan ID
            customer_id: Existing customer ID
            customer_email: Email for new customer
            billing_cycles: Number of billing cycles
            trial_end: Trial end timestamp (Unix seconds)
            addons: List of addons with quantities
            metadata: Custom metadata

        Returns:
            Created subscription data

        Example:
            >>> subscription = await chargebee.create_subscription(
            ...     plan_id="enterprise-monthly",
            ...     customer_id="cust_123",
            ...     addons=[
            ...         {"id": "addon_extra_users", "quantity": 5}
            ...     ],
            ...     trial_end=1704067200
            ... )
        """
        data = {
            'plan_id': plan_id
        }

        if customer_id:
            data['customer_id'] = customer_id
        if customer_email:
            data['customer[email]'] = customer_email
        if billing_cycles:
            data['billing_cycles'] = billing_cycles
        if trial_end:
            data['trial_end'] = trial_end
        if addons:
            for i, addon in enumerate(addons):
                data[f'addons[id][{i}]'] = addon['id']
                data[f'addons[quantity][{i}]'] = addon.get('quantity', 1)
        if metadata:
            data['meta_data'] = metadata

        result = await self._make_request(
            method='POST',
            endpoint='/subscriptions',
            data=data
        )

        logger.info(
            "chargebee_subscription_created",
            subscription_id=result.get('subscription', {}).get('id'),
            plan_id=plan_id
        )

        return result.get('subscription', {})

    async def update_subscription(
        self,
        subscription_id: str,
        plan_id: Optional[str] = None,
        billing_cycles: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Update a subscription.

        Args:
            subscription_id: Subscription ID
            plan_id: New plan ID
            billing_cycles: New billing cycles
            metadata: Updated metadata

        Returns:
            Updated subscription data
        """
        data = {}

        if plan_id:
            data['plan_id'] = plan_id
        if billing_cycles:
            data['billing_cycles'] = billing_cycles
        if metadata:
            data['meta_data'] = metadata

        result = await self._make_request(
            method='POST',
            endpoint=f'/subscriptions/{subscription_id}',
            data=data
        )

        logger.info(
            "chargebee_subscription_updated",
            subscription_id=subscription_id
        )

        return result.get('subscription', {})

    async def cancel_subscription(
        self,
        subscription_id: str,
        end_of_term: bool = True
    ) -> Dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            subscription_id: Subscription ID
            end_of_term: Cancel at end of term (default: True) vs immediately

        Returns:
            Cancelled subscription data
        """
        data = {
            'end_of_term': end_of_term
        }

        result = await self._make_request(
            method='POST',
            endpoint=f'/subscriptions/{subscription_id}/cancel',
            data=data
        )

        logger.info(
            "chargebee_subscription_cancelled",
            subscription_id=subscription_id,
            end_of_term=end_of_term
        )

        return result.get('subscription', {})

    # ===================================================================
    # PLANS API
    # ===================================================================

    async def list_plans(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List plans.

        Args:
            status: Filter by status (active, archived)
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of plans
        """
        params = {
            'limit': min(limit, 100)
        }

        if status:
            params['status[is]'] = status
        if offset:
            params['offset'] = offset

        return await self._make_request(
            method='GET',
            endpoint='/plans',
            params=params
        )

    async def get_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        Get plan by ID.

        Args:
            plan_id: Plan ID

        Returns:
            Plan details with pricing and features
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/plans/{plan_id}'
        )

        return result.get('plan', {})

    async def create_plan(
        self,
        plan_id: str,
        name: str,
        price: int,
        period: int,
        period_unit: str,
        currency_code: str = "USD",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a plan.

        Args:
            plan_id: Plan ID
            name: Plan name
            price: Price in cents
            period: Billing period (e.g., 1)
            period_unit: Period unit (day, week, month, year)
            currency_code: Currency code (default: USD)
            description: Plan description

        Returns:
            Created plan data

        Example:
            >>> plan = await chargebee.create_plan(
            ...     plan_id="enterprise-annual",
            ...     name="Enterprise Annual",
            ...     price=50000,  # $500.00 in cents
            ...     period=1,
            ...     period_unit="year",
            ...     description="Enterprise plan billed annually"
            ... )
        """
        data = {
            'id': plan_id,
            'name': name,
            'price': price,
            'period': period,
            'period_unit': period_unit,
            'currency_code': currency_code
        }

        if description:
            data['description'] = description

        result = await self._make_request(
            method='POST',
            endpoint='/plans',
            data=data
        )

        logger.info(
            "chargebee_plan_created",
            plan_id=plan_id,
            name=name
        )

        return result.get('plan', {})

    # ===================================================================
    # INVOICES API
    # ===================================================================

    async def list_invoices(
        self,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List invoices.

        Args:
            customer_id: Filter by customer ID
            status: Filter by status (paid, posted, payment_due, not_paid, voided)
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of invoices
        """
        params = {
            'limit': min(limit, 100)
        }

        if customer_id:
            params['customer_id[is]'] = customer_id
        if status:
            params['status[is]'] = status
        if offset:
            params['offset'] = offset

        result = await self._make_request(
            method='GET',
            endpoint='/invoices',
            params=params
        )

        logger.info(
            "chargebee_invoices_listed",
            count=len(result.get('list', [])),
            customer_id=customer_id,
            status=status
        )

        return result

    async def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Get invoice by ID.

        Args:
            invoice_id: Invoice ID

        Returns:
            Invoice details with line items and payment info
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/invoices/{invoice_id}'
        )

        return result.get('invoice', {})

    # ===================================================================
    # PAYMENTS API
    # ===================================================================

    async def list_transactions(
        self,
        customer_id: Optional[str] = None,
        limit: int = 50,
        offset: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List payment transactions.

        Args:
            customer_id: Filter by customer ID
            limit: Results limit
            offset: Pagination offset

        Returns:
            List of transactions
        """
        params = {
            'limit': min(limit, 100)
        }

        if customer_id:
            params['customer_id[is]'] = customer_id
        if offset:
            params['offset'] = offset

        return await self._make_request(
            method='GET',
            endpoint='/transactions',
            params=params
        )

    # ===================================================================
    # USAGE API
    # ===================================================================

    async def record_usage(
        self,
        subscription_id: str,
        item_price_id: str,
        quantity: int,
        usage_date: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Record usage for metered billing.

        Args:
            subscription_id: Subscription ID
            item_price_id: Item price ID (for usage-based items)
            quantity: Usage quantity
            usage_date: Usage date (Unix timestamp, default: now)

        Returns:
            Usage recording confirmation

        Example:
            >>> await chargebee.record_usage(
            ...     subscription_id="sub_123",
            ...     item_price_id="api_calls",
            ...     quantity=1000,
            ...     usage_date=1704067200
            ... )
        """
        data = {
            'subscription_id': subscription_id,
            'item_price_id': item_price_id,
            'quantity': quantity
        }

        if usage_date:
            data['usage_date'] = usage_date

        result = await self._make_request(
            method='POST',
            endpoint='/usages',
            data=data
        )

        logger.info(
            "chargebee_usage_recorded",
            subscription_id=subscription_id,
            quantity=quantity
        )

        return result

    # ===================================================================
    # DUNNING API
    # ===================================================================

    async def get_dunning_status(self, customer_id: str) -> Dict[str, Any]:
        """
        Get dunning status for customer.

        Args:
            customer_id: Customer ID

        Returns:
            Dunning status and retry schedule
        """
        result = await self._make_request(
            method='GET',
            endpoint=f'/customers/{customer_id}/dunning_status'
        )

        return result

    async def retry_payment(self, invoice_id: str) -> Dict[str, Any]:
        """
        Retry payment for an invoice.

        Args:
            invoice_id: Invoice ID

        Returns:
            Payment retry result
        """
        result = await self._make_request(
            method='POST',
            endpoint=f'/invoices/{invoice_id}/collect_payment'
        )

        logger.info(
            "chargebee_payment_retry",
            invoice_id=invoice_id
        )

        return result

    # ===================================================================
    # ESTIMATES API
    # ===================================================================

    async def create_subscription_estimate(
        self,
        plan_id: str,
        customer_id: Optional[str] = None,
        billing_cycles: Optional[int] = None,
        addons: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create subscription estimate (preview charges).

        Args:
            plan_id: Plan ID
            customer_id: Customer ID (optional)
            billing_cycles: Number of billing cycles
            addons: List of addons

        Returns:
            Subscription estimate with charges

        Example:
            >>> estimate = await chargebee.create_subscription_estimate(
            ...     plan_id="enterprise-monthly",
            ...     billing_cycles=12,
            ...     addons=[{"id": "addon_support", "quantity": 1}]
            ... )
        """
        data = {
            'subscription[plan_id]': plan_id
        }

        if customer_id:
            data['subscription[customer_id]'] = customer_id
        if billing_cycles:
            data['subscription[billing_cycles]'] = billing_cycles
        if addons:
            for i, addon in enumerate(addons):
                data[f'subscription[addons][id][{i}]'] = addon['id']
                data[f'subscription[addons][quantity][{i}]'] = addon.get('quantity', 1)

        result = await self._make_request(
            method='POST',
            endpoint='/estimates/create_subscription',
            data=data
        )

        return result.get('estimate', {})

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("chargebee_session_closed")
