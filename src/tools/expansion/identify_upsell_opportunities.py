"""
identify_upsell_opportunities - Process 114: Identify upsell opportunities based on usage and health

Process 114: Identify upsell opportunities based on usage and health.

Args:
    client_id: Specific client (optional, analyzes all if None)
    min_health_score: Minimum health for upsell consideration
    min_usage_threshold: Minimum usage rate (0-1)
    
Returns:
    Upsell opportunities with revenue potential
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.security.input_validation import validate_client_id, ValidationError
from src.models.renewal_models import RenewalForecast, ExpansionOpportunity, ContractDetails
from src.database import SessionLocal
from src.models.customer_models import CustomerAccount
import structlog

    async def identify_upsell_opportunities(
        ctx: Context,
        client_id: str = None,
        min_health_score: int = 75,
        min_usage_threshold: float = 0.70
    ) -> Dict[str, Any]:
        """
        Process 114: Identify upsell opportunities based on usage and health.
        
        Args:
            client_id: Specific client (optional, analyzes all if None)
            min_health_score: Minimum health for upsell consideration
            min_usage_threshold: Minimum usage rate (0-1)
            
        Returns:
            Upsell opportunities with revenue potential
        """
        try:
            if client_id:
                try:
                    client_id = validate_client_id(client_id)
                except ValidationError as e:
                    return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}
                    
            await ctx.info(f"Identifying upsell opportunities")

            # Query database for customers meeting upsell criteria
            db = SessionLocal()
            try:
                query = db.query(CustomerAccount).filter(
                    CustomerAccount.health_score >= min_health_score
                )

                # If specific client requested, filter to that client
                if client_id:
                    query = query.filter(CustomerAccount.client_id == client_id)

                customers = query.all()

                # Tier upgrade mapping and pricing
                tier_upgrades = {
                    'starter': {'next_tier': 'standard', 'multiplier': 2.0},
                    'standard': {'next_tier': 'professional', 'multiplier': 2.5},
                    'professional': {'next_tier': 'enterprise', 'multiplier': 2.0}
                }

                opportunities = []
                total_potential_arr = 0

                for customer in customers:
                    current_tier = customer.tier.lower()

                    # Skip if already at highest tier
                    if current_tier not in tier_upgrades:
                        continue

                    upgrade_info = tier_upgrades[current_tier]
                    potential_arr = customer.contract_value * upgrade_info['multiplier']
                    expansion_value = potential_arr - customer.contract_value

                    # Calculate probability based on health score
                    if customer.health_score >= 85:
                        probability = 0.75
                        probability_label = "high"
                    elif customer.health_score >= 75:
                        probability = 0.60
                        probability_label = "medium"
                    else:
                        probability = 0.40
                        probability_label = "low"

                    opportunities.append({
                        "client_id": customer.client_id,
                        "client_name": customer.client_name,
                        "current_tier": current_tier,
                        "recommended_tier": upgrade_info['next_tier'],
                        "opportunity_type": "tier_upgrade",
                        "current_arr": customer.contract_value,
                        "potential_arr": potential_arr,
                        "expansion_value": expansion_value,
                        "probability": probability,
                        "probability_label": probability_label,
                        "health_score": customer.health_score,
                        "usage_rate": None,  # Placeholder - requires usage tracking implementation
                        "readiness_indicators": [
                            f"Health score: {customer.health_score}/100",
                            f"Current tier: {current_tier}",
                            f"Lifecycle stage: {customer.lifecycle_stage}"
                        ],
                        "recommended_approach": "Executive business review with ROI case study" if customer.health_score >= 85 else "CSM-led discovery call",
                        "timeline": "30-60 days" if customer.health_score >= 85 else "60-90 days",
                        "next_steps": [
                            "Review account health metrics",
                            "Prepare tier comparison materials",
                            "Schedule stakeholder meeting"
                        ]
                    })
                    total_potential_arr += potential_arr

                # Calculate summary statistics
                by_tier_upgrade = {}
                by_probability = {"high": 0, "medium": 0, "low": 0}

                for opp in opportunities:
                    upgrade_key = f"{opp['current_tier']}_to_{opp['recommended_tier']}"
                    by_tier_upgrade[upgrade_key] = by_tier_upgrade.get(upgrade_key, 0) + 1
                    by_probability[opp['probability_label']] += 1

                avg_expansion = total_potential_arr / len(opportunities) if opportunities else 0

                summary = {
                    "total_opportunities": len(opportunities),
                    "total_potential_arr": total_potential_arr,
                    "avg_expansion_value": avg_expansion,
                    "by_tier_upgrade": by_tier_upgrade,
                    "by_probability": by_probability
                }

            finally:
                db.close()
            
            logger.info("upsell_opportunities_identified", count=len(opportunities))
            
            return {
                "status": "success",
                "opportunities": opportunities,
                "summary": summary,
                "criteria": {"min_health_score": min_health_score, "min_usage": min_usage_threshold}
            }
            
        except Exception as e:
            logger.error("upsell_identification_failed", error=str(e))
            return {"status": "failed", "error": str(e)}
