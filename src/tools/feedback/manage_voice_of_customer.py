"""
manage_voice_of_customer - Manage comprehensive Voice of Customer (VoC) program

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

from fastmcp import Context
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime, date, timedelta
from src.security.input_validation import (
from src.decorators import mcp_tool
from src.composio import get_composio_client
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
                }if provided
            if client_id:
            '
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
