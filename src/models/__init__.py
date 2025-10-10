"""
Customer Success MCP Models Package

Comprehensive Pydantic models for customer success operations.

Model Categories:
- customer_models: Core customer entities and health scoring
- onboarding_models: Onboarding plans, milestones, and training
- support_models: Support tickets and knowledge base
- renewal_models: Contract renewal and expansion opportunities
- feedback_models: Customer feedback, NPS, and sentiment analysis
- analytics_models: Metrics, analytics, and reporting
"""

# Customer models
from src.models.customer_models import (
    CustomerTier,
    LifecycleStage,
    HealthTrend,
    AccountStatus,
    CustomerAccount,
    HealthScoreComponents,
    CustomerSegment,
    RiskIndicator,
    ChurnPrediction
)

# Onboarding models
from src.models.onboarding_models import (
    OnboardingStatus,
    MilestoneStatus,
    TrainingFormat,
    CertificationLevel,
    OnboardingPlan,
    OnboardingMilestone,
    TrainingModule,
    TrainingCompletion,
    OnboardingProgress
)

# Support models
from src.models.support_models import (
    TicketPriority,
    TicketStatus,
    TicketCategory,
    SLAStatus,
    ArticleStatus,
    SupportTicket,
    TicketComment,
    KnowledgeBaseArticle,
    SupportMetrics
)

# Renewal models
from src.models.renewal_models import (
    RenewalStatus,
    ExpansionType,
    ContractType,
    PaymentStatus,
    RenewalForecast,
    ContractDetails,
    ExpansionOpportunity,
    RenewalCampaign
)

# Feedback models
from src.models.feedback_models import (
    FeedbackType,
    SentimentType,
    FeedbackPriority,
    FeedbackStatus,
    CustomerFeedback,
    NPSResponse,
    SentimentAnalysis,
    SurveyTemplate
)

# Analytics models
from src.models.analytics_models import (
    TimeGranularity,
    TrendDirection,
    BenchmarkComparison,
    HealthMetrics,
    EngagementMetrics,
    UsageAnalytics,
    AccountMetrics,
    CohortAnalysis
)

__all__ = [
    # Customer models
    'CustomerTier',
    'LifecycleStage',
    'HealthTrend',
    'AccountStatus',
    'CustomerAccount',
    'HealthScoreComponents',
    'CustomerSegment',
    'RiskIndicator',
    'ChurnPrediction',

    # Onboarding models
    'OnboardingStatus',
    'MilestoneStatus',
    'TrainingFormat',
    'CertificationLevel',
    'OnboardingPlan',
    'OnboardingMilestone',
    'TrainingModule',
    'TrainingCompletion',
    'OnboardingProgress',

    # Support models
    'TicketPriority',
    'TicketStatus',
    'TicketCategory',
    'SLAStatus',
    'ArticleStatus',
    'SupportTicket',
    'TicketComment',
    'KnowledgeBaseArticle',
    'SupportMetrics',

    # Renewal models
    'RenewalStatus',
    'ExpansionType',
    'ContractType',
    'PaymentStatus',
    'RenewalForecast',
    'ContractDetails',
    'ExpansionOpportunity',
    'RenewalCampaign',

    # Feedback models
    'FeedbackType',
    'SentimentType',
    'FeedbackPriority',
    'FeedbackStatus',
    'CustomerFeedback',
    'NPSResponse',
    'SentimentAnalysis',
    'SurveyTemplate',

    # Analytics models
    'TimeGranularity',
    'TrendDirection',
    'BenchmarkComparison',
    'HealthMetrics',
    'EngagementMetrics',
    'UsageAnalytics',
    'AccountMetrics',
    'CohortAnalysis',
]
