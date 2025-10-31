"""
Learning Question Generator
Generates contextual questions to learn user preferences and improve accuracy
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import random
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class QuestionType(str, Enum):
    """Types of learning questions."""
    CLARIFICATION = "clarification"  # Clarify ambiguous input
    PREFERENCE = "preference"  # Learn user preferences
    VALIDATION = "validation"  # Validate assumptions
    CHOICE = "choice"  # Choose between options
    FEEDBACK = "feedback"  # Get feedback on results


class ConfidenceLevel(str, Enum):
    """Confidence levels for decisions."""
    VERY_LOW = "very_low"  # 0-30%
    LOW = "low"  # 30-50%
    MEDIUM = "medium"  # 50-70%
    HIGH = "high"  # 70-90%
    VERY_HIGH = "very_high"  # 90-100%


class LearningQuestion(BaseModel):
    """
    A learning question to ask the user.

    Attributes:
        question_type: Type of question
        question_text: The actual question to ask
        context: Context about why we're asking
        options: Possible answer options (if applicable)
        default_answer: Suggested default answer
        business_function: What business function this relates to
        confidence_level: Current confidence level
        metadata: Additional metadata
    """
    question_type: QuestionType
    question_text: str
    context: str
    options: Optional[List[str]] = None
    default_answer: Optional[Any] = None
    business_function: Optional[str] = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LearningQuestionGenerator:
    """
    Generates contextual learning questions based on confidence and context.

    Features:
    - Determines when to ask questions based on confidence thresholds
    - Generates appropriate questions for different scenarios
    - Provides question templates by business function
    - Context-aware question selection
    - Learning frequency management

    Usage:
        >>> generator = LearningQuestionGenerator(
        ...     completion_threshold=0.70,
        ...     learning_frequency='often'
        ... )
        >>> if generator.should_ask_question(confidence=0.55, context={'function': 'lead_enrichment'}):
        ...     question = generator.generate_question(
        ...         business_function='lead_enrichment',
        ...         context={'data_source': 'apollo'},
        ...         confidence=0.55
        ...     )
        ...     print(question.question_text)
    """

    def __init__(
        self,
        completion_threshold: float = 0.70,
        learning_frequency: str = 'often',
        question_probability: Optional[Dict[str, float]] = None
    ) -> Any:
        """
        Initialize question generator.

        Args:
            completion_threshold: Confidence threshold below which to ask questions
            learning_frequency: How often to ask ('always', 'often', 'occasionally', 'rarely')
            question_probability: Custom probabilities for asking questions by frequency
        """
        self.completion_threshold = completion_threshold
        self.learning_frequency = learning_frequency

        # Default probabilities for asking questions
        self.question_probability = question_probability or {
            'always': 1.0,
            'often': 0.75,
            'occasionally': 0.40,
            'rarely': 0.15
        }

        # Question templates by business function
        self._init_question_templates()

        logger.info(
            "question_generator_initialized",
            threshold=completion_threshold,
            frequency=learning_frequency
        )

    def _init_question_templates(self) -> Any:
        """Initialize question templates for different business functions."""
        self.question_templates = {
            'lead_enrichment': {
                QuestionType.PREFERENCE: [
                    {
                        'text': "Which data source should I prioritize for enriching lead data: {options}?",
                        'context': "I found contact information from multiple sources.",
                        'options_key': 'data_sources'
                    },
                    {
                        'text': "Should I auto-enrich leads with missing {field} data?",
                        'context': "I can automatically fill in missing information.",
                        'options': ['Yes, always', 'Ask me first', 'No, manual only']
                    }
                ],
                QuestionType.VALIDATION: [
                    {
                        'text': "I found {count} potential matches for this lead. Should I use the one from {source}?",
                        'context': "Multiple data sources returned different results.",
                        'options': ['Yes', 'Show me all options', 'Skip this lead']
                    }
                ],
                QuestionType.CHOICE: [
                    {
                        'text': "Which email address should I use: {options}?",
                        'context': "Found multiple email addresses for this contact.",
                        'options_key': 'email_options'
                    }
                ]
            },
            'email_sequencing': {
                QuestionType.PREFERENCE: [
                    {
                        'text': "What tone should I use for follow-up emails: {options}?",
                        'context': "Customizing email communication style.",
                        'options': ['Professional', 'Friendly', 'Direct', 'Consultative']
                    },
                    {
                        'text': "How many days should I wait between follow-ups?",
                        'context': "Setting up email sequence timing.",
                        'options': ['2 days', '3 days', '5 days', '7 days']
                    }
                ],
                QuestionType.FEEDBACK: [
                    {
                        'text': "Did this email template work well for you?",
                        'context': "Learning from email performance.",
                        'options': ['Yes, keep using it', 'Needs improvement', 'Don\'t use again']
                    }
                ]
            },
            'data_source_selection': {
                QuestionType.PREFERENCE: [
                    {
                        'text': "When multiple sources have data, should I prefer: {options}?",
                        'context': "Learning your data source preferences.",
                        'options': ['Fastest', 'Most accurate', 'Most recent', 'Most complete']
                    }
                ],
                QuestionType.CLARIFICATION: [
                    {
                        'text': "You have both {source1} and {source2} configured. Which should I use for {function}?",
                        'context': "Multiple data sources available for this operation."
                    }
                ]
            },
            'crm_management': {
                QuestionType.PREFERENCE: [
                    {
                        'text': "Should I automatically create {object_type} records in your CRM?",
                        'context': "Managing CRM automation preferences.",
                        'options': ['Yes, always', 'Ask me first', 'No, manual only']
                    },
                    {
                        'text': "Which CRM field should I update when the lead stage changes: {options}?",
                        'context': "Configuring CRM field mappings.",
                        'options_key': 'field_options'
                    }
                ],
                QuestionType.VALIDATION: [
                    {
                        'text': "I\'m about to update {count} CRM records. Should I proceed?",
                        'context': "Confirming bulk CRM operations.",
                        'options': ['Yes, proceed', 'Show me details first', 'Cancel']
                    }
                ]
            },
            'prospect_research': {
                QuestionType.PREFERENCE: [
                    {
                        'text': "What information is most valuable when researching prospects: {options}?",
                        'context': "Prioritizing research data points.",
                        'options': ['Company size', 'Funding', 'Technologies used', 'Recent news', 'All of the above']
                    }
                ],
                QuestionType.CHOICE: [
                    {
                        'text': "Found {count} contacts at {company}. Should I focus on {role1} or {role2}?",
                        'context': "Multiple decision makers identified."
                    }
                ]
            },
            'sales_forecasting': {
                QuestionType.PREFERENCE: [
                    {
                        'text': "Should I be conservative or optimistic when forecasting: {options}?",
                        'context': "Setting forecast methodology.",
                        'options': ['Very conservative', 'Conservative', 'Balanced', 'Optimistic']
                    }
                ],
                QuestionType.VALIDATION: [
                    {
                        'text': "My forecast shows {amount} for {period}. Does this align with your expectations?",
                        'context': "Validating forecast accuracy.",
                        'options': ['Yes', 'Too high', 'Too low']
                    }
                ]
            },
            'task_automation': {
                QuestionType.PREFERENCE: [
                    {
                        'text': "Should I automatically create follow-up tasks after {event}?",
                        'context': "Configuring task automation.",
                        'options': ['Yes, always', 'Only for high-value leads', 'No, I\'ll create manually']
                    }
                ],
                QuestionType.CLARIFICATION: [
                    {
                        'text': "What priority should I assign to {task_type} tasks?",
                        'context': "Learning task prioritization preferences.",
                        'options': ['High', 'Medium', 'Low']
                    }
                ]
            }
        }

    def should_ask_question(
        self,
        confidence: float,
        context: Optional[Dict[str, Any]] = None,
        force: bool = False
    ) -> bool:
        """
        Determine if we should ask a learning question.

        Args:
            confidence: Current confidence level (0.0-1.0)
            context: Additional context for decision
            force: Force asking a question regardless of other factors

        Returns:
            True if should ask a question

        Example:
            >>> should_ask = generator.should_ask_question(
            ...     confidence=0.55,
            ...     context={'function': 'lead_enrichment', 'attempt': 1}
            ... )
            >>> if should_ask:
            ...     # Generate and ask question
        """
        try:
            # Always ask if forced
            if force:
                return True

            # Don't ask if confidence is above threshold
            if confidence >= self.completion_threshold:
                return False

            # Get probability based on learning frequency
            base_probability = self.question_probability.get(
                self.learning_frequency,
                0.5
            )

            # Adjust probability based on how far below threshold we are
            confidence_gap = self.completion_threshold - confidence
            adjusted_probability = min(base_probability + (confidence_gap * 0.5), 1.0)

            # Randomly decide based on adjusted probability
            should_ask = random.random() < adjusted_probability

            logger.info(
                "question_decision",
                confidence=confidence,
                threshold=self.completion_threshold,
                probability=adjusted_probability,
                should_ask=should_ask
            )

            return should_ask

        except Exception as e:
            logger.error("should_ask_question_failed", error=str(e))
            return False

    def generate_question(
        self,
        business_function: str,
        context: Dict[str, Any],
        confidence: float,
        question_type: Optional[QuestionType] = None
    ) -> Optional[LearningQuestion]:
        """
        Generate a contextual learning question.

        Args:
            business_function: The business function context
            context: Additional context for the question
            confidence: Current confidence level
            question_type: Specific question type to generate (optional)

        Returns:
            LearningQuestion or None if no appropriate question

        Example:
            >>> question = generator.generate_question(
            ...     business_function='lead_enrichment',
            ...     context={
            ...         'data_sources': ['apollo', 'zoominfo'],
            ...         'field': 'phone_number'
            ...     },
            ...     confidence=0.60
            ... )
            >>> print(question.question_text)
        """
        try:
            # Get templates for this business function
            templates = self.question_templates.get(business_function, {})

            if not templates:
                logger.warning(
                    "no_templates_for_function",
                    function=business_function
                )
                return None

            # Select question type
            if question_type:
                type_templates = templates.get(question_type, [])
            else:
                # Choose based on confidence level
                if confidence < 0.30:
                    # Very low confidence - ask for clarification or validation
                    type_templates = templates.get(QuestionType.CLARIFICATION, []) or \
                                   templates.get(QuestionType.VALIDATION, [])
                elif confidence < 0.50:
                    # Low confidence - ask for choices or preferences
                    type_templates = templates.get(QuestionType.CHOICE, []) or \
                                   templates.get(QuestionType.PREFERENCE, [])
                else:
                    # Medium confidence - ask for preferences or feedback
                    type_templates = templates.get(QuestionType.PREFERENCE, []) or \
                                   templates.get(QuestionType.FEEDBACK, [])

            if not type_templates:
                return None

            # Select a random template
            template = random.choice(type_templates)

            # Build question from template
            question_text = template['text']
            question_context = template['context']
            options = template.get('options')

            # Fill in template variables from context
            if '{options}' in question_text:
                if template.get('options_key') and template['options_key'] in context:
                    options_list = context[template['options_key']]
                    options = options_list
                    question_text = question_text.format(
                        options=', '.join(options_list)
                    )
                elif options:
                    question_text = question_text.format(
                        options=', '.join(options)
                    )

            # Replace other context variables
            for key, value in context.items():
                placeholder = f"{{{key}}}"
                if placeholder in question_text:
                    question_text = question_text.replace(placeholder, str(value))
                if placeholder in question_context:
                    question_context = question_context.replace(placeholder, str(value))

            # Determine confidence level enum
            if confidence < 0.30:
                confidence_level = ConfidenceLevel.VERY_LOW
            elif confidence < 0.50:
                confidence_level = ConfidenceLevel.LOW
            elif confidence < 0.70:
                confidence_level = ConfidenceLevel.MEDIUM
            elif confidence < 0.90:
                confidence_level = ConfidenceLevel.HIGH
            else:
                confidence_level = ConfidenceLevel.VERY_HIGH

            # Create learning question
            question = LearningQuestion(
                question_type=question_type or QuestionType.PREFERENCE,
                question_text=question_text,
                context=question_context,
                options=options,
                business_function=business_function,
                confidence_level=confidence_level,
                metadata={
                    'confidence_score': confidence,
                    'generated_at': datetime.utcnow().isoformat(),
                    **context
                }
            )

            logger.info(
                "question_generated",
                function=business_function,
                type=question.question_type,
                confidence=confidence
            )

            return question

        except Exception as e:
            logger.error(
                "generate_question_failed",
                function=business_function,
                error=str(e)
            )
            return None

    def get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """
        Convert numeric confidence to confidence level enum.

        Args:
            confidence: Confidence score (0.0-1.0)

        Returns:
            ConfidenceLevel enum
        """
        if confidence < 0.30:
            return ConfidenceLevel.VERY_LOW
        elif confidence < 0.50:
            return ConfidenceLevel.LOW
        elif confidence < 0.70:
            return ConfidenceLevel.MEDIUM
        elif confidence < 0.90:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH


def test_question_generator() -> Any:
    """Test the question generator."""
    print("Test 1: Initialize generator...")
    generator = LearningQuestionGenerator(
        completion_threshold=0.70,
        learning_frequency='often'
    )
    print("✓ Generator initialized")

    print("\nTest 2: Should ask question (low confidence)...")
    should_ask = generator.should_ask_question(confidence=0.45)
    print(f"✓ Decision: {should_ask} (confidence=0.45, threshold=0.70)")

    print("\nTest 3: Should ask question (high confidence)...")
    should_ask = generator.should_ask_question(confidence=0.85)
    assert not should_ask  # Should not ask when above threshold
    print(f"✓ Decision: {should_ask} (confidence=0.85, above threshold)")

    print("\nTest 4: Generate lead enrichment question...")
    question = generator.generate_question(
        business_function='lead_enrichment',
        context={
            'data_sources': ['apollo', 'zoominfo'],
            'field': 'email'
        },
        confidence=0.60
    )
    assert question is not None
    print(f"✓ Question generated:")
    print(f"  Type: {question.question_type}")
    print(f"  Text: {question.question_text}")
    print(f"  Context: {question.context}")
    if question.options:
        print(f"  Options: {question.options}")

    print("\nTest 5: Generate email sequencing question...")
    question = generator.generate_question(
        business_function='email_sequencing',
        context={},
        confidence=0.40
    )
    assert question is not None
    print(f"✓ Question generated:")
    print(f"  Text: {question.question_text}")

    print("\nTest 6: Generate CRM management question...")
    question = generator.generate_question(
        business_function='crm_management',
        context={
            'object_type': 'Contact',
            'count': 25
        },
        confidence=0.55
    )
    assert question is not None
    print(f"✓ Question generated:")
    print(f"  Text: {question.question_text}")

    print("\nTest 7: Get confidence level...")
    level = generator.get_confidence_level(0.35)
    assert level == ConfidenceLevel.LOW
    print(f"✓ Confidence 0.35 → {level}")

    print("\nTest 8: Force question...")
    should_ask = generator.should_ask_question(confidence=0.95, force=True)
    assert should_ask
    print("✓ Forced question even with high confidence")

    print("\n✅ All tests passed!")


if __name__ == '__main__':
    test_question_generator()
