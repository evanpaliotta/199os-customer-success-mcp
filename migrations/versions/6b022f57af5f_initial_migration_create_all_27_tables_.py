"""Initial migration: create all 27+ tables with indexes and constraints

Revision ID: 6b022f57af5f
Revises: 
Create Date: 2025-10-10 10:34:06.435383

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b022f57af5f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create all 27+ tables with indexes and foreign keys."""

    # ========================================================================
    # CUSTOMER TABLES
    # ========================================================================

    # Create customers table (main customer account)
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('client_name', sa.String(200), nullable=False),
        sa.Column('company_name', sa.String(200), nullable=False),
        sa.Column('industry', sa.String(100), server_default='Technology'),
        sa.Column('tier', sa.String(50), nullable=False, server_default='standard'),
        sa.Column('lifecycle_stage', sa.String(50), nullable=False, server_default='onboarding'),
        sa.Column('contract_value', sa.Float(), server_default='0.0'),
        sa.Column('contract_start_date', sa.Date(), nullable=False),
        sa.Column('contract_end_date', sa.Date(), nullable=True),
        sa.Column('renewal_date', sa.Date(), nullable=True),
        sa.Column('primary_contact_email', sa.String(255), nullable=True),
        sa.Column('primary_contact_name', sa.String(200), nullable=True),
        sa.Column('csm_assigned', sa.String(200), nullable=True),
        sa.Column('health_score', sa.Integer(), server_default='50'),
        sa.Column('health_trend', sa.String(20), server_default='stable'),
        sa.Column('last_engagement_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_id'),
        sa.CheckConstraint('health_score >= 0 AND health_score <= 100', name='check_health_score_range'),
        sa.CheckConstraint('contract_value >= 0', name='check_contract_value_positive')
    )

    # Create indexes for customers table
    op.create_index('ix_customers_client_id', 'customers', ['client_id'])
    op.create_index('ix_customers_tier', 'customers', ['tier'])
    op.create_index('ix_customers_lifecycle_stage', 'customers', ['lifecycle_stage'])
    op.create_index('ix_customers_contract_start_date', 'customers', ['contract_start_date'])
    op.create_index('ix_customers_renewal_date', 'customers', ['renewal_date'])
    op.create_index('ix_customers_csm_assigned', 'customers', ['csm_assigned'])
    op.create_index('ix_customers_health_score', 'customers', ['health_score'])
    op.create_index('ix_customers_last_engagement_date', 'customers', ['last_engagement_date'])
    op.create_index('ix_customers_status', 'customers', ['status'])
    op.create_index('ix_customers_created_at', 'customers', ['created_at'])
    op.create_index('ix_customers_client_id_created_at', 'customers', ['client_id', 'created_at'])
    op.create_index('ix_customers_health_score_status', 'customers', ['health_score', 'status'])
    op.create_index('ix_customers_csm_lifecycle', 'customers', ['csm_assigned', 'lifecycle_stage'])

    # Create health_scores table
    op.create_table(
        'health_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('usage_score', sa.Float(), nullable=False),
        sa.Column('engagement_score', sa.Float(), nullable=False),
        sa.Column('support_score', sa.Float(), nullable=False),
        sa.Column('satisfaction_score', sa.Float(), nullable=False),
        sa.Column('payment_score', sa.Float(), nullable=False),
        sa.Column('usage_weight', sa.Float(), server_default='0.35'),
        sa.Column('engagement_weight', sa.Float(), server_default='0.25'),
        sa.Column('support_weight', sa.Float(), server_default='0.15'),
        sa.Column('satisfaction_weight', sa.Float(), server_default='0.15'),
        sa.Column('payment_weight', sa.Float(), server_default='0.10'),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['client_id'], ['customers.client_id'], ondelete='CASCADE'),
        sa.CheckConstraint('usage_score >= 0 AND usage_score <= 100', name='check_usage_score_range'),
        sa.CheckConstraint('engagement_score >= 0 AND engagement_score <= 100', name='check_engagement_score_range')
    )
    op.create_index('ix_health_scores_client_id', 'health_scores', ['client_id'])
    op.create_index('ix_health_scores_created_at', 'health_scores', ['created_at'])
    op.create_index('ix_health_scores_client_created', 'health_scores', ['client_id', 'created_at'])

    # Create customer_segments table
    op.create_table(
        'customer_segments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('segment_id', sa.String(100), nullable=False),
        sa.Column('segment_name', sa.String(200), nullable=False),
        sa.Column('segment_type', sa.String(50), nullable=False),
        sa.Column('criteria', sa.JSON(), nullable=False),
        sa.Column('characteristics', sa.JSON(), server_default='{}'),
        sa.Column('engagement_strategy', sa.JSON(), server_default='{}'),
        sa.Column('success_metrics', sa.JSON(), server_default='{}'),
        sa.Column('customer_count', sa.Integer(), server_default='0'),
        sa.Column('total_arr', sa.Float(), server_default='0.0'),
        sa.Column('avg_health_score', sa.Float(), server_default='50.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('segment_id')
    )
    op.create_index('ix_customer_segments_segment_id', 'customer_segments', ['segment_id'])
    op.create_index('ix_customer_segments_segment_type', 'customer_segments', ['segment_type'])

    # Create risk_indicators table
    op.create_table(
        'risk_indicators',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('indicator_id', sa.String(100), nullable=False),
        sa.Column('indicator_name', sa.String(200), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('current_value', sa.Float(), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('mitigation_actions', sa.JSON(), server_default='[]'),
        sa.Column('detected_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['client_id'], ['customers.client_id'], ondelete='CASCADE')
    )
    op.create_index('ix_risk_indicators_client_id', 'risk_indicators', ['client_id'])
    op.create_index('ix_risk_indicators_category', 'risk_indicators', ['category'])
    op.create_index('ix_risk_indicators_severity', 'risk_indicators', ['severity'])
    op.create_index('ix_risk_indicators_detected_at', 'risk_indicators', ['detected_at'])
    op.create_index('ix_risk_indicators_client_severity', 'risk_indicators', ['client_id', 'severity'])
    op.create_index('ix_risk_indicators_detected', 'risk_indicators', ['detected_at'])

    # Create churn_predictions table
    op.create_table(
        'churn_predictions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('prediction_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('churn_probability', sa.Float(), nullable=False),
        sa.Column('churn_risk_level', sa.String(20), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('contributing_factors', sa.JSON(), server_default='[]'),
        sa.Column('predicted_churn_date', sa.Date(), nullable=True),
        sa.Column('retention_recommendations', sa.JSON(), server_default='[]'),
        sa.Column('model_version', sa.String(20), server_default='v1.0.0'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['client_id'], ['customers.client_id'], ondelete='CASCADE'),
        sa.CheckConstraint('churn_probability >= 0 AND churn_probability <= 1', name='check_churn_probability_range')
    )
    op.create_index('ix_churn_predictions_client_id', 'churn_predictions', ['client_id'])
    op.create_index('ix_churn_predictions_prediction_date', 'churn_predictions', ['prediction_date'])
    op.create_index('ix_churn_predictions_churn_risk_level', 'churn_predictions', ['churn_risk_level'])
    op.create_index('ix_churn_predictions_client_date', 'churn_predictions', ['client_id', 'prediction_date'])
    op.create_index('ix_churn_predictions_risk_level', 'churn_predictions', ['churn_risk_level'])

    # ========================================================================
    # ONBOARDING TABLES
    # ========================================================================

    # Create onboarding_plans table
    op.create_table(
        'onboarding_plans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('plan_id', sa.String(100), nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('plan_name', sa.String(200), nullable=False),
        sa.Column('product_tier', sa.String(50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('target_completion_date', sa.Date(), nullable=False),
        sa.Column('actual_completion_date', sa.Date(), nullable=True),
        sa.Column('timeline_weeks', sa.Integer(), nullable=False),
        sa.Column('customer_goals', sa.JSON(), nullable=False),
        sa.Column('success_criteria', sa.JSON(), nullable=False),
        sa.Column('total_estimated_hours', sa.Integer(), server_default='0'),
        sa.Column('assigned_csm', sa.String(200), nullable=True),
        sa.Column('assigned_implementation_team', sa.JSON(), server_default='[]'),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('completion_percentage', sa.Float(), server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id'),
        sa.ForeignKeyConstraint(['client_id'], ['customers.client_id'], ondelete='CASCADE')
    )
    op.create_index('ix_onboarding_plans_plan_id', 'onboarding_plans', ['plan_id'])
    op.create_index('ix_onboarding_plans_client_id', 'onboarding_plans', ['client_id'])
    op.create_index('ix_onboarding_plans_start_date', 'onboarding_plans', ['start_date'])
    op.create_index('ix_onboarding_plans_assigned_csm', 'onboarding_plans', ['assigned_csm'])
    op.create_index('ix_onboarding_plans_status', 'onboarding_plans', ['status'])
    op.create_index('ix_onboarding_plans_client_status', 'onboarding_plans', ['client_id', 'status'])

    # Create onboarding_milestones table
    op.create_table(
        'onboarding_milestones',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('milestone_id', sa.String(100), nullable=False),
        sa.Column('plan_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('week', sa.Integer(), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('tasks', sa.JSON(), nullable=False),
        sa.Column('success_criteria', sa.JSON(), server_default='[]'),
        sa.Column('dependencies', sa.JSON(), server_default='[]'),
        sa.Column('estimated_hours', sa.Integer(), nullable=False),
        sa.Column('actual_hours', sa.Integer(), nullable=True),
        sa.Column('assigned_to', sa.String(200), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('completion_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='not_started'),
        sa.Column('completion_percentage', sa.Float(), server_default='0.0'),
        sa.Column('blockers', sa.JSON(), server_default='[]'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['plan_id'], ['onboarding_plans.plan_id'], ondelete='CASCADE')
    )
    op.create_index('ix_onboarding_milestones_plan_id', 'onboarding_milestones', ['plan_id'])
    op.create_index('ix_onboarding_milestones_assigned_to', 'onboarding_milestones', ['assigned_to'])
    op.create_index('ix_onboarding_milestones_due_date', 'onboarding_milestones', ['due_date'])
    op.create_index('ix_onboarding_milestones_status', 'onboarding_milestones', ['status'])
    op.create_index('ix_onboarding_milestones_plan_status', 'onboarding_milestones', ['plan_id', 'status'])

    # Create training_modules table
    op.create_table(
        'training_modules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('module_id', sa.String(100), nullable=False),
        sa.Column('module_name', sa.String(200), nullable=False),
        sa.Column('module_description', sa.Text(), nullable=False),
        sa.Column('format', sa.String(50), nullable=False),
        sa.Column('certification_level', sa.String(50), server_default='basic'),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('content_url', sa.String(500), nullable=True),
        sa.Column('prerequisites', sa.JSON(), server_default='[]'),
        sa.Column('learning_objectives', sa.JSON(), nullable=False),
        sa.Column('topics_covered', sa.JSON(), nullable=False),
        sa.Column('assessment_required', sa.Boolean(), server_default='true'),
        sa.Column('passing_score', sa.Float(), server_default='0.75'),
        sa.Column('certification_awarded', sa.String(200), nullable=True),
        sa.Column('max_attempts', sa.Integer(), server_default='3'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('module_id')
    )
    op.create_index('ix_training_modules_module_id', 'training_modules', ['module_id'])

    # Create training_completions table
    op.create_table(
        'training_completions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('completion_id', sa.String(100), nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('module_id', sa.String(100), nullable=False),
        sa.Column('user_email', sa.String(255), nullable=False),
        sa.Column('user_name', sa.String(200), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('time_spent_minutes', sa.Integer(), server_default='0'),
        sa.Column('assessment_score', sa.Float(), nullable=True),
        sa.Column('attempts_used', sa.Integer(), server_default='0'),
        sa.Column('passed', sa.Boolean(), server_default='false'),
        sa.Column('certification_issued', sa.Boolean(), server_default='false'),
        sa.Column('certification_id', sa.String(100), nullable=True),
        sa.Column('feedback_rating', sa.Float(), nullable=True),
        sa.Column('feedback_comments', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('completion_id'),
        sa.ForeignKeyConstraint(['module_id'], ['training_modules.module_id'], ondelete='CASCADE')
    )
    op.create_index('ix_training_completions_completion_id', 'training_completions', ['completion_id'])
    op.create_index('ix_training_completions_client_id', 'training_completions', ['client_id'])
    op.create_index('ix_training_completions_module_id', 'training_completions', ['module_id'])
    op.create_index('ix_training_completions_user_email', 'training_completions', ['user_email'])
    op.create_index('ix_training_completions_started_at', 'training_completions', ['started_at'])
    op.create_index('ix_training_completions_client_user', 'training_completions', ['client_id', 'user_email'])
    op.create_index('ix_training_completions_module_completed', 'training_completions', ['module_id', 'completed_at'])

    # ========================================================================
    # SUPPORT TABLES
    # ========================================================================

    # Create support_tickets table
    op.create_table(
        'support_tickets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ticket_id', sa.String(50), nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(10), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('requester_email', sa.String(255), nullable=False),
        sa.Column('requester_name', sa.String(200), nullable=False),
        sa.Column('assigned_agent', sa.String(255), nullable=True),
        sa.Column('assigned_team', sa.String(100), nullable=True),
        sa.Column('tags', sa.JSON(), server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('first_response_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('sla_first_response_minutes', sa.Integer(), nullable=False),
        sa.Column('sla_resolution_minutes', sa.Integer(), nullable=False),
        sa.Column('first_response_sla_status', sa.String(20), server_default='not_applicable'),
        sa.Column('resolution_sla_status', sa.String(20), server_default='not_applicable'),
        sa.Column('time_to_first_response_minutes', sa.Integer(), nullable=True),
        sa.Column('time_to_resolution_minutes', sa.Integer(), nullable=True),
        sa.Column('satisfaction_rating', sa.Integer(), nullable=True),
        sa.Column('satisfaction_comment', sa.Text(), nullable=True),
        sa.Column('escalated', sa.Boolean(), server_default='false'),
        sa.Column('escalated_at', sa.DateTime(), nullable=True),
        sa.Column('escalation_reason', sa.Text(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),
        sa.Column('customer_visible_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticket_id'),
        sa.ForeignKeyConstraint(['client_id'], ['customers.client_id'], ondelete='CASCADE'),
        sa.CheckConstraint('satisfaction_rating >= 1 AND satisfaction_rating <= 5', name='check_satisfaction_range')
    )
    op.create_index('ix_support_tickets_ticket_id', 'support_tickets', ['ticket_id'])
    op.create_index('ix_support_tickets_client_id', 'support_tickets', ['client_id'])
    op.create_index('ix_support_tickets_priority', 'support_tickets', ['priority'])
    op.create_index('ix_support_tickets_category', 'support_tickets', ['category'])
    op.create_index('ix_support_tickets_status', 'support_tickets', ['status'])
    op.create_index('ix_support_tickets_assigned_agent', 'support_tickets', ['assigned_agent'])
    op.create_index('ix_support_tickets_assigned_team', 'support_tickets', ['assigned_team'])
    op.create_index('ix_support_tickets_created_at', 'support_tickets', ['created_at'])
    op.create_index('ix_support_tickets_resolved_at', 'support_tickets', ['resolved_at'])
    op.create_index('ix_support_tickets_escalated', 'support_tickets', ['escalated'])
    op.create_index('ix_support_tickets_client_status', 'support_tickets', ['client_id', 'status'])
    op.create_index('ix_support_tickets_priority_created', 'support_tickets', ['priority', 'created_at'])
    op.create_index('ix_support_tickets_assigned_status', 'support_tickets', ['assigned_agent', 'status'])

    # Create ticket_comments table
    op.create_table(
        'ticket_comments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('comment_id', sa.String(50), nullable=False),
        sa.Column('ticket_id', sa.String(50), nullable=False),
        sa.Column('author_email', sa.String(255), nullable=False),
        sa.Column('author_name', sa.String(200), nullable=False),
        sa.Column('author_type', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default='true'),
        sa.Column('attachments', sa.JSON(), server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('comment_id'),
        sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.ticket_id'], ondelete='CASCADE')
    )
    op.create_index('ix_ticket_comments_comment_id', 'ticket_comments', ['comment_id'])
    op.create_index('ix_ticket_comments_ticket_id', 'ticket_comments', ['ticket_id'])
    op.create_index('ix_ticket_comments_created_at', 'ticket_comments', ['created_at'])
    op.create_index('ix_ticket_comments_ticket_created', 'ticket_comments', ['ticket_id', 'created_at'])

    # Create knowledge_base_articles table
    op.create_table(
        'knowledge_base_articles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('article_id', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('summary', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('author', sa.String(200), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('view_count', sa.Integer(), server_default='0'),
        sa.Column('helpful_votes', sa.Integer(), server_default='0'),
        sa.Column('not_helpful_votes', sa.Integer(), server_default='0'),
        sa.Column('helpfulness_score', sa.Float(), server_default='0.0'),
        sa.Column('related_articles', sa.JSON(), server_default='[]'),
        sa.Column('search_keywords', sa.JSON(), server_default='[]'),
        sa.Column('customer_facing', sa.Boolean(), server_default='true'),
        sa.Column('requires_authentication', sa.Boolean(), server_default='false'),
        sa.Column('product_tier_restrictions', sa.JSON(), server_default='[]'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article_id')
    )
    op.create_index('ix_kb_articles_article_id', 'knowledge_base_articles', ['article_id'])
    op.create_index('ix_kb_articles_category', 'knowledge_base_articles', ['category'])
    op.create_index('ix_kb_articles_subcategory', 'knowledge_base_articles', ['subcategory'])
    op.create_index('ix_kb_articles_status', 'knowledge_base_articles', ['status'])
    op.create_index('ix_kb_articles_published_at', 'knowledge_base_articles', ['published_at'])
    op.create_index('ix_kb_articles_category_status', 'knowledge_base_articles', ['category', 'status'])
    op.create_index('ix_kb_articles_published', 'knowledge_base_articles', ['published_at'])

    # ========================================================================
    # RENEWAL TABLES
    # ========================================================================

    # Create renewal_forecasts table
    op.create_table(
        'renewal_forecasts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('forecast_id', sa.String(100), nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('contract_id', sa.String(50), nullable=False),
        sa.Column('renewal_date', sa.Date(), nullable=False),
        sa.Column('current_arr', sa.Float(), nullable=False),
        sa.Column('forecasted_arr', sa.Float(), nullable=False),
        sa.Column('renewal_probability', sa.Float(), nullable=False),
        sa.Column('renewal_status', sa.String(20), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('health_score', sa.Integer(), nullable=False),
        sa.Column('risk_factors', sa.JSON(), server_default='[]'),
        sa.Column('positive_indicators', sa.JSON(), server_default='[]'),
        sa.Column('expansion_probability', sa.Float(), server_default='0.0'),
        sa.Column('estimated_expansion_value', sa.Float(), server_default='0.0'),
        sa.Column('days_until_renewal', sa.Integer(), nullable=False),
        sa.Column('last_csm_touchpoint', sa.Date(), nullable=True),
        sa.Column('next_scheduled_touchpoint', sa.Date(), nullable=True),
        sa.Column('recommended_actions', sa.JSON(), server_default='[]'),
        sa.Column('forecast_created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('forecast_updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('model_version', sa.String(20), server_default='v1.0.0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('forecast_id'),
        sa.ForeignKeyConstraint(['client_id'], ['customers.client_id'], ondelete='CASCADE'),
        sa.CheckConstraint('renewal_probability >= 0 AND renewal_probability <= 1', name='check_renewal_probability_range')
    )
    op.create_index('ix_renewal_forecasts_forecast_id', 'renewal_forecasts', ['forecast_id'])
    op.create_index('ix_renewal_forecasts_client_id', 'renewal_forecasts', ['client_id'])
    op.create_index('ix_renewal_forecasts_renewal_date', 'renewal_forecasts', ['renewal_date'])
    op.create_index('ix_renewal_forecasts_renewal_status', 'renewal_forecasts', ['renewal_status'])
    op.create_index('ix_renewal_forecasts_days_until_renewal', 'renewal_forecasts', ['days_until_renewal'])
    op.create_index('ix_renewal_forecasts_client_date', 'renewal_forecasts', ['client_id', 'renewal_date'])
    op.create_index('ix_renewal_forecasts_status_days', 'renewal_forecasts', ['renewal_status', 'days_until_renewal'])

    # Create contracts table
    op.create_table(
        'contracts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('contract_id', sa.String(50), nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('contract_type', sa.String(20), nullable=False),
        sa.Column('contract_value', sa.Float(), nullable=False),
        sa.Column('billing_frequency', sa.String(20), nullable=False),
        sa.Column('currency', sa.String(3), server_default='USD'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('renewal_date', sa.Date(), nullable=False),
        sa.Column('auto_renew', sa.Boolean(), server_default='false'),
        sa.Column('notice_period_days', sa.Integer(), server_default='30'),
        sa.Column('payment_terms', sa.String(100), nullable=False),
        sa.Column('payment_status', sa.String(20), nullable=False, server_default='current'),
        sa.Column('included_users', sa.Integer(), nullable=True),
        sa.Column('included_usage', sa.JSON(), server_default='{}'),
        sa.Column('tier', sa.String(50), nullable=False),
        sa.Column('products_included', sa.JSON(), nullable=False),
        sa.Column('addons', sa.JSON(), server_default='[]'),
        sa.Column('discount_percentage', sa.Float(), server_default='0.0'),
        sa.Column('discount_reason', sa.String(500), nullable=True),
        sa.Column('signed_by', sa.String(200), nullable=True),
        sa.Column('owner_csm', sa.String(200), nullable=True),
        sa.Column('last_modified', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('contract_url', sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contract_id'),
        sa.ForeignKeyConstraint(['client_id'], ['customers.client_id'], ondelete='CASCADE'),
        sa.CheckConstraint('contract_value >= 0', name='check_contract_value_positive')
    )
    op.create_index('ix_contracts_contract_id', 'contracts', ['contract_id'])
    op.create_index('ix_contracts_client_id', 'contracts', ['client_id'])
    op.create_index('ix_contracts_start_date', 'contracts', ['start_date'])
    op.create_index('ix_contracts_end_date', 'contracts', ['end_date'])
    op.create_index('ix_contracts_renewal_date', 'contracts', ['renewal_date'])
    op.create_index('ix_contracts_payment_status', 'contracts', ['payment_status'])
    op.create_index('ix_contracts_owner_csm', 'contracts', ['owner_csm'])
    op.create_index('ix_contracts_client_status', 'contracts', ['client_id', 'payment_status'])

    # Create expansion_opportunities table
    op.create_table(
        'expansion_opportunities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('opportunity_id', sa.String(50), nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('opportunity_name', sa.String(200), nullable=False),
        sa.Column('expansion_type', sa.String(50), nullable=False),
        sa.Column('estimated_value', sa.Float(), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('confidence_score', sa.Float(), server_default='0.5'),
        sa.Column('expected_close_date', sa.Date(), nullable=True),
        sa.Column('current_stage', sa.String(50), nullable=False),
        sa.Column('requirements', sa.JSON(), server_default='[]'),
        sa.Column('value_drivers', sa.JSON(), server_default='[]'),
        sa.Column('blockers', sa.JSON(), server_default='[]'),
        sa.Column('champion', sa.String(200), nullable=True),
        sa.Column('decision_makers', sa.JSON(), server_default='[]'),
        sa.Column('competitive_pressure', sa.String(20), server_default='unknown'),
        sa.Column('assigned_to', sa.String(200), nullable=True),
        sa.Column('next_action', sa.String(500), nullable=True),
        sa.Column('next_action_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('opportunity_id'),
        sa.CheckConstraint('probability >= 0 AND probability <= 1', name='check_probability_range')
    )
    op.create_index('ix_expansion_opportunities_opportunity_id', 'expansion_opportunities', ['opportunity_id'])
    op.create_index('ix_expansion_opportunities_client_id', 'expansion_opportunities', ['client_id'])
    op.create_index('ix_expansion_opportunities_expansion_type', 'expansion_opportunities', ['expansion_type'])
    op.create_index('ix_expansion_opportunities_expected_close_date', 'expansion_opportunities', ['expected_close_date'])
    op.create_index('ix_expansion_opportunities_current_stage', 'expansion_opportunities', ['current_stage'])
    op.create_index('ix_expansion_opportunities_assigned_to', 'expansion_opportunities', ['assigned_to'])
    op.create_index('ix_expansion_opportunities_client_stage', 'expansion_opportunities', ['client_id', 'current_stage'])
    op.create_index('ix_expansion_opportunities_close_date', 'expansion_opportunities', ['expected_close_date'])

    # Create renewal_campaigns table
    op.create_table(
        'renewal_campaigns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('campaign_id', sa.String(50), nullable=False),
        sa.Column('campaign_name', sa.String(200), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('target_renewal_date_range', sa.JSON(), nullable=False),
        sa.Column('total_customers', sa.Integer(), nullable=False),
        sa.Column('total_arr_at_risk', sa.Float(), nullable=False),
        sa.Column('customers_contacted', sa.Integer(), server_default='0'),
        sa.Column('customers_committed', sa.Integer(), server_default='0'),
        sa.Column('customers_at_risk', sa.Integer(), server_default='0'),
        sa.Column('win_rate', sa.Float(), server_default='0.0'),
        sa.Column('expansion_opportunities_identified', sa.Integer(), server_default='0'),
        sa.Column('expansion_value_identified', sa.Float(), server_default='0.0'),
        sa.Column('campaign_activities', sa.JSON(), server_default='[]'),
        sa.Column('success_metrics', sa.JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id')
    )
    op.create_index('ix_renewal_campaigns_campaign_id', 'renewal_campaigns', ['campaign_id'])
    op.create_index('ix_renewal_campaigns_start_date', 'renewal_campaigns', ['start_date'])

    # ========================================================================
    # FEEDBACK TABLES
    # ========================================================================

    # Create customer_feedback table
    op.create_table(
        'customer_feedback',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('feedback_id', sa.String(50), nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('feedback_type', sa.String(50), nullable=False),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('submitter_email', sa.String(255), nullable=False),
        sa.Column('submitter_name', sa.String(200), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('tags', sa.JSON(), server_default='[]'),
        sa.Column('sentiment', sa.String(20), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(20), nullable=False, server_default='new'),
        sa.Column('impact_assessment', sa.Text(), nullable=True),
        sa.Column('assigned_to', sa.String(200), nullable=True),
        sa.Column('follow_up_required', sa.Boolean(), server_default='false'),
        sa.Column('follow_up_by', sa.Date(), nullable=True),
        sa.Column('customer_responded', sa.Boolean(), server_default='false'),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('feedback_id'),
        sa.ForeignKeyConstraint(['client_id'], ['customers.client_id'], ondelete='CASCADE'),
        sa.CheckConstraint('sentiment_score >= -1 AND sentiment_score <= 1', name='check_sentiment_score_range')
    )
    op.create_index('ix_customer_feedback_feedback_id', 'customer_feedback', ['feedback_id'])
    op.create_index('ix_customer_feedback_client_id', 'customer_feedback', ['client_id'])
    op.create_index('ix_customer_feedback_feedback_type', 'customer_feedback', ['feedback_type'])
    op.create_index('ix_customer_feedback_category', 'customer_feedback', ['category'])
    op.create_index('ix_customer_feedback_sentiment', 'customer_feedback', ['sentiment'])
    op.create_index('ix_customer_feedback_priority', 'customer_feedback', ['priority'])
    op.create_index('ix_customer_feedback_status', 'customer_feedback', ['status'])
    op.create_index('ix_customer_feedback_assigned_to', 'customer_feedback', ['assigned_to'])
    op.create_index('ix_customer_feedback_created_at', 'customer_feedback', ['created_at'])
    op.create_index('ix_customer_feedback_client_status', 'customer_feedback', ['client_id', 'status'])
    op.create_index('ix_customer_feedback_sentiment_created', 'customer_feedback', ['sentiment', 'created_at'])
    op.create_index('ix_customer_feedback_priority_status', 'customer_feedback', ['priority', 'status'])

    # Create nps_responses table
    op.create_table(
        'nps_responses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('response_id', sa.String(50), nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('survey_id', sa.String(50), nullable=False),
        sa.Column('respondent_email', sa.String(255), nullable=False),
        sa.Column('respondent_name', sa.String(200), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('follow_up_question_1', sa.Text(), nullable=True),
        sa.Column('follow_up_answer_1', sa.Text(), nullable=True),
        sa.Column('follow_up_question_2', sa.Text(), nullable=True),
        sa.Column('follow_up_answer_2', sa.Text(), nullable=True),
        sa.Column('sentiment', sa.String(20), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('follow_up_required', sa.Boolean(), server_default='false'),
        sa.Column('contacted', sa.Boolean(), server_default='false'),
        sa.Column('survey_sent_at', sa.DateTime(), nullable=False),
        sa.Column('responded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('response_time_hours', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('response_id'),
        sa.ForeignKeyConstraint(['client_id'], ['customers.client_id'], ondelete='CASCADE'),
        sa.CheckConstraint('score >= 0 AND score <= 10', name='check_nps_score_range'),
        sa.CheckConstraint('sentiment_score >= -1 AND sentiment_score <= 1', name='check_nps_sentiment_range')
    )
    op.create_index('ix_nps_responses_response_id', 'nps_responses', ['response_id'])
    op.create_index('ix_nps_responses_client_id', 'nps_responses', ['client_id'])
    op.create_index('ix_nps_responses_survey_id', 'nps_responses', ['survey_id'])
    op.create_index('ix_nps_responses_category', 'nps_responses', ['category'])
    op.create_index('ix_nps_responses_responded_at', 'nps_responses', ['responded_at'])
    op.create_index('ix_nps_responses_client_score', 'nps_responses', ['client_id', 'score'])
    op.create_index('ix_nps_responses_survey_category', 'nps_responses', ['survey_id', 'category'])

    # Create sentiment_analysis table
    op.create_table(
        'sentiment_analysis',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('analysis_id', sa.String(100), nullable=False),
        sa.Column('client_id', sa.String(100), nullable=True),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('total_feedback_items', sa.Integer(), nullable=False),
        sa.Column('feedback_by_type', sa.JSON(), nullable=False),
        sa.Column('overall_sentiment', sa.String(20), nullable=False),
        sa.Column('overall_sentiment_score', sa.Float(), nullable=False),
        sa.Column('sentiment_distribution', sa.JSON(), nullable=False),
        sa.Column('sentiment_trend', sa.String(20), nullable=False),
        sa.Column('top_positive_themes', sa.JSON(), server_default='[]'),
        sa.Column('top_negative_themes', sa.JSON(), server_default='[]'),
        sa.Column('action_items', sa.JSON(), server_default='[]'),
        sa.Column('nps_score', sa.Integer(), nullable=True),
        sa.Column('csat_score', sa.Float(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('analysis_id')
    )
    op.create_index('ix_sentiment_analysis_analysis_id', 'sentiment_analysis', ['analysis_id'])
    op.create_index('ix_sentiment_analysis_client_id', 'sentiment_analysis', ['client_id'])
    op.create_index('ix_sentiment_analysis_period_start', 'sentiment_analysis', ['period_start'])
    op.create_index('ix_sentiment_analysis_client_period', 'sentiment_analysis', ['client_id', 'period_start'])

    # Create survey_templates table
    op.create_table(
        'survey_templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('template_id', sa.String(100), nullable=False),
        sa.Column('template_name', sa.String(200), nullable=False),
        sa.Column('template_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('questions', sa.JSON(), nullable=False),
        sa.Column('targeting', sa.JSON(), server_default='{}'),
        sa.Column('frequency', sa.String(50), server_default='one_time'),
        sa.Column('active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('template_id')
    )
    op.create_index('ix_survey_templates_template_id', 'survey_templates', ['template_id'])
    op.create_index('ix_survey_templates_template_type', 'survey_templates', ['template_type'])
    op.create_index('ix_survey_templates_active', 'survey_templates', ['active'])

    # ========================================================================
    # ANALYTICS TABLES
    # ========================================================================

    # Create health_metrics table
    op.create_table(
        'health_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('overall_health_score', sa.Integer(), nullable=False),
        sa.Column('health_score_trend', sa.String(10), nullable=False),
        sa.Column('health_score_change', sa.Integer(), nullable=False),
        sa.Column('health_components', sa.JSON(), nullable=False),
        sa.Column('component_trends', sa.JSON(), nullable=False),
        sa.Column('risk_indicators', sa.JSON(), server_default='[]'),
        sa.Column('positive_indicators', sa.JSON(), server_default='[]'),
        sa.Column('benchmark_comparison', sa.JSON(), server_default='{}'),
        sa.Column('predicted_next_period_score', sa.Integer(), nullable=True),
        sa.Column('confidence', sa.Float(), server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_health_metrics_client_id', 'health_metrics', ['client_id'])
    op.create_index('ix_health_metrics_period_start', 'health_metrics', ['period_start'])
    op.create_index('ix_health_metrics_client_period', 'health_metrics', ['client_id', 'period_start'])

    # Create engagement_metrics table
    op.create_table(
        'engagement_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('total_users', sa.Integer(), nullable=False),
        sa.Column('active_users', sa.Integer(), nullable=False),
        sa.Column('daily_active_users', sa.Integer(), nullable=False),
        sa.Column('weekly_active_users', sa.Integer(), nullable=False),
        sa.Column('monthly_active_users', sa.Integer(), nullable=False),
        sa.Column('activation_rate', sa.Float(), nullable=False),
        sa.Column('engagement_rate', sa.Float(), nullable=False),
        sa.Column('total_logins', sa.Integer(), nullable=False),
        sa.Column('avg_logins_per_user', sa.Float(), nullable=False),
        sa.Column('total_session_minutes', sa.Integer(), nullable=False),
        sa.Column('avg_session_duration_minutes', sa.Float(), nullable=False),
        sa.Column('total_actions', sa.Integer(), nullable=False),
        sa.Column('avg_actions_per_session', sa.Float(), nullable=False),
        sa.Column('feature_adoption', sa.JSON(), nullable=False),
        sa.Column('power_users', sa.Integer(), server_default='0'),
        sa.Column('inactive_users', sa.Integer(), server_default='0'),
        sa.Column('at_risk_users', sa.Integer(), server_default='0'),
        sa.Column('engagement_trend', sa.String(10), nullable=False),
        sa.Column('vs_previous_period', sa.JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_engagement_metrics_client_id', 'engagement_metrics', ['client_id'])
    op.create_index('ix_engagement_metrics_period_start', 'engagement_metrics', ['period_start'])
    op.create_index('ix_engagement_metrics_client_period', 'engagement_metrics', ['client_id', 'period_start'])

    # Create usage_analytics table
    op.create_table(
        'usage_analytics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('client_id', sa.String(100), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('total_usage_events', sa.Integer(), nullable=False),
        sa.Column('unique_features_used', sa.Integer(), nullable=False),
        sa.Column('total_features_available', sa.Integer(), nullable=False),
        sa.Column('feature_utilization_rate', sa.Float(), nullable=False),
        sa.Column('top_features', sa.JSON(), nullable=False),
        sa.Column('underutilized_features', sa.JSON(), server_default='[]'),
        sa.Column('new_feature_adoption', sa.JSON(), server_default='{}'),
        sa.Column('usage_by_user_role', sa.JSON(), server_default='{}'),
        sa.Column('integration_usage', sa.JSON(), server_default='{}'),
        sa.Column('api_usage', sa.JSON(), server_default='{}'),
        sa.Column('usage_trend', sa.String(10), nullable=False),
        sa.Column('usage_growth_rate', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_usage_analytics_client_id', 'usage_analytics', ['client_id'])
    op.create_index('ix_usage_analytics_period_start', 'usage_analytics', ['period_start'])
    op.create_index('ix_usage_analytics_client_period', 'usage_analytics', ['client_id', 'period_start'])

    # Create cohort_analysis table
    op.create_table(
        'cohort_analysis',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cohort_id', sa.String(100), nullable=False),
        sa.Column('cohort_name', sa.String(200), nullable=False),
        sa.Column('cohort_definition', sa.JSON(), nullable=False),
        sa.Column('cohort_size', sa.Integer(), nullable=False),
        sa.Column('analysis_date', sa.Date(), nullable=False),
        sa.Column('months_since_cohort', sa.Integer(), nullable=False),
        sa.Column('retention_by_month', sa.JSON(), nullable=False),
        sa.Column('engagement_by_month', sa.JSON(), nullable=False),
        sa.Column('revenue_metrics', sa.JSON(), nullable=False),
        sa.Column('benchmark_comparison', sa.JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cohort_id')
    )
    op.create_index('ix_cohort_analysis_cohort_id', 'cohort_analysis', ['cohort_id'])
    op.create_index('ix_cohort_analysis_analysis_date', 'cohort_analysis', ['analysis_date'])


def downgrade() -> None:
    """Downgrade schema - drop all tables."""

    # Analytics tables
    op.drop_table('cohort_analysis')
    op.drop_table('usage_analytics')
    op.drop_table('engagement_metrics')
    op.drop_table('health_metrics')

    # Feedback tables
    op.drop_table('survey_templates')
    op.drop_table('sentiment_analysis')
    op.drop_table('nps_responses')
    op.drop_table('customer_feedback')

    # Renewal tables
    op.drop_table('renewal_campaigns')
    op.drop_table('expansion_opportunities')
    op.drop_table('contracts')
    op.drop_table('renewal_forecasts')

    # Support tables
    op.drop_table('knowledge_base_articles')
    op.drop_table('ticket_comments')
    op.drop_table('support_tickets')

    # Onboarding tables
    op.drop_table('training_completions')
    op.drop_table('training_modules')
    op.drop_table('onboarding_milestones')
    op.drop_table('onboarding_plans')

    # Customer tables
    op.drop_table('churn_predictions')
    op.drop_table('risk_indicators')
    op.drop_table('customer_segments')
    op.drop_table('health_scores')
    op.drop_table('customers')
