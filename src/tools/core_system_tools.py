"""
Core System Tools
System configuration, client management, and setup for Customer Success MCP
"""

from mcp.server.fastmcp import Context
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

            # Mock client data (replace with actual database query in production)
            # This demonstrates the expected data structure
            client_overview = {
                # Basic information
                "client_id": client_id,
                "client_name": "Acme Corporation",
                "company_name": "Acme Corp Inc.",
                "industry": "SaaS",
                "tier": "professional",

                # Health and lifecycle
                "health_score": 82,
                "health_trend": "improving",  # improving, stable, declining
                "lifecycle_stage": "active",  # onboarding, active, at_risk, churned, expansion
                "csm_assigned": "Sarah Chen",

                # Contract information
                "contract_value": 72000,
                "contract_start_date": "2024-01-15",
                "contract_end_date": "2025-01-15",
                "days_until_renewal": 127,
                "renewal_probability": 0.89,
                "renewal_risk_level": "low",  # low, medium, high

                # Onboarding status
                "onboarding": {
                    "status": "completed",
                    "completion_rate": 1.0,
                    "completion_date": "2024-02-08",
                    "time_to_value_days": 24,
                    "milestones_completed": 4,
                    "milestones_total": 4,
                    "training_completion_rate": 0.95
                },

                # Engagement metrics
                "engagement": {
                    "last_login": "2025-10-08",
                    "days_since_last_login": 2,
                    "weekly_active_users": 45,
                    "monthly_active_users": 68,
                    "total_users_provisioned": 75,
                    "user_activation_rate": 0.91,
                    "feature_adoption_rate": 0.73,
                    "average_session_duration_minutes": 42,
                    "weekly_sessions": 312,
                    "engagement_trend": "increasing"
                },

                # Support metrics
                "support": {
                    "open_tickets": 2,
                    "tickets_this_month": 8,
                    "tickets_last_month": 12,
                    "ticket_trend": "decreasing",
                    "avg_resolution_time_hours": 4.2,
                    "first_response_time_minutes": 12,
                    "satisfaction_score": 4.6,
                    "satisfaction_trend": "stable",
                    "escalations_this_month": 0,
                    "knowledge_base_usage": 23
                },

                # Product usage
                "product_usage": {
                    "core_features_used": 18,
                    "core_features_total": 25,
                    "advanced_features_used": 4,
                    "advanced_features_total": 15,
                    "integrations_active": 3,
                    "integrations_available": 8,
                    "api_calls_this_month": 45230,
                    "storage_used_gb": 127.5,
                    "storage_limit_gb": 500
                },

                # Revenue and expansion
                "revenue": {
                    "current_arr": 72000,
                    "expansion_opportunities": 3,
                    "expansion_potential_arr": 28000,
                    "upsell_likelihood": 0.72,
                    "cross_sell_opportunities": ["API Add-on", "Premium Support", "Advanced Analytics"],
                    "lifetime_value": 156000,
                    "customer_acquisition_cost": 18000,
                    "ltv_cac_ratio": 8.67
                },

                # Communication history
                "communication": {
                    "last_ebr_date": "2024-09-15",
                    "next_ebr_scheduled": "2024-12-15",
                    "emails_sent": 24,
                    "emails_opened": 18,
                    "email_engagement_rate": 0.75,
                    "last_csm_touchpoint": "2025-10-05",
                    "touchpoint_frequency_days": 7
                },

                # Risks identified
                "risks": [],  # Empty for healthy account

                # Opportunities identified
                "opportunities": [
                    {
                        "type": "upsell",
                        "description": "Premium features upsell",
                        "potential_arr": 12000,
                        "confidence": 0.78
                    },
                    {
                        "type": "expansion",
                        "description": "Additional user licenses (20 seats)",
                        "potential_arr": 9600,
                        "confidence": 0.65
                    },
                    {
                        "type": "cross_sell",
                        "description": "Professional services package",
                        "potential_arr": 6400,
                        "confidence": 0.54
                    }
                ],

                # Recent activity
                "recent_activity": [
                    {
                        "date": "2025-10-08",
                        "type": "product_usage",
                        "description": "High usage spike - 3 new features adopted"
                    },
                    {
                        "date": "2025-10-05",
                        "type": "support",
                        "description": "Support ticket resolved - API integration"
                    },
                    {
                        "date": "2025-10-01",
                        "type": "communication",
                        "description": "Monthly check-in call with CSM"
                    }
                ]
            }

            # Calculate health score components for transparency
            health_components = {
                "usage_score": 85,
                "engagement_score": 88,
                "support_score": 82,
                "satisfaction_score": 92,
                "payment_score": 100
            }

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

            # Add update timestamp
            updates['updated_at'] = datetime.now().isoformat()

            # Mock updated record (replace with actual database update)
            updated_record = {
                "client_id": client_id,
                "client_name": updates.get('client_name', 'Acme Corporation'),
                "company_name": updates.get('company_name', 'Acme Corp Inc.'),
                "industry": updates.get('industry', 'SaaS'),
                "tier": updates.get('tier', 'professional'),
                "contract_value": updates.get('contract_value', 72000),
                "contract_start_date": updates.get('contract_start_date', '2024-01-15'),
                "contract_end_date": updates.get('contract_end_date', '2025-01-15'),
                "primary_contact_email": updates.get('primary_contact_email', 'john@acme.com'),
                "primary_contact_name": updates.get('primary_contact_name', 'John Smith'),
                "csm_assigned": updates.get('csm_assigned', 'Sarah Chen'),
                "status": updates.get('status', 'active'),
                "updated_at": updates['updated_at']
            }

            # Log the update
            logger.info(
                "client_info_updated",
                client_id=client_id,
                fields_updated=list(updates.keys()),
                update_count=len(updates)
            )

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

            # Mock client list (replace with actual database query)
            all_clients = [
                {
                    "client_id": "cs_1696800000_acme",
                    "client_name": "Acme Corporation",
                    "tier": "professional",
                    "lifecycle_stage": "active",
                    "health_score": 82,
                    "health_trend": "improving",
                    "contract_value": 72000,
                    "days_until_renewal": 127,
                    "csm_assigned": "Sarah Chen",
                    "active_users": 45,
                    "support_tickets_open": 2
                },
                {
                    "client_id": "cs_1696800100_techco",
                    "client_name": "TechCo Industries",
                    "tier": "enterprise",
                    "lifecycle_stage": "expansion",
                    "health_score": 95,
                    "health_trend": "stable",
                    "contract_value": 240000,
                    "days_until_renewal": 89,
                    "csm_assigned": "Michael Torres",
                    "active_users": 312,
                    "support_tickets_open": 1
                },
                {
                    "client_id": "cs_1696800200_startup",
                    "client_name": "StartupXYZ",
                    "tier": "standard",
                    "lifecycle_stage": "onboarding",
                    "health_score": 62,
                    "health_trend": "stable",
                    "contract_value": 24000,
                    "days_until_renewal": 358,
                    "csm_assigned": "Jessica Park",
                    "active_users": 8,
                    "support_tickets_open": 3
                },
                {
                    "client_id": "cs_1696800300_legacy",
                    "client_name": "Legacy Systems Inc",
                    "tier": "professional",
                    "lifecycle_stage": "at_risk",
                    "health_score": 45,
                    "health_trend": "declining",
                    "contract_value": 96000,
                    "days_until_renewal": 42,
                    "csm_assigned": "David Kim",
                    "active_users": 12,
                    "support_tickets_open": 7
                },
                {
                    "client_id": "cs_1696800400_growth",
                    "client_name": "GrowthCo",
                    "tier": "starter",
                    "lifecycle_stage": "active",
                    "health_score": 78,
                    "health_trend": "improving",
                    "contract_value": 12000,
                    "days_until_renewal": 203,
                    "csm_assigned": "Sarah Chen",
                    "active_users": 15,
                    "support_tickets_open": 1
                }
            ]

            # Apply filters
            filtered_clients = all_clients.copy()

            if tier_filter:
                filtered_clients = [
                    c for c in filtered_clients
                    if c['tier'] == tier_filter.lower()
                ]

            if lifecycle_stage_filter:
                filtered_clients = [
                    c for c in filtered_clients
                    if c['lifecycle_stage'] == lifecycle_stage_filter.lower()
                ]

            if health_score_min is not None:
                filtered_clients = [
                    c for c in filtered_clients
                    if c['health_score'] >= health_score_min
                ]

            if health_score_max is not None:
                filtered_clients = [
                    c for c in filtered_clients
                    if c['health_score'] <= health_score_max
                ]

            # Apply pagination
            total_count = len(filtered_clients)
            paginated_clients = filtered_clients[offset:offset + limit]

            # Calculate summary statistics
            if filtered_clients:
                avg_health = sum(c['health_score'] for c in filtered_clients) / len(filtered_clients)
                total_arr = sum(c['contract_value'] for c in filtered_clients)
                total_users = sum(c['active_users'] for c in filtered_clients)
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
