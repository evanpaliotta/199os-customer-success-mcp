"""
Onboarding Models
Pydantic models for customer onboarding and training processes
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from enum import Enum


class OnboardingStatus(str, Enum):
    """Onboarding plan status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class MilestoneStatus(str, Enum):
    """Individual milestone status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class TrainingFormat(str, Enum):
    """Training delivery format"""
    LIVE_WEBINAR = "live_webinar"
    SELF_PACED = "self_paced"
    ONE_ON_ONE = "one_on_one"
    WORKSHOP = "workshop"
    VIDEO = "video"
    DOCUMENTATION = "documentation"


class CertificationLevel(str, Enum):
    """Training certification levels"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class OnboardingPlan(BaseModel):
    """
    Comprehensive onboarding plan for a customer.

    Defines the complete onboarding journey with milestones,
    timelines, and success criteria.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "plan_id": "onb_cs_1696800000_acme_1728576000",
            "client_id": "cs_1696800000_acme",
            "plan_name": "Acme Corporation Onboarding",
            "product_tier": "professional",
            "start_date": "2025-10-15",
            "target_completion_date": "2025-11-12",
            "actual_completion_date": None,
            "timeline_weeks": 4,
            "customer_goals": [
                "Automate customer support workflows",
                "Integrate with existing CRM",
                "Train 15 users across 3 departments"
            ],
            "success_criteria": [
                "All users trained and certified",
                "Primary use case automated",
                "All critical integrations active",
                "Time-to-first-value < 21 days"
            ],
            "milestones": [],
            "total_estimated_hours": 46,
            "assigned_csm": "Sarah Johnson",
            "assigned_implementation_team": ["Mike Chen", "Lisa Wang"],
            "status": "in_progress",
            "completion_percentage": 0.68,
            "created_at": "2025-10-10T09:00:00Z",
            "updated_at": "2025-10-10T09:00:00Z"
        }
    })

    plan_id: str = Field(
        ...,
        description="Unique onboarding plan identifier",
        pattern=r"^onb_[a-z0-9_]+$"
    )
    client_id: str = Field(
        ...,
        description="Customer identifier",
        pattern=r"^cs_[0-9]+_[a-z0-9_]+$"
    )
    plan_name: str = Field(
        ...,
        description="Human-readable plan name",
        min_length=1,
        max_length=200
    )
    product_tier: str = Field(
        ...,
        description="Product tier (starter, standard, professional, enterprise)",
        pattern=r"^(starter|standard|professional|enterprise)$"
    )

    # Timeline
    start_date: date = Field(
        ...,
        description="Onboarding start date"
    )
    target_completion_date: date = Field(
        ...,
        description="Target completion date"
    )
    actual_completion_date: Optional[date] = Field(
        None,
        description="Actual completion date (when status = completed)"
    )
    timeline_weeks: int = Field(
        ...,
        description="Planned duration in weeks",
        ge=1,
        le=52
    )

    # Goals and criteria
    customer_goals: List[str] = Field(
        ...,
        description="Customer's stated success goals",
        min_length=1
    )
    success_criteria: List[str] = Field(
        ...,
        description="Measurable success criteria for completion",
        min_length=1
    )

    # Milestones
    milestones: List["OnboardingMilestone"] = Field(
        default_factory=list,
        description="Ordered list of onboarding milestones"
    )

    # Team and resources
    total_estimated_hours: int = Field(
        default=0,
        description="Total estimated hours for all milestones",
        ge=0
    )
    assigned_csm: Optional[str] = Field(
        None,
        description="Assigned Customer Success Manager"
    )
    assigned_implementation_team: List[str] = Field(
        default_factory=list,
        description="Implementation team members"
    )

    # Status tracking
    status: OnboardingStatus = Field(
        default=OnboardingStatus.DRAFT,
        description="Current onboarding status"
    )
    completion_percentage: float = Field(
        default=0.0,
        description="Overall completion percentage (0-1)",
        ge=0,
        le=1
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Plan creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )

    @field_validator('target_completion_date')
    @classmethod
    def validate_target_date(cls, v: date, info) -> date:
        """Validate target completion date is after start date"""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('target_completion_date must be after start_date')
        return v


class OnboardingMilestone(BaseModel):
    """
    Individual milestone within an onboarding plan.

    Represents a key achievement or phase in the onboarding journey.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "milestone_id": "M1",
            "plan_id": "onb_cs_1696800000_acme_1728576000",
            "name": "Kickoff & Setup",
            "description": "Complete initial setup and kickoff meeting",
            "week": 1,
            "sequence_order": 1,
            "tasks": [
                "Kickoff call with CSM and implementation team",
                "Product access provisioning",
                "Initial configuration and settings",
                "Integration planning session"
            ],
            "success_criteria": [
                "All users have access",
                "Admin settings configured",
                "Integration roadmap created"
            ],
            "dependencies": [],
            "estimated_hours": 8,
            "actual_hours": None,
            "assigned_to": "Sarah Johnson",
            "due_date": "2025-10-22",
            "completion_date": None,
            "status": "in_progress",
            "completion_percentage": 0.75,
            "blockers": []
        }
    })

    milestone_id: str = Field(
        ...,
        description="Unique milestone identifier within plan"
    )
    plan_id: str = Field(
        ...,
        description="Parent onboarding plan ID"
    )
    name: str = Field(
        ...,
        description="Milestone name",
        min_length=1,
        max_length=200
    )
    description: str = Field(
        ...,
        description="Detailed milestone description"
    )
    week: int = Field(
        ...,
        description="Week number in onboarding timeline",
        ge=1
    )
    sequence_order: int = Field(
        ...,
        description="Sequence order for milestone execution",
        ge=1
    )

    # Tasks and criteria
    tasks: List[str] = Field(
        ...,
        description="List of tasks to complete for this milestone",
        min_length=1
    )
    success_criteria: List[str] = Field(
        default_factory=list,
        description="Success criteria for milestone completion"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="IDs of milestones that must complete first"
    )

    # Time tracking
    estimated_hours: int = Field(
        ...,
        description="Estimated hours to complete",
        ge=0
    )
    actual_hours: Optional[int] = Field(
        None,
        description="Actual hours spent (when completed)",
        ge=0
    )
    assigned_to: Optional[str] = Field(
        None,
        description="Team member assigned to this milestone"
    )
    due_date: Optional[date] = Field(
        None,
        description="Milestone due date"
    )
    completion_date: Optional[date] = Field(
        None,
        description="Actual completion date"
    )

    # Status
    status: MilestoneStatus = Field(
        default=MilestoneStatus.NOT_STARTED,
        description="Current milestone status"
    )
    completion_percentage: float = Field(
        default=0.0,
        description="Completion percentage (0-1)",
        ge=0,
        le=1
    )
    blockers: List[str] = Field(
        default_factory=list,
        description="Current blockers preventing progress"
    )


class TrainingModule(BaseModel):
    """
    Training module for customer education.

    Represents a discrete training unit with content,
    assessments, and completion tracking.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "module_id": "train_getting_started_101",
            "module_name": "Getting Started with Platform",
            "module_description": "Introduction to core platform features and navigation",
            "format": "live_webinar",
            "certification_level": "basic",
            "duration_minutes": 90,
            "content_url": "https://training.example.com/modules/getting-started",
            "prerequisites": [],
            "learning_objectives": [
                "Navigate the platform interface",
                "Create and manage basic workflows",
                "Understand key terminology",
                "Access help resources"
            ],
            "topics_covered": [
                "Platform overview",
                "User interface navigation",
                "Basic workflow creation",
                "Help and support resources"
            ],
            "assessment_required": True,
            "passing_score": 0.75,
            "certification_awarded": "Platform Fundamentals",
            "max_attempts": 3,
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-10-01T14:30:00Z"
        }
    })

    module_id: str = Field(
        ...,
        description="Unique training module identifier",
        pattern=r"^train_[a-z0-9_]+$"
    )
    module_name: str = Field(
        ...,
        description="Module name",
        min_length=1,
        max_length=200
    )
    module_description: str = Field(
        ...,
        description="Detailed module description"
    )
    format: TrainingFormat = Field(
        ...,
        description="Training delivery format"
    )
    certification_level: CertificationLevel = Field(
        default=CertificationLevel.BASIC,
        description="Certification level awarded"
    )

    # Content
    duration_minutes: int = Field(
        ...,
        description="Expected duration in minutes",
        ge=1,
        le=480
    )
    content_url: Optional[str] = Field(
        None,
        description="URL to training content"
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Module IDs that must be completed first"
    )
    learning_objectives: List[str] = Field(
        ...,
        description="Learning objectives for this module",
        min_length=1
    )
    topics_covered: List[str] = Field(
        ...,
        description="Topics covered in this module",
        min_length=1
    )

    # Assessment
    assessment_required: bool = Field(
        default=True,
        description="Whether assessment is required for completion"
    )
    passing_score: float = Field(
        default=0.75,
        description="Minimum score required to pass (0-1)",
        ge=0,
        le=1
    )
    certification_awarded: Optional[str] = Field(
        None,
        description="Certification name if awarded upon completion"
    )
    max_attempts: int = Field(
        default=3,
        description="Maximum assessment attempts allowed",
        ge=1,
        le=10
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Module creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )


class TrainingCompletion(BaseModel):
    """
    Training completion record for a user.

    Tracks individual user progress through training modules.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "completion_id": "comp_user123_train_getting_started_101",
            "client_id": "cs_1696800000_acme",
            "module_id": "train_getting_started_101",
            "user_email": "john.smith@acme.com",
            "user_name": "John Smith",
            "started_at": "2025-10-15T10:00:00Z",
            "completed_at": "2025-10-15T11:45:00Z",
            "time_spent_minutes": 105,
            "assessment_score": 0.88,
            "attempts_used": 1,
            "passed": True,
            "certification_issued": True,
            "certification_id": "cert_12345",
            "feedback_rating": 4.5,
            "feedback_comments": "Very helpful introduction to the platform"
        }
    })

    completion_id: str = Field(
        ...,
        description="Unique completion record identifier"
    )
    client_id: str = Field(
        ...,
        description="Customer identifier"
    )
    module_id: str = Field(
        ...,
        description="Training module identifier"
    )
    user_email: str = Field(
        ...,
        description="User email address",
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    user_name: str = Field(
        ...,
        description="User full name"
    )

    # Timing
    started_at: datetime = Field(
        ...,
        description="When user started the module"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="When user completed the module"
    )
    time_spent_minutes: int = Field(
        default=0,
        description="Total time spent in minutes",
        ge=0
    )

    # Assessment results
    assessment_score: Optional[float] = Field(
        None,
        description="Assessment score (0-1)",
        ge=0,
        le=1
    )
    attempts_used: int = Field(
        default=0,
        description="Number of assessment attempts used",
        ge=0
    )
    passed: bool = Field(
        default=False,
        description="Whether user passed the assessment"
    )

    # Certification
    certification_issued: bool = Field(
        default=False,
        description="Whether certification was issued"
    )
    certification_id: Optional[str] = Field(
        None,
        description="Issued certification identifier"
    )

    # Feedback
    feedback_rating: Optional[float] = Field(
        None,
        description="User rating of the training (1-5)",
        ge=1,
        le=5
    )
    feedback_comments: Optional[str] = Field(
        None,
        description="User feedback comments"
    )


class OnboardingProgress(BaseModel):
    """
    Aggregated onboarding progress report for a customer.

    Provides high-level view of onboarding status and metrics.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "client_id": "cs_1696800000_acme",
            "plan_id": "onb_cs_1696800000_acme_1728576000",
            "overall_completion": 0.68,
            "status": "on_track",
            "current_week": 3,
            "total_weeks": 4,
            "days_elapsed": 19,
            "days_remaining": 9,
            "milestones_completed": 2,
            "milestones_total": 4,
            "milestones_on_track": 3,
            "milestones_at_risk": 1,
            "training_users_invited": 15,
            "training_users_started": 12,
            "training_users_completed": 8,
            "training_completion_rate": 0.53,
            "average_assessment_score": 0.84,
            "certification_rate": 0.67,
            "blockers": ["Data migration pending approval"],
            "risks": ["Training completion below target"],
            "time_to_value_days": 19,
            "time_to_value_target_days": 21,
            "health_status": "good",
            "last_updated": "2025-10-10T09:00:00Z"
        }
    })

    client_id: str = Field(..., description="Customer identifier")
    plan_id: str = Field(..., description="Onboarding plan identifier")

    # Overall progress
    overall_completion: float = Field(
        ...,
        description="Overall completion percentage (0-1)",
        ge=0,
        le=1
    )
    status: str = Field(
        ...,
        description="Progress status (on_track, at_risk, delayed, completed)",
        pattern=r"^(on_track|at_risk|delayed|completed)$"
    )

    # Timeline metrics
    current_week: int = Field(..., description="Current week in timeline", ge=0)
    total_weeks: int = Field(..., description="Total planned weeks", ge=1)
    days_elapsed: int = Field(..., description="Days since start", ge=0)
    days_remaining: int = Field(..., description="Days until target completion", ge=0)

    # Milestone metrics
    milestones_completed: int = Field(..., description="Completed milestones", ge=0)
    milestones_total: int = Field(..., description="Total milestones", ge=1)
    milestones_on_track: int = Field(..., description="Milestones on track", ge=0)
    milestones_at_risk: int = Field(..., description="Milestones at risk", ge=0)

    # Training metrics
    training_users_invited: int = Field(..., description="Users invited to training", ge=0)
    training_users_started: int = Field(..., description="Users who started training", ge=0)
    training_users_completed: int = Field(..., description="Users who completed training", ge=0)
    training_completion_rate: float = Field(
        ...,
        description="Training completion rate (0-1)",
        ge=0,
        le=1
    )
    average_assessment_score: float = Field(
        default=0.0,
        description="Average assessment score across users (0-1)",
        ge=0,
        le=1
    )
    certification_rate: float = Field(
        default=0.0,
        description="Percentage of users certified (0-1)",
        ge=0,
        le=1
    )

    # Issues and risks
    blockers: List[str] = Field(
        default_factory=list,
        description="Current blockers preventing progress"
    )
    risks: List[str] = Field(
        default_factory=list,
        description="Identified risks to completion"
    )

    # Time to value
    time_to_value_days: Optional[int] = Field(
        None,
        description="Actual days to first value (if achieved)",
        ge=0
    )
    time_to_value_target_days: int = Field(
        default=21,
        description="Target days to first value",
        ge=1
    )

    # Health indicators
    health_status: str = Field(
        default="good",
        description="Overall onboarding health (excellent, good, fair, poor)",
        pattern=r"^(excellent|good|fair|poor)$"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="Last progress update timestamp"
    )


__all__ = [
    'OnboardingStatus',
    'MilestoneStatus',
    'TrainingFormat',
    'CertificationLevel',
    'OnboardingPlan',
    'OnboardingMilestone',
    'TrainingModule',
    'TrainingCompletion',
    'OnboardingProgress'
]
