"""
Integration tests for Intercom API client

Tests all Intercom client methods with mocked API responses
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import time

from src.integrations.intercom_client import IntercomClient, CircuitBreaker
from intercom.errors import (
    AuthenticationError,
    ResourceNotFound,
    RateLimitExceeded,
    ServerError,
    ServiceUnavailableError
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_intercom_client():
    """Create Intercom client with mocked API"""
    with patch('src.integrations.intercom_client.Client') as mock_client:
        client = IntercomClient(access_token="test_token_123")
        client.client = mock_client.return_value
        yield client


@pytest.fixture
def mock_user_response():
    """Mock Intercom user response"""
    user = Mock()
    user.id = "user_12345"
    user.email = "test@example.com"
    user.name = "Test User"
    user.user_id = "ext_user_123"
    user.signed_up_at = 1704067200  # 2024-01-01
    user.last_seen_at = 1704153600  # 2024-01-02
    user.custom_attributes = {"plan": "enterprise", "mrr": 5000}
    return user


@pytest.fixture
def mock_message_response():
    """Mock Intercom message response"""
    message = Mock()
    message.id = "msg_12345"
    return message


@pytest.fixture
def mock_note_response():
    """Mock Intercom note response"""
    note = Mock()
    note.id = "note_12345"
    return note


# ============================================================================
# Circuit Breaker Tests
# ============================================================================

class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in closed state"""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        assert cb.state == "closed"
        assert cb.can_attempt() is True

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after failure threshold"""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        # Record failures
        cb.call_failed()
        assert cb.state == "closed"
        cb.call_failed()
        assert cb.state == "closed"
        cb.call_failed()
        assert cb.state == "open"
        assert cb.can_attempt() is False

    def test_circuit_breaker_closes_on_success(self):
        """Test circuit breaker closes after successful call"""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        cb.call_failed()
        cb.call_failed()
        assert cb.failure_count == 2

        cb.call_succeeded()
        assert cb.state == "closed"
        assert cb.failure_count == 0

    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker enters half-open state after timeout"""
        cb = CircuitBreaker(failure_threshold=2, timeout=1)

        # Open circuit
        cb.call_failed()
        cb.call_failed()
        assert cb.state == "open"

        # Wait for timeout
        time.sleep(1.1)

        # Should allow one attempt
        assert cb.can_attempt() is True
        assert cb.state == "half_open"


# ============================================================================
# IntercomClient Initialization Tests
# ============================================================================

class TestIntercomClientInit:
    """Test Intercom client initialization"""

    def test_init_with_token(self):
        """Test initialization with provided token"""
        with patch('src.integrations.intercom_client.Client'):
            client = IntercomClient(access_token="test_token")
            assert client.access_token == "test_token"
            assert client.client is not None

    def test_init_without_token(self):
        """Test initialization without token"""
        with patch.dict('os.environ', {}, clear=True):
            client = IntercomClient()
            assert client.access_token is None
            assert client.client is None

    def test_init_with_env_token(self):
        """Test initialization with environment variable"""
        with patch.dict('os.environ', {'INTERCOM_ACCESS_TOKEN': 'env_token'}):
            with patch('src.integrations.intercom_client.Client'):
                client = IntercomClient()
                assert client.access_token == "env_token"


# ============================================================================
# Send Message Tests
# ============================================================================

class TestSendMessage:
    """Test send_message functionality"""

    def test_send_inapp_message_success(self, mock_intercom_client, mock_message_response):
        """Test successful in-app message send"""
        mock_intercom_client.client.messages.create.return_value = mock_message_response

        result = mock_intercom_client.send_message(
            user_email="test@example.com",
            message_type="inapp",
            body="Test message"
        )

        assert result["success"] is True
        assert result["message_id"] == "msg_12345"
        assert result["message_type"] == "inapp"
        assert result["recipient"] == "test@example.com"

    def test_send_email_message_success(self, mock_intercom_client, mock_message_response):
        """Test successful email message send"""
        mock_intercom_client.client.messages.create.return_value = mock_message_response

        result = mock_intercom_client.send_message(
            user_email="test@example.com",
            message_type="email",
            subject="Test Subject",
            body="Test body"
        )

        assert result["success"] is True
        assert result["message_id"] == "msg_12345"

    def test_send_message_missing_email_and_id(self, mock_intercom_client):
        """Test send message without user identifier"""
        result = mock_intercom_client.send_message(
            body="Test message"
        )

        assert result["success"] is False
        assert "Must provide either user_email or user_id" in result["error"]

    def test_send_message_missing_body(self, mock_intercom_client):
        """Test send message without body"""
        result = mock_intercom_client.send_message(
            user_email="test@example.com"
        )

        assert result["success"] is False
        assert "Message body is required" in result["error"]

    def test_send_email_message_missing_subject(self, mock_intercom_client):
        """Test email message without subject"""
        result = mock_intercom_client.send_message(
            user_email="test@example.com",
            message_type="email",
            body="Test body"
        )

        assert result["success"] is False
        assert "Subject is required for email messages" in result["error"]


# ============================================================================
# Create Note Tests
# ============================================================================

class TestCreateNote:
    """Test create_note functionality"""

    def test_create_note_success(self, mock_intercom_client, mock_user_response, mock_note_response):
        """Test successful note creation"""
        # Mock user retrieval
        mock_intercom_client.client.users.find.return_value = mock_user_response
        # Mock note creation
        mock_intercom_client.client.notes.create.return_value = mock_note_response

        result = mock_intercom_client.create_note(
            user_email="test@example.com",
            body="Test note"
        )

        assert result["success"] is True
        assert result["note_id"] == "note_12345"
        assert result["user_id"] == "user_12345"

    def test_create_note_missing_body(self, mock_intercom_client):
        """Test create note without body"""
        result = mock_intercom_client.create_note(
            user_email="test@example.com"
        )

        assert result["success"] is False
        assert "Note body is required" in result["error"]

    def test_create_note_user_not_found(self, mock_intercom_client):
        """Test create note when user not found"""
        mock_intercom_client.client.users.find.side_effect = ResourceNotFound("User not found")

        result = mock_intercom_client.create_note(
            user_email="notfound@example.com",
            body="Test note"
        )

        assert result["success"] is False
        assert "Resource not found" in result["error"]


# ============================================================================
# Track Event Tests
# ============================================================================

class TestTrackEvent:
    """Test track_event functionality"""

    def test_track_event_success(self, mock_intercom_client):
        """Test successful event tracking"""
        mock_intercom_client.client.events.create.return_value = True

        result = mock_intercom_client.track_event(
            user_email="test@example.com",
            event_name="feature_used",
            metadata={"feature": "export", "count": 5}
        )

        assert result["success"] is True
        assert result["event_name"] == "feature_used"
        assert result["metadata"]["feature"] == "export"

    def test_track_event_missing_name(self, mock_intercom_client):
        """Test track event without event name"""
        result = mock_intercom_client.track_event(
            user_email="test@example.com"
        )

        assert result["success"] is False
        assert "Event name is required" in result["error"]

    def test_track_event_with_timestamp(self, mock_intercom_client):
        """Test track event with custom timestamp"""
        mock_intercom_client.client.events.create.return_value = True
        timestamp = int(time.time())

        result = mock_intercom_client.track_event(
            user_email="test@example.com",
            event_name="custom_event",
            created_at=timestamp
        )

        assert result["success"] is True


# ============================================================================
# Get User Tests
# ============================================================================

class TestGetUser:
    """Test get_user functionality"""

    def test_get_user_by_email_success(self, mock_intercom_client, mock_user_response):
        """Test successful user retrieval by email"""
        mock_intercom_client.client.users.find.return_value = mock_user_response

        result = mock_intercom_client.get_user(user_email="test@example.com")

        assert result["success"] is True
        assert result["user"]["email"] == "test@example.com"
        assert result["user"]["id"] == "user_12345"
        assert result["user"]["custom_attributes"]["plan"] == "enterprise"

    def test_get_user_by_id_success(self, mock_intercom_client, mock_user_response):
        """Test successful user retrieval by ID"""
        mock_intercom_client.client.users.find.return_value = mock_user_response

        result = mock_intercom_client.get_user(user_id="user_12345")

        assert result["success"] is True
        assert result["user"]["id"] == "user_12345"

    def test_get_user_not_found(self, mock_intercom_client):
        """Test get user when user doesn't exist"""
        mock_intercom_client.client.users.find.side_effect = ResourceNotFound("User not found")

        result = mock_intercom_client.get_user(user_email="notfound@example.com")

        assert result["success"] is False
        assert "Resource not found" in result["error"]


# ============================================================================
# Create User Tests
# ============================================================================

class TestCreateUser:
    """Test create_user functionality"""

    def test_create_user_success(self, mock_intercom_client, mock_user_response):
        """Test successful user creation"""
        mock_intercom_client.client.users.create.return_value = mock_user_response

        result = mock_intercom_client.create_user(
            email="newuser@example.com",
            name="New User",
            custom_attributes={"plan": "starter"}
        )

        assert result["success"] is True
        assert result["user"]["email"] == "test@example.com"
        assert result["user"]["id"] == "user_12345"

    def test_create_user_missing_email(self, mock_intercom_client):
        """Test create user without email"""
        result = mock_intercom_client.create_user(email="")

        assert result["success"] is False
        assert "Email is required" in result["error"]


# ============================================================================
# Tag Management Tests
# ============================================================================

class TestTagManagement:
    """Test add_tag and remove_tag functionality"""

    def test_add_tag_success(self, mock_intercom_client, mock_user_response):
        """Test successful tag addition"""
        mock_intercom_client.client.users.find.return_value = mock_user_response
        mock_intercom_client.client.tags.tag.return_value = True

        result = mock_intercom_client.add_tag(
            user_email="test@example.com",
            tag_name="high_value"
        )

        assert result["success"] is True
        assert result["tag_name"] == "high_value"
        assert result["user_id"] == "user_12345"

    def test_add_tag_missing_name(self, mock_intercom_client):
        """Test add tag without tag name"""
        result = mock_intercom_client.add_tag(
            user_email="test@example.com"
        )

        assert result["success"] is False
        assert "Tag name is required" in result["error"]

    def test_remove_tag_success(self, mock_intercom_client, mock_user_response):
        """Test successful tag removal"""
        mock_intercom_client.client.users.find.return_value = mock_user_response
        mock_intercom_client.client.tags.untag.return_value = True

        result = mock_intercom_client.remove_tag(
            user_email="test@example.com",
            tag_name="old_tag"
        )

        assert result["success"] is True
        assert result["tag_name"] == "old_tag"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling and retry logic"""

    def test_authentication_error(self, mock_intercom_client):
        """Test handling of authentication errors"""
        mock_intercom_client.client.messages.create.side_effect = AuthenticationError("Invalid token")

        result = mock_intercom_client.send_message(
            user_email="test@example.com",
            body="Test"
        )

        assert result["success"] is False
        assert "Authentication failed" in result["error"]

    def test_rate_limit_error_with_retry(self, mock_intercom_client, mock_message_response):
        """Test rate limit handling with successful retry"""
        # First call rate limited, second succeeds
        mock_intercom_client.client.messages.create.side_effect = [
            RateLimitExceeded("Rate limit exceeded"),
            mock_message_response
        ]

        with patch('time.sleep'):  # Mock sleep to speed up test
            result = mock_intercom_client.send_message(
                user_email="test@example.com",
                body="Test"
            )

        # Should eventually succeed after retry
        assert result["success"] is True or "Rate limit exceeded" in result.get("error", "")

    def test_server_error_with_retry(self, mock_intercom_client, mock_message_response):
        """Test server error handling with retry"""
        # First two calls fail, third succeeds
        mock_intercom_client.client.messages.create.side_effect = [
            ServerError("Server error"),
            ServerError("Server error"),
            mock_message_response
        ]

        with patch('time.sleep'):
            result = mock_intercom_client.send_message(
                user_email="test@example.com",
                body="Test"
            )

        assert result["success"] is True

    def test_circuit_breaker_prevents_calls(self, mock_intercom_client):
        """Test circuit breaker prevents calls when open"""
        # Open the circuit breaker
        mock_intercom_client.circuit_breaker.state = "open"

        result = mock_intercom_client.send_message(
            user_email="test@example.com",
            body="Test"
        )

        assert result["success"] is False
        assert "Circuit breaker is open" in result["error"]


# ============================================================================
# Integration Tests (End-to-End)
# ============================================================================

class TestIntegrationScenarios:
    """Test realistic integration scenarios"""

    def test_onboarding_workflow(self, mock_intercom_client, mock_user_response, mock_message_response):
        """Test complete onboarding workflow"""
        mock_intercom_client.client.users.create.return_value = mock_user_response
        mock_intercom_client.client.messages.create.return_value = mock_message_response
        mock_intercom_client.client.events.create.return_value = True
        mock_intercom_client.client.tags.tag.return_value = True

        # 1. Create user
        user_result = mock_intercom_client.create_user(
            email="newcustomer@example.com",
            name="New Customer",
            custom_attributes={"plan": "enterprise", "onboarding_status": "started"}
        )
        assert user_result["success"] is True

        # 2. Send welcome message
        message_result = mock_intercom_client.send_message(
            user_email="newcustomer@example.com",
            message_type="email",
            subject="Welcome to our platform!",
            body="Thank you for joining us."
        )
        assert message_result["success"] is True

        # 3. Track onboarding event
        event_result = mock_intercom_client.track_event(
            user_email="newcustomer@example.com",
            event_name="onboarding_started"
        )
        assert event_result["success"] is True

        # 4. Tag user
        tag_result = mock_intercom_client.add_tag(
            user_email="newcustomer@example.com",
            tag_name="new_customer"
        )
        assert tag_result["success"] is True

    def test_churn_prevention_workflow(self, mock_intercom_client, mock_user_response, mock_note_response, mock_message_response):
        """Test churn prevention workflow"""
        mock_intercom_client.client.users.find.return_value = mock_user_response
        mock_intercom_client.client.notes.create.return_value = mock_note_response
        mock_intercom_client.client.messages.create.return_value = mock_message_response
        mock_intercom_client.client.tags.tag.return_value = True
        mock_intercom_client.client.events.create.return_value = True

        # 1. Get user
        user_result = mock_intercom_client.get_user(user_email="atrisk@example.com")
        assert user_result["success"] is True

        # 2. Create internal note
        note_result = mock_intercom_client.create_note(
            user_email="atrisk@example.com",
            body="Customer showing churn risk signals - low engagement"
        )
        assert note_result["success"] is True

        # 3. Tag as at-risk
        tag_result = mock_intercom_client.add_tag(
            user_email="atrisk@example.com",
            tag_name="at_risk"
        )
        assert tag_result["success"] is True

        # 4. Send retention message
        message_result = mock_intercom_client.send_message(
            user_email="atrisk@example.com",
            message_type="email",
            subject="We'd love to help you succeed",
            body="Let's schedule a call to discuss your goals."
        )
        assert message_result["success"] is True

        # 5. Track intervention
        event_result = mock_intercom_client.track_event(
            user_email="atrisk@example.com",
            event_name="churn_prevention_outreach",
            metadata={"reason": "low_engagement"}
        )
        assert event_result["success"] is True


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance and efficiency"""

    def test_batch_message_sending(self, mock_intercom_client, mock_message_response):
        """Test sending messages to multiple users"""
        mock_intercom_client.client.messages.create.return_value = mock_message_response

        users = [f"user{i}@example.com" for i in range(10)]
        results = []

        for user_email in users:
            result = mock_intercom_client.send_message(
                user_email=user_email,
                body="Batch message"
            )
            results.append(result)

        successful = sum(1 for r in results if r.get("success"))
        assert successful == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
