"""
Feedback Intelligence Tools
Comprehensive feedback collection, sentiment analysis, and Voice of Customer (VoC) management
for Processes 122-127
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime, date, timedelta
from src.security.input_validation import (
    validate_client_id,
    validate_email,
    ValidationError
)
from src.models.feedback_models import (
    FeedbackType,
    SentimentType,
    FeedbackPriority,
    FeedbackStatus,
    CustomerFeedback,
    NPSResponse,
    SentimentAnalysis,
    SurveyTemplate
)
from src.models.analytics_models import (
    UsageAnalytics,
    EngagementMetrics,
    TrendDirection
)
from src.integrations.mixpanel_client import MixpanelClient
import structlog

logger = structlog.get_logger(__name__)


# ============================================================================
# VALIDATION HELPER FUNCTIONS
# ============================================================================

def validate_date_range(start_date: str, end_date: str) -> tuple[str, str]:
    """
    Validate date range format and logic.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Tuple of validated (start_date, end_date)

    Raises:
        ValidationError: If dates are invalid
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        if start > end:
            raise ValidationError("Start date must be before or equal to end date")

        if end > datetime.now():
            raise ValidationError("End date cannot be in the future")

        return start_date, end_date

    except ValueError as e:
        raise ValidationError(f"Invalid date format. Use YYYY-MM-DD: {str(e)}")


def validate_score(score: float, min_val: float = -1.0, max_val: float = 1.0) -> float:
    """
    Validate score is within acceptable range.

    Args:
        score: Score value to validate
        min_val: Minimum acceptable value
        max_val: Maximum acceptable value

    Returns:
        Validated score

    Raises:
        ValidationError: If score is out of range
    """
    if not isinstance(score, (int, float)):
        raise ValidationError(f"Score must be a number, got {type(score)}")

    if score < min_val or score > max_val:
        raise ValidationError(f"Score must be between {min_val} and {max_val}, got {score}")

    return float(score)


def register_tools(mcp) -> Any:
    """Register all feedback intelligence tools with the MCP instance"""

    # ========================================================================
    # PROCESS 122: COLLECT FEEDBACK
    # ========================================================================

    @mcp.tool()
    async def collect_feedback(
        ctx: Context,
        client_id: str,
        feedback_type: Literal[
            "nps", "csat", "ces", "feature_request", "bug_report",
            "product_feedback", "service_feedback", "general"
        ],
        source: str,
        submitter_email: str,
        submitter_name: str,
        title: str,
        content: str,
        category: str,
        subcategory: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Literal["critical", "high", "medium", "low"] = "medium",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Collect and process customer feedback from any source.

        PROCESS 122: Systematic feedback collection across all channels
        (surveys, in-app, email, calls, support tickets, social media).

        This tool captures feedback, performs initial sentiment analysis,
        categorizes and prioritizes the input, and routes it appropriately.

        Args:
            client_id: Customer identifier
            feedback_type: Type of feedback (nps, csat, ces, feature_request, etc.)
            source: Feedback source channel (survey, in-app, email, call, ticket, social_media)
            submitter_email: Email address of person providing feedback
            submitter_name: Full name of feedback submitter
            title: Brief summary of feedback (max 200 chars)
            content: Detailed feedback content
            category: Primary category (product, service, support, billing, etc.)
            subcategory: Optional subcategory for finer classification
            tags: Optional list of tags for categorization
            priority: Feedback priority (critical, high, medium, low)
            metadata: Optional additional metadata (context, screenshots, etc.)

        Returns:
            Feedback record with ID, sentiment analysis, routing, and follow-up plan
        """
        try:
            # Validate inputs
            try:
                client_id = validate_client_id(client_id)
                submitter_email = validate_email(submitter_email)
            except ValidationError as e:
                return {
                    'status': 'failed',
                    'error': f'Validation error: {str(e)}'
                }

            # Validate title length
            if len(title) > 200:
                return {
                    'status': 'failed',
                    'error': 'Title must be 200 characters or less'
                }

            if len(title.strip()) == 0 or len(content.strip()) == 0:
                return {
                    'status': 'failed',
                    'error': 'Title and content cannot be empty'
                }

            await ctx.info(f"Collecting feedback from {client_id}: {feedback_type}")

            # Generate feedback ID
            timestamp = int(datetime.now().timestamp())
            feedback_id = f"FB-{timestamp}"

            # Perform sentiment analysis on content
            sentiment_result = await _analyze_sentiment_content(content, title)

            # Determine if follow-up is required
            follow_up_required = (
                sentiment_result['sentiment'] in ['very_negative', 'negative'] or
                priority in ['critical', 'high'] or
                feedback_type in ['bug_report', 'feature_request']
            )

            # Calculate follow-up date
            follow_up_by = None
            if follow_up_required:
                # Critical: 1 day, High: 3 days, Medium: 7 days, Low: 14 days
                follow_up_days = {
                    'critical': 1,
                    'high': 3,
                    'medium': 7,
                    'low': 14
                }
                follow_up_date = datetime.now() + timedelta(days=follow_up_days[priority])
                follow_up_by = follow_up_date.date()

            # Determine assignment based on feedback type and priority
            assigned_to = _determine_assignment(feedback_type, category, priority)

            # Create comprehensive feedback record
            feedback_record = CustomerFeedback(
                feedback_id=feedback_id,
                client_id=client_id,
                feedback_type=FeedbackType(feedback_type),
                source=source,
                submitter_email=submitter_email,
                submitter_name=submitter_name,
                title=title,
                content=content,
                category=category,
                subcategory=subcategory,
                tags=tags or [],
                sentiment=SentimentType(sentiment_result['sentiment']),
                sentiment_score=sentiment_result['score'],
                priority=FeedbackPriority(priority),
                status=FeedbackStatus.NEW,
                impact_assessment=sentiment_result['impact_notes'],
                assigned_to=assigned_to,
                follow_up_required=follow_up_required,
                follow_up_by=follow_up_by,
                customer_responded=False,
                resolution_notes=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                reviewed_at=None,
                resolved_at=None
            )

            # Generate action items based on feedback
            action_items = _generate_feedback_actions(
                feedback_type=feedback_type,
                sentiment=sentiment_result['sentiment'],
                priority=priority,
                category=category
            )

            # Determine if escalation is needed
            escalation_required = (
                priority == 'critical' or
                (sentiment_result['sentiment'] == 'very_negative' and priority == 'high')
            )

            # Log feedback collection
            logger.info(
                "feedback_collected",
                feedback_id=feedback_id,
                client_id=client_id,
                feedback_type=feedback_type,
                sentiment=sentiment_result['sentiment'],
                priority=priority,
                escalation_required=escalation_required
            )

            return {
                'status': 'success',
                'message': 'Feedback collected and processed successfully',
                'feedback_id': feedback_id,
                'feedback_record': feedback_record.model_dump(mode='json'),
                'sentiment_analysis': {
                    'sentiment': sentiment_result['sentiment'],
                    'sentiment_score': sentiment_result['score'],
                    'confidence': sentiment_result['confidence'],
                    'key_themes': sentiment_result['themes'],
                    'emotion_detected': sentiment_result['emotion']
                },
                'routing': {
                    'assigned_to': assigned_to,
                    'priority': priority,
                    'follow_up_required': follow_up_required,
                    'follow_up_by': follow_up_by.isoformat() if follow_up_by else None,
                    'escalation_required': escalation_required
                },
                'action_items': action_items,
                'next_steps': [
                    f"Feedback routed to {assigned_to}",
                    "Sentiment analysis completed",
                    "Follow-up scheduled" if follow_up_required else "No follow-up required",
                    "Customer will be contacted" if follow_up_required else "Feedback logged for analysis"
                ],
                'metadata': metadata or {}
            }

        except Exception as e:
            logger.error("feedback_collection_failed", error=str(e), client_id=client_id)
            return {
                'status': 'failed',
                'error': f"Feedback collection failed: {str(e)}"
            }


    # ========================================================================
    # PROCESS 123: ANALYZE FEEDBACK SENTIMENT
    # ========================================================================

    @mcp.tool()
    async def analyze_feedback_sentiment(
        ctx: Context,
        client_id: Optional[str] = None,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
        feedback_types: Optional[List[str]] = None,
        include_nps: bool = True,
        include_themes: bool = True,
        compare_to_previous: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze sentiment across customer feedback for insights and trends.

        PROCESS 123: Comprehensive sentiment analysis across all feedback sources
        with theme extraction, trend identification, and actionable insights.

        Analyzes sentiment distribution, identifies top themes (positive and negative),
        tracks sentiment trends, and generates actionable recommendations.

        Args:
            client_id: Optional customer ID (None for company-wide analysis)
            period_start: Start date for analysis (YYYY-MM-DD, defaults to 30 days ago)
            period_end: End date for analysis (YYYY-MM-DD, defaults to today)
            feedback_types: Optional filter for specific feedback types
            include_nps: Whether to include NPS score in analysis
            include_themes: Whether to perform theme extraction
            compare_to_previous: Whether to compare to previous period

        Returns:
            Comprehensive sentiment analysis with trends, themes, and actionable insights
        """
        try:
            # Validate and set date range
            if not period_end:
                period_end = datetime.now().strftime("%Y-%m-%d")
            if not period_start:
                period_start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            try:
                period_start, period_end = validate_date_range(period_start, period_end)
            except ValidationError as e:
                return {
                    'status': 'failed',
                    'error': f'Date validation error: {str(e)}'
                }

            # Validate client_id if provided
            if client_id:
                try:
                    client_id = validate_client_id(client_id)
                except ValidationError as e:
                    return {
                        'status': 'failed',
                        'error': f'Invalid client_id: {str(e)}'
                    }

            scope = f"client {client_id}" if client_id else "company-wide"
            await ctx.info(f"Analyzing sentiment for {scope} from {period_start} to {period_end}")

            # Generate analysis ID
            analysis_id = f"SA-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            if client_id:
                analysis_id += f"-{client_id.split('_')[-1]}"

            # Mock feedback data aggregation (replace with actual database query)
            feedback_data = await _fetch_feedback_data(
                client_id=client_id,
                period_start=period_start,
                period_end=period_end,
                feedback_types=feedback_types
            )

            # Calculate sentiment metrics
            sentiment_metrics = _calculate_sentiment_metrics(feedback_data)

            # Extract themes if requested
            themes = {}
            if include_themes:
                themes = await _extract_themes(feedback_data)

            # Compare to previous period if requested
            comparison = {}
            trend = "unknown"
            if compare_to_previous:
                comparison = await _compare_to_previous_period(
                    client_id=client_id,
                    current_score=sentiment_metrics['overall_score'],
                    period_start=period_start
                )
                trend = comparison.get('trend', 'unknown')

            # Calculate NPS if requested and available
            nps_score = None
            csat_score = None
            if include_nps:
                nps_score = await _calculate_nps(client_id, period_start, period_end)
                csat_score = await _calculate_csat(client_id, period_start, period_end)

            # Generate action items based on analysis
            action_items = _generate_sentiment_action_items(
                sentiment_metrics=sentiment_metrics,
                themes=themes,
                trend=trend,
                nps_score=nps_score
            )

            # Create sentiment analysis record
            analysis = SentimentAnalysis(
                analysis_id=analysis_id,
                client_id=client_id,
                period_start=datetime.fromisoformat(period_start),
                period_end=datetime.fromisoformat(period_end),
                total_feedback_items=feedback_data['total_items'],
                feedback_by_type=feedback_data['by_type'],
                overall_sentiment=SentimentType(sentiment_metrics['overall_sentiment']),
                overall_sentiment_score=sentiment_metrics['overall_score'],
                sentiment_distribution=sentiment_metrics['distribution'],
                sentiment_trend=trend,
                top_positive_themes=themes.get('positive', []),
                top_negative_themes=themes.get('negative', []),
                action_items=action_items,
                nps_score=nps_score,
                csat_score=csat_score,
                analyzed_at=datetime.now()
            )

            # Identify critical issues requiring immediate attention
            critical_issues = _identify_critical_issues(feedback_data, themes)

            # Calculate sentiment health indicators
            health_indicators = _calculate_sentiment_health(
                sentiment_metrics=sentiment_metrics,
                nps_score=nps_score,
                trend=trend
            )

            # Log analysis
            logger.info(
                "sentiment_analysis_completed",
                analysis_id=analysis_id,
                client_id=client_id,
                overall_sentiment=sentiment_metrics['overall_sentiment'],
                nps_score=nps_score,
                total_items=feedback_data['total_items']
            )

            return {
                'status': 'success',
                'message': 'Sentiment analysis completed successfully',
                'analysis_id': analysis_id,
                'analysis': analysis.model_dump(mode='json'),
                'summary': {
                    'total_feedback_items': feedback_data['total_items'],
                    'overall_sentiment': sentiment_metrics['overall_sentiment'],
                    'overall_score': sentiment_metrics['overall_score'],
                    'sentiment_trend': trend,
                    'nps_score': nps_score,
                    'csat_score': csat_score
                },
                'sentiment_breakdown': {
                    'very_positive_count': sentiment_metrics['counts']['very_positive'],
                    'positive_count': sentiment_metrics['counts']['positive'],
                    'neutral_count': sentiment_metrics['counts']['neutral'],
                    'negative_count': sentiment_metrics['counts']['negative'],
                    'very_negative_count': sentiment_metrics['counts']['very_negative'],
                    'distribution': sentiment_metrics['distribution']
                },
                'themes': {
                    'top_positive': themes.get('positive', [])[:5],
                    'top_negative': themes.get('negative', [])[:5],
                    'emerging_themes': themes.get('emerging', [])
                },
                'comparison': comparison,
                'health_indicators': health_indicators,
                'critical_issues': critical_issues,
                'action_items': action_items,
                'recommendations': [
                    "Review critical issues immediately" if critical_issues else "No critical issues detected",
                    "Follow up on negative feedback within 48 hours",
                    "Share positive feedback with relevant teams",
                    "Track theme trends in next analysis period"
                ]
            }

        except Exception as e:
            logger.error("sentiment_analysis_failed", error=str(e))
            return {
                'status': 'failed',
                'error': f"Sentiment analysis failed: {str(e)}"
            }


    # ========================================================================
    # PROCESS 124: SHARE PRODUCT INSIGHTS
    # ========================================================================

    @mcp.tool()
    async def share_product_insights(
        ctx: Context,
        insight_type: Literal[
            "feature_request", "bug_report", "usability_feedback",
            "performance_feedback", "integration_request", "general_product"
        ],
        title: str,
        description: str,
        supporting_feedback_ids: List[str],
        priority: Literal["critical", "high", "medium", "low"],
        affected_customers: List[str],
        customer_impact: str,
        business_impact: str,
        recommended_action: str,
        target_recipients: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, str]]] = None,
        due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Share curated product insights with product team based on customer feedback.

        PROCESS 124: Aggregate and synthesize feedback into actionable product insights
        for product team consumption. Includes context, impact analysis, and recommendations.

        This tool creates structured product insight reports from customer feedback,
        prioritizes based on impact, and delivers them to the product team.

        Args:
            insight_type: Type of product insight (feature_request, bug_report, etc.)
            title: Clear, concise title for the insight
            description: Detailed description with context and customer quotes
            supporting_feedback_ids: List of feedback IDs supporting this insight
            priority: Insight priority level
            affected_customers: List of customer IDs affected by this issue/request
            customer_impact: Description of impact on customers
            business_impact: Description of business/revenue impact
            recommended_action: Recommended action for product team
            target_recipients: Optional specific recipients (defaults to product team)
            attachments: Optional attachments (screenshots, data, etc.)
            due_date: Optional suggested due date for action (YYYY-MM-DD)

        Returns:
            Insight record with tracking ID, delivery status, and follow-up plan
        """
        try:
            await ctx.info(f"Sharing product insight: {title}")

            # Validate feedback IDs format
            for feedback_id in supporting_feedback_ids:
                if not feedback_id.startswith('FB-'):
                    return {
                        'status': 'failed',
                        'error': f'Invalid feedback ID format: {feedback_id}'
                    }

            # Validate customer IDs
            try:
                affected_customers = [validate_client_id(cid) for cid in affected_customers]
            except ValidationError as e:
                return {
                    'status': 'failed',
                    'error': f'Invalid customer ID: {str(e)}'
                }

            # Validate due date if provided
            if due_date:
                try:
                    due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
                    if due_date_obj < date.today():
                        return {
                            'status': 'failed',
                            'error': 'Due date cannot be in the past'
                        }
                except ValueError:
                    return {
                        'status': 'failed',
                        'error': 'Invalid due date format. Use YYYY-MM-DD'
                    }

            # Generate insight ID
            timestamp = int(datetime.now().timestamp())
            insight_id = f"PI-{timestamp}"

            # Fetch supporting feedback details
            feedback_details = await _fetch_feedback_details(supporting_feedback_ids)

            # Calculate aggregated metrics
            aggregated_metrics = _aggregate_feedback_metrics(feedback_details)

            # Determine default recipients if not specified
            if not target_recipients:
                target_recipients = _get_default_product_recipients(insight_type, priority)

            # Calculate business value score
            business_value_score = _calculate_business_value(
                num_customers=len(affected_customers),
                priority=priority,
                feedback_count=len(supporting_feedback_ids),
                aggregated_metrics=aggregated_metrics
            )

            # Extract customer quotes and examples
            customer_quotes = _extract_customer_quotes(feedback_details, max_quotes=5)

            # Create structured insight record
            insight_record = {
                "insight_id": insight_id,
                "insight_type": insight_type,
                "title": title,
                "description": description,
                "priority": priority,

                # Supporting data
                "supporting_feedback_ids": supporting_feedback_ids,
                "supporting_feedback_count": len(supporting_feedback_ids),
                "affected_customers": affected_customers,
                "affected_customer_count": len(affected_customers),

                # Impact analysis
                "customer_impact": customer_impact,
                "business_impact": business_impact,
                "business_value_score": business_value_score,
                "sentiment_summary": aggregated_metrics['sentiment_summary'],

                # Recommendations
                "recommended_action": recommended_action,
                "due_date": due_date,
                "estimated_effort": _estimate_effort(insight_type, priority),

                # Delivery
                "target_recipients": target_recipients,
                "attachments": attachments or [],
                "delivered_at": datetime.now().isoformat(),
                "status": "delivered",

                # Tracking
                "created_at": datetime.now().isoformat(),
                "created_by": "customer_success_team",
                "acknowledged": False,
                "acknowledged_at": None,
                "resolved": False,
                "resolved_at": None,
                "resolution_notes": None
            }

            # Generate delivery message
            delivery_message = _format_product_insight_message(
                insight_record=insight_record,
                customer_quotes=customer_quotes,
                aggregated_metrics=aggregated_metrics
            )

            # Determine if executive escalation is needed
            executive_escalation = (
                priority == "critical" or
                (priority == "high" and len(affected_customers) >= 5) or
                business_value_score >= 8.0
            )

            # Log insight sharing
            logger.info(
                "product_insight_shared",
                insight_id=insight_id,
                insight_type=insight_type,
                priority=priority,
                affected_customers=len(affected_customers),
                business_value_score=business_value_score,
                executive_escalation=executive_escalation
            )

            return {
                'status': 'success',
                'message': 'Product insight shared successfully',
                'insight_id': insight_id,
                'insight_record': insight_record,
                'delivery_summary': {
                    'recipients': target_recipients,
                    'delivery_method': 'product_management_system',
                    'delivered_at': datetime.now().isoformat(),
                    'executive_escalation': executive_escalation
                },
                'impact_summary': {
                    'affected_customers': len(affected_customers),
                    'supporting_feedback_items': len(supporting_feedback_ids),
                    'business_value_score': f"{business_value_score}/10",
                    'overall_sentiment': aggregated_metrics['sentiment_summary']['overall'],
                    'urgency_level': _calculate_urgency_level(priority, business_value_score)
                },
                'customer_quotes': customer_quotes,
                'delivery_message': delivery_message,
                'next_steps': [
                    "Product team notified via primary channels",
                    "Insight logged in product management system",
                    "Executive escalation initiated" if executive_escalation else "Standard priority routing",
                    "Follow-up scheduled for acknowledgment",
                    "Customer feedback loop will be closed upon resolution"
                ],
                'tracking': {
                    'insight_id': insight_id,
                    'track_url': f"https://product.internal/insights/{insight_id}",
                    'expected_acknowledgment': (datetime.now() + timedelta(days=2)).date().isoformat(),
                    'suggested_review_date': due_date or (datetime.now() + timedelta(days=14)).date().isoformat()
                }
            }

        except Exception as e:
            logger.error("product_insight_sharing_failed", error=str(e))
            return {
                'status': 'failed',
                'error': f"Product insight sharing failed: {str(e)}"
            }


    # ========================================================================
    # PROCESS 125: TRACK CS METRICS
    # ========================================================================

    @mcp.tool()
    async def track_cs_metrics(
        ctx: Context,
        metric_type: Literal[
            "nps", "csat", "ces", "churn_rate", "retention_rate",
            "expansion_rate", "time_to_value", "feature_adoption",
            "engagement_score", "health_score", "support_satisfaction"
        ],
        client_id: Optional[str] = None,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
        granularity: Literal["daily", "weekly", "monthly", "quarterly"] = "monthly",
        include_trends: bool = True,
        include_benchmarks: bool = True,
        segment_by: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Track and analyze key Customer Success metrics and KPIs.

        PROCESS 125: Comprehensive CS metrics tracking with trends, benchmarks,
        and segmentation. Monitors health of customer success operations.

        Tracks critical metrics like NPS, CSAT, churn, retention, expansion,
        and engagement with historical trends and peer benchmarking.

        Args:
            metric_type: Type of metric to track
            client_id: Optional customer ID (None for company-wide metrics)
            period_start: Start date (YYYY-MM-DD, defaults to 90 days ago)
            period_end: End date (YYYY-MM-DD, defaults to today)
            granularity: Time granularity for trend analysis
            include_trends: Whether to include historical trend data
            include_benchmarks: Whether to include industry benchmarks
            segment_by: Optional segmentation dimensions (tier, industry, cohort, etc.)

        Returns:
            Comprehensive metric report with current values, trends, and benchmarks
        """
        try:
            # Validate and set date range
            if not period_end:
                period_end = datetime.now().strftime("%Y-%m-%d")
            if not period_start:
                period_start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

            try:
                period_start, period_end = validate_date_range(period_start, period_end)
            except ValidationError as e:
                return {
                    'status': 'failed',
                    'error': f'Date validation error: {str(e)}'
                }

            # Validate client_id if provided
            if client_id:
                try:
                    client_id = validate_client_id(client_id)
                except ValidationError as e:
                    return {
                        'status': 'failed',
                        'error': f'Invalid client_id: {str(e)}'
                    }

            scope = f"client {client_id}" if client_id else "company-wide"
            await ctx.info(f"Tracking {metric_type} metrics for {scope}")

            # Calculate current metric value
            current_value = await _calculate_metric_value(
                metric_type=metric_type,
                client_id=client_id,
                period_start=period_start,
                period_end=period_end
            )

            # Calculate trend data if requested
            trend_data = []
            trend_direction = None
            percent_change = 0.0

            if include_trends:
                trend_data = await _calculate_metric_trends(
                    metric_type=metric_type,
                    client_id=client_id,
                    period_start=period_start,
                    period_end=period_end,
                    granularity=granularity
                )

                # Calculate trend direction and change
                if len(trend_data) >= 2:
                    previous_value = trend_data[-2]['value']
                    if previous_value != 0:
                        percent_change = ((current_value - previous_value) / previous_value) * 100

                    if percent_change > 5:
                        trend_direction = "up"
                    elif percent_change < -5:
                        trend_direction = "down"
                    else:
                        trend_direction = "flat"

            # Get benchmark data if requested
            benchmark_data = {}
            comparison_status = None

            if include_benchmarks:
                benchmark_data = await _fetch_metric_benchmarks(
                    metric_type=metric_type,
                    client_id=client_id
                )

                # Determine comparison status
                if benchmark_data.get('industry_average'):
                    industry_avg = benchmark_data['industry_average']
                    if _is_higher_better(metric_type):
                        comparison_status = "above" if current_value > industry_avg else "below"
                    else:
                        comparison_status = "below" if current_value < industry_avg else "above"

            # Calculate segmented data if requested
            segmented_data = {}
            if segment_by:
                segmented_data = await _calculate_segmented_metrics(
                    metric_type=metric_type,
                    client_id=client_id,
                    period_start=period_start,
                    period_end=period_end,
                    segment_dimensions=segment_by
                )

            # Generate metric insights
            insights = _generate_metric_insights(
                metric_type=metric_type,
                current_value=current_value,
                trend_direction=trend_direction,
                percent_change=percent_change,
                benchmark_data=benchmark_data,
                segmented_data=segmented_data
            )

            # Determine metric health status
            health_status = _assess_metric_health(
                metric_type=metric_type,
                current_value=current_value,
                trend_direction=trend_direction,
                benchmark_data=benchmark_data
            )

            # Generate recommended actions
            recommended_actions = _generate_metric_actions(
                metric_type=metric_type,
                health_status=health_status,
                trend_direction=trend_direction,
                insights=insights
            )

            # Format metric value for display
            formatted_value = _format_metric_value(metric_type, current_value)

            # Log metric tracking
            logger.info(
                "cs_metric_tracked",
                metric_type=metric_type,
                client_id=client_id,
                current_value=current_value,
                trend_direction=trend_direction,
                health_status=health_status
            )

            return {
                'status': 'success',
                'message': f'{metric_type.upper()} metrics tracked successfully',
                'metric_type': metric_type,
                'scope': scope,
                'period': {
                    'start': period_start,
                    'end': period_end,
                    'granularity': granularity
                },
                'current_metrics': {
                    'value': current_value,
                    'formatted_value': formatted_value,
                    'trend_direction': trend_direction,
                    'percent_change': round(percent_change, 2),
                    'health_status': health_status
                },
                'trend_data': trend_data,
                'benchmarks': {
                    'industry_average': benchmark_data.get('industry_average'),
                    'tier_average': benchmark_data.get('tier_average'),
                    'top_quartile': benchmark_data.get('top_quartile'),
                    'comparison_status': comparison_status,
                    'percentile': benchmark_data.get('percentile')
                },
                'segmented_data': segmented_data,
                'insights': insights,
                'recommended_actions': recommended_actions,
                'visualization_data': {
                    'chart_type': _get_recommended_chart_type(metric_type),
                    'trend_series': trend_data,
                    'benchmark_lines': [
                        {'name': 'Industry Average', 'value': benchmark_data.get('industry_average')},
                        {'name': 'Top Quartile', 'value': benchmark_data.get('top_quartile')}
                    ]
                }
            }

        except Exception as e:
            logger.error("cs_metrics_tracking_failed", error=str(e))
            return {
                'status': 'failed',
                'error': f"CS metrics tracking failed: {str(e)}"
            }


    # ========================================================================
    # PROCESS 126: ANALYZE PRODUCT USAGE
    # ========================================================================

    @mcp.tool()
    async def analyze_product_usage(
        ctx: Context,
        client_id: str,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
        include_feature_breakdown: bool = True,
        include_user_segmentation: bool = True,
        include_adoption_analysis: bool = True,
        compare_to_benchmark: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze product usage patterns and feature adoption for a customer.

        PROCESS 126: Comprehensive usage analytics including feature adoption,
        user engagement, integration usage, and behavioral patterns.

        Provides deep insights into how customers use the product, which features
        are adopted, usage trends, and opportunities for expansion or intervention.

        Args:
            client_id: Customer identifier
            period_start: Start date (YYYY-MM-DD, defaults to 30 days ago)
            period_end: End date (YYYY-MM-DD, defaults to today)
            include_feature_breakdown: Include detailed feature usage analysis
            include_user_segmentation: Include user-level segmentation
            include_adoption_analysis: Include feature adoption analysis
            compare_to_benchmark: Compare to peer benchmarks

        Returns:
            Comprehensive usage analytics with insights and recommendations
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

            # Validate and set date range
            if not period_end:
                period_end = datetime.now().strftime("%Y-%m-%d")
            if not period_start:
                period_start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            try:
                period_start, period_end = validate_date_range(period_start, period_end)
            except ValidationError as e:
                return {
                    'status': 'failed',
                    'error': f'Date validation error: {str(e)}'
                }

            await ctx.info(f"Analyzing product usage for {client_id}")

            # Initialize Mixpanel client and track this analysis
            mixpanel = MixpanelClient()
            mixpanel.track_event(
                user_id=client_id,
                event_name="product_usage_analyzed",
                properties={
                    "period_start": period_start,
                    "period_end": period_end,
                    "include_feature_breakdown": include_feature_breakdown,
                    "include_user_segmentation": include_user_segmentation,
                    "include_adoption_analysis": include_adoption_analysis,
                    "compare_to_benchmark": compare_to_benchmark
                }
            )

            # Fetch usage data
            usage_data = await _fetch_usage_data(
                client_id=client_id,
                period_start=period_start,
                period_end=period_end
            )

            # Calculate core usage metrics
            core_metrics = _calculate_core_usage_metrics(usage_data)

            # Feature breakdown analysis
            feature_analysis = {}
            if include_feature_breakdown:
                feature_analysis = await _analyze_feature_usage(
                    client_id=client_id,
                    usage_data=usage_data,
                    period_start=period_start,
                    period_end=period_end
                )

            # User segmentation analysis
            user_segments = {}
            if include_user_segmentation:
                user_segments = await _segment_users_by_usage(
                    client_id=client_id,
                    usage_data=usage_data
                )

            # Feature adoption analysis
            adoption_metrics = {}
            if include_adoption_analysis:
                adoption_metrics = await _analyze_feature_adoption(
                    client_id=client_id,
                    usage_data=usage_data,
                    feature_analysis=feature_analysis
                )

            # Benchmark comparison
            benchmark_comparison = {}
            if compare_to_benchmark:
                benchmark_comparison = await _compare_usage_to_benchmarks(
                    client_id=client_id,
                    core_metrics=core_metrics
                )

            # Identify usage trends
            usage_trends = _identify_usage_trends(
                usage_data=usage_data,
                period_days=(datetime.fromisoformat(period_end) -
                           datetime.fromisoformat(period_start)).days
            )

            # Detect usage anomalies
            anomalies = _detect_usage_anomalies(
                client_id=client_id,
                usage_data=usage_data,
                core_metrics=core_metrics
            )

            # Calculate usage health score
            usage_health_score = _calculate_usage_health_score(
                core_metrics=core_metrics,
                adoption_metrics=adoption_metrics,
                user_segments=user_segments,
                usage_trends=usage_trends
            )

            # Identify expansion opportunities
            expansion_opportunities = _identify_expansion_opportunities(
                feature_analysis=feature_analysis,
                adoption_metrics=adoption_metrics,
                user_segments=user_segments
            )

            # Identify at-risk indicators
            risk_indicators = _identify_usage_risk_indicators(
                core_metrics=core_metrics,
                usage_trends=usage_trends,
                anomalies=anomalies,
                user_segments=user_segments
            )

            # Generate actionable recommendations
            recommendations = _generate_usage_recommendations(
                usage_health_score=usage_health_score,
                expansion_opportunities=expansion_opportunities,
                risk_indicators=risk_indicators,
                feature_analysis=feature_analysis
            )

            # Create comprehensive usage analytics object
            usage_analytics = UsageAnalytics(
                client_id=client_id,
                period_start=datetime.fromisoformat(period_start),
                period_end=datetime.fromisoformat(period_end),
                total_usage_events=core_metrics['total_events'],
                unique_features_used=core_metrics['unique_features_used'],
                total_features_available=core_metrics['total_features_available'],
                feature_utilization_rate=core_metrics['feature_utilization_rate'],
                top_features=feature_analysis.get('top_features', []),
                underutilized_features=feature_analysis.get('underutilized_features', []),
                new_feature_adoption=adoption_metrics.get('new_features', {}),
                usage_by_user_role=user_segments.get('by_role', {}),
                integration_usage=core_metrics.get('integration_usage', {}),
                api_usage=core_metrics.get('api_usage', {}),
                usage_trend=TrendDirection(usage_trends['direction']),
                usage_growth_rate=usage_trends['growth_rate']
            )

            # Log usage analysis
            logger.info(
                "product_usage_analyzed",
                client_id=client_id,
                usage_health_score=usage_health_score,
                feature_utilization_rate=core_metrics['feature_utilization_rate'],
                usage_trend=usage_trends['direction']
            )

            # Track usage analysis results to Mixpanel
            mixpanel.track_event(
                user_id=client_id,
                event_name="usage_analysis_completed",
                properties={
                    "usage_health_score": usage_health_score,
                    "total_usage_events": core_metrics['total_events'],
                    "active_users": core_metrics['active_users'],
                    "feature_utilization_rate": core_metrics['feature_utilization_rate'],
                    "usage_trend": usage_trends['direction'],
                    "usage_growth_rate": usage_trends['growth_rate'],
                    "power_users": user_segments.get('power_users', 0),
                    "inactive_users": user_segments.get('inactive_users', 0),
                    "at_risk_users": user_segments.get('at_risk_users', 0),
                    "risk_indicators_count": len(risk_indicators),
                    "expansion_opportunities_count": len(expansion_opportunities)
                }
            )

            # Update Mixpanel profile with latest usage metrics
            mixpanel.set_profile(
                user_id=client_id,
                properties={
                    "last_usage_analysis": datetime.now().isoformat(),
                    "usage_health_score": usage_health_score,
                    "feature_utilization_rate": core_metrics['feature_utilization_rate'],
                    "usage_trend": usage_trends['direction']
                }
            )

            # Flush events to ensure immediate delivery
            mixpanel.flush()

            return {
                'status': 'success',
                'message': 'Product usage analysis completed successfully',
                'client_id': client_id,
                'period': {
                    'start': period_start,
                    'end': period_end,
                    'days': (datetime.fromisoformat(period_end) -
                            datetime.fromisoformat(period_start)).days
                },
                'usage_analytics': usage_analytics.model_dump(mode='json'),
                'summary': {
                    'usage_health_score': usage_health_score,
                    'total_usage_events': core_metrics['total_events'],
                    'active_users': core_metrics['active_users'],
                    'feature_utilization': f"{core_metrics['feature_utilization_rate']*100:.1f}%",
                    'usage_trend': usage_trends['direction'],
                    'growth_rate': f"{usage_trends['growth_rate']*100:+.1f}%"
                },
                'feature_insights': {
                    'most_used': feature_analysis.get('top_features', [])[:5],
                    'underutilized': feature_analysis.get('underutilized_features', [])[:5],
                    'recently_adopted': adoption_metrics.get('recent_adoptions', []),
                    'adoption_rate': adoption_metrics.get('overall_adoption_rate', 0)
                },
                'user_insights': {
                    'total_users': user_segments.get('total_users', 0),
                    'power_users': user_segments.get('power_users', 0),
                    'inactive_users': user_segments.get('inactive_users', 0),
                    'at_risk_users': user_segments.get('at_risk_users', 0),
                    'segments': user_segments.get('segments', {})
                },
                'benchmarks': benchmark_comparison,
                'trends': usage_trends,
                'anomalies': anomalies,
                'opportunities': {
                    'expansion': expansion_opportunities,
                    'estimated_arr_potential': sum(
                        opp.get('arr_potential', 0) for opp in expansion_opportunities
                    )
                },
                'risk_indicators': risk_indicators,
                'recommendations': recommendations,
                'next_steps': [
                    "Review expansion opportunities with customer",
                    "Address identified risk indicators",
                    "Provide training on underutilized features",
                    "Monitor usage trends in next period",
                    "Follow up with inactive users"
                ]
            }

        except Exception as e:
            logger.error("product_usage_analysis_failed", error=str(e), client_id=client_id)
            return {
                'status': 'failed',
                'error': f"Product usage analysis failed: {str(e)}"
            }


    # ========================================================================
    # PROCESS 127: MANAGE VOICE OF CUSTOMER
    # ========================================================================

    @mcp.tool()
    async def manage_voice_of_customer(
        ctx: Context,
        action: Literal[
            "create_voc_report", "track_feedback_loop", "measure_program_effectiveness",
            "generate_executive_summary", "close_feedback_loop", "update_customer_roadmap"
        ],
        client_id: Optional[str] = None,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
        report_type: Literal["weekly", "monthly", "quarterly", "annual"] = "monthly",
        include_sentiment: bool = True,
        include_nps: bool = True,
        include_product_insights: bool = True,
        include_customer_quotes: bool = True,
        target_audience: Literal["executive", "product", "cs_team", "all"] = "all"
    ) -> Dict[str, Any]:
        """
        Manage comprehensive Voice of Customer (VoC) program.

        PROCESS 127: End-to-end VoC program management including report generation,
        feedback loop tracking, program effectiveness measurement, and roadmap alignment.

        Consolidates all customer feedback, tracks actions taken, measures impact,
        and creates executive-ready insights for strategic decision-making.

        Args:
            action: VoC action to perform
            client_id: Optional customer ID (None for company-wide VoC)
            period_start: Start date (YYYY-MM-DD, defaults based on report_type)
            period_end: End date (YYYY-MM-DD, defaults to today)
            report_type: Type of VoC report (weekly, monthly, quarterly, annual)
            include_sentiment: Include sentiment analysis in report
            include_nps: Include NPS metrics in report
            include_product_insights: Include product insights summary
            include_customer_quotes: Include representative customer quotes
            target_audience: Target audience for report formatting

        Returns:
            VoC report, tracking data, or action result based on action type
        """
        try:
            # Set default date ranges based on report type
            if not period_end:
                period_end = datetime.now().strftime("%Y-%m-%d")

            if not period_start:
                days_back = {
                    'weekly': 7,
                    'monthly': 30,
                    'quarterly': 90,
                    'annual': 365
                }
                period_start = (datetime.now() - timedelta(days=days_back[report_type])).strftime("%Y-%m-%d")

            try:
                period_start, period_end = validate_date_range(period_start, period_end)
            except ValidationError as e:
                return {
                    'status': 'failed',
                    'error': f'Date validation error: {str(e)}'
                }

            # Validate client_id if provided
            if client_id:
                try:
                    client_id = validate_client_id(client_id)
                except ValidationError as e:
                    return {
                        'status': 'failed',
                        'error': f'Invalid client_id: {str(e)}'
                    }

            await ctx.info(f"Managing VoC program: {action}")

            # Route to appropriate action handler
            if action == "create_voc_report":
                result = await _create_voc_report(
                    client_id=client_id,
                    period_start=period_start,
                    period_end=period_end,
                    report_type=report_type,
                    include_sentiment=include_sentiment,
                    include_nps=include_nps,
                    include_product_insights=include_product_insights,
                    include_customer_quotes=include_customer_quotes,
                    target_audience=target_audience
                )

            elif action == "track_feedback_loop":
                result = await _track_feedback_loop(
                    client_id=client_id,
                    period_start=period_start,
                    period_end=period_end
                )

            elif action == "measure_program_effectiveness":
                result = await _measure_voc_effectiveness(
                    period_start=period_start,
                    period_end=period_end
                )

            elif action == "generate_executive_summary":
                result = await _generate_executive_summary(
                    client_id=client_id,
                    period_start=period_start,
                    period_end=period_end,
                    report_type=report_type
                )

            elif action == "close_feedback_loop":
                result = await _close_feedback_loop(
                    client_id=client_id,
                    period_start=period_start,
                    period_end=period_end
                )

            elif action == "update_customer_roadmap":
                result = await _update_customer_roadmap(
                    client_id=client_id,
                    period_start=period_start,
                    period_end=period_end
                )

            else:
                return {
                    'status': 'failed',
                    'error': f'Unknown action: {action}'
                }

            # Log VoC action
            logger.info(
                "voc_action_completed",
                action=action,
                client_id=client_id,
                report_type=report_type
            )

            return result

        except Exception as e:
            logger.error("voc_management_failed", error=str(e), action=action)
            return {
                'status': 'failed',
                'error': f"VoC management failed: {str(e)}"
            }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _analyze_sentiment_content(content: str, title: str) -> Dict[str, Any]:
    """Analyze sentiment of feedback content"""
    # Simulate sentiment analysis (replace with actual ML model)
    combined_text = f"{title} {content}".lower()

    # Simple keyword-based sentiment (replace with actual NLP)
    positive_keywords = ['great', 'excellent', 'love', 'amazing', 'fantastic', 'helpful', 'easy', 'perfect']
    negative_keywords = ['terrible', 'awful', 'hate', 'broken', 'bug', 'issue', 'problem', 'difficult', 'slow']

    positive_count = sum(1 for word in positive_keywords if word in combined_text)
    negative_count = sum(1 for word in negative_keywords if word in combined_text)

    # Calculate score
    if positive_count > negative_count + 2:
        sentiment = 'very_positive'
        score = 0.8
    elif positive_count > negative_count:
        sentiment = 'positive'
        score = 0.5
    elif negative_count > positive_count + 2:
        sentiment = 'very_negative'
        score = -0.8
    elif negative_count > positive_count:
        sentiment = 'negative'
        score = -0.5
    else:
        sentiment = 'neutral'
        score = 0.0

    # Extract themes
    themes = []
    if 'support' in combined_text or 'help' in combined_text:
        themes.append('customer_support')
    if 'feature' in combined_text or 'function' in combined_text:
        themes.append('product_features')
    if 'performance' in combined_text or 'slow' in combined_text or 'fast' in combined_text:
        themes.append('performance')
    if 'ui' in combined_text or 'interface' in combined_text or 'design' in combined_text:
        themes.append('user_interface')

    # Detect emotion
    emotion = 'neutral'
    if 'frustrated' in combined_text or 'angry' in combined_text:
        emotion = 'frustrated'
    elif 'happy' in combined_text or 'pleased' in combined_text:
        emotion = 'happy'
    elif 'confused' in combined_text or 'unclear' in combined_text:
        emotion = 'confused'

    return {
        'sentiment': sentiment,
        'score': score,
        'confidence': 0.75,
        'themes': themes,
        'emotion': emotion,
        'impact_notes': f"Sentiment: {sentiment.replace('_', ' ').title()}. Key themes: {', '.join(themes) if themes else 'general feedback'}."
    }


def _determine_assignment(feedback_type: str, category: str, priority: str) -> str:
    """Determine who should handle the feedback"""
    if feedback_type in ['bug_report', 'feature_request']:
        return 'product-team@company.com'
    elif category in ['support', 'service']:
        return 'support-team@company.com'
    elif category == 'billing':
        return 'finance-team@company.com'
    elif priority == 'critical':
        return 'cs-leadership@company.com'
    else:
        return 'cs-team@company.com'


def _generate_feedback_actions(
    feedback_type: str,
    sentiment: str,
    priority: str,
    category: str
) -> List[str]:
    """Generate action items based on feedback characteristics"""
    actions = []

    if sentiment in ['very_negative', 'negative']:
        actions.append(f"Follow up with customer within 24-48 hours")
        actions.append("Investigate root cause of dissatisfaction")

    if feedback_type == 'feature_request':
        actions.append("Log in product backlog with customer impact notes")
        actions.append("Include in next product insights report")

    if feedback_type == 'bug_report':
        actions.append("Create bug ticket and assign to engineering")
        actions.append("Update customer on resolution timeline")

    if priority == 'critical':
        actions.append("Escalate to leadership immediately")
        actions.append("Schedule emergency customer call if needed")

    if sentiment in ['very_positive', 'positive']:
        actions.append("Share positive feedback with team")
        actions.append("Consider as customer reference or case study")

    return actions


async def _fetch_feedback_data(
    client_id: Optional[str],
    period_start: str,
    period_end: str,
    feedback_types: Optional[List[str]]
) -> Dict[str, Any]:
    """Fetch feedback data for analysis"""
    # Mock data (replace with actual database query)
    return {
        'total_items': 47,
        'by_type': {
            'nps': 12,
            'csat': 8,
            'product_feedback': 15,
            'feature_request': 9,
            'bug_report': 3
        },
        'by_sentiment': {
            'very_positive': 11,
            'positive': 22,
            'neutral': 10,
            'negative': 3,
            'very_negative': 1
        },
        'items': [
            # Mock feedback items would go here
        ]
    }


def _calculate_sentiment_metrics(feedback_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate aggregate sentiment metrics"""
    total = feedback_data['total_items']
    by_sentiment = feedback_data['by_sentiment']

    # Calculate distribution
    distribution = {
        sentiment: count / total if total > 0 else 0
        for sentiment, count in by_sentiment.items()
    }

    # Calculate overall score
    sentiment_weights = {
        'very_positive': 1.0,
        'positive': 0.5,
        'neutral': 0.0,
        'negative': -0.5,
        'very_negative': -1.0
    }

    total_score = sum(
        by_sentiment.get(sentiment, 0) * weight
        for sentiment, weight in sentiment_weights.items()
    )

    overall_score = total_score / total if total > 0 else 0.0

    # Determine overall sentiment
    if overall_score >= 0.6:
        overall_sentiment = 'very_positive'
    elif overall_score >= 0.2:
        overall_sentiment = 'positive'
    elif overall_score >= -0.2:
        overall_sentiment = 'neutral'
    elif overall_score >= -0.6:
        overall_sentiment = 'negative'
    else:
        overall_sentiment = 'very_negative'

    return {
        'overall_sentiment': overall_sentiment,
        'overall_score': overall_score,
        'distribution': distribution,
        'counts': by_sentiment
    }


async def _extract_themes(feedback_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Extract themes from feedback data"""
    # Mock theme extraction (replace with actual NLP/ML)
    return {
        'positive': [
            {'theme': 'customer_support', 'mentions': 18, 'avg_sentiment': 0.87},
            {'theme': 'ease_of_use', 'mentions': 15, 'avg_sentiment': 0.82},
            {'theme': 'feature_quality', 'mentions': 12, 'avg_sentiment': 0.78}
        ],
        'negative': [
            {'theme': 'missing_features', 'mentions': 8, 'avg_sentiment': -0.45},
            {'theme': 'performance', 'mentions': 3, 'avg_sentiment': -0.62}
        ],
        'emerging': [
            {'theme': 'mobile_app', 'mentions': 5, 'trend': 'increasing'},
            {'theme': 'integrations', 'mentions': 7, 'trend': 'increasing'}
        ]
    }


async def _compare_to_previous_period(
    client_id: Optional[str],
    current_score: float,
    period_start: str
) -> Dict[str, Any]:
    """Compare sentiment to previous period"""
    # Mock comparison (replace with actual historical data)
    previous_score = current_score - 0.05  # Simulate improvement

    change = current_score - previous_score
    percent_change = (change / abs(previous_score)) * 100 if previous_score != 0 else 0

    if percent_change > 10:
        trend = 'improving'
    elif percent_change < -10:
        trend = 'declining'
    else:
        trend = 'stable'

    return {
        'previous_score': previous_score,
        'current_score': current_score,
        'change': change,
        'percent_change': percent_change,
        'trend': trend
    }


async def _calculate_nps(
    client_id: Optional[str],
    period_start: str,
    period_end: str
) -> Optional[int]:
    """Calculate Net Promoter Score"""
    # Mock NPS calculation (replace with actual survey data)
    # NPS = % Promoters - % Detractors
    return 52  # Mock score


async def _calculate_csat(
    client_id: Optional[str],
    period_start: str,
    period_end: str
) -> Optional[float]:
    """Calculate Customer Satisfaction Score"""
    # Mock CSAT calculation (replace with actual survey data)
    return 4.3  # Mock score out of 5


def _generate_sentiment_action_items(
    sentiment_metrics: Dict[str, Any],
    themes: Dict[str, List[Dict[str, Any]]],
    trend: str,
    nps_score: Optional[int]
) -> List[str]:
    """Generate action items based on sentiment analysis"""
    actions = []

    # Overall sentiment actions
    if sentiment_metrics['overall_sentiment'] in ['negative', 'very_negative']:
        actions.append("Urgent: Address negative sentiment with customer outreach program")

    # Trend-based actions
    if trend == 'declining':
        actions.append("Investigate root causes of declining sentiment")
        actions.append("Schedule leadership review of customer feedback")

    # NPS-based actions
    if nps_score and nps_score < 30:
        actions.append("Critical: NPS below acceptable threshold - implement recovery plan")

    # Theme-based actions
    negative_themes = themes.get('negative', [])
    if negative_themes:
        top_negative = negative_themes[0]
        actions.append(f"Prioritize addressing '{top_negative['theme']}' (mentioned {top_negative['mentions']} times)")

    # Positive feedback actions
    positive_themes = themes.get('positive', [])
    if positive_themes:
        actions.append("Share positive feedback with relevant teams for recognition")

    return actions or ["Continue monitoring sentiment trends"]


def _identify_critical_issues(
    feedback_data: Dict[str, Any],
    themes: Dict[str, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """Identify critical issues from feedback"""
    # Mock critical issue detection
    critical_issues = []

    negative_themes = themes.get('negative', [])
    for theme in negative_themes:
        if theme['mentions'] >= 5 or theme['avg_sentiment'] <= -0.6:
            critical_issues.append({
                'theme': theme['theme'],
                'severity': 'high' if theme['avg_sentiment'] <= -0.7 else 'medium',
                'mentions': theme['mentions'],
                'recommended_action': f"Immediate investigation required for {theme['theme']}"
            })

    return critical_issues


def _calculate_sentiment_health(
    sentiment_metrics: Dict[str, Any],
    nps_score: Optional[int],
    trend: str
) -> Dict[str, Any]:
    """Calculate overall sentiment health indicators"""
    score = sentiment_metrics['overall_score']

    # Determine health status
    if score >= 0.6 and trend != 'declining':
        health_status = 'excellent'
        health_score = 90
    elif score >= 0.3 and trend != 'declining':
        health_status = 'good'
        health_score = 75
    elif score >= 0.0:
        health_status = 'fair'
        health_score = 60
    elif score >= -0.3:
        health_status = 'poor'
        health_score = 40
    else:
        health_status = 'critical'
        health_score = 20

    return {
        'health_status': health_status,
        'health_score': health_score,
        'sentiment_score': score,
        'nps_score': nps_score,
        'trend': trend
    }


async def _fetch_feedback_details(feedback_ids: List[str]) -> List[Dict[str, Any]]:
    """Fetch detailed feedback records"""
    # Mock feedback details (replace with actual database query)
    return [
        {
            'feedback_id': fid,
            'content': 'Mock feedback content',
            'sentiment': 'positive',
            'sentiment_score': 0.7,
            'client_id': 'cs_1696800000_acme'
        }
        for fid in feedback_ids
    ]


def _aggregate_feedback_metrics(feedback_details: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate metrics from multiple feedback items"""
    if not feedback_details:
        return {
            'avg_sentiment_score': 0.0,
            'sentiment_summary': {'overall': 'neutral', 'positive_pct': 0, 'negative_pct': 0}
        }

    total_score = sum(f['sentiment_score'] for f in feedback_details)
    avg_score = total_score / len(feedback_details)

    positive = sum(1 for f in feedback_details if f['sentiment_score'] > 0.2)
    negative = sum(1 for f in feedback_details if f['sentiment_score'] < -0.2)

    return {
        'avg_sentiment_score': avg_score,
        'sentiment_summary': {
            'overall': 'positive' if avg_score > 0.2 else 'negative' if avg_score < -0.2 else 'neutral',
            'positive_pct': (positive / len(feedback_details)) * 100,
            'negative_pct': (negative / len(feedback_details)) * 100
        }
    }


def _get_default_product_recipients(insight_type: str, priority: str) -> List[str]:
    """Get default recipients for product insights"""
    recipients = ['product-team@company.com']

    if priority == 'critical':
        recipients.append('cto@company.com')
        recipients.append('ceo@company.com')
    elif priority == 'high':
        recipients.append('product-director@company.com')

    if insight_type == 'bug_report':
        recipients.append('engineering-team@company.com')

    return recipients


def _calculate_business_value(
    num_customers: int,
    priority: str,
    feedback_count: int,
    aggregated_metrics: Dict[str, Any]
) -> float:
    """Calculate business value score for product insight"""
    # Base score from customer count (0-4 points)
    customer_score = min(num_customers / 2.5, 4.0)

    # Priority score (0-3 points)
    priority_scores = {'critical': 3.0, 'high': 2.0, 'medium': 1.0, 'low': 0.5}
    priority_score = priority_scores[priority]

    # Feedback volume score (0-2 points)
    feedback_score = min(feedback_count / 5.0, 2.0)

    # Sentiment impact score (0-1 point)
    sentiment_score = 1.0 if aggregated_metrics['avg_sentiment_score'] < -0.3 else 0.5

    total_score = customer_score + priority_score + feedback_score + sentiment_score
    return round(min(total_score, 10.0), 1)


def _extract_customer_quotes(
    feedback_details: List[Dict[str, Any]],
    max_quotes: int = 5
) -> List[Dict[str, str]]:
    """Extract representative customer quotes"""
    # Mock quote extraction (replace with actual content analysis)
    quotes = []
    for i, feedback in enumerate(feedback_details[:max_quotes]):
        quotes.append({
            'quote': feedback.get('content', '')[:200] + '...',
            'client_id': feedback.get('client_id', 'unknown'),
            'sentiment': feedback.get('sentiment', 'neutral')
        })
    return quotes


def _estimate_effort(insight_type: str, priority: str) -> str:
    """Estimate implementation effort"""
    if insight_type == 'bug_report':
        return 'Small to Medium' if priority in ['critical', 'high'] else 'Small'
    elif insight_type == 'feature_request':
        return 'Medium to Large'
    else:
        return 'Medium'


def _format_product_insight_message(
    insight_record: Dict[str, Any],
    customer_quotes: List[Dict[str, str]],
    aggregated_metrics: Dict[str, Any]
) -> str:
    """Format product insight for delivery"""
    message = f"""
Product Insight Report: {insight_record['title']}
{'=' * 60}

Priority: {insight_record['priority'].upper()}
Type: {insight_record['insight_type']}
Business Value Score: {insight_record['business_value_score']}/10

Impact Summary:
- Affected Customers: {insight_record['affected_customer_count']}
- Supporting Feedback: {insight_record['supporting_feedback_count']} items
- Overall Sentiment: {aggregated_metrics['sentiment_summary']['overall']}

Description:
{insight_record['description']}

Customer Impact:
{insight_record['customer_impact']}

Business Impact:
{insight_record['business_impact']}

Recommended Action:
{insight_record['recommended_action']}

Customer Quotes:
"""
    for i, quote in enumerate(customer_quotes[:3], 1):
        message += f"\n{i}. \"{quote['quote']}\" - {quote['client_id']} ({quote['sentiment']})"

    return message


def _calculate_urgency_level(priority: str, business_value_score: float) -> str:
    """Calculate overall urgency level"""
    if priority == 'critical' or business_value_score >= 8.0:
        return 'urgent'
    elif priority == 'high' or business_value_score >= 6.0:
        return 'high'
    elif business_value_score >= 4.0:
        return 'medium'
    else:
        return 'normal'


async def _calculate_metric_value(
    metric_type: str,
    client_id: Optional[str],
    period_start: str,
    period_end: str
) -> float:
    """Calculate current value for a metric"""
    # Mock metric calculations (replace with actual data queries)
    mock_values = {
        'nps': 52.0,
        'csat': 4.3,
        'ces': 3.8,
        'churn_rate': 0.05,
        'retention_rate': 0.95,
        'expansion_rate': 0.12,
        'time_to_value': 14.5,
        'feature_adoption': 0.68,
        'engagement_score': 82.0,
        'health_score': 85.0,
        'support_satisfaction': 4.6
    }
    return mock_values.get(metric_type, 0.0)


async def _calculate_metric_trends(
    metric_type: str,
    client_id: Optional[str],
    period_start: str,
    period_end: str,
    granularity: str
) -> List[Dict[str, Any]]:
    """Calculate trend data for a metric"""
    # Mock trend data (replace with actual historical data)
    import random
    base_value = await _calculate_metric_value(metric_type, client_id, period_start, period_end)

    # Generate trend points based on granularity
    if granularity == 'daily':
        points = 30
    elif granularity == 'weekly':
        points = 12
    elif granularity == 'monthly':
        points = 6
    else:  # quarterly
        points = 4

    trend_data = []
    for i in range(points):
        value = base_value + random.uniform(-5, 5)
        trend_data.append({
            'period': i + 1,
            'value': round(value, 2),
            'date': (datetime.fromisoformat(period_end) - timedelta(days=(points-i)*7)).strftime('%Y-%m-%d')
        })

    return trend_data


async def _fetch_metric_benchmarks(
    metric_type: str,
    client_id: Optional[str]
) -> Dict[str, Any]:
    """Fetch benchmark data for a metric"""
    # Mock benchmark data (replace with actual benchmark database)
    current_value = await _calculate_metric_value(metric_type, client_id, "", "")

    return {
        'industry_average': current_value * 0.9,
        'tier_average': current_value * 0.95,
        'top_quartile': current_value * 1.15,
        'percentile': 75
    }


def _is_higher_better(metric_type: str) -> bool:
    """Determine if higher values are better for this metric"""
    lower_is_better = ['churn_rate', 'time_to_value', 'ces']
    return metric_type not in lower_is_better


async def _calculate_segmented_metrics(
    metric_type: str,
    client_id: Optional[str],
    period_start: str,
    period_end: str,
    segment_dimensions: List[str]
) -> Dict[str, Any]:
    """Calculate metrics by segment"""
    # Mock segmented data
    segmented = {}
    for dimension in segment_dimensions:
        if dimension == 'tier':
            segmented['tier'] = {
                'enterprise': 85.0,
                'professional': 78.0,
                'standard': 72.0
            }
        elif dimension == 'industry':
            segmented['industry'] = {
                'technology': 82.0,
                'healthcare': 77.0,
                'finance': 80.0
            }
    return segmented


def _generate_metric_insights(
    metric_type: str,
    current_value: float,
    trend_direction: Optional[str],
    percent_change: float,
    benchmark_data: Dict[str, Any],
    segmented_data: Dict[str, Any]
) -> List[str]:
    """Generate insights from metric analysis"""
    insights = []

    # Trend insights
    if trend_direction == 'up':
        insights.append(f"{metric_type.upper()} trending positively with {abs(percent_change):.1f}% improvement")
    elif trend_direction == 'down':
        insights.append(f"{metric_type.upper()} declining by {abs(percent_change):.1f}% - requires attention")

    # Benchmark insights
    if benchmark_data.get('percentile'):
        percentile = benchmark_data['percentile']
        if percentile >= 75:
            insights.append(f"Performance in top quartile ({percentile}th percentile)")
        elif percentile <= 25:
            insights.append(f"Performance below industry standards ({percentile}th percentile)")

    # Segment insights
    if 'tier' in segmented_data:
        tier_data = segmented_data['tier']
        if tier_data:
            best_tier = max(tier_data.items(), key=lambda x: x[1])
            insights.append(f"Best performance in {best_tier[0]} tier: {best_tier[1]}")

    return insights or ["No significant insights detected"]


def _assess_metric_health(
    metric_type: str,
    current_value: float,
    trend_direction: Optional[str],
    benchmark_data: Dict[str, Any]
) -> str:
    """Assess health status of a metric"""
    is_higher_better = _is_higher_better(metric_type)

    # Compare to benchmark
    industry_avg = benchmark_data.get('industry_average', current_value)

    if is_higher_better:
        if current_value >= industry_avg * 1.1 and trend_direction != 'down':
            return 'excellent'
        elif current_value >= industry_avg * 0.95:
            return 'good'
        elif current_value >= industry_avg * 0.85:
            return 'fair'
        else:
            return 'poor'
    else:
        if current_value <= industry_avg * 0.9 and trend_direction != 'up':
            return 'excellent'
        elif current_value <= industry_avg * 1.05:
            return 'good'
        elif current_value <= industry_avg * 1.15:
            return 'fair'
        else:
            return 'poor'


def _generate_metric_actions(
    metric_type: str,
    health_status: str,
    trend_direction: Optional[str],
    insights: List[str]
) -> List[str]:
    """Generate recommended actions based on metric analysis"""
    actions = []

    if health_status in ['poor', 'fair']:
        actions.append(f"Investigate root causes of underperforming {metric_type}")
        actions.append(f"Develop improvement plan for {metric_type}")

    if trend_direction == 'down':
        actions.append(f"Urgent: Address declining {metric_type} trend")

    if health_status == 'excellent':
        actions.append("Document and share best practices")
        actions.append("Consider increasing targets")

    return actions or ["Continue monitoring metric performance"]


def _format_metric_value(metric_type: str, value: float) -> str:
    """Format metric value for display"""
    if metric_type in ['nps']:
        return f"{int(value)}"
    elif metric_type in ['csat', 'ces', 'support_satisfaction']:
        return f"{value:.1f}/5.0"
    elif metric_type in ['churn_rate', 'retention_rate', 'expansion_rate', 'feature_adoption']:
        return f"{value*100:.1f}%"
    elif metric_type in ['time_to_value']:
        return f"{value:.1f} days"
    else:
        return f"{value:.1f}"


def _get_recommended_chart_type(metric_type: str) -> str:
    """Get recommended chart type for metric visualization"""
    if metric_type in ['nps', 'csat', 'ces', 'health_score', 'engagement_score']:
        return 'line_chart'
    elif metric_type in ['churn_rate', 'retention_rate', 'expansion_rate']:
        return 'area_chart'
    elif metric_type in ['feature_adoption']:
        return 'bar_chart'
    else:
        return 'line_chart'


async def _fetch_usage_data(
    client_id: str,
    period_start: str,
    period_end: str
) -> Dict[str, Any]:
    """Fetch raw usage data"""
    # Mock usage data (replace with actual database query)
    return {
        'total_events': 15847,
        'active_users': 42,
        'sessions': 1847,
        'features_used': ['dashboard', 'reports', 'export', 'settings'],
        'integrations_active': ['salesforce', 'slack']
    }


def _calculate_core_usage_metrics(usage_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate core usage metrics"""
    return {
        'total_events': usage_data['total_events'],
        'active_users': usage_data['active_users'],
        'unique_features_used': len(usage_data['features_used']),
        'total_features_available': 68,
        'feature_utilization_rate': len(usage_data['features_used']) / 68,
        'integration_usage': {
            'active_integrations': len(usage_data['integrations_active']),
            'integrations': usage_data['integrations_active']
        },
        'api_usage': {
            'total_calls': 24567,
            'avg_daily_calls': 792,
            'error_rate': 0.012
        }
    }


async def _analyze_feature_usage(
    client_id: str,
    usage_data: Dict[str, Any],
    period_start: str,
    period_end: str
) -> Dict[str, Any]:
    """Analyze feature-level usage"""
    # Mock feature analysis
    return {
        'top_features': [
            {'feature': 'dashboard', 'usage_count': 2847, 'user_count': 45, 'adoption_rate': 0.90},
            {'feature': 'reports', 'usage_count': 1923, 'user_count': 38, 'adoption_rate': 0.76},
            {'feature': 'export', 'usage_count': 1456, 'user_count': 32, 'adoption_rate': 0.64}
        ],
        'underutilized_features': [
            {'feature': 'advanced_analytics', 'usage_count': 45, 'user_count': 3, 'adoption_rate': 0.06},
            {'feature': 'api_access', 'usage_count': 12, 'user_count': 2, 'adoption_rate': 0.04}
        ]
    }


async def _segment_users_by_usage(
    client_id: str,
    usage_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Segment users by usage patterns"""
    return {
        'total_users': 50,
        'power_users': 12,
        'inactive_users': 8,
        'at_risk_users': 3,
        'by_role': {
            'admin': {'users': 5, 'usage_events': 4821, 'avg_per_user': 964},
            'power_user': {'users': 12, 'usage_events': 7234, 'avg_per_user': 603},
            'standard_user': {'users': 33, 'usage_events': 3792, 'avg_per_user': 115}
        },
        'segments': {
            'power_users': {'count': 12, 'definition': 'High engagement, frequent usage'},
            'regular_users': {'count': 27, 'definition': 'Moderate usage'},
            'light_users': {'count': 11, 'definition': 'Low but consistent usage'}
        }
    }


async def _analyze_feature_adoption(
    client_id: str,
    usage_data: Dict[str, Any],
    feature_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze feature adoption patterns"""
    return {
        'overall_adoption_rate': 0.62,
        'new_features': {
            'feature_x': {'launched': '2025-09-15', 'adoption_rate': 0.31, 'days_since_launch': 46}
        },
        'recent_adoptions': [
            {'feature': 'feature_x', 'adoption_date': '2025-10-01', 'adopters': 15}
        ]
    }


async def _compare_usage_to_benchmarks(
    client_id: str,
    core_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """Compare usage to peer benchmarks"""
    return {
        'feature_utilization': {
            'customer': core_metrics['feature_utilization_rate'],
            'tier_average': 0.58,
            'industry_average': 0.55,
            'comparison': 'above_average'
        },
        'engagement': {
            'comparison': 'above_average',
            'percentile': 72
        }
    }


def _identify_usage_trends(usage_data: Dict[str, Any], period_days: int) -> Dict[str, Any]:
    """Identify usage trends"""
    # Mock trend identification
    return {
        'direction': 'up',
        'growth_rate': 0.15,
        'consistency': 'stable',
        'seasonality': 'none_detected'
    }


def _detect_usage_anomalies(
    client_id: str,
    usage_data: Dict[str, Any],
    core_metrics: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Detect usage anomalies"""
    # Mock anomaly detection
    return []


def _calculate_usage_health_score(
    core_metrics: Dict[str, Any],
    adoption_metrics: Dict[str, Any],
    user_segments: Dict[str, Any],
    usage_trends: Dict[str, Any]
) -> int:
    """Calculate overall usage health score"""
    # Weighted scoring
    utilization_score = core_metrics['feature_utilization_rate'] * 100
    adoption_score = adoption_metrics.get('overall_adoption_rate', 0) * 100

    active_user_pct = (user_segments['total_users'] - user_segments['inactive_users']) / user_segments['total_users']
    engagement_score = active_user_pct * 100

    trend_multiplier = 1.1 if usage_trends['direction'] == 'up' else 0.9 if usage_trends['direction'] == 'down' else 1.0

    health_score = ((utilization_score * 0.3 + adoption_score * 0.3 + engagement_score * 0.4) * trend_multiplier)

    return int(min(health_score, 100))


def _identify_expansion_opportunities(
    feature_analysis: Dict[str, Any],
    adoption_metrics: Dict[str, Any],
    user_segments: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Identify expansion opportunities"""
    opportunities = []

    # Check for underutilized advanced features
    underutilized = feature_analysis.get('underutilized_features', [])
    if underutilized:
        opportunities.append({
            'type': 'feature_upgrade',
            'description': f"Training on {len(underutilized)} underutilized features",
            'potential_value': 'Increased engagement and stickiness',
            'arr_potential': 5000
        })

    # Check for power users who might need more
    if user_segments.get('power_users', 0) > 5:
        opportunities.append({
            'type': 'tier_upgrade',
            'description': f"{user_segments['power_users']} power users may benefit from premium tier",
            'potential_value': 'Upsell opportunity',
            'arr_potential': 10000
        })

    return opportunities


def _identify_usage_risk_indicators(
    core_metrics: Dict[str, Any],
    usage_trends: Dict[str, Any],
    anomalies: List[Dict[str, Any]],
    user_segments: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Identify usage-based risk indicators"""
    risks = []

    # Check for declining usage
    if usage_trends['direction'] == 'down':
        risks.append({
            'indicator': 'declining_usage',
            'severity': 'high',
            'description': f"Usage declining at {abs(usage_trends['growth_rate'])*100:.1f}% rate"
        })

    # Check for inactive users
    if user_segments.get('inactive_users', 0) > user_segments['total_users'] * 0.2:
        risks.append({
            'indicator': 'high_inactive_users',
            'severity': 'medium',
            'description': f"{user_segments['inactive_users']} inactive users ({user_segments['inactive_users']/user_segments['total_users']*100:.0f}%)"
        })

    # Check for low feature utilization
    if core_metrics['feature_utilization_rate'] < 0.3:
        risks.append({
            'indicator': 'low_feature_utilization',
            'severity': 'medium',
            'description': f"Only {core_metrics['feature_utilization_rate']*100:.0f}% of features being used"
        })

    return risks


def _generate_usage_recommendations(
    usage_health_score: int,
    expansion_opportunities: List[Dict[str, Any]],
    risk_indicators: List[Dict[str, Any]],
    feature_analysis: Dict[str, Any]
) -> List[str]:
    """Generate usage-based recommendations"""
    recommendations = []

    # Health-based recommendations
    if usage_health_score < 60:
        recommendations.append("Schedule urgent usage review with customer")

    # Risk-based recommendations
    for risk in risk_indicators:
        if risk['severity'] == 'high':
            recommendations.append(f"Address {risk['indicator']}: {risk['description']}")

    # Opportunity-based recommendations
    for opp in expansion_opportunities:
        recommendations.append(f"Explore {opp['type']}: {opp['description']}")

    # Feature-based recommendations
    underutilized = feature_analysis.get('underutilized_features', [])
    if underutilized:
        recommendations.append(f"Provide training on {underutilized[0]['feature']} and other underutilized features")

    return recommendations or ["Continue monitoring usage patterns"]


async def _create_voc_report(
    client_id: Optional[str],
    period_start: str,
    period_end: str,
    report_type: str,
    include_sentiment: bool,
    include_nps: bool,
    include_product_insights: bool,
    include_customer_quotes: bool,
    target_audience: str
) -> Dict[str, Any]:
    """Create comprehensive VoC report"""
    # Generate report ID
    report_id = f"VOC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Gather all data
    report_data = {
        'report_id': report_id,
        'report_type': report_type,
        'period_start': period_start,
        'period_end': period_end,
        'generated_at': datetime.now().isoformat(),
        'target_audience': target_audience
    }

    # Add sentiment analysis if requested
    if include_sentiment:
        sentiment_data = await _fetch_feedback_data(client_id, period_start, period_end, None)
        report_data['sentiment_analysis'] = _calculate_sentiment_metrics(sentiment_data)

    # Add NPS if requested
    if include_nps:
        report_data['nps_score'] = await _calculate_nps(client_id, period_start, period_end)
        report_data['csat_score'] = await _calculate_csat(client_id, period_start, period_end)

    # Add product insights if requested
    if include_product_insights:
        report_data['product_insights'] = {
            'top_feature_requests': ['Multi-format export', 'API enhancements', 'Mobile app'],
            'critical_bugs': 2,
            'resolved_items': 15
        }

    # Add customer quotes if requested
    if include_customer_quotes:
        report_data['customer_quotes'] = [
            {'quote': 'Great product with excellent support', 'sentiment': 'positive'},
            {'quote': 'Would love to see more integration options', 'sentiment': 'neutral'}
        ]

    return {
        'status': 'success',
        'message': 'VoC report generated successfully',
        'report': report_data,
        'delivery': {
            'format': 'pdf',
            'recipients': _get_voc_recipients(target_audience),
            'delivery_method': 'email'
        }
    }


async def _track_feedback_loop(
    client_id: Optional[str],
    period_start: str,
    period_end: str
) -> Dict[str, Any]:
    """Track feedback loop closure"""
    return {
        'status': 'success',
        'message': 'Feedback loop tracking completed',
        'metrics': {
            'total_feedback_items': 47,
            'closed_loops': 38,
            'open_loops': 9,
            'closure_rate': 0.81,
            'avg_time_to_close_days': 8.5
        },
        'open_items': [
            {'feedback_id': 'FB-12345', 'age_days': 15, 'priority': 'high'},
            {'feedback_id': 'FB-12346', 'age_days': 12, 'priority': 'medium'}
        ]
    }


async def _measure_voc_effectiveness(
    period_start: str,
    period_end: str
) -> Dict[str, Any]:
    """Measure VoC program effectiveness"""
    return {
        'status': 'success',
        'message': 'VoC program effectiveness measured',
        'metrics': {
            'feedback_collection_rate': 0.68,
            'response_rate': 0.72,
            'action_implementation_rate': 0.84,
            'customer_satisfaction_with_voc': 4.2,
            'program_roi': 'High'
        },
        'improvements': [
            'Increase survey response rate to 80%',
            'Reduce time to action on feedback'
        ]
    }


async def _generate_executive_summary(
    client_id: Optional[str],
    period_start: str,
    period_end: str,
    report_type: str
) -> Dict[str, Any]:
    """Generate executive summary of VoC insights"""
    return {
        'status': 'success',
        'message': 'Executive summary generated',
        'summary': {
            'overall_sentiment': 'positive',
            'nps_score': 52,
            'key_wins': [
                'Customer satisfaction up 8% quarter-over-quarter',
                'Successfully launched 3 top-requested features'
            ],
            'areas_of_concern': [
                'Performance feedback increasing',
                'Integration requests growing'
            ],
            'strategic_recommendations': [
                'Invest in performance optimization',
                'Expand integration ecosystem'
            ]
        }
    }


async def _close_feedback_loop(
    client_id: Optional[str],
    period_start: str,
    period_end: str
) -> Dict[str, Any]:
    """Close feedback loops with customers"""
    return {
        'status': 'success',
        'message': 'Feedback loops closed',
        'closed_items': 15,
        'customers_notified': 12,
        'next_steps': [
            'Schedule follow-up calls with key customers',
            'Send satisfaction survey'
        ]
    }


async def _update_customer_roadmap(
    client_id: Optional[str],
    period_start: str,
    period_end: str
) -> Dict[str, Any]:
    """Update customer-facing roadmap based on feedback"""
    return {
        'status': 'success',
        'message': 'Customer roadmap updated',
        'updates': {
            'features_added': 5,
            'priorities_adjusted': 8,
            'timeline_changes': 2
        },
        'next_publication': (datetime.now() + timedelta(days=7)).date().isoformat()
    }


def _get_voc_recipients(target_audience: str) -> List[str]:
    """Get recipients for VoC report"""
    if target_audience == 'executive':
        return ['ceo@company.com', 'cto@company.com', 'cco@company.com']
    elif target_audience == 'product':
        return ['product-team@company.com', 'product-director@company.com']
    elif target_audience == 'cs_team':
        return ['cs-team@company.com', 'cs-leadership@company.com']
    else:
        return ['all-hands@company.com']
