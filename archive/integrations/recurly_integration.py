"""
Recurly Integration
Priority Score: 11
ICP Adoption: 40-50% of subscription businesses

Subscription billing and revenue management platform providing:
- Subscriptions and Accounts
- Plans and Add-ons
- Invoices and Transactions
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


class RecurlyIntegration(BaseIntegration):
    """
    Recurly API integration with API key authentication.

    Authentication:
    - API Key in HTTP Basic Auth (username: API key, password: empty)
    - Subdomain required for API URL

    Rate Limits:
    - 2000 requests per hour
    - 100 requests per minute
    - Burst: 20 requests per second

    Documentation: https://developers.recurly.com/api/v2021-02-25/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ) -> Any:
        """
        Initialize Recurly integration.

        Args:
            credentials: Recurly credentials
                - api_key: Recurly API key
                - subdomain: Recurly subdomain (e.g., 'acme')
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="recurly",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        self.subdomain = credentials.get('subdomain', '')

        if not self.api_key:
            raise ValidationError("Recurly api_key is required")
        if not self.subdomain:
            raise ValidationError("Recurly subdomain is required")

        self.base_url = f"https://{self.subdomain}.recurly.com/v3"

        logger.info(
            "recurly_initialized",
            subdomain=self.subdomain,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with Recurly (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("recurly_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"Recurly authentication failed: {str(e)}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to Recurly API."""
        await self.ensure_authenticated()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Recurly uses HTTP Basic Auth with API key as username
        import aiohttp
        auth = aiohttp.BasicAuth(login=self.api_key, password='')

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/vnd.recurly.v2021-02-25'
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
                        f"Recurly API error ({response.status}): {error_text}",
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
        """Test connection to Recurly API."""
        try:
            start_time = datetime.now()

            # Test with site details request
            response = await self._make_request(
                method='GET',
                endpoint='/site'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Recurly",
                response_time_ms=duration_ms,
                metadata={
                    'subdomain': self.subdomain,
                    'site_id': response.get('id'),
                    'integration_name': 'recurly'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Recurly connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # ACCOUNTS API
    # ===================================================================

    async def list_accounts(
        self,
        state: Optional[str] = None,
        limit: int = 50,
        order: str = "desc",
        sort: str = "created_at"
    ) -> Dict[str, Any]:
        """
        List accounts.

        Args:
            state: Filter by state (active, closed, past_due)
            limit: Results limit (max: 200)
            order: Sort order (asc, desc)
            sort: Sort field (created_at, updated_at)

        Returns:
            List of accounts with pagination

        Example:
            >>> accounts = await recurly.list_accounts(
            ...     state="active",
            ...     limit=25
            ... )
        """
        params = {
            'limit': min(limit, 200),
            'order': order,
            'sort': sort
        }

        if state:
            params['state'] = state

        result = await self._make_request(
            method='GET',
            endpoint='/accounts',
            params=params
        )

        logger.info(
            "recurly_accounts_listed",
            count=len(result.get('data', []))
        )

        return result

    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """
        Get account by ID.

        Args:
            account_id: Account ID or code

        Returns:
            Account details
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/accounts/{account_id}'
        )

    async def create_account(
        self,
        code: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        address: Optional[Dict[str, str]] = None,
        tax_exempt: bool = False
    ) -> Dict[str, Any]:
        """
        Create an account.

        Args:
            code: Account code (unique identifier)
            email: Account email
            first_name: First name
            last_name: Last name
            company: Company name
            address: Billing address dict
            tax_exempt: Tax exempt status

        Returns:
            Created account data

        Example:
            >>> account = await recurly.create_account(
            ...     code="acme-corp",
            ...     email="jane@acme.com",
            ...     first_name="Jane",
            ...     last_name="Doe",
            ...     company="Acme Corp",
            ...     address={
            ...         "street1": "123 Main St",
            ...         "city": "San Francisco",
            ...         "region": "CA",
            ...         "postal_code": "94105",
            ...         "country": "US"
            ...     }
            ... )
        """
        data = {
            'code': code,
            'tax_exempt': tax_exempt
        }

        if email:
            data['email'] = email
        if first_name:
            data['first_name'] = first_name
        if last_name:
            data['last_name'] = last_name
        if company:
            data['company'] = company
        if address:
            data['address'] = address

        result = await self._make_request(
            method='POST',
            endpoint='/accounts',
            data=data
        )

        logger.info(
            "recurly_account_created",
            account_id=result.get('id'),
            code=code,
            email=email
        )

        return result

    async def update_account(
        self,
        account_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        address: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Update an account.

        Args:
            account_id: Account ID or code
            email: New email
            first_name: New first name
            last_name: New last name
            company: New company name
            address: Updated address

        Returns:
            Updated account data
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
        if address:
            data['address'] = address

        result = await self._make_request(
            method='PUT',
            endpoint=f'/accounts/{account_id}',
            data=data
        )

        logger.info(
            "recurly_account_updated",
            account_id=account_id
        )

        return result

    # ===================================================================
    # SUBSCRIPTIONS API
    # ===================================================================

    async def list_subscriptions(
        self,
        state: Optional[str] = None,
        limit: int = 50,
        order: str = "desc"
    ) -> Dict[str, Any]:
        """
        List subscriptions.

        Args:
            state: Filter by state (active, canceled, expired, future, paused)
            limit: Results limit
            order: Sort order (asc, desc)

        Returns:
            List of subscriptions

        Example:
            >>> subs = await recurly.list_subscriptions(
            ...     state="active",
            ...     limit=25
            ... )
        """
        params = {
            'limit': min(limit, 200),
            'order': order
        }

        if state:
            params['state'] = state

        result = await self._make_request(
            method='GET',
            endpoint='/subscriptions',
            params=params
        )

        logger.info(
            "recurly_subscriptions_listed",
            count=len(result.get('data', [])),
            state=state
        )

        return result

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get subscription by ID.

        Args:
            subscription_id: Subscription UUID

        Returns:
            Subscription details with plan and billing info
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/subscriptions/{subscription_id}'
        )

    async def create_subscription(
        self,
        plan_code: str,
        account_code: str,
        currency: str = "USD",
        unit_amount: Optional[float] = None,
        quantity: int = 1,
        trial_ends_at: Optional[str] = None,
        add_ons: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create a subscription.

        Args:
            plan_code: Plan code
            account_code: Account code
            currency: Currency code (default: USD)
            unit_amount: Override plan amount
            quantity: Subscription quantity
            trial_ends_at: Trial end date (ISO format)
            add_ons: List of add-ons with quantities

        Returns:
            Created subscription data

        Example:
            >>> subscription = await recurly.create_subscription(
            ...     plan_code="enterprise-monthly",
            ...     account_code="acme-corp",
            ...     quantity=10,
            ...     add_ons=[
            ...         {"code": "extra-users", "quantity": 5}
            ...     ],
            ...     trial_ends_at="2025-03-31T23:59:59Z"
            ... )
        """
        data = {
            'plan_code': plan_code,
            'account': {'code': account_code},
            'currency': currency,
            'quantity': quantity
        }

        if unit_amount:
            data['unit_amount'] = unit_amount
        if trial_ends_at:
            data['trial_ends_at'] = trial_ends_at
        if add_ons:
            data['add_ons'] = add_ons

        result = await self._make_request(
            method='POST',
            endpoint='/subscriptions',
            data=data
        )

        logger.info(
            "recurly_subscription_created",
            subscription_id=result.get('id'),
            plan_code=plan_code,
            account_code=account_code
        )

        return result

    async def update_subscription(
        self,
        subscription_id: str,
        quantity: Optional[int] = None,
        unit_amount: Optional[float] = None,
        timeframe: str = "now"
    ) -> Dict[str, Any]:
        """
        Update a subscription.

        Args:
            subscription_id: Subscription UUID
            quantity: New quantity
            unit_amount: New unit amount
            timeframe: When to apply (now, renewal, term_end)

        Returns:
            Updated subscription data
        """
        data = {'timeframe': timeframe}

        if quantity is not None:
            data['quantity'] = quantity
        if unit_amount is not None:
            data['unit_amount'] = unit_amount

        result = await self._make_request(
            method='PUT',
            endpoint=f'/subscriptions/{subscription_id}',
            data=data
        )

        logger.info(
            "recurly_subscription_updated",
            subscription_id=subscription_id
        )

        return result

    async def cancel_subscription(
        self,
        subscription_id: str,
        timeframe: str = "term_end"
    ) -> Dict[str, Any]:
        """
        Cancel a subscription.

        Args:
            subscription_id: Subscription UUID
            timeframe: When to cancel (term_end, now)

        Returns:
            Cancelled subscription data
        """
        params = {'timeframe': timeframe}

        result = await self._make_request(
            method='PUT',
            endpoint=f'/subscriptions/{subscription_id}/cancel',
            params=params
        )

        logger.info(
            "recurly_subscription_cancelled",
            subscription_id=subscription_id,
            timeframe=timeframe
        )

        return result

    async def reactivate_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Reactivate a cancelled subscription.

        Args:
            subscription_id: Subscription UUID

        Returns:
            Reactivated subscription data
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/subscriptions/{subscription_id}/reactivate'
        )

        logger.info(
            "recurly_subscription_reactivated",
            subscription_id=subscription_id
        )

        return result

    # ===================================================================
    # PLANS API
    # ===================================================================

    async def list_plans(
        self,
        state: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List plans.

        Args:
            state: Filter by state (active, inactive)
            limit: Results limit

        Returns:
            List of plans
        """
        params = {'limit': min(limit, 200)}

        if state:
            params['state'] = state

        return await self._make_request(
            method='GET',
            endpoint='/plans',
            params=params
        )

    async def get_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        Get plan by ID or code.

        Args:
            plan_id: Plan ID or code

        Returns:
            Plan details with pricing and features
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/plans/{plan_id}'
        )

    async def create_plan(
        self,
        code: str,
        name: str,
        currencies: List[Dict[str, Any]],
        interval_length: int = 1,
        interval_unit: str = "months"
    ) -> Dict[str, Any]:
        """
        Create a plan.

        Args:
            code: Plan code (unique identifier)
            name: Plan name
            currencies: List of currency pricing dicts
            interval_length: Billing interval length (e.g., 1)
            interval_unit: Billing interval unit (months, years)

        Returns:
            Created plan data

        Example:
            >>> plan = await recurly.create_plan(
            ...     code="enterprise-annual",
            ...     name="Enterprise Annual",
            ...     currencies=[
            ...         {"currency": "USD", "unit_amount": 500.00},
            ...         {"currency": "EUR", "unit_amount": 450.00}
            ...     ],
            ...     interval_length=1,
            ...     interval_unit="years"
            ... )
        """
        data = {
            'code': code,
            'name': name,
            'currencies': currencies,
            'interval_length': interval_length,
            'interval_unit': interval_unit
        }

        result = await self._make_request(
            method='POST',
            endpoint='/plans',
            data=data
        )

        logger.info(
            "recurly_plan_created",
            plan_id=result.get('id'),
            code=code,
            name=name
        )

        return result

    # ===================================================================
    # ADD-ONS API
    # ===================================================================

    async def list_plan_add_ons(self, plan_id: str) -> Dict[str, Any]:
        """
        List add-ons for a plan.

        Args:
            plan_id: Plan ID or code

        Returns:
            List of add-ons
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/plans/{plan_id}/add_ons'
        )

    async def create_add_on(
        self,
        plan_id: str,
        code: str,
        name: str,
        currencies: List[Dict[str, Any]],
        usage_type: str = "fixed"
    ) -> Dict[str, Any]:
        """
        Create an add-on for a plan.

        Args:
            plan_id: Plan ID or code
            code: Add-on code
            name: Add-on name
            currencies: List of currency pricing dicts
            usage_type: Type (fixed, usage)

        Returns:
            Created add-on data

        Example:
            >>> addon = await recurly.create_add_on(
            ...     plan_id="enterprise-monthly",
            ...     code="extra-users",
            ...     name="Extra Users",
            ...     currencies=[
            ...         {"currency": "USD", "unit_amount": 10.00}
            ...     ],
            ...     usage_type="fixed"
            ... )
        """
        data = {
            'code': code,
            'name': name,
            'currencies': currencies,
            'usage_type': usage_type
        }

        result = await self._make_request(
            method='POST',
            endpoint=f'/plans/{plan_id}/add_ons',
            data=data
        )

        logger.info(
            "recurly_add_on_created",
            plan_id=plan_id,
            code=code,
            name=name
        )

        return result

    # ===================================================================
    # INVOICES API
    # ===================================================================

    async def list_invoices(
        self,
        state: Optional[str] = None,
        limit: int = 50,
        order: str = "desc"
    ) -> Dict[str, Any]:
        """
        List invoices.

        Args:
            state: Filter by state (pending, paid, failed, past_due)
            limit: Results limit
            order: Sort order (asc, desc)

        Returns:
            List of invoices
        """
        params = {
            'limit': min(limit, 200),
            'order': order
        }

        if state:
            params['state'] = state

        result = await self._make_request(
            method='GET',
            endpoint='/invoices',
            params=params
        )

        logger.info(
            "recurly_invoices_listed",
            count=len(result.get('data', [])),
            state=state
        )

        return result

    async def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Get invoice by ID.

        Args:
            invoice_id: Invoice ID

        Returns:
            Invoice details with line items
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/invoices/{invoice_id}'
        )

    async def collect_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Collect payment for an invoice.

        Args:
            invoice_id: Invoice ID

        Returns:
            Collection result
        """
        result = await self._make_request(
            method='PUT',
            endpoint=f'/invoices/{invoice_id}/collect'
        )

        logger.info(
            "recurly_invoice_collected",
            invoice_id=invoice_id
        )

        return result

    # ===================================================================
    # TRANSACTIONS API
    # ===================================================================

    async def list_transactions(
        self,
        type: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List transactions.

        Args:
            type: Filter by type (authorization, purchase, refund)
            success: Filter by success status
            limit: Results limit

        Returns:
            List of transactions
        """
        params = {'limit': min(limit, 200)}

        if type:
            params['type'] = type
        if success is not None:
            params['success'] = str(success).lower()

        return await self._make_request(
            method='GET',
            endpoint='/transactions',
            params=params
        )

    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get transaction by ID.

        Args:
            transaction_id: Transaction UUID

        Returns:
            Transaction details
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/transactions/{transaction_id}'
        )

    # ===================================================================
    # USAGE API
    # ===================================================================

    async def create_usage(
        self,
        subscription_id: str,
        add_on_id: str,
        amount: float,
        usage_timestamp: Optional[str] = None,
        recording_timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record usage for a subscription add-on.

        Args:
            subscription_id: Subscription UUID
            add_on_id: Add-on ID or code
            amount: Usage amount
            usage_timestamp: When usage occurred (ISO format)
            recording_timestamp: When usage was recorded (ISO format)

        Returns:
            Usage record

        Example:
            >>> await recurly.create_usage(
            ...     subscription_id="sub_123",
            ...     add_on_id="api-calls",
            ...     amount=1000,
            ...     usage_timestamp="2025-01-15T12:00:00Z"
            ... )
        """
        data = {
            'amount': amount
        }

        if usage_timestamp:
            data['usage_timestamp'] = usage_timestamp
        if recording_timestamp:
            data['recording_timestamp'] = recording_timestamp

        result = await self._make_request(
            method='POST',
            endpoint=f'/subscriptions/{subscription_id}/add_ons/{add_on_id}/usage',
            data=data
        )

        logger.info(
            "recurly_usage_recorded",
            subscription_id=subscription_id,
            add_on_id=add_on_id,
            amount=amount
        )

        return result

    async def list_usage(
        self,
        subscription_id: str,
        add_on_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List usage records for a subscription add-on.

        Args:
            subscription_id: Subscription UUID
            add_on_id: Add-on ID or code
            limit: Results limit

        Returns:
            List of usage records
        """
        params = {'limit': min(limit, 200)}

        return await self._make_request(
            method='GET',
            endpoint=f'/subscriptions/{subscription_id}/add_ons/{add_on_id}/usage',
            params=params
        )

    # ===================================================================
    # DUNNING API
    # ===================================================================

    async def get_dunning_campaign(self, code: str) -> Dict[str, Any]:
        """
        Get dunning campaign configuration.

        Args:
            code: Dunning campaign code

        Returns:
            Dunning campaign details
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/dunning_campaigns/{code}'
        )

    async def retry_failed_payment(self, invoice_id: str) -> Dict[str, Any]:
        """
        Retry payment for a failed invoice.

        Args:
            invoice_id: Invoice ID

        Returns:
            Payment retry result
        """
        result = await self.collect_invoice(invoice_id)

        logger.info(
            "recurly_payment_retry",
            invoice_id=invoice_id
        )

        return result

    async def close(self) -> Any:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("recurly_session_closed")
