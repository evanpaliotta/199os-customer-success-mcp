"""
collect_feedback - Collect and process customer feedback from any source

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

from fastmcp import Context
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime, date, timedelta
from src.security.input_validation import (

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
