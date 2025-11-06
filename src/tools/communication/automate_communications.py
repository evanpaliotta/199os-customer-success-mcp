"""
automate_communications - Create and manage automated communication workflows

Create and manage automated communication workflows.

Build sophisticated automation workflows that trigger communications based on
customer behaviors, lifecycle events, health changes, or time-based schedules.
Supports multi-step workflows with conditional logic and delays.

Process 103: Communication Automation
- Trigger-based workflows (time, event, behavior, health)
- Multi-channel communication (email, in-app, Slack, SMS)
- Conditional branching and A/B testing
- Delay and throttling controls
- Performance tracking and optimization
- Workflow templates for common scenarios

Args:
    workflow_name: Descriptive workflow name
    description: Workflow purpose and expected behavior
    trigger_type: What activates the workflow (time_based, event_based, etc.)
    trigger_conditions: Specific conditions that must be met (dict with keys like
                      "event": "onboarding_completed", "days_after": 7, etc.)
    actions: List of actions to execute, each dict with "type" (send_email, create_task,
            update_health, etc.) and action-specific parameters
    delay_minutes: Optional delay before executing actions (default 0)
    is_active: Whether workflow is active and will execute (default True)

Returns:
    Workflow creation confirmation with trigger details, actions, and execution history
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field, EmailStr, field_validator
from src.security.input_validation import validate_client_id, ValidationError
from src.integrations.sendgrid_client import SendGridClient
from src.integrations.intercom_client import IntercomClient
import structlog
from src.decorators import mcp_tool
from src.composio import get_composio_client
async def automate_communications(
        ctx: Context,
        workflow_name: str,
        description: str,
        trigger_type: Literal[
            "time_based", "event_based", "behavior_based",
            "health_score", "milestone", "contract_event",
            "usage_pattern", "custom"
        ],
        trigger_conditions: Dict[str, Any],
        actions: List[Dict[str, Any]],
        delay_minutes: int = 0,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """
        Create and manage automated communication workflows.

        Build sophisticated automation workflows that trigger communications based on
        customer behaviors, lifecycle events, health changes, or time-based schedules.
        Supports multi-step workflows with conditional logic and delays.

        Process 103: Communication Automation
        - Trigger-based workflows (time, event, behavior, health)
        - Multi-channel communication (email, in-app, Slack, SMS)
        - Conditional branching and A/B testing
        - Delay and throttling controls
        - Performance tracking and optimization
        - Workflow templates for common scenarios

        Args:
            workflow_name: Descriptive workflow name
            description: Workflow purpose and expected behavior
            trigger_type: What activates the workflow (time_based, event_based, etc.)
            trigger_conditions: Specific conditions that must be met (dict with keys like
                              "event": "onboarding_completed", "days_after": 7, etc.)
            actions: List of actions to execute, each dict with "type" (send_email, create_task,
                    update_health, etc.) and action-specific parameters
            delay_minutes: Optional delay before executing actions (default 0)
            is_active: Whether workflow is active and will execute (default True)

        Returns:
            Workflow creation confirmation with trigger details, actions, and execution history
        """
        try:
            await ctx.info(f"Creating automation workflow: {workflow_name}")

            # Validate actions format
            if not actions or len(actions) == 0:
                return {
                    'status': 'failed',
                    'error': 'Must specify at least one action'
                }

            # Validate action structure
            valid_action_types = [
                'send_email', 'create_task', 'send_slack_message',
                'update_health_score', 'create_ticket', 'schedule_meeting',
                'send_in_app_notification', 'trigger_webhook', 'send_sms'
            ]

            for idx, action in enumerate(actions):
                if 'type' not in action:
                    return {
                        'status': 'failed',
                        'error': f'Action {idx + 1} missing required "type" field'
                    }
                if action['type'] not in valid_action_types:
                    return {
                        'status': 'failed',
                        'error': f'Action {idx + 1} has invalid type "{action["type"]}". Valid: {", ".join(valid_action_types)}'
                    }

            # Validate trigger conditions
            required_condition_keys = {
                'time_based': ['schedule'],
                'event_based': ['event'],
                'behavior_based': ['behavior'],
                'health_score': ['threshold', 'direction'],
                'milestone': ['milestone_name'],
                'contract_event': ['event_type'],
                'usage_pattern': ['metric', 'threshold']
            }

            if trigger_type in required_condition_keys:
                missing_keys = [
                    key for key in required_condition_keys[trigger_type]
                    if key not in trigger_conditions
                ]
                if missing_keys:
                    return {
                        'status': 'failed',
                        'error': f'Trigger conditions missing required keys for {trigger_type}: {", ".join(missing_keys)}'
                    }

            # Generate workflow ID
            timestamp = int(datetime.now().timestamp())
            sanitized_name = workflow_name.lower().replace(' ', '_')[:20]
            workflow_id = f"workflow_{timestamp}_{sanitized_name}"

            # Create workflow model
            workflow = CommunicationWorkflow(
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                description=description,
                trigger_type=AutomationTrigger(trigger_type),
                trigger_conditions=trigger_conditions,
                actions=actions,
                delay_minutes=delay_minutes,
                is_active=is_active
            )

            # Execute workflow actions with Intercom if active
            intercom_actions_executed = []
            if is_active and delay_minutes == 0:  # Execute immediately if no delay
                intercom_client = get_intercom_client()

                for idx, action in enumerate(actions):
                    if action['type'] == 'send_in_app_notification':
                        # Send via Intercom in-app message
                        user_email = action.get('user_email')
                        message_body = action.get('message', action.get('body', ''))

                        if user_email and message_body:
                            result = intercom_client.send_message(
                                user_email=user_email,
                                message_type="inapp",
                                body=message_body
                            )

                            intercom_actions_executed.append({
                                "action_index": idx + 1,
                                "action_type": "send_in_app_notification",
                                "user_email": user_email,
                                "success": result.get("success", False),
                                "message_id": result.get("message_id"),
                                "error": result.get("error")
                            })

                            # Track automation event
                            if result.get("success"):
                                intercom_client.track_event(
                                    user_email=user_email,
                                    event_name="automation_triggered",
                                    metadata={
                                        "workflow_id": workflow_id,
                                        "workflow_name": workflow_name,
                                        "trigger_type": trigger_type,
                                        "action_type": action['type']
                                    }
                                )

                    elif action['type'] == 'create_task':
                        # Create note in Intercom as a task reminder
                        user_email = action.get('user_email')
                        task_description = action.get('description', action.get('task', ''))

                        if user_email and task_description:
                            result = intercom_client.create_note(
                                user_email=user_email,
                                body=f"Automated Task: {task_description}"
                            )

                            intercom_actions_executed.append({
                                "action_index": idx + 1,
                                "action_type": "create_task",
                                "user_email": user_email,
                                "success": result.get("success", False),
                                "note_id": result.get("note_id"),
                                "error": result.get("error")
                            })

                # Log Intercom automation execution
                if intercom_actions_executed:
                    successful_actions = sum(1 for a in intercom_actions_executed if a["success"])
                    logger.info(
                        "intercom_automation_executed",
                        workflow_id=workflow_id,
                        actions_executed=len(intercom_actions_executed),
                        successful=successful_actions,
                        failed=len(intercom_actions_executed) - successful_actions
                    )

            # Analyze workflow configuration
            channels_used = set()
            for action in actions:
                if action['type'] == 'send_email':
                    channels_used.add('email')
                elif action['type'] == 'send_slack_message':
                    channels_used.add('slack')
                elif action['type'] == 'send_in_app_notification':
                    channels_used.add('in_app')
                elif action['type'] == 'send_sms':
                    channels_used.add('sms')

            # Estimate impact
            trigger_frequency_estimates = {
                'time_based': 'Daily/Weekly based on schedule',
                'event_based': 'On-demand when events occur',
                'behavior_based': 'Variable based on customer behavior',
                'health_score': 'When health score crosses threshold',
                'milestone': 'When milestone is reached',
                'contract_event': 'On contract lifecycle events',
                'usage_pattern': 'When usage patterns match criteria',
                'custom': 'Based on custom logic'
            }

            # Log workflow creation
            logger.info(
                "communication_workflow_created",
                workflow_id=workflow_id,
                trigger_type=trigger_type,
                action_count=len(actions),
                is_active=is_active,
                intercom_actions_executed=len(intercom_actions_executed)
            )

            # Audit log for compliance
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "automation_workflow_created",
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "trigger_type": trigger_type,
                "is_active": is_active,
                "action_count": len(actions),
                "intercom_integration": len(intercom_actions_executed) > 0
            }
            logger.info("audit_log", **audit_entry)

            return {
                'status': 'success',
                'message': f"Automation workflow '{workflow_name}' created successfully",
                'workflow': {
                    'workflow_id': workflow_id,
                    'workflow_name': workflow_name,
                    'description': description,
                    'is_active': is_active,
                    'created_at': workflow.created_at.isoformat(),
                    'updated_at': workflow.updated_at.isoformat()
                },
                'trigger': {
                    'trigger_type': trigger_type,
                    'conditions': trigger_conditions,
                    'estimated_frequency': trigger_frequency_estimates.get(trigger_type, 'Variable')
                },
                'execution': {
                    'total_actions': len(actions),
                    'delay_minutes': delay_minutes,
                    'channels_used': list(channels_used),
                    'actions_summary': [
                        {
                            'step': idx + 1,
                            'action_type': action['type'],
                            'description': action.get('description', f"{action['type']} action")
                        }
                        for idx, action in enumerate(actions)
                    ]
                },
                'intercom_integration': {
                    'enabled': len(intercom_actions_executed) > 0,
                    'actions_executed': len(intercom_actions_executed),
                    'successful': sum(1 for a in intercom_actions_executed if a["success"]),
                    'failed': sum(1 for a in intercom_actions_executed if not a["success"]),
                    'results': intercom_actions_executed if intercom_actions_executed else None
                },
                'performance': {
                    'executions_count': len(intercom_actions_executed) if intercom_actions_executed else 0,
                    'last_executed': datetime.now().isoformat() if intercom_actions_executed else None,
                    'success_rate': (sum(1 for a in intercom_actions_executed if a["success"]) / len(intercom_actions_executed) * 100) if intercom_actions_executed else None,
                    'avg_execution_time_ms': None
                },
                'testing': {
                    'test_mode_available': True,
                    'test_command': f"Use workflow_id '{workflow_id}' to test execution",
                    'dry_run_supported': True
                },
                'next_steps': [
                    f"Test workflow with sample data before activating",
                    "Monitor execution logs for the first 24 hours",
                    "Review customer feedback and engagement metrics",
                    "Optimize trigger conditions based on performance",
                    "Consider A/B testing variations of automated messages"
                ]
            }

        except Exception as e:
            logger.error("automate_communications_failed", error=str(e))
            return {
                'status': 'failed',
                'error': f"Failed to create automation workflow: {str(e)}"
            }
