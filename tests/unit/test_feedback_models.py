"""
Unit Tests for Feedback Models

Tests for all feedback-related Pydantic models including customer feedback,
NPS responses, sentiment analysis, and survey templates.
"""

import pytest
from datetime import datetime, date, timedelta
from pydantic import ValidationError

from src.models.feedback_models import (
    FeedbackType, SentimentType, FeedbackPriority, FeedbackStatus,
    CustomerFeedback, NPSResponse, SentimentAnalysis, SurveyTemplate
)


# ============================================================================
# FeedbackType Enum Tests
# ============================================================================

@pytest.mark.unit
def test_feedback_type_enum_values():
    """Test that FeedbackType enum has all expected values."""
    assert FeedbackType.NPS == "nps"
    assert FeedbackType.CSAT == "csat"
    assert FeedbackType.CES == "ces"
    assert FeedbackType.FEATURE_REQUEST == "feature_request"
    assert FeedbackType.BUG_REPORT == "bug_report"
    assert FeedbackType.PRODUCT_FEEDBACK == "product_feedback"
    assert FeedbackType.SERVICE_FEEDBACK == "service_feedback"
    assert FeedbackType.GENERAL == "general"


@pytest.mark.unit
def test_feedback_type_enum_count():
    """Test that FeedbackType has exactly 8 types."""
    assert len(list(FeedbackType)) == 8


# ============================================================================
# SentimentType Enum Tests
# ============================================================================

@pytest.mark.unit
def test_sentiment_type_enum_values():
    """Test that SentimentType enum has all expected values."""
    assert SentimentType.VERY_POSITIVE == "very_positive"
    assert SentimentType.POSITIVE == "positive"
    assert SentimentType.NEUTRAL == "neutral"
    assert SentimentType.NEGATIVE == "negative"
    assert SentimentType.VERY_NEGATIVE == "very_negative"


@pytest.mark.unit
def test_sentiment_type_enum_count():
    """Test that SentimentType has exactly 5 sentiment levels."""
    assert len(list(SentimentType)) == 5


# ============================================================================
# FeedbackPriority Enum Tests
# ============================================================================

@pytest.mark.unit
def test_feedback_priority_enum_values():
    """Test that FeedbackPriority enum has all expected values."""
    assert FeedbackPriority.CRITICAL == "critical"
    assert FeedbackPriority.HIGH == "high"
    assert FeedbackPriority.MEDIUM == "medium"
    assert FeedbackPriority.LOW == "low"


# ============================================================================
# FeedbackStatus Enum Tests
# ============================================================================

@pytest.mark.unit
def test_feedback_status_enum_values():
    """Test that FeedbackStatus enum has all expected values."""
    assert FeedbackStatus.NEW == "new"
    assert FeedbackStatus.REVIEWED == "reviewed"
    assert FeedbackStatus.IN_PROGRESS == "in_progress"
    assert FeedbackStatus.RESOLVED == "resolved"
    assert FeedbackStatus.CLOSED == "closed"
    assert FeedbackStatus.WONT_FIX == "wont_fix"


# ============================================================================
# CustomerFeedback Model Tests
# ============================================================================

@pytest.mark.unit
def test_customer_feedback_valid_creation(sample_client_id):
    """Test creating a valid CustomerFeedback with all required fields."""
    feedback = CustomerFeedback(
        feedback_id="FB-12345",
        client_id=sample_client_id,
        feedback_type=FeedbackType.PRODUCT_FEEDBACK,
        source="in-app_survey",
        submitter_email="user@example.com",
        submitter_name="John Doe",
        title="Great product feature",
        content="I really like the new export feature. Very helpful!",
        category="feature_feedback",
        sentiment=SentimentType.POSITIVE,
        sentiment_score=0.85
    )

    assert feedback.feedback_id == "FB-12345"
    assert feedback.client_id == sample_client_id
    assert feedback.feedback_type == FeedbackType.PRODUCT_FEEDBACK
    assert feedback.sentiment == SentimentType.POSITIVE
    assert feedback.sentiment_score == 0.85


@pytest.mark.unit
def test_customer_feedback_invalid_id_format():
    """Test that invalid feedback_id format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        CustomerFeedback(
            feedback_id="INVALID-123",  # Should be FB-
            client_id="cs_1234_test",
            feedback_type=FeedbackType.GENERAL,
            source="email",
            submitter_email="user@example.com",
            submitter_name="John Doe",
            title="Test",
            content="Test content",
            category="test",
            sentiment=SentimentType.NEUTRAL,
            sentiment_score=0.0
        )

    assert "feedback_id" in str(exc_info.value)


@pytest.mark.unit
def test_customer_feedback_invalid_email():
    """Test that invalid email format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        CustomerFeedback(
            feedback_id="FB-123",
            client_id="cs_1234_test",
            feedback_type=FeedbackType.GENERAL,
            source="email",
            submitter_email="invalid_email",  # Missing @
            submitter_name="John Doe",
            title="Test",
            content="Test content",
            category="test",
            sentiment=SentimentType.NEUTRAL,
            sentiment_score=0.0
        )

    assert "submitter_email" in str(exc_info.value)


@pytest.mark.unit
def test_customer_feedback_sentiment_score_boundaries():
    """Test that sentiment_score respects -1 to 1 boundaries."""
    # Test minimum
    feedback = CustomerFeedback(
        feedback_id="FB-123",
        client_id="cs_1234_test",
        feedback_type=FeedbackType.GENERAL,
        source="email",
        submitter_email="user@example.com",
        submitter_name="John Doe",
        title="Test",
        content="Test content",
        category="test",
        sentiment=SentimentType.VERY_NEGATIVE,
        sentiment_score=-1.0
    )
    assert feedback.sentiment_score == -1.0

    # Test maximum
    feedback.sentiment_score = 1.0
    assert feedback.sentiment_score == 1.0

    # Test below minimum
    with pytest.raises(ValidationError) as exc_info:
        CustomerFeedback(
            feedback_id="FB-123",
            client_id="cs_1234_test",
            feedback_type=FeedbackType.GENERAL,
            source="email",
            submitter_email="user@example.com",
            submitter_name="John Doe",
            title="Test",
            content="Test content",
            category="test",
            sentiment=SentimentType.VERY_NEGATIVE,
            sentiment_score=-1.5
        )

    assert "sentiment_score" in str(exc_info.value)


@pytest.mark.unit
def test_customer_feedback_default_values(sample_client_id):
    """Test that CustomerFeedback has correct default values."""
    feedback = CustomerFeedback(
        feedback_id="FB-123",
        client_id=sample_client_id,
        feedback_type=FeedbackType.GENERAL,
        source="email",
        submitter_email="user@example.com",
        submitter_name="John Doe",
        title="Test",
        content="Test content",
        category="test",
        sentiment=SentimentType.NEUTRAL,
        sentiment_score=0.0
    )

    assert feedback.priority == FeedbackPriority.MEDIUM
    assert feedback.status == FeedbackStatus.NEW
    assert feedback.follow_up_required == False
    assert feedback.customer_responded == False
    assert feedback.tags == []


@pytest.mark.unit
def test_customer_feedback_with_all_optional_fields(sample_client_id):
    """Test CustomerFeedback with all optional fields populated."""
    feedback = CustomerFeedback(
        feedback_id="FB-123",
        client_id=sample_client_id,
        feedback_type=FeedbackType.FEATURE_REQUEST,
        source="support_ticket",
        submitter_email="user@example.com",
        submitter_name="John Doe",
        title="Need bulk export",
        content="Would like to export multiple reports at once",
        category="feature_request",
        subcategory="reporting",
        tags=["export", "bulk", "enhancement"],
        sentiment=SentimentType.POSITIVE,
        sentiment_score=0.7,
        priority=FeedbackPriority.HIGH,
        status=FeedbackStatus.IN_PROGRESS,
        impact_assessment="Requested by 5+ customers",
        assigned_to="product-team@company.com",
        follow_up_required=True,
        follow_up_by=date.today() + timedelta(days=7),
        resolution_notes="Feature added to roadmap"
    )

    assert feedback.subcategory == "reporting"
    assert len(feedback.tags) == 3
    assert feedback.priority == FeedbackPriority.HIGH
    assert feedback.follow_up_required == True


@pytest.mark.unit
def test_customer_feedback_title_length_validation():
    """Test that title respects max_length constraint."""
    long_title = "A" * 201  # Max is 200
    with pytest.raises(ValidationError) as exc_info:
        CustomerFeedback(
            feedback_id="FB-123",
            client_id="cs_1234_test",
            feedback_type=FeedbackType.GENERAL,
            source="email",
            submitter_email="user@example.com",
            submitter_name="John Doe",
            title=long_title,
            content="Test content",
            category="test",
            sentiment=SentimentType.NEUTRAL,
            sentiment_score=0.0
        )

    assert "title" in str(exc_info.value)


# ============================================================================
# NPSResponse Model Tests
# ============================================================================

@pytest.mark.unit
def test_nps_response_valid_creation(sample_client_id):
    """Test creating a valid NPSResponse."""
    response = NPSResponse(
        response_id="NPS-12345",
        client_id=sample_client_id,
        survey_id="SURVEY-Q4-2025",
        respondent_email="user@example.com",
        respondent_name="Jane Smith",
        score=9,
        category="promoter",
        sentiment=SentimentType.VERY_POSITIVE,
        sentiment_score=0.9,
        survey_sent_at=datetime.now() - timedelta(hours=24),
        response_time_hours=2.5
    )

    assert response.response_id == "NPS-12345"
    assert response.score == 9
    assert response.category == "promoter"


@pytest.mark.unit
def test_nps_response_invalid_id_format():
    """Test that invalid response_id format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        NPSResponse(
            response_id="INVALID-123",  # Should be NPS-
            client_id="cs_1234_test",
            survey_id="SURVEY-1",
            respondent_email="user@example.com",
            respondent_name="Jane Smith",
            score=8,
            category="passive",
            sentiment=SentimentType.POSITIVE,
            sentiment_score=0.6,
            survey_sent_at=datetime.now(),
            response_time_hours=1.0
        )

    assert "response_id" in str(exc_info.value)


@pytest.mark.unit
def test_nps_response_score_boundaries():
    """Test that NPS score respects 0-10 boundaries."""
    # Test minimum
    response = NPSResponse(
        response_id="NPS-123",
        client_id="cs_1234_test",
        survey_id="SURVEY-1",
        respondent_email="user@example.com",
        respondent_name="Jane Smith",
        score=0,
        category="detractor",
        sentiment=SentimentType.NEGATIVE,
        sentiment_score=-0.5,
        survey_sent_at=datetime.now(),
        response_time_hours=1.0
    )
    assert response.score == 0

    # Test maximum
    response = NPSResponse(
        response_id="NPS-124",
        client_id="cs_1234_test",
        survey_id="SURVEY-1",
        respondent_email="user@example.com",
        respondent_name="Jane Smith",
        score=10,
        category="promoter",
        sentiment=SentimentType.VERY_POSITIVE,
        sentiment_score=0.95,
        survey_sent_at=datetime.now(),
        response_time_hours=1.0
    )
    assert response.score == 10

    # Test below minimum
    with pytest.raises(ValidationError) as exc_info:
        NPSResponse(
            response_id="NPS-125",
            client_id="cs_1234_test",
            survey_id="SURVEY-1",
            respondent_email="user@example.com",
            respondent_name="Jane Smith",
            score=-1,
            category="detractor",
            sentiment=SentimentType.NEGATIVE,
            sentiment_score=-0.5,
            survey_sent_at=datetime.now(),
            response_time_hours=1.0
        )

    assert "score" in str(exc_info.value)


@pytest.mark.unit
def test_nps_response_category_validation_detractor():
    """Test NPS category validation for detractor (score 0-6)."""
    response = NPSResponse(
        response_id="NPS-123",
        client_id="cs_1234_test",
        survey_id="SURVEY-1",
        respondent_email="user@example.com",
        respondent_name="Jane Smith",
        score=5,
        category="detractor",
        sentiment=SentimentType.NEGATIVE,
        sentiment_score=-0.3,
        survey_sent_at=datetime.now(),
        response_time_hours=1.0
    )
    assert response.category == "detractor"


@pytest.mark.unit
def test_nps_response_category_validation_passive():
    """Test NPS category validation for passive (score 7-8)."""
    response = NPSResponse(
        response_id="NPS-123",
        client_id="cs_1234_test",
        survey_id="SURVEY-1",
        respondent_email="user@example.com",
        respondent_name="Jane Smith",
        score=7,
        category="passive",
        sentiment=SentimentType.NEUTRAL,
        sentiment_score=0.1,
        survey_sent_at=datetime.now(),
        response_time_hours=1.0
    )
    assert response.category == "passive"


@pytest.mark.unit
def test_nps_response_category_validation_promoter():
    """Test NPS category validation for promoter (score 9-10)."""
    response = NPSResponse(
        response_id="NPS-123",
        client_id="cs_1234_test",
        survey_id="SURVEY-1",
        respondent_email="user@example.com",
        respondent_name="Jane Smith",
        score=10,
        category="promoter",
        sentiment=SentimentType.VERY_POSITIVE,
        sentiment_score=0.95,
        survey_sent_at=datetime.now(),
        response_time_hours=1.0
    )
    assert response.category == "promoter"


@pytest.mark.unit
def test_nps_response_category_mismatch():
    """Test that mismatched category and score raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        NPSResponse(
            response_id="NPS-123",
            client_id="cs_1234_test",
            survey_id="SURVEY-1",
            respondent_email="user@example.com",
            respondent_name="Jane Smith",
            score=9,
            category="detractor",  # Wrong category for score 9
            sentiment=SentimentType.POSITIVE,
            sentiment_score=0.8,
            survey_sent_at=datetime.now(),
            response_time_hours=1.0
        )

    assert "Category" in str(exc_info.value)
    assert "does not match score" in str(exc_info.value)


@pytest.mark.unit
def test_nps_response_with_follow_up_questions(sample_client_id):
    """Test NPSResponse with follow-up questions and answers."""
    response = NPSResponse(
        response_id="NPS-123",
        client_id=sample_client_id,
        survey_id="SURVEY-1",
        respondent_email="user@example.com",
        respondent_name="Jane Smith",
        score=9,
        category="promoter",
        reason="Great product and excellent support",
        follow_up_question_1="What do you value most?",
        follow_up_answer_1="The customer support team",
        follow_up_question_2="What could we improve?",
        follow_up_answer_2="More integration options",
        sentiment=SentimentType.VERY_POSITIVE,
        sentiment_score=0.9,
        survey_sent_at=datetime.now() - timedelta(hours=24),
        response_time_hours=2.5
    )

    assert response.reason == "Great product and excellent support"
    assert response.follow_up_answer_1 == "The customer support team"
    assert response.follow_up_answer_2 == "More integration options"


# ============================================================================
# SentimentAnalysis Model Tests
# ============================================================================

@pytest.mark.unit
def test_sentiment_analysis_valid_creation(sample_client_id):
    """Test creating a valid SentimentAnalysis."""
    analysis = SentimentAnalysis(
        analysis_id="SA-2025Q4",
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 12, 31),
        total_feedback_items=50,
        feedback_by_type={"nps": 20, "csat": 15, "feedback": 15},
        overall_sentiment=SentimentType.POSITIVE,
        overall_sentiment_score=0.72,
        sentiment_distribution={
            "very_positive": 0.2,
            "positive": 0.5,
            "neutral": 0.2,
            "negative": 0.08,
            "very_negative": 0.02
        },
        sentiment_trend="improving"
    )

    assert analysis.analysis_id == "SA-2025Q4"
    assert analysis.total_feedback_items == 50
    assert analysis.overall_sentiment == SentimentType.POSITIVE
    assert analysis.overall_sentiment_score == 0.72


@pytest.mark.unit
def test_sentiment_analysis_sentiment_trend_validation():
    """Test that sentiment_trend must be one of allowed values."""
    for trend in ["improving", "stable", "declining", "unknown"]:
        analysis = SentimentAnalysis(
            analysis_id="SA-TEST",
            period_start=datetime(2025, 10, 1),
            period_end=datetime(2025, 10, 31),
            total_feedback_items=10,
            feedback_by_type={"nps": 10},
            overall_sentiment=SentimentType.POSITIVE,
            overall_sentiment_score=0.7,
            sentiment_distribution={"positive": 1.0},
            sentiment_trend=trend
        )
        assert analysis.sentiment_trend == trend

    # Invalid trend
    with pytest.raises(ValidationError) as exc_info:
        SentimentAnalysis(
            analysis_id="SA-TEST",
            period_start=datetime(2025, 10, 1),
            period_end=datetime(2025, 10, 31),
            total_feedback_items=10,
            feedback_by_type={"nps": 10},
            overall_sentiment=SentimentType.POSITIVE,
            overall_sentiment_score=0.7,
            sentiment_distribution={"positive": 1.0},
            sentiment_trend="invalid"
        )

    assert "sentiment_trend" in str(exc_info.value)


@pytest.mark.unit
def test_sentiment_analysis_with_themes(sample_client_id):
    """Test SentimentAnalysis with positive and negative themes."""
    top_positive = [
        {"theme": "support", "mentions": 15, "avg_sentiment": 0.9},
        {"theme": "ease_of_use", "mentions": 12, "avg_sentiment": 0.85}
    ]
    top_negative = [
        {"theme": "bugs", "mentions": 5, "avg_sentiment": -0.6},
        {"theme": "missing_features", "mentions": 3, "avg_sentiment": -0.4}
    ]

    analysis = SentimentAnalysis(
        analysis_id="SA-TEST",
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_feedback_items=30,
        feedback_by_type={"feedback": 30},
        overall_sentiment=SentimentType.POSITIVE,
        overall_sentiment_score=0.65,
        sentiment_distribution={"positive": 0.7, "negative": 0.3},
        sentiment_trend="stable",
        top_positive_themes=top_positive,
        top_negative_themes=top_negative
    )

    assert len(analysis.top_positive_themes) == 2
    assert len(analysis.top_negative_themes) == 2
    assert analysis.top_positive_themes[0]["theme"] == "support"


@pytest.mark.unit
def test_sentiment_analysis_nps_csat_scores(sample_client_id):
    """Test SentimentAnalysis with optional NPS and CSAT scores."""
    analysis = SentimentAnalysis(
        analysis_id="SA-TEST",
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_feedback_items=50,
        feedback_by_type={"nps": 30, "csat": 20},
        overall_sentiment=SentimentType.POSITIVE,
        overall_sentiment_score=0.7,
        sentiment_distribution={"positive": 0.8, "negative": 0.2},
        sentiment_trend="improving",
        nps_score=45,
        csat_score=4.2
    )

    assert analysis.nps_score == 45
    assert analysis.csat_score == 4.2


@pytest.mark.unit
def test_sentiment_analysis_nps_score_boundaries():
    """Test that NPS score respects -100 to 100 boundaries."""
    # Test valid NPS scores
    for nps in [-100, 0, 50, 100]:
        analysis = SentimentAnalysis(
            analysis_id="SA-TEST",
            period_start=datetime(2025, 10, 1),
            period_end=datetime(2025, 10, 31),
            total_feedback_items=10,
            feedback_by_type={"nps": 10},
            overall_sentiment=SentimentType.POSITIVE,
            overall_sentiment_score=0.7,
            sentiment_distribution={"positive": 1.0},
            sentiment_trend="stable",
            nps_score=nps
        )
        assert analysis.nps_score == nps


# ============================================================================
# SurveyTemplate Model Tests
# ============================================================================

@pytest.mark.unit
def test_survey_template_valid_creation():
    """Test creating a valid SurveyTemplate."""
    questions = [
        {
            "question_id": "Q1",
            "question_text": "How satisfied are you?",
            "question_type": "scale_1_5",
            "required": True
        }
    ]

    template = SurveyTemplate(
        template_id="TMPL-NPS-Q4",
        template_name="Quarterly NPS Survey",
        template_type=FeedbackType.NPS,
        description="Standard NPS survey for all customers",
        questions=questions
    )

    assert template.template_id == "TMPL-NPS-Q4"
    assert template.template_name == "Quarterly NPS Survey"
    assert template.template_type == FeedbackType.NPS
    assert len(template.questions) == 1


@pytest.mark.unit
def test_survey_template_questions_min_length():
    """Test that questions list must have at least one question."""
    with pytest.raises(ValidationError) as exc_info:
        SurveyTemplate(
            template_id="TMPL-TEST",
            template_name="Test Survey",
            template_type=FeedbackType.CSAT,
            description="Test",
            questions=[]  # Empty list should fail
        )

    assert "questions" in str(exc_info.value)


@pytest.mark.unit
def test_survey_template_with_targeting():
    """Test SurveyTemplate with targeting criteria."""
    questions = [
        {
            "question_id": "Q1",
            "question_text": "Rate our product",
            "question_type": "scale",
            "required": True
        }
    ]

    targeting = {
        "customer_tiers": ["professional", "enterprise"],
        "lifecycle_stages": ["active"],
        "min_tenure_days": 30
    }

    template = SurveyTemplate(
        template_id="TMPL-CSAT",
        template_name="Customer Satisfaction Survey",
        template_type=FeedbackType.CSAT,
        description="CSAT survey for active customers",
        questions=questions,
        targeting=targeting,
        frequency="monthly"
    )

    assert template.targeting["customer_tiers"] == ["professional", "enterprise"]
    assert template.frequency == "monthly"


@pytest.mark.unit
def test_survey_template_default_values():
    """Test that SurveyTemplate has correct default values."""
    questions = [
        {
            "question_id": "Q1",
            "question_text": "Test question",
            "question_type": "text",
            "required": False
        }
    ]

    template = SurveyTemplate(
        template_id="TMPL-TEST",
        template_name="Test Survey",
        template_type=FeedbackType.GENERAL,
        description="Test description",
        questions=questions
    )

    assert template.targeting == {}
    assert template.frequency == "one_time"
    assert template.active == True


@pytest.mark.unit
def test_survey_template_multiple_questions():
    """Test SurveyTemplate with multiple questions."""
    questions = [
        {
            "question_id": "Q1",
            "question_text": "How likely are you to recommend us?",
            "question_type": "scale_0_10",
            "required": True
        },
        {
            "question_id": "Q2",
            "question_text": "What is the reason for your score?",
            "question_type": "open_text",
            "required": True
        },
        {
            "question_id": "Q3",
            "question_text": "What do you value most?",
            "question_type": "open_text",
            "required": False
        }
    ]

    template = SurveyTemplate(
        template_id="TMPL-NPS",
        template_name="NPS Survey",
        template_type=FeedbackType.NPS,
        description="Standard NPS survey",
        questions=questions
    )

    assert len(template.questions) == 3
    assert template.questions[0]["required"] == True
    assert template.questions[2]["required"] == False
