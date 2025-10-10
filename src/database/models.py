"""
SQLAlchemy ORM models for Customer Success MCP.

These models define the database schema with proper relationships,
indexes, and constraints for optimal query performance.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Date, DateTime, Text,
    ForeignKey, JSON, Index, CheckConstraint, UniqueConstraint, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from src.database import Base


# ============================================================================
# CUSTOMER MODELS
# ============================================================================

class CustomerAccount(Base):
    """Customer account table with core customer information."""
    __tablename__ = 'customers'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), unique=True, nullable=False, index=True)

    # Basic information
    client_name = Column(String(200), nullable=False)
    company_name = Column(String(200), nullable=False)
    industry = Column(String(100), default='Technology')

    # Classification
    tier = Column(String(50), nullable=False, default='standard', index=True)
    lifecycle_stage = Column(String(50), nullable=False, default='onboarding', index=True)

    # Contract details
    contract_value = Column(Float, default=0.0)
    contract_start_date = Column(Date, nullable=False, index=True)
    contract_end_date = Column(Date, nullable=True)
    renewal_date = Column(Date, nullable=True, index=True)

    # Contact information
    primary_contact_email = Column(String(255), nullable=True)
    primary_contact_name = Column(String(200), nullable=True)
    csm_assigned = Column(String(200), nullable=True, index=True)

    # Health and engagement
    health_score = Column(Integer, default=50, index=True)
    health_trend = Column(String(20), default='stable')
    last_engagement_date = Column(DateTime, nullable=True, index=True)

    # Metadata
    status = Column(String(20), nullable=False, default='active', index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    health_scores = relationship("HealthScoreComponents", back_populates="customer", cascade="all, delete-orphan")
    risk_indicators = relationship("RiskIndicator", back_populates="customer", cascade="all, delete-orphan")
    churn_predictions = relationship("ChurnPrediction", back_populates="customer", cascade="all, delete-orphan")
    onboarding_plans = relationship("OnboardingPlan", back_populates="customer", cascade="all, delete-orphan")
    support_tickets = relationship("SupportTicket", back_populates="customer", cascade="all, delete-orphan")
    contracts = relationship("ContractDetails", back_populates="customer", cascade="all, delete-orphan")
    renewal_forecasts = relationship("RenewalForecast", back_populates="customer", cascade="all, delete-orphan")
    feedback = relationship("CustomerFeedback", back_populates="customer", cascade="all, delete-orphan")
    nps_responses = relationship("NPSResponse", back_populates="customer", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_customers_client_id_created_at', 'client_id', 'created_at'),
        Index('ix_customers_health_score_status', 'health_score', 'status'),
        Index('ix_customers_csm_lifecycle', 'csm_assigned', 'lifecycle_stage'),
        CheckConstraint('health_score >= 0 AND health_score <= 100', name='check_health_score_range'),
        CheckConstraint('contract_value >= 0', name='check_contract_value_positive'),
    )


class HealthScoreComponents(Base):
    """Health score component breakdowns."""
    __tablename__ = 'health_scores'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), ForeignKey('customers.client_id', ondelete='CASCADE'), nullable=False, index=True)

    # Component scores
    usage_score = Column(Float, nullable=False)
    engagement_score = Column(Float, nullable=False)
    support_score = Column(Float, nullable=False)
    satisfaction_score = Column(Float, nullable=False)
    payment_score = Column(Float, nullable=False)

    # Weights
    usage_weight = Column(Float, default=0.35)
    engagement_weight = Column(Float, default=0.25)
    support_weight = Column(Float, default=0.15)
    satisfaction_weight = Column(Float, default=0.15)
    payment_weight = Column(Float, default=0.10)

    # Calculated overall score
    overall_score = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    customer = relationship("CustomerAccount", back_populates="health_scores")

    __table_args__ = (
        Index('ix_health_scores_client_created', 'client_id', 'created_at'),
        CheckConstraint('usage_score >= 0 AND usage_score <= 100', name='check_usage_score_range'),
        CheckConstraint('engagement_score >= 0 AND engagement_score <= 100', name='check_engagement_score_range'),
    )


class CustomerSegment(Base):
    """Customer segmentation definitions."""
    __tablename__ = 'customer_segments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    segment_id = Column(String(100), unique=True, nullable=False, index=True)
    segment_name = Column(String(200), nullable=False)
    segment_type = Column(String(50), nullable=False, index=True)

    # Segmentation criteria and characteristics (stored as JSON)
    criteria = Column(JSON, nullable=False)
    characteristics = Column(JSON, default={})
    engagement_strategy = Column(JSON, default={})
    success_metrics = Column(JSON, default={})

    # Metrics
    customer_count = Column(Integer, default=0)
    total_arr = Column(Float, default=0.0)
    avg_health_score = Column(Float, default=50.0)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class RiskIndicator(Base):
    """Individual risk indicators for churn prediction."""
    __tablename__ = 'risk_indicators'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), ForeignKey('customers.client_id', ondelete='CASCADE'), nullable=False, index=True)

    indicator_id = Column(String(100), nullable=False)
    indicator_name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)

    current_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    description = Column(Text, nullable=False)

    mitigation_actions = Column(JSON, default=[])

    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationship
    customer = relationship("CustomerAccount", back_populates="risk_indicators")

    __table_args__ = (
        Index('ix_risk_indicators_client_severity', 'client_id', 'severity'),
        Index('ix_risk_indicators_detected', 'detected_at'),
    )


class ChurnPrediction(Base):
    """Churn prediction model outputs."""
    __tablename__ = 'churn_predictions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), ForeignKey('customers.client_id', ondelete='CASCADE'), nullable=False, index=True)

    prediction_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    churn_probability = Column(Float, nullable=False)
    churn_risk_level = Column(String(20), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)

    contributing_factors = Column(JSON, default=[])
    predicted_churn_date = Column(Date, nullable=True)
    retention_recommendations = Column(JSON, default=[])

    model_version = Column(String(20), default='v1.0.0')

    # Relationship
    customer = relationship("CustomerAccount", back_populates="churn_predictions")

    __table_args__ = (
        Index('ix_churn_predictions_client_date', 'client_id', 'prediction_date'),
        Index('ix_churn_predictions_risk_level', 'churn_risk_level'),
        CheckConstraint('churn_probability >= 0 AND churn_probability <= 1', name='check_churn_probability_range'),
    )


# ============================================================================
# ONBOARDING MODELS
# ============================================================================

class OnboardingPlan(Base):
    """Onboarding plan definitions."""
    __tablename__ = 'onboarding_plans'

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(String(100), unique=True, nullable=False, index=True)
    client_id = Column(String(100), ForeignKey('customers.client_id', ondelete='CASCADE'), nullable=False, index=True)

    plan_name = Column(String(200), nullable=False)
    product_tier = Column(String(50), nullable=False)

    # Timeline
    start_date = Column(Date, nullable=False, index=True)
    target_completion_date = Column(Date, nullable=False)
    actual_completion_date = Column(Date, nullable=True)
    timeline_weeks = Column(Integer, nullable=False)

    # Goals (stored as JSON arrays)
    customer_goals = Column(JSON, nullable=False)
    success_criteria = Column(JSON, nullable=False)

    # Team
    total_estimated_hours = Column(Integer, default=0)
    assigned_csm = Column(String(200), nullable=True, index=True)
    assigned_implementation_team = Column(JSON, default=[])

    # Status
    status = Column(String(20), nullable=False, default='draft', index=True)
    completion_percentage = Column(Float, default=0.0)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("CustomerAccount", back_populates="onboarding_plans")
    milestones = relationship("OnboardingMilestone", back_populates="plan", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_onboarding_plans_client_status', 'client_id', 'status'),
        Index('ix_onboarding_plans_start_date', 'start_date'),
    )


class OnboardingMilestone(Base):
    """Individual milestones within onboarding plans."""
    __tablename__ = 'onboarding_milestones'

    id = Column(Integer, primary_key=True, autoincrement=True)
    milestone_id = Column(String(100), nullable=False)
    plan_id = Column(String(100), ForeignKey('onboarding_plans.plan_id', ondelete='CASCADE'), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    week = Column(Integer, nullable=False)
    sequence_order = Column(Integer, nullable=False)

    tasks = Column(JSON, nullable=False)
    success_criteria = Column(JSON, default=[])
    dependencies = Column(JSON, default=[])

    # Time tracking
    estimated_hours = Column(Integer, nullable=False)
    actual_hours = Column(Integer, nullable=True)
    assigned_to = Column(String(200), nullable=True, index=True)
    due_date = Column(Date, nullable=True, index=True)
    completion_date = Column(Date, nullable=True)

    # Status
    status = Column(String(20), nullable=False, default='not_started', index=True)
    completion_percentage = Column(Float, default=0.0)
    blockers = Column(JSON, default=[])

    # Relationship
    plan = relationship("OnboardingPlan", back_populates="milestones")

    __table_args__ = (
        Index('ix_onboarding_milestones_plan_status', 'plan_id', 'status'),
        Index('ix_onboarding_milestones_due_date', 'due_date'),
    )


class TrainingModule(Base):
    """Training module definitions."""
    __tablename__ = 'training_modules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(String(100), unique=True, nullable=False, index=True)

    module_name = Column(String(200), nullable=False)
    module_description = Column(Text, nullable=False)
    format = Column(String(50), nullable=False)
    certification_level = Column(String(50), default='basic')

    # Content
    duration_minutes = Column(Integer, nullable=False)
    content_url = Column(String(500), nullable=True)
    prerequisites = Column(JSON, default=[])
    learning_objectives = Column(JSON, nullable=False)
    topics_covered = Column(JSON, nullable=False)

    # Assessment
    assessment_required = Column(Boolean, default=True)
    passing_score = Column(Float, default=0.75)
    certification_awarded = Column(String(200), nullable=True)
    max_attempts = Column(Integer, default=3)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    completions = relationship("TrainingCompletion", back_populates="module", cascade="all, delete-orphan")


class TrainingCompletion(Base):
    """Training completion records."""
    __tablename__ = 'training_completions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    completion_id = Column(String(100), unique=True, nullable=False, index=True)
    client_id = Column(String(100), nullable=False, index=True)
    module_id = Column(String(100), ForeignKey('training_modules.module_id', ondelete='CASCADE'), nullable=False, index=True)

    user_email = Column(String(255), nullable=False, index=True)
    user_name = Column(String(200), nullable=False)

    # Timing
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    time_spent_minutes = Column(Integer, default=0)

    # Assessment results
    assessment_score = Column(Float, nullable=True)
    attempts_used = Column(Integer, default=0)
    passed = Column(Boolean, default=False)

    # Certification
    certification_issued = Column(Boolean, default=False)
    certification_id = Column(String(100), nullable=True)

    # Feedback
    feedback_rating = Column(Float, nullable=True)
    feedback_comments = Column(Text, nullable=True)

    # Relationship
    module = relationship("TrainingModule", back_populates="completions")

    __table_args__ = (
        Index('ix_training_completions_client_user', 'client_id', 'user_email'),
        Index('ix_training_completions_module_completed', 'module_id', 'completed_at'),
    )


# ============================================================================
# SUPPORT MODELS
# ============================================================================

class SupportTicket(Base):
    """Support ticket records."""
    __tablename__ = 'support_tickets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(String(50), unique=True, nullable=False, index=True)
    client_id = Column(String(100), ForeignKey('customers.client_id', ondelete='CASCADE'), nullable=False, index=True)

    # Content
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(10), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False, default='open', index=True)

    # Requester
    requester_email = Column(String(255), nullable=False)
    requester_name = Column(String(200), nullable=False)

    # Assignment
    assigned_agent = Column(String(255), nullable=True, index=True)
    assigned_team = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    first_response_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True, index=True)
    closed_at = Column(DateTime, nullable=True)

    # SLA tracking
    sla_first_response_minutes = Column(Integer, nullable=False)
    sla_resolution_minutes = Column(Integer, nullable=False)
    first_response_sla_status = Column(String(20), default='not_applicable')
    resolution_sla_status = Column(String(20), default='not_applicable')
    time_to_first_response_minutes = Column(Integer, nullable=True)
    time_to_resolution_minutes = Column(Integer, nullable=True)

    # Satisfaction
    satisfaction_rating = Column(Integer, nullable=True)
    satisfaction_comment = Column(Text, nullable=True)

    # Escalation
    escalated = Column(Boolean, default=False, index=True)
    escalated_at = Column(DateTime, nullable=True)
    escalation_reason = Column(Text, nullable=True)

    # Resolution
    resolution_notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    customer_visible_notes = Column(Text, nullable=True)

    # Relationships
    customer = relationship("CustomerAccount", back_populates="support_tickets")
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_support_tickets_client_status', 'client_id', 'status'),
        Index('ix_support_tickets_priority_created', 'priority', 'created_at'),
        Index('ix_support_tickets_assigned_status', 'assigned_agent', 'status'),
        CheckConstraint('satisfaction_rating >= 1 AND satisfaction_rating <= 5', name='check_satisfaction_range'),
    )


class TicketComment(Base):
    """Comments on support tickets."""
    __tablename__ = 'ticket_comments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(String(50), unique=True, nullable=False, index=True)
    ticket_id = Column(String(50), ForeignKey('support_tickets.ticket_id', ondelete='CASCADE'), nullable=False, index=True)

    author_email = Column(String(255), nullable=False)
    author_name = Column(String(200), nullable=False)
    author_type = Column(String(20), nullable=False)

    content = Column(Text, nullable=False)
    is_public = Column(Boolean, default=True)
    attachments = Column(JSON, default=[])

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationship
    ticket = relationship("SupportTicket", back_populates="comments")

    __table_args__ = (
        Index('ix_ticket_comments_ticket_created', 'ticket_id', 'created_at'),
    )


class KnowledgeBaseArticle(Base):
    """Knowledge base articles."""
    __tablename__ = 'knowledge_base_articles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String(50), unique=True, nullable=False, index=True)

    title = Column(String(200), nullable=False)
    summary = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)

    # Organization
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, nullable=False)

    # Publishing
    status = Column(String(20), nullable=False, default='draft', index=True)
    author = Column(String(200), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True, index=True)
    version = Column(Integer, default=1)

    # Analytics
    view_count = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)
    not_helpful_votes = Column(Integer, default=0)
    helpfulness_score = Column(Float, default=0.0)

    # Relationships
    related_articles = Column(JSON, default=[])
    search_keywords = Column(JSON, default=[])

    # Access control
    customer_facing = Column(Boolean, default=True)
    requires_authentication = Column(Boolean, default=False)
    product_tier_restrictions = Column(JSON, default=[])

    __table_args__ = (
        Index('ix_kb_articles_category_status', 'category', 'status'),
        Index('ix_kb_articles_published', 'published_at'),
    )


# ============================================================================
# RENEWAL MODELS
# ============================================================================

class RenewalForecast(Base):
    """Renewal forecasts."""
    __tablename__ = 'renewal_forecasts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    forecast_id = Column(String(100), unique=True, nullable=False, index=True)
    client_id = Column(String(100), ForeignKey('customers.client_id', ondelete='CASCADE'), nullable=False, index=True)
    contract_id = Column(String(50), nullable=False)

    renewal_date = Column(Date, nullable=False, index=True)
    current_arr = Column(Float, nullable=False)
    forecasted_arr = Column(Float, nullable=False)

    # Prediction
    renewal_probability = Column(Float, nullable=False)
    renewal_status = Column(String(20), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    health_score = Column(Integer, nullable=False)

    # Factors
    risk_factors = Column(JSON, default=[])
    positive_indicators = Column(JSON, default=[])

    # Expansion
    expansion_probability = Column(Float, default=0.0)
    estimated_expansion_value = Column(Float, default=0.0)

    # Timeline
    days_until_renewal = Column(Integer, nullable=False, index=True)
    last_csm_touchpoint = Column(Date, nullable=True)
    next_scheduled_touchpoint = Column(Date, nullable=True)

    recommended_actions = Column(JSON, default=[])

    forecast_created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    forecast_updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    model_version = Column(String(20), default='v1.0.0')

    # Relationship
    customer = relationship("CustomerAccount", back_populates="renewal_forecasts")

    __table_args__ = (
        Index('ix_renewal_forecasts_client_date', 'client_id', 'renewal_date'),
        Index('ix_renewal_forecasts_status_days', 'renewal_status', 'days_until_renewal'),
        CheckConstraint('renewal_probability >= 0 AND renewal_probability <= 1', name='check_renewal_probability_range'),
    )


class ContractDetails(Base):
    """Contract details."""
    __tablename__ = 'contracts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(String(50), unique=True, nullable=False, index=True)
    client_id = Column(String(100), ForeignKey('customers.client_id', ondelete='CASCADE'), nullable=False, index=True)

    # Contract type and value
    contract_type = Column(String(20), nullable=False)
    contract_value = Column(Float, nullable=False)
    billing_frequency = Column(String(20), nullable=False)
    currency = Column(String(3), default='USD')

    # Dates
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    renewal_date = Column(Date, nullable=False, index=True)
    auto_renew = Column(Boolean, default=False)
    notice_period_days = Column(Integer, default=30)

    # Payment
    payment_terms = Column(String(100), nullable=False)
    payment_status = Column(String(20), nullable=False, default='current', index=True)

    # Entitlements
    included_users = Column(Integer, nullable=True)
    included_usage = Column(JSON, default={})
    tier = Column(String(50), nullable=False)
    products_included = Column(JSON, nullable=False)
    addons = Column(JSON, default=[])

    # Pricing
    discount_percentage = Column(Float, default=0.0)
    discount_reason = Column(String(500), nullable=True)

    # Ownership
    signed_by = Column(String(200), nullable=True)
    owner_csm = Column(String(200), nullable=True, index=True)

    last_modified = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    contract_url = Column(String(500), nullable=True)

    # Relationship
    customer = relationship("CustomerAccount", back_populates="contracts")

    __table_args__ = (
        Index('ix_contracts_client_status', 'client_id', 'payment_status'),
        Index('ix_contracts_renewal_date', 'renewal_date'),
        CheckConstraint('contract_value >= 0', name='check_contract_value_positive'),
    )


class ExpansionOpportunity(Base):
    """Expansion opportunities."""
    __tablename__ = 'expansion_opportunities'

    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_id = Column(String(50), unique=True, nullable=False, index=True)
    client_id = Column(String(100), nullable=False, index=True)

    opportunity_name = Column(String(200), nullable=False)
    expansion_type = Column(String(50), nullable=False, index=True)

    # Value and probability
    estimated_value = Column(Float, nullable=False)
    probability = Column(Float, nullable=False)
    confidence_score = Column(Float, default=0.5)
    expected_close_date = Column(Date, nullable=True, index=True)
    current_stage = Column(String(50), nullable=False, index=True)

    # Details
    requirements = Column(JSON, default=[])
    value_drivers = Column(JSON, default=[])
    blockers = Column(JSON, default=[])

    # Stakeholders
    champion = Column(String(200), nullable=True)
    decision_makers = Column(JSON, default=[])
    competitive_pressure = Column(String(20), default='unknown')

    # Ownership
    assigned_to = Column(String(200), nullable=True, index=True)
    next_action = Column(String(500), nullable=True)
    next_action_date = Column(Date, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_expansion_opportunities_client_stage', 'client_id', 'current_stage'),
        Index('ix_expansion_opportunities_close_date', 'expected_close_date'),
        CheckConstraint('probability >= 0 AND probability <= 1', name='check_probability_range'),
    )


class RenewalCampaign(Base):
    """Renewal campaigns."""
    __tablename__ = 'renewal_campaigns'

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String(50), unique=True, nullable=False, index=True)
    campaign_name = Column(String(200), nullable=False)

    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False)
    target_renewal_date_range = Column(JSON, nullable=False)

    # Volume metrics
    total_customers = Column(Integer, nullable=False)
    total_arr_at_risk = Column(Float, nullable=False)
    customers_contacted = Column(Integer, default=0)
    customers_committed = Column(Integer, default=0)
    customers_at_risk = Column(Integer, default=0)

    # Performance
    win_rate = Column(Float, default=0.0)
    expansion_opportunities_identified = Column(Integer, default=0)
    expansion_value_identified = Column(Float, default=0.0)

    campaign_activities = Column(JSON, default=[])
    success_metrics = Column(JSON, default={})

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# FEEDBACK MODELS
# ============================================================================

class CustomerFeedback(Base):
    """Customer feedback records."""
    __tablename__ = 'customer_feedback'

    id = Column(Integer, primary_key=True, autoincrement=True)
    feedback_id = Column(String(50), unique=True, nullable=False, index=True)
    client_id = Column(String(100), ForeignKey('customers.client_id', ondelete='CASCADE'), nullable=False, index=True)

    feedback_type = Column(String(50), nullable=False, index=True)
    source = Column(String(100), nullable=False)

    # Submitter
    submitter_email = Column(String(255), nullable=False)
    submitter_name = Column(String(200), nullable=False)

    # Content
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    tags = Column(JSON, default=[])

    # Sentiment
    sentiment = Column(String(20), nullable=False, index=True)
    sentiment_score = Column(Float, nullable=False)

    # Prioritization
    priority = Column(String(20), nullable=False, default='medium', index=True)
    status = Column(String(20), nullable=False, default='new', index=True)
    impact_assessment = Column(Text, nullable=True)

    # Assignment
    assigned_to = Column(String(200), nullable=True, index=True)
    follow_up_required = Column(Boolean, default=False)
    follow_up_by = Column(Date, nullable=True)
    customer_responded = Column(Boolean, default=False)
    resolution_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationship
    customer = relationship("CustomerAccount", back_populates="feedback")

    __table_args__ = (
        Index('ix_customer_feedback_client_status', 'client_id', 'status'),
        Index('ix_customer_feedback_sentiment_created', 'sentiment', 'created_at'),
        Index('ix_customer_feedback_priority_status', 'priority', 'status'),
        CheckConstraint('sentiment_score >= -1 AND sentiment_score <= 1', name='check_sentiment_score_range'),
    )


class NPSResponse(Base):
    """NPS survey responses."""
    __tablename__ = 'nps_responses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    response_id = Column(String(50), unique=True, nullable=False, index=True)
    client_id = Column(String(100), ForeignKey('customers.client_id', ondelete='CASCADE'), nullable=False, index=True)
    survey_id = Column(String(50), nullable=False, index=True)

    # Respondent
    respondent_email = Column(String(255), nullable=False)
    respondent_name = Column(String(200), nullable=False)

    # NPS score
    score = Column(Integer, nullable=False)
    category = Column(String(20), nullable=False, index=True)
    reason = Column(Text, nullable=True)

    # Follow-up questions
    follow_up_question_1 = Column(Text, nullable=True)
    follow_up_answer_1 = Column(Text, nullable=True)
    follow_up_question_2 = Column(Text, nullable=True)
    follow_up_answer_2 = Column(Text, nullable=True)

    # Sentiment
    sentiment = Column(String(20), nullable=False)
    sentiment_score = Column(Float, nullable=False)

    # Follow-up tracking
    follow_up_required = Column(Boolean, default=False)
    contacted = Column(Boolean, default=False)

    survey_sent_at = Column(DateTime, nullable=False)
    responded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    response_time_hours = Column(Float, nullable=False)

    # Relationship
    customer = relationship("CustomerAccount", back_populates="nps_responses")

    __table_args__ = (
        Index('ix_nps_responses_client_score', 'client_id', 'score'),
        Index('ix_nps_responses_survey_category', 'survey_id', 'category'),
        Index('ix_nps_responses_responded_at', 'responded_at'),
        CheckConstraint('score >= 0 AND score <= 10', name='check_nps_score_range'),
        CheckConstraint('sentiment_score >= -1 AND sentiment_score <= 1', name='check_nps_sentiment_range'),
    )


class SentimentAnalysis(Base):
    """Aggregated sentiment analysis."""
    __tablename__ = 'sentiment_analysis'

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(100), unique=True, nullable=False, index=True)
    client_id = Column(String(100), nullable=True, index=True)

    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # Volume
    total_feedback_items = Column(Integer, nullable=False)
    feedback_by_type = Column(JSON, nullable=False)

    # Sentiment
    overall_sentiment = Column(String(20), nullable=False)
    overall_sentiment_score = Column(Float, nullable=False)
    sentiment_distribution = Column(JSON, nullable=False)
    sentiment_trend = Column(String(20), nullable=False)

    # Themes
    top_positive_themes = Column(JSON, default=[])
    top_negative_themes = Column(JSON, default=[])
    action_items = Column(JSON, default=[])

    # Scores
    nps_score = Column(Integer, nullable=True)
    csat_score = Column(Float, nullable=True)

    analyzed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_sentiment_analysis_client_period', 'client_id', 'period_start'),
    )


class SurveyTemplate(Base):
    """Survey templates."""
    __tablename__ = 'survey_templates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(String(100), unique=True, nullable=False, index=True)
    template_name = Column(String(200), nullable=False)
    template_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)

    questions = Column(JSON, nullable=False)
    targeting = Column(JSON, default={})
    frequency = Column(String(50), default='one_time')
    active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class HealthMetrics(Base):
    """Comprehensive health metrics."""
    __tablename__ = 'health_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), nullable=False, index=True)

    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # Overall health
    overall_health_score = Column(Integer, nullable=False)
    health_score_trend = Column(String(10), nullable=False)
    health_score_change = Column(Integer, nullable=False)

    # Components
    health_components = Column(JSON, nullable=False)
    component_trends = Column(JSON, nullable=False)

    # Indicators
    risk_indicators = Column(JSON, default=[])
    positive_indicators = Column(JSON, default=[])

    # Benchmarking
    benchmark_comparison = Column(JSON, default={})

    # Predictions
    predicted_next_period_score = Column(Integer, nullable=True)
    confidence = Column(Float, default=0.0)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_health_metrics_client_period', 'client_id', 'period_start'),
    )


class EngagementMetrics(Base):
    """Engagement metrics."""
    __tablename__ = 'engagement_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), nullable=False, index=True)

    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # User metrics
    total_users = Column(Integer, nullable=False)
    active_users = Column(Integer, nullable=False)
    daily_active_users = Column(Integer, nullable=False)
    weekly_active_users = Column(Integer, nullable=False)
    monthly_active_users = Column(Integer, nullable=False)

    # Engagement rates
    activation_rate = Column(Float, nullable=False)
    engagement_rate = Column(Float, nullable=False)

    # Activity
    total_logins = Column(Integer, nullable=False)
    avg_logins_per_user = Column(Float, nullable=False)
    total_session_minutes = Column(Integer, nullable=False)
    avg_session_duration_minutes = Column(Float, nullable=False)
    total_actions = Column(Integer, nullable=False)
    avg_actions_per_session = Column(Float, nullable=False)

    # Feature adoption
    feature_adoption = Column(JSON, nullable=False)

    # User segmentation
    power_users = Column(Integer, default=0)
    inactive_users = Column(Integer, default=0)
    at_risk_users = Column(Integer, default=0)

    # Trends
    engagement_trend = Column(String(10), nullable=False)
    vs_previous_period = Column(JSON, default={})

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_engagement_metrics_client_period', 'client_id', 'period_start'),
    )


class UsageAnalytics(Base):
    """Usage analytics."""
    __tablename__ = 'usage_analytics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(String(100), nullable=False, index=True)

    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)

    # Overall usage
    total_usage_events = Column(Integer, nullable=False)
    unique_features_used = Column(Integer, nullable=False)
    total_features_available = Column(Integer, nullable=False)
    feature_utilization_rate = Column(Float, nullable=False)

    # Feature breakdown
    top_features = Column(JSON, nullable=False)
    underutilized_features = Column(JSON, default=[])
    new_feature_adoption = Column(JSON, default={})

    # User segmentation
    usage_by_user_role = Column(JSON, default={})

    # Integration and API
    integration_usage = Column(JSON, default={})
    api_usage = Column(JSON, default={})

    # Trends
    usage_trend = Column(String(10), nullable=False)
    usage_growth_rate = Column(Float, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_usage_analytics_client_period', 'client_id', 'period_start'),
    )


class CohortAnalysis(Base):
    """Cohort analysis."""
    __tablename__ = 'cohort_analysis'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cohort_id = Column(String(100), unique=True, nullable=False, index=True)
    cohort_name = Column(String(200), nullable=False)

    cohort_definition = Column(JSON, nullable=False)
    cohort_size = Column(Integer, nullable=False)
    analysis_date = Column(Date, nullable=False, index=True)
    months_since_cohort = Column(Integer, nullable=False)

    # Retention and engagement
    retention_by_month = Column(JSON, nullable=False)
    engagement_by_month = Column(JSON, nullable=False)

    # Revenue
    revenue_metrics = Column(JSON, nullable=False)

    # Benchmarking
    benchmark_comparison = Column(JSON, default={})

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# Export all models
__all__ = [
    'CustomerAccount', 'HealthScoreComponents', 'CustomerSegment', 'RiskIndicator', 'ChurnPrediction',
    'OnboardingPlan', 'OnboardingMilestone', 'TrainingModule', 'TrainingCompletion',
    'SupportTicket', 'TicketComment', 'KnowledgeBaseArticle',
    'RenewalForecast', 'ContractDetails', 'ExpansionOpportunity', 'RenewalCampaign',
    'CustomerFeedback', 'NPSResponse', 'SentimentAnalysis', 'SurveyTemplate',
    'HealthMetrics', 'EngagementMetrics', 'UsageAnalytics', 'CohortAnalysis'
]
