"""
analyze_product_usage - Analyze product usage patterns and feature adoption for a customer

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

from fastmcp import Context
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime, date, timedelta
from src.security.input_validation import (
from src.decorators import mcp_tool
from src.composio import get_composio_client
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
    # LOCAL PROCESSING PATTERN:
    # 1. Fetch data via Composio: data = await composio.execute_action("action_name", client_id, params)
    # 2. Process locally: df = pd.DataFrame(data); summary = df.groupby('stage').agg(...)
    # 3. Return summary only (not raw data)
    # This keeps large datasets out of model context (98.9% token savings)

        
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
