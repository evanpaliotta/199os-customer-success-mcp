"""
route_tickets - Process 109: Intelligent ticket routing and prioritization

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

from fastmcp import Context
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re
import structlog
from src.models.support_models import (
from src.decorators import mcp_tool
from src.composio import get_composio_client
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
