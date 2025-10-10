"""
Agent Integration Module

This module provides the integration layer between the adaptive agent system
and the existing MCP server tools. It includes:

- Routing middleware decorator for automatic data source routing
- Learning question generation and processing
- Tool result enhancement with confidence reporting
- Process execution tracking and optimization
"""

import asyncio
import functools
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple
from pathlib import Path

import structlog
from mcp.server.fastmcp import Context

from .adaptive_agent import (
    DataSourceRegistry,
    DataSourceDiscovery,
    AgentMemory,
    UnifiedDataClient,
    ConfidenceAssessment
)

logger = structlog.get_logger(__name__)


class AdaptiveSalesAgent:
    """Main agent orchestrator that coordinates all adaptive capabilities"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.discovery = DataSourceDiscovery(config_path)
        self._client_memories = {}  # Cache of AgentMemory instances per client
        self._last_processes = {}   # Track process sequences per client
        
    def get_memory(self, client_id: str) -> AgentMemory:
        """Get or create memory instance for client"""
        if client_id not in self._client_memories:
            self._client_memories[client_id] = AgentMemory(client_id, self.config_path)
        return self._client_memories[client_id]
    
    def get_unified_client(self, client_id: str) -> UnifiedDataClient:
        """Get unified data client for client"""
        memory = self.get_memory(client_id)
        return UnifiedDataClient(self.discovery, memory)
    
    async def execute_process_with_intelligence(
        self, 
        process_num: int, 
        client_id: str,
        business_function: str,
        process_func: Callable,
        ctx: Context,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a process with full adaptive intelligence
        This is the main entry point for intelligent process execution
        """
        start_time = time.time()
        
        # Get memory and track process sequence
        memory = self.get_memory(client_id)
        self._track_process_sequence(client_id, process_num)
        
        # Get unified data client
        data_client = self.get_unified_client(client_id)
        
        # Load relevant memory for this task
        task_memory = memory.get_relevant_memory(process_num, business_function)
        
        try:
            await ctx.info(f"Executing Process {process_num} with adaptive intelligence")
            
            # Discover available data sources
            available_sources = self.discovery.discover_available_sources(business_function)
            
            # Execute the process function with enhanced context
            enhanced_kwargs = {
                **kwargs,
                'adaptive_context': {
                    'available_sources': available_sources,
                    'task_memory': task_memory,
                    'data_client': data_client,
                    'client_id': client_id
                }
            }
            
            # Execute the actual process
            result = await process_func(ctx, **enhanced_kwargs)
            
            # Assess confidence and generate intelligent reporting
            confidence_report = ConfidenceAssessment.assess_confidence(
                result, available_sources, task_memory, business_function
            )
            
            # Enhance result with intelligence
            enhanced_result = self._enhance_result_with_intelligence(
                result, confidence_report, available_sources, process_num, business_function
            )
            
            # Update performance tracking
            execution_time = time.time() - start_time
            primary_source = available_sources.get('priority_source', 'unknown')
            memory.update_performance(
                primary_source, 
                True,  # Success if we got here
                confidence_report['confidence_score'],
                execution_time,
                business_function
            )
            
            await ctx.info(f"Process {process_num} completed with {confidence_report['completion_estimate']} confidence")
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error in intelligent process execution: {e}")
            
            # Still try to provide intelligent error reporting
            error_result = {
                'status': 'error',
                'error': str(e),
                'process_num': process_num,
                'execution_time': time.time() - start_time
            }
            
            # Add basic intelligence even to errors
            available_sources = self.discovery.discover_available_sources(business_function)
            confidence_report = ConfidenceAssessment.assess_confidence(
                {}, available_sources, task_memory, business_function
            )
            
            error_result.update({
                'adaptive_feedback': {
                    'what_went_wrong': f'Process {process_num} encountered an error during execution',
                    'suggestions': [
                        'Check if required data sources are properly configured',
                        'Verify network connectivity for API calls',
                        'Review process parameters for validity'
                    ],
                    'available_alternatives': self._suggest_alternative_processes(process_num, business_function)
                }
            })
            
            return error_result
    
    def _enhance_result_with_intelligence(
        self, 
        original_result: Dict[str, Any], 
        confidence_report: Dict[str, Any], 
        available_sources: Dict[str, Any],
        process_num: int,
        business_function: str
    ) -> Dict[str, Any]:
        """Enhance process result with adaptive intelligence"""
        
        enhanced_result = original_result.copy() if original_result else {}
        
        # Add adaptive feedback section based on user's detail preference
        user_preferences = self.get_memory(client_id).get_relevant_memory(process_num, business_function).get('user_preferences', {})
        detail_level = user_preferences.get('response_detail_level', 'standard')
        
        # Always include basic completion info
        adaptive_feedback = {
            'completion_estimate': confidence_report['completion_estimate'],
            'confidence_score': confidence_report['confidence_score']
        }
        
        # Add detail based on preference
        if detail_level in ['standard', 'comprehensive']:
            adaptive_feedback.update({
                'what_worked': confidence_report['what_worked'],
                'what_didnt': confidence_report['what_didnt'],
                'data_sources_used': confidence_report['data_sources_used']
            })
        
        if detail_level == 'comprehensive':
            adaptive_feedback.update({
                'suggestions': confidence_report['suggestions'],
                'confidence_factors': confidence_report.get('factors', {}),
                'execution_details': {
                    'business_function': business_function,
                    'process_number': process_num,
                    'timestamp': datetime.now().isoformat()
                }
            })
        elif detail_level == 'standard':
            adaptive_feedback['suggestions'] = confidence_report['suggestions']
        
        enhanced_result['adaptive_feedback'] = adaptive_feedback
        
        # Add learning question if confidence is low and user preferences allow it
        completion_threshold = user_preferences.get('completion_threshold', 0.70)
        learning_frequency = user_preferences.get('learning_frequency', 'often')
        
        should_ask_question = (
            confidence_report['confidence_score'] < completion_threshold and
            self._should_ask_learning_question(learning_frequency)
        )
        
        if should_ask_question:
            learning_question = self._generate_learning_question(
                confidence_report, business_function, process_num, available_sources
            )
            if learning_question:
                enhanced_result['adaptive_feedback']['learning_question'] = learning_question
                enhanced_result['adaptive_feedback']['learning_context'] = {
                    'process_num': process_num,
                    'business_function': business_function,
                    'timestamp': datetime.now().isoformat(),
                    'client_id': client_id
                }
        
        # Add related process suggestions based on collaboration mode
        collaboration_mode = user_preferences.get('collaboration_mode', 'suggest')
        if collaboration_mode in ['suggest', 'auto_related']:
            related_processes = self._suggest_related_processes(process_num, business_function)
            if related_processes:
                enhanced_result['adaptive_feedback']['related_processes'] = related_processes
                
                if collaboration_mode == 'auto_related':
                    enhanced_result['adaptive_feedback']['auto_prepare_message'] = (
                        "Based on your preferences, I'm preparing these related processes. "
                        "They'll be ready if you need them."
                    )
        
        # Add optimization suggestions if user wants them
        auto_suggestions = user_preferences.get('auto_suggestions', True)
        if auto_suggestions:
            optimizations = self._suggest_optimizations(available_sources, confidence_report, business_function)
            if optimizations:
                enhanced_result['adaptive_feedback']['optimizations'] = optimizations
        
        return enhanced_result
    
    def _should_ask_learning_question(self, learning_frequency: str) -> bool:
        """Determine if we should ask a learning question based on user preferences"""
        import random
        
        frequency_thresholds = {
            'always': 1.0,    # Always ask
            'often': 0.8,     # Ask 80% of the time
            'occasionally': 0.4,  # Ask 40% of the time  
            'rarely': 0.1     # Ask 10% of the time
        }
        
        threshold = frequency_thresholds.get(learning_frequency, 0.8)
        return random.random() < threshold
    
    def _generate_learning_question(
        self, 
        confidence_report: Dict[str, Any], 
        business_function: str, 
        process_num: int,
        available_sources: Dict[str, Any]
    ) -> Optional[str]:
        """Generate contextual learning question based on confidence assessment"""
        
        factors = confidence_report.get('factors', {})
        
        # Low data source quality
        if factors.get('data_source', 1.0) < 0.7:
            if available_sources.get('priority_source') == 'web_search':
                return (f"I had to use web search for Process {process_num} which gave limited results. "
                       f"For {business_function} tasks, do you typically prioritize data accuracy, "
                       f"speed, or comprehensiveness? This helps me choose better fallback strategies.")
        
        # Low completeness
        if factors.get('completeness', 1.0) < 0.7:
            return (f"I got partial results for this {business_function} analysis. "
                   f"What are the most critical data points you need for Process {process_num} "
                   f"to be useful? This helps me focus on what matters most when data is limited.")
        
        # Low freshness
        if factors.get('freshness', 1.0) < 0.6:
            return (f"Some of the {business_function} data I found seems outdated. "
                   f"How current does information need to be for Process {process_num} decisions? "
                   f"Should I prioritize newer data even if it's less complete?")
        
        # Poor historical performance
        if factors.get('historical', 1.0) < 0.6:
            return (f"This approach for Process {process_num} has had mixed results before. "
                   f"Would you prefer me to try alternative methods even if they take longer, "
                   f"or is speed more important than perfect accuracy for {business_function}?")
        
        return None
    
    def _suggest_related_processes(self, process_num: int, business_function: str) -> List[Dict[str, Any]]:
        """Suggest related processes that might be useful"""
        
        # Define process relationships based on business logic
        process_relationships = {
            38: [39, 41, 44],  # Prospect discovery -> enrichment, qualification, outreach
            31: [32, 33, 34],  # Annual planning -> territory, quota, hiring
            46: [47, 48],      # CRM setup -> data cleanup, migration
            53: [54, 55],      # Email campaigns -> follow-up, tracking
            # Add more relationships as needed
        }
        
        related = process_relationships.get(process_num, [])
        if not related:
            return []
        
        suggestions = []
        for related_num in related[:3]:  # Limit to top 3 suggestions
            suggestions.append({
                'process_number': related_num,
                'description': f'Process {related_num} often follows Process {process_num}',
                'business_value': f'Enhances {business_function} workflow'
            })
        
        return suggestions
    
    def _suggest_alternative_processes(self, process_num: int, business_function: str) -> List[str]:
        """Suggest alternative processes when primary fails"""
        
        # Define alternative processes for common failures
        alternatives = {
            38: ['Process 39 (Individual Prospect Research) for targeted analysis',
                'Process 44 (Manual Research) as comprehensive backup'],
            31: ['Process 32 (Territory Planning) for focused approach',
                'Process 74 (Performance Analysis) to inform planning'],
        }
        
        return alternatives.get(process_num, [
            f'Review Process {process_num} parameters and try again',
            'Check configuration for required data sources'
        ])
    
    def _suggest_optimizations(
        self, 
        available_sources: Dict[str, Any], 
        confidence_report: Dict[str, Any],
        business_function: str
    ) -> List[str]:
        """Suggest optimizations based on current performance"""
        
        optimizations = []
        
        # Source-based optimizations
        if available_sources.get('priority_source') == 'web_search':
            api_keys = available_sources.get('api_keys', {})
            missing_apis = [k for k, v in api_keys.items() if not v]
            if missing_apis:
                optimizations.append(
                    f"Configure {missing_apis[0]} API key for better {business_function} data quality"
                )
        
        # Performance-based optimizations
        if confidence_report['confidence_score'] < 0.8:
            optimizations.append(
                f"Consider adding specialized data sources for {business_function} tasks"
            )
        
        return optimizations
    
    def _track_process_sequence(self, client_id: str, process_num: int):
        """Track process sequences for workflow pattern analysis"""
        if client_id not in self._last_processes:
            self._last_processes[client_id] = []
        
        sequence = self._last_processes[client_id]
        sequence.append(process_num)
        
        # Keep last 5 processes
        if len(sequence) > 5:
            sequence.pop(0)
        
        # Record patterns of 2+ processes
        if len(sequence) >= 2:
            memory = self.get_memory(client_id)
            memory.record_workflow_pattern(sequence[-2:])  # Record pairs
            
        # Record longer sequences periodically
        if len(sequence) >= 3:
            memory = self.get_memory(client_id)
            memory.record_workflow_pattern(sequence[-3:])  # Record triplets
    
    async def process_learning_feedback(
        self, 
        client_id: str, 
        feedback: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process learning feedback from user"""
        
        memory = self.get_memory(client_id)
        
        # Extract context information
        process_num = context.get('process_num')
        business_function = context.get('business_function', 'general')
        timestamp = context.get('timestamp', datetime.now().isoformat())
        
        # Create learning key
        learning_key = f"{business_function}_{process_num}_{int(time.time())}"
        
        # Update memory with learning
        memory.update_learning(learning_key, feedback, context)
        
        logger.info(f"Processed learning feedback for client {client_id}: {learning_key}")
        
        return {
            'status': 'success',
            'message': "Thanks! I'll remember this for future similar tasks.",
            'learning_key': learning_key,
            'applied_to': f"Process {process_num} and similar {business_function} tasks"
        }


def route_data_source(business_function: str):
    """
    Decorator for automatic data source routing and intelligent enhancement
    This decorator wraps process functions to provide adaptive capabilities
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(ctx: Context, *args, **kwargs) -> Dict[str, Any]:
            # Extract client_id from kwargs (should be first parameter of all process functions)
            client_id = kwargs.get('client_id', 'default_client')
            
            # Get process number from function name if available
            process_num = 0
            if hasattr(func, '__name__'):
                # Try to extract process number from function name
                import re
                match = re.search(r'(\d+)', func.__name__)
                if match:
                    process_num = int(match.group(1))
            
            # Get global agent instance 
            agent = getattr(wrapper, '_adaptive_agent', None)
            if not agent:
                # Try to get from global module
                import sys
                current_module = sys.modules[__name__]
                agent = getattr(current_module, 'GLOBAL_AGENT', None)
            
            if not agent:
                # Fallback to direct execution if no agent available
                logger.warning("No adaptive agent available, executing function directly")
                return await func(ctx, *args, **kwargs)
            
            # Execute with full intelligence
            return await agent.execute_process_with_intelligence(
                process_num, client_id, business_function, func, ctx, **kwargs
            )
            
        return wrapper
    return decorator


# Convenience decorators for common business functions
def crm_function(func: Callable) -> Callable:
    """Decorator for CRM-related functions"""
    return route_data_source('crm')(func)

def prospect_discovery(func: Callable) -> Callable:
    """Decorator for prospect discovery functions"""  
    return route_data_source('prospect_discovery')(func)

def email_outreach(func: Callable) -> Callable:
    """Decorator for email outreach functions"""
    return route_data_source('email_outreach')(func)

def market_research(func: Callable) -> Callable:
    """Decorator for market research functions"""
    return route_data_source('market_research')(func)

def analytics(func: Callable) -> Callable:
    """Decorator for analytics functions"""
    return route_data_source('analytics')(func)

def scheduling(func: Callable) -> Callable:
    """Decorator for scheduling functions"""
    return route_data_source('scheduling')(func)

def document_management(func: Callable) -> Callable:
    """Decorator for document management functions"""
    return route_data_source('document_management')(func)

def conversation_intelligence(func: Callable) -> Callable:
    """Decorator for conversation intelligence functions"""
    return route_data_source('conversation_intelligence')(func)


# Helper function to create learning feedback tools
def create_learning_feedback_tool(agent: AdaptiveSalesAgent):
    """Create the learning feedback tool function"""
    
    async def provide_learning_feedback(
        ctx: Context,
        client_id: str,
        feedback: str,
        process_num: int,
        business_function: str = 'general'
    ) -> Dict[str, Any]:
        """
        Process learning feedback to improve future performance
        
        Args:
            client_id: Client identifier
            feedback: User feedback about preferences or requirements
            process_num: Process number this feedback relates to  
            business_function: Type of business function (optional)
        
        Returns:
            Confirmation of learning update
        """
        context = {
            'process_num': process_num,
            'business_function': business_function,
            'timestamp': datetime.now().isoformat()
        }
        
        result = await agent.process_learning_feedback(client_id, feedback, context)
        
        await ctx.info(f"Learning feedback processed for Process {process_num}")
        
        return result
    
    return provide_learning_feedback


# Helper function to inject agent into context
def setup_agent_context(mcp_server, config_path: Path):
    """Setup adaptive agent and inject into MCP server context"""
    
    agent = AdaptiveSalesAgent(config_path)
    
    # Store agent globally for access in decorators
    # This is a workaround since decorators are applied at module load time
    import sys
    current_module = sys.modules[__name__]
    setattr(current_module, 'GLOBAL_AGENT', agent)
    
    # Also inject into server.py module if available
    try:
        import server
        setattr(server, 'GLOBAL_AGENT', agent)
    except ImportError:
        pass
    
    # Create and register learning feedback tool
    learning_tool = create_learning_feedback_tool(agent)
    
    return agent, learning_tool