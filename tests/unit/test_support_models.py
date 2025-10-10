"""
Unit Tests for Support Models

Tests for all support-related Pydantic models including support tickets,
ticket comments, knowledge base articles, and support metrics.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.models.support_models import (
    TicketPriority, TicketStatus, TicketCategory, SLAStatus, ArticleStatus,
    SupportTicket, TicketComment, KnowledgeBaseArticle, SupportMetrics
)


# ============================================================================
# TicketPriority Enum Tests
# ============================================================================

@pytest.mark.unit
def test_ticket_priority_enum_values():
    """Test that TicketPriority enum has all expected values."""
    assert TicketPriority.P0_CRITICAL == "P0"
    assert TicketPriority.P1_HIGH == "P1"
    assert TicketPriority.P2_MEDIUM == "P2"
    assert TicketPriority.P3_NORMAL == "P3"
    assert TicketPriority.P4_LOW == "P4"


@pytest.mark.unit
def test_ticket_priority_enum_count():
    """Test that TicketPriority has exactly 5 priority levels."""
    assert len(list(TicketPriority)) == 5


# ============================================================================
# TicketStatus Enum Tests
# ============================================================================

@pytest.mark.unit
def test_ticket_status_enum_values():
    """Test that TicketStatus enum has all expected values."""
    assert TicketStatus.OPEN == "open"
    assert TicketStatus.IN_PROGRESS == "in_progress"
    assert TicketStatus.WAITING_ON_CUSTOMER == "waiting_on_customer"
    assert TicketStatus.WAITING_ON_ENGINEERING == "waiting_on_engineering"
    assert TicketStatus.RESOLVED == "resolved"
    assert TicketStatus.CLOSED == "closed"
    assert TicketStatus.REOPENED == "reopened"


# ============================================================================
# TicketCategory Enum Tests
# ============================================================================

@pytest.mark.unit
def test_ticket_category_enum_values():
    """Test that TicketCategory enum has all expected values."""
    assert TicketCategory.TECHNICAL_ISSUE == "technical_issue"
    assert TicketCategory.BUG_REPORT == "bug_report"
    assert TicketCategory.FEATURE_REQUEST == "feature_request"
    assert TicketCategory.HOW_TO_QUESTION == "how_to_question"
    assert TicketCategory.ACCOUNT_BILLING == "account_billing"


# ============================================================================
# SLAStatus Enum Tests
# ============================================================================

@pytest.mark.unit
def test_sla_status_enum_values():
    """Test that SLAStatus enum has all expected values."""
    assert SLAStatus.MET == "met"
    assert SLAStatus.AT_RISK == "at_risk"
    assert SLAStatus.BREACHED == "breached"
    assert SLAStatus.NOT_APPLICABLE == "not_applicable"


# ============================================================================
# ArticleStatus Enum Tests
# ============================================================================

@pytest.mark.unit
def test_article_status_enum_values():
    """Test that ArticleStatus enum has all expected values."""
    assert ArticleStatus.DRAFT == "draft"
    assert ArticleStatus.REVIEW == "review"
    assert ArticleStatus.PUBLISHED == "published"
    assert ArticleStatus.ARCHIVED == "archived"


# ============================================================================
# SupportTicket Model Tests
# ============================================================================

@pytest.mark.unit
def test_support_ticket_valid_creation(sample_client_id):
    """Test creating a valid SupportTicket with all required fields."""
    ticket = SupportTicket(
        ticket_id="TKT-12345",
        client_id=sample_client_id,
        subject="Unable to export reports",
        description="Getting 500 error when exporting CSV reports",
        priority=TicketPriority.P1_HIGH,
        category=TicketCategory.TECHNICAL_ISSUE,
        requester_email="user@example.com",
        requester_name="John Doe",
        sla_first_response_minutes=15,
        sla_resolution_minutes=240
    )

    assert ticket.ticket_id == "TKT-12345"
    assert ticket.priority == TicketPriority.P1_HIGH
    assert ticket.category == TicketCategory.TECHNICAL_ISSUE
    assert ticket.status == TicketStatus.OPEN  # Default


@pytest.mark.unit
def test_support_ticket_invalid_id_format():
    """Test that invalid ticket_id format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        SupportTicket(
            ticket_id="INVALID-123",  # Should be TKT-
            client_id="cs_1234_test",
            subject="Test",
            description="Test description",
            priority=TicketPriority.P3_NORMAL,
            category=TicketCategory.HOW_TO_QUESTION,
            requester_email="user@example.com",
            requester_name="John Doe",
            sla_first_response_minutes=30,
            sla_resolution_minutes=480
        )

    assert "ticket_id" in str(exc_info.value)


@pytest.mark.unit
def test_support_ticket_invalid_email():
    """Test that invalid email format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        SupportTicket(
            ticket_id="TKT-123",
            client_id="cs_1234_test",
            subject="Test",
            description="Test description",
            priority=TicketPriority.P3_NORMAL,
            category=TicketCategory.HOW_TO_QUESTION,
            requester_email="invalid_email",  # Missing @
            requester_name="John Doe",
            sla_first_response_minutes=30,
            sla_resolution_minutes=480
        )

    assert "requester_email" in str(exc_info.value)


@pytest.mark.unit
def test_support_ticket_satisfaction_rating_boundaries():
    """Test that satisfaction_rating respects 1-5 boundaries."""
    ticket = SupportTicket(
        ticket_id="TKT-123",
        client_id="cs_1234_test",
        subject="Test",
        description="Test description",
        priority=TicketPriority.P3_NORMAL,
        category=TicketCategory.HOW_TO_QUESTION,
        requester_email="user@example.com",
        requester_name="John Doe",
        sla_first_response_minutes=30,
        sla_resolution_minutes=480,
        satisfaction_rating=5
    )
    assert ticket.satisfaction_rating == 5

    # Test below minimum
    with pytest.raises(ValidationError) as exc_info:
        SupportTicket(
            ticket_id="TKT-124",
            client_id="cs_1234_test",
            subject="Test",
            description="Test description",
            priority=TicketPriority.P3_NORMAL,
            category=TicketCategory.HOW_TO_QUESTION,
            requester_email="user@example.com",
            requester_name="John Doe",
            sla_first_response_minutes=30,
            sla_resolution_minutes=480,
            satisfaction_rating=0
        )

    assert "satisfaction_rating" in str(exc_info.value)


@pytest.mark.unit
def test_support_ticket_calculate_sla_status_method():
    """Test the calculate_sla_status method for SLA tracking."""
    ticket = SupportTicket(
        ticket_id="TKT-123",
        client_id="cs_1234_test",
        subject="Test",
        description="Test description",
        priority=TicketPriority.P1_HIGH,
        category=TicketCategory.TECHNICAL_ISSUE,
        requester_email="user@example.com",
        requester_name="John Doe",
        sla_first_response_minutes=15,
        sla_resolution_minutes=240,
        created_at=datetime.now() - timedelta(minutes=10)
    )

    # Call the method
    ticket.calculate_sla_status()

    # First response not yet provided, but within SLA
    assert ticket.first_response_sla_status in [SLAStatus.NOT_APPLICABLE, SLAStatus.AT_RISK]


@pytest.mark.unit
def test_support_ticket_with_response_timestamps():
    """Test SupportTicket with first_response and resolution timestamps."""
    created = datetime.now() - timedelta(hours=2)
    first_response = datetime.now() - timedelta(hours=1, minutes=50)
    resolved = datetime.now() - timedelta(minutes=10)

    ticket = SupportTicket(
        ticket_id="TKT-123",
        client_id="cs_1234_test",
        subject="Test",
        description="Test description",
        priority=TicketPriority.P2_MEDIUM,
        category=TicketCategory.TECHNICAL_ISSUE,
        requester_email="user@example.com",
        requester_name="John Doe",
        sla_first_response_minutes=30,
        sla_resolution_minutes=240,
        created_at=created,
        first_response_at=first_response,
        resolved_at=resolved,
        status=TicketStatus.RESOLVED
    )

    assert ticket.first_response_at is not None
    assert ticket.resolved_at is not None
    assert ticket.status == TicketStatus.RESOLVED


@pytest.mark.unit
def test_support_ticket_escalation():
    """Test SupportTicket escalation fields."""
    ticket = SupportTicket(
        ticket_id="TKT-123",
        client_id="cs_1234_test",
        subject="Critical Issue",
        description="Production system down",
        priority=TicketPriority.P0_CRITICAL,
        category=TicketCategory.TECHNICAL_ISSUE,
        requester_email="user@example.com",
        requester_name="John Doe",
        sla_first_response_minutes=5,
        sla_resolution_minutes=60,
        escalated=True,
        escalated_at=datetime.now(),
        escalation_reason="P0 issue requires immediate attention"
    )

    assert ticket.escalated == True
    assert ticket.escalation_reason is not None


@pytest.mark.unit
def test_support_ticket_default_values(sample_client_id):
    """Test that SupportTicket has correct default values."""
    ticket = SupportTicket(
        ticket_id="TKT-123",
        client_id=sample_client_id,
        subject="Test",
        description="Test description",
        priority=TicketPriority.P3_NORMAL,
        category=TicketCategory.HOW_TO_QUESTION,
        requester_email="user@example.com",
        requester_name="John Doe",
        sla_first_response_minutes=30,
        sla_resolution_minutes=480
    )

    assert ticket.status == TicketStatus.OPEN
    assert ticket.escalated == False
    assert ticket.tags == []
    assert ticket.first_response_sla_status == SLAStatus.NOT_APPLICABLE
    assert ticket.resolution_sla_status == SLAStatus.NOT_APPLICABLE


# ============================================================================
# TicketComment Model Tests
# ============================================================================

@pytest.mark.unit
def test_ticket_comment_valid_creation():
    """Test creating a valid TicketComment."""
    comment = TicketComment(
        comment_id="CMT-12345",
        ticket_id="TKT-123",
        author_email="agent@company.com",
        author_name="Support Agent",
        author_type="agent",
        content="We're investigating this issue and will update you shortly."
    )

    assert comment.comment_id == "CMT-12345"
    assert comment.author_type == "agent"
    assert comment.is_public == True  # Default


@pytest.mark.unit
def test_ticket_comment_author_type_validation():
    """Test that author_type must be one of allowed values."""
    for author_type in ["agent", "customer", "system"]:
        comment = TicketComment(
            comment_id="CMT-123",
            ticket_id="TKT-123",
            author_email="test@example.com",
            author_name="Test User",
            author_type=author_type,
            content="Test comment"
        )
        assert comment.author_type == author_type

    # Invalid author type
    with pytest.raises(ValidationError) as exc_info:
        TicketComment(
            comment_id="CMT-124",
            ticket_id="TKT-123",
            author_email="test@example.com",
            author_name="Test User",
            author_type="invalid",
            content="Test comment"
        )

    assert "author_type" in str(exc_info.value)


@pytest.mark.unit
def test_ticket_comment_public_vs_internal():
    """Test public vs internal comments."""
    # Public comment
    public_comment = TicketComment(
        comment_id="CMT-123",
        ticket_id="TKT-123",
        author_email="agent@company.com",
        author_name="Agent",
        author_type="agent",
        content="Public response to customer",
        is_public=True
    )
    assert public_comment.is_public == True

    # Internal comment
    internal_comment = TicketComment(
        comment_id="CMT-124",
        ticket_id="TKT-123",
        author_email="agent@company.com",
        author_name="Agent",
        author_type="agent",
        content="Internal notes for team",
        is_public=False
    )
    assert internal_comment.is_public == False


@pytest.mark.unit
def test_ticket_comment_with_attachments():
    """Test TicketComment with file attachments."""
    attachments = [
        "https://example.com/files/screenshot1.png",
        "https://example.com/files/logs.txt"
    ]

    comment = TicketComment(
        comment_id="CMT-123",
        ticket_id="TKT-123",
        author_email="customer@example.com",
        author_name="Customer",
        author_type="customer",
        content="Here are the screenshots you requested",
        attachments=attachments
    )

    assert len(comment.attachments) == 2


# ============================================================================
# KnowledgeBaseArticle Model Tests
# ============================================================================

@pytest.mark.unit
def test_knowledge_base_article_valid_creation():
    """Test creating a valid KnowledgeBaseArticle."""
    article = KnowledgeBaseArticle(
        article_id="KB-1001",
        title="How to Export Reports",
        summary="Step-by-step guide for exporting reports",
        content="To export reports: 1. Navigate to Reports...",
        category="Reports & Analytics",
        tags=["export", "reports", "how-to"],
        author="Support Team"
    )

    assert article.article_id == "KB-1001"
    assert article.title == "How to Export Reports"
    assert len(article.tags) == 3


@pytest.mark.unit
def test_knowledge_base_article_invalid_id_format():
    """Test that invalid article_id format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        KnowledgeBaseArticle(
            article_id="INVALID-1",  # Should be KB-
            title="Test Article",
            summary="Test summary",
            content="Test content",
            category="Test",
            tags=["test"],
            author="Author"
        )

    assert "article_id" in str(exc_info.value)


@pytest.mark.unit
def test_knowledge_base_article_tags_min_length():
    """Test that tags must have at least one tag."""
    with pytest.raises(ValidationError) as exc_info:
        KnowledgeBaseArticle(
            article_id="KB-100",
            title="Test Article",
            summary="Test summary",
            content="Test content",
            category="Test",
            tags=[],  # Empty list
            author="Author"
        )

    assert "tags" in str(exc_info.value)


@pytest.mark.unit
def test_knowledge_base_article_helpfulness_score():
    """Test the calculate_helpfulness_score method."""
    article = KnowledgeBaseArticle(
        article_id="KB-100",
        title="Test Article",
        summary="Test summary",
        content="Test content",
        category="Test",
        tags=["test"],
        author="Author",
        helpful_votes=80,
        not_helpful_votes=20
    )

    article.calculate_helpfulness_score()
    assert article.helpfulness_score == 0.8


@pytest.mark.unit
def test_knowledge_base_article_helpfulness_score_no_votes():
    """Test helpfulness score calculation with no votes."""
    article = KnowledgeBaseArticle(
        article_id="KB-100",
        title="Test Article",
        summary="Test summary",
        content="Test content",
        category="Test",
        tags=["test"],
        author="Author",
        helpful_votes=0,
        not_helpful_votes=0
    )

    article.calculate_helpfulness_score()
    assert article.helpfulness_score == 0.0


@pytest.mark.unit
def test_knowledge_base_article_version():
    """Test article version tracking."""
    article = KnowledgeBaseArticle(
        article_id="KB-100",
        title="Test Article",
        summary="Test summary",
        content="Test content",
        category="Test",
        tags=["test"],
        author="Author",
        version=3
    )
    assert article.version == 3


@pytest.mark.unit
def test_knowledge_base_article_access_control():
    """Test article access control fields."""
    article = KnowledgeBaseArticle(
        article_id="KB-100",
        title="Internal Article",
        summary="Internal use only",
        content="Internal content",
        category="Internal",
        tags=["internal"],
        author="Admin",
        customer_facing=False,
        requires_authentication=True,
        product_tier_restrictions=["enterprise"]
    )

    assert article.customer_facing == False
    assert article.requires_authentication == True
    assert len(article.product_tier_restrictions) == 1


@pytest.mark.unit
def test_knowledge_base_article_default_values():
    """Test that KnowledgeBaseArticle has correct default values."""
    article = KnowledgeBaseArticle(
        article_id="KB-100",
        title="Test Article",
        summary="Test summary",
        content="Test content",
        category="Test",
        tags=["test"],
        author="Author"
    )

    assert article.status == ArticleStatus.DRAFT
    assert article.version == 1
    assert article.view_count == 0
    assert article.helpful_votes == 0
    assert article.not_helpful_votes == 0
    assert article.helpfulness_score == 0.0
    assert article.customer_facing == True
    assert article.requires_authentication == False
    assert article.product_tier_restrictions == []


# ============================================================================
# SupportMetrics Model Tests
# ============================================================================

@pytest.mark.unit
def test_support_metrics_valid_creation(sample_client_id):
    """Test creating valid SupportMetrics."""
    metrics = SupportMetrics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_tickets=50,
        tickets_opened=50,
        tickets_resolved=45,
        tickets_closed=40,
        open_tickets=5,
        avg_first_response_minutes=12.5,
        avg_resolution_minutes=180.0,
        first_response_sla_met_percentage=0.95,
        resolution_sla_met_percentage=0.88
    )

    assert metrics.client_id == sample_client_id
    assert metrics.total_tickets == 50
    assert metrics.tickets_resolved == 45


@pytest.mark.unit
def test_support_metrics_sla_percentage_boundaries():
    """Test that SLA percentages respect 0-1 boundaries."""
    metrics = SupportMetrics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        first_response_sla_met_percentage=1.0,
        resolution_sla_met_percentage=0.0
    )

    assert metrics.first_response_sla_met_percentage == 1.0
    assert metrics.resolution_sla_met_percentage == 0.0


@pytest.mark.unit
def test_support_metrics_with_distributions():
    """Test SupportMetrics with ticket distributions."""
    metrics = SupportMetrics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        tickets_by_priority={
            "P0": 2,
            "P1": 10,
            "P2": 20,
            "P3": 15,
            "P4": 3
        },
        tickets_by_category={
            "technical_issue": 25,
            "how_to_question": 15,
            "bug_report": 10
        }
    )

    assert metrics.tickets_by_priority["P0"] == 2
    assert metrics.tickets_by_category["technical_issue"] == 25


@pytest.mark.unit
def test_support_metrics_escalation_rate():
    """Test escalation rate calculations."""
    metrics = SupportMetrics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_tickets=100,
        tickets_escalated=5,
        escalation_rate=0.05
    )

    assert metrics.escalation_rate == 0.05


@pytest.mark.unit
def test_support_metrics_satisfaction_metrics():
    """Test customer satisfaction metrics."""
    metrics = SupportMetrics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        avg_satisfaction_rating=4.5,
        satisfaction_response_rate=0.80
    )

    assert metrics.avg_satisfaction_rating == 4.5
    assert metrics.satisfaction_response_rate == 0.80


@pytest.mark.unit
def test_support_metrics_kb_metrics():
    """Test knowledge base metrics."""
    metrics = SupportMetrics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        kb_article_views=2500,
        kb_deflection_rate=0.35
    )

    assert metrics.kb_article_views == 2500
    assert metrics.kb_deflection_rate == 0.35


@pytest.mark.unit
def test_support_metrics_default_values(sample_client_id):
    """Test that SupportMetrics has correct default values."""
    metrics = SupportMetrics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31)
    )

    assert metrics.total_tickets == 0
    assert metrics.tickets_opened == 0
    assert metrics.tickets_resolved == 0
    assert metrics.avg_first_response_minutes == 0.0
    assert metrics.avg_resolution_minutes == 0.0
    assert metrics.tickets_by_priority == {}
    assert metrics.tickets_by_category == {}
