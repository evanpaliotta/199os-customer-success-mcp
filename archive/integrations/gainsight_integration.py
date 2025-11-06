"""
Gainsight Integration
Priority Score: 20 (HIGHEST for Customer Success)
ICP Adoption: 60% of enterprise B2B SaaS companies

Industry-leading customer success platform providing:
- Customer Health Scores
- CTAs (Calls to Action)
- Playbooks and Automation
- Success Plans
- Timeline Events
- NPS/CSAT Surveys
- Relationship Management
- Renewals and Upsells
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

from .auth.oauth2_base import OAuth2Integration
from .base import ConnectionTestResult, IntegrationStatus, ValidationError, APIError

logger = structlog.get_logger(__name__)


class GainsightIntegration(OAuth2Integration):
    """
    Gainsight OAuth2 integration for customer success operations.

    Authentication:
    - OAuth2 with client credentials flow
    - Requires: client_id, client_secret, subdomain
    - Access token format: Bearer token

    Rate Limits:
    - 5000 requests per hour per organization
    - 100 requests per minute per user
    - Burst limit: 20 requests per second

    Documentation: https://support.gainsight.com/Gainsight_NXT/API_and_Developer_Docs
    """

    def __init__(
        self,
        credentials: Dict[str, str],
        rate_limit_calls: int = 100,
        rate_limit_window: int = 60
    ):
        """
        Initialize Gainsight integration.

        Args:
            credentials: OAuth2 credentials
                - client_id: Gainsight OAuth client ID
                - client_secret: Gainsight OAuth client secret
                - subdomain: Gainsight subdomain (e.g., "company")
                - access_token: Current access token (optional)
                - refresh_token: Refresh token (optional)
            rate_limit_calls: Max API calls per window (default: 100)
            rate_limit_window: Rate limit window in seconds (default: 60)
        """
        self.subdomain = credentials.get('subdomain', '')
        if not self.subdomain:
            raise ValidationError("Gainsight subdomain is required")

        super().__init__(
            integration_name="gainsight",
            credentials=credentials,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window,
            max_retries=3
        )

        logger.info(
            "gainsight_initialized",
            subdomain=self.subdomain,
            rate_limit=f"{rate_limit_calls}/{rate_limit_window}s"
        )

    def get_oauth_config(self) -> Dict[str, Any]:
        """Get Gainsight OAuth2 configuration."""
        return {
            'auth_url': f'https://{self.subdomain}.gainsight.com/v1/oauth/authorize',
            'token_url': f'https://{self.subdomain}.gainsight.com/v1/oauth/token',
            'api_base_url': f'https://{self.subdomain}.gainsight.com/v1',
            'scopes': ['api']  # Gainsight uses single scope
        }

    async def test_connection(self) -> ConnectionTestResult:
        """Test connection to Gainsight API."""
        try:
            start_time = datetime.now()

            # Test with a simple user info request
            response = await self._make_request(
                method='GET',
                endpoint='/users/me'
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionTestResult(
                success=True,
                status=IntegrationStatus.CONNECTED,
                message="Successfully connected to Gainsight",
                response_time_ms=duration_ms,
                metadata={
                    'user_id': response.get('id'),
                    'email': response.get('email'),
                    'subdomain': self.subdomain,
                    'integration_name': 'gainsight'
                }
            )

        except Exception as e:
            return ConnectionTestResult(
                success=False,
                status=IntegrationStatus.ERROR,
                message=f"Gainsight connection test failed: {str(e)}",
                metadata={'error': str(e)}
            )

    # ===================================================================
    # COMPANIES (CUSTOMERS) API
    # ===================================================================

    async def get_company(self, company_id: str) -> Dict[str, Any]:
        """
        Get company (customer account) details.

        Args:
            company_id: Gainsight company ID (GSID)

        Returns:
            Company data including health score, ARR, lifecycle stage

        Example:
            >>> company = await gainsight.get_company("C001")
            >>> print(company['Name'], company['Health_Score__c'])
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/data/objects/Company/{company_id}'
        )

    async def list_companies(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List companies with optional filters.

        Args:
            filters: Filter criteria (e.g., {"Health_Score__c": {"$gte": 70}})
            limit: Max results (default: 100, max: 500)
            offset: Pagination offset

        Returns:
            List of companies

        Example:
            >>> # Get healthy accounts
            >>> companies = await gainsight.list_companies(
            ...     filters={"Health_Score__c": {"$gte": 80}}
            ... )
        """
        params = {
            'limit': limit,
            'offset': offset
        }
        if filters:
            params['filter'] = filters

        return await self._make_request(
            method='GET',
            endpoint='/data/objects/Company',
            params=params
        )

    async def update_company(
        self,
        company_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update company fields.

        Args:
            company_id: Gainsight company ID
            data: Fields to update

        Returns:
            Updated company data

        Example:
            >>> await gainsight.update_company(
            ...     company_id="C001",
            ...     data={"ARR__c": 50000, "Stage__c": "Expansion"}
            ... )
        """
        return await self._make_request(
            method='PUT',
            endpoint=f'/data/objects/Company/{company_id}',
            data=data
        )

    # ===================================================================
    # HEALTH SCORES API
    # ===================================================================

    async def get_health_score(self, company_id: str) -> Dict[str, Any]:
        """
        Get company health score with component breakdown.

        Args:
            company_id: Gainsight company ID

        Returns:
            Health score data with measures and trends

        Example:
            >>> health = await gainsight.get_health_score("C001")
            >>> print(f"Overall: {health['overall_score']}")
            >>> print(f"Product Usage: {health['measures']['product_usage']}")
        """
        return await self._make_request(
            method='GET',
            endpoint=f'/health/companies/{company_id}/score'
        )

    async def get_health_score_history(
        self,
        company_id: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get health score history over time.

        Args:
            company_id: Gainsight company ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Time series health score data

        Example:
            >>> history = await gainsight.get_health_score_history(
            ...     company_id="C001",
            ...     start_date="2024-01-01",
            ...     end_date="2024-12-31"
            ... )
        """
        params = {
            'start_date': start_date,
            'end_date': end_date
        }

        return await self._make_request(
            method='GET',
            endpoint=f'/health/companies/{company_id}/history',
            params=params
        )

    # ===================================================================
    # CTAs (CALLS TO ACTION) API
    # ===================================================================

    async def create_cta(
        self,
        name: str,
        company_id: str,
        owner_id: str,
        type: str,
        priority: str = "Medium",
        reason: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Call to Action (CTA).

        Args:
            name: CTA name/title
            company_id: Gainsight company ID
            owner_id: CSM user ID
            type: CTA type (e.g., "Risk", "Renewal", "Upsell", "Onboarding")
            priority: Priority level (High, Medium, Low)
            reason: Reason for CTA
            due_date: Due date (ISO format)

        Returns:
            Created CTA data

        Example:
            >>> cta = await gainsight.create_cta(
            ...     name="Low Product Adoption Risk",
            ...     company_id="C001",
            ...     owner_id="U123",
            ...     type="Risk",
            ...     priority="High",
            ...     reason="Login frequency dropped 50% in last 30 days",
            ...     due_date="2024-12-31T23:59:59Z"
            ... )
        """
        data = {
            'Name': name,
            'Company': company_id,
            'Owner': owner_id,
            'Type': type,
            'Priority': priority
        }

        if reason:
            data['Reason'] = reason
        if due_date:
            data['Due_Date__c'] = due_date

        result = await self._make_request(
            method='POST',
            endpoint='/data/objects/CTA',
            data=data
        )

        logger.info(
            "gainsight_cta_created",
            cta_id=result.get('Id'),
            company_id=company_id,
            type=type
        )

        return result

    async def list_ctas(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List CTAs with optional filters.

        Args:
            filters: Filter criteria (e.g., {"Status": "Open", "Priority": "High"})
            limit: Max results

        Returns:
            List of CTAs

        Example:
            >>> # Get open high-priority CTAs
            >>> ctas = await gainsight.list_ctas(
            ...     filters={"Status": "Open", "Priority": "High"}
            ... )
        """
        params = {'limit': limit}
        if filters:
            params['filter'] = filters

        return await self._make_request(
            method='GET',
            endpoint='/data/objects/CTA',
            params=params
        )

    async def update_cta(
        self,
        cta_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update CTA fields.

        Args:
            cta_id: CTA ID
            data: Fields to update

        Returns:
            Updated CTA data

        Example:
            >>> await gainsight.update_cta(
            ...     cta_id="CTA123",
            ...     data={"Status": "Closed", "Outcome": "Resolved"}
            ... )
        """
        return await self._make_request(
            method='PUT',
            endpoint=f'/data/objects/CTA/{cta_id}',
            data=data
        )

    async def close_cta(
        self,
        cta_id: str,
        outcome: str,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Close a CTA with outcome.

        Args:
            cta_id: CTA ID
            outcome: Outcome (e.g., "Resolved", "Escalated", "Not Actionable")
            comments: Closing comments

        Returns:
            Closed CTA data
        """
        data = {
            'Status': 'Closed',
            'Outcome': outcome
        }
        if comments:
            data['Comments'] = comments

        return await self.update_cta(cta_id, data)

    # ===================================================================
    # TIMELINE API
    # ===================================================================

    async def create_timeline_activity(
        self,
        company_id: str,
        activity_type: str,
        subject: str,
        details: Optional[str] = None,
        activity_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create timeline activity/event.

        Args:
            company_id: Gainsight company ID
            activity_type: Activity type (e.g., "Meeting", "Email", "Call")
            subject: Activity subject/title
            details: Activity details/notes
            activity_date: Activity date (ISO format, defaults to now)

        Returns:
            Created timeline activity

        Example:
            >>> activity = await gainsight.create_timeline_activity(
            ...     company_id="C001",
            ...     activity_type="Meeting",
            ...     subject="Quarterly Business Review",
            ...     details="Reviewed Q4 performance and 2025 goals",
            ...     activity_date="2024-12-15T14:00:00Z"
            ... )
        """
        data = {
            'Company': company_id,
            'Activity_Type__c': activity_type,
            'Subject': subject,
            'Activity_Date__c': activity_date or datetime.utcnow().isoformat()
        }

        if details:
            data['Details__c'] = details

        result = await self._make_request(
            method='POST',
            endpoint='/data/objects/Timeline',
            data=data
        )

        logger.info(
            "gainsight_timeline_activity_created",
            activity_id=result.get('Id'),
            company_id=company_id,
            type=activity_type
        )

        return result

    async def get_timeline(
        self,
        company_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get company timeline activities.

        Args:
            company_id: Gainsight company ID
            limit: Max activities to return

        Returns:
            List of timeline activities
        """
        params = {
            'filter': {'Company': company_id},
            'limit': limit,
            'sort': [{'Activity_Date__c': 'desc'}]
        }

        return await self._make_request(
            method='GET',
            endpoint='/data/objects/Timeline',
            params=params
        )

    # ===================================================================
    # SUCCESS PLANS API
    # ===================================================================

    async def create_success_plan(
        self,
        name: str,
        company_id: str,
        owner_id: str,
        template_id: Optional[str] = None,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create success plan.

        Args:
            name: Success plan name
            company_id: Gainsight company ID
            owner_id: CSM user ID
            template_id: Success plan template ID (optional)
            start_date: Start date (ISO format)
            due_date: Due date (ISO format)

        Returns:
            Created success plan

        Example:
            >>> plan = await gainsight.create_success_plan(
            ...     name="Enterprise Onboarding - Acme Corp",
            ...     company_id="C001",
            ...     owner_id="U123",
            ...     template_id="TPL_ONBOARDING",
            ...     due_date="2025-03-31T23:59:59Z"
            ... )
        """
        data = {
            'Name': name,
            'Company': company_id,
            'Owner': owner_id
        }

        if template_id:
            data['Template__c'] = template_id
        if start_date:
            data['Start_Date__c'] = start_date
        if due_date:
            data['Due_Date__c'] = due_date

        result = await self._make_request(
            method='POST',
            endpoint='/data/objects/SuccessPlan',
            data=data
        )

        logger.info(
            "gainsight_success_plan_created",
            plan_id=result.get('Id'),
            company_id=company_id
        )

        return result

    async def list_success_plans(
        self,
        company_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List success plans.

        Args:
            company_id: Filter by company ID (optional)
            status: Filter by status (e.g., "Active", "Completed")

        Returns:
            List of success plans
        """
        filters = {}
        if company_id:
            filters['Company'] = company_id
        if status:
            filters['Status'] = status

        params = {}
        if filters:
            params['filter'] = filters

        return await self._make_request(
            method='GET',
            endpoint='/data/objects/SuccessPlan',
            params=params
        )

    # ===================================================================
    # SURVEYS API (NPS, CSAT)
    # ===================================================================

    async def get_nps_scores(
        self,
        company_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get NPS (Net Promoter Score) survey results.

        Args:
            company_id: Filter by company (optional)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            NPS survey results

        Example:
            >>> nps = await gainsight.get_nps_scores(
            ...     company_id="C001",
            ...     start_date="2024-01-01",
            ...     end_date="2024-12-31"
            ... )
            >>> print(f"Average NPS: {nps['average_score']}")
        """
        params = {}
        if company_id:
            params['company_id'] = company_id
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint='/surveys/nps',
            params=params
        )

    async def get_csat_scores(
        self,
        company_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get CSAT (Customer Satisfaction) survey results.

        Args:
            company_id: Filter by company (optional)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            CSAT survey results
        """
        params = {}
        if company_id:
            params['company_id'] = company_id
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return await self._make_request(
            method='GET',
            endpoint='/surveys/csat',
            params=params
        )

    # ===================================================================
    # RELATIONSHIPS (CONTACTS) API
    # ===================================================================

    async def create_relationship(
        self,
        company_id: str,
        first_name: str,
        last_name: str,
        email: str,
        title: Optional[str] = None,
        role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create relationship (contact) at a company.

        Args:
            company_id: Gainsight company ID
            first_name: Contact first name
            last_name: Contact last name
            email: Contact email
            title: Job title
            role: Role (e.g., "Champion", "Decision Maker", "Influencer")

        Returns:
            Created relationship data

        Example:
            >>> contact = await gainsight.create_relationship(
            ...     company_id="C001",
            ...     first_name="Jane",
            ...     last_name="Doe",
            ...     email="jane.doe@acme.com",
            ...     title="VP of Operations",
            ...     role="Champion"
            ... )
        """
        data = {
            'Company': company_id,
            'First_Name__c': first_name,
            'Last_Name__c': last_name,
            'Email__c': email
        }

        if title:
            data['Title__c'] = title
        if role:
            data['Role__c'] = role

        result = await self._make_request(
            method='POST',
            endpoint='/data/objects/Relationship',
            data=data
        )

        logger.info(
            "gainsight_relationship_created",
            relationship_id=result.get('Id'),
            company_id=company_id,
            email=email
        )

        return result

    async def list_relationships(
        self,
        company_id: str
    ) -> Dict[str, Any]:
        """
        List relationships (contacts) for a company.

        Args:
            company_id: Gainsight company ID

        Returns:
            List of relationships
        """
        params = {
            'filter': {'Company': company_id}
        }

        return await self._make_request(
            method='GET',
            endpoint='/data/objects/Relationship',
            params=params
        )

    # ===================================================================
    # RENEWALS API
    # ===================================================================

    async def get_renewals(
        self,
        company_id: Optional[str] = None,
        status: Optional[str] = None,
        upcoming_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get renewal opportunities.

        Args:
            company_id: Filter by company (optional)
            status: Filter by status (e.g., "Open", "Closed Won", "Closed Lost")
            upcoming_days: Get renewals due in next N days

        Returns:
            List of renewals

        Example:
            >>> # Get renewals due in next 90 days
            >>> renewals = await gainsight.get_renewals(upcoming_days=90)
        """
        filters = {}
        if company_id:
            filters['Company'] = company_id
        if status:
            filters['Status'] = status

        params = {}
        if filters:
            params['filter'] = filters
        if upcoming_days:
            params['upcoming_days'] = upcoming_days

        return await self._make_request(
            method='GET',
            endpoint='/data/objects/Renewal',
            params=params
        )

    # ===================================================================
    # PLAYBOOKS API
    # ===================================================================

    async def trigger_playbook(
        self,
        playbook_id: str,
        company_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger/execute a playbook for a company.

        Args:
            playbook_id: Gainsight playbook ID
            company_id: Gainsight company ID
            context: Additional context variables for playbook

        Returns:
            Playbook execution result

        Example:
            >>> await gainsight.trigger_playbook(
            ...     playbook_id="PB_CHURN_RISK",
            ...     company_id="C001",
            ...     context={"risk_reason": "Low product usage"}
            ... )
        """
        data = {
            'PlaybookId': playbook_id,
            'CompanyId': company_id,
            'Context': context or {}
        }

        result = await self._make_request(
            method='POST',
            endpoint='/playbooks/execute',
            data=data
        )

        logger.info(
            "gainsight_playbook_triggered",
            playbook_id=playbook_id,
            company_id=company_id
        )

        return result
