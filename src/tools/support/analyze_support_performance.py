"""
analyze_support_performance - Process 113: Support performance analytics and optimization

Process 113: Support performance analytics and optimization.

Comprehensive support analytics including SLA compliance, ticket metrics,
agent performance, customer satisfaction, knowledge base effectiveness,
and actionable recommendations for improvement.

Analysis Types:
- overview: Comprehensive support metrics overview
- sla: SLA compliance and performance
- agent: Agent performance and productivity
- satisfaction: Customer satisfaction analysis
- knowledge_base: KB effectiveness and usage
- trends: Historical trends and forecasting
- comparison: Period-over-period comparison

Args:
    client_id: Customer identifier (optional, for client-specific analysis)
    analysis_type: Type of analysis to perform
    period_days: Analysis period in days (default 30)
    team_filter: Filter by support team
    agent_filter: Filter by specific agent
    priority_filter: Filter by priority level
    include_trends: Include historical trends
    include_recommendations: Include optimization recommendations

Returns:
    Comprehensive analytics with metrics, trends, insights, and recommendations
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re
import structlog
from src.models.support_models import (

    from src.decorators import mcp_tool
from src.composio import get_composio_client

async def analyze_support_performance(
        ctx: Context,
        client_id: Optional[str] = None,
        analysis_type: str = "overview",
        period_days: int = 30,
        team_filter: Optional[str] = None,
        agent_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        include_trends: bool = True,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Process 113: Support performance analytics and optimization.

        Comprehensive support analytics including SLA compliance, ticket metrics,
        agent performance, customer satisfaction, knowledge base effectiveness,
        and actionable recommendations for improvement.

        Analysis Types:
        - overview: Comprehensive support metrics overview
        - sla: SLA compliance and performance
        - agent: Agent performance and productivity
        - satisfaction: Customer satisfaction analysis
        - knowledge_base: KB effectiveness and usage
        - trends: Historical trends and forecasting
        - comparison: Period-over-period comparison

        Args:
            client_id: Customer identifier (optional, for client-specific analysis)
            analysis_type: Type of analysis to perform
            period_days: Analysis period in days (default 30)
            team_filter: Filter by support team
            agent_filter: Filter by specific agent
            priority_filter: Filter by priority level
            include_trends: Include historical trends
            include_recommendations: Include optimization recommendations

        Returns:
            Comprehensive analytics with metrics, trends, insights, and recommendations
        """
        try:
            await ctx.info(f"Analyzing support performance: {analysis_type}")if provided
            if client_id:
            '
                    }

            period_start = datetime.now() - timedelta(days=period_days)
            period_end = datetime.now()

            # OVERVIEW ANALYSIS
            if analysis_type == "overview":
                metrics = _calculate_support_metrics(
                    client_id=client_id,
                    period_start=period_start,
                    period_end=period_end,
                    team_filter=team_filter,
                    agent_filter=agent_filter
                )

                return {
                    'status': 'success',
                    'analysis_type': 'overview',
                    'period': {
                        'start': period_start.isoformat(),
                        'end': period_end.isoformat(),
                        'days': period_days
                    },
                    'metrics': metrics,
                    'key_findings': [
                        f"Total tickets: {metrics['total_tickets']}",
                        f"SLA compliance: {metrics['sla_compliance']:.1%}",
                        f"Avg satisfaction: {metrics['avg_satisfaction']:.1f}/5.0",
                        f"Ticket deflection rate: {metrics['deflection_rate']:.1%}"
                    ],
                    'trends': _calculate_trends(metrics) if include_trends else None,
                    'recommendations': _generate_recommendations(metrics) if include_recommendations else None
                }

            # SLA ANALYSIS
            elif analysis_type == "sla":
                sla_data = _analyze_sla_performance(
                    client_id=client_id,
                    period_start=period_start,
                    period_end=period_end,
                    priority_filter=priority_filter
                )

                return {
                    'status': 'success',
                    'analysis_type': 'sla',
                    'period_days': period_days,
                    'sla_metrics': {
                        'first_response': {
                            'target': '15 minutes',
                            'actual_avg': f"{sla_data['avg_first_response']:.1f} minutes",
                            'compliance': sla_data['first_response_compliance'],
                            'breaches': sla_data['first_response_breaches']
                        },
                        'resolution': {
                            'target': '4 hours',
                            'actual_avg': f"{sla_data['avg_resolution'] / 60:.1f} hours",
                            'compliance': sla_data['resolution_compliance'],
                            'breaches': sla_data['resolution_breaches']
                        }
                    },
                    'by_priority': sla_data['by_priority'],
                    'at_risk_tickets': sla_data['at_risk_tickets'],
                    'critical_alerts': _identify_sla_issues(sla_data),
                    'recommendations': [
                        "Increase staffing during peak hours" if sla_data['resolution_compliance'] < 0.85 else None,
                        "Implement automated routing for P0/P1 tickets" if sla_data['first_response_breaches'] > 5 else None,
                        "Review and update SLA targets for P2/P3 tickets" if sla_data['resolution_compliance'] > 0.98 else None
                    ]
                }

            # AGENT PERFORMANCE
            elif analysis_type == "agent":
                agent_stats = _analyze_agent_performance(
                    period_start=period_start,
                    period_end=period_end,
                    team_filter=team_filter,
                    agent_filter=agent_filter
                )

                return {
                    'status': 'success',
                    'analysis_type': 'agent',
                    'period_days': period_days,
                    'agent_performance': agent_stats['agents'],
                    'team_summary': {
                        'total_agents': len(agent_stats['agents']),
                        'avg_tickets_per_agent': agent_stats['avg_tickets'],
                        'avg_satisfaction': agent_stats['avg_satisfaction'],
                        'top_performers': agent_stats['top_performers'][:5],
                        'needs_support': agent_stats['needs_support']
                    },
                    'workload_distribution': agent_stats['workload_dist'],
                    'insights': _generate_agent_insights(agent_stats)
                }

            # CUSTOMER SATISFACTION
            elif analysis_type == "satisfaction":
                satisfaction_data = _analyze_satisfaction(
                    client_id=client_id,
                    period_start=period_start,
                    period_end=period_end
                )

                return {
                    'status': 'success',
                    'analysis_type': 'satisfaction',
                    'period_days': period_days,
                    'satisfaction_metrics': {
                        'average_rating': satisfaction_data['avg_rating'],
                        'response_rate': satisfaction_data['response_rate'],
                        'ratings_distribution': satisfaction_data['distribution'],
                        'nps_score': satisfaction_data['nps_score']
                    },
                    'sentiment_analysis': {
                        'positive_comments': satisfaction_data['positive_count'],
                        'negative_comments': satisfaction_data['negative_count'],
                        'common_themes': satisfaction_data['themes']
                    },
                    'correlations': {
                        'rating_vs_resolution_time': satisfaction_data['time_correlation'],
                        'rating_vs_priority': satisfaction_data['priority_correlation']
                    },
                    'action_items': _generate_satisfaction_actions(satisfaction_data)
                }

            # KNOWLEDGE BASE EFFECTIVENESS
            elif analysis_type == "knowledge_base":
                kb_analytics = _analyze_kb_effectiveness(
                    period_start=period_start,
                    period_end=period_end
                )

                return {
                    'status': 'success',
                    'analysis_type': 'knowledge_base',
                    'period_days': period_days,
                    'kb_metrics': {
                        'total_articles': kb_analytics['total_articles'],
                        'total_views': kb_analytics['total_views'],
                        'avg_helpfulness': kb_analytics['avg_helpfulness'],
                        'search_queries': kb_analytics['search_count']
                    },
                    'effectiveness': {
                        'deflection_rate': kb_analytics['deflection_rate'],
                        'self_service_ratio': kb_analytics['self_service_ratio'],
                        'estimated_tickets_deflected': kb_analytics['tickets_deflected']
                    },
                    'top_articles': kb_analytics['top_articles'][:10],
                    'low_performing_articles': kb_analytics['low_performing'][:5],
                    'search_gaps': kb_analytics['search_gaps'],
                    'recommendations': [
                        f"Create articles for: {', '.join(kb_analytics['search_gaps'][:3])}",
                        f"Update low-performing articles: {len(kb_analytics['low_performing'])} articles need review",
                        "Promote top articles in customer communications"
                    ]
                }

            # TREND ANALYSIS
            elif analysis_type == "trends":
                trends = _analyze_support_trends(
                    client_id=client_id,
                    period_days=period_days
                )

                return {
                    'status': 'success',
                    'analysis_type': 'trends',
                    'period_days': period_days,
                    'trends': {
                        'ticket_volume': trends['volume_trend'],
                        'sla_compliance': trends['sla_trend'],
                        'satisfaction': trends['satisfaction_trend'],
                        'resolution_time': trends['resolution_trend']
                    },
                    'seasonality': trends['seasonality'],
                    'forecast': {
                        'next_30_days': trends['forecast'],
                        'confidence': trends['forecast_confidence']
                    },
                    'insights': _interpret_trends(trends)
                }

            # COMPARISON ANALYSIS
            elif analysis_type == "comparison":
                # Compare current period to previous period
                current_metrics = _calculate_support_metrics(
                    client_id=client_id,
                    period_start=period_start,
                    period_end=period_end
                )

                previous_start = period_start - timedelta(days=period_days)
                previous_end = period_start

                previous_metrics = _calculate_support_metrics(
                    client_id=client_id,
                    period_start=previous_start,
                    period_end=previous_end
                )

                comparison = _compare_metrics(current_metrics, previous_metrics)

                return {
                    'status': 'success',
                    'analysis_type': 'comparison',
                    'current_period': {
                        'start': period_start.isoformat(),
                        'end': period_end.isoformat()
                    },
                    'previous_period': {
                        'start': previous_start.isoformat(),
                        'end': previous_end.isoformat()
                    },
                    'comparison': comparison,
                    'improvements': comparison['improvements'],
                    'declines': comparison['declines'],
                    'summary': _generate_comparison_summary(comparison)
                }

            else:
                return {
                    'status': 'failed',
                    'error': f"Invalid analysis_type: {analysis_type}"
                }

        except Exception as e:
            logger.error(
                "analyze_support_performance_failed",
                analysis_type=analysis_type,
                error=str(e)
            )
            return {
                'status': 'failed',
                'error': f"Failed to analyze support performance: {str(e)}"
            }
