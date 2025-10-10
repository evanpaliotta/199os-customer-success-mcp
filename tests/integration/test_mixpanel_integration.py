"""Integration Tests for Mixpanel Product Analytics Client

Tests the production-ready MixpanelClient implementation including:
- Event tracking with batching
- User profile management
- JQL query execution
- Circuit breaker pattern
- Retry logic
- Error handling
"""
import os
import json
import time
import base64
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pytest
import requests
from requests.exceptions import HTTPError, Timeout, ConnectionError

from src.integrations.mixpanel_client import MixpanelClient, CircuitBreaker


class TestCircuitBreaker:
    """Test circuit breaker pattern for API resilience"""

    def test_circuit_breaker_closed_state(self):
        """Circuit breaker should allow calls when closed"""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        def success_func():
            return "success"

        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == "closed"
        assert cb.failures == 0

    def test_circuit_breaker_opens_after_threshold(self):
        """Circuit breaker should open after failure threshold"""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        def failing_func():
            raise Exception("API Error")

        # Record 3 failures
        for i in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == "open"
        assert cb.failures == 3

    def test_circuit_breaker_blocks_when_open(self):
        """Circuit breaker should block calls when open"""
        cb = CircuitBreaker(failure_threshold=2, timeout=60)

        def failing_func():
            raise Exception("API Error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        # Should now block
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            cb.call(failing_func)

    def test_circuit_breaker_half_open_after_timeout(self):
        """Circuit breaker should enter half-open state after timeout"""
        cb = CircuitBreaker(failure_threshold=2, timeout=1)  # 1 second timeout

        def failing_func():
            raise Exception("API Error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == "open"

        # Wait for timeout
        time.sleep(1.1)

        # Next call should transition to half-open (but still fail)
        with pytest.raises(Exception, match="API Error"):
            cb.call(failing_func)

    def test_circuit_breaker_resets_on_success(self):
        """Circuit breaker should reset when call succeeds in half-open"""
        cb = CircuitBreaker(failure_threshold=2, timeout=1)

        def failing_func():
            raise Exception("API Error")

        def success_func():
            return "success"

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        # Wait for timeout
        time.sleep(1.1)

        # Successful call should reset
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == "closed"
        assert cb.failures == 0


class TestMixpanelClientInitialization:
    """Test Mixpanel client initialization and configuration"""

    def test_init_with_env_vars(self):
        """Should initialize with environment variables"""
        with patch.dict(os.environ, {
            'MIXPANEL_PROJECT_TOKEN': 'test_token_123',
            'MIXPANEL_API_SECRET': 'test_secret_456'
        }):
            client = MixpanelClient()

            assert client.project_token == 'test_token_123'
            assert client.api_secret == 'test_secret_456'
            assert client.client is True
            assert client.batch_size == 50
            assert client.flush_interval == 10

    def test_init_with_explicit_credentials(self):
        """Should initialize with explicit credentials"""
        client = MixpanelClient(
            project_token='explicit_token',
            api_secret='explicit_secret',
            batch_size=100,
            flush_interval=5
        )

        assert client.project_token == 'explicit_token'
        assert client.api_secret == 'explicit_secret'
        assert client.batch_size == 100
        assert client.flush_interval == 5

    def test_init_without_credentials(self):
        """Should handle missing credentials gracefully"""
        with patch.dict(os.environ, {}, clear=True):
            client = MixpanelClient()

            assert client.project_token is None
            assert client.client is None

    def test_http_session_created(self):
        """Should create HTTP session with retry strategy"""
        with patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'test_token'}):
            client = MixpanelClient()

            assert hasattr(client, 'session')
            assert isinstance(client.session, requests.Session)

    def test_circuit_breaker_initialized(self):
        """Should initialize circuit breaker"""
        with patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'test_token'}):
            client = MixpanelClient()

            assert hasattr(client, 'circuit_breaker')
            assert isinstance(client.circuit_breaker, CircuitBreaker)


class TestMixpanelEventTracking:
    """Test event tracking functionality"""

    @pytest.fixture
    def mock_client(self):
        """Create client with mocked HTTP requests"""
        with patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'test_token'}):
            client = MixpanelClient(batch_size=2, flush_interval=10)

            # Mock the session.post method
            with patch.object(client.session, 'post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": 1}
                mock_post.return_value = mock_response

                yield client, mock_post

    def test_track_event_basic(self, mock_client):
        """Should track a basic event"""
        client, mock_post = mock_client

        result = client.track_event(
            user_id="user_123",
            event_name="page_view"
        )

        assert result["status"] == "success"
        assert result["event_tracked"] is True
        assert len(client.event_buffer) == 1

    def test_track_event_with_properties(self, mock_client):
        """Should track event with custom properties"""
        client, mock_post = mock_client

        result = client.track_event(
            user_id="user_123",
            event_name="feature_used",
            properties={
                "feature_name": "dashboard",
                "plan": "enterprise",
                "session_id": "sess_456"
            }
        )

        assert result["status"] == "success"
        assert result["event_tracked"] is True

        # Check event structure
        event = list(client.event_buffer)[0]
        assert event["event"] == "feature_used"
        assert event["properties"]["distinct_id"] == "user_123"
        assert event["properties"]["feature_name"] == "dashboard"

    def test_track_event_with_timestamp(self, mock_client):
        """Should track event with custom timestamp"""
        client, mock_post = mock_client

        custom_time = datetime(2025, 10, 1, 12, 0, 0)
        result = client.track_event(
            user_id="user_123",
            event_name="login",
            timestamp=custom_time
        )

        assert result["status"] == "success"
        event = list(client.event_buffer)[0]
        assert event["properties"]["time"] == int(custom_time.timestamp())

    def test_batch_auto_flush(self, mock_client):
        """Should auto-flush when batch size reached"""
        client, mock_post = mock_client

        # Track 2 events (batch_size=2)
        client.track_event("user_1", "event_1")
        client.track_event("user_2", "event_2")

        # Should have auto-flushed
        assert mock_post.called
        assert len(client.event_buffer) == 0

    def test_track_event_without_config(self):
        """Should handle tracking without configuration"""
        with patch.dict(os.environ, {}, clear=True):
            client = MixpanelClient()

            result = client.track_event("user_123", "test_event")

            assert result["status"] == "error"
            assert result["event_tracked"] is False
            assert "not configured" in result["error"]

    def test_track_usage_engagement_convenience(self, mock_client):
        """Should track usage engagement events"""
        client, mock_post = mock_client

        result = client.track_usage_engagement(
            client_id="client_abc",
            event_type="feature_usage",
            properties={"feature": "reports"}
        )

        assert result["status"] == "success"
        event = list(client.event_buffer)[0]
        assert event["event"] == "cs_feature_usage"
        assert event["properties"]["client_id"] == "client_abc"
        assert event["properties"]["event_type"] == "feature_usage"


class TestMixpanelBatchOperations:
    """Test batch event tracking and flushing"""

    @pytest.fixture
    def client_with_buffer(self):
        """Create client with events in buffer"""
        with patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'test_token'}):
            client = MixpanelClient(batch_size=100, flush_interval=10)

            # Add events to buffer without flushing
            for i in range(5):
                client.event_buffer.append({
                    "event": f"test_event_{i}",
                    "properties": {
                        "distinct_id": f"user_{i}",
                        "token": "test_token"
                    }
                })

            yield client

    def test_flush_empty_buffer(self):
        """Should handle flushing empty buffer"""
        with patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'test_token'}):
            client = MixpanelClient()

            result = client.flush()

            assert result["status"] == "success"
            assert result["events_flushed"] == 0

    def test_flush_with_events(self, client_with_buffer):
        """Should flush buffered events"""
        client = client_with_buffer

        with patch.object(client.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": 1}
            mock_post.return_value = mock_response

            result = client.flush()

            assert result["status"] == "success"
            assert result["events_flushed"] == 5
            assert len(client.event_buffer) == 0
            assert mock_post.called

    def test_flush_payload_encoding(self, client_with_buffer):
        """Should properly encode events for Mixpanel API"""
        client = client_with_buffer

        with patch.object(client.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": 1}
            mock_post.return_value = mock_response

            client.flush()

            # Check that post was called with base64 encoded data
            call_args = mock_post.call_args
            assert 'data' in call_args[1]

            # Decode and verify
            encoded_data = call_args[1]['data']['data']
            decoded = json.loads(base64.b64decode(encoded_data))
            assert len(decoded) == 5
            assert decoded[0]['event'] == 'test_event_0'

    def test_flush_network_error(self, client_with_buffer):
        """Should handle network errors during flush"""
        client = client_with_buffer

        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Network error")

            result = client.flush()

            assert result["status"] == "error"
            assert result["events_flushed"] == 0
            # Events should remain in buffer on error
            assert len(client.event_buffer) == 5

    def test_flush_api_error(self, client_with_buffer):
        """Should handle API errors during flush"""
        client = client_with_buffer

        with patch.object(client.session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.raise_for_status.side_effect = HTTPError("Bad request")
            mock_post.return_value = mock_response

            result = client.flush()

            assert result["status"] == "error"
            assert "Bad request" in str(result["error"])


class TestMixpanelProfileManagement:
    """Test user profile management"""

    @pytest.fixture
    def mock_client(self):
        """Create client with mocked HTTP requests"""
        with patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'test_token'}):
            client = MixpanelClient()

            with patch.object(client.session, 'post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": 1}
                mock_post.return_value = mock_response

                yield client, mock_post

    def test_set_profile_basic(self, mock_client):
        """Should set user profile properties"""
        client, mock_post = mock_client

        result = client.set_profile(
            user_id="user_123",
            properties={
                "name": "John Doe",
                "email": "john@example.com",
                "plan": "enterprise"
            }
        )

        assert result["status"] == "success"
        assert result["profile_updated"] is True
        assert result["user_id"] == "user_123"
        assert result["properties_set"] == 3
        assert mock_post.called

    def test_set_profile_with_ip(self, mock_client):
        """Should set profile with IP address for geolocation"""
        client, mock_post = mock_client

        result = client.set_profile(
            user_id="user_123",
            properties={"name": "John"},
            ip_address="192.168.1.1"
        )

        assert result["status"] == "success"
        assert result["profile_updated"] is True

    def test_set_profile_payload_structure(self, mock_client):
        """Should create proper profile update payload"""
        client, mock_post = mock_client

        client.set_profile(
            user_id="user_123",
            properties={"score": 85}
        )

        # Verify payload structure
        call_args = mock_post.call_args
        encoded_data = call_args[1]['data']['data']
        decoded = json.loads(base64.b64decode(encoded_data))

        assert len(decoded) == 1
        assert decoded[0]['$token'] == 'test_token'
        assert decoded[0]['$distinct_id'] == 'user_123'
        assert decoded[0]['$set'] == {'score': 85}

    def test_increment_profile_properties(self, mock_client):
        """Should increment numeric profile properties"""
        client, mock_post = mock_client

        result = client.increment(
            user_id="user_123",
            properties={
                "login_count": 1,
                "api_calls": 50,
                "errors": -1
            }
        )

        assert result["status"] == "success"
        assert result["profile_incremented"] is True
        assert result["increments"] == {"login_count": 1, "api_calls": 50, "errors": -1}

    def test_increment_payload_structure(self, mock_client):
        """Should create proper increment payload"""
        client, mock_post = mock_client

        client.increment(
            user_id="user_123",
            properties={"sessions": 1}
        )

        # Verify payload structure
        call_args = mock_post.call_args
        encoded_data = call_args[1]['data']['data']
        decoded = json.loads(base64.b64decode(encoded_data))

        assert decoded[0]['$add'] == {'sessions': 1}

    def test_profile_operations_without_config(self):
        """Should handle profile operations without configuration"""
        with patch.dict(os.environ, {}, clear=True):
            client = MixpanelClient()

            result = client.set_profile("user_123", {"name": "John"})
            assert result["status"] == "error"
            assert result["profile_updated"] is False

            result = client.increment("user_123", {"count": 1})
            assert result["status"] == "error"
            assert result["profile_incremented"] is False


class TestMixpanelQueryAPI:
    """Test JQL query API functionality"""

    @pytest.fixture
    def mock_client(self):
        """Create client with mocked HTTP requests"""
        with patch.dict(os.environ, {
            'MIXPANEL_PROJECT_TOKEN': 'test_token',
            'MIXPANEL_API_SECRET': 'test_secret'
        }):
            client = MixpanelClient()

            with patch.object(client.session, 'post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = [
                    {"key": ["client_1"], "value": 150},
                    {"key": ["client_2"], "value": 200}
                ]
                mock_post.return_value = mock_response

                yield client, mock_post

    def test_get_events_basic_query(self, mock_client):
        """Should execute basic JQL query"""
        client, mock_post = mock_client

        jql_query = """
        function main() {
            return Events({
                from_date: '2025-10-01',
                to_date: '2025-10-10'
            })
            .groupBy(['properties.client_id'], mixpanel.reducer.count());
        }
        """

        result = client.get_events(jql_query)

        assert result["status"] == "success"
        assert result["query_executed"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["key"] == ["client_1"]
        assert result["data"][0]["value"] == 150

    def test_get_events_with_params(self, mock_client):
        """Should execute query with parameters"""
        client, mock_post = mock_client

        jql_query = "function main() { return Events(params); }"
        params = {"from_date": "2025-10-01", "to_date": "2025-10-10"}

        result = client.get_events(jql_query, params)

        assert result["status"] == "success"
        assert result["query_executed"] is True
        assert mock_post.called

        # Verify params were included
        call_args = mock_post.call_args
        assert 'json' in call_args[1]
        assert call_args[1]['json']['from_date'] == '2025-10-01'

    def test_get_events_authentication(self, mock_client):
        """Should use API secret for authentication"""
        client, mock_post = mock_client

        client.get_events("function main() { return Events({}); }")

        # Verify auth was used
        call_args = mock_post.call_args
        assert 'auth' in call_args[1]
        assert call_args[1]['auth'] == ('test_secret', '')

    def test_get_events_without_secret(self):
        """Should fail gracefully without API secret"""
        with patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'test_token'}):
            client = MixpanelClient()

            result = client.get_events("function main() {}")

            assert result["status"] == "error"
            assert result["query_executed"] is False
            assert "API secret required" in result["error"]

    def test_get_events_api_error(self, mock_client):
        """Should handle API errors during query"""
        client, mock_post = mock_client

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid JQL syntax"
        mock_response.raise_for_status.side_effect = HTTPError("Bad request")
        mock_post.return_value = mock_response

        result = client.get_events("invalid query")

        assert result["status"] == "error"
        assert result["query_executed"] is False
        assert "HTTP 400" in result["error"]


class TestMixpanelRetryLogic:
    """Test retry and resilience patterns"""

    @pytest.fixture
    def mock_client(self):
        """Create client for retry testing"""
        with patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'test_token'}):
            client = MixpanelClient()
            yield client

    def test_retry_on_timeout(self, mock_client):
        """Should retry on timeout errors"""
        client = mock_client

        call_count = 0
        def timeout_then_success(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Timeout("Request timeout")
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": 1}
            return mock_response

        with patch.object(client.session, 'post', side_effect=timeout_then_success):
            client.track_event("user_123", "test_event")
            result = client.flush()

            # Should eventually succeed after retries
            assert result["status"] == "success"

    def test_circuit_breaker_with_flush(self, mock_client):
        """Should use circuit breaker for flush operations"""
        client = mock_client

        # Add events to buffer
        for i in range(3):
            client.event_buffer.append({"event": f"test_{i}", "properties": {}})

        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = Exception("API Error")

            # Multiple failed flushes should open circuit breaker
            for i in range(6):
                client.flush()

            # Circuit should be open
            assert client.circuit_breaker.state == "open"

    def test_circuit_breaker_with_profile_update(self, mock_client):
        """Should use circuit breaker for profile operations"""
        client = mock_client

        with patch.object(client.session, 'post') as mock_post:
            mock_post.side_effect = Exception("API Error")

            # Multiple failed profile updates should open circuit
            for i in range(6):
                result = client.set_profile("user_123", {"name": "Test"})
                if i >= 5:
                    assert "Circuit breaker is OPEN" in str(result.get("error", ""))


class TestMixpanelClientCleanup:
    """Test client cleanup and resource management"""

    def test_close_flushes_buffer(self):
        """Should flush events on close"""
        with patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'test_token'}):
            client = MixpanelClient()

            # Add events
            client.event_buffer.append({"event": "test", "properties": {}})

            with patch.object(client, 'flush') as mock_flush:
                client.close()

                assert mock_flush.called

    def test_close_closes_session(self):
        """Should close HTTP session"""
        with patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'test_token'}):
            client = MixpanelClient()

            with patch.object(client.session, 'close') as mock_close:
                client.close()

                assert mock_close.called

    def test_close_without_config(self):
        """Should handle close without configuration"""
        with patch.dict(os.environ, {}, clear=True):
            client = MixpanelClient()

            # Should not raise error
            client.close()


class TestMixpanelIntegrationEndToEnd:
    """End-to-end integration tests"""

    def test_complete_tracking_workflow(self):
        """Test complete event tracking workflow"""
        with patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'test_token'}):
            client = MixpanelClient(batch_size=3)

            with patch.object(client.session, 'post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": 1}
                mock_post.return_value = mock_response

                # Track multiple events
                for i in range(5):
                    result = client.track_event(
                        user_id=f"user_{i}",
                        event_name="feature_used",
                        properties={"feature": f"feature_{i}"}
                    )
                    assert result["event_tracked"] is True

                # Should have auto-flushed once (3 events) and have 2 buffered
                assert len(client.event_buffer) == 2

                # Manual flush remaining events
                result = client.flush()
                assert result["events_flushed"] == 2
                assert len(client.event_buffer) == 0

    def test_complete_profile_workflow(self):
        """Test complete profile management workflow"""
        with patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'test_token'}):
            client = MixpanelClient()

            with patch.object(client.session, 'post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": 1}
                mock_post.return_value = mock_response

                # Set initial profile
                result = client.set_profile(
                    user_id="user_123",
                    properties={
                        "name": "John Doe",
                        "email": "john@example.com",
                        "signup_date": "2025-01-01"
                    }
                )
                assert result["profile_updated"] is True

                # Increment counters
                result = client.increment(
                    user_id="user_123",
                    properties={"login_count": 1}
                )
                assert result["profile_incremented"] is True

                # Update profile again
                result = client.set_profile(
                    user_id="user_123",
                    properties={"last_login": "2025-10-10"}
                )
                assert result["profile_updated"] is True

    def test_mixed_operations(self):
        """Test mixing events and profile operations"""
        with patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'test_token'}):
            client = MixpanelClient(batch_size=10)

            with patch.object(client.session, 'post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": 1}
                mock_post.return_value = mock_response

                # Track event
                client.track_event("user_123", "login")

                # Update profile
                client.set_profile("user_123", {"last_login": "2025-10-10"})

                # Track more events
                client.track_event("user_123", "feature_used", {"feature": "dashboard"})

                # Increment
                client.increment("user_123", {"login_count": 1})

                # Flush events
                result = client.flush()
                assert result["status"] == "success"

                # Close cleanly
                client.close()
