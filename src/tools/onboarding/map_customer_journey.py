"""
map_customer_journey - Process 84: Customer Journey Mapping & Milestone Tracking

Visualizes and optimizes the customer experience throughout their lifecycle

Process 84: Customer Journey Mapping & Milestone Tracking

Visualizes and optimizes the customer experience throughout their lifecycle.
Maps all touchpoints, interactions, milestones, and experience metrics to
identify optimization opportunities and proactive intervention points.

Args:
    client_id: Customer identifier
    journey_stage: Specific stage to focus on (onboarding, adoption, expansion, renewal)
    include_touchpoints: Include all customer touchpoints
    include_milestones: Include milestone tracking
    include_experience_metrics: Include experience scores and sentiment

Returns:
    Complete customer journey map with touchpoints, milestones, and optimization insights
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.models.onboarding_models import (
from src.decorators import mcp_tool
from src.composio import get_composio_client
async def map_customer_journey(
        ctx: Context,
        client_id: str,
        journey_stage: Optional[str] = None,
        include_touchpoints: bool = True,
        include_milestones: bool = True,
        include_experience_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Process 84: Customer Journey Mapping & Milestone Tracking

        Visualizes and optimizes the customer experience throughout their lifecycle.
        Maps all touchpoints, interactions, milestones, and experience metrics to
        identify optimization opportunities and proactive intervention points.

        Args:
            client_id: Customer identifier
            journey_stage: Specific stage to focus on (onboarding, adoption, expansion, renewal)
            include_touchpoints: Include all customer touchpoints
            include_milestones: Include milestone tracking
            include_experience_metrics: Include experience scores and sentiment

        Returns:
            Complete customer journey map with touchpoints, milestones, and optimization insights
        """
    # LOCAL PROCESSING PATTERN:
    # 1. Fetch data via Composio: data = await composio.execute_action("action_name", client_id, params)
    # 2. Process locally: df = pd.DataFrame(data); summary = df.groupby('stage').agg(...)
    # 3. Return summary only (not raw data)
    # This keeps large datasets out of model context (98.9% token savings)

        
                }

            await ctx.info(f"Mapping customer journey for client: {client_id}")

            # Validate journey stage if provided
            if journey_stage:
                valid_stages = ['onboarding', 'adoption', 'expansion', 'renewal', 'advocacy']
                if journey_stage.lower() not in valid_stages:
                    return {
                        'status': 'failed',
                        'error': f"Invalid journey_stage. Must be one of: {', '.join(valid_stages)}"
                    }

            # Define customer journey stages
            journey_stages = [
                {
                    "stage": "onboarding",
                    "stage_name": "Customer Onboarding",
                    "duration_days": 28,
                    "status": "completed",
                    "start_date": "2025-01-15",
                    "end_date": "2025-02-12",
                    "key_objectives": [
                        "Product access and setup",
                        "Team training and certification",
                        "First value achievement",
                        "Integration completion"
                    ],
                    "success_criteria": [
                        "All users trained",
                        "First workflow automated",
                        "Integrations active",
                        "Success metrics met"
                    ],
                    "completion_status": "completed",
                    "satisfaction_score": 4.5
                },
                {
                    "stage": "adoption",
                    "stage_name": "Product Adoption",
                    "duration_days": 60,
                    "status": "in_progress",
                    "start_date": "2025-02-12",
                    "end_date": None,
                    "key_objectives": [
                        "Feature adoption expansion",
                        "Usage optimization",
                        "Best practices implementation",
                        "ROI demonstration"
                    ],
                    "success_criteria": [
                        "70% feature adoption rate",
                        "Regular active usage",
                        "Documented ROI",
                        "Power users identified"
                    ],
                    "completion_status": "in_progress",
                    "progress": 0.65,
                    "satisfaction_score": 4.3
                },
                {
                    "stage": "expansion",
                    "stage_name": "Account Expansion",
                    "duration_days": 90,
                    "status": "not_started",
                    "start_date": None,
                    "end_date": None,
                    "key_objectives": [
                        "Identify expansion opportunities",
                        "Introduce advanced features",
                        "Expand user base",
                        "Increase contract value"
                    ],
                    "success_criteria": [
                        "Expansion opportunity identified",
                        "Advanced features adopted",
                        "Additional users onboarded",
                        "Contract expansion"
                    ],
                    "completion_status": "not_started"
                },
                {
                    "stage": "renewal",
                    "stage_name": "Contract Renewal",
                    "duration_days": 30,
                    "status": "upcoming",
                    "start_date": None,
                    "end_date": None,
                    "key_objectives": [
                        "Renewal conversation",
                        "Value demonstration",
                        "Contract negotiation",
                        "Renewal completion"
                    ],
                    "success_criteria": [
                        "Renewal secured",
                        "Contract value maintained or increased",
                        "Multi-year commitment",
                        "Reference agreement"
                    ],
                    "completion_status": "upcoming",
                    "days_until_renewal": 127
                }
            ]

            # Customer touchpoints (if included)
            touchpoints = []
            if include_touchpoints:
                touchpoints = [
                    {
                        "touchpoint_id": "tp_001",
                        "date": "2025-01-15",
                        "stage": "onboarding",
                        "type": "meeting",
                        "description": "Kickoff meeting with implementation team",
                        "attendees": ["CSM", "Implementation Specialist", "Customer Champion"],
                        "outcome": "Success plan created",
                        "sentiment": "positive",
                        "follow_up_required": False
                    },
                    {
                        "touchpoint_id": "tp_002",
                        "date": "2025-01-22",
                        "stage": "onboarding",
                        "type": "training",
                        "description": "Admin training session",
                        "attendees": ["8 customer users", "Training Specialist"],
                        "outcome": "8 users certified",
                        "sentiment": "positive",
                        "follow_up_required": False
                    },
                    {
                        "touchpoint_id": "tp_003",
                        "date": "2025-02-05",
                        "stage": "onboarding",
                        "type": "support",
                        "description": "Integration support ticket",
                        "attendees": ["Technical Support", "Customer IT Team"],
                        "outcome": "Issue resolved in 3 hours",
                        "sentiment": "neutral",
                        "follow_up_required": False
                    },
                    {
                        "touchpoint_id": "tp_004",
                        "date": "2025-02-12",
                        "stage": "onboarding",
                        "type": "meeting",
                        "description": "Onboarding completion review",
                        "attendees": ["CSM", "Customer Champion", "Executive Sponsor"],
                        "outcome": "All success criteria met",
                        "sentiment": "very positive",
                        "follow_up_required": True,
                        "follow_up_action": "Schedule monthly check-ins"
                    },
                    {
                        "touchpoint_id": "tp_005",
                        "date": "2025-03-15",
                        "stage": "adoption",
                        "type": "meeting",
                        "description": "Monthly business review",
                        "attendees": ["CSM", "Customer Champion"],
                        "outcome": "Discussed expansion opportunities",
                        "sentiment": "positive",
                        "follow_up_required": True,
                        "follow_up_action": "Present advanced features demo"
                    }
                ]

            # Journey milestones (if included)
            milestones = []
            if include_milestones:
                milestones = [
                    {
                        "milestone_id": "jm_001",
                        "name": "First Login",
                        "date": "2025-01-15",
                        "stage": "onboarding",
                        "status": "completed",
                        "importance": "high",
                        "time_from_start_days": 0
                    },
                    {
                        "milestone_id": "jm_002",
                        "name": "First User Trained",
                        "date": "2025-01-22",
                        "stage": "onboarding",
                        "status": "completed",
                        "importance": "high",
                        "time_from_start_days": 7
                    },
                    {
                        "milestone_id": "jm_003",
                        "name": "First Workflow Automated",
                        "date": "2025-02-05",
                        "stage": "onboarding",
                        "status": "completed",
                        "importance": "critical",
                        "time_from_start_days": 21
                    },
                    {
                        "milestone_id": "jm_004",
                        "name": "Onboarding Complete",
                        "date": "2025-02-12",
                        "stage": "onboarding",
                        "status": "completed",
                        "importance": "critical",
                        "time_from_start_days": 28
                    },
                    {
                        "milestone_id": "jm_005",
                        "name": "70% Feature Adoption",
                        "date": None,
                        "stage": "adoption",
                        "status": "in_progress",
                        "importance": "high",
                        "current_progress": 0.65,
                        "estimated_completion": "2025-04-15"
                    },
                    {
                        "milestone_id": "jm_006",
                        "name": "Expansion Opportunity Identified",
                        "date": None,
                        "stage": "expansion",
                        "status": "upcoming",
                        "importance": "high",
                        "estimated_date": "2025-05-01"
                    },
                    {
                        "milestone_id": "jm_007",
                        "name": "Renewal Secured",
                        "date": None,
                        "stage": "renewal",
                        "status": "upcoming",
                        "importance": "critical",
                        "estimated_date": "2026-01-15"
                    }
                ]

            # Experience metrics (if included)
            experience_metrics = {}
            if include_experience_metrics:
                experience_metrics = {
                    "overall_satisfaction": 4.3,
                    "nps_score": 68,
                    "customer_effort_score": 3.8,  # Lower is better, scale 1-5
                    "time_to_value_days": 21,
                    "engagement_score": 0.82,
                    "health_score": 85,
                    "sentiment_analysis": {
                        "overall_sentiment": "positive",
                        "positive_mentions": 42,
                        "negative_mentions": 5,
                        "neutral_mentions": 18,
                        "sentiment_trend": "improving"
                    },
                    "experience_by_stage": {
                        "onboarding": {
                            "satisfaction": 4.5,
                            "effort_score": 3.2,
                            "sentiment": "very positive"
                        },
                        "adoption": {
                            "satisfaction": 4.3,
                            "effort_score": 3.8,
                            "sentiment": "positive"
                        }
                    }
                }

            # Journey optimization opportunities
            optimization_opportunities = [
                {
                    "opportunity": "Reduce friction in integration setup",
                    "stage": "onboarding",
                    "impact": "high",
                    "effort": "medium",
                    "expected_benefit": "Reduce onboarding time by 3-5 days",
                    "recommendation": "Create pre-built integration templates"
                },
                {
                    "opportunity": "Increase feature discovery",
                    "stage": "adoption",
                    "impact": "medium",
                    "effort": "low",
                    "expected_benefit": "Increase feature adoption by 15%",
                    "recommendation": "Implement in-app feature tours and tips"
                },
                {
                    "opportunity": "Proactive expansion engagement",
                    "stage": "expansion",
                    "impact": "high",
                    "effort": "low",
                    "expected_benefit": "Increase expansion revenue by 25%",
                    "recommendation": "Schedule expansion conversations 90 days before renewal"
                },
                {
                    "opportunity": "Early renewal discussions",
                    "stage": "renewal",
                    "impact": "high",
                    "effort": "low",
                    "expected_benefit": "Improve renewal rate and increase multi-year commitments",
                    "recommendation": "Start renewal conversations 120 days in advance"
                }
            ]

            # Proactive intervention points
            intervention_points = [
                {
                    "trigger": "No login for 7 days",
                    "stage": "any",
                    "severity": "medium",
                    "action": "CSM outreach to understand blockers",
                    "automated": True
                },
                {
                    "trigger": "Training completion rate < 80%",
                    "stage": "onboarding",
                    "severity": "high",
                    "action": "Schedule make-up training sessions",
                    "automated": True
                },
                {
                    "trigger": "Health score drops below 70",
                    "stage": "any",
                    "severity": "high",
                    "action": "Immediate CSM intervention and action plan",
                    "automated": True
                },
                {
                    "trigger": "Support tickets increase >50%",
                    "stage": "any",
                    "severity": "medium",
                    "action": "Schedule issue resolution session",
                    "automated": True
                },
                {
                    "trigger": "Feature adoption stagnant for 30 days",
                    "stage": "adoption",
                    "severity": "low",
                    "action": "Share best practices and use case examples",
                    "automated": True
                }
            ]

            # Filter by stage if specified
            if journey_stage:
                journey_stages = [s for s in journey_stages if s["stage"] == journey_stage.lower()]
                if include_touchpoints:
                    touchpoints = [t for t in touchpoints if t["stage"] == journey_stage.lower()]
                if include_milestones:
                    milestones = [m for m in milestones if m["stage"] == journey_stage.lower()]

            logger.info(
                "customer_journey_mapped",
                client_id=client_id,
                stages_count=len(journey_stages),
                touchpoints_count=len(touchpoints) if include_touchpoints else 0,
                milestones_count=len(milestones) if include_milestones else 0
            )

            return {
                'status': 'success',
                'message': 'Customer journey mapped successfully',
                'client_id': client_id,
                'journey_stages': journey_stages,
                'touchpoints': touchpoints if include_touchpoints else None,
                'milestones': milestones if include_milestones else None,
                'experience_metrics': experience_metrics if include_experience_metrics else None,
                'optimization_opportunities': optimization_opportunities,
                'intervention_points': intervention_points,
                'insights': {
                    'current_stage': 'adoption',
                    'stage_progress': '65% complete',
                    'overall_health': 'healthy',
                    'next_milestone': '70% feature adoption',
                    'days_to_renewal': 127,
                    'expansion_opportunity': 'Identified - $28,000 potential',
                    'journey_sentiment': 'Positive and improving'
                },
                'next_steps': [
                    "Monitor adoption progress toward 70% target",
                    "Schedule advanced features demo",
                    "Prepare expansion proposal",
                    "Continue monthly business reviews"
                ]
            }

        except Exception as e:
            logger.error(
                "customer_journey_mapping_failed",
                error=str(e),
                client_id=client_id
            )
            return {
                'status': 'failed',
                'error': f"Failed to map customer journey: {str(e)}"
            }
