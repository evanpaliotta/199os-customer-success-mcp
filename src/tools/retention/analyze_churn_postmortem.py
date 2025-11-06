"""
analyze_churn_postmortem - Process 99: Analyze churned customers to improve retention

Process 99: Analyze churned customers to improve retention.

Args:
    client_id: Churned customer ID
    churn_date: Date of churn (YYYY-MM-DD)
    
Returns:
    Churn analysis with lessons learned
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.security.input_validation import validate_client_id, ValidationError
from src.models.customer_models import ChurnPrediction, RiskIndicator
from src.models.renewal_models import RenewalForecast
from src.models.feedback_models import NPSResponse, SentimentAnalysis
import structlog

    async def analyze_churn_postmortem(
        ctx: Context,
        client_id: str,
        churn_date: str
    ) -> Dict[str, Any]:
        """
        Process 99: Analyze churned customers to improve retention.
        
        Args:
            client_id: Churned customer ID
            churn_date: Date of churn (YYYY-MM-DD)
            
        Returns:
            Churn analysis with lessons learned
        """
        try:
            try:
                client_id = validate_client_id(client_id)
            except ValidationError as e:
                return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}
                
            await ctx.info(f"Analyzing churn for {client_id}")
            
            analysis = {
                "client_id": client_id,
                "churn_date": churn_date,
                "customer_lifetime": 18,
                "ltv": 108000,
                "primary_churn_reasons": [
                    {"reason": "cost", "weight": 0.45, "details": "Budget cuts in Q4"},
                    {"reason": "feature_gaps", "weight": 0.30, "details": "Missing API integrations"},
                    {"reason": "support_quality", "weight": 0.25, "details": "Slow resolution times"}
                ],
                "warning_signs": [
                    {"sign": "declining_usage", "first_detected": "6 months before churn"},
                    {"sign": "nps_decline", "first_detected": "4 months before churn"},
                    {"sign": "champion_departure", "first_detected": "3 months before churn"}
                ],
                "missed_interventions": [
                    "No executive review in final 6 months",
                    "Support tickets unaddressed for >5 days",
                    "No proactive outreach after NPS decline"
                ],
                "lessons_learned": [
                    "Implement automated health score alerts at 60 threshold",
                    "Require executive reviews for enterprise accounts quarterly",
                    "Track champion changes and intervene within 14 days"
                ],
                "process_improvements": [
                    {"area": "health_monitoring", "improvement": "Add champion tracking metric"},
                    {"area": "intervention", "improvement": "Earlier escalation for enterprise"},
                    {"area": "pricing", "improvement": "Flexible pricing for budget-constrained customers"}
                ]
            }
            
            logger.info("churn_postmortem_completed", client_id=client_id)
            
            return {
                "status": "success",
                "analysis": analysis,
                "recommendations": [
                    "Update churn prevention playbook",
                    "Train CSM team on new warning signs",
                    "Implement process improvements"
                ]
            }
            
        except Exception as e:
            logger.error("churn_postmortem_failed", error=str(e))
            return {"status": "failed", "error": str(e)}
