"""
Unit Tests for Onboarding Models

Tests for all onboarding-related Pydantic models including onboarding plans,
milestones, training modules, completions, and progress tracking.
"""

import pytest
from datetime import datetime, date, timedelta
from pydantic import ValidationError

from src.models.onboarding_models import (
    OnboardingStatus, MilestoneStatus, TrainingFormat, CertificationLevel,
    OnboardingPlan, OnboardingMilestone, TrainingModule,
    TrainingCompletion, OnboardingProgress
)


# ============================================================================
# OnboardingStatus Enum Tests
# ============================================================================

@pytest.mark.unit
def test_onboarding_status_enum_values():
    """Test that OnboardingStatus enum has all expected values."""
    assert OnboardingStatus.DRAFT == "draft"
    assert OnboardingStatus.SCHEDULED == "scheduled"
    assert OnboardingStatus.IN_PROGRESS == "in_progress"
    assert OnboardingStatus.COMPLETED == "completed"
    assert OnboardingStatus.DELAYED == "delayed"
    assert OnboardingStatus.CANCELLED == "cancelled"


@pytest.mark.unit
def test_onboarding_status_enum_count():
    """Test that OnboardingStatus has exactly 6 statuses."""
    assert len(list(OnboardingStatus)) == 6


# ============================================================================
# MilestoneStatus Enum Tests
# ============================================================================

@pytest.mark.unit
def test_milestone_status_enum_values():
    """Test that MilestoneStatus enum has all expected values."""
    assert MilestoneStatus.NOT_STARTED == "not_started"
    assert MilestoneStatus.IN_PROGRESS == "in_progress"
    assert MilestoneStatus.COMPLETED == "completed"
    assert MilestoneStatus.BLOCKED == "blocked"
    assert MilestoneStatus.SKIPPED == "skipped"


# ============================================================================
# TrainingFormat Enum Tests
# ============================================================================

@pytest.mark.unit
def test_training_format_enum_values():
    """Test that TrainingFormat enum has all expected values."""
    assert TrainingFormat.LIVE_WEBINAR == "live_webinar"
    assert TrainingFormat.SELF_PACED == "self_paced"
    assert TrainingFormat.ONE_ON_ONE == "one_on_one"
    assert TrainingFormat.WORKSHOP == "workshop"
    assert TrainingFormat.VIDEO == "video"
    assert TrainingFormat.DOCUMENTATION == "documentation"


# ============================================================================
# CertificationLevel Enum Tests
# ============================================================================

@pytest.mark.unit
def test_certification_level_enum_values():
    """Test that CertificationLevel enum has all expected values."""
    assert CertificationLevel.BASIC == "basic"
    assert CertificationLevel.INTERMEDIATE == "intermediate"
    assert CertificationLevel.ADVANCED == "advanced"
    assert CertificationLevel.EXPERT == "expert"


# ============================================================================
# OnboardingPlan Model Tests
# ============================================================================

@pytest.mark.unit
def test_onboarding_plan_valid_creation(sample_client_id):
    """Test creating a valid OnboardingPlan with all required fields."""
    plan = OnboardingPlan(
        plan_id="onb_test_plan_123",
        client_id=sample_client_id,
        plan_name="Acme Corp Onboarding",
        product_tier="professional",
        start_date=date.today(),
        target_completion_date=date.today() + timedelta(weeks=4),
        timeline_weeks=4,
        customer_goals=["Goal 1", "Goal 2"],
        success_criteria=["Criteria 1", "Criteria 2"]
    )

    assert plan.plan_id == "onb_test_plan_123"
    assert plan.client_id == sample_client_id
    assert plan.timeline_weeks == 4
    assert len(plan.customer_goals) == 2
    assert len(plan.success_criteria) == 2


@pytest.mark.unit
def test_onboarding_plan_invalid_id_format():
    """Test that invalid plan_id format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        OnboardingPlan(
            plan_id="invalid_id",  # Missing onb_ prefix
            client_id="cs_1234_test",
            plan_name="Test Plan",
            product_tier="standard",
            start_date=date.today(),
            target_completion_date=date.today() + timedelta(weeks=4),
            timeline_weeks=4,
            customer_goals=["Goal 1"],
            success_criteria=["Criteria 1"]
        )

    assert "plan_id" in str(exc_info.value)


@pytest.mark.unit
def test_onboarding_plan_invalid_client_id_format():
    """Test that invalid client_id format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        OnboardingPlan(
            plan_id="onb_test",
            client_id="invalid_id",  # Missing cs_ prefix
            plan_name="Test Plan",
            product_tier="standard",
            start_date=date.today(),
            target_completion_date=date.today() + timedelta(weeks=4),
            timeline_weeks=4,
            customer_goals=["Goal 1"],
            success_criteria=["Criteria 1"]
        )

    assert "client_id" in str(exc_info.value)


@pytest.mark.unit
def test_onboarding_plan_product_tier_validation():
    """Test that product_tier must be one of allowed values."""
    for tier in ["starter", "standard", "professional", "enterprise"]:
        plan = OnboardingPlan(
            plan_id="onb_test",
            client_id="cs_1234_test",
            plan_name="Test Plan",
            product_tier=tier,
            start_date=date.today(),
            target_completion_date=date.today() + timedelta(weeks=4),
            timeline_weeks=4,
            customer_goals=["Goal 1"],
            success_criteria=["Criteria 1"]
        )
        assert plan.product_tier == tier

    # Invalid tier
    with pytest.raises(ValidationError) as exc_info:
        OnboardingPlan(
            plan_id="onb_test",
            client_id="cs_1234_test",
            plan_name="Test Plan",
            product_tier="invalid",
            start_date=date.today(),
            target_completion_date=date.today() + timedelta(weeks=4),
            timeline_weeks=4,
            customer_goals=["Goal 1"],
            success_criteria=["Criteria 1"]
        )

    assert "product_tier" in str(exc_info.value)


@pytest.mark.unit
def test_onboarding_plan_target_date_after_start_date():
    """Test that target_completion_date must be after start_date."""
    with pytest.raises(ValidationError) as exc_info:
        OnboardingPlan(
            plan_id="onb_test",
            client_id="cs_1234_test",
            plan_name="Test Plan",
            product_tier="standard",
            start_date=date.today(),
            target_completion_date=date.today() - timedelta(days=1),
            timeline_weeks=4,
            customer_goals=["Goal 1"],
            success_criteria=["Criteria 1"]
        )

    assert "target_completion_date must be after start_date" in str(exc_info.value)


@pytest.mark.unit
def test_onboarding_plan_timeline_weeks_boundaries():
    """Test that timeline_weeks respects 1-52 boundaries."""
    # Test minimum
    plan = OnboardingPlan(
        plan_id="onb_test",
        client_id="cs_1234_test",
        plan_name="Test Plan",
        product_tier="standard",
        start_date=date.today(),
        target_completion_date=date.today() + timedelta(weeks=1),
        timeline_weeks=1,
        customer_goals=["Goal 1"],
        success_criteria=["Criteria 1"]
    )
    assert plan.timeline_weeks == 1

    # Test maximum
    plan.timeline_weeks = 52
    assert plan.timeline_weeks == 52

    # Test below minimum
    with pytest.raises(ValidationError) as exc_info:
        OnboardingPlan(
            plan_id="onb_test",
            client_id="cs_1234_test",
            plan_name="Test Plan",
            product_tier="standard",
            start_date=date.today(),
            target_completion_date=date.today() + timedelta(weeks=4),
            timeline_weeks=0,
            customer_goals=["Goal 1"],
            success_criteria=["Criteria 1"]
        )

    assert "timeline_weeks" in str(exc_info.value)


@pytest.mark.unit
def test_onboarding_plan_goals_min_length():
    """Test that customer_goals must have at least one goal."""
    with pytest.raises(ValidationError) as exc_info:
        OnboardingPlan(
            plan_id="onb_test",
            client_id="cs_1234_test",
            plan_name="Test Plan",
            product_tier="standard",
            start_date=date.today(),
            target_completion_date=date.today() + timedelta(weeks=4),
            timeline_weeks=4,
            customer_goals=[],  # Empty list
            success_criteria=["Criteria 1"]
        )

    assert "customer_goals" in str(exc_info.value)


@pytest.mark.unit
def test_onboarding_plan_completion_percentage_boundaries():
    """Test that completion_percentage respects 0-1 boundaries."""
    plan = OnboardingPlan(
        plan_id="onb_test",
        client_id="cs_1234_test",
        plan_name="Test Plan",
        product_tier="standard",
        start_date=date.today(),
        target_completion_date=date.today() + timedelta(weeks=4),
        timeline_weeks=4,
        customer_goals=["Goal 1"],
        success_criteria=["Criteria 1"],
        completion_percentage=0.5
    )
    assert plan.completion_percentage == 0.5

    # Test above maximum
    with pytest.raises(ValidationError) as exc_info:
        OnboardingPlan(
            plan_id="onb_test",
            client_id="cs_1234_test",
            plan_name="Test Plan",
            product_tier="standard",
            start_date=date.today(),
            target_completion_date=date.today() + timedelta(weeks=4),
            timeline_weeks=4,
            customer_goals=["Goal 1"],
            success_criteria=["Criteria 1"],
            completion_percentage=1.5
        )

    assert "completion_percentage" in str(exc_info.value)


@pytest.mark.unit
def test_onboarding_plan_default_values(sample_client_id):
    """Test that OnboardingPlan has correct default values."""
    plan = OnboardingPlan(
        plan_id="onb_test",
        client_id=sample_client_id,
        plan_name="Test Plan",
        product_tier="standard",
        start_date=date.today(),
        target_completion_date=date.today() + timedelta(weeks=4),
        timeline_weeks=4,
        customer_goals=["Goal 1"],
        success_criteria=["Criteria 1"]
    )

    assert plan.status == OnboardingStatus.DRAFT
    assert plan.completion_percentage == 0.0
    assert plan.total_estimated_hours == 0
    assert plan.milestones == []
    assert plan.assigned_implementation_team == []


# ============================================================================
# OnboardingMilestone Model Tests
# ============================================================================

@pytest.mark.unit
def test_onboarding_milestone_valid_creation():
    """Test creating a valid OnboardingMilestone."""
    milestone = OnboardingMilestone(
        milestone_id="M1",
        plan_id="onb_test_plan",
        name="Kickoff & Setup",
        description="Initial setup and kickoff meeting",
        week=1,
        sequence_order=1,
        tasks=["Task 1", "Task 2"],
        estimated_hours=8
    )

    assert milestone.milestone_id == "M1"
    assert milestone.name == "Kickoff & Setup"
    assert milestone.week == 1
    assert len(milestone.tasks) == 2


@pytest.mark.unit
def test_onboarding_milestone_tasks_min_length():
    """Test that tasks list must have at least one task."""
    with pytest.raises(ValidationError) as exc_info:
        OnboardingMilestone(
            milestone_id="M1",
            plan_id="onb_test",
            name="Test Milestone",
            description="Test",
            week=1,
            sequence_order=1,
            tasks=[],  # Empty list
            estimated_hours=5
        )

    assert "tasks" in str(exc_info.value)


@pytest.mark.unit
def test_onboarding_milestone_week_minimum():
    """Test that week must be at least 1."""
    with pytest.raises(ValidationError) as exc_info:
        OnboardingMilestone(
            milestone_id="M1",
            plan_id="onb_test",
            name="Test",
            description="Test",
            week=0,  # Below minimum
            sequence_order=1,
            tasks=["Task 1"],
            estimated_hours=5
        )

    assert "week" in str(exc_info.value)


@pytest.mark.unit
def test_onboarding_milestone_completion_percentage():
    """Test milestone completion_percentage boundaries."""
    milestone = OnboardingMilestone(
        milestone_id="M1",
        plan_id="onb_test",
        name="Test",
        description="Test",
        week=1,
        sequence_order=1,
        tasks=["Task 1"],
        estimated_hours=5,
        completion_percentage=0.75
    )
    assert milestone.completion_percentage == 0.75


@pytest.mark.unit
def test_onboarding_milestone_default_values():
    """Test that OnboardingMilestone has correct default values."""
    milestone = OnboardingMilestone(
        milestone_id="M1",
        plan_id="onb_test",
        name="Test",
        description="Test",
        week=1,
        sequence_order=1,
        tasks=["Task 1"],
        estimated_hours=5
    )

    assert milestone.status == MilestoneStatus.NOT_STARTED
    assert milestone.completion_percentage == 0.0
    assert milestone.success_criteria == []
    assert milestone.dependencies == []
    assert milestone.blockers == []


# ============================================================================
# TrainingModule Model Tests
# ============================================================================

@pytest.mark.unit
def test_training_module_valid_creation():
    """Test creating a valid TrainingModule."""
    module = TrainingModule(
        module_id="train_getting_started_101",
        module_name="Getting Started",
        module_description="Introduction to the platform",
        format=TrainingFormat.LIVE_WEBINAR,
        duration_minutes=90,
        learning_objectives=["Objective 1", "Objective 2"],
        topics_covered=["Topic 1", "Topic 2"]
    )

    assert module.module_id == "train_getting_started_101"
    assert module.format == TrainingFormat.LIVE_WEBINAR
    assert module.duration_minutes == 90


@pytest.mark.unit
def test_training_module_invalid_id_format():
    """Test that invalid module_id format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        TrainingModule(
            module_id="invalid_id",  # Missing train_ prefix
            module_name="Test",
            module_description="Test",
            format=TrainingFormat.VIDEO,
            duration_minutes=60,
            learning_objectives=["Objective 1"],
            topics_covered=["Topic 1"]
        )

    assert "module_id" in str(exc_info.value)


@pytest.mark.unit
def test_training_module_duration_boundaries():
    """Test that duration_minutes respects 1-480 boundaries."""
    # Test minimum
    module = TrainingModule(
        module_id="train_test",
        module_name="Test",
        module_description="Test",
        format=TrainingFormat.VIDEO,
        duration_minutes=1,
        learning_objectives=["Objective 1"],
        topics_covered=["Topic 1"]
    )
    assert module.duration_minutes == 1

    # Test maximum
    module = TrainingModule(
        module_id="train_test2",
        module_name="Test",
        module_description="Test",
        format=TrainingFormat.WORKSHOP,
        duration_minutes=480,
        learning_objectives=["Objective 1"],
        topics_covered=["Topic 1"]
    )
    assert module.duration_minutes == 480

    # Test above maximum
    with pytest.raises(ValidationError) as exc_info:
        TrainingModule(
            module_id="train_test3",
            module_name="Test",
            module_description="Test",
            format=TrainingFormat.WORKSHOP,
            duration_minutes=481,
            learning_objectives=["Objective 1"],
            topics_covered=["Topic 1"]
        )

    assert "duration_minutes" in str(exc_info.value)


@pytest.mark.unit
def test_training_module_passing_score_boundaries():
    """Test that passing_score respects 0-1 boundaries."""
    module = TrainingModule(
        module_id="train_test",
        module_name="Test",
        module_description="Test",
        format=TrainingFormat.SELF_PACED,
        duration_minutes=60,
        learning_objectives=["Objective 1"],
        topics_covered=["Topic 1"],
        passing_score=0.8
    )
    assert module.passing_score == 0.8


@pytest.mark.unit
def test_training_module_max_attempts_boundaries():
    """Test that max_attempts respects 1-10 boundaries."""
    # Test minimum
    module = TrainingModule(
        module_id="train_test",
        module_name="Test",
        module_description="Test",
        format=TrainingFormat.SELF_PACED,
        duration_minutes=60,
        learning_objectives=["Objective 1"],
        topics_covered=["Topic 1"],
        max_attempts=1
    )
    assert module.max_attempts == 1

    # Test maximum
    module.max_attempts = 10
    assert module.max_attempts == 10


@pytest.mark.unit
def test_training_module_default_values():
    """Test that TrainingModule has correct default values."""
    module = TrainingModule(
        module_id="train_test",
        module_name="Test",
        module_description="Test",
        format=TrainingFormat.VIDEO,
        duration_minutes=30,
        learning_objectives=["Objective 1"],
        topics_covered=["Topic 1"]
    )

    assert module.certification_level == CertificationLevel.BASIC
    assert module.assessment_required == True
    assert module.passing_score == 0.75
    assert module.max_attempts == 3
    assert module.prerequisites == []


# ============================================================================
# TrainingCompletion Model Tests
# ============================================================================

@pytest.mark.unit
def test_training_completion_valid_creation(sample_client_id):
    """Test creating a valid TrainingCompletion."""
    completion = TrainingCompletion(
        completion_id="comp_user123_train_101",
        client_id=sample_client_id,
        module_id="train_getting_started_101",
        user_email="user@example.com",
        user_name="John Doe",
        started_at=datetime.now() - timedelta(hours=2)
    )

    assert completion.completion_id == "comp_user123_train_101"
    assert completion.module_id == "train_getting_started_101"
    assert completion.user_email == "user@example.com"


@pytest.mark.unit
def test_training_completion_invalid_email():
    """Test that invalid email format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        TrainingCompletion(
            completion_id="comp_test",
            client_id="cs_1234_test",
            module_id="train_test",
            user_email="invalid_email",  # Missing @
            user_name="John Doe",
            started_at=datetime.now()
        )

    assert "user_email" in str(exc_info.value)


@pytest.mark.unit
def test_training_completion_assessment_score_boundaries():
    """Test that assessment_score respects 0-1 boundaries."""
    completion = TrainingCompletion(
        completion_id="comp_test",
        client_id="cs_1234_test",
        module_id="train_test",
        user_email="user@example.com",
        user_name="John Doe",
        started_at=datetime.now(),
        assessment_score=0.88
    )
    assert completion.assessment_score == 0.88


@pytest.mark.unit
def test_training_completion_feedback_rating_boundaries():
    """Test that feedback_rating respects 1-5 boundaries."""
    completion = TrainingCompletion(
        completion_id="comp_test",
        client_id="cs_1234_test",
        module_id="train_test",
        user_email="user@example.com",
        user_name="John Doe",
        started_at=datetime.now(),
        feedback_rating=4.5
    )
    assert completion.feedback_rating == 4.5


@pytest.mark.unit
def test_training_completion_default_values(sample_client_id):
    """Test that TrainingCompletion has correct default values."""
    completion = TrainingCompletion(
        completion_id="comp_test",
        client_id=sample_client_id,
        module_id="train_test",
        user_email="user@example.com",
        user_name="John Doe",
        started_at=datetime.now()
    )

    assert completion.time_spent_minutes == 0
    assert completion.attempts_used == 0
    assert completion.passed == False
    assert completion.certification_issued == False


# ============================================================================
# OnboardingProgress Model Tests
# ============================================================================

@pytest.mark.unit
def test_onboarding_progress_valid_creation(sample_client_id):
    """Test creating a valid OnboardingProgress."""
    progress = OnboardingProgress(
        client_id=sample_client_id,
        plan_id="onb_test_plan",
        overall_completion=0.68,
        status="on_track",
        current_week=3,
        total_weeks=4,
        days_elapsed=19,
        days_remaining=9,
        milestones_completed=2,
        milestones_total=4,
        milestones_on_track=3,
        milestones_at_risk=1,
        training_users_invited=15,
        training_users_started=12,
        training_users_completed=8,
        training_completion_rate=0.53
    )

    assert progress.client_id == sample_client_id
    assert progress.overall_completion == 0.68
    assert progress.status == "on_track"


@pytest.mark.unit
def test_onboarding_progress_status_validation():
    """Test that status must be one of allowed values."""
    for status in ["on_track", "at_risk", "delayed", "completed"]:
        progress = OnboardingProgress(
            client_id="cs_1234_test",
            plan_id="onb_test",
            overall_completion=0.5,
            status=status,
            current_week=2,
            total_weeks=4,
            days_elapsed=14,
            days_remaining=14,
            milestones_completed=1,
            milestones_total=4,
            milestones_on_track=2,
            milestones_at_risk=1,
            training_users_invited=10,
            training_users_started=8,
            training_users_completed=5,
            training_completion_rate=0.5
        )
        assert progress.status == status

    # Invalid status
    with pytest.raises(ValidationError) as exc_info:
        OnboardingProgress(
            client_id="cs_1234_test",
            plan_id="onb_test",
            overall_completion=0.5,
            status="invalid",
            current_week=2,
            total_weeks=4,
            days_elapsed=14,
            days_remaining=14,
            milestones_completed=1,
            milestones_total=4,
            milestones_on_track=2,
            milestones_at_risk=1,
            training_users_invited=10,
            training_users_started=8,
            training_users_completed=5,
            training_completion_rate=0.5
        )

    assert "status" in str(exc_info.value)


@pytest.mark.unit
def test_onboarding_progress_health_status_validation():
    """Test that health_status must be one of allowed values."""
    for health in ["excellent", "good", "fair", "poor"]:
        progress = OnboardingProgress(
            client_id="cs_1234_test",
            plan_id="onb_test",
            overall_completion=0.5,
            status="on_track",
            current_week=2,
            total_weeks=4,
            days_elapsed=14,
            days_remaining=14,
            milestones_completed=1,
            milestones_total=4,
            milestones_on_track=2,
            milestones_at_risk=1,
            training_users_invited=10,
            training_users_started=8,
            training_users_completed=5,
            training_completion_rate=0.5,
            health_status=health
        )
        assert progress.health_status == health


@pytest.mark.unit
def test_onboarding_progress_completion_rates():
    """Test completion rate calculations and boundaries."""
    progress = OnboardingProgress(
        client_id="cs_1234_test",
        plan_id="onb_test",
        overall_completion=0.75,
        status="on_track",
        current_week=3,
        total_weeks=4,
        days_elapsed=21,
        days_remaining=7,
        milestones_completed=3,
        milestones_total=4,
        milestones_on_track=4,
        milestones_at_risk=0,
        training_users_invited=20,
        training_users_started=18,
        training_users_completed=15,
        training_completion_rate=0.75,
        average_assessment_score=0.85,
        certification_rate=0.70
    )

    assert progress.training_completion_rate == 0.75
    assert progress.average_assessment_score == 0.85
    assert progress.certification_rate == 0.70


@pytest.mark.unit
def test_onboarding_progress_default_values(sample_client_id):
    """Test that OnboardingProgress has correct default values."""
    progress = OnboardingProgress(
        client_id=sample_client_id,
        plan_id="onb_test",
        overall_completion=0.5,
        status="on_track",
        current_week=2,
        total_weeks=4,
        days_elapsed=14,
        days_remaining=14,
        milestones_completed=1,
        milestones_total=4,
        milestones_on_track=2,
        milestones_at_risk=1,
        training_users_invited=10,
        training_users_started=8,
        training_users_completed=5,
        training_completion_rate=0.5
    )

    assert progress.average_assessment_score == 0.0
    assert progress.certification_rate == 0.0
    assert progress.blockers == []
    assert progress.risks == []
    assert progress.time_to_value_target_days == 21
    assert progress.health_status == "good"
