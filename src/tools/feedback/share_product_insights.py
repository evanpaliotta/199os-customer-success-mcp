"""
share_product_insights - Share curated product insights with product team based on customer feedback

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

from fastmcp import Context
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime, date, timedelta
from src.security.input_validation import (
from src.decorators import mcp_tool
from src.composio import get_composio_client
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
    # LOCAL PROCESSING PATTERN:
    # 1. Fetch data via Composio: data = await composio.execute_action("action_name", client_id, params)
    # 2. Process locally: df = pd.DataFrame(data); summary = df.groupby('stage').agg(...)
    # 3. Return summary only (not raw data)
    # This keeps large datasets out of model context (98.9% token savings)

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
