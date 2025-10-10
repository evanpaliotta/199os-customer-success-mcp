"""
Support Models
Pydantic models for customer support and knowledge base processes
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum


class TicketPriority(str, Enum):
    """Support ticket priority levels"""
    P0_CRITICAL = "P0"  # System down, business-critical
    P1_HIGH = "P1"      # Major functionality impaired
    P2_MEDIUM = "P2"    # Important but not critical
    P3_NORMAL = "P3"    # Normal priority
    P4_LOW = "P4"       # Low priority, enhancement


class TicketStatus(str, Enum):
    """Support ticket status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_ON_CUSTOMER = "waiting_on_customer"
    WAITING_ON_ENGINEERING = "waiting_on_engineering"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class TicketCategory(str, Enum):
    """Support ticket categories"""
    TECHNICAL_ISSUE = "technical_issue"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    HOW_TO_QUESTION = "how_to_question"
    ACCOUNT_BILLING = "account_billing"
    INTEGRATION_SUPPORT = "integration_support"
    TRAINING_REQUEST = "training_request"
    DATA_ISSUE = "data_issue"
    PERFORMANCE = "performance"
    OTHER = "other"


class SLAStatus(str, Enum):
    """SLA compliance status"""
    MET = "met"
    AT_RISK = "at_risk"
    BREACHED = "breached"
    NOT_APPLICABLE = "not_applicable"


class ArticleStatus(str, Enum):
    """Knowledge base article status"""
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SupportTicket(BaseModel):
    """
    Support ticket for customer issues and requests.

    Comprehensive ticket model with SLA tracking, routing,
    and resolution management.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "ticket_id": "TKT-12345",
            "client_id": "cs_1696800000_acme",
            "subject": "Unable to export reports",
            "description": "Users are getting a 500 error when trying to export CSV reports from the dashboard.",
            "priority": "P1",
            "category": "technical_issue",
            "status": "in_progress",
            "requester_email": "john.smith@acme.com",
            "requester_name": "John Smith",
            "assigned_agent": "support-agent@company.com",
            "assigned_team": "Technical Support",
            "tags": ["export", "reports", "error-500"],
            "created_at": "2025-10-10T08:00:00Z",
            "updated_at": "2025-10-10T09:15:00Z",
            "first_response_at": "2025-10-10T08:12:00Z",
            "resolved_at": None,
            "closed_at": None,
            "sla_first_response_minutes": 15,
            "sla_resolution_minutes": 240,
            "first_response_sla_status": "met",
            "resolution_sla_status": "at_risk",
            "time_to_first_response_minutes": 12,
            "time_to_resolution_minutes": None,
            "satisfaction_rating": None,
            "satisfaction_comment": None,
            "escalated": False,
            "escalated_at": None,
            "escalation_reason": None,
            "resolution_notes": None,
            "internal_notes": "Investigating with engineering team",
            "customer_visible_notes": "We are actively working on this issue and will provide an update within 2 hours."
        }
    })

    # Identification
    ticket_id: str = Field(
        ...,
        description="Unique ticket identifier",
        pattern=r"^TKT-[0-9]+$"
    )
    client_id: str = Field(
        ...,
        description="Customer identifier"
    )

    # Ticket content
    subject: str = Field(
        ...,
        description="Ticket subject/title",
        min_length=1,
        max_length=500
    )
    description: str = Field(
        ...,
        description="Detailed issue description",
        min_length=1
    )
    priority: TicketPriority = Field(
        ...,
        description="Ticket priority level"
    )
    category: TicketCategory = Field(
        ...,
        description="Ticket category/type"
    )
    status: TicketStatus = Field(
        default=TicketStatus.OPEN,
        description="Current ticket status"
    )

    # Requester information
    requester_email: str = Field(
        ...,
        description="Requester email address",
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    requester_name: str = Field(
        ...,
        description="Requester full name"
    )

    # Assignment
    assigned_agent: Optional[str] = Field(
        None,
        description="Email of assigned support agent"
    )
    assigned_team: Optional[str] = Field(
        None,
        description="Assigned support team name"
    )

    # Metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Ticket tags for categorization and search"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Ticket creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )
    first_response_at: Optional[datetime] = Field(
        None,
        description="Timestamp of first agent response"
    )
    resolved_at: Optional[datetime] = Field(
        None,
        description="Timestamp when ticket was resolved"
    )
    closed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when ticket was closed"
    )

    # SLA tracking
    sla_first_response_minutes: int = Field(
        ...,
        description="SLA target for first response (minutes)",
        ge=0
    )
    sla_resolution_minutes: int = Field(
        ...,
        description="SLA target for resolution (minutes)",
        ge=0
    )
    first_response_sla_status: SLAStatus = Field(
        default=SLAStatus.NOT_APPLICABLE,
        description="First response SLA status"
    )
    resolution_sla_status: SLAStatus = Field(
        default=SLAStatus.NOT_APPLICABLE,
        description="Resolution SLA status"
    )
    time_to_first_response_minutes: Optional[int] = Field(
        None,
        description="Actual time to first response (minutes)",
        ge=0
    )
    time_to_resolution_minutes: Optional[int] = Field(
        None,
        description="Actual time to resolution (minutes)",
        ge=0
    )

    # Customer satisfaction
    satisfaction_rating: Optional[int] = Field(
        None,
        description="Customer satisfaction rating (1-5)",
        ge=1,
        le=5
    )
    satisfaction_comment: Optional[str] = Field(
        None,
        description="Customer satisfaction feedback"
    )

    # Escalation
    escalated: bool = Field(
        default=False,
        description="Whether ticket has been escalated"
    )
    escalated_at: Optional[datetime] = Field(
        None,
        description="Escalation timestamp"
    )
    escalation_reason: Optional[str] = Field(
        None,
        description="Reason for escalation"
    )

    # Resolution
    resolution_notes: Optional[str] = Field(
        None,
        description="Resolution notes and solution provided"
    )
    internal_notes: Optional[str] = Field(
        None,
        description="Internal notes (not visible to customer)"
    )
    customer_visible_notes: Optional[str] = Field(
        None,
        description="Notes visible to customer"
    )

    def calculate_sla_status(self) -> None:
        """Calculate and update SLA status based on timestamps"""
        now = datetime.now()

        # First response SLA
        if self.first_response_at is None:
            elapsed = (now - self.created_at).total_seconds() / 60
            if elapsed > self.sla_first_response_minutes:
                self.first_response_sla_status = SLAStatus.BREACHED
            elif elapsed > self.sla_first_response_minutes * 0.8:
                self.first_response_sla_status = SLAStatus.AT_RISK
        else:
            self.time_to_first_response_minutes = int(
                (self.first_response_at - self.created_at).total_seconds() / 60
            )
            if self.time_to_first_response_minutes <= self.sla_first_response_minutes:
                self.first_response_sla_status = SLAStatus.MET
            else:
                self.first_response_sla_status = SLAStatus.BREACHED

        # Resolution SLA
        if self.resolved_at is None and self.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            elapsed = (now - self.created_at).total_seconds() / 60
            if elapsed > self.sla_resolution_minutes:
                self.resolution_sla_status = SLAStatus.BREACHED
            elif elapsed > self.sla_resolution_minutes * 0.8:
                self.resolution_sla_status = SLAStatus.AT_RISK
        elif self.resolved_at is not None:
            self.time_to_resolution_minutes = int(
                (self.resolved_at - self.created_at).total_seconds() / 60
            )
            if self.time_to_resolution_minutes <= self.sla_resolution_minutes:
                self.resolution_sla_status = SLAStatus.MET
            else:
                self.resolution_sla_status = SLAStatus.BREACHED


class TicketComment(BaseModel):
    """
    Comment or update on a support ticket.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "comment_id": "CMT-67890",
            "ticket_id": "TKT-12345",
            "author_email": "support-agent@company.com",
            "author_name": "Support Agent",
            "author_type": "agent",
            "content": "We've identified the issue and are working on a fix. ETA 2 hours.",
            "is_public": True,
            "created_at": "2025-10-10T09:15:00Z",
            "attachments": []
        }
    })

    comment_id: str = Field(..., description="Unique comment identifier")
    ticket_id: str = Field(..., description="Parent ticket ID")
    author_email: str = Field(..., description="Comment author email")
    author_name: str = Field(..., description="Comment author name")
    author_type: str = Field(
        ...,
        description="Author type (agent, customer, system)",
        pattern=r"^(agent|customer|system)$"
    )
    content: str = Field(
        ...,
        description="Comment content",
        min_length=1
    )
    is_public: bool = Field(
        default=True,
        description="Whether comment is visible to customer"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Comment timestamp"
    )
    attachments: List[str] = Field(
        default_factory=list,
        description="URLs or paths to attached files"
    )


class KnowledgeBaseArticle(BaseModel):
    """
    Knowledge base article for self-service support.

    Searchable, versioned content to help customers
    resolve issues independently.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "article_id": "KB-1001",
            "title": "How to Export Reports in CSV Format",
            "summary": "Step-by-step guide to exporting dashboard reports as CSV files",
            "content": "To export reports: 1. Navigate to Reports... 2. Click Export...",
            "category": "Reports & Analytics",
            "subcategory": "Data Export",
            "tags": ["export", "reports", "csv", "how-to"],
            "status": "published",
            "author": "Support Team",
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-09-20T14:30:00Z",
            "published_at": "2025-01-15T11:00:00Z",
            "version": 3,
            "view_count": 1247,
            "helpful_votes": 183,
            "not_helpful_votes": 12,
            "helpfulness_score": 0.94,
            "related_articles": ["KB-1002", "KB-1003"],
            "search_keywords": ["export", "csv", "download", "reports"],
            "customer_facing": True,
            "requires_authentication": False,
            "product_tier_restrictions": []
        }
    })

    # Identification
    article_id: str = Field(
        ...,
        description="Unique article identifier",
        pattern=r"^KB-[0-9]+$"
    )
    title: str = Field(
        ...,
        description="Article title",
        min_length=1,
        max_length=200
    )
    summary: str = Field(
        ...,
        description="Brief article summary (1-2 sentences)",
        max_length=500
    )
    content: str = Field(
        ...,
        description="Full article content (supports markdown)",
        min_length=1
    )

    # Organization
    category: str = Field(
        ...,
        description="Primary category",
        max_length=100
    )
    subcategory: Optional[str] = Field(
        None,
        description="Subcategory for finer organization",
        max_length=100
    )
    tags: List[str] = Field(
        ...,
        description="Tags for search and categorization",
        min_length=1
    )

    # Publishing
    status: ArticleStatus = Field(
        default=ArticleStatus.DRAFT,
        description="Article publication status"
    )
    author: str = Field(
        ...,
        description="Article author name"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Article creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )
    published_at: Optional[datetime] = Field(
        None,
        description="Publication timestamp"
    )
    version: int = Field(
        default=1,
        description="Article version number",
        ge=1
    )

    # Analytics
    view_count: int = Field(
        default=0,
        description="Total article views",
        ge=0
    )
    helpful_votes: int = Field(
        default=0,
        description="Number of 'helpful' votes",
        ge=0
    )
    not_helpful_votes: int = Field(
        default=0,
        description="Number of 'not helpful' votes",
        ge=0
    )
    helpfulness_score: float = Field(
        default=0.0,
        description="Helpfulness ratio (helpful / total votes)",
        ge=0,
        le=1
    )

    # Relationships
    related_articles: List[str] = Field(
        default_factory=list,
        description="IDs of related articles"
    )

    # Search optimization
    search_keywords: List[str] = Field(
        default_factory=list,
        description="Additional keywords for search optimization"
    )

    # Access control
    customer_facing: bool = Field(
        default=True,
        description="Whether article is visible to customers"
    )
    requires_authentication: bool = Field(
        default=False,
        description="Whether article requires login to access"
    )
    product_tier_restrictions: List[str] = Field(
        default_factory=list,
        description="Product tiers that can access this article (empty = all)"
    )

    def calculate_helpfulness_score(self) -> None:
        """Calculate helpfulness score from votes"""
        total_votes = self.helpful_votes + self.not_helpful_votes
        if total_votes > 0:
            self.helpfulness_score = self.helpful_votes / total_votes
        else:
            self.helpfulness_score = 0.0


class SupportMetrics(BaseModel):
    """
    Support performance metrics for a time period.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "client_id": "cs_1696800000_acme",
            "period_start": "2025-10-01T00:00:00Z",
            "period_end": "2025-10-31T23:59:59Z",
            "total_tickets": 47,
            "tickets_opened": 47,
            "tickets_resolved": 42,
            "tickets_closed": 38,
            "open_tickets": 5,
            "avg_first_response_minutes": 11.2,
            "avg_resolution_minutes": 187.5,
            "first_response_sla_met_percentage": 0.96,
            "resolution_sla_met_percentage": 0.89,
            "tickets_by_priority": {
                "P0": 1,
                "P1": 8,
                "P2": 18,
                "P3": 15,
                "P4": 5
            },
            "tickets_by_category": {
                "technical_issue": 22,
                "how_to_question": 12,
                "bug_report": 8,
                "feature_request": 5
            },
            "tickets_escalated": 3,
            "escalation_rate": 0.064,
            "avg_satisfaction_rating": 4.4,
            "satisfaction_response_rate": 0.78,
            "kb_article_views": 1847,
            "kb_deflection_rate": 0.31
        }
    })

    client_id: str = Field(..., description="Customer identifier")
    period_start: datetime = Field(..., description="Metrics period start")
    period_end: datetime = Field(..., description="Metrics period end")

    # Volume metrics
    total_tickets: int = Field(default=0, description="Total tickets in period", ge=0)
    tickets_opened: int = Field(default=0, description="New tickets opened", ge=0)
    tickets_resolved: int = Field(default=0, description="Tickets resolved", ge=0)
    tickets_closed: int = Field(default=0, description="Tickets closed", ge=0)
    open_tickets: int = Field(default=0, description="Currently open tickets", ge=0)

    # Performance metrics
    avg_first_response_minutes: float = Field(
        default=0.0,
        description="Average time to first response",
        ge=0
    )
    avg_resolution_minutes: float = Field(
        default=0.0,
        description="Average time to resolution",
        ge=0
    )
    first_response_sla_met_percentage: float = Field(
        default=0.0,
        description="Percentage of tickets meeting first response SLA",
        ge=0,
        le=1
    )
    resolution_sla_met_percentage: float = Field(
        default=0.0,
        description="Percentage of tickets meeting resolution SLA",
        ge=0,
        le=1
    )

    # Distribution
    tickets_by_priority: Dict[str, int] = Field(
        default_factory=dict,
        description="Ticket count by priority level"
    )
    tickets_by_category: Dict[str, int] = Field(
        default_factory=dict,
        description="Ticket count by category"
    )

    # Quality metrics
    tickets_escalated: int = Field(default=0, description="Tickets escalated", ge=0)
    escalation_rate: float = Field(
        default=0.0,
        description="Percentage of tickets escalated",
        ge=0,
        le=1
    )
    avg_satisfaction_rating: float = Field(
        default=0.0,
        description="Average customer satisfaction rating",
        ge=0,
        le=5
    )
    satisfaction_response_rate: float = Field(
        default=0.0,
        description="Percentage of tickets with satisfaction ratings",
        ge=0,
        le=1
    )

    # Self-service metrics
    kb_article_views: int = Field(
        default=0,
        description="Knowledge base article views in period",
        ge=0
    )
    kb_deflection_rate: float = Field(
        default=0.0,
        description="Estimated ticket deflection rate via KB",
        ge=0,
        le=1
    )


__all__ = [
    'TicketPriority',
    'TicketStatus',
    'TicketCategory',
    'SLAStatus',
    'ArticleStatus',
    'SupportTicket',
    'TicketComment',
    'KnowledgeBaseArticle',
    'SupportMetrics'
]
