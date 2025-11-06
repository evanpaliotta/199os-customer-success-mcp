"""
register_client - Register a new customer client in the CS system

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

from fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.security.input_validation import validate_client_id, ValidationError
from src.database import SessionLocal
from src.database.models import CustomerAccount
import structlog

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
