"""
track_cs_metrics - Track and analyze key Customer Success metrics and KPIs

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

from fastmcp import Context
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime, date, timedelta
from src.security.input_validation import (

    from src.decorators import mcp_tool
from src.composio import get_composio_client

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
                }if provided
            if client_id:
            '
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
