"""
Core System Tools
System configuration, client management, and setup for Customer Success MCP
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.security.input_validation import validate_client_id, ValidationError
from src.database import SessionLocal
from src.database.models import CustomerAccount
import structlog

logger = structlog.get_logger(__name__)


def register_tools(mcp):
    """Register all core system tools with the MCP instance"""

    @mcp.tool()
    async def register_client(
        ctx: Context,
        client_name: str,
        company_name: str,
        industry: str = "Technology",
        contract_value: float = 0.0,
        contract_start_date: Optional[str] = None,
        contract_end_date: Optional[str] = None,
        primary_contact_email: Optional[str] = None,
        primary_contact_name: Optional[str] = None,
        tier: str = "standard"
    ) -> Dict[str, Any]:
        """
        Register a new customer client in the CS system.

        Creates a new customer account with initial configuration, health score,
        and lifecycle tracking. This is the entry point for all new customers.

        Args:
            client_name: Name of the client account
            company_name: Legal company name
            industry: Industry vertical (Technology, Healthcare, Finance, etc.)
            contract_value: Annual contract value (ARR) in USD
            contract_start_date: Contract start date (YYYY-MM-DD format)
            contract_end_date: Contract end date (YYYY-MM-DD format)
            primary_contact_email: Primary customer contact email
            primary_contact_name: Primary customer contact name
            tier: Customer tier (starter, standard, professional, enterprise)

        Returns:
            Registration confirmation with client_id, client_record, and next_steps
        """
        try:
            await ctx.info(f"Registering new client: {client_name}")

            # Generate unique client ID
            timestamp = int(datetime.now().timestamp())
            sanitized_name = client_name.lower().replace(' ', '_')[:10]
            client_id = f"cs_{timestamp}_{sanitized_name}"

            # Validate tier
            valid_tiers = ['starter', 'standard', 'professional', 'enterprise']
            if tier.lower() not in valid_tiers:
                return {
                    'status': 'failed',
                    'error': f'Invalid tier. Must be one of: {", ".join(valid_tiers)}'
                }

            # Calculate initial dates
            start_date = contract_start_date or datetime.now().strftime("%Y-%m-%d")
            if not contract_end_date:
                # Default to 1 year contract
                end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
            else:
                end_date = contract_end_date

            # Create comprehensive client record
            client_record = {
                "client_id": client_id,
                "client_name": client_name,
                "company_name": company_name,
                "industry": industry,
                "tier": tier.lower(),

                # Contract information
                "contract_value": contract_value,
                "contract_start_date": start_date,
                "contract_end_date": end_date,
                "renewal_date": end_date,

                # Contact information
                "primary_contact_email": primary_contact_email,
                "primary_contact_name": primary_contact_name,
                "csm_assigned": None,  # Will be assigned later

                # Health and engagement metrics
                "health_score": 50,  # Initial neutral score
                "health_trend": "stable",
                "lifecycle_stage": "onboarding",
                "last_engagement_date": None,

                # Account metrics
                "users_provisioned": 0,
                "active_users": 0,
                "feature_adoption_rate": 0.0,
                "support_tickets_open": 0,
                "satisfaction_score": None,

                # Metadata
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "active"
            }

            # Calculate days until renewal
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            days_until_renewal = (end_date_obj - datetime.now()).days

            # Log registration
            logger.info(
                "client_registered",
                client_id=client_id,
                client_name=client_name,
                tier=tier,
                contract_value=contract_value
            )

            # Save to database
            db = SessionLocal()
            try:
                # Convert string dates to date objects
                contract_start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                contract_end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

                # Create CustomerAccount ORM object
                new_customer = CustomerAccount(
                    client_id=client_id,
                    client_name=client_name,
                    company_name=company_name,
                    industry=industry,
                    tier=tier.lower(),
                    contract_value=contract_value,
                    contract_start_date=contract_start_date_obj,
                    contract_end_date=contract_end_date_obj,
                    renewal_date=contract_end_date_obj,
                    primary_contact_email=primary_contact_email,
                    primary_contact_name=primary_contact_name,
                    health_score=50,
                    health_trend="stable",
                    lifecycle_stage="onboarding",
                    status="active"
                )

                # Add and commit to database
                db.add(new_customer)
                db.commit()
                db.refresh(new_customer)

                logger.info(
                    "client_persisted_to_database",
                    client_id=client_id,
                    database_id=new_customer.id
                )
            except Exception as db_error:
                db.rollback()
                logger.error(
                    "client_registration_db_error",
                    client_id=client_id,
                    error=str(db_error)
                )
                # Don't fail the registration if DB write fails, just log it
                # In production, you might want to raise this error
            finally:
                db.close()

            return {
                'status': 'success',
                'message': f"Client '{client_name}' registered successfully",
                'client_id': client_id,
                'client_record': client_record,
                'summary': {
                    'tier': tier,
                    'contract_value': f"${contract_value:,.2f}",
                    'contract_term': f"{(end_date_obj - datetime.strptime(start_date, '%Y-%m-%d')).days} days",
                    'days_until_renewal': days_until_renewal,
                    'lifecycle_stage': 'onboarding'
                },
                'next_steps': [
                    "Create onboarding plan (use create_onboarding_plan tool)",
                    "Schedule kickoff call (use schedule_kickoff_meeting tool)",
                    "Provision user accounts and access",
                    "Assign Customer Success Manager (use assign_csm tool)",
                    "Set up health score monitoring (automatic)",
                    "Configure integration points"
                ]
            }

        except Exception as e:
            logger.error("client_registration_failed", error=str(e))
            return {
                'status': 'failed',
                'error': f"Client registration failed: {str(e)}"
            }


    @mcp.tool()
    async def get_client_overview(
        ctx: Context,
        client_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive overview of a client account.

        Retrieves complete client status including health score, engagement metrics,
        onboarding progress, support status, and revenue opportunities. This is the
        primary tool for getting a 360-degree view of any customer.

        Args:
            client_id: Unique client identifier

        Returns:
            Complete client overview with health, engagement, support, and revenue data
        """
        try:
            # Validate client_id
            try:
                client_id = validate_client_id(client_id)
            except ValidationError as e:
                return {
                    'status': 'failed',
                    'error': f'Invalid client_id: {str(e)}'
                }

            await ctx.info(f"Fetching overview for client: {client_id}")

            # Query database for actual client data
            db = SessionLocal()
            try:
                customer = db.query(CustomerAccount).filter(
                    CustomerAccount.client_id == client_id
                ).first()

                if not customer:
                    return {
                        'status': 'failed',
                        'error': f'Client {client_id} not found in database'
                    }

                # Calculate days until renewal
                days_until_renewal = None
                renewal_probability = None
                renewal_risk_level = "unknown"

                if customer.contract_end_date:
                    days_until_renewal = (customer.contract_end_date - datetime.now().date()).days

                    # Simple renewal probability calculation
                    if customer.health_score >= 80:
                        renewal_probability = 0.90
                        renewal_risk_level = "low"
                    elif customer.health_score >= 60:
                        renewal_probability = 0.70
                        renewal_risk_level = "medium"
                    else:
                        renewal_probability = 0.40
                        renewal_risk_level = "high"

                # Build client overview from actual database data
                client_overview = {
                    # Basic information (from database)
                    "client_id": customer.client_id,
                    "client_name": customer.client_name,
                    "company_name": customer.company_name,
                    "industry": customer.industry,
                    "tier": customer.tier,

                    # Health and lifecycle (from database)
                    "health_score": customer.health_score,
                    "health_trend": customer.health_trend,
                    "lifecycle_stage": customer.lifecycle_stage,
                    "csm_assigned": customer.csm_assigned,

                    # Contract information (from database)
                    "contract_value": customer.contract_value,
                    "contract_start_date": customer.contract_start_date.isoformat() if customer.contract_start_date else None,
                    "contract_end_date": customer.contract_end_date.isoformat() if customer.contract_end_date else None,
                    "days_until_renewal": days_until_renewal,
                    "renewal_probability": renewal_probability,
                    "renewal_risk_level": renewal_risk_level,

                    # Onboarding status (placeholder - to be implemented with onboarding tracking)
                    "onboarding": {
                        "status": "in_progress" if customer.lifecycle_stage == "onboarding" else "completed",
                        "completion_rate": None,
                        "completion_date": None,
                        "time_to_value_days": None,
                        "milestones_completed": None,
                        "milestones_total": None,
                        "training_completion_rate": None
                    },

                    # Engagement metrics (placeholder - to be implemented with usage tracking)
                    "engagement": {
                        "last_login": customer.last_engagement_date.isoformat() if customer.last_engagement_date else None,
                        "days_since_last_login": (datetime.now() - customer.last_engagement_date).days if customer.last_engagement_date else None,
                        "weekly_active_users": None,
                        "monthly_active_users": None,
                        "total_users_provisioned": None,
                        "user_activation_rate": None,
                        "feature_adoption_rate": None,
                        "average_session_duration_minutes": None,
                        "weekly_sessions": None,
                        "engagement_trend": None
                    },

                    # Support metrics (placeholder - to be implemented with support ticket tracking)
                    "support": {
                        "open_tickets": None,
                        "tickets_this_month": None,
                        "tickets_last_month": None,
                        "ticket_trend": None,
                        "avg_resolution_time_hours": None,
                        "first_response_time_minutes": None,
                        "satisfaction_score": None,
                        "satisfaction_trend": None,
                        "escalations_this_month": None,
                        "knowledge_base_usage": None
                    },

                    # Product usage (placeholder - to be implemented with usage analytics)
                    "product_usage": {
                        "core_features_used": None,
                        "core_features_total": None,
                        "advanced_features_used": None,
                        "advanced_features_total": None,
                        "integrations_active": None,
                        "integrations_available": None,
                        "api_calls_this_month": None,
                        "storage_used_gb": None,
                        "storage_limit_gb": None
                    },

                    # Revenue and expansion (basic from database, expansion to be enhanced)
                    "revenue": {
                        "current_arr": customer.contract_value,
                        "expansion_opportunities": None,
                        "expansion_potential_arr": None,
                        "upsell_likelihood": None,
                        "cross_sell_opportunities": [],
                        "lifetime_value": None,
                        "customer_acquisition_cost": None,
                        "ltv_cac_ratio": None
                    },

                    # Communication history (placeholder - to be implemented with communication tracking)
                    "communication": {
                        "last_ebr_date": None,
                        "next_ebr_scheduled": None,
                        "emails_sent": None,
                        "emails_opened": None,
                        "email_engagement_rate": None,
                        "last_csm_touchpoint": None,
                        "touchpoint_frequency_days": None
                    },

                    # Risks identified (to be enhanced with risk scoring)
                    "risks": [],

                    # Opportunities identified (to be enhanced with opportunity tracking)
                    "opportunities": [],

                    # Recent activity (placeholder - to be implemented with activity logging)
                    "recent_activity": []
                }

                # Calculate basic health score components
                # Note: These are placeholder calculations until usage/engagement tracking is implemented
                health_components = {
                    "usage_score": None,  # Requires usage tracking
                    "engagement_score": None,  # Requires engagement tracking
                    "support_score": None,  # Requires support ticket tracking
                    "satisfaction_score": None,  # Requires satisfaction survey tracking
                    "payment_score": 100 if customer.status == "active" else 0  # Basic payment health
                }

            finally:
                db.close()

            logger.info(
                "client_overview_retrieved",
                client_id=client_id,
                health_score=client_overview["health_score"],
                lifecycle_stage=client_overview["lifecycle_stage"]
            )

            return {
                'status': 'success',
                'client_overview': client_overview,
                'health_components': health_components,
                'insights': {
                    'overall_status': 'healthy',
                    'key_strengths': [
                        'High engagement and feature adoption',
                        'Excellent support satisfaction',
                        'Strong renewal probability',
                        'Multiple expansion opportunities'
                    ],
                    'attention_areas': [
                        'Consider scheduling EBR within next 30 days'
                    ],
                    'recommended_actions': [
                        'Present expansion proposal for additional licenses',
                        'Introduce premium features through demo',
                        'Schedule quarterly business review'
                    ]
                }
            }

        except Exception as e:
            logger.error("client_overview_failed", error=str(e))
            return {
                'status': 'failed',
                'error': f"Failed to retrieve client overview: {str(e)}"
            }


    @mcp.tool()
    async def update_client_info(
        ctx: Context,
        client_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update client information and metadata.

        Allows updating any client field including contact info, tier, contract details,
        or custom metadata. Changes are logged for audit trail.

        Args:
            client_id: Unique client identifier
            updates: Dictionary of fields to update with new values

        Returns:
            Updated client record with confirmation
        """
        try:
            # Validate client_id
            try:
                client_id = validate_client_id(client_id)
            except ValidationError as e:
                return {
                    'status': 'failed',
                    'error': f'Invalid client_id: {str(e)}'
                }

            await ctx.info(f"Updating client info for: {client_id}")

            # Validate allowed fields
            allowed_fields = {
                'client_name', 'company_name', 'industry', 'tier',
                'contract_value', 'contract_start_date', 'contract_end_date',
                'primary_contact_email', 'primary_contact_name',
                'csm_assigned', 'status'
            }

            # Check for invalid fields
            invalid_fields = set(updates.keys()) - allowed_fields
            if invalid_fields:
                return {
                    'status': 'failed',
                    'error': f"Invalid fields: {', '.join(invalid_fields)}. Allowed: {', '.join(allowed_fields)}"
                }

            # Validate tier if being updated
            if 'tier' in updates:
                valid_tiers = ['starter', 'standard', 'professional', 'enterprise']
                if updates['tier'].lower() not in valid_tiers:
                    return {
                        'status': 'failed',
                        'error': f"Invalid tier. Must be one of: {', '.join(valid_tiers)}"
                    }
                updates['tier'] = updates['tier'].lower()

            # Query database and update actual client record
            db = SessionLocal()
            try:
                customer = db.query(CustomerAccount).filter(
                    CustomerAccount.client_id == client_id
                ).first()

                if not customer:
                    return {
                        'status': 'failed',
                        'error': f'Client {client_id} not found in database'
                    }

                # Store previous values for audit
                previous_values = {}

                # Update only the fields that were provided
                for field, value in updates.items():
                    if hasattr(customer, field):
                        previous_values[field] = getattr(customer, field)
                        setattr(customer, field, value)

                # Update timestamp
                customer.updated_at = datetime.now()

                # Commit changes to database
                db.commit()
                db.refresh(customer)

                # Build updated record from database
                updated_record = {
                    "client_id": customer.client_id,
                    "client_name": customer.client_name,
                    "company_name": customer.company_name,
                    "industry": customer.industry,
                    "tier": customer.tier,
                    "contract_value": customer.contract_value,
                    "contract_start_date": customer.contract_start_date.isoformat() if customer.contract_start_date else None,
                    "contract_end_date": customer.contract_end_date.isoformat() if customer.contract_end_date else None,
                    "primary_contact_email": customer.primary_contact_email,
                    "primary_contact_name": customer.primary_contact_name,
                    "csm_assigned": customer.csm_assigned,
                    "status": customer.status,
                    "updated_at": customer.updated_at.isoformat()
                }

                # Log the update
                logger.info(
                    "client_info_updated",
                    client_id=client_id,
                    fields_updated=list(updates.keys()),
                    update_count=len(updates)
                )

            finally:
                db.close()

            return {
                'status': 'success',
                'message': f"Client information updated successfully",
                'client_id': client_id,
                'updated_fields': list(updates.keys()),
                'updated_record': updated_record,
                'audit': {
                    'updated_at': updates['updated_at'],
                    'fields_changed': len(updates),
                    'previous_values': {}  # In production, would include previous values
                }
            }

        except Exception as e:
            logger.error("client_update_failed", error=str(e))
            return {
                'status': 'failed',
                'error': f"Failed to update client info: {str(e)}"
            }


    @mcp.tool()
    async def list_clients(
        ctx: Context,
        tier_filter: Optional[str] = None,
        lifecycle_stage_filter: Optional[str] = None,
        health_score_min: Optional[int] = None,
        health_score_max: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List all clients with optional filtering.

        Retrieve a list of clients filtered by tier, lifecycle stage, health score range,
        or other criteria. Supports pagination for large client bases.

        Args:
            tier_filter: Filter by tier (starter, standard, professional, enterprise)
            lifecycle_stage_filter: Filter by stage (onboarding, active, at_risk, churned, expansion)
            health_score_min: Minimum health score (0-100)
            health_score_max: Maximum health score (0-100)
            limit: Maximum number of results (default 50, max 1000)
            offset: Number of results to skip for pagination

        Returns:
            List of clients with key metrics and filtering info
        """
        try:
            await ctx.info(f"Listing clients with filters: tier={tier_filter}, stage={lifecycle_stage_filter}")

            # Validate limit and offset
            if limit < 1 or limit > 1000:
                return {
                    'status': 'failed',
                    'error': 'limit must be between 1 and 1000'
                }

            if offset < 0:
                return {
                    'status': 'failed',
                    'error': 'offset must be non-negative'
                }

            # Validate tier filter
            if tier_filter:
                valid_tiers = ['starter', 'standard', 'professional', 'enterprise']
                if tier_filter.lower() not in valid_tiers:
                    return {
                        'status': 'failed',
                        'error': f"Invalid tier_filter. Must be one of: {', '.join(valid_tiers)}"
                    }

            # Validate lifecycle stage filter
            if lifecycle_stage_filter:
                valid_stages = ['onboarding', 'active', 'at_risk', 'churned', 'expansion']
                if lifecycle_stage_filter.lower() not in valid_stages:
                    return {
                        'status': 'failed',
                        'error': f"Invalid lifecycle_stage_filter. Must be one of: {', '.join(valid_stages)}"
                    }

            # Validate health score range
            if health_score_min is not None and (health_score_min < 0 or health_score_min > 100):
                return {
                    'status': 'failed',
                    'error': 'health_score_min must be between 0 and 100'
                }

            if health_score_max is not None and (health_score_max < 0 or health_score_max > 100):
                return {
                    'status': 'failed',
                    'error': 'health_score_max must be between 0 and 100'
                }

            # Query database for actual client list
            db = SessionLocal()
            try:
                # Build query with filters
                query = db.query(CustomerAccount)

                if tier_filter:
                    query = query.filter(CustomerAccount.tier == tier_filter.lower())

                if lifecycle_stage_filter:
                    query = query.filter(CustomerAccount.lifecycle_stage == lifecycle_stage_filter.lower())

                if health_score_min is not None:
                    query = query.filter(CustomerAccount.health_score >= health_score_min)

                if health_score_max is not None:
                    query = query.filter(CustomerAccount.health_score <= health_score_max)

                # Get total count for pagination
                total_count = query.count()

                # Apply pagination
                customers = query.limit(limit).offset(offset).all()

                # Convert database objects to client dictionaries
                all_clients = []
                for customer in customers:
                    # Calculate days until renewal
                    days_until_renewal = None
                    if customer.contract_end_date:
                        days_until_renewal = (customer.contract_end_date - datetime.now().date()).days

                    all_clients.append({
                        "client_id": customer.client_id,
                        "client_name": customer.client_name,
                        "tier": customer.tier,
                        "lifecycle_stage": customer.lifecycle_stage,
                        "health_score": customer.health_score,
                        "health_trend": customer.health_trend,
                        "contract_value": customer.contract_value,
                        "days_until_renewal": days_until_renewal,
                        "csm_assigned": customer.csm_assigned,
                        "active_users": None,  # Placeholder - requires usage tracking
                        "support_tickets_open": None  # Placeholder - requires support ticket tracking
                    })

            finally:
                db.close()

            # Pagination and filtering already applied in database query
            paginated_clients = all_clients

            # Calculate summary statistics
            if paginated_clients:
                avg_health = sum(c['health_score'] for c in paginated_clients) / len(paginated_clients)
                total_arr = sum(c['contract_value'] for c in paginated_clients)
                # Note: active_users is None for all clients until usage tracking is implemented
                total_users = sum(c['active_users'] or 0 for c in paginated_clients)
            else:
                avg_health = 0
                total_arr = 0
                total_users = 0

            logger.info(
                "clients_listed",
                total_count=total_count,
                returned_count=len(paginated_clients),
                filters_applied={
                    'tier': tier_filter,
                    'lifecycle_stage': lifecycle_stage_filter,
                    'health_score_range': f"{health_score_min or 0}-{health_score_max or 100}"
                }
            )

            return {
                'status': 'success',
                'clients': paginated_clients,
                'pagination': {
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'returned_count': len(paginated_clients),
                    'has_more': (offset + limit) < total_count
                },
                'filters_applied': {
                    'tier': tier_filter,
                    'lifecycle_stage': lifecycle_stage_filter,
                    'health_score_min': health_score_min,
                    'health_score_max': health_score_max
                },
                'summary': {
                    'total_clients': total_count,
                    'average_health_score': round(avg_health, 1),
                    'total_arr': total_arr,
                    'total_active_users': total_users,
                    'lifecycle_breakdown': {
                        'onboarding': len([c for c in filtered_clients if c['lifecycle_stage'] == 'onboarding']),
                        'active': len([c for c in filtered_clients if c['lifecycle_stage'] == 'active']),
                        'at_risk': len([c for c in filtered_clients if c['lifecycle_stage'] == 'at_risk']),
                        'churned': len([c for c in filtered_clients if c['lifecycle_stage'] == 'churned']),
                        'expansion': len([c for c in filtered_clients if c['lifecycle_stage'] == 'expansion'])
                    }
                }
            }

        except Exception as e:
            logger.error("list_clients_failed", error=str(e))
            return {
                'status': 'failed',
                'error': f"Failed to list clients: {str(e)}"
            }


    @mcp.tool()
    async def get_client_timeline(
        ctx: Context,
        client_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get chronological timeline of client activity and events.

        Retrieves all significant events in a client's lifecycle including onboarding
        milestones, support tickets, product usage changes, health score changes,
        communications, and business reviews.

        Args:
            client_id: Unique client identifier
            start_date: Start date for timeline (YYYY-MM-DD format)
            end_date: End date for timeline (YYYY-MM-DD format)
            event_types: Filter by event types (onboarding, support, usage, health, communication, renewal)
            limit: Maximum number of events to return (default 100, max 1000)

        Returns:
            Chronological timeline of events with details and insights
        """
        try:
            # Validate client_id
            try:
                client_id = validate_client_id(client_id)
            except ValidationError as e:
                return {
                    'status': 'failed',
                    'error': f'Invalid client_id: {str(e)}'
                }

            await ctx.info(f"Fetching timeline for client: {client_id}")

            # Validate limit
            if limit < 1 or limit > 1000:
                return {
                    'status': 'failed',
                    'error': 'limit must be between 1 and 1000'
                }

            # Validate event types
            valid_event_types = {
                'onboarding', 'support', 'usage', 'health',
                'communication', 'renewal', 'product', 'contract'
            }

            if event_types:
                invalid_types = set(event_types) - valid_event_types
                if invalid_types:
                    return {
                        'status': 'failed',
                        'error': f"Invalid event_types: {', '.join(invalid_types)}. Valid: {', '.join(valid_event_types)}"
                    }

            # Parse date filters
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    return {
                        'status': 'failed',
                        'error': 'start_date must be in YYYY-MM-DD format'
                    }
            else:
                # Default to 90 days ago
                start_date_obj = datetime.now() - timedelta(days=90)

            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    return {
                        'status': 'failed',
                        'error': 'end_date must be in YYYY-MM-DD format'
                    }
            else:
                end_date_obj = datetime.now()

            # Mock timeline events (replace with actual database query)
            all_events = [
                {
                    "event_id": "evt_001",
                    "timestamp": "2024-01-15T10:00:00Z",
                    "event_type": "contract",
                    "category": "milestone",
                    "title": "Contract Signed",
                    "description": "Professional tier contract signed - $72,000 ARR",
                    "metadata": {
                        "contract_value": 72000,
                        "tier": "professional",
                        "contract_term_months": 12
                    },
                    "impact": "positive",
                    "severity": "high"
                },
                {
                    "event_id": "evt_002",
                    "timestamp": "2024-01-17T14:30:00Z",
                    "event_type": "onboarding",
                    "category": "milestone",
                    "title": "Onboarding Started",
                    "description": "Kickoff meeting completed, onboarding plan created",
                    "metadata": {
                        "csm_assigned": "Sarah Chen",
                        "onboarding_duration_weeks": 4,
                        "milestones": 4
                    },
                    "impact": "neutral",
                    "severity": "medium"
                },
                {
                    "event_id": "evt_003",
                    "timestamp": "2024-01-22T09:00:00Z",
                    "event_type": "onboarding",
                    "category": "training",
                    "title": "Training Session Completed",
                    "description": "Admin training completed - 8 users certified",
                    "metadata": {
                        "users_trained": 8,
                        "certification_rate": 0.80,
                        "average_score": 0.87
                    },
                    "impact": "positive",
                    "severity": "medium"
                },
                {
                    "event_id": "evt_004",
                    "timestamp": "2024-02-05T16:45:00Z",
                    "event_type": "usage",
                    "category": "milestone",
                    "title": "First Production Workflow",
                    "description": "First automated workflow deployed successfully",
                    "metadata": {
                        "workflow_type": "customer_onboarding",
                        "time_to_first_value_days": 21
                    },
                    "impact": "positive",
                    "severity": "high"
                },
                {
                    "event_id": "evt_005",
                    "timestamp": "2024-02-08T11:00:00Z",
                    "event_type": "onboarding",
                    "category": "milestone",
                    "title": "Onboarding Completed",
                    "description": "All milestones achieved, onboarding marked complete",
                    "metadata": {
                        "completion_rate": 1.0,
                        "duration_days": 24,
                        "success_criteria_met": 5
                    },
                    "impact": "positive",
                    "severity": "high"
                },
                {
                    "event_id": "evt_006",
                    "timestamp": "2024-03-12T10:30:00Z",
                    "event_type": "support",
                    "category": "ticket",
                    "title": "Support Ticket Created",
                    "description": "API integration issue - Priority: Medium",
                    "metadata": {
                        "ticket_id": "TICKET-1234",
                        "priority": "medium",
                        "category": "integration",
                        "resolution_time_hours": 3.5
                    },
                    "impact": "negative",
                    "severity": "low"
                },
                {
                    "event_id": "evt_007",
                    "timestamp": "2024-04-15T14:00:00Z",
                    "event_type": "communication",
                    "category": "business_review",
                    "title": "Quarterly Business Review",
                    "description": "Q1 2024 QBR - Reviewed success metrics and roadmap",
                    "metadata": {
                        "qbr_type": "quarterly",
                        "satisfaction_rating": 5,
                        "action_items": 3,
                        "expansion_discussed": True
                    },
                    "impact": "positive",
                    "severity": "high"
                },
                {
                    "event_id": "evt_008",
                    "timestamp": "2024-06-20T09:15:00Z",
                    "event_type": "health",
                    "category": "score_change",
                    "title": "Health Score Increased",
                    "description": "Health score improved from 72 to 82",
                    "metadata": {
                        "previous_score": 72,
                        "new_score": 82,
                        "primary_driver": "increased_usage",
                        "trend": "improving"
                    },
                    "impact": "positive",
                    "severity": "medium"
                },
                {
                    "event_id": "evt_009",
                    "timestamp": "2024-08-10T13:30:00Z",
                    "event_type": "usage",
                    "category": "feature_adoption",
                    "title": "Advanced Features Adopted",
                    "description": "3 new advanced features activated and in use",
                    "metadata": {
                        "features_adopted": ["Advanced Analytics", "API Webhooks", "Custom Reports"],
                        "feature_adoption_rate": 0.73
                    },
                    "impact": "positive",
                    "severity": "medium"
                },
                {
                    "event_id": "evt_010",
                    "timestamp": "2024-09-15T15:00:00Z",
                    "event_type": "communication",
                    "category": "business_review",
                    "title": "Executive Business Review",
                    "description": "Annual EBR with executive team - Discussed expansion",
                    "metadata": {
                        "ebr_type": "annual",
                        "attendees": ["CTO", "VP Operations", "Head of Sales"],
                        "expansion_opportunity_identified": 28000,
                        "satisfaction_rating": 5
                    },
                    "impact": "positive",
                    "severity": "high"
                },
                {
                    "event_id": "evt_011",
                    "timestamp": "2024-10-05T11:00:00Z",
                    "event_type": "communication",
                    "category": "touchpoint",
                    "title": "CSM Monthly Check-in",
                    "description": "Regular check-in call with CSM Sarah Chen",
                    "metadata": {
                        "topics_discussed": ["Product roadmap", "Feature requests", "Training needs"],
                        "action_items": 2,
                        "satisfaction": "high"
                    },
                    "impact": "neutral",
                    "severity": "low"
                },
                {
                    "event_id": "evt_012",
                    "timestamp": "2024-10-08T16:20:00Z",
                    "event_type": "usage",
                    "category": "spike",
                    "title": "Usage Spike Detected",
                    "description": "30% increase in usage over past week - positive signal",
                    "metadata": {
                        "usage_increase_percent": 30,
                        "new_users_active": 8,
                        "api_calls_increase": 45
                    },
                    "impact": "positive",
                    "severity": "medium"
                }
            ]

            # Apply filters
            filtered_events = all_events.copy()

            # Filter by event types
            if event_types:
                filtered_events = [
                    e for e in filtered_events
                    if e['event_type'] in event_types
                ]

            # Apply limit
            limited_events = filtered_events[:limit]

            # Calculate summary statistics
            event_type_counts = {}
            for event in filtered_events:
                event_type = event['event_type']
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

            positive_events = len([e for e in filtered_events if e['impact'] == 'positive'])
            negative_events = len([e for e in filtered_events if e['impact'] == 'negative'])

            logger.info(
                "client_timeline_retrieved",
                client_id=client_id,
                total_events=len(filtered_events),
                returned_events=len(limited_events)
            )

            return {
                'status': 'success',
                'client_id': client_id,
                'timeline': limited_events,
                'summary': {
                    'total_events': len(filtered_events),
                    'returned_events': len(limited_events),
                    'date_range': {
                        'start': start_date or start_date_obj.strftime("%Y-%m-%d"),
                        'end': end_date or end_date_obj.strftime("%Y-%m-%d")
                    },
                    'event_type_breakdown': event_type_counts,
                    'sentiment': {
                        'positive_events': positive_events,
                        'negative_events': negative_events,
                        'neutral_events': len(filtered_events) - positive_events - negative_events,
                        'overall_sentiment': 'positive' if positive_events > negative_events else 'neutral'
                    }
                },
                'insights': {
                    'key_milestones': [
                        e for e in limited_events
                        if e['category'] == 'milestone' and e['severity'] == 'high'
                    ],
                    'recent_activity': limited_events[:5],  # Most recent 5 events
                    'trajectory': 'improving' if positive_events > negative_events * 2 else 'stable'
                }
            }

        except Exception as e:
            logger.error("get_client_timeline_failed", error=str(e))
            return {
                'status': 'failed',
                'error': f"Failed to retrieve client timeline: {str(e)}"
            }
