"""
Enhanced Agent System Integration

This module integrates all the new UX features:
- Natural language processing
- Intelligent caching
- Conversation context
- HTML dashboard generation
- Smart rate limiting
- Workflow automation

This creates a complete intelligent sales operations system.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import structlog

from src.intelligence.natural_language_processor import NaturalLanguageProcessor, IntentRouter
from src.utils.cache_manager import IntelligentCacheManager
from src.intelligence.conversation_context import ConversationContextManager
from src.utils.dashboard_generator import DashboardGenerator
from .adaptive_agent import AgentMemory
from .agent_integration import AdaptiveSalesAgent

logger = structlog.get_logger(__name__)

class EnhancedSalesAgent:
    """
    Enhanced sales agent with natural language interface,
    intelligent caching, and conversation context
    """
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        
        # Initialize all subsystems
        self.nlp = NaturalLanguageProcessor(config_path)
        self.intent_router = IntentRouter(self.nlp)
        self.cache_manager = IntelligentCacheManager(config_path / "cache")
        self.context_manager = ConversationContextManager(config_path)
        self.dashboard_generator = DashboardGenerator(config_path)
        self.adaptive_agent = AdaptiveSalesAgent(config_path)
        
        # Performance tracking
        self.performance_data = {
            'process_executions': [],
            'confidence_history': [],
            'learning_events': [],
            'cost_tracking': {},
            'cache_usage': [],
        }
        
        logger.info("Enhanced Sales Agent initialized with all subsystems")
    
    async def process_natural_language_request(self, client_id: str, request: str) -> Dict[str, Any]:
        """
        Process a natural language request and execute appropriate processes
        
        This is the main entry point for natural language interactions
        """
        logger.info(f"Processing NL request from {client_id}: {request}")
        
        # Get or create conversation session
        session = self.context_manager.get_or_create_session(client_id)
        
        try:
            # Route the request to appropriate processes
            routing_result = self.intent_router.route_request(request)
            
            # Check if confirmation is needed
            if routing_result.get('requires_confirmation'):
                return {
                    'status': 'confirmation_required',
                    'confirmation_dialog': routing_result['confirmation_dialog'],
                    'routing_result': routing_result,
                    'session_id': session.session_id
                }
            
            # Execute the processes
            execution_result = await self._execute_routing_result(
                client_id, session.session_id, routing_result
            )
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Error processing NL request: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'suggestion': 'Try rephrasing your request or being more specific'
            }
    
    async def _execute_routing_result(self, client_id: str, session_id: str, 
                                    routing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the processes identified by natural language routing"""
        
        processes = routing_result['intent']['processes']
        parameters = routing_result['intent']['parameters']
        rate_limit = routing_result.get('rate_limit')
        
        # Update conversation context
        self.context_manager.update_context(
            session_id, processes, parameters, 
            routing_result['intent']['original_request']
        )
        
        results = []
        
        for process_num in processes:
            # Check cache first
            should_use_cache, cache_entry, cache_reason = self.cache_manager.should_use_cache(
                f"process_{process_num}",
                parameters,
                ['nlp_triggered'],
                routing_result['intent']['original_request']
            )
            
            if should_use_cache and cache_entry:
                # Use cached result
                result = cache_entry.data.copy()
                result['adaptive_feedback'] = {
                    'cache_used': True,
                    'cache_info': self.cache_manager.create_usage_report(cache_entry),
                    'completion_estimate': 'Instant (cached)'
                }
                
                logger.info(f"Used cached data for Process {process_num}: {cache_reason}")
                
            else:
                # Execute process with adaptive agent
                if rate_limit:
                    parameters['rate_limit'] = rate_limit
                
                # This would call the actual process function
                # For now, we'll simulate with the adaptive agent
                result = await self._simulate_process_execution(
                    client_id, process_num, parameters
                )
                
                # Cache the result if it's worth caching
                if result.get('adaptive_feedback', {}).get('confidence_score', 0) > 0.6:
                    self.cache_manager.store_data(
                        f"process_{process_num}",
                        parameters,
                        ['process_execution'],
                        result,
                        result.get('adaptive_feedback', {}).get('confidence_score', 0.8)
                    )
            
            # Add process result to context
            self.context_manager.add_process_result(
                session_id, process_num, f"Process {process_num}",
                parameters, result,
                result.get('adaptive_feedback', {}).get('confidence_score', 0.8)
            )
            
            results.append({
                'process': process_num,
                'result': result
            })
        
        # Get contextual suggestions
        suggestions = self.context_manager.get_contextual_suggestions(session_id)
        
        # Create response
        response = {
            'status': 'completed',
            'results': results,
            'contextual_suggestions': suggestions[:3],  # Top 3
            'session_context': self.context_manager.create_context_summary(session_id),
            'execution_summary': {
                'processes_executed': len(processes),
                'total_time': time.time(),  # Would be actual execution time
                'cache_hits': sum(1 for r in results if r['result'].get('adaptive_feedback', {}).get('cache_used')),
            }
        }
        
        # Track performance
        self._track_performance(client_id, processes, results, routing_result)
        
        return response
    
    async def _simulate_process_execution(self, client_id: str, process_num: int, 
                                        parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate process execution (in real implementation, this would call actual processes)
        """
        # Get memory for this client
        memory = self.adaptive_agent.get_memory(client_id)
        
        # Simulate some result data based on process type
        if process_num == 38:  # Prospect discovery
            result_data = {
                'prospects': [
                    {'name': f'Company {i}', 'industry': 'Technology', 'size': f'{50+i*10} employees'}
                    for i in range(parameters.get('quantity', 10))
                ],
                'total_found': parameters.get('quantity', 10),
                'search_criteria': parameters
            }
        elif process_num in [74, 75, 76]:  # Analytics processes
            result_data = {
                'metrics': {
                    'total_processes': len(memory.load_memory().get('learning_context', {})),
                    'confidence_trend': 0.85,
                    'success_rate': 0.92
                },
                'insights': ['Performance is improving', 'Cache usage is optimized']
            }
        else:
            result_data = {
                'process_completed': True,
                'parameters_used': parameters,
                'timestamp': datetime.now().isoformat()
            }
        
        # Add adaptive feedback
        result_data['adaptive_feedback'] = {
            'completion_estimate': 'About 80%',
            'confidence_score': 0.82,
            'what_worked': ['Natural language processing', 'Parameter extraction'],
            'what_didnt': ['Some parameters were estimated'],
            'suggestions': ['Consider providing more specific criteria'],
            'data_sources_used': ['simulated_data']
        }
        
        return result_data
    
    def _track_performance(self, client_id: str, processes: List[int], 
                          results: List[Dict], routing_result: Dict[str, Any]):
        """Track performance metrics"""
        timestamp = time.time()
        
        # Track process executions
        self.performance_data['process_executions'].append({
            'timestamp': timestamp,
            'client_id': client_id,
            'processes': processes,
            'success': True,
            'confidence': sum(r['result'].get('adaptive_feedback', {}).get('confidence_score', 0) 
                            for r in results) / len(results)
        })
        
        # Track confidence
        avg_confidence = sum(r['result'].get('adaptive_feedback', {}).get('confidence_score', 0) 
                           for r in results) / len(results)
        self.performance_data['confidence_history'].append({
            'timestamp': timestamp,
            'confidence': avg_confidence
        })
        
        # Keep data bounded
        for key in self.performance_data:
            if len(self.performance_data[key]) > 1000:
                self.performance_data[key] = self.performance_data[key][-1000:]
    
    async def generate_analytics_dashboard(self, client_id: str) -> str:
        """Generate HTML analytics dashboard"""
        
        # Collect analytics data
        analytics_data = await self._collect_analytics_data(client_id)
        
        # Generate HTML dashboard
        html_content = self.dashboard_generator.generate_dashboard(
            client_id, analytics_data
        )
        
        return html_content
    
    async def _collect_analytics_data(self, client_id: str) -> Dict[str, Any]:
        """Collect comprehensive analytics data"""
        
        # Get memory data
        memory = self.adaptive_agent.get_memory(client_id)
        memory_data = memory.load_memory()
        
        # Get cache stats
        cache_stats = self.cache_manager.get_cache_stats()
        
        # Get conversation context
        session = self.context_manager.get_or_create_session(client_id)
        
        # Process usage from memory
        process_usage = {}
        for result in session.completed_processes:
            process_num = result.process_number
            process_usage[process_num] = process_usage.get(process_num, 0) + 1
        
        # Source performance from memory
        source_performance = memory_data.get('data_source_performance', {})
        
        # Learning progress
        learning_progress = []
        learning_contexts = memory_data.get('learning_context', {})
        cumulative_count = 0
        
        for i, (key, learning) in enumerate(learning_contexts.items()):
            cumulative_count += 1
            learning_progress.append({
                'timestamp': time.time() - (len(learning_contexts) - i) * 86400,  # Simulate dates
                'cumulative_learnings': cumulative_count
            })
        
        # Cost breakdown (simulated)
        cost_breakdown = {
            'API Calls': 45.30,
            'Data Storage': 12.50,
            'Processing': 8.20,
            'Cache Storage': 2.10
        }
        
        analytics_data = {
            'confidence_history': self.performance_data['confidence_history'],
            'process_usage': process_usage,
            'source_performance': source_performance,
            'learning_progress': learning_progress,
            'cost_breakdown': cost_breakdown,
            'cache_stats': cache_stats,
            'estimated_cost_savings': cache_stats.get('total_accesses', 0) * 0.05,  # Estimate
            'session_info': {
                'client_id': client_id,
                'session_age_hours': (time.time() - session.created_at) / 3600,
                'total_processes': len(session.completed_processes)
            }
        }
        
        return analytics_data
    
    async def handle_confirmation_response(self, client_id: str, session_id: str,
                                         response: str, routing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user response to confirmation dialog"""
        
        response_lower = response.lower()
        
        if 'cancel' in response_lower or 'no' in response_lower:
            return {
                'status': 'cancelled',
                'message': 'Request cancelled by user'
            }
        
        elif 'reduce' in response_lower or 'limit' in response_lower:
            # Reduce the rate limit
            routing_result['rate_limit'] = 10
            return await self._execute_routing_result(client_id, session_id, routing_result)
        
        elif 'cache' in response_lower:
            # Try to use cached data
            # Implementation would check cache more aggressively
            return {
                'status': 'using_cache',
                'message': 'Using cached data where available'
            }
        
        else:
            # Proceed with original request
            return await self._execute_routing_result(client_id, session_id, routing_result)
    
    def get_conversation_context(self, client_id: str) -> Dict[str, Any]:
        """Get current conversation context for client"""
        session = self.context_manager.get_or_create_session(client_id)
        return self.context_manager.create_context_summary(session.session_id)
    
    def invalidate_cache(self, client_id: str, task_type: Optional[str] = None):
        """Invalidate cache for client"""
        self.cache_manager.invalidate_cache(task_type)
        logger.info(f"Cache invalidated for client {client_id}")
    
    def cleanup(self):
        """Clean up expired sessions and cache"""
        self.context_manager.cleanup_expired_sessions()
        logger.info("Cleanup completed")