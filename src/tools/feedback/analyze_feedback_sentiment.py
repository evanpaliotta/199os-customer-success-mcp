"""
analyze_feedback_sentiment - Analyze sentiment across customer feedback for insights and trends

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

from fastmcp import Context
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime, date, timedelta
from src.security.input_validation import (
from src.decorators import mcp_tool
from src.composio import get_composio_client
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
                }if provided
            if client_id:
            '
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
