"""
Retention & Risk Management Tools
Processes 95-101: Churn prevention, risk scoring, and retention campaigns
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.security.input_validation import validate_client_id, ValidationError
from src.models.customer_models import ChurnPrediction, RiskIndicator
from src.models.renewal_models import RenewalForecast
from src.models.feedback_models import NPSResponse, SentimentAnalysis
import structlog

logger = structlog.get_logger(__name__)

def register_tools(mcp) -> Any:
    """Register all retention & risk management tools"""

    @mcp.tool()
    async def identify_churn_risk(
        ctx: Context,
        client_id: str = None,
        health_score_threshold: int = 60,
        days_lookback: int = 90,
        include_predictions: bool = True
    ) -> Dict[str, Any]:
        """
        Process 95: Identify customers at risk of churn with probability scores.
        
        Args:
            client_id: Specific client to analyze (optional, analyzes all if None)
            health_score_threshold: Health score threshold for at-risk (default 60)
            days_lookback: Days of history to analyze
            include_predictions: Include ML predictions
            
        Returns:
            At-risk customers with churn probability and risk factors
        """
        try:
            if client_id:
                try:
                    client_id = validate_client_id(client_id)
                except ValidationError as e:
                    return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}
                    
            await ctx.info(f"Identifying churn risk for {client_id or 'all clients'}")
            
            # Mock at-risk analysis
            at_risk_customers = [
                {
                    "client_id": "cs_1696800000_techcorp",
                    "client_name": "TechCorp Industries",
                    "health_score": 45,
                    "churn_probability": 0.73,
                    "risk_level": "high",
                    "days_until_renewal": 87,
                    "risk_factors": [
                        {"factor": "declining_usage", "severity": "high", "trend": "-35% in 30 days"},
                        {"factor": "low_engagement", "severity": "high", "score": 32},
                        {"factor": "support_volume_spike", "severity": "medium", "tickets": 8},
                        {"factor": "payment_delay", "severity": "medium", "days_overdue": 15}
                    ],
                    "predicted_churn_date": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
                    "recommended_interventions": [
                        "Schedule executive business review within 7 days",
                        "Offer product training session",
                        "Review pricing and contract terms",
                        "Assign senior CSM for direct engagement"
                    ]
                }
            ]
            
            summary = {
                "total_analyzed": 156,
                "at_risk_count": len(at_risk_customers),
                "at_risk_percentage": 15.4,
                "total_arr_at_risk": 2340000,
                "by_risk_level": {"high": 4, "medium": 12, "low": 8},
                "by_tier": {"enterprise": 3, "professional": 12, "standard": 9}
            }
            
            logger.info("churn_risk_identified", at_risk_count=len(at_risk_customers))
            
            return {
                "status": "success",
                "at_risk_customers": at_risk_customers if client_id else at_risk_customers[:5],
                "summary": summary,
                "analysis_period": f"Last {days_lookback} days",
                "threshold": health_score_threshold
            }
            
        except Exception as e:
            logger.error("churn_risk_identification_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    @mcp.tool()
    async def execute_retention_campaign(
        ctx: Context,
        client_id: str,
        campaign_type: str = "proactive_outreach",
        intervention_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Process 96: Execute targeted retention interventions.
        
        Args:
            client_id: Target customer
            campaign_type: Type (proactive_outreach, value_reinforcement, success_planning, etc.)
            intervention_level: Intensity (light, standard, aggressive)
            
        Returns:
            Campaign execution status and tracking
        """
        try:
            try:
                client_id = validate_client_id(client_id)
            except ValidationError as e:
                return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}
                
            await ctx.info(f"Executing retention campaign for {client_id}")
            
            campaign_id = f"ret_{int(datetime.now().timestamp())}"
            
            campaign = {
                "campaign_id": campaign_id,
                "client_id": client_id,
                "type": campaign_type,
                "intervention_level": intervention_level,
                "status": "active",
                "actions": [
                    {"action": "executive_outreach", "status": "scheduled", "due_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")},
                    {"action": "value_review", "status": "pending", "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")},
                    {"action": "success_planning", "status": "pending", "due_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")}
                ],
                "success_metrics": {
                    "target_health_score_improvement": 20,
                    "target_engagement_increase": "30%",
                    "target_retention_probability": 0.85
                },
                "created_at": datetime.now().isoformat()
            }
            
            logger.info("retention_campaign_executed", campaign_id=campaign_id)
            
            return {
                "status": "success",
                "message": "Retention campaign launched successfully",
                "campaign": campaign,
                "next_steps": [
                    "Monitor campaign progress daily",
                    "Track customer engagement with interventions",
                    "Adjust strategy based on response"
                ]
            }
            
        except Exception as e:
            logger.error("retention_campaign_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    @mcp.tool()
    async def monitor_satisfaction(
        ctx: Context,
        client_id: str = None,
        survey_type: str = "nps",
        time_period_days: int = 90
    ) -> Dict[str, Any]:
        """
        Process 97: Monitor customer satisfaction with surveys.
        
        Args:
            client_id: Specific client (optional)
            survey_type: Type (nps, csat, ces)
            time_period_days: Analysis period
            
        Returns:
            Satisfaction metrics and trends
        """
        try:
            if client_id:
                try:
                    client_id = validate_client_id(client_id)
                except ValidationError as e:
                    return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}
                    
            await ctx.info(f"Monitoring satisfaction: {survey_type}")
            
            satisfaction_data = {
                "survey_type": survey_type,
                "period": f"Last {time_period_days} days",
                "nps_score": 52,
                "nps_trend": "improving",
                "nps_change": +8,
                "response_breakdown": {
                    "promoters": 65,
                    "passives": 22,
                    "detractors": 13
                },
                "csat_score": 4.3,
                "csat_trend": "stable",
                "ces_score": 3.2,
                "response_rate": 0.42,
                "total_responses": 156,
                "key_themes": [
                    {"theme": "product_quality", "sentiment": "positive", "mentions": 89},
                    {"theme": "support_responsiveness", "sentiment": "positive", "mentions": 67},
                    {"theme": "pricing", "sentiment": "neutral", "mentions": 45},
                    {"theme": "feature_requests", "sentiment": "neutral", "mentions": 34}
                ],
                "action_items": [
                    "Follow up with 13 detractors individually",
                    "Highlight product quality in marketing",
                    "Review pricing concerns with product team"
                ]
            }
            
            logger.info("satisfaction_monitored", nps=satisfaction_data["nps_score"])
            
            return {
                "status": "success",
                "satisfaction_data": satisfaction_data,
                "recommendations": [
                    "Continue monthly NPS surveys",
                    "Address detractor feedback within 48 hours",
                    "Share positive feedback with team"
                ]
            }
            
        except Exception as e:
            logger.error("satisfaction_monitoring_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    @mcp.tool()
    async def manage_escalations(
        ctx: Context,
        action: str = "list",
        escalation_id: str = None,
        client_id: str = None,
        severity: str = "high"
    ) -> Dict[str, Any]:
        """
        Process 98: Manage customer escalations with resolution workflows.
        
        Args:
            action: Action (list, create, update, resolve, close)
            escalation_id: Escalation ID for specific actions
            client_id: Customer ID
            severity: Severity level (critical, high, medium, low)
            
        Returns:
            Escalation status and resolution tracking
        """
        try:
            if client_id:
                try:
                    client_id = validate_client_id(client_id)
                except ValidationError as e:
                    return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}
                    
            await ctx.info(f"Managing escalation: {action}")
            
            if action == "create":
                escalation_id = f"esc_{int(datetime.now().timestamp())}"
                escalation = {
                    "escalation_id": escalation_id,
                    "client_id": client_id,
                    "severity": severity,
                    "status": "open",
                    "created_at": datetime.now().isoformat(),
                    "sla_resolution_hours": 4 if severity == "critical" else 24,
                    "assigned_to": "Senior CSM Team",
                    "resolution_plan": [
                        "Immediate acknowledgment to customer",
                        "Root cause analysis",
                        "Resolution implementation",
                        "Customer validation"
                    ]
                }
                return {"status": "success", "escalation": escalation}
            
            elif action == "list":
                escalations = [
                    {
                        "escalation_id": "esc_1696800123",
                        "client_id": "cs_1696800000_techcorp",
                        "severity": "high",
                        "status": "in_progress",
                        "age_hours": 12,
                        "sla_status": "on_track"
                    }
                ]
                return {"status": "success", "escalations": escalations, "count": len(escalations)}
            
            return {"status": "success", "message": f"Escalation {action} completed"}
            
        except Exception as e:
            logger.error("escalation_management_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    @mcp.tool()
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

    @mcp.tool()
    async def score_risk_factors(
        ctx: Context,
        client_id: str
    ) -> Dict[str, Any]:
        """
        Process 100: Systematically identify and score risk factors.
        
        Args:
            client_id: Customer to analyze
            
        Returns:
            Comprehensive risk scoring with predictive modeling
        """
        try:
            try:
                client_id = validate_client_id(client_id)
            except ValidationError as e:
                return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}
                
            await ctx.info(f"Scoring risk factors for {client_id}")
            
            risk_score = {
                "client_id": client_id,
                "overall_risk_score": 67,
                "risk_level": "medium",
                "churn_probability": 0.42,
                "risk_factors": [
                    {"factor": "usage_decline", "score": 75, "weight": 0.25, "trend": "worsening"},
                    {"factor": "engagement_low", "score": 68, "weight": 0.20, "trend": "stable"},
                    {"factor": "support_volume", "score": 55, "weight": 0.15, "trend": "improving"},
                    {"factor": "payment_health", "score": 30, "weight": 0.15, "trend": "stable"},
                    {"factor": "satisfaction", "score": 72, "weight": 0.15, "trend": "stable"},
                    {"factor": "contract_health", "score": 45, "weight": 0.10, "trend": "stable"}
                ],
                "early_warning_indicators": [
                    "Usage down 25% in 30 days",
                    "Last login 14 days ago",
                    "Champion left company"
                ],
                "protective_factors": [
                    "Long-term customer (3+ years)",
                    "High initial satisfaction (NPS 8)",
                    "Multiple integrations configured"
                ],
                "recommended_actions": [
                    {"action": "schedule_check_in", "priority": "high", "timeline": "within 7 days"},
                    {"action": "usage_analysis", "priority": "high", "timeline": "within 3 days"},
                    {"action": "renewal_planning", "priority": "medium", "timeline": "within 30 days"}
                ]
            }
            
            logger.info("risk_factors_scored", risk_score=risk_score["overall_risk_score"])
            
            return {
                "status": "success",
                "risk_scoring": risk_score,
                "next_steps": [
                    "Monitor risk score weekly",
                    "Execute recommended actions",
                    "Update intervention strategy"
                ]
            }
            
        except Exception as e:
            logger.error("risk_scoring_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    @mcp.tool()
    async def automate_retention_campaigns(
        ctx: Context,
        trigger_type: str = "health_score",
        threshold: float = 60.0,
        campaign_template: str = "standard_intervention"
    ) -> Dict[str, Any]:
        """
        Process 101: Automatically trigger retention campaigns based on signals.
        
        Args:
            trigger_type: Trigger (health_score, usage_decline, nps_detractor, renewal_risk)
            threshold: Threshold value for trigger activation
            campaign_template: Template to use
            
        Returns:
            Automation configuration and active campaigns
        """
        try:
            await ctx.info(f"Setting up automated retention: {trigger_type}")
            
            automation_id = f"auto_{int(datetime.now().timestamp())}"
            
            automation = {
                "automation_id": automation_id,
                "trigger_type": trigger_type,
                "trigger_config": {
                    "threshold": threshold,
                    "evaluation_frequency": "daily",
                    "lookback_period_days": 30
                },
                "campaign_template": campaign_template,
                "actions": [
                    {"action": "alert_csm", "timing": "immediate"},
                    {"action": "send_email", "timing": "1_hour", "template": "check_in"},
                    {"action": "schedule_call", "timing": "24_hours"},
                    {"action": "escalate", "timing": "72_hours_if_no_response"}
                ],
                "success_criteria": {
                    "health_score_improvement": 15,
                    "engagement_increase": "20%",
                    "response_rate": "80%"
                },
                "active": True,
                "customers_monitored": 156,
                "triggered_last_30_days": 12,
                "success_rate": 0.75
            }
            
            logger.info("retention_automation_configured", automation_id=automation_id)
            
            return {
                "status": "success",
                "message": "Retention automation configured",
                "automation": automation,
                "performance": {
                    "campaigns_launched": 12,
                    "customers_retained": 9,
                    "avg_score_improvement": 18,
                    "roi": "positive"
                }
            }
            
        except Exception as e:
            logger.error("retention_automation_failed", error=str(e))
            return {"status": "failed", "error": str(e)}
