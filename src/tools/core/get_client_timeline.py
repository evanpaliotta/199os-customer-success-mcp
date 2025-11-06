"""
get_client_timeline - Get chronological timeline of client activity and events

Get chronological timeline of client activity and events.

Retrieves all significant events in a client's lifecycle including onboarding
milestones, support tickets, product usage changes, health score changes,
communications, and business reviews.

Args:
    client_id: Unique client identifier
    start_date: Start date for timeline (YYYY-MM-DD format)
    end_date: End date for timeline (YYYY-MM-DD format)
    event_types: Filter by event types (onboarding, support, usage, health, communication, renewal)
    limit: Maximum number of events to return (default 100, max 1000)

Returns:
    Chronological timeline of events with details and insights
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.security.input_validation import validate_client_id, ValidationError
from src.database import SessionLocal
from src.database.models import CustomerAccount
import structlog

    async def get_client_timeline(
        ctx: Context,
        client_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get chronological timeline of client activity and events.

        Retrieves all significant events in a client's lifecycle including onboarding
        milestones, support tickets, product usage changes, health score changes,
        communications, and business reviews.

        Args:
            client_id: Unique client identifier
            start_date: Start date for timeline (YYYY-MM-DD format)
            end_date: End date for timeline (YYYY-MM-DD format)
            event_types: Filter by event types (onboarding, support, usage, health, communication, renewal)
            limit: Maximum number of events to return (default 100, max 1000)

        Returns:
            Chronological timeline of events with details and insights
        """
        try:
            # Validate client_id
            try:
                client_id = validate_client_id(client_id)
            except ValidationError as e:
                return {
                    'status': 'failed',
                    'error': f'Invalid client_id: {str(e)}'
                }

            await ctx.info(f"Fetching timeline for client: {client_id}")

            # Validate limit
            if limit < 1 or limit > 1000:
                return {
                    'status': 'failed',
                    'error': 'limit must be between 1 and 1000'
                }

            # Validate event types
            valid_event_types = {
                'onboarding', 'support', 'usage', 'health',
                'communication', 'renewal', 'product', 'contract'
            }

            if event_types:
                invalid_types = set(event_types) - valid_event_types
                if invalid_types:
                    return {
                        'status': 'failed',
                        'error': f"Invalid event_types: {', '.join(invalid_types)}. Valid: {', '.join(valid_event_types)}"
                    }

            # Parse date filters
            if start_date:
                try:
                    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    return {
                        'status': 'failed',
                        'error': 'start_date must be in YYYY-MM-DD format'
                    }
            else:
                # Default to 90 days ago
                start_date_obj = datetime.now() - timedelta(days=90)

            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    return {
                        'status': 'failed',
                        'error': 'end_date must be in YYYY-MM-DD format'
                    }
            else:
                end_date_obj = datetime.now()

            # Mock timeline events (replace with actual database query)
            all_events = [
                {
                    "event_id": "evt_001",
                    "timestamp": "2024-01-15T10:00:00Z",
                    "event_type": "contract",
                    "category": "milestone",
                    "title": "Contract Signed",
                    "description": "Professional tier contract signed - $72,000 ARR",
                    "metadata": {
                        "contract_value": 72000,
                        "tier": "professional",
                        "contract_term_months": 12
                    },
                    "impact": "positive",
                    "severity": "high"
                },
                {
                    "event_id": "evt_002",
                    "timestamp": "2024-01-17T14:30:00Z",
                    "event_type": "onboarding",
                    "category": "milestone",
                    "title": "Onboarding Started",
                    "description": "Kickoff meeting completed, onboarding plan created",
                    "metadata": {
                        "csm_assigned": "Sarah Chen",
                        "onboarding_duration_weeks": 4,
                        "milestones": 4
                    },
                    "impact": "neutral",
                    "severity": "medium"
                },
                {
                    "event_id": "evt_003",
                    "timestamp": "2024-01-22T09:00:00Z",
                    "event_type": "onboarding",
                    "category": "training",
                    "title": "Training Session Completed",
                    "description": "Admin training completed - 8 users certified",
                    "metadata": {
                        "users_trained": 8,
                        "certification_rate": 0.80,
                        "average_score": 0.87
                    },
                    "impact": "positive",
                    "severity": "medium"
                },
                {
                    "event_id": "evt_004",
                    "timestamp": "2024-02-05T16:45:00Z",
                    "event_type": "usage",
                    "category": "milestone",
                    "title": "First Production Workflow",
                    "description": "First automated workflow deployed successfully",
                    "metadata": {
                        "workflow_type": "customer_onboarding",
                        "time_to_first_value_days": 21
                    },
                    "impact": "positive",
                    "severity": "high"
                },
                {
                    "event_id": "evt_005",
                    "timestamp": "2024-02-08T11:00:00Z",
                    "event_type": "onboarding",
                    "category": "milestone",
                    "title": "Onboarding Completed",
                    "description": "All milestones achieved, onboarding marked complete",
                    "metadata": {
                        "completion_rate": 1.0,
                        "duration_days": 24,
                        "success_criteria_met": 5
                    },
                    "impact": "positive",
                    "severity": "high"
                },
                {
                    "event_id": "evt_006",
                    "timestamp": "2024-03-12T10:30:00Z",
                    "event_type": "support",
                    "category": "ticket",
                    "title": "Support Ticket Created",
                    "description": "API integration issue - Priority: Medium",
                    "metadata": {
                        "ticket_id": "TICKET-1234",
                        "priority": "medium",
                        "category": "integration",
                        "resolution_time_hours": 3.5
                    },
                    "impact": "negative",
                    "severity": "low"
                },
                {
                    "event_id": "evt_007",
                    "timestamp": "2024-04-15T14:00:00Z",
                    "event_type": "communication",
                    "category": "business_review",
                    "title": "Quarterly Business Review",
                    "description": "Q1 2024 QBR - Reviewed success metrics and roadmap",
                    "metadata": {
                        "qbr_type": "quarterly",
                        "satisfaction_rating": 5,
                        "action_items": 3,
                        "expansion_discussed": True
                    },
                    "impact": "positive",
                    "severity": "high"
                },
                {
                    "event_id": "evt_008",
                    "timestamp": "2024-06-20T09:15:00Z",
                    "event_type": "health",
                    "category": "score_change",
                    "title": "Health Score Increased",
                    "description": "Health score improved from 72 to 82",
                    "metadata": {
                        "previous_score": 72,
                        "new_score": 82,
                        "primary_driver": "increased_usage",
                        "trend": "improving"
                    },
                    "impact": "positive",
                    "severity": "medium"
                },
                {
                    "event_id": "evt_009",
                    "timestamp": "2024-08-10T13:30:00Z",
                    "event_type": "usage",
                    "category": "feature_adoption",
                    "title": "Advanced Features Adopted",
                    "description": "3 new advanced features activated and in use",
                    "metadata": {
                        "features_adopted": ["Advanced Analytics", "API Webhooks", "Custom Reports"],
                        "feature_adoption_rate": 0.73
                    },
                    "impact": "positive",
                    "severity": "medium"
                },
                {
                    "event_id": "evt_010",
                    "timestamp": "2024-09-15T15:00:00Z",
                    "event_type": "communication",
                    "category": "business_review",
                    "title": "Executive Business Review",
                    "description": "Annual EBR with executive team - Discussed expansion",
                    "metadata": {
                        "ebr_type": "annual",
                        "attendees": ["CTO", "VP Operations", "Head of Sales"],
                        "expansion_opportunity_identified": 28000,
                        "satisfaction_rating": 5
                    },
                    "impact": "positive",
                    "severity": "high"
                },
                {
                    "event_id": "evt_011",
                    "timestamp": "2024-10-05T11:00:00Z",
                    "event_type": "communication",
                    "category": "touchpoint",
                    "title": "CSM Monthly Check-in",
                    "description": "Regular check-in call with CSM Sarah Chen",
                    "metadata": {
                        "topics_discussed": ["Product roadmap", "Feature requests", "Training needs"],
                        "action_items": 2,
                        "satisfaction": "high"
                    },
                    "impact": "neutral",
                    "severity": "low"
                },
                {
                    "event_id": "evt_012",
                    "timestamp": "2024-10-08T16:20:00Z",
                    "event_type": "usage",
                    "category": "spike",
                    "title": "Usage Spike Detected",
                    "description": "30% increase in usage over past week - positive signal",
                    "metadata": {
                        "usage_increase_percent": 30,
                        "new_users_active": 8,
                        "api_calls_increase": 45
                    },
                    "impact": "positive",
                    "severity": "medium"
                }
            ]

            # Apply filters
            filtered_events = all_events.copy()

            # Filter by event types
            if event_types:
                filtered_events = [
                    e for e in filtered_events
                    if e['event_type'] in event_types
                ]

            # Apply limit
            limited_events = filtered_events[:limit]

            # Calculate summary statistics
            event_type_counts = {}
            for event in filtered_events:
                event_type = event['event_type']
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

            positive_events = len([e for e in filtered_events if e['impact'] == 'positive'])
            negative_events = len([e for e in filtered_events if e['impact'] == 'negative'])

            logger.info(
                "client_timeline_retrieved",
                client_id=client_id,
                total_events=len(filtered_events),
                returned_events=len(limited_events)
            )

            return {
                'status': 'success',
                'client_id': client_id,
                'timeline': limited_events,
                'summary': {
                    'total_events': len(filtered_events),
                    'returned_events': len(limited_events),
                    'date_range': {
                        'start': start_date or start_date_obj.strftime("%Y-%m-%d"),
                        'end': end_date or end_date_obj.strftime("%Y-%m-%d")
                    },
                    'event_type_breakdown': event_type_counts,
                    'sentiment': {
                        'positive_events': positive_events,
                        'negative_events': negative_events,
                        'neutral_events': len(filtered_events) - positive_events - negative_events,
                        'overall_sentiment': 'positive' if positive_events > negative_events else 'neutral'
                    }
                },
                'insights': {
                    'key_milestones': [
                        e for e in limited_events
                        if e['category'] == 'milestone' and e['severity'] == 'high'
                    ],
                    'recent_activity': limited_events[:5],  # Most recent 5 events
                    'trajectory': 'improving' if positive_events > negative_events * 2 else 'stable'
                }
            }

        except Exception as e:
            logger.error("get_client_timeline_failed", error=str(e))
            return {
                'status': 'failed',
                'error': f"Failed to retrieve client timeline: {str(e)}"
            }
