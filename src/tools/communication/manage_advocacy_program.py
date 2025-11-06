"""
manage_advocacy_program - Manage customer advocacy and reference programs

Manage customer advocacy and reference programs.

Build and operate customer advocacy programs including case studies, testimonials,
references, speaking engagements, and referrals. Track advocate contributions,
award points, and manage tiered reward systems.

Process 105: Advocacy Program Management
- Multi-tier advocacy programs (Bronze through Champion)
- Contribution tracking (case studies, references, reviews, testimonials)
- Points and rewards system
- Advocate recruitment and nurturing
- Reference management and matching
- ROI tracking and program analytics

Args:
    action: Action to perform (enroll_advocate, get_advocate_profile, track_contribution, etc.)
    client_id: Customer client ID (required for enroll_advocate)
    contact_name: Advocate contact name (required for enroll_advocate)
    contact_email: Advocate email address (required for enroll_advocate)
    contact_title: Advocate job title (optional for enroll_advocate)
    tier: Advocacy tier (required for enroll_advocate)
    advocate_id: Specific advocate ID (required for get_advocate_profile, track_contribution)
    contribution_type: Type of contribution (required for track_contribution)
    contribution_details: Description of contribution (optional for track_contribution)
    points: Points to award (required for award_points)

Returns:
    Action-specific results with advocate details, contributions, or program analytics
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, field_validator
from src.security.input_validation import validate_client_id, ValidationError
import structlog
from src.decorators import mcp_tool
from src.composio import get_composio_client
async def manage_advocacy_program(
        ctx: Context,
        action: Literal[
            "enroll_advocate", "get_advocate_profile", "list_advocates",
            "track_contribution", "award_points", "get_program_analytics"
        ],
        client_id: Optional[str] = None,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_title: Optional[str] = None,
        tier: Optional[Literal["bronze", "silver", "gold", "platinum", "champion"]] = None,
        advocate_id: Optional[str] = None,
        contribution_type: Optional[Literal[
            "case_study", "reference", "review", "testimonial",
            "speaking_engagement", "referral"
        ]] = None,
        contribution_details: Optional[str] = None,
        points: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Manage customer advocacy and reference programs.

        Build and operate customer advocacy programs including case studies, testimonials,
        references, speaking engagements, and referrals. Track advocate contributions,
        award points, and manage tiered reward systems.

        Process 105: Advocacy Program Management
        - Multi-tier advocacy programs (Bronze through Champion)
        - Contribution tracking (case studies, references, reviews, testimonials)
        - Points and rewards system
        - Advocate recruitment and nurturing
        - Reference management and matching
        - ROI tracking and program analytics

        Args:
            action: Action to perform (enroll_advocate, get_advocate_profile, track_contribution, etc.)
            client_id: Customer client ID (required for enroll_advocate)
            contact_name: Advocate contact name (required for enroll_advocate)
            contact_email: Advocate email address (required for enroll_advocate)
            contact_title: Advocate job title (optional for enroll_advocate)
            tier: Advocacy tier (required for enroll_advocate)
            advocate_id: Specific advocate ID (required for get_advocate_profile, track_contribution)
            contribution_type: Type of contribution (required for track_contribution)
            contribution_details: Description of contribution (optional for track_contribution)
            points: Points to award (required for award_points)

        Returns:
            Action-specific results with advocate details, contributions, or program analytics
        """
        try:
            await ctx.info(f"Executing advocacy action: {action}")

            # ================================================================
            # ENROLL ADVOCATE
            # ================================================================
            if action == "enroll_advocate":
                if not client_id or not contact_name or not contact_email or not tier:
                    return {
                        'status': 'failed',
                        'error': 'enroll_advocate requires client_id, contact_name, contact_email, and tier'
                    }'
                    }

                # Generate advocate ID
                timestamp = int(datetime.now().timestamp())
                advocate_id = f"advocate_{timestamp}_{client_id.split('_')[-1]}"

                # Create advocate profile
                advocate = AdvocateProfile(
                    advocate_id=advocate_id,
                    client_id=client_id,
                    contact_name=contact_name,
                    contact_email=contact_email,
                    contact_title=contact_title or "Customer",
                    tier=AdvocacyTier(tier)
                )

                # Tier benefits
                tier_benefits = {
                    'bronze': {
                        'points_multiplier': 1.0,
                        'perks': ['Exclusive content', 'Early feature access', 'Advocate badge'],
                        'point_threshold': 0
                    },
                    'silver': {
                        'points_multiplier': 1.25,
                        'perks': ['All Bronze perks', 'Priority support', 'Swag package'],
                        'point_threshold': 500
                    },
                    'gold': {
                        'points_multiplier': 1.5,
                        'perks': ['All Silver perks', 'Executive roundtables', 'Conference pass'],
                        'point_threshold': 1500
                    },
                    'platinum': {
                        'points_multiplier': 1.75,
                        'perks': ['All Gold perks', 'Advisory board seat', 'Co-marketing opportunities'],
                        'point_threshold': 3000
                    },
                    'champion': {
                        'points_multiplier': 2.0,
                        'perks': ['All Platinum perks', 'Speaking opportunities', 'VIP treatment', 'Custom rewards'],
                        'point_threshold': 5000
                    }
                }

                logger.info(
                    "advocate_enrolled",
                    advocate_id=advocate_id,
                    client_id=client_id,
                    tier=tier
                )

                return {
                    'status': 'success',
                    'message': f"Advocate '{contact_name}' enrolled successfully in {tier} tier",
                    'advocate': {
                        'advocate_id': advocate_id,
                        'client_id': client_id,
                        'contact_name': contact_name,
                        'contact_email': contact_email,
                        'contact_title': contact_title,
                        'tier': tier,
                        'enrolled_date': advocate.enrolled_date.isoformat(),
                        'points_earned': 0,
                        'is_active': True
                    },
                    'program_benefits': tier_benefits[tier],
                    'contribution_opportunities': [
                        {
                            'type': 'case_study',
                            'description': 'Participate in customer success story',
                            'points': 500,
                            'estimated_time': '2-3 hours'
                        },
                        {
                            'type': 'reference',
                            'description': 'Provide reference call for prospect',
                            'points': 250,
                            'estimated_time': '30 minutes'
                        },
                        {
                            'type': 'review',
                            'description': 'Write review on G2/Capterra',
                            'points': 300,
                            'estimated_time': '15 minutes'
                        },
                        {
                            'type': 'testimonial',
                            'description': 'Provide testimonial quote',
                            'points': 150,
                            'estimated_time': '10 minutes'
                        },
                        {
                            'type': 'speaking_engagement',
                            'description': 'Speak at webinar or conference',
                            'points': 1000,
                            'estimated_time': '3-5 hours'
                        },
                        {
                            'type': 'referral',
                            'description': 'Refer qualified prospect',
                            'points': 400,
                            'estimated_time': '5 minutes'
                        }
                    ],
                    'next_steps': [
                        'Send welcome email with program details',
                        'Schedule onboarding call to discuss opportunities',
                        'Add to advocate Slack channel or community',
                        'Send first contribution request within 7 days',
                        'Schedule quarterly check-in'
                    ]
                }

            # ================================================================
            # GET ADVOCATE PROFILE
            # ================================================================
            elif action == "get_advocate_profile":
                if not advocate_id:
                    return {
                        'status': 'failed',
                        'error': 'get_advocate_profile requires advocate_id'
                    }

                # Mock advocate profile
                advocate_profile = {
                    'advocate_id': advocate_id,
                    'client_id': 'cs_1696800000_acme',
                    'contact_name': 'Sarah Thompson',
                    'contact_email': 'sarah.thompson@acme.com',
                    'contact_title': 'VP of Product',
                    'tier': 'gold',
                    'enrolled_date': '2024-02-15T10:00:00Z',
                    'is_active': True,

                    # Contributions
                    'contributions': {
                        'case_studies_completed': 2,
                        'references_provided': 7,
                        'reviews_written': 3,
                        'testimonials_given': 4,
                        'speaking_engagements': 1,
                        'referrals_made': 5,
                        'total_contributions': 22
                    },

                    # Points and rewards
                    'points': {
                        'points_earned': 3450,
                        'points_redeemed': 800,
                        'points_available': 2650,
                        'lifetime_points': 3450,
                        'next_tier': 'platinum',
                        'points_to_next_tier': 450
                    },

                    # Impact
                    'impact': {
                        'influenced_deals': 12,
                        'influenced_revenue': 428000,
                        'reference_win_rate': 0.71,
                        'avg_reference_rating': 4.8
                    },

                    # Recent activity
                    'recent_contributions': [
                        {
                            'date': '2025-09-28',
                            'type': 'reference',
                            'description': 'Reference call for Enterprise prospect',
                            'points_earned': 250,
                            'outcome': 'Deal won - $65,000 ARR'
                        },
                        {
                            'date': '2025-09-15',
                            'type': 'case_study',
                            'description': 'Featured customer success story',
                            'points_earned': 500,
                            'outcome': 'Published on website and social media'
                        },
                        {
                            'date': '2025-08-20',
                            'type': 'review',
                            'description': 'G2 review with 5-star rating',
                            'points_earned': 300,
                            'outcome': 'Improved G2 rating to 4.8'
                        }
                    ],

                    # Rewards claimed
                    'rewards_claimed': [
                        'Conference pass - SaaS Summit 2024',
                        'Premium swag package',
                        'Gift card - $200'
                    ]
                }

                return {
                    'status': 'success',
                    'advocate_profile': advocate_profile,
                    'performance': {
                        'advocacy_score': 92,
                        'engagement_level': 'very_high',
                        'responsiveness': 'excellent',
                        'quality_rating': 4.8,
                        'program_tenure_months': 8
                    },
                    'recommendations': [
                        'Nominate for Platinum tier upgrade (450 points away)',
                        'Feature in upcoming webinar series',
                        'Invite to customer advisory board',
                        'Request participation in product launch',
                        'Consider co-marketing case study expansion'
                    ]
                }

            # ================================================================
            # LIST ADVOCATES
            # ================================================================
            elif action == "list_advocates":
                advocates = [
                    {
                        'advocate_id': 'advocate_001',
                        'contact_name': 'Sarah Thompson',
                        'client_id': 'cs_1696800000_acme',
                        'tier': 'gold',
                        'points_earned': 3450,
                        'total_contributions': 22,
                        'enrolled_date': '2024-02-15'
                    },
                    {
                        'advocate_id': 'advocate_002',
                        'contact_name': 'Michael Rodriguez',
                        'client_id': 'cs_1696800100_techco',
                        'tier': 'platinum',
                        'points_earned': 4200,
                        'total_contributions': 31,
                        'enrolled_date': '2023-11-20'
                    },
                    {
                        'advocate_id': 'advocate_003',
                        'contact_name': 'Jennifer Lee',
                        'client_id': 'cs_1696800200_startup',
                        'tier': 'silver',
                        'points_earned': 875,
                        'total_contributions': 8,
                        'enrolled_date': '2024-06-10'
                    }
                ]

                return {
                    'status': 'success',
                    'advocates': advocates,
                    'total_advocates': len(advocates),
                    'program_summary': {
                        'total_advocates': 47,
                        'active_advocates': 42,
                        'by_tier': {
                            'bronze': 18,
                            'silver': 15,
                            'gold': 10,
                            'platinum': 3,
                            'champion': 1
                        },
                        'total_contributions_ytd': 342,
                        'influenced_revenue_ytd': 1847000,
                        'avg_points_per_advocate': 1456
                    }
                }

            # ================================================================
            # TRACK CONTRIBUTION
            # ================================================================
            elif action == "track_contribution":
                if not advocate_id or not contribution_type:
                    return {
                        'status': 'failed',
                        'error': 'track_contribution requires advocate_id and contribution_type'
                    }

                # Points mapping
                contribution_points = {
                    'case_study': 500,
                    'reference': 250,
                    'review': 300,
                    'testimonial': 150,
                    'speaking_engagement': 1000,
                    'referral': 400
                }

                points_earned = contribution_points.get(contribution_type, 100)

                # Generate contribution ID
                timestamp = int(datetime.now().timestamp())
                contribution_id = f"contribution_{timestamp}"

                contribution = {
                    'contribution_id': contribution_id,
                    'advocate_id': advocate_id,
                    'contribution_type': contribution_type,
                    'contribution_details': contribution_details or f"{contribution_type} contribution",
                    'points_earned': points_earned,
                    'recorded_at': datetime.now().isoformat(),
                    'status': 'recorded'
                }

                logger.info(
                    "advocacy_contribution_tracked",
                    contribution_id=contribution_id,
                    advocate_id=advocate_id,
                    type=contribution_type,
                    points=points_earned
                )

                return {
                    'status': 'success',
                    'message': f"{contribution_type.replace('_', ' ').title()} contribution tracked successfully",
                    'contribution': contribution,
                    'advocate_update': {
                        'new_total_points': 3850,  # Mock updated total
                        'tier_progress': 'On track for next tier',
                        'rank': 'Top 15% of advocates'
                    },
                    'next_actions': [
                        'Send thank you email to advocate',
                        'Update advocate profile with contribution',
                        'Share impact metrics when available',
                        'Consider featuring advocate in spotlight'
                    ]
                }

            # ================================================================
            # AWARD POINTS
            # ================================================================
            elif action == "award_points":
                if not advocate_id or points is None:
                    return {
                        'status': 'failed',
                        'error': 'award_points requires advocate_id and points'
                    }

                if points <= 0:
                    return {
                        'status': 'failed',
                        'error': 'points must be greater than 0'
                    }

                award = {
                    'award_id': f"award_{int(datetime.now().timestamp())}",
                    'advocate_id': advocate_id,
                    'points_awarded': points,
                    'reason': contribution_details or 'Bonus points',
                    'awarded_at': datetime.now().isoformat(),
                    'awarded_by': 'CS Team'
                }

                logger.info(
                    "advocacy_points_awarded",
                    advocate_id=advocate_id,
                    points=points
                )

                return {
                    'status': 'success',
                    'message': f"{points} points awarded successfully",
                    'award': award,
                    'advocate_update': {
                        'previous_points': 3450,
                        'new_points': 3450 + points,
                        'tier_status': 'Gold tier maintained'
                    }
                }

            # ================================================================
            # GET PROGRAM ANALYTICS
            # ================================================================
            elif action == "get_program_analytics":
                analytics = {
                    'program_overview': {
                        'total_advocates': 47,
                        'active_advocates': 42,
                        'new_advocates_30d': 5,
                        'churn_rate': 0.04,
                        'avg_tenure_months': 11.3
                    },
                    'tier_distribution': {
                        'bronze': {'count': 18, 'percent': 38.3},
                        'silver': {'count': 15, 'percent': 31.9},
                        'gold': {'count': 10, 'percent': 21.3},
                        'platinum': {'count': 3, 'percent': 6.4},
                        'champion': {'count': 1, 'percent': 2.1}
                    },
                    'contributions': {
                        'total_ytd': 342,
                        'by_type': {
                            'references': 134,
                            'case_studies': 28,
                            'reviews': 67,
                            'testimonials': 54,
                            'speaking_engagements': 12,
                            'referrals': 47
                        },
                        'avg_per_advocate': 7.3,
                        'month_over_month_growth': 0.12
                    },
                    'business_impact': {
                        'influenced_pipeline': 3245000,
                        'influenced_revenue': 1847000,
                        'deals_influenced': 67,
                        'win_rate_with_references': 0.73,
                        'win_rate_without_references': 0.42,
                        'reference_lift': 0.74
                    },
                    'engagement': {
                        'active_participation_rate': 0.89,
                        'avg_contributions_per_advocate': 7.3,
                        'response_rate_to_requests': 0.82,
                        'avg_time_to_respond_days': 2.1
                    },
                    'roi': {
                        'program_cost_ytd': 125000,
                        'influenced_revenue_ytd': 1847000,
                        'roi_ratio': 14.78,
                        'cost_per_advocate': 2660,
                        'revenue_per_advocate': 39298
                    }
                }

                return {
                    'status': 'success',
                    'analytics': analytics,
                    'insights': {
                        'program_health': 'excellent',
                        'key_strengths': [
                            'Outstanding ROI of 14.78:1',
                            'High reference win rate (73% vs 42% baseline)',
                            'Strong advocate engagement and response rates',
                            'Healthy distribution across tiers'
                        ],
                        'opportunities': [
                            'Recruit more Gold and Platinum advocates',
                            'Increase speaking engagement participation',
                            'Launch case study campaign for champions',
                            'Create tiered reward marketplace',
                            'Implement advocate referral bonus program'
                        ]
                    }
                }

            else:
                return {
                    'status': 'failed',
                    'error': f'Unknown action: {action}. Valid: enroll_advocate, get_advocate_profile, list_advocates, track_contribution, award_points, get_program_analytics'
                }

        except Exception as e:
            logger.error("manage_advocacy_program_failed", error=str(e), action=action)
            return {
                'status': 'failed',
                'error': f"Failed to execute advocacy action: {str(e)}"
            }
