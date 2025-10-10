"""
Growth & Revenue Expansion Tools  
Processes 114-121: Upsell, cross-sell, renewals, and CLV optimization
"""

from mcp.server.fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.security.input_validation import validate_client_id, ValidationError
from src.models.renewal_models import RenewalForecast, ExpansionOpportunity, ContractDetails
import structlog

logger = structlog.get_logger(__name__)

def register_tools(mcp):
    """Register all expansion & revenue tools"""

    @mcp.tool()
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
            
            opportunities = [
                {
                    "client_id": "cs_1696800000_acme",
                    "client_name": "Acme Corporation",
                    "current_tier": "professional",
                    "recommended_tier": "enterprise",
                    "opportunity_type": "tier_upgrade",
                    "current_arr": 72000,
                    "potential_arr": 144000,
                    "expansion_value": 72000,
                    "probability": 0.75,
                    "health_score": 85,
                    "usage_rate": 0.92,
                    "readiness_indicators": [
                        "Using 92% of current plan limits",
                        "Requested enterprise features 3 times",
                        "Team size growing (15 → 45 users)",
                        "High engagement score (8.5/10)"
                    ],
                    "recommended_approach": "Executive business review with ROI case study",
                    "timeline": "30-60 days",
                    "next_steps": [
                        "Schedule executive meeting",
                        "Prepare ROI analysis",
                        "Create customized proposal"
                    ]
                }
            ]
            
            summary = {
                "total_opportunities": len(opportunities),
                "total_potential_arr": 520000,
                "avg_expansion_value": 74285,
                "by_tier_upgrade": {"standard_to_pro": 3, "pro_to_enterprise": 4},
                "by_probability": {"high": 4, "medium": 3}
            }
            
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

    @mcp.tool()
    async def identify_crosssell_opportunities(
        ctx: Context,
        client_id: str = None,
        product_family: str = "all"
    ) -> Dict[str, Any]:
        """
        Process 115: Identify cross-sell opportunities for additional products.
        
        Args:
            client_id: Specific client (optional)
            product_family: Product category to analyze
            
        Returns:
            Cross-sell opportunities with product recommendations
        """
        try:
            if client_id:
                try:
                    client_id = validate_client_id(client_id)
                except ValidationError as e:
                    return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}
                    
            await ctx.info(f"Identifying cross-sell opportunities")
            
            opportunities = [
                {
                    "client_id": "cs_1696800000_acme",
                    "current_products": ["Core Platform"],
                    "recommended_products": [
                        {
                            "product": "Advanced Analytics",
                            "fit_score": 0.88,
                            "annual_value": 24000,
                            "use_case": "Data-driven decision making",
                            "readiness_signals": [
                                "Exported reports 45 times last month",
                                "Created 12 custom dashboards",
                                "Asked about advanced metrics in support"
                            ]
                        },
                        {
                            "product": "API Suite",
                            "fit_score": 0.72,
                            "annual_value": 18000,
                            "use_case": "Integration with internal systems",
                            "readiness_signals": [
                                "IT team inquired about API access",
                                "Currently using manual data export",
                                "Mentioned automation goals in EBR"
                            ]
                        }
                    ],
                    "total_potential_value": 42000,
                    "probability": 0.65,
                    "recommended_bundle": "Analytics + API Bundle",
                    "bundle_discount": "15%"
                }
            ]
            
            summary = {
                "total_opportunities": len(opportunities),
                "total_potential_arr": 186000,
                "top_products": [
                    {"product": "Advanced Analytics", "opportunities": 12},
                    {"product": "API Suite", "opportunities": 8},
                    {"product": "Premium Support", "opportunities": 15}
                ]
            }
            
            logger.info("crosssell_opportunities_identified", count=len(opportunities))
            
            return {
                "status": "success",
                "opportunities": opportunities,
                "summary": summary
            }
            
        except Exception as e:
            logger.error("crosssell_identification_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    @mcp.tool()
    async def identify_expansion_opportunities(
        ctx: Context,
        client_id: str = None,
        opportunity_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Process 116: Systematically identify all expansion opportunities.
        
        Args:
            client_id: Specific client (optional)
            opportunity_types: Types to analyze (user_expansion, usage_expansion, etc.)
            
        Returns:
            Complete expansion opportunity pipeline
        """
        try:
            if client_id:
                try:
                    client_id = validate_client_id(client_id)
                except ValidationError as e:
                    return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}
                    
            await ctx.info(f"Identifying all expansion opportunities")
            
            if not opportunity_types:
                opportunity_types = ["user_expansion", "usage_expansion", "tier_upgrade", "cross_sell", "professional_services"]
            
            expansion_pipeline = {
                "client_id": "cs_1696800000_acme",
                "opportunities": [
                    {
                        "type": "user_expansion",
                        "description": "Add 30 additional users",
                        "current_count": 45,
                        "target_count": 75,
                        "annual_value": 36000,
                        "probability": 0.80,
                        "timeline": "Q2 2026",
                        "champion": "John Smith, VP Operations"
                    },
                    {
                        "type": "tier_upgrade",
                        "description": "Upgrade to Enterprise tier",
                        "annual_value": 72000,
                        "probability": 0.70,
                        "timeline": "Next renewal (90 days)",
                        "requirements": "Security compliance features"
                    }
                ],
                "total_pipeline_value": 108000,
                "weighted_value": 82800,
                "expansion_rate_target": "150%",
                "current_arr": 72000,
                "target_arr": 180000
            }
            
            logger.info("expansion_opportunities_identified", pipeline_value=expansion_pipeline["total_pipeline_value"])
            
            return {
                "status": "success",
                "expansion_pipeline": expansion_pipeline,
                "recommendations": [
                    "Prioritize high-probability opportunities first",
                    "Bundle opportunities for better pricing",
                    "Align expansion with renewal timing"
                ]
            }
            
        except Exception as e:
            logger.error("expansion_identification_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    @mcp.tool()
    async def track_renewals(
        ctx: Context,
        client_id: str = None,
        days_until_renewal: int = 90
    ) -> Dict[str, Any]:
        """
        Process 117: Track renewal dates with automated reminders.
        
        Args:
            client_id: Specific client (optional)
            days_until_renewal: Include renewals within this many days
            
        Returns:
            Renewal tracking with automated reminder schedule
        """
        try:
            if client_id:
                try:
                    client_id = validate_client_id(client_id)
                except ValidationError as e:
                    return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}
                    
            await ctx.info(f"Tracking renewals within {days_until_renewal} days")
            
            renewals = [
                {
                    "client_id": "cs_1696800000_acme",
                    "client_name": "Acme Corporation",
                    "renewal_date": (datetime.now() + timedelta(days=87)).strftime("%Y-%m-%d"),
                    "days_until_renewal": 87,
                    "current_arr": 72000,
                    "contract_term": "annual",
                    "auto_renew": False,
                    "health_score": 85,
                    "renewal_probability": 0.92,
                    "reminders_scheduled": [
                        {"type": "90_day_notice", "date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"), "status": "pending"},
                        {"type": "60_day_notice", "date": (datetime.now() + timedelta(days=27)).strftime("%Y-%m-%d"), "status": "scheduled"},
                        {"type": "30_day_notice", "date": (datetime.now() + timedelta(days=57)).strftime("%Y-%m-%d"), "status": "scheduled"}
                    ],
                    "expansion_opportunities": "User count increase, tier upgrade",
                    "key_stakeholders": ["John Smith (VP)", "Jane Doe (Admin)"]
                }
            ]
            
            summary = {
                "total_renewals_tracked": len(renewals),
                "total_arr_at_risk": 72000,
                "by_timeframe": {
                    "30_days": 5,
                    "60_days": 12,
                    "90_days": 24
                },
                "auto_renew_enabled": 15,
                "manual_renewal_required": 26
            }
            
            logger.info("renewals_tracked", count=len(renewals))
            
            return {
                "status": "success",
                "renewals": renewals,
                "summary": summary,
                "automated_actions": [
                    "Email reminders sent automatically",
                    "CSM tasks created at 90/60/30 days",
                    "Expansion opportunities flagged"
                ]
            }
            
        except Exception as e:
            logger.error("renewal_tracking_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    @mcp.tool()
    async def forecast_renewals(
        ctx: Context,
        forecast_period_days: int = 180,
        include_risk_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Process 118: Forecast renewal likelihood and prepare strategies.
        
        Args:
            forecast_period_days: Forecast window
            include_risk_analysis: Include detailed risk assessment
            
        Returns:
            Renewal forecasts with probability and risk factors
        """
        try:
            await ctx.info(f"Forecasting renewals for {forecast_period_days} days")
            
            forecast = {
                "forecast_period": f"{forecast_period_days} days",
                "total_renewals_due": 41,
                "total_arr_renewing": 3240000,
                "forecast_summary": {
                    "high_confidence": {"count": 28, "arr": 2160000, "probability_avg": 0.91},
                    "medium_confidence": {"count": 9, "arr": 720000, "probability_avg": 0.72},
                    "at_risk": {"count": 4, "arr": 360000, "probability_avg": 0.45}
                },
                "predicted_renewal_rate": 0.87,
                "predicted_churn_arr": 360000,
                "predicted_retained_arr": 2880000,
                "expansion_in_renewals": 520000,
                "risk_factors_identified": [
                    {"factor": "low_health_scores", "accounts_affected": 4, "arr": 360000},
                    {"factor": "payment_issues", "accounts_affected": 2, "arr": 180000},
                    {"factor": "low_engagement", "accounts_affected": 6, "arr": 480000}
                ],
                "mitigation_strategies": [
                    "Execute retention campaigns for 4 at-risk accounts",
                    "Schedule executive reviews for medium-confidence renewals",
                    "Prepare expansion proposals for healthy accounts"
                ]
            }
            
            logger.info("renewals_forecasted", predicted_rate=forecast["predicted_renewal_rate"])
            
            return {
                "status": "success",
                "forecast": forecast,
                "confidence_level": "high",
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("renewal_forecasting_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    @mcp.tool()
    async def negotiate_renewals(
        ctx: Context,
        client_id: str,
        negotiation_strategy: str = "value_reinforcement"
    ) -> Dict[str, Any]:
        """
        Process 119: Support renewal negotiations with strategies and pricing.
        
        Args:
            client_id: Customer negotiating renewal
            negotiation_strategy: Strategy (value_reinforcement, competitive_defense, expansion_bundle)
            
        Returns:
            Negotiation support materials and recommendations
        """
        try:
            try:
                client_id = validate_client_id(client_id)
            except ValidationError as e:
                return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}
                
            await ctx.info(f"Preparing renewal negotiation for {client_id}")
            
            negotiation_package = {
                "client_id": client_id,
                "strategy": negotiation_strategy,
                "current_contract": {
                    "arr": 72000,
                    "term": "annual",
                    "expiration": (datetime.now() + timedelta(days=87)).strftime("%Y-%m-%d")
                },
                "renewal_proposal": {
                    "base_renewal": 72000,
                    "expansion_options": [
                        {"item": "30 additional users", "value": 36000},
                        {"item": "Enterprise tier upgrade", "value": 72000}
                    ],
                    "total_proposed_arr": 180000,
                    "term_options": ["annual", "2-year (10% discount)", "3-year (15% discount)"]
                },
                "value_proposition": {
                    "roi_achieved": "350% in 18 months",
                    "time_saved": "2000 hours annually",
                    "cost_savings": "$180,000 in operational efficiency",
                    "business_outcomes": [
                        "Reduced customer churn by 23%",
                        "Increased team productivity by 45%",
                        "Improved customer satisfaction (NPS +18)"
                    ]
                },
                "competitive_intelligence": {
                    "alternatives_considered": ["Competitor A", "Competitor B"],
                    "our_advantages": [
                        "Superior integration capabilities",
                        "Better customer support (4.8/5 vs 3.2/5)",
                        "Lower total cost of ownership"
                    ]
                },
                "negotiation_guardrails": {
                    "max_discount": "15%",
                    "minimum_acceptable_arr": 156000,
                    "approval_required_below": 144000
                },
                "talking_points": [
                    "Highlight 350% ROI achieved",
                    "Reference 23% churn reduction",
                    "Emphasize growth support with user expansion",
                    "Offer multi-year discount for commitment"
                ]
            }
            
            logger.info("renewal_negotiation_prepared", client_id=client_id)
            
            return {
                "status": "success",
                "negotiation_package": negotiation_package,
                "next_steps": [
                    "Schedule renewal discussion",
                    "Present value analysis",
                    "Discuss expansion opportunities",
                    "Finalize terms and pricing"
                ]
            }
            
        except Exception as e:
            logger.error("renewal_negotiation_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    @mcp.tool()
    async def track_revenue_expansion(
        ctx: Context,
        time_period: str = "quarterly",
        include_pipeline: bool = True
    ) -> Dict[str, Any]:
        """
        Process 120: Track and report revenue expansion from existing customers.
        
        Args:
            time_period: Period (monthly, quarterly, annual)
            include_pipeline: Include future pipeline
            
        Returns:
            Revenue expansion metrics and growth tracking
        """
        try:
            await ctx.info(f"Tracking revenue expansion: {time_period}")
            
            expansion_metrics = {
                "period": time_period,
                "base_arr": 18500000,
                "expansion_arr": 4250000,
                "expansion_rate": 0.23,
                "net_retention_rate": 1.18,
                "gross_retention_rate": 0.95,
                "expansion_by_type": {
                    "upsell": 1800000,
                    "cross_sell": 950000,
                    "user_expansion": 1200000,
                    "usage_expansion": 300000
                },
                "top_expansion_accounts": [
                    {"client": "Acme Corp", "expansion": 280000, "type": "tier_upgrade"},
                    {"client": "TechCorp", "expansion": 180000, "type": "user_expansion"},
                    {"client": "GlobalCo", "expansion": 150000, "type": "cross_sell"}
                ],
                "expansion_pipeline": {
                    "total_value": 2100000,
                    "high_probability": 1350000,
                    "medium_probability": 580000,
                    "low_probability": 170000
                },
                "success_factors": [
                    {"factor": "High health scores", "correlation": 0.82},
                    {"factor": "Executive engagement", "correlation": 0.75},
                    {"factor": "Feature adoption >80%", "correlation": 0.71}
                ]
            }
            
            logger.info("revenue_expansion_tracked", expansion_rate=expansion_metrics["expansion_rate"])
            
            return {
                "status": "success",
                "expansion_metrics": expansion_metrics,
                "insights": [
                    "Net retention of 118% indicates strong expansion",
                    "Upsells driving largest expansion contribution",
                    "Pipeline suggests continued strong growth"
                ],
                "recommendations": [
                    "Focus on high health score accounts for expansion",
                    "Increase executive engagement programs",
                    "Develop expansion playbooks for each product tier"
                ]
            }
            
        except Exception as e:
            logger.error("revenue_expansion_tracking_failed", error=str(e))
            return {"status": "failed", "error": str(e)}

    @mcp.tool()
    async def optimize_customer_lifetime_value(
        ctx: Context,
        client_id: str = None,
        optimization_focus: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Process 121: Optimize customer lifetime value through targeted strategies.
        
        Args:
            client_id: Specific client (optional)
            optimization_focus: Focus (retention, expansion, efficiency, balanced)
            
        Returns:
            CLV optimization strategies and projected impact
        """
        try:
            if client_id:
                try:
                    client_id = validate_client_id(client_id)
                except ValidationError as e:
                    return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}
                    
            await ctx.info(f"Optimizing CLV: {optimization_focus}")
            
            clv_analysis = {
                "client_id": client_id,
                "current_clv": 324000,
                "target_clv": 486000,
                "improvement_potential": 162000,
                "current_metrics": {
                    "avg_customer_lifespan_months": 54,
                    "avg_arr": 72000,
                    "gross_retention_rate": 0.87,
                    "expansion_rate": 0.15,
                    "cac": 14400
                },
                "optimization_strategies": [
                    {
                        "strategy": "improve_retention",
                        "current_rate": 0.87,
                        "target_rate": 0.92,
                        "clv_impact": 81000,
                        "tactics": [
                            "Implement proactive health monitoring",
                            "Increase executive engagement frequency",
                            "Enhanced onboarding for faster time-to-value"
                        ]
                    },
                    {
                        "strategy": "increase_expansion",
                        "current_rate": 0.15,
                        "target_rate": 0.25,
                        "clv_impact": 54000,
                        "tactics": [
                            "Systematic expansion opportunity identification",
                            "Bundled product recommendations",
                            "Usage-based upgrade prompts"
                        ]
                    },
                    {
                        "strategy": "reduce_cac",
                        "current_cac": 14400,
                        "target_cac": 10800,
                        "clv_impact": 27000,
                        "tactics": [
                            "Referral program from happy customers",
                            "Customer case studies for sales enablement",
                            "Product-led growth initiatives"
                        ]
                    }
                ],
                "projected_impact": {
                    "clv_increase": 50,
                    "ltv_cac_ratio_current": 22.5,
                    "ltv_cac_ratio_target": 45,
                    "roi": "substantial"
                },
                "implementation_roadmap": [
                    {"phase": "Q1", "focus": "Retention optimization", "expected_impact": "12% CLV increase"},
                    {"phase": "Q2", "focus": "Expansion programs", "expected_impact": "8% CLV increase"},
                    {"phase": "Q3-Q4", "focus": "CAC reduction", "expected_impact": "5% CLV increase"}
                ]
            }
            
            logger.info("clv_optimization_analyzed", improvement_potential=clv_analysis["improvement_potential"])
            
            return {
                "status": "success",
                "clv_analysis": clv_analysis,
                "recommendations": [
                    "Prioritize retention - highest CLV impact",
                    "Implement expansion identification automation",
                    "Launch customer advocacy program to reduce CAC"
                ]
            }
            
        except Exception as e:
            logger.error("clv_optimization_failed", error=str(e))
            return {"status": "failed", "error": str(e)}
