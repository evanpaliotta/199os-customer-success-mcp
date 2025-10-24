"""
Support & Self-Service Tools
Comprehensive ticket handling, knowledge base management, and support analytics
Processes 108-113
"""

from fastmcp import Context
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re
import structlog

from src.models.support_models import (
    SupportTicket,
    TicketComment,
    KnowledgeBaseArticle,
    SupportMetrics,
    TicketPriority,
    TicketStatus,
    TicketCategory,
    SLAStatus,
    ArticleStatus
)
from src.security.input_validation import (
    validate_client_id,
    ValidationError,
    SecurityValidator
)
from src.integrations.zendesk_client import ZendeskClient

logger = structlog.get_logger(__name__)

# Initialize Zendesk client (singleton pattern)
_zendesk_client = None

def _get_zendesk_client():
    """Get or create Zendesk client instance"""
    global _zendesk_client
    if _zendesk_client is None:
        _zendesk_client = ZendeskClient()
    return _zendesk_client


def register_tools(mcp):
    """Register all support and self-service tools with the MCP instance"""

    @mcp.tool()
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
                    }

                # Validate client_id
                try:
                    client_id = validate_client_id(client_id)
                except ValidationError as e:
                    return {
                        'status': 'failed',
                        'error': f'Invalid client_id: {str(e)}'
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

    @mcp.tool()
    async def route_tickets(
        ctx: Context,
        routing_strategy: str = "auto",
        ticket_id: Optional[str] = None,
        team_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        load_balance: bool = True,
        max_tickets_per_agent: int = 10
    ) -> Dict[str, Any]:
        """
        Process 109: Intelligent ticket routing and prioritization.

        Routes tickets to appropriate teams/agents based on priority, category,
        agent workload, expertise, and SLA requirements. Supports manual routing,
        automatic routing, and workload balancing.

        Routing Strategies:
        - auto: Automatic routing based on category, priority, and workload
        - manual: Manual assignment to specific ticket
        - rebalance: Redistribute tickets across team
        - escalation: Route escalated tickets to senior agents
        - workload: Balance based on agent capacity

        Args:
            routing_strategy: Routing approach (auto, manual, rebalance, escalation, workload)
            ticket_id: Specific ticket ID for manual routing
            team_filter: Filter by team name
            priority_filter: Filter by priority level (P0-P4)
            category_filter: Filter by category
            load_balance: Whether to balance load across agents
            max_tickets_per_agent: Maximum active tickets per agent

        Returns:
            Routing results with assignments, queue status, and SLA tracking
        """
        try:
            await ctx.info(f"Routing tickets with strategy: {routing_strategy}")

            # Validate routing strategy
            valid_strategies = ['auto', 'manual', 'rebalance', 'escalation', 'workload']
            if routing_strategy not in valid_strategies:
                return {
                    'status': 'failed',
                    'error': f"Invalid routing_strategy. Must be one of: {', '.join(valid_strategies)}"
                }

            # Get current ticket queue (mock data)
            tickets = _get_ticket_queue(
                team_filter=team_filter,
                priority_filter=priority_filter,
                category_filter=category_filter
            )

            # Get available agents (mock data)
            agents = _get_available_agents(team_filter)

            routing_results = []
            queue_summary = {
                'total_tickets': len(tickets),
                'unassigned_tickets': 0,
                'sla_at_risk': 0,
                'sla_breached': 0,
                'tickets_by_priority': defaultdict(int),
                'tickets_by_category': defaultdict(int)
            }

            # AUTOMATIC ROUTING
            if routing_strategy == "auto":
                # Sort tickets by priority and SLA urgency
                sorted_tickets = sorted(
                    tickets,
                    key=lambda t: (
                        _priority_weight(t['priority']),
                        t.get('sla_breach_risk', 0)
                    ),
                    reverse=True
                )

                for ticket in sorted_tickets:
                    if ticket.get('assigned_agent'):
                        continue  # Skip already assigned tickets

                    # Find best agent based on:
                    # 1. Expertise (category match)
                    # 2. Current workload
                    # 3. Availability
                    best_agent = _find_best_agent(
                        agents,
                        ticket,
                        load_balance,
                        max_tickets_per_agent
                    )

                    if best_agent:
                        assignment = {
                            'ticket_id': ticket['ticket_id'],
                            'assigned_to': best_agent['email'],
                            'team': best_agent['team'],
                            'reason': f"Auto-routed based on {ticket['category']} expertise",
                            'priority': ticket['priority'],
                            'sla_target_minutes': ticket.get('sla_resolution_minutes', 240)
                        }
                        routing_results.append(assignment)

                        # Update agent workload
                        best_agent['current_tickets'] += 1
                    else:
                        queue_summary['unassigned_tickets'] += 1

            # MANUAL ROUTING
            elif routing_strategy == "manual":
                if not ticket_id:
                    return {
                        'status': 'failed',
                        'error': 'ticket_id required for manual routing'
                    }

                ticket = next((t for t in tickets if t['ticket_id'] == ticket_id), None)
                if not ticket:
                    return {
                        'status': 'failed',
                        'error': f'Ticket not found: {ticket_id}'
                    }

                # Present routing options
                agent_options = []
                for agent in agents:
                    if agent['current_tickets'] < max_tickets_per_agent:
                        expertise_match = ticket['category'] in agent.get('expertise', [])
                        agent_options.append({
                            'email': agent['email'],
                            'name': agent['name'],
                            'team': agent['team'],
                            'current_tickets': agent['current_tickets'],
                            'expertise_match': expertise_match,
                            'availability': agent.get('status', 'available')
                        })

                return {
                    'status': 'success',
                    'ticket': ticket,
                    'routing_options': sorted(
                        agent_options,
                        key=lambda a: (not a['expertise_match'], a['current_tickets'])
                    ),
                    'recommendation': agent_options[0] if agent_options else None
                }

            # REBALANCE WORKLOAD
            elif routing_strategy == "rebalance":
                # Calculate average tickets per agent
                total_assigned = sum(a['current_tickets'] for a in agents)
                avg_tickets = total_assigned / len(agents) if agents else 0

                # Find overloaded and underloaded agents
                overloaded = [a for a in agents if a['current_tickets'] > avg_tickets + 2]
                underloaded = [a for a in agents if a['current_tickets'] < avg_tickets - 1]

                rebalance_moves = []
                for overloaded_agent in overloaded:
                    # Get lowest priority tickets from overloaded agent
                    agent_tickets = [t for t in tickets
                                   if t.get('assigned_agent') == overloaded_agent['email']]
                    low_priority = sorted(
                        agent_tickets,
                        key=lambda t: _priority_weight(t['priority'])
                    )

                    for ticket in low_priority:
                        if not underloaded:
                            break

                        target_agent = underloaded[0]
                        rebalance_moves.append({
                            'ticket_id': ticket['ticket_id'],
                            'from_agent': overloaded_agent['email'],
                            'to_agent': target_agent['email'],
                            'reason': 'Workload rebalancing'
                        })

                        target_agent['current_tickets'] += 1
                        if target_agent['current_tickets'] >= avg_tickets - 1:
                            underloaded.pop(0)

                return {
                    'status': 'success',
                    'strategy': 'rebalance',
                    'rebalance_moves': rebalance_moves,
                    'summary': {
                        'tickets_reassigned': len(rebalance_moves),
                        'average_tickets_per_agent': avg_tickets,
                        'agents_balanced': len(overloaded) + len(underloaded)
                    }
                }

            # ESCALATION ROUTING
            elif routing_strategy == "escalation":
                # Get escalated tickets
                escalated_tickets = [t for t in tickets if t.get('escalated', False)]

                # Route to senior agents or escalation team
                senior_agents = [a for a in agents if a.get('seniority') == 'senior']

                for ticket in escalated_tickets:
                    best_senior = min(
                        senior_agents,
                        key=lambda a: a['current_tickets'],
                        default=None
                    )

                    if best_senior:
                        routing_results.append({
                            'ticket_id': ticket['ticket_id'],
                            'assigned_to': best_senior['email'],
                            'team': 'Escalation Team',
                            'reason': f"Escalated: {ticket.get('escalation_reason', 'N/A')}",
                            'priority': 'P1',  # Upgrade to P1
                            'requires_senior': True
                        })

            # WORKLOAD BALANCING
            elif routing_strategy == "workload":
                # Distribute unassigned tickets evenly
                unassigned = [t for t in tickets if not t.get('assigned_agent')]

                # Sort agents by current workload
                sorted_agents = sorted(agents, key=lambda a: a['current_tickets'])

                for ticket in unassigned:
                    # Get agent with lowest workload
                    agent = sorted_agents[0]

                    if agent['current_tickets'] < max_tickets_per_agent:
                        routing_results.append({
                            'ticket_id': ticket['ticket_id'],
                            'assigned_to': agent['email'],
                            'team': agent['team'],
                            'reason': 'Workload balancing',
                            'priority': ticket['priority']
                        })

                        agent['current_tickets'] += 1
                        sorted_agents.sort(key=lambda a: a['current_tickets'])

            # Calculate queue summary
            for ticket in tickets:
                queue_summary['tickets_by_priority'][ticket['priority']] += 1
                queue_summary['tickets_by_category'][ticket['category']] += 1

                if ticket.get('resolution_sla_status') == 'at_risk':
                    queue_summary['sla_at_risk'] += 1
                elif ticket.get('resolution_sla_status') == 'breached':
                    queue_summary['sla_breached'] += 1

                if not ticket.get('assigned_agent'):
                    queue_summary['unassigned_tickets'] += 1

            logger.info(
                "tickets_routed",
                strategy=routing_strategy,
                tickets_routed=len(routing_results)
            )

            return {
                'status': 'success',
                'routing_strategy': routing_strategy,
                'routing_results': routing_results,
                'queue_summary': dict(queue_summary),
                'agent_utilization': [
                    {
                        'agent': a['email'],
                        'current_tickets': a['current_tickets'],
                        'capacity': max_tickets_per_agent,
                        'utilization': a['current_tickets'] / max_tickets_per_agent
                    }
                    for a in agents
                ],
                'sla_alerts': {
                    'at_risk': queue_summary['sla_at_risk'],
                    'breached': queue_summary['sla_breached'],
                    'needs_immediate_attention': queue_summary['sla_breached']
                }
            }

        except Exception as e:
            logger.error(
                "route_tickets_failed",
                strategy=routing_strategy,
                error=str(e)
            )
            return {
                'status': 'failed',
                'error': f"Failed to route tickets: {str(e)}"
            }

    @mcp.tool()
    async def manage_knowledge_base(
        ctx: Context,
        action: str = "search",
        article_id: Optional[str] = None,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        search_category: Optional[str] = None,
        status: str = "published",
        author: Optional[str] = None,
        limit: int = 10,
        include_drafts: bool = False
    ) -> Dict[str, Any]:
        """
        Process 110: Knowledge base management for self-service support.

        Manages the complete knowledge base lifecycle including article creation,
        search, categorization, and analytics. Enables customers to find solutions
        independently and reduces ticket volume.

        Actions:
        - search: Search knowledge base articles
        - create: Create new article
        - get: Get specific article by ID
        - list: List articles by category
        - recommend: Get article recommendations
        - analytics: Get KB usage analytics

        Args:
            action: Action to perform (search, create, get, list, recommend, analytics)
            article_id: Article identifier (required for get)
            title: Article title (required for create)
            summary: Brief article summary (required for create)
            content: Full article content in markdown (required for create)
            category: Primary category
            subcategory: Subcategory for organization
            tags: Tags for search and categorization
            search_query: Search query string
            search_category: Filter search by category
            status: Article status (draft, review, published, archived)
            author: Article author name
            limit: Maximum number of results to return
            include_drafts: Whether to include draft articles

        Returns:
            Knowledge base operation results with articles, search results, or analytics
        """
        try:
            await ctx.info(f"Managing knowledge base: {action}")

            # Validate action
            valid_actions = ['search', 'create', 'get', 'list', 'recommend', 'analytics']
            if action not in valid_actions:
                return {
                    'status': 'failed',
                    'error': f"Invalid action. Must be one of: {', '.join(valid_actions)}"
                }

            # SEARCH KNOWLEDGE BASE
            if action == "search":
                if not search_query:
                    return {
                        'status': 'failed',
                        'error': 'search_query is required for search action'
                    }

                # Sanitize search query
                search_query = SecurityValidator.validate_no_sql_injection(search_query)

                # Search articles (mock implementation)
                results = _search_knowledge_base(
                    query=search_query,
                    category=search_category,
                    status=status,
                    include_drafts=include_drafts,
                    limit=limit
                )

                logger.info(
                    "kb_search_performed",
                    query=search_query,
                    results_found=len(results)
                )

                return {
                    'status': 'success',
                    'search_query': search_query,
                    'results_found': len(results),
                    'articles': results,
                    'search_suggestions': _generate_search_suggestions(search_query),
                    'related_categories': _get_related_categories(results)
                }

            # CREATE ARTICLE
            elif action == "create":
                if not all([title, summary, content, category, tags, author]):
                    return {
                        'status': 'failed',
                        'error': 'Missing required fields: title, summary, content, category, tags, author'
                    }

                # Sanitize inputs
                title = SecurityValidator.validate_no_xss(title)
                summary = SecurityValidator.validate_no_xss(summary)
                content = SecurityValidator.validate_no_xss(content)

                # Generate article ID
                timestamp = int(datetime.now().timestamp())
                new_article_id = f"KB-{timestamp % 10000}"

                # Create article
                try:
                    article = KnowledgeBaseArticle(
                        article_id=new_article_id,
                        title=title,
                        summary=summary,
                        content=content,
                        category=category,
                        subcategory=subcategory,
                        tags=tags,
                        status=ArticleStatus.DRAFT,  # Start as draft
                        author=author,
                        search_keywords=_extract_keywords(title, content, tags)
                    )

                    logger.info(
                        "kb_article_created",
                        article_id=new_article_id,
                        title=title,
                        category=category
                    )

                    return {
                        'status': 'success',
                        'message': f"Article {new_article_id} created successfully",
                        'article_id': new_article_id,
                        'article': article.model_dump(),
                        'next_steps': [
                            "Article created in DRAFT status",
                            "Review and edit content as needed",
                            "Submit for review when ready",
                            "Publish to make available to customers"
                        ]
                    }

                except Exception as e:
                    return {
                        'status': 'failed',
                        'error': f"Failed to create article: {str(e)}"
                    }

            # GET ARTICLE
            elif action == "get":
                if not article_id:
                    return {
                        'status': 'failed',
                        'error': 'article_id is required for get action'
                    }

                # Get article (mock data)
                article_data = _get_mock_article(article_id)
                if not article_data:
                    return {
                        'status': 'failed',
                        'error': f'Article not found: {article_id}'
                    }

                article = KnowledgeBaseArticle(**article_data)

                # Increment view count
                article.view_count += 1

                # Get related articles
                related = _get_related_articles(article)

                logger.info("kb_article_viewed", article_id=article_id)

                return {
                    'status': 'success',
                    'article': article.model_dump(),
                    'related_articles': related,
                    'metrics': {
                        'view_count': article.view_count,
                        'helpfulness_score': article.helpfulness_score,
                        'total_votes': article.helpful_votes + article.not_helpful_votes
                    }
                }

            # LIST ARTICLES
            elif action == "list":
                # Get articles by category (mock data)
                articles = _list_articles_by_category(
                    category=category,
                    subcategory=subcategory,
                    status=status,
                    include_drafts=include_drafts,
                    limit=limit
                )

                # Group by subcategory
                grouped = defaultdict(list)
                for article in articles:
                    subcat = article.get('subcategory', 'Uncategorized')
                    grouped[subcat].append(article)

                return {
                    'status': 'success',
                    'category': category,
                    'total_articles': len(articles),
                    'articles_by_subcategory': dict(grouped),
                    'articles': articles
                }

            # RECOMMEND ARTICLES
            elif action == "recommend":
                # Get recommendations based on popular articles and user behavior
                recommendations = _get_article_recommendations(
                    category=category,
                    limit=limit
                )

                return {
                    'status': 'success',
                    'recommended_articles': recommendations,
                    'recommendation_basis': [
                        'High helpfulness scores',
                        'Frequently viewed',
                        'Recently updated',
                        'Related to common issues'
                    ]
                }

            # KB ANALYTICS
            elif action == "analytics":
                analytics = _get_kb_analytics(
                    category=category,
                    days=30
                )

                return {
                    'status': 'success',
                    'analytics': analytics,
                    'insights': _generate_kb_insights(analytics)
                }

        except Exception as e:
            logger.error(
                "manage_knowledge_base_failed",
                action=action,
                error=str(e)
            )
            return {
                'status': 'failed',
                'error': f"Failed to manage knowledge base: {str(e)}"
            }

    @mcp.tool()
    async def update_knowledge_base(
        ctx: Context,
        article_id: str,
        action: str = "update",
        title: Optional[str] = None,
        summary: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        helpful_vote: Optional[bool] = None,
        publish: bool = False,
        archive: bool = False
    ) -> Dict[str, Any]:
        """
        Process 111: Knowledge base updates and maintenance.

        Updates existing KB articles including content, metadata, status,
        and versioning. Tracks article effectiveness through voting and
        manages publication lifecycle.

        Actions:
        - update: Update article content/metadata
        - publish: Publish draft article
        - archive: Archive outdated article
        - vote: Record helpfulness vote
        - increment_version: Create new version

        Args:
            article_id: Article identifier (required)
            action: Update action (update, publish, archive, vote, increment_version)
            title: Updated article title
            summary: Updated summary
            content: Updated content
            category: Updated category
            subcategory: Updated subcategory
            tags: Updated tags
            status: Updated status (draft, review, published, archived)
            helpful_vote: True for helpful, False for not helpful
            publish: Publish the article immediately
            archive: Archive the article

        Returns:
            Update confirmation with article details, version info, and impact metrics
        """
        try:
            await ctx.info(f"Updating KB article: {article_id}")

            # Get existing article
            article_data = _get_mock_article(article_id)
            if not article_data:
                return {
                    'status': 'failed',
                    'error': f'Article not found: {article_id}'
                }

            article = KnowledgeBaseArticle(**article_data)
            changes = []

            # UPDATE CONTENT/METADATA
            if action == "update":
                if title:
                    old_title = article.title
                    article.title = SecurityValidator.validate_no_xss(title)
                    changes.append(f"title: '{old_title}' -> '{article.title}'")

                if summary:
                    article.summary = SecurityValidator.validate_no_xss(summary)
                    changes.append("summary updated")

                if content:
                    article.content = SecurityValidator.validate_no_xss(content)
                    article.version += 1  # Increment version on content change
                    changes.append(f"content updated (version {article.version})")

                if category:
                    article.category = category
                    changes.append(f"category -> {category}")

                if subcategory:
                    article.subcategory = subcategory
                    changes.append(f"subcategory -> {subcategory}")

                if tags:
                    article.tags = tags
                    article.search_keywords = _extract_keywords(article.title, article.content, tags)
                    changes.append(f"tags updated: {tags}")

                if status:
                    article.status = ArticleStatus(status)
                    changes.append(f"status -> {status}")

                article.updated_at = datetime.now()

                logger.info(
                    "kb_article_updated",
                    article_id=article_id,
                    changes=changes
                )

                return {
                    'status': 'success',
                    'message': f"Article {article_id} updated successfully",
                    'article_id': article_id,
                    'changes': changes,
                    'article': article.model_dump(),
                    'version': article.version
                }

            # PUBLISH ARTICLE
            elif action == "publish" or publish:
                if article.status == ArticleStatus.PUBLISHED:
                    return {
                        'status': 'failed',
                        'error': 'Article is already published'
                    }

                article.status = ArticleStatus.PUBLISHED
                article.published_at = datetime.now()
                article.updated_at = datetime.now()

                logger.info(
                    "kb_article_published",
                    article_id=article_id,
                    title=article.title
                )

                return {
                    'status': 'success',
                    'message': f"Article {article_id} published successfully",
                    'article_id': article_id,
                    'article': article.model_dump(),
                    'publication': {
                        'published_at': article.published_at.isoformat(),
                        'version': article.version,
                        'category': article.category
                    },
                    'distribution': [
                        "Article now visible in customer portal",
                        "Indexed for search",
                        "Added to category listing",
                        "Included in recommendations"
                    ]
                }

            # ARCHIVE ARTICLE
            elif action == "archive" or archive:
                if article.status == ArticleStatus.ARCHIVED:
                    return {
                        'status': 'failed',
                        'error': 'Article is already archived'
                    }

                old_status = article.status
                article.status = ArticleStatus.ARCHIVED
                article.updated_at = datetime.now()

                logger.info(
                    "kb_article_archived",
                    article_id=article_id,
                    title=article.title
                )

                return {
                    'status': 'success',
                    'message': f"Article {article_id} archived successfully",
                    'article_id': article_id,
                    'article': article.model_dump(),
                    'archival': {
                        'archived_at': article.updated_at.isoformat(),
                        'previous_status': old_status.value,
                        'total_views': article.view_count,
                        'helpfulness_score': article.helpfulness_score
                    },
                    'impact': [
                        "Article removed from public listings",
                        "No longer appears in search results",
                        "Historic analytics preserved",
                        "Can be restored if needed"
                    ]
                }

            # RECORD VOTE
            elif action == "vote":
                if helpful_vote is None:
                    return {
                        'status': 'failed',
                        'error': 'helpful_vote (True/False) is required for vote action'
                    }

                if helpful_vote:
                    article.helpful_votes += 1
                else:
                    article.not_helpful_votes += 1

                article.calculate_helpfulness_score()
                article.updated_at = datetime.now()

                logger.info(
                    "kb_article_vote_recorded",
                    article_id=article_id,
                    helpful=helpful_vote,
                    new_score=article.helpfulness_score
                )

                return {
                    'status': 'success',
                    'message': f"Vote recorded for article {article_id}",
                    'article_id': article_id,
                    'vote': 'helpful' if helpful_vote else 'not helpful',
                    'metrics': {
                        'helpful_votes': article.helpful_votes,
                        'not_helpful_votes': article.not_helpful_votes,
                        'total_votes': article.helpful_votes + article.not_helpful_votes,
                        'helpfulness_score': article.helpfulness_score
                    },
                    'article': article.model_dump()
                }

            # INCREMENT VERSION
            elif action == "increment_version":
                article.version += 1
                article.updated_at = datetime.now()

                logger.info(
                    "kb_article_version_incremented",
                    article_id=article_id,
                    new_version=article.version
                )

                return {
                    'status': 'success',
                    'message': f"Article {article_id} version incremented",
                    'article_id': article_id,
                    'version': article.version,
                    'article': article.model_dump()
                }

            else:
                return {
                    'status': 'failed',
                    'error': f"Invalid action: {action}"
                }

        except Exception as e:
            logger.error(
                "update_knowledge_base_failed",
                article_id=article_id,
                action=action,
                error=str(e)
            )
            return {
                'status': 'failed',
                'error': f"Failed to update knowledge base: {str(e)}"
            }

    @mcp.tool()
    async def manage_customer_portal(
        ctx: Context,
        client_id: str,
        action: str = "get_status",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        enable_feature: Optional[str] = None,
        disable_feature: Optional[str] = None,
        customize_branding: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process 112: Customer portal and self-service resource management.

        Manages the customer self-service portal including access to knowledge
        base, ticket submission, resource downloads, feature customization,
        and branding.

        Actions:
        - get_status: Get portal status and configuration
        - enable_feature: Enable portal feature
        - disable_feature: Disable portal feature
        - customize: Customize portal branding
        - list_resources: List available resources
        - get_activity: Get portal usage activity

        Args:
            client_id: Customer identifier (required)
            action: Action to perform
            resource_type: Resource type (documentation, downloads, training, api_docs)
            resource_id: Specific resource identifier
            enable_feature: Feature to enable (tickets, kb, downloads, api_access, chat)
            disable_feature: Feature to disable
            customize_branding: Branding customization (logo, colors, domain)

        Returns:
            Portal management results with configuration, features, and usage metrics
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

            await ctx.info(f"Managing customer portal for client: {client_id}")

            # GET PORTAL STATUS
            if action == "get_status":
                portal_config = _get_portal_config(client_id)

                return {
                    'status': 'success',
                    'client_id': client_id,
                    'portal': portal_config,
                    'features': {
                        'ticket_submission': portal_config['features']['tickets'],
                        'knowledge_base': portal_config['features']['kb'],
                        'downloads': portal_config['features']['downloads'],
                        'api_documentation': portal_config['features']['api_docs'],
                        'live_chat': portal_config['features']['chat']
                    },
                    'usage_stats': {
                        'monthly_logins': portal_config['usage']['monthly_logins'],
                        'tickets_submitted': portal_config['usage']['tickets_submitted'],
                        'kb_articles_viewed': portal_config['usage']['kb_views'],
                        'downloads': portal_config['usage']['downloads']
                    },
                    'customization': {
                        'custom_domain': portal_config['branding']['custom_domain'],
                        'logo_url': portal_config['branding']['logo_url'],
                        'primary_color': portal_config['branding']['primary_color']
                    }
                }

            # ENABLE FEATURE
            elif action == "enable_feature":
                if not enable_feature:
                    return {
                        'status': 'failed',
                        'error': 'enable_feature parameter required'
                    }

                valid_features = ['tickets', 'kb', 'downloads', 'api_access', 'chat']
                if enable_feature not in valid_features:
                    return {
                        'status': 'failed',
                        'error': f"Invalid feature. Must be one of: {', '.join(valid_features)}"
                    }

                logger.info(
                    "portal_feature_enabled",
                    client_id=client_id,
                    feature=enable_feature
                )

                return {
                    'status': 'success',
                    'message': f"Feature '{enable_feature}' enabled successfully",
                    'client_id': client_id,
                    'feature': enable_feature,
                    'enabled': True,
                    'next_steps': _get_feature_setup_steps(enable_feature)
                }

            # DISABLE FEATURE
            elif action == "disable_feature":
                if not disable_feature:
                    return {
                        'status': 'failed',
                        'error': 'disable_feature parameter required'
                    }

                logger.info(
                    "portal_feature_disabled",
                    client_id=client_id,
                    feature=disable_feature
                )

                return {
                    'status': 'success',
                    'message': f"Feature '{disable_feature}' disabled successfully",
                    'client_id': client_id,
                    'feature': disable_feature,
                    'enabled': False
                }

            # CUSTOMIZE BRANDING
            elif action == "customize":
                if not customize_branding:
                    return {
                        'status': 'failed',
                        'error': 'customize_branding parameter required'
                    }

                logger.info(
                    "portal_branding_customized",
                    client_id=client_id,
                    customizations=list(customize_branding.keys())
                )

                return {
                    'status': 'success',
                    'message': 'Portal branding customized successfully',
                    'client_id': client_id,
                    'branding': customize_branding,
                    'preview_url': f"https://portal.company.com/{client_id}/preview"
                }

            # LIST RESOURCES
            elif action == "list_resources":
                resources = _get_portal_resources(
                    client_id,
                    resource_type=resource_type
                )

                return {
                    'status': 'success',
                    'client_id': client_id,
                    'resource_type': resource_type or 'all',
                    'resources': resources,
                    'total_resources': len(resources)
                }

            # GET ACTIVITY
            elif action == "get_activity":
                activity = _get_portal_activity(client_id, days=30)

                return {
                    'status': 'success',
                    'client_id': client_id,
                    'period': '30 days',
                    'activity': activity,
                    'insights': {
                        'most_active_users': activity['top_users'],
                        'popular_resources': activity['popular_resources'],
                        'peak_usage_hours': activity['peak_hours'],
                        'engagement_trend': activity['trend']
                    }
                }

            else:
                return {
                    'status': 'failed',
                    'error': f"Invalid action: {action}"
                }

        except Exception as e:
            logger.error(
                "manage_customer_portal_failed",
                client_id=client_id,
                action=action,
                error=str(e)
            )
            return {
                'status': 'failed',
                'error': f"Failed to manage customer portal: {str(e)}"
            }

    @mcp.tool()
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
            await ctx.info(f"Analyzing support performance: {analysis_type}")

            # Validate client_id if provided
            if client_id:
                try:
                    client_id = validate_client_id(client_id)
                except ValidationError as e:
                    return {
                        'status': 'failed',
                        'error': f'Invalid client_id: {str(e)}'
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


# Helper Functions

def _calculate_sla_targets(priority: str) -> Dict[str, int]:
    """Calculate SLA targets based on priority level"""
    sla_matrix = {
        'P0': {'first_response': 5, 'resolution': 60},      # 5 min, 1 hour
        'P1': {'first_response': 15, 'resolution': 240},    # 15 min, 4 hours
        'P2': {'first_response': 60, 'resolution': 1440},   # 1 hour, 24 hours
        'P3': {'first_response': 240, 'resolution': 2880},  # 4 hours, 48 hours
        'P4': {'first_response': 480, 'resolution': 4320}   # 8 hours, 72 hours
    }
    return sla_matrix.get(priority, sla_matrix['P3'])


def _determine_team(category: str, priority: str) -> str:
    """Determine support team based on category and priority"""
    if priority in ['P0', 'P1']:
        return "Escalation Team"

    team_mapping = {
        'technical_issue': "Technical Support",
        'bug_report': "Engineering Support",
        'feature_request': "Product Support",
        'how_to_question': "Customer Success",
        'account_billing': "Billing Support",
        'integration_support': "Integration Team",
        'training_request': "Training Team",
        'data_issue': "Data Support",
        'performance': "Technical Support"
    }
    return team_mapping.get(category, "General Support")


def _priority_weight(priority: str) -> int:
    """Convert priority to numeric weight for sorting"""
    weights = {'P0': 5, 'P1': 4, 'P2': 3, 'P3': 2, 'P4': 1}
    return weights.get(priority, 0)


def _get_mock_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Get mock ticket data (replace with database query in production)"""
    return {
        'ticket_id': ticket_id,
        'client_id': 'cs_1696800000_acme',
        'subject': 'Unable to export reports',
        'description': 'Users getting 500 error when exporting CSV reports',
        'priority': 'P1',
        'category': 'technical_issue',
        'status': 'in_progress',
        'requester_email': 'john.smith@acme.com',
        'requester_name': 'John Smith',
        'assigned_agent': 'support@company.com',
        'assigned_team': 'Technical Support',
        'tags': ['export', 'reports', 'error'],
        'created_at': datetime.now() - timedelta(hours=2),
        'updated_at': datetime.now() - timedelta(minutes=30),
        'first_response_at': datetime.now() - timedelta(hours=1, minutes=45),
        'resolved_at': None,
        'closed_at': None,
        'sla_first_response_minutes': 15,
        'sla_resolution_minutes': 240,
        'first_response_sla_status': 'met',
        'resolution_sla_status': 'at_risk',
        'time_to_first_response_minutes': 15,
        'time_to_resolution_minutes': None,
        'satisfaction_rating': None,
        'satisfaction_comment': None,
        'escalated': False,
        'escalated_at': None,
        'escalation_reason': None,
        'resolution_notes': None,
        'internal_notes': 'Investigating with engineering',
        'customer_visible_notes': 'We are actively working on this issue'
    }


def _get_ticket_queue(
    team_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    category_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get current ticket queue (mock data)"""
    # Mock ticket queue
    tickets = [
        {
            'ticket_id': f'TKT-{1000 + i}',
            'priority': ['P0', 'P1', 'P2', 'P3', 'P4'][i % 5],
            'category': ['technical_issue', 'bug_report', 'how_to_question'][i % 3],
            'assigned_agent': None if i % 3 == 0 else f'agent{i % 5}@company.com',
            'team': _determine_team(['technical_issue', 'bug_report', 'how_to_question'][i % 3], ['P0', 'P1', 'P2', 'P3', 'P4'][i % 5]),
            'sla_resolution_minutes': 240,
            'resolution_sla_status': ['met', 'at_risk', 'breached'][i % 3],
            'sla_breach_risk': i % 3
        }
        for i in range(20)
    ]

    # Apply filters
    if team_filter:
        tickets = [t for t in tickets if t['team'] == team_filter]
    if priority_filter:
        tickets = [t for t in tickets if t['priority'] == priority_filter]
    if category_filter:
        tickets = [t for t in tickets if t['category'] == category_filter]

    return tickets


def _get_available_agents(team_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get available support agents (mock data)"""
    agents = [
        {
            'email': f'agent{i}@company.com',
            'name': f'Agent {i}',
            'team': ['Technical Support', 'Customer Success', 'Escalation Team'][i % 3],
            'current_tickets': i % 8,
            'expertise': [['technical_issue', 'bug_report'], ['how_to_question'], ['technical_issue']][i % 3],
            'seniority': 'senior' if i % 4 == 0 else 'standard',
            'status': 'available'
        }
        for i in range(10)
    ]

    if team_filter:
        agents = [a for a in agents if a['team'] == team_filter]

    return agents


def _find_best_agent(
    agents: List[Dict[str, Any]],
    ticket: Dict[str, Any],
    load_balance: bool,
    max_tickets: int
) -> Optional[Dict[str, Any]]:
    """Find best agent for ticket assignment"""
    available = [a for a in agents if a['current_tickets'] < max_tickets]

    if not available:
        return None

    # Score agents based on expertise and workload
    def score_agent(agent):
        expertise_match = 10 if ticket['category'] in agent.get('expertise', []) else 0
        workload_score = (max_tickets - agent['current_tickets']) * 2
        return expertise_match + workload_score

    return max(available, key=score_agent)


def _search_knowledge_base(
    query: str,
    category: Optional[str],
    status: str,
    include_drafts: bool,
    limit: int
) -> List[Dict[str, Any]]:
    """Search knowledge base articles (mock implementation)"""
    # Mock search results
    results = [
        {
            'article_id': f'KB-{1000 + i}',
            'title': f'How to {query} - Article {i}',
            'summary': f'Learn how to {query} efficiently',
            'category': category or 'General',
            'helpfulness_score': 0.85 - (i * 0.05),
            'view_count': 1000 - (i * 100),
            'relevance_score': 0.95 - (i * 0.1)
        }
        for i in range(min(5, limit))
    ]
    return results


def _generate_search_suggestions(query: str) -> List[str]:
    """Generate search suggestions based on query"""
    return [
        f"{query} tutorial",
        f"{query} best practices",
        f"{query} troubleshooting",
        f"advanced {query}"
    ]


def _get_related_categories(results: List[Dict[str, Any]]) -> List[str]:
    """Extract related categories from search results"""
    categories = set()
    for result in results:
        if 'category' in result:
            categories.add(result['category'])
    return list(categories)[:5]


def _extract_keywords(title: str, content: str, tags: List[str]) -> List[str]:
    """Extract search keywords from article content"""
    # Simple keyword extraction (replace with NLP in production)
    keywords = set(tags)

    # Extract words from title
    title_words = [w.lower() for w in re.findall(r'\w+', title) if len(w) > 3]
    keywords.update(title_words)

    return list(keywords)[:20]


def _get_mock_article(article_id: str) -> Optional[Dict[str, Any]]:
    """Get mock article data"""
    return {
        'article_id': article_id,
        'title': 'How to Export Reports in CSV Format',
        'summary': 'Step-by-step guide to exporting dashboard reports',
        'content': '# Export Reports\n\n1. Navigate to Reports\n2. Click Export...',
        'category': 'Reports & Analytics',
        'subcategory': 'Data Export',
        'tags': ['export', 'reports', 'csv'],
        'status': 'published',
        'author': 'Support Team',
        'created_at': datetime.now() - timedelta(days=90),
        'updated_at': datetime.now() - timedelta(days=10),
        'published_at': datetime.now() - timedelta(days=85),
        'version': 3,
        'view_count': 1247,
        'helpful_votes': 183,
        'not_helpful_votes': 12,
        'helpfulness_score': 0.94,
        'related_articles': ['KB-1002', 'KB-1003'],
        'search_keywords': ['export', 'csv', 'download', 'reports'],
        'customer_facing': True,
        'requires_authentication': False,
        'product_tier_restrictions': []
    }


def _get_related_articles(article: KnowledgeBaseArticle) -> List[Dict[str, Any]]:
    """Get related articles based on category and tags"""
    return [
        {
            'article_id': f'KB-{1000 + i}',
            'title': f'Related: {article.category} Article {i}',
            'helpfulness_score': 0.9 - (i * 0.1)
        }
        for i in range(3)
    ]


def _list_articles_by_category(
    category: Optional[str],
    subcategory: Optional[str],
    status: str,
    include_drafts: bool,
    limit: int
) -> List[Dict[str, Any]]:
    """List articles by category"""
    return [
        {
            'article_id': f'KB-{1000 + i}',
            'title': f'Article {i} in {category}',
            'category': category or 'General',
            'subcategory': subcategory or 'General',
            'status': status,
            'view_count': 1000 - (i * 50)
        }
        for i in range(min(10, limit))
    ]


def _get_article_recommendations(category: Optional[str], limit: int) -> List[Dict[str, Any]]:
    """Get article recommendations"""
    return [
        {
            'article_id': f'KB-{2000 + i}',
            'title': f'Recommended Article {i}',
            'category': category or 'Popular',
            'helpfulness_score': 0.95 - (i * 0.05),
            'view_count': 5000 - (i * 500),
            'recommendation_score': 0.9 - (i * 0.1)
        }
        for i in range(limit)
    ]


def _get_kb_analytics(category: Optional[str], days: int) -> Dict[str, Any]:
    """Get knowledge base analytics"""
    return {
        'total_articles': 247,
        'published_articles': 198,
        'total_views': 18473,
        'avg_helpfulness': 0.87,
        'search_queries': 5284,
        'top_categories': [
            {'name': 'Reports', 'views': 4200},
            {'name': 'Integration', 'views': 3100},
            {'name': 'Getting Started', 'views': 2800}
        ],
        'top_articles': [
            {'article_id': 'KB-1001', 'title': 'Export Reports', 'views': 1247},
            {'article_id': 'KB-1002', 'title': 'API Authentication', 'views': 982}
        ]
    }


def _generate_kb_insights(analytics: Dict[str, Any]) -> List[str]:
    """Generate insights from KB analytics"""
    return [
        f"Knowledge base has {analytics['total_articles']} articles with {analytics['avg_helpfulness']:.0%} average helpfulness",
        f"Top category '{analytics['top_categories'][0]['name']}' accounts for {analytics['top_categories'][0]['views'] / analytics['total_views']:.0%} of views",
        "Consider creating more articles in popular categories"
    ]


def _get_portal_config(client_id: str) -> Dict[str, Any]:
    """Get portal configuration for client"""
    return {
        'portal_url': f'https://portal.company.com/{client_id}',
        'enabled': True,
        'features': {
            'tickets': True,
            'kb': True,
            'downloads': True,
            'api_docs': True,
            'chat': False
        },
        'branding': {
            'custom_domain': None,
            'logo_url': None,
            'primary_color': '#0066CC'
        },
        'usage': {
            'monthly_logins': 487,
            'tickets_submitted': 23,
            'kb_views': 1847,
            'downloads': 94
        }
    }


def _get_feature_setup_steps(feature: str) -> List[str]:
    """Get setup steps for enabling a feature"""
    steps = {
        'tickets': [
            "Configure ticket submission form",
            "Set up email notifications",
            "Train users on ticket system"
        ],
        'kb': [
            "Publish initial articles",
            "Configure search settings",
            "Enable customer feedback"
        ],
        'chat': [
            "Configure chat widget",
            "Set business hours",
            "Assign chat agents"
        ]
    }
    return steps.get(feature, ["Feature is now enabled"])


def _get_portal_resources(client_id: str, resource_type: Optional[str]) -> List[Dict[str, Any]]:
    """Get portal resources"""
    resources = [
        {
            'resource_id': f'RES-{1000 + i}',
            'type': ['documentation', 'downloads', 'training'][i % 3],
            'title': f'Resource {i}',
            'description': f'Description for resource {i}',
            'url': f'https://portal.company.com/resources/{i}',
            'downloads': 100 - (i * 10)
        }
        for i in range(15)
    ]

    if resource_type:
        resources = [r for r in resources if r['type'] == resource_type]

    return resources


def _get_portal_activity(client_id: str, days: int) -> Dict[str, Any]:
    """Get portal activity metrics"""
    return {
        'total_sessions': 487,
        'unique_users': 42,
        'avg_session_duration': 8.5,
        'top_users': [
            {'email': 'john@acme.com', 'sessions': 24},
            {'email': 'jane@acme.com', 'sessions': 18}
        ],
        'popular_resources': [
            {'title': 'API Documentation', 'views': 156},
            {'title': 'Getting Started Guide', 'views': 98}
        ],
        'peak_hours': ['10:00-11:00', '14:00-15:00'],
        'trend': 'increasing'
    }


def _calculate_support_metrics(
    client_id: Optional[str],
    period_start: datetime,
    period_end: datetime,
    team_filter: Optional[str] = None,
    agent_filter: Optional[str] = None
) -> Dict[str, Any]:
    """Calculate comprehensive support metrics"""
    return {
        'total_tickets': 47,
        'tickets_opened': 47,
        'tickets_resolved': 42,
        'tickets_closed': 38,
        'open_tickets': 5,
        'avg_first_response_minutes': 11.2,
        'avg_resolution_minutes': 187.5,
        'sla_compliance': 0.89,
        'first_response_sla_met': 0.96,
        'resolution_sla_met': 0.89,
        'avg_satisfaction': 4.4,
        'satisfaction_response_rate': 0.78,
        'escalation_rate': 0.064,
        'deflection_rate': 0.31,
        'tickets_by_priority': {'P0': 1, 'P1': 8, 'P2': 18, 'P3': 15, 'P4': 5},
        'tickets_by_category': {
            'technical_issue': 22,
            'how_to_question': 12,
            'bug_report': 8,
            'feature_request': 5
        }
    }


def _calculate_trends(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate metric trends"""
    return {
        'ticket_volume': {'trend': 'increasing', 'change': 0.12},
        'sla_compliance': {'trend': 'stable', 'change': -0.02},
        'satisfaction': {'trend': 'improving', 'change': 0.08}
    }


def _generate_recommendations(metrics: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on metrics"""
    recommendations = []

    if metrics['sla_compliance'] < 0.9:
        recommendations.append("SLA compliance is below 90%. Consider increasing support capacity or optimizing routing.")

    if metrics['avg_satisfaction'] < 4.0:
        recommendations.append("Customer satisfaction is below target. Review ticket resolutions and agent training.")

    if metrics['deflection_rate'] < 0.25:
        recommendations.append("KB deflection rate is low. Improve knowledge base content and visibility.")

    if metrics['escalation_rate'] > 0.1:
        recommendations.append("Escalation rate is high. Provide additional training to L1 support team.")

    if not recommendations:
        recommendations.append("Support performance is strong. Maintain current practices.")

    return recommendations


def _analyze_sla_performance(
    client_id: Optional[str],
    period_start: datetime,
    period_end: datetime,
    priority_filter: Optional[str]
) -> Dict[str, Any]:
    """Analyze SLA performance"""
    return {
        'avg_first_response': 11.2,
        'avg_resolution': 187.5,
        'first_response_compliance': 0.96,
        'resolution_compliance': 0.89,
        'first_response_breaches': 2,
        'resolution_breaches': 5,
        'by_priority': {
            'P0': {'compliance': 1.0, 'avg_resolution': 45},
            'P1': {'compliance': 0.88, 'avg_resolution': 220},
            'P2': {'compliance': 0.92, 'avg_resolution': 890},
            'P3': {'compliance': 0.85, 'avg_resolution': 2100}
        },
        'at_risk_tickets': 3
    }


def _identify_sla_issues(sla_data: Dict[str, Any]) -> List[str]:
    """Identify critical SLA issues"""
    issues = []

    if sla_data['first_response_breaches'] > 5:
        issues.append(f"High first response breaches: {sla_data['first_response_breaches']}")

    if sla_data['resolution_breaches'] > 10:
        issues.append(f"High resolution breaches: {sla_data['resolution_breaches']}")

    if sla_data['at_risk_tickets'] > 5:
        issues.append(f"{sla_data['at_risk_tickets']} tickets currently at risk of SLA breach")

    return issues


def _analyze_agent_performance(
    period_start: datetime,
    period_end: datetime,
    team_filter: Optional[str],
    agent_filter: Optional[str]
) -> Dict[str, Any]:
    """Analyze agent performance"""
    agents = [
        {
            'email': f'agent{i}@company.com',
            'tickets_resolved': 20 - i,
            'avg_resolution_time': 180 + (i * 30),
            'satisfaction': 4.5 - (i * 0.1),
            'sla_compliance': 0.95 - (i * 0.05)
        }
        for i in range(10)
    ]

    return {
        'agents': agents,
        'avg_tickets': 15,
        'avg_satisfaction': 4.3,
        'top_performers': sorted(agents, key=lambda a: a['satisfaction'], reverse=True),
        'needs_support': [a for a in agents if a['sla_compliance'] < 0.85],
        'workload_dist': {'balanced': 7, 'overloaded': 2, 'underutilized': 1}
    }


def _generate_agent_insights(agent_stats: Dict[str, Any]) -> List[str]:
    """Generate insights from agent performance"""
    return [
        f"Top performer: {agent_stats['top_performers'][0]['email']} with {agent_stats['top_performers'][0]['satisfaction']:.1f} satisfaction",
        f"{len(agent_stats['needs_support'])} agents need additional support",
        "Workload is generally well-balanced across team"
    ]


def _analyze_satisfaction(
    client_id: Optional[str],
    period_start: datetime,
    period_end: datetime
) -> Dict[str, Any]:
    """Analyze customer satisfaction"""
    return {
        'avg_rating': 4.4,
        'response_rate': 0.78,
        'distribution': {
            '5': 28,
            '4': 16,
            '3': 4,
            '2': 1,
            '1': 0
        },
        'nps_score': 68,
        'positive_count': 44,
        'negative_count': 5,
        'themes': ['quick resolution', 'helpful agents', 'clear communication'],
        'time_correlation': -0.65,  # Negative correlation: faster = better
        'priority_correlation': {'P1': 4.2, 'P2': 4.5, 'P3': 4.6}
    }


def _generate_satisfaction_actions(satisfaction_data: Dict[str, Any]) -> List[str]:
    """Generate action items from satisfaction analysis"""
    actions = []

    if satisfaction_data['response_rate'] < 0.8:
        actions.append("Increase satisfaction survey response rate through better timing and incentives")

    if satisfaction_data['avg_rating'] < 4.0:
        actions.append("Address negative feedback themes to improve ratings")

    negative_pct = satisfaction_data['negative_count'] / (satisfaction_data['positive_count'] + satisfaction_data['negative_count'])
    if negative_pct > 0.15:
        actions.append("Review and address negative feedback - significant dissatisfaction detected")

    return actions or ["Satisfaction is strong - maintain current service levels"]


def _analyze_kb_effectiveness(
    period_start: datetime,
    period_end: datetime
) -> Dict[str, Any]:
    """Analyze knowledge base effectiveness"""
    return {
        'total_articles': 247,
        'total_views': 18473,
        'avg_helpfulness': 0.87,
        'search_count': 5284,
        'deflection_rate': 0.31,
        'self_service_ratio': 0.45,
        'tickets_deflected': 89,
        'top_articles': [
            {'article_id': 'KB-1001', 'title': 'Export Reports', 'views': 1247, 'helpfulness': 0.94},
            {'article_id': 'KB-1002', 'title': 'API Auth', 'views': 982, 'helpfulness': 0.91}
        ],
        'low_performing': [
            {'article_id': 'KB-1099', 'title': 'Legacy Feature', 'views': 12, 'helpfulness': 0.42}
        ],
        'search_gaps': ['bulk import', 'data migration', 'webhook setup']
    }


def _analyze_support_trends(
    client_id: Optional[str],
    period_days: int
) -> Dict[str, Any]:
    """Analyze support trends over time"""
    return {
        'volume_trend': {'direction': 'increasing', 'rate': 0.12},
        'sla_trend': {'direction': 'stable', 'rate': -0.02},
        'satisfaction_trend': {'direction': 'improving', 'rate': 0.08},
        'resolution_trend': {'direction': 'improving', 'rate': -0.15},
        'seasonality': {
            'peak_days': ['Monday', 'Tuesday'],
            'peak_hours': ['10:00-12:00', '14:00-16:00']
        },
        'forecast': {
            'tickets': 52,
            'avg_satisfaction': 4.5
        },
        'forecast_confidence': 0.82
    }


def _interpret_trends(trends: Dict[str, Any]) -> List[str]:
    """Interpret trend data"""
    insights = []

    if trends['volume_trend']['direction'] == 'increasing':
        insights.append(f"Ticket volume trending up {trends['volume_trend']['rate']:.0%} - plan capacity accordingly")

    if trends['satisfaction_trend']['direction'] == 'improving':
        insights.append("Customer satisfaction improving - current initiatives are working")

    insights.append(f"Peak support times: {', '.join(trends['seasonality']['peak_hours'])}")

    return insights


def _compare_metrics(
    current: Dict[str, Any],
    previous: Dict[str, Any]
) -> Dict[str, Any]:
    """Compare current vs previous metrics"""
    comparison = {
        'ticket_volume': {
            'current': current['total_tickets'],
            'previous': previous['total_tickets'],
            'change': (current['total_tickets'] - previous['total_tickets']) / previous['total_tickets']
        },
        'sla_compliance': {
            'current': current['sla_compliance'],
            'previous': previous['sla_compliance'],
            'change': current['sla_compliance'] - previous['sla_compliance']
        },
        'satisfaction': {
            'current': current['avg_satisfaction'],
            'previous': previous['avg_satisfaction'],
            'change': current['avg_satisfaction'] - previous['avg_satisfaction']
        }
    }

    comparison['improvements'] = [
        k for k, v in comparison.items()
        if v['change'] > 0 and k != 'ticket_volume'
    ]

    comparison['declines'] = [
        k for k, v in comparison.items()
        if v['change'] < 0 and k != 'ticket_volume'
    ]

    return comparison


def _generate_comparison_summary(comparison: Dict[str, Any]) -> str:
    """Generate summary from comparison"""
    improvements = len(comparison['improvements'])
    declines = len(comparison['declines'])

    if improvements > declines:
        return f"Performance improving: {improvements} metrics up, {declines} down"
    elif declines > improvements:
        return f"Performance declining: {declines} metrics down, {improvements} up"
    else:
        return "Performance stable: mixed changes across metrics"
