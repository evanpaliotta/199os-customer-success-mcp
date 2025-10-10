"""
Adaptive Agent System for Sales MCP Server

This module implements the core agentic architecture including:
- Dynamic data source discovery and routing
- Memory management and learning
- Confidence assessment and reporting
- Performance tracking and optimization

Key Components:
- DataSourceRegistry: Maps business functions to available data sources
- DataSourceDiscovery: Runtime environment scanning and source prioritization
- AgentMemory: Persistent learning and performance tracking
- UnifiedDataClient: Abstracted data access layer
- ConfidenceAssessment: Task completion evaluation
"""

import json
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import structlog
from src.utils.file_operations import SafeFileOperations

# Import MCP Orchestrator for MCP server integration
from src.mcp.orchestrator import MCPOrchestrator, MCPToolCall

# Import real integrations
from src.integrations import (
    SalesforceIntegration,
    GmailIntegration,
    ApolloIntegration,
)

# Import security manager for credentials
from src.security.credential_manager import CredentialManager

logger = structlog.get_logger(__name__)

class DataSourceRegistry:
    """Maps business functions to potential data sources with priority ordering"""
    
    DATA_SOURCE_MAP = {
        'crm': {
            'mcp_servers': ['salesforce', 'hubspot-mcp', 'pipedrive-mcp'],
            'api_keys': ['SALESFORCE_CLIENT_ID', 'HUBSPOT_API_KEY', 'PIPEDRIVE_API_TOKEN', 
                        'DYNAMICS_CLIENT_ID', 'COPPER_API_KEY'],
            'web_search_terms': ['CRM data', 'customer relationship management', 'sales pipeline']
        },
        'prospect_discovery': {
            'mcp_servers': ['actors-mcp-server'],  # Has Apollo.io scraper
            'api_keys': ['APOLLO_API_KEY', 'ZOOMINFO_API_KEY', 'CLEARBIT_API_KEY', 
                        'LUSHA_API_KEY', 'SEAMLESS_API_KEY', 'LINKEDIN_API_KEY'],
            'web_search_terms': ['company prospects', 'business directory', 'company information']
        },
        'email_outreach': {
            'mcp_servers': ['gmail'],
            'api_keys': ['OUTREACH_API_KEY', 'SALESLOFT_API_KEY', 'REPLY_API_KEY', 
                        'LEMLIST_API_KEY', 'MAILSHAKE_API_KEY', 'MIXMAX_API_KEY'],
            'web_search_terms': ['email templates', 'outreach strategies', 'cold email']
        },
        'conversation_intelligence': {
            'mcp_servers': [],
            'api_keys': ['GONG_ACCESS_KEY', 'CHORUS_API_TOKEN', 'OTTER_API_KEY', 
                        'REV_API_KEY', 'DIALPAD_API_KEY'],
            'web_search_terms': ['sales call analysis', 'conversation insights', 'call recording']
        },
        'market_research': {
            'mcp_servers': ['sec-edgar-mcp', 'actors-mcp-server'],
            'api_keys': ['CLEARBIT_API_KEY', 'SIXSENSE_API_KEY', 'BOMBORA_API_KEY', 
                        'DNB_API_KEY', 'ZOOMINFO_API_KEY'],
            'web_search_terms': ['market analysis', 'industry trends', 'competitor analysis']
        },
        'scheduling': {
            'mcp_servers': [],
            'api_keys': ['CALENDLY_ACCESS_TOKEN', 'CHILIPIPER_API_KEY', 'ACUITY_API_KEY', 
                        'GOOGLE_API_KEY', 'MEETINGBIRD_API_KEY'],
            'web_search_terms': ['meeting scheduling', 'calendar booking', 'appointment setting']
        },
        'document_management': {
            'mcp_servers': [],
            'api_keys': ['DOCUSIGN_INTEGRATION_KEY', 'PANDADOC_API_KEY', 'HELLOSIGN_API_KEY', 
                        'ADOBE_SIGN_CLIENT_ID'],
            'web_search_terms': ['document templates', 'contract templates', 'proposal formats']
        },
        'analytics': {
            'mcp_servers': [],
            'api_keys': ['TABLEAU_USERNAME', 'LOOKER_CLIENT_ID', 'POWERBI_CLIENT_ID', 
                        'SNOWFLAKE_USERNAME'],
            'web_search_terms': ['sales analytics', 'performance metrics', 'sales KPIs']
        }
    }
    
    @classmethod
    def get_sources_for_function(cls, business_function: str) -> Dict[str, List[str]]:
        """Get all potential data sources for a business function"""
        return cls.DATA_SOURCE_MAP.get(business_function, {
            'mcp_servers': [],
            'api_keys': [],
            'web_search_terms': ['general business information']
        })
    
    @classmethod
    def get_all_functions(cls) -> List[str]:
        """Get all supported business functions"""
        return list(cls.DATA_SOURCE_MAP.keys())


class DataSourceDiscovery:
    """Runtime discovery and prioritization of available data sources"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.claude_desktop_config = self._load_claude_desktop_config()
        
    def _load_claude_desktop_config(self) -> Dict[str, Any]:
        """Load Claude Desktop configuration to check available MCP servers"""
        try:
            safe_file_ops = SafeFileOperations()
            config_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
            if config_path.exists():
                config = safe_file_ops.read_json(config_path)
                if config:
                    return config.get('mcpServers', {})
            return {}
        except Exception as e:
            logger.warning(f"Could not load Claude Desktop config: {e}")
            return {}
    
    def discover_available_sources(self, business_function: str) -> Dict[str, Any]:
        """
        Discover available data sources for a business function
        Priority: API Keys → MCP Servers → Web Search → Dummy Data
        """
        sources = DataSourceRegistry.get_sources_for_function(business_function)
        
        available = {
            'api_keys': self._check_api_keys(sources['api_keys']),
            'mcp_servers': self._check_mcp_servers(sources['mcp_servers']),
            'web_search': True,  # Always available in Claude Desktop
            'web_search_terms': sources['web_search_terms'],
            'dummy_data': True,  # Always available as fallback
            'priority_source': None,
            'confidence_factors': {}
        }
        
        # Determine priority source
        if available['api_keys']:
            available['priority_source'] = 'api_keys'
            available['confidence_factors']['primary'] = 'direct_api_access'
        elif available['mcp_servers']:
            available['priority_source'] = 'mcp_servers'
            available['confidence_factors']['primary'] = 'mcp_integration'
        else:
            available['priority_source'] = 'web_search'
            available['confidence_factors']['primary'] = 'web_search_fallback'
            
        return available
    
    def _check_api_keys(self, api_keys: List[str]) -> Dict[str, bool]:
        """Check which API keys are configured in environment"""
        available_keys = {}
        for key in api_keys:
            available_keys[key] = bool(os.getenv(key))
        return available_keys
    
    def _check_mcp_servers(self, mcp_servers: List[str]) -> Dict[str, bool]:
        """Check which MCP servers are configured in Claude Desktop"""
        available_servers = {}
        for server in mcp_servers:
            available_servers[server] = server in self.claude_desktop_config
        return available_servers


class AgentMemory:
    """Persistent memory management with bounded growth and learning capabilities"""
    
    MAX_FILE_SIZE = 500 * 1024  # 500KB limit
    MAX_LEARNING_CONTEXTS = 50
    MAX_PERFORMANCE_RECORDS = 100
    MAX_WORKFLOW_PATTERNS = 20
    
    def __init__(self, client_id: str, config_path: Path):
        self.client_id = client_id
        self.config_path = config_path
        self.memory_dir = config_path / "client_configs" / client_id
        self.memory_file = self.memory_dir / "agent_memory.json"
        self.client_config_file = self.memory_dir / "config.json"
        self._memory_cache = None
        self._cache_timestamp = 0
        
        # Ensure memory directory exists
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory file if it doesn't exist
        if not self.memory_file.exists():
            self._create_default_memory()
        
        # Update memory with client configuration if available
        self._sync_with_client_config()
    
    def _create_default_memory(self):
        """Create default memory structure"""
        default_memory = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "learning_context": {},
            "data_source_performance": {},
            "workflow_patterns": {
                "frequent_sequences": [],
                "common_combinations": {},
                "suggested_workflows": []
            },
            "user_preferences": {
                "response_detail_level": "standard",
                "completion_threshold": 0.70,
                "auto_suggestions": True,
                "collaboration_mode": "suggest",
                "learning_frequency": "often",
                "data_source_preferences": "balanced"
            },
            "confidence_patterns": {
                "high_confidence_indicators": [],
                "low_confidence_triggers": []
            }
        }
        
        safe_file_ops = SafeFileOperations()
        safe_file_ops.write_json(self.memory_file, default_memory)

        logger.info(f"Created default memory for client {self.client_id}")
    
    def _sync_with_client_config(self):
        """Sync memory preferences with client configuration"""
        try:
            if not self.client_config_file.exists():
                return

            safe_file_ops = SafeFileOperations()
            client_config = safe_file_ops.read_json(self.client_config_file)
            if not client_config:
                return
            
            # Extract agent settings from client config
            agent_settings = client_config.get('adaptive_agent_settings', {})
            if not agent_settings:
                return
            
            # Load current memory
            memory = self.load_memory(force_reload=True)
            
            # Update preferences from client config
            preferences = memory.get('user_preferences', {})
            
            if 'completion_threshold' in agent_settings:
                preferences['completion_threshold'] = float(agent_settings['completion_threshold'])
            if 'response_detail_level' in agent_settings:
                preferences['response_detail_level'] = agent_settings['response_detail_level']
            if 'auto_suggestions' in agent_settings:
                preferences['auto_suggestions'] = agent_settings['auto_suggestions']
            if 'collaboration_mode' in agent_settings:
                preferences['collaboration_mode'] = agent_settings['collaboration_mode']
            if 'learning_frequency' in agent_settings:
                preferences['learning_frequency'] = agent_settings['learning_frequency']
            if 'data_source_preferences' in agent_settings:
                preferences['data_source_preferences'] = agent_settings['data_source_preferences']
            
            memory['user_preferences'] = preferences
            self.save_memory(memory)
            
            logger.info(f"Synced agent preferences from client config for {self.client_id}")
            
        except Exception as e:
            logger.warning(f"Could not sync with client config: {e}")
    
    def load_memory(self, force_reload: bool = False) -> Dict[str, Any]:
        """Load memory with caching"""
        current_time = time.time()
        
        # Use cache if recent and not forced reload
        if (not force_reload and 
            self._memory_cache is not None and 
            (current_time - self._cache_timestamp) < 60):  # 60 second cache
            return self._memory_cache
        
        try:
            safe_file_ops = SafeFileOperations()
            memory = safe_file_ops.read_json(self.memory_file)

            if not memory:
                logger.warning("Memory file corrupted or missing, recreating")
                self._create_default_memory()
                return self.load_memory(force_reload=True)

            self._memory_cache = memory
            self._cache_timestamp = current_time
            return memory

        except Exception as e:
            logger.warning(f"Error loading memory, recreating: {e}")
            self._create_default_memory()
            return self.load_memory(force_reload=True)
    
    def save_memory(self, memory: Dict[str, Any]):
        """Atomically save memory with backup"""
        # Update timestamp
        memory["last_updated"] = datetime.now().isoformat()
        
        # Prune if needed
        memory = self._prune_memory_if_needed(memory)
        
        # Use safe file operations for atomic write
        safe_file_ops = SafeFileOperations()

        try:
            # Safe atomic write handles backups internally
            success = safe_file_ops.write_json(self.memory_file, memory)

            if not success:
                raise Exception("Failed to write memory file")

            # Update cache
            self._memory_cache = memory
            self._cache_timestamp = time.time()

            logger.debug(f"Memory saved for client {self.client_id}")

        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            raise
    
    def get_relevant_memory(self, process_num: int, task_type: str) -> Dict[str, Any]:
        """Get memory relevant to current task"""
        full_memory = self.load_memory()
        
        relevant = {
            "user_preferences": full_memory.get("user_preferences", {}),
            "general_performance": {},
            "task_specific_learning": {},
            "workflow_context": {}
        }
        
        # Extract performance data for relevant data sources
        performance_data = full_memory.get("data_source_performance", {})
        for source, metrics in performance_data.items():
            if task_type in source or any(word in source for word in task_type.split('_')):
                relevant["general_performance"][source] = metrics
        
        # Extract task-specific learnings
        learning_context = full_memory.get("learning_context", {})
        for context_key, learning in learning_context.items():
            if (task_type in context_key or 
                str(process_num) in context_key or
                any(word in context_key for word in task_type.split('_'))):
                relevant["task_specific_learning"][context_key] = learning
        
        # Extract workflow patterns
        workflow_patterns = full_memory.get("workflow_patterns", {})
        for pattern in workflow_patterns.get("frequent_sequences", []):
            if process_num in pattern.get("processes", []):
                relevant["workflow_context"] = pattern
                break
        
        return relevant
    
    def update_learning(self, learning_key: str, user_feedback: str, context: Dict[str, Any]):
        """Update memory with new learning from user feedback"""
        memory = self.load_memory()
        
        learning_entry = {
            "feedback": user_feedback,
            "context": context,
            "learned_at": datetime.now().isoformat(),
            "usage_count": 1
        }
        
        # If learning already exists, update it
        if learning_key in memory["learning_context"]:
            existing = memory["learning_context"][learning_key]
            existing["usage_count"] = existing.get("usage_count", 0) + 1
            existing["last_reinforced"] = datetime.now().isoformat()
            existing["feedback_history"] = existing.get("feedback_history", [])
            existing["feedback_history"].append({
                "feedback": user_feedback,
                "timestamp": datetime.now().isoformat()
            })
        else:
            memory["learning_context"][learning_key] = learning_entry
        
        self.save_memory(memory)
        logger.info(f"Updated learning for key: {learning_key}")
    
    def update_performance(self, data_source: str, success: bool, quality_score: float, 
                          response_time: float, task_type: str):
        """Update data source performance metrics"""
        memory = self.load_memory()
        
        performance_key = f"{data_source}_{task_type}"
        
        if performance_key not in memory["data_source_performance"]:
            memory["data_source_performance"][performance_key] = {
                "success_count": 0,
                "total_attempts": 0,
                "avg_quality": 0.0,
                "avg_response_time": 0.0,
                "last_used": None,
                "task_type": task_type
            }
        
        perf = memory["data_source_performance"][performance_key]
        perf["total_attempts"] += 1
        if success:
            perf["success_count"] += 1
        
        # Update running averages
        total_attempts = perf["total_attempts"]
        perf["avg_quality"] = ((perf["avg_quality"] * (total_attempts - 1)) + quality_score) / total_attempts
        perf["avg_response_time"] = ((perf["avg_response_time"] * (total_attempts - 1)) + response_time) / total_attempts
        perf["last_used"] = datetime.now().isoformat()
        
        self.save_memory(memory)
    
    def record_workflow_pattern(self, process_sequence: List[int]):
        """Record a sequence of processes for workflow pattern analysis"""
        if len(process_sequence) < 2:
            return  # Only record meaningful sequences
        
        memory = self.load_memory()
        patterns = memory["workflow_patterns"]
        
        # Find existing pattern or create new one
        sequence_key = "_".join(map(str, process_sequence))
        
        existing_pattern = None
        for pattern in patterns["frequent_sequences"]:
            if pattern["processes"] == process_sequence:
                existing_pattern = pattern
                break
        
        if existing_pattern:
            existing_pattern["frequency"] += 1
            existing_pattern["last_seen"] = datetime.now().isoformat()
        else:
            new_pattern = {
                "processes": process_sequence,
                "frequency": 1,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "success_rate": 1.0
            }
            patterns["frequent_sequences"].append(new_pattern)
        
        # Sort by frequency and keep top patterns
        patterns["frequent_sequences"].sort(key=lambda x: x["frequency"], reverse=True)
        patterns["frequent_sequences"] = patterns["frequent_sequences"][:self.MAX_WORKFLOW_PATTERNS]
        
        self.save_memory(memory)
    
    def _prune_memory_if_needed(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Prune memory if it exceeds size limits"""
        # Check memory size using string length as proxy
        try:
            memory_str = json.dumps(memory)
            estimated_size = len(memory_str.encode('utf-8'))

            if estimated_size > self.MAX_FILE_SIZE:
                memory = self._prune_memory_content(memory)

        except Exception as e:
            logger.warning(f"Could not check memory size, skipping pruning: {e}")
        
        return memory
    
    def _prune_memory_content(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Prune memory content to stay within limits"""
        logger.info(f"Pruning memory for client {self.client_id}")
        
        # Prune learning contexts - keep most recent and most used
        learning_contexts = memory.get("learning_context", {})
        if len(learning_contexts) > self.MAX_LEARNING_CONTEXTS:
            # Sort by usage count and recency
            sorted_contexts = sorted(
                learning_contexts.items(),
                key=lambda x: (x[1].get("usage_count", 0), x[1].get("learned_at", "")),
                reverse=True
            )
            memory["learning_context"] = dict(sorted_contexts[:self.MAX_LEARNING_CONTEXTS])
        
        # Prune performance records - keep recent and high performers
        performance_data = memory.get("data_source_performance", {})
        if len(performance_data) > self.MAX_PERFORMANCE_RECORDS:
            sorted_performance = sorted(
                performance_data.items(),
                key=lambda x: (x[1].get("success_count", 0) / max(x[1].get("total_attempts", 1), 1), 
                              x[1].get("last_used", "")),
                reverse=True
            )
            memory["data_source_performance"] = dict(sorted_performance[:self.MAX_PERFORMANCE_RECORDS])
        
        # Prune workflow patterns - keep most frequent
        workflow_patterns = memory.get("workflow_patterns", {})
        sequences = workflow_patterns.get("frequent_sequences", [])
        if len(sequences) > self.MAX_WORKFLOW_PATTERNS:
            sequences.sort(key=lambda x: x.get("frequency", 0), reverse=True)
            workflow_patterns["frequent_sequences"] = sequences[:self.MAX_WORKFLOW_PATTERNS]
        
        return memory


class ConfidenceAssessment:
    """Evaluates task completion confidence and generates human-like reporting"""
    
    @staticmethod
    def assess_confidence(result: Dict[str, Any], available_sources: Dict[str, Any], 
                         memory: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """Assess confidence in task completion and generate report"""
        
        # Calculate confidence factors
        factors = {}
        
        # Data source quality factor
        primary_source = available_sources.get('priority_source')
        if primary_source == 'api_keys':
            factors['data_source'] = 0.9
        elif primary_source == 'mcp_servers':
            factors['data_source'] = 0.8
        elif primary_source == 'web_search':
            factors['data_source'] = 0.6
        else:
            factors['data_source'] = 0.4
        
        # Data completeness factor
        factors['completeness'] = ConfidenceAssessment._assess_completeness(result)
        
        # Data freshness factor  
        factors['freshness'] = ConfidenceAssessment._assess_freshness(result, available_sources)
        
        # Historical performance factor
        factors['historical'] = ConfidenceAssessment._assess_historical_performance(
            memory, task_type, primary_source
        )
        
        # Overall confidence (weighted average)
        confidence = (
            factors['data_source'] * 0.3 +
            factors['completeness'] * 0.3 +
            factors['freshness'] * 0.2 +
            factors['historical'] * 0.2
        )
        
        # Generate human-like completion estimate
        completion_percentage = int(confidence * 100)
        completion_text = ConfidenceAssessment._humanize_percentage(completion_percentage)
        
        # Generate what worked / didn't work / suggestions
        analysis = ConfidenceAssessment._generate_analysis(
            factors, available_sources, result, task_type
        )
        
        return {
            'confidence_score': confidence,
            'completion_percentage': completion_percentage,
            'completion_estimate': completion_text,
            'what_worked': analysis['what_worked'],
            'what_didnt': analysis['what_didnt'],
            'suggestions': analysis['suggestions'],
            'data_sources_used': analysis['sources_used'],
            'factors': factors
        }
    
    @staticmethod
    def _assess_completeness(result: Dict[str, Any]) -> float:
        """Assess how complete the result data is"""
        if not result:
            return 0.1
        
        # Count non-empty fields
        total_fields = len(result)
        populated_fields = sum(1 for v in result.values() if v and v != [] and v != {})
        
        if total_fields == 0:
            return 0.1
        
        return min(populated_fields / total_fields, 1.0)
    
    @staticmethod  
    def _assess_freshness(result: Dict[str, Any], available_sources: Dict[str, Any]) -> float:
        """Assess how fresh/current the data is"""
        primary_source = available_sources.get('priority_source')
        
        # API data is typically freshest
        if primary_source == 'api_keys':
            return 0.9
        # MCP servers vary
        elif primary_source == 'mcp_servers':
            return 0.7
        # Web search can be mixed
        elif primary_source == 'web_search':
            return 0.6
        # Dummy data is stale
        else:
            return 0.2
    
    @staticmethod
    def _assess_historical_performance(memory: Dict[str, Any], task_type: str, 
                                     primary_source: str) -> float:
        """Assess based on historical performance of this approach"""
        relevant_memory = memory.get('general_performance', {})
        
        # Look for performance data matching this task and source
        for perf_key, perf_data in relevant_memory.items():
            if task_type in perf_key and primary_source in perf_key:
                success_rate = perf_data.get('success_count', 0) / max(perf_data.get('total_attempts', 1), 1)
                return success_rate
        
        # Default to moderate confidence if no history
        return 0.7
    
    @staticmethod
    def _humanize_percentage(percentage: int) -> str:
        """Convert percentage to human-like estimate"""
        if percentage >= 90:
            return f"About {percentage}%"
        elif percentage >= 80:
            return f"Around {percentage}%"  
        elif percentage >= 70:
            return f"Roughly {percentage}%"
        elif percentage >= 60:
            return f"About {percentage}%"
        elif percentage >= 50:
            return f"Around {percentage}%"
        else:
            return f"Maybe {percentage}%"
    
    @staticmethod
    def _generate_analysis(factors: Dict[str, float], available_sources: Dict[str, Any],
                          result: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """Generate what worked, didn't work, and suggestions"""
        
        what_worked = []
        what_didnt = []
        suggestions = []
        sources_used = []
        
        primary_source = available_sources.get('priority_source')
        
        # Analyze what worked
        if factors['data_source'] > 0.8:
            if primary_source == 'api_keys':
                api_keys = [k for k, v in available_sources.get('api_keys', {}).items() if v]
                what_worked.append(f"Direct API access provided reliable data from {', '.join(api_keys[:2])}")
                sources_used.extend(api_keys[:2])
        elif factors['data_source'] > 0.7:
            if primary_source == 'mcp_servers':
                mcp_servers = [k for k, v in available_sources.get('mcp_servers', {}).items() if v]
                what_worked.append(f"MCP server integration worked well via {', '.join(mcp_servers[:2])}")
                sources_used.extend(mcp_servers[:2])
        elif factors['data_source'] > 0.5:
            what_worked.append("Web search provided general information")
            sources_used.append("web_search")
        
        if factors['completeness'] > 0.8:
            what_worked.append("Found comprehensive data covering most requirements")
        elif factors['completeness'] > 0.6:
            what_worked.append("Got good coverage of key data points")
        
        # Analyze what didn't work
        if factors['data_source'] < 0.7:
            what_didnt.append("Limited to lower-quality data sources")
        
        if factors['completeness'] < 0.6:
            what_didnt.append("Missing some important data fields")
        
        if factors['freshness'] < 0.6:
            what_didnt.append("Some data may be outdated")
        
        if factors['historical'] < 0.6:
            what_didnt.append("This approach has had mixed results in the past")
        
        # Generate suggestions
        if primary_source != 'api_keys':
            # Suggest API improvements
            potential_apis = available_sources.get('api_keys', {})
            missing_apis = [k for k, v in potential_apis.items() if not v]
            if missing_apis:
                suggestions.append(f"Configure {missing_apis[0]} for more reliable {task_type} data")
        
        if primary_source == 'web_search':
            suggestions.append(f"Set up specialized data sources for better {task_type} results")
        
        if factors['completeness'] < 0.8:
            suggestions.append("Consider additional data sources to fill information gaps")
        
        return {
            'what_worked': what_worked,
            'what_didnt': what_didnt,
            'suggestions': suggestions,
            'sources_used': sources_used
        }


class UnifiedDataClient:
    """Abstracted data access layer that routes to best available source"""
    
    def __init__(self, discovery: DataSourceDiscovery, memory: AgentMemory,
                 credential_manager: Optional[CredentialManager] = None,
                 mcp_orchestrator: Optional[MCPOrchestrator] = None):
        self.discovery = discovery
        self.memory = memory
        self.credential_manager = credential_manager
        self.mcp_orchestrator = mcp_orchestrator

        # Initialize integrations (lazy loaded when credentials available)
        self._salesforce_integration: Optional[SalesforceIntegration] = None
        self._gmail_integration: Optional[GmailIntegration] = None
        self._apollo_integration: Optional[ApolloIntegration] = None
    
    async def get_data(self, business_function: str, criteria: Dict[str, Any], 
                       ctx=None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Get data using best available source with fallback chain
        Returns: (result_data, metadata)
        """
        start_time = time.time()
        
        # Discover available sources
        available_sources = self.discovery.discover_available_sources(business_function)
        
        # Load relevant memory
        task_memory = self.memory.get_relevant_memory(0, business_function)  # Process 0 for general
        
        result = None
        metadata = {
            'sources_attempted': [],
            'success': False,
            'primary_source': available_sources['priority_source'],
            'response_time': 0,
            'available_sources': available_sources
        }
        
        # Try sources in priority order
        try:
            # 1. Try API keys first
            if available_sources['api_keys'] and available_sources['priority_source'] == 'api_keys':
                result = await self._try_api_sources(business_function, criteria, available_sources, ctx)
                if result:
                    metadata['sources_attempted'].append('api_keys')
                    metadata['success'] = True
            
            # 2. Try MCP servers
            if not result and available_sources['mcp_servers']:
                result = await self._try_mcp_sources(business_function, criteria, available_sources, ctx)
                if result:
                    metadata['sources_attempted'].append('mcp_servers')
                    metadata['success'] = True
            
            # 3. Try web search
            if not result:
                result = await self._try_web_search(business_function, criteria, available_sources, ctx)
                if result:
                    metadata['sources_attempted'].append('web_search')
                    metadata['success'] = True
            
            # 4. Fallback to dummy data
            if not result:
                result = self._generate_dummy_data(business_function, criteria)
                metadata['sources_attempted'].append('dummy_data')
                metadata['success'] = True  # Dummy data always "succeeds"
        
        except Exception as e:
            logger.error(f"Error in data retrieval: {e}")
            result = self._generate_dummy_data(business_function, criteria)
            metadata['sources_attempted'].append('dummy_data_error_fallback')
            metadata['error'] = str(e)
        
        metadata['response_time'] = time.time() - start_time
        
        # Update performance metrics
        primary_source = metadata['sources_attempted'][0] if metadata['sources_attempted'] else 'none'
        quality_score = self._estimate_data_quality(result, metadata)
        self.memory.update_performance(
            primary_source, metadata['success'], quality_score, 
            metadata['response_time'], business_function
        )
        
        return result, metadata
    
    async def _try_api_sources(self, business_function: str, criteria: Dict[str, Any],
                              available_sources: Dict[str, Any], ctx) -> Optional[Dict[str, Any]]:
        """Try direct API access using real integrations"""
        if not self.credential_manager:
            if ctx:
                await ctx.info("Credential manager not available, skipping API sources")
            return None

        try:
            # CRM operations - use Salesforce
            if business_function in ['crm', 'analytics']:
                integration = await self._get_salesforce_integration()
                if integration:
                    if ctx:
                        await ctx.info(f"Using Salesforce API for {business_function}")

                    # Query based on business function
                    if business_function == 'crm':
                        # Query accounts or opportunities
                        query = criteria.get('soql', 'SELECT Id, Name FROM Account LIMIT 10')
                        result = await integration.query(query)
                        return result
                    elif business_function == 'analytics':
                        # Get analytics data
                        return await integration.get_analytics_data()

            # Email outreach - use Gmail
            elif business_function == 'email_outreach':
                integration = await self._get_gmail_integration()
                if integration:
                    if ctx:
                        await ctx.info(f"Using Gmail API for {business_function}")

                    # Send email or search
                    if 'send' in criteria:
                        result = await integration.send_email(
                            to=criteria.get('to', []),
                            subject=criteria.get('subject', ''),
                            body=criteria.get('body', '')
                        )
                        return result
                    else:
                        result = await integration.search_emails(
                            query=criteria.get('query', ''),
                            max_results=criteria.get('max_results', 10)
                        )
                        return result

            # Prospect discovery - use Apollo
            elif business_function == 'prospect_discovery':
                integration = await self._get_apollo_integration()
                if integration:
                    if ctx:
                        await ctx.info(f"Using Apollo API for {business_function}")

                    # Search people or companies
                    if criteria.get('search_type') == 'people':
                        result = await integration.search_people(
                            keywords=criteria.get('keywords', []),
                            titles=criteria.get('titles', []),
                            company_names=criteria.get('companies', [])
                        )
                        return result
                    else:
                        result = await integration.search_companies(
                            keywords=criteria.get('keywords', []),
                            industries=criteria.get('industries', [])
                        )
                        return result

            if ctx:
                await ctx.info(f"No API integration available for {business_function}")
            return None

        except Exception as e:
            logger.error(f"Error accessing API sources: {e}")
            if ctx:
                await ctx.error(f"API integration error: {str(e)}")
            return None
    
    async def _try_mcp_sources(self, business_function: str, criteria: Dict[str, Any],
                              available_sources: Dict[str, Any], ctx) -> Optional[Dict[str, Any]]:
        """Try MCP server integration using orchestrator"""
        if not self.mcp_orchestrator:
            if ctx:
                await ctx.info("MCP orchestrator not available, skipping MCP sources")
            return None

        try:
            # Get suggested tools for this business function
            suggestions = self.mcp_orchestrator.suggest_tool_for_function(business_function)

            if not suggestions:
                if ctx:
                    await ctx.info(f"No MCP tools found for {business_function}")
                return None

            # Try the best matching tool
            best_tool = suggestions[0]
            tool_name = best_tool['tool_name']

            if ctx:
                await ctx.info(f"Using MCP tool: {tool_name} from {best_tool['server_name']}")

            # Create tool call with criteria as arguments
            tool_call = MCPToolCall(
                tool_name=tool_name,
                arguments=criteria,
                server_name=best_tool['server_name']
            )

            # Execute the tool
            result = await self.mcp_orchestrator.call_tool(tool_call)

            if result.success:
                if ctx:
                    await ctx.info(f"MCP tool executed successfully in {result.execution_time:.2f}s")
                return result.result
            else:
                if ctx:
                    await ctx.error(f"MCP tool failed: {result.error}")
                return None

        except Exception as e:
            logger.error(f"Error accessing MCP sources: {e}")
            if ctx:
                await ctx.error(f"MCP integration error: {str(e)}")
            return None
    
    async def _try_web_search(self, business_function: str, criteria: Dict[str, Any],
                             available_sources: Dict[str, Any], ctx) -> Optional[Dict[str, Any]]:
        """Try web search approach"""
        # For now, return None to indicate web search integration not yet implemented
        # This would use Claude's built-in web search capabilities
        if ctx:
            await ctx.info(f"Web search for {business_function} not yet implemented, falling back")
        return None
    
    def _generate_dummy_data(self, business_function: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dummy data as final fallback"""
        return {
            'data_type': 'dummy',
            'business_function': business_function,
            'criteria': criteria,
            'warning': 'This is dummy data. Configure real data sources for actual results.',
            'timestamp': datetime.now().isoformat()
        }
    
    def _estimate_data_quality(self, result: Dict[str, Any], metadata: Dict[str, Any]) -> float:
        """Estimate data quality score"""
        if not result:
            return 0.0

        if result.get('data_type') == 'dummy':
            return 0.3

        primary_source = metadata.get('primary_source', 'unknown')
        if primary_source == 'api_keys':
            return 0.9
        elif primary_source == 'mcp_servers':
            return 0.8
        elif primary_source == 'web_search':
            return 0.6
        else:
            return 0.4

    async def _get_salesforce_integration(self) -> Optional[SalesforceIntegration]:
        """Lazy load Salesforce integration"""
        if self._salesforce_integration:
            return self._salesforce_integration

        if not self.credential_manager:
            return None

        try:
            # Get Salesforce credentials
            creds = await self.credential_manager.get_credentials(
                'salesforce',
                required_fields=['client_id', 'client_secret', 'username', 'password']
            )

            if not creds:
                return None

            # Initialize integration
            self._salesforce_integration = SalesforceIntegration(
                client_id=creds['client_id'],
                client_secret=creds['client_secret'],
                username=creds['username'],
                password=creds['password'],
                security_token=creds.get('security_token', ''),
                instance_url=creds.get('instance_url', 'https://login.salesforce.com')
            )

            await self._salesforce_integration.connect()
            return self._salesforce_integration

        except Exception as e:
            logger.error(f"Failed to initialize Salesforce integration: {e}")
            return None

    async def _get_gmail_integration(self) -> Optional[GmailIntegration]:
        """Lazy load Gmail integration"""
        if self._gmail_integration:
            return self._gmail_integration

        if not self.credential_manager:
            return None

        try:
            # Get Gmail credentials
            creds = await self.credential_manager.get_credentials(
                'gmail',
                required_fields=['credentials_json']
            )

            if not creds:
                return None

            # Initialize integration
            self._gmail_integration = GmailIntegration(
                credentials_json=creds['credentials_json'],
                token_path=creds.get('token_path', 'config/gmail_token.json')
            )

            await self._gmail_integration.connect()
            return self._gmail_integration

        except Exception as e:
            logger.error(f"Failed to initialize Gmail integration: {e}")
            return None

    async def _get_apollo_integration(self) -> Optional[ApolloIntegration]:
        """Lazy load Apollo integration"""
        if self._apollo_integration:
            return self._apollo_integration

        if not self.credential_manager:
            return None

        try:
            # Get Apollo credentials
            creds = await self.credential_manager.get_credentials(
                'apollo',
                required_fields=['api_key']
            )

            if not creds:
                return None

            # Initialize integration
            self._apollo_integration = ApolloIntegration(
                api_key=creds['api_key']
            )

            await self._apollo_integration.connect()
            return self._apollo_integration

        except Exception as e:
            logger.error(f"Failed to initialize Apollo integration: {e}")
            return None