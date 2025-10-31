"""
Preference Manager
Learns and stores user preferences to improve automation and personalization
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import json
import asyncio
import structlog
from pydantic import BaseModel, Field
from collections import defaultdict
from src.utils.file_operations import SafeFileOperations

logger = structlog.get_logger(__name__)
safe_file_ops = SafeFileOperations()


class PreferenceType(str, Enum):
    """Types of preferences."""
    DATA_SOURCE = "data_source"  # Which data source to use
    WORKFLOW = "workflow"  # How to execute workflows
    COMMUNICATION = "communication"  # Communication preferences
    AUTOMATION = "automation"  # Automation preferences
    FORMAT = "format"  # Output format preferences
    PRIORITY = "priority"  # Prioritization preferences


class LearningEvent(BaseModel):
    """
    A learning event that teaches us about user preferences.

    Attributes:
        event_type: Type of learning event
        business_function: What business function this relates to
        context: Context of the decision
        user_choice: What the user chose
        alternatives: What other options were available
        outcome: Outcome of the choice (if known)
        confidence_impact: How much this improved confidence
        timestamp: When this event occurred
    """
    event_type: str
    business_function: str
    context: Dict[str, Any]
    user_choice: Any
    alternatives: Optional[List[Any]] = None
    outcome: Optional[str] = None
    confidence_impact: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Preference(BaseModel):
    """
    A learned user preference.

    Attributes:
        preference_key: Unique key for this preference
        preference_type: Type of preference
        business_function: Business function this applies to
        value: The preferred value
        confidence: Confidence in this preference (0-1)
        usage_count: How many times this has been applied
        success_count: How many times it led to success
        last_used: When it was last used
        context_rules: Context rules that trigger this preference
        metadata: Additional metadata
    """
    preference_key: str
    preference_type: PreferenceType
    business_function: str
    value: Any
    confidence: float = 0.5
    usage_count: int = 0
    success_count: int = 0
    last_used: Optional[datetime] = None
    context_rules: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PreferenceManager:
    """
    Manages learning and storage of user preferences.

    Features:
    - Record learning events
    - Update preferences based on events
    - Retrieve preferences for business functions
    - Infer preferences from behavior patterns
    - Track preference confidence
    - Decay old preferences

    Usage:
        >>> manager = PreferenceManager(client_id="client_123")
        >>> await manager.record_learning_event(
        ...     event_type='data_source_selection',
        ...     business_function='lead_enrichment',
        ...     context={'available_sources': ['apollo', 'zoominfo']},
        ...     user_choice='apollo'
        ... )
        >>> prefs = await manager.get_preferences('lead_enrichment')
        >>> print(prefs['data_source'])
    """

    def __init__(
        self,
        client_id: str,
        storage_path: Optional[Path] = None,
        confidence_decay_days: int = 30,
        min_confidence_threshold: float = 0.3
    ) -> Any:
        """
        Initialize preference manager.

        Args:
            client_id: Client identifier
            storage_path: Path to store preferences (optional)
            confidence_decay_days: Days before preference confidence starts decaying
            min_confidence_threshold: Minimum confidence to keep a preference
        """
        self.client_id = client_id
        self.confidence_decay_days = confidence_decay_days
        self.min_confidence_threshold = min_confidence_threshold

        # Storage
        if storage_path:
            self.storage_path = Path(storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
        else:
            self.storage_path = None

        # In-memory storage
        self.preferences: Dict[str, Preference] = {}
        self.learning_events: List[LearningEvent] = []

        # Load existing preferences if storage path exists
        if self.storage_path:
            self._load_from_disk()

        logger.info(
            "preference_manager_initialized",
            client_id=client_id,
            decay_days=confidence_decay_days
        )

    def _get_preference_file(self) -> Optional[Path]:
        """Get path to preference storage file."""
        if not self.storage_path:
            return None
        return self.storage_path / f"{self.client_id}_preferences.json"

    def _get_events_file(self) -> Optional[Path]:
        """Get path to learning events storage file."""
        if not self.storage_path:
            return None
        return self.storage_path / f"{self.client_id}_events.json"

    def _load_from_disk(self) -> Any:
        """Load preferences and events from disk."""
        try:
            # Load preferences using safe file operations
            pref_file = self._get_preference_file()
            if pref_file and pref_file.exists():
                data = safe_file_ops.read_json(pref_file)
                if data:
                    for key, pref_dict in data.items():
                        # Convert timestamps
                        if pref_dict.get('last_used'):
                            pref_dict['last_used'] = datetime.fromisoformat(pref_dict['last_used'])
                        pref_dict['created_at'] = datetime.fromisoformat(pref_dict['created_at'])
                        pref_dict['updated_at'] = datetime.fromisoformat(pref_dict['updated_at'])

                        self.preferences[key] = Preference(**pref_dict)

                    logger.info("preferences_loaded", count=len(self.preferences))

            # Load events using safe file operations
            events_file = self._get_events_file()
            if events_file and events_file.exists():
                data = safe_file_ops.read_json(events_file)
                if data:
                    for event_dict in data:
                        event_dict['timestamp'] = datetime.fromisoformat(event_dict['timestamp'])
                        self.learning_events.append(LearningEvent(**event_dict))

                logger.info("learning_events_loaded", count=len(self.learning_events))

        except Exception as e:
            logger.error("load_from_disk_failed", error=str(e))

    def _save_to_disk(self) -> Any:
        """Save preferences and events to disk."""
        try:
            # Save preferences
            pref_file = self._get_preference_file()
            if pref_file:
                data = {}
                for key, pref in self.preferences.items():
                    pref_dict = pref.dict()
                    # Convert timestamps to ISO format
                    if pref_dict.get('last_used'):
                        pref_dict['last_used'] = pref_dict['last_used'].isoformat()
                    pref_dict['created_at'] = pref_dict['created_at'].isoformat()
                    pref_dict['updated_at'] = pref_dict['updated_at'].isoformat()
                    data[key] = pref_dict

                # Use safe file operations with locking
                safe_file_ops.write_json(pref_file, data)

            # Save events (keep last 1000)
            events_file = self._get_events_file()
            if events_file:
                recent_events = self.learning_events[-1000:]
                data = []
                for event in recent_events:
                    event_dict = event.dict()
                    event_dict['timestamp'] = event_dict['timestamp'].isoformat()
                    data.append(event_dict)

                # Use safe file operations with locking
                safe_file_ops.write_json(events_file, data)

            logger.info("preferences_saved", count=len(self.preferences))

        except Exception as e:
            logger.error("save_to_disk_failed", error=str(e))

    async def record_learning_event(
        self,
        event_type: str,
        business_function: str,
        context: Dict[str, Any],
        user_choice: Any,
        alternatives: Optional[List[Any]] = None,
        outcome: Optional[str] = None
    ) -> bool:
        """
        Record a learning event.

        Args:
            event_type: Type of event (e.g., 'data_source_selection')
            business_function: Business function context
            context: Context of the decision
            user_choice: What the user chose
            alternatives: What other options were available
            outcome: Outcome of the choice ('success', 'failure', etc.)

        Returns:
            True if event recorded successfully

        Example:
            >>> await manager.record_learning_event(
            ...     event_type='email_tone_selection',
            ...     business_function='email_sequencing',
            ...     context={'recipient_role': 'CEO'},
            ...     user_choice='professional',
            ...     alternatives=['friendly', 'direct'],
            ...     outcome='success'
            ... )
        """
        try:
            # Calculate confidence impact
            confidence_impact = 0.0
            if outcome == 'success':
                confidence_impact = 0.1
            elif outcome == 'failure':
                confidence_impact = -0.05

            # Create event
            event = LearningEvent(
                event_type=event_type,
                business_function=business_function,
                context=context,
                user_choice=user_choice,
                alternatives=alternatives,
                outcome=outcome,
                confidence_impact=confidence_impact
            )

            self.learning_events.append(event)

            # Update preferences based on this event
            await self.update_preferences(event)

            # Save to disk
            if self.storage_path:
                await asyncio.to_thread(self._save_to_disk)

            logger.info(
                "learning_event_recorded",
                event_type=event_type,
                function=business_function,
                choice=user_choice
            )

            return True

        except Exception as e:
            logger.error("record_learning_event_failed", error=str(e))
            return False

    async def update_preferences(self, event: LearningEvent) -> bool:
        """
        Update preferences based on a learning event.

        Args:
            event: Learning event to learn from

        Returns:
            True if preferences updated
        """
        try:
            # Generate preference key
            pref_key = f"{event.business_function}:{event.event_type}"

            # Get or create preference
            if pref_key in self.preferences:
                pref = self.preferences[pref_key]
            else:
                # Determine preference type from event type
                pref_type = self._infer_preference_type(event.event_type)

                pref = Preference(
                    preference_key=pref_key,
                    preference_type=pref_type,
                    business_function=event.business_function,
                    value=event.user_choice,
                    context_rules=event.context
                )

            # Update preference value if user chose differently
            if pref.value != event.user_choice:
                # User changed their mind - reset confidence
                pref.value = event.user_choice
                pref.confidence = 0.5
                pref.success_count = 0
                pref.usage_count = 0
            else:
                # Reinforce existing preference
                pref.usage_count += 1

                # Update confidence based on outcome
                if event.outcome == 'success':
                    pref.success_count += 1
                    pref.confidence = min(pref.confidence + 0.05, 1.0)
                elif event.outcome == 'failure':
                    pref.confidence = max(pref.confidence - 0.03, 0.0)

            # Update timestamps
            pref.last_used = datetime.utcnow()
            pref.updated_at = datetime.utcnow()

            # Update context rules (merge with existing)
            for key, value in event.context.items():
                if key not in pref.context_rules:
                    pref.context_rules[key] = value

            # Store updated preference
            self.preferences[pref_key] = pref

            logger.info(
                "preference_updated",
                key=pref_key,
                value=pref.value,
                confidence=pref.confidence
            )

            return True

        except Exception as e:
            logger.error("update_preferences_failed", error=str(e))
            return False

    def _infer_preference_type(self, event_type: str) -> PreferenceType:
        """Infer preference type from event type."""
        type_mapping = {
            'data_source': PreferenceType.DATA_SOURCE,
            'workflow': PreferenceType.WORKFLOW,
            'communication': PreferenceType.COMMUNICATION,
            'email': PreferenceType.COMMUNICATION,
            'automation': PreferenceType.AUTOMATION,
            'format': PreferenceType.FORMAT,
            'priority': PreferenceType.PRIORITY,
        }

        for keyword, pref_type in type_mapping.items():
            if keyword in event_type.lower():
                return pref_type

        return PreferenceType.WORKFLOW  # Default

    async def get_preferences(
        self,
        business_function: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get preferences for a business function.

        Args:
            business_function: Business function to get preferences for
            context: Optional context to match against

        Returns:
            Dictionary of preferences

        Example:
            >>> prefs = await manager.get_preferences(
            ...     'lead_enrichment',
            ...     context={'industry': 'SaaS'}
            ... )
            >>> print(prefs['data_source'])  # 'apollo'
        """
        try:
            # Apply confidence decay first
            await self._apply_confidence_decay()

            result = {}

            # Find all preferences for this business function
            for pref_key, pref in self.preferences.items():
                if pref.business_function != business_function:
                    continue

                # Skip low-confidence preferences
                if pref.confidence < self.min_confidence_threshold:
                    continue

                # Check context match if provided
                if context:
                    matches = self._matches_context(pref.context_rules, context)
                    if not matches:
                        continue

                # Extract preference name from key
                pref_name = pref_key.split(':')[-1]

                result[pref_name] = {
                    'value': pref.value,
                    'confidence': pref.confidence,
                    'usage_count': pref.usage_count,
                    'success_rate': (
                        pref.success_count / pref.usage_count
                        if pref.usage_count > 0 else 0.0
                    ),
                    'last_used': pref.last_used.isoformat() if pref.last_used else None
                }

            logger.info(
                "preferences_retrieved",
                function=business_function,
                count=len(result)
            )

            return result

        except Exception as e:
            logger.error("get_preferences_failed", error=str(e))
            return {}

    def _matches_context(
        self,
        rules: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if context matches preference rules."""
        if not rules:
            return True  # No rules means always matches

        for key, expected_value in rules.items():
            if key not in context:
                continue

            actual_value = context[key]

            # Handle list matching
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            # Handle exact matching
            elif actual_value != expected_value:
                return False

        return True

    async def infer_preferences(
        self,
        business_function: str,
        min_event_count: int = 3
    ) -> Dict[str, Preference]:
        """
        Infer preferences from behavior patterns.

        Args:
            business_function: Business function to analyze
            min_event_count: Minimum events needed to infer preference

        Returns:
            Dictionary of inferred preferences

        Example:
            >>> inferred = await manager.infer_preferences('lead_enrichment')
            >>> for pref_name, pref in inferred.items():
            ...     print(f"{pref_name}: {pref.value} (confidence: {pref.confidence})")
        """
        try:
            # Get events for this function
            relevant_events = [
                e for e in self.learning_events
                if e.business_function == business_function
            ]

            if len(relevant_events) < min_event_count:
                return {}

            # Group events by type
            events_by_type = defaultdict(list)
            for event in relevant_events:
                events_by_type[event.event_type].append(event)

            inferred = {}

            # Analyze each event type
            for event_type, events in events_by_type.items():
                if len(events) < min_event_count:
                    continue

                # Count user choices
                choice_counts = defaultdict(int)
                success_counts = defaultdict(int)

                for event in events:
                    choice = str(event.user_choice)
                    choice_counts[choice] += 1
                    if event.outcome == 'success':
                        success_counts[choice] += 1

                # Find most common choice
                most_common = max(choice_counts, key=choice_counts.get)
                total_uses = choice_counts[most_common]
                successes = success_counts.get(most_common, 0)

                # Calculate confidence
                frequency_ratio = total_uses / len(events)
                success_ratio = successes / total_uses if total_uses > 0 else 0
                confidence = (frequency_ratio + success_ratio) / 2

                # Only keep if confidence is above threshold
                if confidence >= self.min_confidence_threshold:
                    pref_key = f"{business_function}:{event_type}"
                    pref_type = self._infer_preference_type(event_type)

                    inferred[event_type] = Preference(
                        preference_key=pref_key,
                        preference_type=pref_type,
                        business_function=business_function,
                        value=most_common,
                        confidence=confidence,
                        usage_count=total_uses,
                        success_count=successes
                    )

            logger.info(
                "preferences_inferred",
                function=business_function,
                count=len(inferred)
            )

            return inferred

        except Exception as e:
            logger.error("infer_preferences_failed", error=str(e))
            return {}

    async def _apply_confidence_decay(self) -> Any:
        """Apply time-based confidence decay to old preferences."""
        try:
            now = datetime.utcnow()
            decay_threshold = now - timedelta(days=self.confidence_decay_days)

            for pref in self.preferences.values():
                if pref.last_used and pref.last_used < decay_threshold:
                    # Calculate decay based on age
                    days_old = (now - pref.last_used).days
                    decay_factor = max(0.5, 1.0 - (days_old / 365))

                    # Apply decay
                    pref.confidence *= decay_factor

                    # Remove if too low
                    if pref.confidence < self.min_confidence_threshold:
                        logger.info(
                            "preference_decayed_removed",
                            key=pref.preference_key,
                            confidence=pref.confidence
                        )

        except Exception as e:
            logger.error("confidence_decay_failed", error=str(e))

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about learned preferences.

        Returns:
            Statistics dictionary
        """
        try:
            total_prefs = len(self.preferences)
            high_confidence = sum(1 for p in self.preferences.values() if p.confidence >= 0.7)

            # Group by function
            by_function = defaultdict(int)
            for pref in self.preferences.values():
                by_function[pref.business_function] += 1

            return {
                'total_preferences': total_prefs,
                'high_confidence_preferences': high_confidence,
                'total_learning_events': len(self.learning_events),
                'preferences_by_function': dict(by_function),
                'client_id': self.client_id
            }

        except Exception as e:
            logger.error("get_statistics_failed", error=str(e))
            return {}


def test_preference_manager() -> Any:
    """Test preference manager."""
    import asyncio
    import tempfile
    import shutil

    async def run_tests() -> Any:
        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp())

        try:
            print("Test 1: Initialize manager...")
            manager = PreferenceManager(
                client_id="test_client",
                storage_path=temp_dir
            )
            print("✓ Manager initialized")

            print("\nTest 2: Record learning event...")
            success = await manager.record_learning_event(
                event_type='data_source_selection',
                business_function='lead_enrichment',
                context={'available_sources': ['apollo', 'zoominfo']},
                user_choice='apollo',
                alternatives=['apollo', 'zoominfo'],
                outcome='success'
            )
            assert success
            print("✓ Event recorded")

            print("\nTest 3: Record more events...")
            for i in range(5):
                await manager.record_learning_event(
                    event_type='data_source_selection',
                    business_function='lead_enrichment',
                    context={},
                    user_choice='apollo',
                    outcome='success' if i < 4 else 'failure'
                )
            print("✓ Multiple events recorded")

            print("\nTest 4: Get preferences...")
            prefs = await manager.get_preferences('lead_enrichment')
            assert 'data_source_selection' in prefs
            assert prefs['data_source_selection']['value'] == 'apollo'
            print(f"✓ Preferences retrieved: {prefs}")

            print("\nTest 5: Infer preferences...")
            inferred = await manager.infer_preferences('lead_enrichment', min_event_count=3)
            assert 'data_source_selection' in inferred
            print(f"✓ Preferences inferred: {len(inferred)} preferences")

            print("\nTest 6: Get statistics...")
            stats = manager.get_statistics()
            assert stats['total_learning_events'] == 6
            print(f"✓ Statistics: {stats}")

            print("\nTest 7: Save and reload...")
            # Create new manager instance
            manager2 = PreferenceManager(
                client_id="test_client",
                storage_path=temp_dir
            )
            prefs2 = await manager2.get_preferences('lead_enrichment')
            assert 'data_source_selection' in prefs2
            print("✓ Preferences persisted and reloaded")

            print("\n✅ All tests passed!")

        finally:
            # Cleanup
            shutil.rmtree(temp_dir)

    asyncio.run(run_tests())


if __name__ == '__main__':
    test_preference_manager()
