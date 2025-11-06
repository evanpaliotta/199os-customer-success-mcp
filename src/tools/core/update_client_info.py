"""
update_client_info - Update client information and metadata

Update client information and metadata.

Allows updating any client field including contact info, tier, contract details,
or custom metadata. Changes are logged for audit trail.

Args:
    client_id: Unique client identifier
    updates: Dictionary of fields to update with new values

Returns:
    Updated client record with confirmation
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.security.input_validation import validate_client_id, ValidationError
from src.database import SessionLocal
from src.database.models import CustomerAccount
import structlog

    from src.decorators import mcp_tool
from src.composio import get_composio_client

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
        try:'
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
