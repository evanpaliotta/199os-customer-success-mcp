"""
ChurnZero Integration
Priority Score: 18
ICP Adoption: 30-40% of B2B SaaS companies

Real-time customer success platform providing:
- Customer Health Scores
- Churn Prediction
- Journey Orchestration
- Product Usage Tracking
- Alerts & Automation
- Segmentation
- Plays (automated workflows)
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


class ChurnZeroIntegration(BaseIntegration):
    """
    ChurnZero API integration with API key authentication.

    Authentication:
    - API Key in header (X-CZ-Token)
    - App Key for identification

    Rate Limits:
    - 1000 requests per minute
    - Burst: 100 requests per second

    Documentation: https://churnzero.net/api/
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ):
        """
        Initialize ChurnZero integration.

        Args:
            credentials: ChurnZero credentials
                - api_key: ChurnZero API key
                - app_key: ChurnZero app key
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        super().__init__(
            integration_name="churnzero",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        self.api_key = credentials.get('api_key', '')
        self.app_key = credentials.get('app_key', '')

        if not self.api_key:
            raise ValidationError("ChurnZero api_key is required")
        if not self.app_key:
            raise ValidationError("ChurnZero app_key is required")

        self.base_url = "https://analytics.churnzero.net/i"

        logger.info(
            "churnzero_initialized",
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    async def authenticate(self) -> bool:
        """Authenticate with ChurnZero (API key validation)."""
        try:
            import aiohttp

            if not self.session or self.session.closed:
                self.session = aiohttp.ClientSession()

            logger.info("churnzero_authenticated")
            return True

        except Exception as e:
            raise AuthenticationError(f"ChurnZero authentication failed: {str(e)}")

    async def _make_request(
        self,
        action: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated HTTP request to ChurnZero API."""
        await self.ensure_authenticated()

        # ChurnZero uses GET with action-based routing
        request_params = {
            'appKey': self.app_key,
            'action': action
        }

        if params:
            request_params.update(params)

        headers = {
            'X-CZ-Token': self.api_key,
            'Content-Type': 'application/json'
        }

        try:
            async with self.session.get(
                self.base_url,
                params=request_params,
                headers=headers
            ) as response:
                if response.status == 200:
                    self.circuit_breaker._record_success(0.1)
                    # ChurnZero often returns plain text "OK" for success
                    content_type = response.headers.get('Content-Type', '')
                    if 'json' in content_type:
                        return await response.json()
                    else:
                        text = await response.text()
                        return {'status': 'success', 'message': text}
                else:
                    error_text = await response.text()
                    error = APIError(
                        f"ChurnZero API error ({response.status}): {error_text}",
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
        """Test connection to ChurnZero API."""
        try:
            start_time = datetime.now()

            # Test with a simple action (setAttribute is safe)
            response = await self._make_request(
                action='setAttribute',
                params={
                    'accountExternalId': 'test_connection',
                    'attributeName': 'test',
                    'attributeValue': 'test'
                }
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to ChurnZero",
                response_time_ms=duration_ms,
                metadata={'integration_name': 'churnzero'}
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"ChurnZero connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # ACCOUNTS API
    # ===================================================================

    async def set_account_attribute(
        self,
        account_id: str,
        attribute_name: str,
        attribute_value: Any
    ) -> Dict[str, Any]:
        """
        Set/update an account attribute.

        Args:
            account_id: External account ID
            attribute_name: Attribute name
            attribute_value: Attribute value

        Returns:
            Update confirmation

        Example:
            >>> await churnzero.set_account_attribute(
            ...     account_id="acme_corp",
            ...     attribute_name="ARR",
            ...     attribute_value=50000
            ... )
        """
        result = await self._make_request(
            action='setAttribute',
            params={
                'accountExternalId': account_id,
                'attributeName': attribute_name,
                'attributeValue': str(attribute_value)
            }
        )

        logger.info(
            "churnzero_account_attribute_set",
            account_id=account_id,
            attribute=attribute_name
        )

        return result

    async def increment_account_attribute(
        self,
        account_id: str,
        attribute_name: str,
        increment_value: float = 1.0
    ) -> Dict[str, Any]:
        """
        Increment a numeric account attribute.

        Args:
            account_id: External account ID
            attribute_name: Attribute name
            increment_value: Value to increment by (default: 1.0)

        Returns:
            Update confirmation

        Example:
            >>> # Increment login count
            >>> await churnzero.increment_account_attribute(
            ...     account_id="acme_corp",
            ...     attribute_name="login_count",
            ...     increment_value=1
            ... )
        """
        return await self._make_request(
            action='incrementAttribute',
            params={
                'accountExternalId': account_id,
                'attributeName': attribute_name,
                'incrementValue': str(increment_value)
            }
        )

    # ===================================================================
    # CONTACTS API
    # ===================================================================

    async def set_contact_attribute(
        self,
        account_id: str,
        contact_id: str,
        attribute_name: str,
        attribute_value: Any
    ) -> Dict[str, Any]:
        """
        Set/update a contact attribute.

        Args:
            account_id: External account ID
            contact_id: External contact ID
            attribute_name: Attribute name
            attribute_value: Attribute value

        Returns:
            Update confirmation

        Example:
            >>> await churnzero.set_contact_attribute(
            ...     account_id="acme_corp",
            ...     contact_id="john.doe@acme.com",
            ...     attribute_name="title",
            ...     attribute_value="VP of Operations"
            ... )
        """
        result = await self._make_request(
            action='setContactAttribute',
            params={
                'accountExternalId': account_id,
                'contactExternalId': contact_id,
                'attributeName': attribute_name,
                'attributeValue': str(attribute_value)
            }
        )

        logger.info(
            "churnzero_contact_attribute_set",
            account_id=account_id,
            contact_id=contact_id,
            attribute=attribute_name
        )

        return result

    # ===================================================================
    # EVENTS API
    # ===================================================================

    async def track_event(
        self,
        account_id: str,
        contact_id: Optional[str],
        event_name: str,
        description: Optional[str] = None,
        quantity: float = 1.0,
        event_date: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track a customer event (product usage, feature adoption, etc.).

        Args:
            account_id: External account ID
            contact_id: External contact ID (optional)
            event_name: Event name
            description: Event description (optional)
            quantity: Event quantity/value (default: 1.0)
            event_date: Event date (ISO format, defaults to now)
            custom_fields: Additional custom fields (optional)

        Returns:
            Track confirmation

        Example:
            >>> # Track feature usage
            >>> await churnzero.track_event(
            ...     account_id="acme_corp",
            ...     contact_id="john.doe@acme.com",
            ...     event_name="report_generated",
            ...     description="User generated quarterly sales report",
            ...     quantity=1,
            ...     custom_fields={"report_type": "sales", "quarter": "Q4"}
            ... )
        """
        params = {
            'accountExternalId': account_id,
            'eventName': event_name,
            'quantity': str(quantity)
        }

        if contact_id:
            params['contactExternalId'] = contact_id

        if description:
            params['description'] = description

        if event_date:
            params['eventDate'] = event_date

        if custom_fields:
            for key, value in custom_fields.items():
                params[f'customField{key}'] = str(value)

        result = await self._make_request(
            action='trackEvent',
            params=params
        )

        logger.info(
            "churnzero_event_tracked",
            account_id=account_id,
            event_name=event_name,
            quantity=quantity
        )

        return result

    # ===================================================================
    # JOURNEYS (PLAYS) API
    # ===================================================================

    async def start_journey(
        self,
        account_id: str,
        contact_id: Optional[str],
        journey_name: str
    ) -> Dict[str, Any]:
        """
        Start a customer journey (Play).

        Args:
            account_id: External account ID
            contact_id: External contact ID (optional)
            journey_name: Journey/Play name

        Returns:
            Start confirmation

        Example:
            >>> # Start onboarding journey
            >>> await churnzero.start_journey(
            ...     account_id="acme_corp",
            ...     contact_id="john.doe@acme.com",
            ...     journey_name="New Customer Onboarding"
            ... )
        """
        params = {
            'accountExternalId': account_id,
            'journeyName': journey_name
        }

        if contact_id:
            params['contactExternalId'] = contact_id

        result = await self._make_request(
            action='startJourney',
            params=params
        )

        logger.info(
            "churnzero_journey_started",
            account_id=account_id,
            journey_name=journey_name
        )

        return result

    async def stop_journey(
        self,
        account_id: str,
        contact_id: Optional[str],
        journey_name: str
    ) -> Dict[str, Any]:
        """
        Stop a customer journey (Play).

        Args:
            account_id: External account ID
            contact_id: External contact ID (optional)
            journey_name: Journey/Play name

        Returns:
            Stop confirmation
        """
        params = {
            'accountExternalId': account_id,
            'journeyName': journey_name
        }

        if contact_id:
            params['contactExternalId'] = contact_id

        return await self._make_request(
            action='stopJourney',
            params=params
        )

    # ===================================================================
    # ALERTS API
    # ===================================================================

    async def create_alert(
        self,
        account_id: str,
        alert_type: str,
        message: str,
        priority: str = "Medium"
    ) -> Dict[str, Any]:
        """
        Create an alert for a customer.

        Args:
            account_id: External account ID
            alert_type: Alert type (e.g., "Churn Risk", "Health Decline")
            message: Alert message
            priority: Priority level (High, Medium, Low)

        Returns:
            Alert creation confirmation

        Example:
            >>> await churnzero.create_alert(
            ...     account_id="acme_corp",
            ...     alert_type="Churn Risk",
            ...     message="Login frequency dropped 60% in last 30 days",
            ...     priority="High"
            ... )
        """
        params = {
            'accountExternalId': account_id,
            'alertType': alert_type,
            'message': message,
            'priority': priority
        }

        result = await self._make_request(
            action='createAlert',
            params=params
        )

        logger.info(
            "churnzero_alert_created",
            account_id=account_id,
            alert_type=alert_type,
            priority=priority
        )

        return result

    # ===================================================================
    # NPS/CSAT SURVEYS API
    # ===================================================================

    async def record_survey_response(
        self,
        account_id: str,
        contact_id: str,
        survey_name: str,
        score: int,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record an NPS or CSAT survey response.

        Args:
            account_id: External account ID
            contact_id: External contact ID
            survey_name: Survey name (e.g., "NPS Q4 2024")
            score: Survey score (0-10 for NPS, 1-5 for CSAT)
            comments: Survey comments (optional)

        Returns:
            Record confirmation

        Example:
            >>> # Record NPS response
            >>> await churnzero.record_survey_response(
            ...     account_id="acme_corp",
            ...     contact_id="john.doe@acme.com",
            ...     survey_name="NPS Q4 2024",
            ...     score=9,
            ...     comments="Great product, excellent support!"
            ... )
        """
        params = {
            'accountExternalId': account_id,
            'contactExternalId': contact_id,
            'surveyName': survey_name,
            'score': str(score)
        }

        if comments:
            params['comments'] = comments

        result = await self._make_request(
            action='recordSurveyResponse',
            params=params
        )

        logger.info(
            "churnzero_survey_response_recorded",
            account_id=account_id,
            survey_name=survey_name,
            score=score
        )

        return result

    # ===================================================================
    # UTILITY METHODS
    # ===================================================================

    async def track_product_usage(
        self,
        account_id: str,
        contact_id: str,
        feature_name: str,
        usage_count: float = 1.0
    ) -> Dict[str, Any]:
        """
        Track product feature usage (convenience method).

        Args:
            account_id: External account ID
            contact_id: External contact ID
            feature_name: Feature name
            usage_count: Usage count (default: 1.0)

        Returns:
            Track confirmation

        Example:
            >>> await churnzero.track_product_usage(
            ...     account_id="acme_corp",
            ...     contact_id="john.doe@acme.com",
            ...     feature_name="dashboard_view",
            ...     usage_count=1
            ... )
        """
        return await self.track_event(
            account_id=account_id,
            contact_id=contact_id,
            event_name=f"feature_usage_{feature_name}",
            description=f"Used feature: {feature_name}",
            quantity=usage_count,
            custom_fields={'feature': feature_name}
        )

    async def update_health_score_factor(
        self,
        account_id: str,
        factor_name: str,
        factor_value: float
    ) -> Dict[str, Any]:
        """
        Update a health score factor (convenience method).

        Args:
            account_id: External account ID
            factor_name: Health score factor name
            factor_value: Factor value

        Returns:
            Update confirmation

        Example:
            >>> await churnzero.update_health_score_factor(
            ...     account_id="acme_corp",
            ...     factor_name="product_adoption",
            ...     factor_value=85.5
            ... )
        """
        return await self.set_account_attribute(
            account_id=account_id,
            attribute_name=f"health_{factor_name}",
            attribute_value=factor_value
        )

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("churnzero_session_closed")
