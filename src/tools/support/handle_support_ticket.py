"""
handle_support_ticket - Process 108: Comprehensive support ticket handling and resolution

Process 108: Comprehensive support ticket handling and resolution.

Handles the complete ticket lifecycle from creation to resolution,
including updates, escalations, and customer satisfaction tracking.

Actions:
- create: Create new support ticket
- update: Update existing ticket status/details
- resolve: Mark ticket as resolved with solution
- close: Close resolved ticket
- escalate: Escalate ticket to higher tier
- reopen: Reopen closed ticket
- add_comment: Add comment/update to ticket
- rate: Submit customer satisfaction rating

Args:
    ticket_id: Ticket identifier (required for all actions except create)
    action: Action to perform (create, update, resolve, close, escalate, reopen, add_comment, rate)
    client_id: Customer identifier (required for create)
    subject: Ticket subject/title (required for create)
    description: Issue description (required for create)
    priority: Priority level (P0-P4, default P3)
    category: Ticket category (technical_issue, bug_report, etc.)
    requester_email: Customer email (required for create)
    requester_name: Customer name (required for create)
    assigned_agent: Agent email for assignment
    status: Ticket status (open, in_progress, waiting_on_customer, etc.)
    resolution_notes: Resolution details and solution provided
    internal_notes: Internal notes (not visible to customer)
    customer_visible_notes: Notes visible to customer
    satisfaction_rating: Customer satisfaction rating (1-5)
    satisfaction_comment: Customer satisfaction feedback
    escalate: Whether to escalate ticket
    escalation_reason: Reason for escalation
    tags: Tags for categorization

Returns:
    Ticket processing result with updated ticket details, SLA status, and next steps
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

async def handle_support_ticket(
        ctx: Context,
        ticket_id: Optional[str] = None,
        action: str = "create",
        client_id: Optional[str] = None,
        subject: Optional[str] = None,
        description: Optional[str] = None,
        priority: str = "P3",
        category: str = "technical_issue",
        requester_email: Optional[str] = None,
        requester_name: Optional[str] = None,
        assigned_agent: Optional[str] = None,
        status: Optional[str] = None,
        resolution_notes: Optional[str] = None,
        internal_notes: Optional[str] = None,
        customer_visible_notes: Optional[str] = None,
        satisfaction_rating: Optional[int] = None,
        satisfaction_comment: Optional[str] = None,
        escalate: bool = False,
        escalation_reason: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process 108: Comprehensive support ticket handling and resolution.

        Handles the complete ticket lifecycle from creation to resolution,
        including updates, escalations, and customer satisfaction tracking.

        Actions:
        - create: Create new support ticket
        - update: Update existing ticket status/details
        - resolve: Mark ticket as resolved with solution
        - close: Close resolved ticket
        - escalate: Escalate ticket to higher tier
        - reopen: Reopen closed ticket
        - add_comment: Add comment/update to ticket
        - rate: Submit customer satisfaction rating

        Args:
            ticket_id: Ticket identifier (required for all actions except create)
            action: Action to perform (create, update, resolve, close, escalate, reopen, add_comment, rate)
            client_id: Customer identifier (required for create)
            subject: Ticket subject/title (required for create)
            description: Issue description (required for create)
            priority: Priority level (P0-P4, default P3)
            category: Ticket category (technical_issue, bug_report, etc.)
            requester_email: Customer email (required for create)
            requester_name: Customer name (required for create)
            assigned_agent: Agent email for assignment
            status: Ticket status (open, in_progress, waiting_on_customer, etc.)
            resolution_notes: Resolution details and solution provided
            internal_notes: Internal notes (not visible to customer)
            customer_visible_notes: Notes visible to customer
            satisfaction_rating: Customer satisfaction rating (1-5)
            satisfaction_comment: Customer satisfaction feedback
            escalate: Whether to escalate ticket
            escalation_reason: Reason for escalation
            tags: Tags for categorization

        Returns:
            Ticket processing result with updated ticket details, SLA status, and next steps
        """
        try:
            await ctx.info(f"Processing ticket action: {action}")

            # Validate action
            valid_actions = ['create', 'update', 'resolve', 'close', 'escalate',
                           'reopen', 'add_comment', 'rate']
            if action not in valid_actions:
                return {
                    'status': 'failed',
                    'error': f"Invalid action. Must be one of: {', '.join(valid_actions)}"
                }

            # CREATE NEW TICKET
            if action == "create":
                # Validate required fields
                if not all([client_id, subject, description, requester_email, requester_name]):
                    return {
                        'status': 'failed',
                        'error': 'Missing required fields: client_id, subject, description, requester_email, requester_name'
                    }'
                    }

                # Validate and sanitize inputs
                subject = SecurityValidator.validate_no_xss(subject)
                description = SecurityValidator.validate_no_xss(description)

                # Generate ticket ID
                timestamp = int(datetime.now().timestamp())
                new_ticket_id = f"TKT-{timestamp % 1000000}"

                # Determine SLA targets based on priority
                sla_targets = _calculate_sla_targets(priority)

                # Create ticket in local system
                try:
                    ticket = SupportTicket(
                        ticket_id=new_ticket_id,
                        client_id=client_id,
                        subject=subject,
                        description=description,
                        priority=TicketPriority(priority),
                        category=TicketCategory(category),
                        status=TicketStatus.OPEN,
                        requester_email=requester_email,
                        requester_name=requester_name,
                        assigned_agent=assigned_agent,
                        assigned_team=_determine_team(category, priority),
                        tags=tags or [],
                        sla_first_response_minutes=sla_targets['first_response'],
                        sla_resolution_minutes=sla_targets['resolution']
                    )

                    # Calculate initial SLA status
                    ticket.calculate_sla_status()

                    # Create ticket in Zendesk (if configured)
                    zendesk_client = _get_zendesk_client()
                    zendesk_result = None
                    zendesk_ticket_id = None

                    if zendesk_client.client:
                        # Map priority to Zendesk priority format
                        zendesk_priority = {
                            'P0': 'urgent',
                            'P1': 'high',
                            'P2': 'normal',
                            'P3': 'normal',
                            'P4': 'low'
                        }.get(priority, 'normal')

                        # Add category and client_id to tags
                        zendesk_tags = (tags or []) + [category, f'client:{client_id}']

                        zendesk_result = zendesk_client.create_ticket(
                            subject=subject,
                            description=description,
                            requester_email=requester_email,
                            priority=zendesk_priority,
                            tags=zendesk_tags
                        )

                        if zendesk_result.get('status') == 'success':
                            zendesk_ticket_id = zendesk_result.get('ticket_id')
                            logger.info(
                                "zendesk_ticket_created_for_support",
                                local_ticket_id=new_ticket_id,
                                zendesk_ticket_id=zendesk_ticket_id
                            )

                    logger.info(
                        "support_ticket_created",
                        ticket_id=new_ticket_id,
                        client_id=client_id,
                        priority=priority,
                        category=category,
                        zendesk_ticket_id=zendesk_ticket_id
                    )

                    response = {
                        'status': 'success',
                        'message': f"Ticket {new_ticket_id} created successfully",
                        'ticket_id': new_ticket_id,
                        'ticket': ticket.model_dump(),
                        'sla_targets': sla_targets,
                        'routing': {
                            'assigned_team': ticket.assigned_team,
                            'assigned_agent': ticket.assigned_agent,
                            'priority': priority,
                            'expected_first_response': (
                                datetime.now() + timedelta(minutes=sla_targets['first_response'])
                            ).isoformat(),
                            'expected_resolution': (
                                datetime.now() + timedelta(minutes=sla_targets['resolution'])
                            ).isoformat()
                        },
                        'next_steps': [
                            f"Agent should respond within {sla_targets['first_response']} minutes",
                            "Ticket will be auto-routed based on priority and category",
                            "Customer will receive email confirmation",
                            f"Resolution expected within {sla_targets['resolution']} minutes"
                        ]
                    }

                    # Add Zendesk info if available
                    if zendesk_result:
                        response['zendesk'] = {
                            'status': zendesk_result.get('status'),
                            'ticket_id': zendesk_result.get('ticket_id'),
                            'ticket_url': zendesk_result.get('ticket_url'),
                            'error': zendesk_result.get('error')
                        }

                    return response

                except Exception as e:
                    return {
                        'status': 'failed',
                        'error': f"Failed to create ticket: {str(e)}"
                    }

            # All other actions require ticket_id
            if not ticket_id:
                return {
                    'status': 'failed',
                    'error': f'ticket_id is required for action: {action}'
                }

            # Mock ticket retrieval (replace with actual database query)
            ticket_data = _get_mock_ticket(ticket_id)
            if not ticket_data:
                return {
                    'status': 'failed',
                    'error': f'Ticket not found: {ticket_id}'
                }

            ticket = SupportTicket(**ticket_data)

            # UPDATE TICKET
            if action == "update":
                updated_fields = []

                if status:
                    ticket.status = TicketStatus(status)
                    updated_fields.append(f"status -> {status}")

                if assigned_agent:
                    ticket.assigned_agent = assigned_agent
                    updated_fields.append(f"assigned_agent -> {assigned_agent}")

                if priority:
                    old_priority = ticket.priority
                    ticket.priority = TicketPriority(priority)
                    if old_priority != ticket.priority:
                        # Recalculate SLA targets
                        sla_targets = _calculate_sla_targets(priority)
                        ticket.sla_first_response_minutes = sla_targets['first_response']
                        ticket.sla_resolution_minutes = sla_targets['resolution']
                        updated_fields.append(f"priority -> {priority} (SLA updated)")

                if internal_notes:
                    ticket.internal_notes = SecurityValidator.validate_no_xss(internal_notes)
                    updated_fields.append("internal_notes updated")

                if customer_visible_notes:
                    ticket.customer_visible_notes = SecurityValidator.validate_no_xss(customer_visible_notes)
                    updated_fields.append("customer_visible_notes updated")

                if tags:
                    ticket.tags = tags
                    updated_fields.append(f"tags -> {tags}")

                ticket.updated_at = datetime.now()
                ticket.calculate_sla_status()

                logger.info(
                    "support_ticket_updated",
                    ticket_id=ticket_id,
                    fields_updated=updated_fields
                )

                return {
                    'status': 'success',
                    'message': f"Ticket {ticket_id} updated successfully",
                    'ticket_id': ticket_id,
                    'updates': updated_fields,
                    'ticket': ticket.model_dump(),
                    'sla_status': {
                        'first_response': ticket.first_response_sla_status.value,
                        'resolution': ticket.resolution_sla_status.value
                    }
                }

            # RESOLVE TICKET
            elif action == "resolve":
                if not resolution_notes:
                    return {
                        'status': 'failed',
                        'error': 'resolution_notes is required to resolve a ticket'
                    }

                ticket.status = TicketStatus.RESOLVED
                ticket.resolution_notes = SecurityValidator.validate_no_xss(resolution_notes)
                ticket.resolved_at = datetime.now()
                ticket.updated_at = datetime.now()
                ticket.calculate_sla_status()

                logger.info(
                    "support_ticket_resolved",
                    ticket_id=ticket_id,
                    resolution_time_minutes=ticket.time_to_resolution_minutes,
                    sla_met=ticket.resolution_sla_status == SLAStatus.MET
                )

                return {
                    'status': 'success',
                    'message': f"Ticket {ticket_id} resolved successfully",
                    'ticket_id': ticket_id,
                    'resolution': {
                        'resolved_at': ticket.resolved_at.isoformat(),
                        'resolution_time_minutes': ticket.time_to_resolution_minutes,
                        'resolution_notes': ticket.resolution_notes,
                        'sla_status': ticket.resolution_sla_status.value,
                        'sla_met': ticket.resolution_sla_status == SLAStatus.MET
                    },
                    'ticket': ticket.model_dump(),
                    'next_steps': [
                        "Customer will receive resolution notification",
                        "Ticket will auto-close in 48 hours if no response",
                        "Customer satisfaction survey will be sent"
                    ]
                }

            # CLOSE TICKET
            elif action == "close":
                if ticket.status != TicketStatus.RESOLVED:
                    return {
                        'status': 'failed',
                        'error': 'Ticket must be resolved before closing'
                    }

                ticket.status = TicketStatus.CLOSED
                ticket.closed_at = datetime.now()
                ticket.updated_at = datetime.now()

                logger.info("support_ticket_closed", ticket_id=ticket_id)

                return {
                    'status': 'success',
                    'message': f"Ticket {ticket_id} closed successfully",
                    'ticket_id': ticket_id,
                    'closure': {
                        'closed_at': ticket.closed_at.isoformat(),
                        'total_time_minutes': int(
                            (ticket.closed_at - ticket.created_at).total_seconds() / 60
                        ),
                        'satisfaction_rating': ticket.satisfaction_rating,
                        'sla_met': ticket.resolution_sla_status == SLAStatus.MET
                    },
                    'ticket': ticket.model_dump()
                }

            # ESCALATE TICKET
            elif action == "escalate":
                if not escalation_reason:
                    return {
                        'status': 'failed',
                        'error': 'escalation_reason is required to escalate a ticket'
                    }

                ticket.escalated = True
                ticket.escalated_at = datetime.now()
                ticket.escalation_reason = SecurityValidator.validate_no_xss(escalation_reason)
                ticket.updated_at = datetime.now()

                # Upgrade priority if possible
                if ticket.priority == TicketPriority.P4_LOW:
                    ticket.priority = TicketPriority.P3_NORMAL
                elif ticket.priority == TicketPriority.P3_NORMAL:
                    ticket.priority = TicketPriority.P2_MEDIUM
                elif ticket.priority == TicketPriority.P2_MEDIUM:
                    ticket.priority = TicketPriority.P1_HIGH

                # Reassign to escalation team
                ticket.assigned_team = "Escalation Team"

                logger.warning(
                    "support_ticket_escalated",
                    ticket_id=ticket_id,
                    reason=escalation_reason,
                    new_priority=ticket.priority.value
                )

                return {
                    'status': 'success',
                    'message': f"Ticket {ticket_id} escalated successfully",
                    'ticket_id': ticket_id,
                    'escalation': {
                        'escalated_at': ticket.escalated_at.isoformat(),
                        'reason': ticket.escalation_reason,
                        'new_priority': ticket.priority.value,
                        'assigned_team': ticket.assigned_team
                    },
                    'ticket': ticket.model_dump(),
                    'next_steps': [
                        "Escalation team will review within 1 hour",
                        "Senior agent will be assigned",
                        "Customer will be notified of escalation"
                    ]
                }

            # REOPEN TICKET
            elif action == "reopen":
                if ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
                    return {
                        'status': 'failed',
                        'error': 'Can only reopen resolved or closed tickets'
                    }

                ticket.status = TicketStatus.REOPENED
                ticket.updated_at = datetime.now()
                ticket.resolved_at = None
                ticket.closed_at = None

                logger.info("support_ticket_reopened", ticket_id=ticket_id)

                return {
                    'status': 'success',
                    'message': f"Ticket {ticket_id} reopened successfully",
                    'ticket_id': ticket_id,
                    'ticket': ticket.model_dump(),
                    'next_steps': [
                        "Ticket will be re-routed to appropriate team",
                        "Original agent will be notified",
                        "New SLA clock starts"
                    ]
                }

            # ADD COMMENT
            elif action == "add_comment":
                if not customer_visible_notes and not internal_notes:
                    return {
                        'status': 'failed',
                        'error': 'Either customer_visible_notes or internal_notes required'
                    }

                comment_id = f"CMT-{int(datetime.now().timestamp()) % 1000000}"
                comment = TicketComment(
                    comment_id=comment_id,
                    ticket_id=ticket_id,
                    author_email=assigned_agent or "system@company.com",
                    author_name=assigned_agent or "System",
                    author_type="agent",
                    content=customer_visible_notes or internal_notes,
                    is_public=bool(customer_visible_notes)
                )

                # Update first response time if this is first agent comment
                if not ticket.first_response_at and assigned_agent:
                    ticket.first_response_at = datetime.now()
                    ticket.calculate_sla_status()

                ticket.updated_at = datetime.now()

                logger.info(
                    "support_ticket_comment_added",
                    ticket_id=ticket_id,
                    comment_id=comment_id,
                    is_public=comment.is_public
                )

                return {
                    'status': 'success',
                    'message': f"Comment added to ticket {ticket_id}",
                    'ticket_id': ticket_id,
                    'comment': comment.model_dump(),
                    'first_response_recorded': bool(not ticket.first_response_at),
                    'ticket': ticket.model_dump()
                }

            # RATE TICKET
            elif action == "rate":
                if not satisfaction_rating:
                    return {
                        'status': 'failed',
                        'error': 'satisfaction_rating (1-5) is required'
                    }

                if not 1 <= satisfaction_rating <= 5:
                    return {
                        'status': 'failed',
                        'error': 'satisfaction_rating must be between 1 and 5'
                    }

                ticket.satisfaction_rating = satisfaction_rating
                ticket.satisfaction_comment = SecurityValidator.validate_no_xss(
                    satisfaction_comment
                ) if satisfaction_comment else None
                ticket.updated_at = datetime.now()

                logger.info(
                    "support_ticket_rated",
                    ticket_id=ticket_id,
                    rating=satisfaction_rating
                )

                return {
                    'status': 'success',
                    'message': f"Satisfaction rating recorded for ticket {ticket_id}",
                    'ticket_id': ticket_id,
                    'satisfaction': {
                        'rating': satisfaction_rating,
                        'comment': ticket.satisfaction_comment
                    },
                    'ticket': ticket.model_dump()
                }

        except Exception as e:
            logger.error(
                "handle_support_ticket_failed",
                action=action,
                ticket_id=ticket_id,
                error=str(e)
            )
            return {
                'status': 'failed',
                'error': f"Failed to process ticket: {str(e)}"
            }
