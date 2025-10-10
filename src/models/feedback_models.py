"""
Feedback Models
Pydantic models for customer feedback, surveys, and sentiment analysis
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from enum import Enum


class FeedbackType(str, Enum):
    """Types of customer feedback"""
    NPS = "nps"                      # Net Promoter Score
    CSAT = "csat"                    # Customer Satisfaction
    CES = "ces"                      # Customer Effort Score
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    PRODUCT_FEEDBACK = "product_feedback"
    SERVICE_FEEDBACK = "service_feedback"
    GENERAL = "general"


class SentimentType(str, Enum):
    """Sentiment classification"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class FeedbackPriority(str, Enum):
    """Feedback priority levels"""
    CRITICAL = "critical"      # Urgent issue requiring immediate attention
    HIGH = "high"              # Important feedback to address soon
    MEDIUM = "medium"          # Normal priority
    LOW = "low"                # Nice to have, low urgency


class FeedbackStatus(str, Enum):
    """Feedback processing status"""
    NEW = "new"
    REVIEWED = "reviewed"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    WONT_FIX = "wont_fix"


class CustomerFeedback(BaseModel):
    """
    Customer feedback record from any source.

    Comprehensive feedback model with sentiment analysis,
    categorization, and action tracking.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "feedback_id": "FB-12345",
            "client_id": "cs_1696800000_acme",
            "feedback_type": "product_feedback",
            "source": "in-app_survey",
            "submitter_email": "john.smith@acme.com",
            "submitter_name": "John Smith",
            "title": "Export feature enhancement request",
            "content": "It would be great if we could export reports in multiple formats (CSV, Excel, PDF). Currently only CSV is supported.",
            "category": "feature_request",
            "subcategory": "reporting",
            "tags": ["export", "reporting", "enhancement"],
            "sentiment": "positive",
            "sentiment_score": 0.72,
            "priority": "medium",
            "status": "reviewed",
            "impact_assessment": "Requested by 5+ customers, moderate development effort",
            "assigned_to": "product-team@company.com",
            "follow_up_required": True,
            "follow_up_by": "2025-10-17",
            "customer_responded": False,
            "resolution_notes": None,
            "created_at": "2025-10-10T09:00:00Z",
            "updated_at": "2025-10-10T09:00:00Z",
            "reviewed_at": "2025-10-10T10:30:00Z",
            "resolved_at": None
        }
    })

    # Identification
    feedback_id: str = Field(
        ...,
        description="Unique feedback identifier",
        pattern=r"^FB-[0-9]+$"
    )
    client_id: str = Field(
        ...,
        description="Customer identifier"
    )
    feedback_type: FeedbackType = Field(
        ...,
        description="Type of feedback"
    )
    source: str = Field(
        ...,
        description="Feedback source (survey, in-app, email, call, etc.)"
    )

    # Submitter information
    submitter_email: str = Field(
        ...,
        description="Submitter email address",
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    submitter_name: str = Field(
        ...,
        description="Submitter full name"
    )

    # Content
    title: str = Field(
        ...,
        description="Feedback title/summary",
        min_length=1,
        max_length=200
    )
    content: str = Field(
        ...,
        description="Detailed feedback content",
        min_length=1
    )
    category: str = Field(
        ...,
        description="Primary feedback category"
    )
    subcategory: Optional[str] = Field(
        None,
        description="Feedback subcategory for finer classification"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and search"
    )

    # Sentiment analysis
    sentiment: SentimentType = Field(
        ...,
        description="Overall sentiment classification"
    )
    sentiment_score: float = Field(
        ...,
        description="Sentiment score (-1 to 1, negative to positive)",
        ge=-1,
        le=1
    )

    # Prioritization
    priority: FeedbackPriority = Field(
        default=FeedbackPriority.MEDIUM,
        description="Feedback priority level"
    )
    status: FeedbackStatus = Field(
        default=FeedbackStatus.NEW,
        description="Processing status"
    )
    impact_assessment: Optional[str] = Field(
        None,
        description="Impact assessment notes"
    )

    # Assignment and tracking
    assigned_to: Optional[str] = Field(
        None,
        description="Team or person assigned to handle feedback"
    )
    follow_up_required: bool = Field(
        default=False,
        description="Whether customer follow-up is required"
    )
    follow_up_by: Optional[date] = Field(
        None,
        description="Target date for customer follow-up"
    )
    customer_responded: bool = Field(
        default=False,
        description="Whether customer has been contacted about this feedback"
    )
    resolution_notes: Optional[str] = Field(
        None,
        description="Resolution or action taken"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Feedback submission timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )
    reviewed_at: Optional[datetime] = Field(
        None,
        description="When feedback was reviewed"
    )
    resolved_at: Optional[datetime] = Field(
        None,
        description="When feedback was resolved"
    )


class NPSResponse(BaseModel):
    """
    Net Promoter Score survey response.

    Tracks NPS scores with follow-up questions and
    categorization (Promoter, Passive, Detractor).
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "response_id": "NPS-67890",
            "client_id": "cs_1696800000_acme",
            "survey_id": "SURVEY-Q3-2025",
            "respondent_email": "john.smith@acme.com",
            "respondent_name": "John Smith",
            "score": 9,
            "category": "promoter",
            "reason": "Great product with excellent support. The recent features have been very helpful.",
            "follow_up_question_1": "What do you value most?",
            "follow_up_answer_1": "Ease of use and responsive customer support",
            "follow_up_question_2": "What could we improve?",
            "follow_up_answer_2": "More integrations with other tools",
            "sentiment": "very_positive",
            "sentiment_score": 0.88,
            "follow_up_required": False,
            "contacted": False,
            "survey_sent_at": "2025-10-01T10:00:00Z",
            "responded_at": "2025-10-02T14:30:00Z",
            "response_time_hours": 28.5
        }
    })

    # Identification
    response_id: str = Field(
        ...,
        description="Unique response identifier",
        pattern=r"^NPS-[0-9]+$"
    )
    client_id: str = Field(
        ...,
        description="Customer identifier"
    )
    survey_id: str = Field(
        ...,
        description="Survey campaign identifier"
    )

    # Respondent
    respondent_email: str = Field(
        ...,
        description="Respondent email address",
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    respondent_name: str = Field(
        ...,
        description="Respondent full name"
    )

    # NPS score
    score: int = Field(
        ...,
        description="NPS score (0-10)",
        ge=0,
        le=10
    )
    category: str = Field(
        ...,
        description="NPS category (detractor: 0-6, passive: 7-8, promoter: 9-10)",
        pattern=r"^(detractor|passive|promoter)$"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for score (open-ended response)"
    )

    # Follow-up questions (customizable)
    follow_up_question_1: Optional[str] = Field(
        None,
        description="First follow-up question"
    )
    follow_up_answer_1: Optional[str] = Field(
        None,
        description="Answer to first follow-up question"
    )
    follow_up_question_2: Optional[str] = Field(
        None,
        description="Second follow-up question"
    )
    follow_up_answer_2: Optional[str] = Field(
        None,
        description="Answer to second follow-up question"
    )

    # Sentiment analysis
    sentiment: SentimentType = Field(
        ...,
        description="Analyzed sentiment from open-ended responses"
    )
    sentiment_score: float = Field(
        ...,
        description="Sentiment score (-1 to 1)",
        ge=-1,
        le=1
    )

    # Follow-up tracking
    follow_up_required: bool = Field(
        default=False,
        description="Whether personal follow-up is required"
    )
    contacted: bool = Field(
        default=False,
        description="Whether respondent has been contacted"
    )

    # Timestamps
    survey_sent_at: datetime = Field(
        ...,
        description="When survey was sent"
    )
    responded_at: datetime = Field(
        default_factory=datetime.now,
        description="When response was submitted"
    )
    response_time_hours: float = Field(
        ...,
        description="Time to respond in hours",
        ge=0
    )

    @field_validator('category')
    @classmethod
    def validate_category_matches_score(cls, v: str, info) -> str:
        """Validate NPS category matches score"""
        if 'score' not in info.data:
            return v

        score = info.data['score']
        expected_category = (
            'detractor' if score <= 6
            else 'passive' if score <= 8
            else 'promoter'
        )

        if v != expected_category:
            raise ValueError(
                f'Category "{v}" does not match score {score}. '
                f'Expected "{expected_category}"'
            )
        return v


class SentimentAnalysis(BaseModel):
    """
    Aggregated sentiment analysis for a customer or time period.

    Provides sentiment trends, topics, and insights from
    all feedback sources.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "analysis_id": "SA-2025Q3",
            "client_id": "cs_1696800000_acme",
            "period_start": "2025-07-01T00:00:00Z",
            "period_end": "2025-09-30T23:59:59Z",
            "total_feedback_items": 47,
            "feedback_by_type": {
                "nps": 12,
                "csat": 8,
                "product_feedback": 15,
                "feature_request": 9,
                "bug_report": 3
            },
            "overall_sentiment": "positive",
            "overall_sentiment_score": 0.68,
            "sentiment_distribution": {
                "very_positive": 0.23,
                "positive": 0.47,
                "neutral": 0.21,
                "negative": 0.07,
                "very_negative": 0.02
            },
            "sentiment_trend": "improving",
            "top_positive_themes": [
                {"theme": "customer_support", "mentions": 18, "avg_sentiment": 0.87},
                {"theme": "ease_of_use", "mentions": 15, "avg_sentiment": 0.82},
                {"theme": "feature_quality", "mentions": 12, "avg_sentiment": 0.78}
            ],
            "top_negative_themes": [
                {"theme": "missing_features", "mentions": 8, "avg_sentiment": -0.45},
                {"theme": "performance", "mentions": 3, "avg_sentiment": -0.62}
            ],
            "action_items": [
                "Prioritize top 3 requested features",
                "Investigate performance issues",
                "Share positive support feedback with team"
            ],
            "nps_score": 52,
            "csat_score": 4.3,
            "analyzed_at": "2025-10-10T09:00:00Z"
        }
    })

    # Identification
    analysis_id: str = Field(
        ...,
        description="Unique analysis identifier"
    )
    client_id: Optional[str] = Field(
        None,
        description="Customer identifier (None for company-wide analysis)"
    )

    # Time period
    period_start: datetime = Field(
        ...,
        description="Analysis period start"
    )
    period_end: datetime = Field(
        ...,
        description="Analysis period end"
    )

    # Volume metrics
    total_feedback_items: int = Field(
        ...,
        description="Total feedback items analyzed",
        ge=0
    )
    feedback_by_type: Dict[str, int] = Field(
        ...,
        description="Feedback count by type"
    )

    # Sentiment metrics
    overall_sentiment: SentimentType = Field(
        ...,
        description="Overall sentiment classification"
    )
    overall_sentiment_score: float = Field(
        ...,
        description="Overall sentiment score (-1 to 1)",
        ge=-1,
        le=1
    )
    sentiment_distribution: Dict[str, float] = Field(
        ...,
        description="Distribution of sentiment types (percentages)"
    )
    sentiment_trend: str = Field(
        ...,
        description="Sentiment trend vs. previous period (improving, stable, declining)",
        pattern=r"^(improving|stable|declining|unknown)$"
    )

    # Theme analysis
    top_positive_themes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most mentioned positive themes with sentiment scores"
    )
    top_negative_themes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most mentioned negative themes with sentiment scores"
    )

    # Actionable insights
    action_items: List[str] = Field(
        default_factory=list,
        description="Recommended actions based on analysis"
    )

    # Survey scores
    nps_score: Optional[int] = Field(
        None,
        description="Net Promoter Score (-100 to 100)",
        ge=-100,
        le=100
    )
    csat_score: Optional[float] = Field(
        None,
        description="Customer Satisfaction Score (1-5)",
        ge=1,
        le=5
    )

    # Metadata
    analyzed_at: datetime = Field(
        default_factory=datetime.now,
        description="Analysis timestamp"
    )


class SurveyTemplate(BaseModel):
    """
    Survey template for customer feedback collection.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "template_id": "TMPL-NPS-QUARTERLY",
            "template_name": "Quarterly NPS Survey",
            "template_type": "nps",
            "description": "Standard quarterly Net Promoter Score survey",
            "questions": [
                {
                    "question_id": "Q1",
                    "question_text": "How likely are you to recommend our product to a colleague?",
                    "question_type": "scale_0_10",
                    "required": True
                },
                {
                    "question_id": "Q2",
                    "question_text": "What is the primary reason for your score?",
                    "question_type": "open_text",
                    "required": True
                },
                {
                    "question_id": "Q3",
                    "question_text": "What do you value most about our product?",
                    "question_type": "open_text",
                    "required": False
                }
            ],
            "targeting": {
                "customer_tiers": ["professional", "enterprise"],
                "lifecycle_stages": ["active"],
                "min_tenure_days": 30
            },
            "frequency": "quarterly",
            "active": True,
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-10-01T14:30:00Z"
        }
    })

    template_id: str = Field(..., description="Unique template identifier")
    template_name: str = Field(..., description="Template name")
    template_type: FeedbackType = Field(..., description="Survey type")
    description: str = Field(..., description="Template description")

    questions: List[Dict[str, Any]] = Field(
        ...,
        description="Survey questions configuration",
        min_length=1
    )
    targeting: Dict[str, Any] = Field(
        default_factory=dict,
        description="Target audience criteria"
    )
    frequency: str = Field(
        default="one_time",
        description="Survey frequency (one_time, monthly, quarterly, annual)"
    )
    active: bool = Field(
        default=True,
        description="Whether template is active"
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Template creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )


__all__ = [
    'FeedbackType',
    'SentimentType',
    'FeedbackPriority',
    'FeedbackStatus',
    'CustomerFeedback',
    'NPSResponse',
    'SentimentAnalysis',
    'SurveyTemplate'
]
