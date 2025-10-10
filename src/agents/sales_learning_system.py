"""
Sales Learning System for Sales MCP Server

Implements sophisticated learning and adaptation capabilities:
- Pattern learning from win/loss data and sales outcomes
- Strategy adaptation based on historical performance
- Client preference learning and customization  
- Team performance optimization
- Continuous improvement through feedback loops

Key Components:
- SalesLearningEngine: Core learning algorithms and pattern recognition
- StrategyAdapter: Adapts sales strategies based on learned patterns
- PerformanceOptimizer: Optimizes team and process performance
- ClientPreferenceLearner: Learns client-specific preferences and behaviors
- OutcomeFeedbackLoop: Processes outcomes to improve future recommendations
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import structlog
from pathlib import Path
import statistics
import numpy as np
from collections import defaultdict, deque

logger = structlog.get_logger(__name__)


class OutcomeType(Enum):
    """Types of sales outcomes for learning"""
    WIN = "win"
    LOSS = "loss"
    NO_DECISION = "no_decision"
    PIPELINE = "pipeline"
    QUALIFIED_OUT = "qualified_out"


class StrategyType(Enum):
    """Types of sales strategies"""
    TERRITORY_ALLOCATION = "territory_allocation"
    QUOTA_SETTING = "quota_setting"
    COACHING_APPROACH = "coaching_approach"
    PROCESS_OPTIMIZATION = "process_optimization"
    RESOURCE_ALLOCATION = "resource_allocation"
    TIMING_STRATEGY = "timing_strategy"


class LearningDomain(Enum):
    """Domains for learning categorization"""
    DEAL_MANAGEMENT = "deal_management"
    LEAD_QUALIFICATION = "lead_qualification"
    TERRITORY_MANAGEMENT = "territory_management"
    TEAM_PERFORMANCE = "team_performance"
    CLIENT_ENGAGEMENT = "client_engagement"
    FORECASTING = "forecasting"


@dataclass
class SalesOutcome:
    """Record of a sales outcome for learning"""
    outcome_id: str
    outcome_type: OutcomeType
    deal_value: float
    sales_cycle_days: int
    rep_id: str
    client_id: str
    strategy_used: Dict[str, Any]
    context_factors: Dict[str, Any]
    outcome_date: datetime
    feedback_score: Optional[float] = None
    lessons_learned: List[str] = field(default_factory=list)
    contributing_factors: List[str] = field(default_factory=list)


@dataclass
class LearningPattern:
    """A learned pattern from sales outcomes"""
    pattern_id: str
    pattern_type: str
    conditions: Dict[str, Any]
    outcomes: Dict[str, Any]
    confidence_score: float
    sample_size: int
    success_rate: float
    average_deal_value: float
    average_cycle_time: int
    first_observed: datetime
    last_updated: datetime
    client_ids: Set[str]


@dataclass
class StrategyRecommendation:
    """A strategy recommendation based on learned patterns"""
    recommendation_id: str
    strategy_type: StrategyType
    recommendation: str
    supporting_patterns: List[str]
    expected_outcomes: Dict[str, float]
    confidence: float
    risk_factors: List[str]
    implementation_steps: List[str]
    measurement_criteria: List[str]


class SalesLearningEngine:
    """
    Core learning engine for sales patterns and outcomes
    
    Analyzes historical sales data to identify:
    - Successful patterns and strategies
    - Failure modes and risk factors
    - Optimal timing and approach patterns
    - Rep and client-specific preferences
    """
    
    def __init__(self, client_id: str, storage_dir: Optional[Path] = None):
        self.client_id = client_id
        self.storage_dir = storage_dir or Path("client_configs") / client_id
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Learning data
        self.outcomes_history: List[SalesOutcome] = []
        self.learned_patterns: Dict[str, LearningPattern] = {}
        self.pattern_performance: Dict[str, List[float]] = defaultdict(list)
        
        # Learning parameters
        self.min_pattern_samples = 5  # Minimum samples to establish a pattern
        self.pattern_confidence_threshold = 0.7
        self.max_outcomes_history = 2000  # Maximum outcomes to keep
        self.learning_rate = 0.1  # How quickly to adapt to new information
        
        # Load existing data
        self._load_learning_data()
    
    def _load_learning_data(self):
        """Load learning data from storage"""
        try:
            # Load outcomes history
            outcomes_file = self.storage_dir / "outcomes_history.json"
            if outcomes_file.exists():
                with open(outcomes_file, 'r') as f:
                    outcomes_data = json.load(f)
                
                for outcome_data in outcomes_data:
                    outcome = SalesOutcome(
                        outcome_id=outcome_data["outcome_id"],
                        outcome_type=OutcomeType(outcome_data["outcome_type"]),
                        deal_value=outcome_data["deal_value"],
                        sales_cycle_days=outcome_data["sales_cycle_days"],
                        rep_id=outcome_data["rep_id"],
                        client_id=outcome_data["client_id"],
                        strategy_used=outcome_data["strategy_used"],
                        context_factors=outcome_data["context_factors"],
                        outcome_date=datetime.fromisoformat(outcome_data["outcome_date"]),
                        feedback_score=outcome_data.get("feedback_score"),
                        lessons_learned=outcome_data.get("lessons_learned", []),
                        contributing_factors=outcome_data.get("contributing_factors", [])
                    )
                    self.outcomes_history.append(outcome)
            
            # Load learned patterns
            patterns_file = self.storage_dir / "learned_patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                
                for pattern_id, pattern_data in patterns_data.items():
                    pattern = LearningPattern(
                        pattern_id=pattern_data["pattern_id"],
                        pattern_type=pattern_data["pattern_type"],
                        conditions=pattern_data["conditions"],
                        outcomes=pattern_data["outcomes"],
                        confidence_score=pattern_data["confidence_score"],
                        sample_size=pattern_data["sample_size"],
                        success_rate=pattern_data["success_rate"],
                        average_deal_value=pattern_data["average_deal_value"],
                        average_cycle_time=pattern_data["average_cycle_time"],
                        first_observed=datetime.fromisoformat(pattern_data["first_observed"]),
                        last_updated=datetime.fromisoformat(pattern_data["last_updated"]),
                        client_ids=set(pattern_data["client_ids"])
                    )
                    self.learned_patterns[pattern_id] = pattern
            
            logger.info(f"Loaded learning data for client {self.client_id}",
                       outcomes=len(self.outcomes_history),
                       patterns=len(self.learned_patterns))
                       
        except Exception as e:
            logger.warning(f"Could not load learning data: {e}")
    
    def _save_learning_data(self):
        """Save learning data to storage"""
        try:
            # Save outcomes history (keep recent)
            recent_outcomes = self.outcomes_history[-self.max_outcomes_history:]
            outcomes_data = []
            
            for outcome in recent_outcomes:
                outcome_data = {
                    "outcome_id": outcome.outcome_id,
                    "outcome_type": outcome.outcome_type.value,
                    "deal_value": outcome.deal_value,
                    "sales_cycle_days": outcome.sales_cycle_days,
                    "rep_id": outcome.rep_id,
                    "client_id": outcome.client_id,
                    "strategy_used": outcome.strategy_used,
                    "context_factors": outcome.context_factors,
                    "outcome_date": outcome.outcome_date.isoformat(),
                    "feedback_score": outcome.feedback_score,
                    "lessons_learned": outcome.lessons_learned,
                    "contributing_factors": outcome.contributing_factors
                }
                outcomes_data.append(outcome_data)
            
            outcomes_file = self.storage_dir / "outcomes_history.json"
            with open(outcomes_file, 'w') as f:
                json.dump(outcomes_data, f, indent=2)
            
            # Save learned patterns
            patterns_data = {}
            for pattern_id, pattern in self.learned_patterns.items():
                patterns_data[pattern_id] = {
                    "pattern_id": pattern.pattern_id,
                    "pattern_type": pattern.pattern_type,
                    "conditions": pattern.conditions,
                    "outcomes": pattern.outcomes,
                    "confidence_score": pattern.confidence_score,
                    "sample_size": pattern.sample_size,
                    "success_rate": pattern.success_rate,
                    "average_deal_value": pattern.average_deal_value,
                    "average_cycle_time": pattern.average_cycle_time,
                    "first_observed": pattern.first_observed.isoformat(),
                    "last_updated": pattern.last_updated.isoformat(),
                    "client_ids": list(pattern.client_ids)
                }
            
            patterns_file = self.storage_dir / "learned_patterns.json"
            with open(patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save learning data: {e}")
    
    async def record_outcome(self, outcome: SalesOutcome) -> str:
        """Record a sales outcome for learning"""
        self.outcomes_history.append(outcome)
        
        # Trigger pattern learning
        await self._update_patterns_with_outcome(outcome)
        
        # Save data
        self._save_learning_data()
        
        logger.info(f"Recorded sales outcome {outcome.outcome_id}")
        return outcome.outcome_id
    
    async def _update_patterns_with_outcome(self, outcome: SalesOutcome):
        """Update learned patterns with new outcome"""
        # Extract pattern candidates from outcome
        pattern_candidates = self._extract_pattern_candidates(outcome)
        
        for candidate in pattern_candidates:
            pattern_id = candidate["pattern_id"]
            
            if pattern_id in self.learned_patterns:
                # Update existing pattern
                await self._update_existing_pattern(pattern_id, outcome, candidate)
            else:
                # Check if we should create a new pattern
                similar_outcomes = self._find_similar_outcomes(candidate["conditions"])
                if len(similar_outcomes) >= self.min_pattern_samples:
                    await self._create_new_pattern(pattern_id, similar_outcomes, candidate)
    
    def _extract_pattern_candidates(self, outcome: SalesOutcome) -> List[Dict[str, Any]]:
        """Extract potential patterns from an outcome"""
        candidates = []
        
        # Territory-based patterns
        if "territory" in outcome.context_factors:
            candidates.append({
                "pattern_id": f"territory_{outcome.context_factors['territory']}_{outcome.outcome_type.value}",
                "pattern_type": "territory_performance",
                "conditions": {
                    "territory": outcome.context_factors["territory"],
                    "outcome_type": outcome.outcome_type.value
                }
            })
        
        # Rep-based patterns
        candidates.append({
            "pattern_id": f"rep_{outcome.rep_id}_{outcome.outcome_type.value}",
            "pattern_type": "rep_performance",
            "conditions": {
                "rep_id": outcome.rep_id,
                "outcome_type": outcome.outcome_type.value
            }
        })
        
        # Deal size patterns
        deal_size_category = self._categorize_deal_size(outcome.deal_value)
        candidates.append({
            "pattern_id": f"deal_size_{deal_size_category}_{outcome.outcome_type.value}",
            "pattern_type": "deal_size_performance",
            "conditions": {
                "deal_size_category": deal_size_category,
                "outcome_type": outcome.outcome_type.value
            }
        })
        
        # Sales cycle patterns
        cycle_category = self._categorize_cycle_length(outcome.sales_cycle_days)
        candidates.append({
            "pattern_id": f"cycle_{cycle_category}_{outcome.outcome_type.value}",
            "pattern_type": "sales_cycle_performance",
            "conditions": {
                "cycle_category": cycle_category,
                "outcome_type": outcome.outcome_type.value
            }
        })
        
        # Strategy-based patterns
        if "strategy_type" in outcome.strategy_used:
            strategy_type = outcome.strategy_used["strategy_type"]
            candidates.append({
                "pattern_id": f"strategy_{strategy_type}_{outcome.outcome_type.value}",
                "pattern_type": "strategy_effectiveness",
                "conditions": {
                    "strategy_type": strategy_type,
                    "outcome_type": outcome.outcome_type.value
                }
            })
        
        return candidates
    
    def _categorize_deal_size(self, deal_value: float) -> str:
        """Categorize deal size for pattern learning"""
        if deal_value < 10000:
            return "small"
        elif deal_value < 50000:
            return "medium"
        elif deal_value < 200000:
            return "large"
        else:
            return "enterprise"
    
    def _categorize_cycle_length(self, cycle_days: int) -> str:
        """Categorize sales cycle length for pattern learning"""
        if cycle_days < 30:
            return "short"
        elif cycle_days < 90:
            return "medium"
        elif cycle_days < 180:
            return "long"
        else:
            return "extended"
    
    def _find_similar_outcomes(self, conditions: Dict[str, Any]) -> List[SalesOutcome]:
        """Find outcomes matching given conditions"""
        similar = []
        
        for outcome in self.outcomes_history:
            if self._matches_conditions(outcome, conditions):
                similar.append(outcome)
        
        return similar
    
    def _matches_conditions(self, outcome: SalesOutcome, conditions: Dict[str, Any]) -> bool:
        """Check if outcome matches pattern conditions"""
        for key, value in conditions.items():
            if key == "outcome_type" and outcome.outcome_type.value != value:
                return False
            elif key == "rep_id" and outcome.rep_id != value:
                return False
            elif key == "territory" and outcome.context_factors.get("territory") != value:
                return False
            elif key == "deal_size_category":
                if self._categorize_deal_size(outcome.deal_value) != value:
                    return False
            elif key == "cycle_category":
                if self._categorize_cycle_length(outcome.sales_cycle_days) != value:
                    return False
            elif key == "strategy_type":
                if outcome.strategy_used.get("strategy_type") != value:
                    return False
        
        return True
    
    async def _update_existing_pattern(self, pattern_id: str, outcome: SalesOutcome, candidate: Dict[str, Any]):
        """Update an existing learned pattern"""
        pattern = self.learned_patterns[pattern_id]
        
        # Update statistics with exponential moving average
        alpha = self.learning_rate
        
        # Update success rate
        is_success = outcome.outcome_type in [OutcomeType.WIN, OutcomeType.PIPELINE]
        current_success = 1.0 if is_success else 0.0
        pattern.success_rate = alpha * current_success + (1 - alpha) * pattern.success_rate
        
        # Update average deal value
        pattern.average_deal_value = alpha * outcome.deal_value + (1 - alpha) * pattern.average_deal_value
        
        # Update average cycle time
        pattern.average_cycle_time = int(
            alpha * outcome.sales_cycle_days + (1 - alpha) * pattern.average_cycle_time
        )
        
        # Update sample size and confidence
        pattern.sample_size += 1
        pattern.confidence_score = min(0.95, pattern.confidence_score + 0.01)
        pattern.last_updated = datetime.now()
        pattern.client_ids.add(outcome.client_id)
        
        # Update outcomes dictionary
        outcome_key = outcome.outcome_type.value
        if outcome_key not in pattern.outcomes:
            pattern.outcomes[outcome_key] = 0
        pattern.outcomes[outcome_key] += 1
    
    async def _create_new_pattern(self, pattern_id: str, similar_outcomes: List[SalesOutcome], candidate: Dict[str, Any]):
        """Create a new learned pattern"""
        # Calculate statistics from similar outcomes
        success_outcomes = [o for o in similar_outcomes if o.outcome_type in [OutcomeType.WIN, OutcomeType.PIPELINE]]
        success_rate = len(success_outcomes) / len(similar_outcomes)
        
        avg_deal_value = sum(o.deal_value for o in similar_outcomes) / len(similar_outcomes)
        avg_cycle_time = int(sum(o.sales_cycle_days for o in similar_outcomes) / len(similar_outcomes))
        
        # Create outcomes distribution
        outcomes_dist = {}
        for outcome in similar_outcomes:
            outcome_type = outcome.outcome_type.value
            if outcome_type not in outcomes_dist:
                outcomes_dist[outcome_type] = 0
            outcomes_dist[outcome_type] += 1
        
        # Calculate initial confidence based on sample size and consistency
        base_confidence = min(0.8, len(similar_outcomes) / 20)  # Up to 0.8 for 20+ samples
        consistency_bonus = abs(success_rate - 0.5) * 0.4  # Bonus for clear success/failure patterns
        initial_confidence = min(0.9, base_confidence + consistency_bonus)
        
        # Create pattern
        pattern = LearningPattern(
            pattern_id=pattern_id,
            pattern_type=candidate["pattern_type"],
            conditions=candidate["conditions"],
            outcomes=outcomes_dist,
            confidence_score=initial_confidence,
            sample_size=len(similar_outcomes),
            success_rate=success_rate,
            average_deal_value=avg_deal_value,
            average_cycle_time=avg_cycle_time,
            first_observed=min(o.outcome_date for o in similar_outcomes),
            last_updated=datetime.now(),
            client_ids=set(o.client_id for o in similar_outcomes)
        )
        
        self.learned_patterns[pattern_id] = pattern
        
        logger.info(f"Created new pattern {pattern_id}",
                   sample_size=len(similar_outcomes),
                   success_rate=success_rate)
    
    def get_patterns_for_context(self, context: Dict[str, Any], 
                                min_confidence: float = 0.7) -> List[LearningPattern]:
        """Get relevant patterns for given context"""
        relevant_patterns = []
        
        for pattern in self.learned_patterns.values():
            if pattern.confidence_score < min_confidence:
                continue
            
            # Check if pattern conditions match context
            matches = True
            for key, value in pattern.conditions.items():
                if key == "outcome_type":
                    continue  # Skip outcome type for context matching
                elif key in context and context[key] != value:
                    matches = False
                    break
                elif key == "deal_size_category" and "deal_value" in context:
                    if self._categorize_deal_size(context["deal_value"]) != value:
                        matches = False
                        break
                elif key == "cycle_category" and "expected_cycle_days" in context:
                    if self._categorize_cycle_length(context["expected_cycle_days"]) != value:
                        matches = False
                        break
            
            if matches:
                relevant_patterns.append(pattern)
        
        # Sort by confidence and sample size
        relevant_patterns.sort(key=lambda p: (p.confidence_score, p.sample_size), reverse=True)
        return relevant_patterns
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Generate insights from learned patterns"""
        if not self.learned_patterns:
            return {"status": "No patterns learned yet"}
        
        # Top performing patterns
        top_patterns = sorted(
            [p for p in self.learned_patterns.values() if p.sample_size >= self.min_pattern_samples],
            key=lambda p: p.success_rate * p.confidence_score,
            reverse=True
        )[:10]
        
        # Pattern type analysis
        pattern_types = defaultdict(list)
        for pattern in self.learned_patterns.values():
            pattern_types[pattern.pattern_type].append(pattern)
        
        type_analysis = {}
        for pattern_type, patterns in pattern_types.items():
            avg_success_rate = sum(p.success_rate for p in patterns) / len(patterns)
            avg_confidence = sum(p.confidence_score for p in patterns) / len(patterns)
            total_samples = sum(p.sample_size for p in patterns)
            
            type_analysis[pattern_type] = {
                "pattern_count": len(patterns),
                "average_success_rate": avg_success_rate,
                "average_confidence": avg_confidence,
                "total_samples": total_samples
            }
        
        # Recent learning trends
        recent_patterns = [
            p for p in self.learned_patterns.values()
            if p.last_updated > datetime.now() - timedelta(days=30)
        ]
        
        return {
            "total_patterns": len(self.learned_patterns),
            "high_confidence_patterns": len([p for p in self.learned_patterns.values() if p.confidence_score > 0.8]),
            "pattern_type_analysis": type_analysis,
            "top_performing_patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_type": p.pattern_type,
                    "success_rate": p.success_rate,
                    "confidence": p.confidence_score,
                    "sample_size": p.sample_size
                }
                for p in top_patterns
            ],
            "recent_learning_activity": len(recent_patterns),
            "total_outcomes_analyzed": len(self.outcomes_history)
        }


class StrategyAdapter:
    """
    Adapts sales strategies based on learned patterns
    
    Uses historical performance data and learned patterns to:
    - Recommend optimal strategies for given contexts
    - Adapt existing strategies based on performance
    - Generate new strategy variations
    """
    
    def __init__(self, learning_engine: SalesLearningEngine):
        self.learning_engine = learning_engine
        self.strategy_templates = self._initialize_strategy_templates()
        self.adaptation_history: List[Dict[str, Any]] = []
    
    def _initialize_strategy_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize strategy templates"""
        return {
            "territory_optimization": {
                "description": "Optimize territory assignments for balanced performance",
                "parameters": ["geographic_balance", "account_distribution", "rep_capacity"],
                "success_factors": ["travel_efficiency", "account_coverage", "rep_satisfaction"],
                "risk_factors": ["change_resistance", "customer_disruption"],
                "measurement_criteria": ["territory_balance", "coverage_metrics", "performance_variance"]
            },
            "quota_setting": {
                "description": "Set optimal quotas based on historical performance and market conditions",
                "parameters": ["historical_performance", "market_potential", "rep_capability"],
                "success_factors": ["achievability", "motivation", "fairness"],
                "risk_factors": ["under_performance", "demotivation", "turnover"],
                "measurement_criteria": ["attainment_rate", "performance_distribution", "rep_satisfaction"]
            },
            "coaching_intensive": {
                "description": "Intensive coaching program for underperforming reps",
                "parameters": ["performance_gaps", "skill_deficits", "coaching_capacity"],
                "success_factors": ["skill_improvement", "performance_lift", "engagement"],
                "risk_factors": ["coaching_resource_strain", "rep_overwhelm"],
                "measurement_criteria": ["skill_assessments", "performance_metrics", "activity_levels"]
            },
            "process_optimization": {
                "description": "Optimize sales processes for efficiency and effectiveness",
                "parameters": ["process_bottlenecks", "efficiency_metrics", "outcome_quality"],
                "success_factors": ["time_savings", "quality_improvement", "adoption_rate"],
                "risk_factors": ["process_complexity", "change_resistance"],
                "measurement_criteria": ["process_time", "quality_scores", "adoption_metrics"]
            }
        }
    
    async def recommend_strategy(self, context: Dict[str, Any], 
                               strategy_type: StrategyType) -> StrategyRecommendation:
        """Recommend optimal strategy based on learned patterns"""
        
        # Get relevant patterns for context
        relevant_patterns = self.learning_engine.get_patterns_for_context(context)
        
        # Get strategy template
        template_key = strategy_type.value
        if template_key not in self.strategy_templates:
            template_key = "process_optimization"  # Default fallback
        
        template = self.strategy_templates[template_key]
        
        # Analyze patterns to generate recommendation
        if relevant_patterns:
            recommendation_text, expected_outcomes, confidence = self._generate_pattern_based_recommendation(
                relevant_patterns, template, context
            )
            supporting_patterns = [p.pattern_id for p in relevant_patterns[:5]]
        else:
            # Generate template-based recommendation
            recommendation_text, expected_outcomes, confidence = self._generate_template_based_recommendation(
                template, context
            )
            supporting_patterns = []
        
        # Generate implementation steps
        implementation_steps = self._generate_implementation_steps(template, context, relevant_patterns)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(template, context, relevant_patterns)
        
        recommendation = StrategyRecommendation(
            recommendation_id=f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            strategy_type=strategy_type,
            recommendation=recommendation_text,
            supporting_patterns=supporting_patterns,
            expected_outcomes=expected_outcomes,
            confidence=confidence,
            risk_factors=risk_factors,
            implementation_steps=implementation_steps,
            measurement_criteria=template["measurement_criteria"]
        )
        
        # Record adaptation
        self.adaptation_history.append({
            "timestamp": datetime.now().isoformat(),
            "strategy_type": strategy_type.value,
            "context": context,
            "recommendation": recommendation_text,
            "confidence": confidence,
            "patterns_used": len(relevant_patterns)
        })
        
        return recommendation
    
    def _generate_pattern_based_recommendation(self, patterns: List[LearningPattern], 
                                             template: Dict[str, Any], 
                                             context: Dict[str, Any]) -> Tuple[str, Dict[str, float], float]:
        """Generate recommendation based on learned patterns"""
        
        # Analyze successful patterns
        successful_patterns = [p for p in patterns if p.success_rate > 0.7]
        
        if successful_patterns:
            # Find common success factors
            avg_success_rate = sum(p.success_rate for p in successful_patterns) / len(successful_patterns)
            avg_deal_value = sum(p.average_deal_value for p in successful_patterns) / len(successful_patterns)
            avg_cycle_time = sum(p.average_cycle_time for p in successful_patterns) / len(successful_patterns)
            
            # Generate recommendation based on successful patterns
            recommendation = f"Based on {len(successful_patterns)} successful patterns, recommend focusing on strategies that achieved {avg_success_rate:.1%} success rate with average deal value of ${avg_deal_value:,.0f} and {avg_cycle_time} day cycles."
            
            # Add pattern-specific insights
            pattern_insights = []
            for pattern in successful_patterns[:3]:  # Top 3 patterns
                if pattern.pattern_type == "territory_performance":
                    territory = pattern.conditions.get("territory", "unknown")
                    pattern_insights.append(f"Territory {territory} shows strong performance")
                elif pattern.pattern_type == "rep_performance":
                    rep_id = pattern.conditions.get("rep_id", "unknown")
                    pattern_insights.append(f"Rep {rep_id} demonstrates effective approach")
                elif pattern.pattern_type == "strategy_effectiveness":
                    strategy = pattern.conditions.get("strategy_type", "unknown")
                    pattern_insights.append(f"Strategy {strategy} shows consistent results")
            
            if pattern_insights:
                recommendation += " Key insights: " + "; ".join(pattern_insights) + "."
            
            expected_outcomes = {
                "success_probability": avg_success_rate,
                "expected_deal_value": avg_deal_value,
                "expected_cycle_days": avg_cycle_time,
                "confidence_interval": 0.1  # 10% variance
            }
            
            # Calculate confidence based on pattern quality
            pattern_confidence = sum(p.confidence_score for p in successful_patterns) / len(successful_patterns)
            overall_confidence = min(0.9, pattern_confidence * 0.9)  # Slight discount for uncertainty
            
        else:
            # No successful patterns - conservative recommendation
            recommendation = f"Limited successful patterns found. Recommend cautious approach with close monitoring and frequent adjustments."
            
            expected_outcomes = {
                "success_probability": 0.5,
                "expected_deal_value": context.get("average_deal_value", 50000),
                "expected_cycle_days": context.get("average_cycle_days", 90),
                "confidence_interval": 0.3  # High uncertainty
            }
            
            overall_confidence = 0.4  # Low confidence
        
        return recommendation, expected_outcomes, overall_confidence
    
    def _generate_template_based_recommendation(self, template: Dict[str, Any], 
                                              context: Dict[str, Any]) -> Tuple[str, Dict[str, float], float]:
        """Generate recommendation based on template when no patterns available"""
        
        recommendation = f"{template['description']}. Focus on {', '.join(template['success_factors'][:3])}."
        
        # Generate conservative expected outcomes
        expected_outcomes = {
            "success_probability": 0.6,  # Moderate expectation
            "expected_improvement": 0.15,  # 15% improvement
            "implementation_time_weeks": 4,
            "confidence_interval": 0.25  # Moderate uncertainty
        }
        
        confidence = 0.5  # Moderate confidence for template-based recommendations
        
        return recommendation, expected_outcomes, confidence
    
    def _generate_implementation_steps(self, template: Dict[str, Any], 
                                     context: Dict[str, Any], 
                                     patterns: List[LearningPattern]) -> List[str]:
        """Generate implementation steps based on template and patterns"""
        
        base_steps = [
            f"Analyze current state of {template['parameters'][0]}",
            f"Identify improvement opportunities in {template['parameters'][1] if len(template['parameters']) > 1 else 'key areas'}",
            "Develop detailed implementation plan",
            "Execute changes with monitoring",
            "Measure results and adjust as needed"
        ]
        
        # Add pattern-specific steps
        if patterns:
            successful_patterns = [p for p in patterns if p.success_rate > 0.7]
            if successful_patterns:
                pattern_step = f"Apply insights from {len(successful_patterns)} successful similar cases"
                base_steps.insert(2, pattern_step)
        
        # Add context-specific steps
        if "urgent" in context and context["urgent"]:
            base_steps.insert(0, "Fast-track due to urgency - compress timeline")
        
        if "budget_constraints" in context:
            base_steps.insert(-1, "Implement cost-effective measures within budget constraints")
        
        return base_steps
    
    def _identify_risk_factors(self, template: Dict[str, Any], 
                              context: Dict[str, Any], 
                              patterns: List[LearningPattern]) -> List[str]:
        """Identify risk factors based on template and patterns"""
        
        risk_factors = template.get("risk_factors", []).copy()
        
        # Add pattern-based risk factors
        if patterns:
            failed_patterns = [p for p in patterns if p.success_rate < 0.4]
            if failed_patterns:
                risk_factors.append(f"Similar approaches failed in {len(failed_patterns)} cases")
        
        # Add context-specific risks
        if "team_size" in context and context["team_size"] > 20:
            risk_factors.append("Large team size may complicate implementation")
        
        if "timeline_pressure" in context and context["timeline_pressure"]:
            risk_factors.append("Tight timeline increases implementation risk")
        
        return risk_factors
    
    async def adapt_strategy_based_on_feedback(self, strategy_id: str, 
                                             performance_data: Dict[str, Any],
                                             context: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt strategy based on performance feedback"""
        
        # Analyze performance vs expectations
        actual_results = performance_data.get("results", {})
        expected_results = performance_data.get("expected", {})
        
        performance_ratio = {}
        for metric, actual in actual_results.items():
            expected = expected_results.get(metric, actual)
            if expected > 0:
                performance_ratio[metric] = actual / expected
            else:
                performance_ratio[metric] = 1.0
        
        # Determine adaptation type
        overall_performance = sum(performance_ratio.values()) / len(performance_ratio)
        
        if overall_performance > 1.2:
            # Outperforming - amplify successful elements
            adaptation_type = "amplify"
            adaptation_actions = [
                "Identify and amplify successful strategy elements",
                "Scale successful approaches to broader context",
                "Document best practices for replication"
            ]
        elif overall_performance < 0.8:
            # Underperforming - adjust approach
            adaptation_type = "adjust"
            adaptation_actions = [
                "Analyze underperformance root causes",
                "Adjust strategy parameters based on learnings",
                "Implement corrective measures",
                "Increase monitoring frequency"
            ]
        else:
            # Meeting expectations - minor optimization
            adaptation_type = "optimize"
            adaptation_actions = [
                "Fine-tune strategy parameters",
                "Look for incremental improvements",
                "Maintain current approach with minor adjustments"
            ]
        
        # Generate specific recommendations
        specific_recommendations = self._generate_adaptation_recommendations(
            performance_ratio, context, adaptation_type
        )
        
        adaptation_result = {
            "strategy_id": strategy_id,
            "adaptation_type": adaptation_type,
            "performance_analysis": {
                "overall_performance": overall_performance,
                "metric_performance": performance_ratio
            },
            "adaptation_actions": adaptation_actions,
            "specific_recommendations": specific_recommendations,
            "timestamp": datetime.now().isoformat()
        }
        
        # Record adaptation
        self.adaptation_history.append(adaptation_result)
        
        return adaptation_result
    
    def _generate_adaptation_recommendations(self, performance_ratio: Dict[str, float], 
                                           context: Dict[str, Any], 
                                           adaptation_type: str) -> List[str]:
        """Generate specific adaptation recommendations"""
        
        recommendations = []
        
        # Analyze specific underperforming metrics
        underperforming = {k: v for k, v in performance_ratio.items() if v < 0.8}
        overperforming = {k: v for k, v in performance_ratio.items() if v > 1.2}
        
        for metric, ratio in underperforming.items():
            if metric == "success_probability":
                recommendations.append(f"Success rate below target by {(1-ratio)*100:.0f}% - review qualification criteria")
            elif metric == "expected_deal_value":
                recommendations.append(f"Deal values below target - focus on value positioning and upselling")
            elif metric == "expected_cycle_days":
                if ratio > 1.0:  # Longer cycles than expected
                    recommendations.append(f"Sales cycles {(ratio-1)*100:.0f}% longer - streamline decision process")
        
        for metric, ratio in overperforming.items():
            if metric == "success_probability":
                recommendations.append(f"Success rate exceeds target - consider scaling approach")
            elif metric == "expected_deal_value":
                recommendations.append(f"Deal values above target - document value creation strategies")
        
        # Add adaptation-type specific recommendations
        if adaptation_type == "amplify":
            recommendations.append("Document and systematize successful practices")
            recommendations.append("Train team on high-performing approaches")
        elif adaptation_type == "adjust":
            recommendations.append("Conduct root cause analysis on underperformance")
            recommendations.append("Implement A/B testing for strategy variations")
        
        return recommendations


class PerformanceOptimizer:
    """
    Optimizes team and process performance based on learned patterns
    """
    
    def __init__(self, learning_engine: SalesLearningEngine, strategy_adapter: StrategyAdapter):
        self.learning_engine = learning_engine
        self.strategy_adapter = strategy_adapter
        self.optimization_history: List[Dict[str, Any]] = []
    
    async def optimize_team_performance(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize team performance based on learned patterns"""
        
        # Analyze team performance patterns
        team_patterns = self._analyze_team_patterns(team_data)
        
        # Identify optimization opportunities
        opportunities = self._identify_optimization_opportunities(team_patterns, team_data)
        
        # Generate optimization recommendations
        recommendations = await self._generate_optimization_recommendations(opportunities, team_data)
        
        optimization_result = {
            "team_id": team_data.get("team_id", "unknown"),
            "analysis_date": datetime.now().isoformat(),
            "team_patterns": team_patterns,
            "optimization_opportunities": opportunities,
            "recommendations": recommendations,
            "expected_improvement": self._calculate_expected_improvement(opportunities),
            "implementation_priority": self._prioritize_recommendations(recommendations)
        }
        
        self.optimization_history.append(optimization_result)
        
        return optimization_result
    
    def _analyze_team_patterns(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance patterns within the team"""
        
        team_members = team_data.get("members", [])
        if not team_members:
            return {"status": "No team member data available"}
        
        # Get patterns for each team member
        member_patterns = {}
        for member in team_members:
            member_id = member.get("rep_id", member.get("id", "unknown"))
            
            # Get patterns for this rep
            context = {"rep_id": member_id}
            patterns = self.learning_engine.get_patterns_for_context(context)
            
            if patterns:
                member_patterns[member_id] = {
                    "pattern_count": len(patterns),
                    "avg_success_rate": sum(p.success_rate for p in patterns) / len(patterns),
                    "avg_confidence": sum(p.confidence_score for p in patterns) / len(patterns),
                    "top_pattern": max(patterns, key=lambda p: p.confidence_score).pattern_id
                }
            else:
                member_patterns[member_id] = {
                    "pattern_count": 0,
                    "avg_success_rate": 0.5,
                    "avg_confidence": 0.3,
                    "top_pattern": None
                }
        
        # Analyze team-level patterns
        if member_patterns:
            team_avg_success = sum(p["avg_success_rate"] for p in member_patterns.values()) / len(member_patterns)
            performance_variance = np.var([p["avg_success_rate"] for p in member_patterns.values()])
            high_performers = [k for k, v in member_patterns.items() if v["avg_success_rate"] > team_avg_success + 0.1]
            low_performers = [k for k, v in member_patterns.items() if v["avg_success_rate"] < team_avg_success - 0.1]
        else:
            team_avg_success = 0.5
            performance_variance = 0
            high_performers = []
            low_performers = []
        
        return {
            "member_patterns": member_patterns,
            "team_average_success": team_avg_success,
            "performance_variance": performance_variance,
            "high_performers": high_performers,
            "low_performers": low_performers,
            "team_size": len(team_members)
        }
    
    def _identify_optimization_opportunities(self, team_patterns: Dict[str, Any], 
                                           team_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific optimization opportunities"""
        
        opportunities = []
        
        # High performance variance opportunity
        if team_patterns.get("performance_variance", 0) > 0.05:
            opportunities.append({
                "type": "performance_leveling",
                "description": "High performance variance across team members",
                "potential_impact": "medium",
                "affected_members": len(team_patterns.get("low_performers", [])),
                "recommendation": "Implement peer mentoring between high and low performers"
            })
        
        # Low overall performance opportunity
        if team_patterns.get("team_average_success", 0.5) < 0.6:
            opportunities.append({
                "type": "overall_performance",
                "description": "Team average performance below target",
                "potential_impact": "high",
                "affected_members": team_patterns.get("team_size", 0),
                "recommendation": "Comprehensive team training and process optimization"
            })
        
        # Pattern learning opportunity
        low_pattern_members = [
            member_id for member_id, patterns in team_patterns.get("member_patterns", {}).items()
            if patterns["pattern_count"] < 3
        ]
        
        if len(low_pattern_members) > len(team_patterns.get("member_patterns", {})) * 0.3:
            opportunities.append({
                "type": "pattern_learning",
                "description": "Many team members lack established performance patterns",
                "potential_impact": "medium",
                "affected_members": len(low_pattern_members),
                "recommendation": "Increase activity tracking and outcome recording for pattern development"
            })
        
        return opportunities
    
    async def _generate_optimization_recommendations(self, opportunities: List[Dict[str, Any]], 
                                                   team_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific optimization recommendations"""
        
        recommendations = []
        
        for opportunity in opportunities:
            if opportunity["type"] == "performance_leveling":
                # Generate peer mentoring recommendations
                recommendations.append({
                    "title": "Implement Peer Mentoring Program",
                    "description": "Pair high performers with struggling team members",
                    "implementation_steps": [
                        "Identify mentor-mentee pairs based on performance and compatibility",
                        "Set up structured mentoring program with regular check-ins",
                        "Track progress and adjust pairs as needed"
                    ],
                    "expected_impact": "15-25% improvement in low performer results",
                    "timeline": "6-8 weeks",
                    "resources_required": ["2 hours/week mentoring time", "Program coordination"]
                })
            
            elif opportunity["type"] == "overall_performance":
                # Generate comprehensive improvement recommendations
                recommendations.append({
                    "title": "Comprehensive Performance Improvement Program",
                    "description": "Multi-faceted approach to lift overall team performance",
                    "implementation_steps": [
                        "Conduct skills gap analysis for each team member",
                        "Implement targeted training programs",
                        "Optimize sales processes and tools",
                        "Increase coaching frequency and quality"
                    ],
                    "expected_impact": "20-30% improvement in team metrics",
                    "timeline": "12-16 weeks",
                    "resources_required": ["Training budget", "Management time", "Process optimization"]
                })
            
            elif opportunity["type"] == "pattern_learning":
                # Generate pattern development recommendations
                recommendations.append({
                    "title": "Accelerate Pattern Learning and Recognition",
                    "description": "Improve data capture and analysis to develop performance patterns faster",
                    "implementation_steps": [
                        "Implement comprehensive activity and outcome tracking",
                        "Conduct weekly pattern review sessions",
                        "Share successful patterns across team",
                        "Set up automated pattern detection and reporting"
                    ],
                    "expected_impact": "Faster identification of effective approaches",
                    "timeline": "4-6 weeks",
                    "resources_required": ["CRM configuration", "Weekly review time"]
                })
        
        return recommendations
    
    def _calculate_expected_improvement(self, opportunities: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate expected improvement from optimization opportunities"""
        
        if not opportunities:
            return {"overall_improvement": 0.0}
        
        # Calculate potential improvement based on opportunity impact
        impact_values = {
            "high": 0.25,     # 25% improvement
            "medium": 0.15,   # 15% improvement  
            "low": 0.08       # 8% improvement
        }
        
        total_impact = 0
        for opportunity in opportunities:
            impact = impact_values.get(opportunity.get("potential_impact", "low"), 0.05)
            # Diminishing returns for multiple opportunities
            total_impact += impact * (0.8 ** len(opportunities))
        
        return {
            "overall_improvement": min(total_impact, 0.5),  # Cap at 50% improvement
            "opportunity_count": len(opportunities),
            "confidence": 0.7 if len(opportunities) <= 3 else 0.5
        }
    
    def _prioritize_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize recommendations by impact and feasibility"""
        
        # Score each recommendation
        for rec in recommendations:
            impact_score = 0
            if "20-30%" in rec.get("expected_impact", ""):
                impact_score = 3
            elif "15-25%" in rec.get("expected_impact", ""):
                impact_score = 2
            else:
                impact_score = 1
            
            # Parse timeline for feasibility score
            timeline = rec.get("timeline", "")
            if "4-6" in timeline or "6-8" in timeline:
                feasibility_score = 3
            elif "8-12" in timeline:
                feasibility_score = 2
            else:
                feasibility_score = 1
            
            # Resource intensity (inverse scoring)
            resources = len(rec.get("resources_required", []))
            resource_score = max(1, 4 - resources)
            
            # Overall priority score
            rec["priority_score"] = (impact_score * 0.5 + feasibility_score * 0.3 + resource_score * 0.2)
        
        # Sort by priority score
        prioritized = sorted(recommendations, key=lambda x: x.get("priority_score", 0), reverse=True)
        
        # Add priority labels
        for i, rec in enumerate(prioritized):
            if i == 0:
                rec["priority"] = "High"
            elif i < len(prioritized) // 2:
                rec["priority"] = "Medium"
            else:
                rec["priority"] = "Low"
        
        return prioritized


class ClientPreferenceLearner:
    """
    Learns client-specific preferences and customization patterns
    """
    
    def __init__(self, client_id: str, storage_dir: Optional[Path] = None):
        self.client_id = client_id
        self.storage_dir = storage_dir or Path("client_configs") / client_id
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Client preferences and patterns
        self.preferences: Dict[str, Any] = {}
        self.interaction_patterns: List[Dict[str, Any]] = []
        self.customization_history: List[Dict[str, Any]] = []
        
        # Load existing data
        self._load_preference_data()
    
    def _load_preference_data(self):
        """Load client preference data"""
        try:
            prefs_file = self.storage_dir / "client_preferences.json"
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    data = json.load(f)
                    self.preferences = data.get("preferences", {})
                    self.interaction_patterns = data.get("interaction_patterns", [])
                    self.customization_history = data.get("customization_history", [])
        except Exception as e:
            logger.warning(f"Could not load client preferences: {e}")
    
    def _save_preference_data(self):
        """Save client preference data"""
        try:
            prefs_file = self.storage_dir / "client_preferences.json"
            data = {
                "preferences": self.preferences,
                "interaction_patterns": self.interaction_patterns[-100:],  # Keep recent
                "customization_history": self.customization_history[-50:]  # Keep recent
            }
            with open(prefs_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save client preferences: {e}")
    
    async def record_interaction(self, interaction_type: str, context: Dict[str, Any], 
                               satisfaction_score: Optional[float] = None):
        """Record client interaction for preference learning"""
        
        interaction = {
            "interaction_id": f"int_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "interaction_type": interaction_type,
            "context": context,
            "satisfaction_score": satisfaction_score,
            "timestamp": datetime.now().isoformat()
        }
        
        self.interaction_patterns.append(interaction)
        
        # Update preferences based on interaction
        await self._update_preferences_from_interaction(interaction)
        
        self._save_preference_data()
    
    async def _update_preferences_from_interaction(self, interaction: Dict[str, Any]):
        """Update preferences based on interaction data"""
        
        interaction_type = interaction["interaction_type"]
        context = interaction["context"]
        satisfaction = interaction.get("satisfaction_score", 0.5)
        
        # Update communication preferences
        if interaction_type in ["report_generation", "briefing", "analysis"]:
            current_detail = self.preferences.get("report_detail_level", 0.5)
            
            if "detailed" in str(context).lower() and satisfaction > 0.7:
                self.preferences["report_detail_level"] = min(1.0, current_detail + 0.1)
            elif "summary" in str(context).lower() and satisfaction > 0.7:
                self.preferences["report_detail_level"] = max(0.0, current_detail - 0.1)
        
        # Update autonomy preferences
        if interaction_type in ["decision_making", "recommendation"]:
            current_autonomy = self.preferences.get("autonomy_level", 0.5)
            
            if "autonomous" in str(context).lower() and satisfaction > 0.7:
                self.preferences["autonomy_level"] = min(1.0, current_autonomy + 0.1)
            elif "human_approval" in str(context).lower() and satisfaction > 0.7:
                self.preferences["autonomy_level"] = max(0.0, current_autonomy - 0.1)
        
        # Update frequency preferences
        if "frequency" in context:
            freq = context["frequency"]
            if satisfaction > 0.7:
                self.preferences[f"{interaction_type}_frequency"] = freq
    
    def get_client_preferences(self) -> Dict[str, Any]:
        """Get current client preferences"""
        
        # Set defaults for missing preferences
        defaults = {
            "report_detail_level": 0.6,    # Moderate detail
            "autonomy_level": 0.4,         # More human oversight
            "communication_frequency": "weekly",
            "preferred_analysis_depth": "standard",
            "notification_preferences": ["email", "dashboard"],
            "decision_consultation": True   # Prefer consultation on decisions
        }
        
        # Merge with learned preferences
        combined_prefs = defaults.copy()
        combined_prefs.update(self.preferences)
        
        return combined_prefs
    
    def get_preference_insights(self) -> Dict[str, Any]:
        """Get insights about client preferences and patterns"""
        
        if not self.interaction_patterns:
            return {"status": "No interaction data available"}
        
        # Analyze interaction patterns
        recent_interactions = [
            i for i in self.interaction_patterns
            if datetime.fromisoformat(i["timestamp"]) > datetime.now() - timedelta(days=30)
        ]
        
        # Most common interaction types
        interaction_types = defaultdict(int)
        satisfaction_by_type = defaultdict(list)
        
        for interaction in recent_interactions:
            itype = interaction["interaction_type"]
            interaction_types[itype] += 1
            
            if interaction.get("satisfaction_score") is not None:
                satisfaction_by_type[itype].append(interaction["satisfaction_score"])
        
        # Calculate average satisfaction by type
        avg_satisfaction_by_type = {}
        for itype, scores in satisfaction_by_type.items():
            if scores:
                avg_satisfaction_by_type[itype] = sum(scores) / len(scores)
        
        return {
            "total_interactions": len(self.interaction_patterns),
            "recent_interactions": len(recent_interactions),
            "most_common_interactions": dict(sorted(interaction_types.items(), 
                                                  key=lambda x: x[1], reverse=True)[:5]),
            "satisfaction_by_interaction_type": avg_satisfaction_by_type,
            "learned_preferences": self.preferences,
            "preference_confidence": len(recent_interactions) / 50  # Confidence based on interaction volume
        }


# Factory functions and utilities
async def create_sales_learning_system(client_id: str, 
                                     storage_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Factory function to create complete sales learning system"""
    
    learning_engine = SalesLearningEngine(client_id, storage_dir)
    strategy_adapter = StrategyAdapter(learning_engine)
    performance_optimizer = PerformanceOptimizer(learning_engine, strategy_adapter)
    client_learner = ClientPreferenceLearner(client_id, storage_dir)
    
    logger.info(f"Sales learning system created for client {client_id}")
    
    return {
        "learning_engine": learning_engine,
        "strategy_adapter": strategy_adapter,
        "performance_optimizer": performance_optimizer,
        "client_learner": client_learner
    }