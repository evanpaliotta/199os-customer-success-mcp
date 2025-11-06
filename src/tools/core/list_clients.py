"""
list_clients - List all clients with optional filtering

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

from fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.security.input_validation import validate_client_id, ValidationError
from src.database import SessionLocal
from src.database.models import CustomerAccount
import structlog

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
                        'onboarding': len([c for c in paginated_clients if c['lifecycle_stage'] == 'onboarding']),
                        'active': len([c for c in paginated_clients if c['lifecycle_stage'] == 'active']),
                        'at_risk': len([c for c in paginated_clients if c['lifecycle_stage'] == 'at_risk']),
                        'churned': len([c for c in paginated_clients if c['lifecycle_stage'] == 'churned']),
                        'expansion': len([c for c in paginated_clients if c['lifecycle_stage'] == 'expansion'])
                    }
                }
            }

        except Exception as e:
            logger.error("list_clients_failed", error=str(e))
            return {
                'status': 'failed',
                'error': f"Failed to list clients: {str(e)}"
            }
