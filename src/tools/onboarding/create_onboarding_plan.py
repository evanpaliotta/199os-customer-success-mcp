"""
create_onboarding_plan - Process 79: Create Onboarding Plans & Timelines

Creates a customized onboarding plan with clear milestones, timelines,
and success metrics for each customer

Process 79: Create Onboarding Plans & Timelines

Creates a customized onboarding plan with clear milestones, timelines,
and success metrics for each customer. This ensures structured activation
and reduces time-to-value.

Args:
    client_id: Customer identifier
    customer_goals: List of customer success goals to achieve
    product_tier: Product tier (starter, standard, professional, enterprise)
    team_size: Number of users to onboard
    technical_complexity: Complexity level (low, medium, high)
    timeline_weeks: Target onboarding duration in weeks (1-12)
    success_criteria: Custom success criteria (defaults provided if None)

Returns:
    Customized onboarding plan with milestones, timelines, and success metrics
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.models.onboarding_models import (
from src.decorators import mcp_tool
from src.composio import get_composio_client
async def create_onboarding_plan(
        ctx: Context,
        client_id: str,
        customer_goals: List[str],
        product_tier: str = "professional",
        team_size: int = 10,
        technical_complexity: str = "medium",
        timeline_weeks: int = 4,
        success_criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process 79: Create Onboarding Plans & Timelines

        Creates a customized onboarding plan with clear milestones, timelines,
        and success metrics for each customer. This ensures structured activation
        and reduces time-to-value.

        Args:
            client_id: Customer identifier
            customer_goals: List of customer success goals to achieve
            product_tier: Product tier (starter, standard, professional, enterprise)
            team_size: Number of users to onboard
            technical_complexity: Complexity level (low, medium, high)
            timeline_weeks: Target onboarding duration in weeks (1-12)
            success_criteria: Custom success criteria (defaults provided if None)

        Returns:
            Customized onboarding plan with milestones, timelines, and success metrics
        """
        try:'
                }

            await ctx.info(f"Creating onboarding plan for client: {client_id}")

            # Validate inputs
            valid_tiers = ['starter', 'standard', 'professional', 'enterprise']
            if product_tier.lower() not in valid_tiers:
                return {
                    'status': 'failed',
                    'error': f"Invalid product_tier. Must be one of: {', '.join(valid_tiers)}"
                }

            valid_complexity = ['low', 'medium', 'high']
            if technical_complexity.lower() not in valid_complexity:
                return {
                    'status': 'failed',
                    'error': f"Invalid technical_complexity. Must be one of: {', '.join(valid_complexity)}"
                }

            if timeline_weeks < 1 or timeline_weeks > 12:
                return {
                    'status': 'failed',
                    'error': 'timeline_weeks must be between 1 and 12'
                }

            if team_size < 1 or team_size > 10000:
                return {
                    'status': 'failed',
                    'error': 'team_size must be between 1 and 10000'
                }

            if not customer_goals:
                return {
                    'status': 'failed',
                    'error': 'customer_goals cannot be empty'
                }

            # Define standard milestones based on tier and complexity
            milestones = []

            # Week 1: Foundation
            milestones.append({
                "milestone_id": "M1",
                "name": "Kickoff & Setup",
                "week": 1,
                "sequence_order": 1,
                "description": "Complete initial setup and kickoff meeting",
                "tasks": [
                    "Kickoff call with CSM and implementation team",
                    "Product access provisioning for all users",
                    "Initial configuration and settings",
                    "Integration planning session",
                    "Establish success metrics and KPIs"
                ],
                "success_criteria": [
                    "All users have access",
                    "Admin settings configured",
                    "Integration roadmap created",
                    "Success metrics agreed upon"
                ],
                "estimated_hours": 8,
                "dependencies": [],
                "status": "not_started",
                "completion_percentage": 0.0,
                "blockers": []
            })

            # Week 2: Training & Configuration
            milestones.append({
                "milestone_id": "M2",
                "name": "Core Training",
                "week": 2,
                "sequence_order": 2,
                "description": "Complete core product training for all users",
                "tasks": [
                    "Admin training session (2 hours)",
                    "End-user training session (1.5 hours)",
                    "Best practices workshop",
                    "Q&A and troubleshooting",
                    "Training materials distribution"
                ],
                "success_criteria": [
                    "80% of users completed training",
                    "Training assessment passed (>75% score)",
                    "Key workflows understood",
                    "Users can perform basic tasks independently"
                ],
                "estimated_hours": 12,
                "dependencies": ["M1"],
                "status": "not_started",
                "completion_percentage": 0.0,
                "blockers": []
            })

            # Week 3: Integration & Adoption
            milestones.append({
                "milestone_id": "M3",
                "name": "Integration & First Value",
                "week": 3,
                "sequence_order": 3,
                "description": "Complete integrations and achieve first measurable value",
                "tasks": [
                    "Complete primary integrations",
                    "Import historical data",
                    "Set up automations and workflows",
                    "First production use case completion",
                    "Validate data accuracy"
                ],
                "success_criteria": [
                    "All critical integrations active",
                    "Data migration completed",
                    "First workflow automated",
                    "First measurable outcome achieved",
                    "Data validation passed"
                ],
                "estimated_hours": 16,
                "dependencies": ["M2"],
                "status": "not_started",
                "completion_percentage": 0.0,
                "blockers": []
            })

            # Week 4: Optimization & Handoff
            milestones.append({
                "milestone_id": "M4",
                "name": "Optimization & Success",
                "week": 4,
                "sequence_order": 4,
                "description": "Optimize usage and confirm success criteria met",
                "tasks": [
                    "Usage analysis and optimization review",
                    "Advanced features enablement",
                    "Success metrics review with stakeholders",
                    "Ongoing support transition",
                    "Documentation of customizations"
                ],
                "success_criteria": [
                    "All success criteria met",
                    "Team is self-sufficient",
                    "Ongoing support plan in place",
                    "Customer satisfaction score >4.0",
                    "Usage metrics meeting targets"
                ],
                "estimated_hours": 10,
                "dependencies": ["M3"],
                "status": "not_started",
                "completion_percentage": 0.0,
                "blockers": []
            })

            # Add advanced milestones for enterprise tier
            if product_tier.lower() == "enterprise":
                milestones.append({
                    "milestone_id": "M5",
                    "name": "Advanced Configuration",
                    "week": min(5, timeline_weeks),
                    "sequence_order": 5,
                    "description": "Enterprise features and advanced workflows",
                    "tasks": [
                        "Custom API integrations",
                        "Advanced reporting setup",
                        "Role-based access control (RBAC)",
                        "Enterprise security configuration",
                        "Custom workflow automations",
                        "Single sign-on (SSO) setup"
                    ],
                    "success_criteria": [
                        "Custom integrations deployed",
                        "Enterprise reports configured",
                        "Security audit passed",
                        "RBAC fully implemented",
                        "SSO functioning correctly"
                    ],
                    "estimated_hours": 20,
                    "dependencies": ["M4"],
                    "status": "not_started",
                    "completion_percentage": 0.0,
                    "blockers": []
                })

            # Add complexity-based milestones
            if technical_complexity.lower() == "high":
                milestones.append({
                    "milestone_id": "M6",
                    "name": "Technical Deep Dive",
                    "week": min(timeline_weeks, len(milestones) + 1),
                    "sequence_order": len(milestones) + 1,
                    "description": "Advanced technical implementation and customization",
                    "tasks": [
                        "Custom API development",
                        "Database optimization",
                        "Performance tuning",
                        "Advanced security hardening",
                        "Custom integration development"
                    ],
                    "success_criteria": [
                        "All custom APIs functioning",
                        "Performance benchmarks met",
                        "Security requirements satisfied",
                        "Custom integrations stable"
                    ],
                    "estimated_hours": 24,
                    "dependencies": [milestones[-1]["milestone_id"]],
                    "status": "not_started",
                    "completion_percentage": 0.0,
                    "blockers": []
                })

            # Calculate timeline
            start_date = datetime.now()
            end_date = start_date + timedelta(weeks=timeline_weeks)

            # Generate plan ID
            plan_id = f"onb_{client_id}_{int(datetime.now().timestamp())}"

            # Define default success criteria if not provided
            if not success_criteria:
                success_criteria = [
                    "All users trained and certified",
                    "Primary use case automated",
                    "Integrations completed successfully",
                    f"Time-to-value achieved within {timeline_weeks} weeks",
                    "Customer satisfaction score >4.0",
                    f"Feature adoption rate >70%"
                ]

            # Create onboarding plan
            onboarding_plan = {
                "plan_id": plan_id,
                "client_id": client_id,
                "plan_name": f"Onboarding Plan - {product_tier.title()} Tier",
                "product_tier": product_tier.lower(),
                "start_date": start_date.strftime("%Y-%m-%d"),
                "target_completion_date": end_date.strftime("%Y-%m-%d"),
                "actual_completion_date": None,
                "timeline_weeks": timeline_weeks,
                "customer_goals": customer_goals,
                "success_criteria": success_criteria,
                "milestones": milestones,
                "total_estimated_hours": sum(m["estimated_hours"] for m in milestones),
                "assigned_csm": "Auto-assigned based on tier and availability",
                "assigned_implementation_team": [],
                "status": "draft",
                "completion_percentage": 0.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # Calculate planning metrics
            metrics = {
                "total_tasks": sum(len(m["tasks"]) for m in milestones),
                "total_milestones": len(milestones),
                "estimated_completion_weeks": timeline_weeks,
                "time_to_first_value_target_days": milestones[2]["week"] * 7,  # Week 3, Milestone M3
                "complexity_score": {
                    "low": 1,
                    "medium": 2,
                    "high": 3
                }.get(technical_complexity.lower(), 2),
                "tier_complexity": {
                    "starter": 1,
                    "standard": 2,
                    "professional": 3,
                    "enterprise": 4
                }.get(product_tier.lower(), 2)
            }

            # Generate recommendations
            recommendations = [
                "Review plan with customer stakeholders",
                "Schedule kickoff meeting within 3 days",
                "Assign dedicated CSM and implementation team",
                "Set up automated milestone reminders",
                "Prepare training materials and schedule sessions"
            ]

            if team_size > 50:
                recommendations.append("Consider phased rollout for large team")

            if technical_complexity.lower() == "high":
                recommendations.append("Assign technical specialist for integration support")

            if product_tier.lower() == "enterprise":
                recommendations.append("Schedule executive sponsor alignment call")

            logger.info(
                "onboarding_plan_created",
                client_id=client_id,
                plan_id=plan_id,
                milestones=len(milestones),
                estimated_hours=onboarding_plan["total_estimated_hours"]
            )

            return {
                'status': 'success',
                'message': 'Onboarding plan created successfully',
                'onboarding_plan': onboarding_plan,
                'metrics': metrics,
                'recommendations': recommendations,
                'next_steps': [
                    "Review plan with customer",
                    "Schedule kickoff meeting",
                    "Assign CSM and implementation team",
                    "Activate automated workflows (use activate_onboarding_automation tool)",
                    "Send onboarding welcome email"
                ]
            }

        except Exception as e:
            logger.error("onboarding_plan_creation_failed", error=str(e), client_id=client_id)
            return {
                'status': 'failed',
                'error': f"Failed to create onboarding plan: {str(e)}"
            }
