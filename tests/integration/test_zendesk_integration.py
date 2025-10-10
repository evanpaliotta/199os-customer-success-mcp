"""
Integration tests for Zendesk client
Tests real API interactions with mocked responses
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.integrations.zendesk_client import ZendeskClient, CircuitBreaker


class TestCircuitBreaker:
    """Test circuit breaker pattern"""

    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state allows calls"""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        def successful_function():
            return "success"

        result = cb.call(successful_function)
        assert result == "success"
        assert cb.state == "closed"
        assert cb.failure_count == 0

    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures"""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)

        def failing_function():
            raise Exception("API Error")

        # First 3 failures
        for i in range(3):
            with pytest.raises(Exception):
                cb.call(failing_function)

        assert cb.state == "open"
        assert cb.failure_count == 3

    def test_circuit_breaker_blocks_when_open(self):
        """Test circuit breaker blocks calls when open"""
        cb = CircuitBreaker(failure_threshold=2, timeout=60)

        def failing_function():
            raise Exception("API Error")

        # Cause circuit to open
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_function)

        # Should now be blocked
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            cb.call(failing_function)


class TestZendeskClientInitialization:
    """Test Zendesk client initialization"""

    @patch.dict('os.environ', {
        'ZENDESK_SUBDOMAIN': 'test',
        'ZENDESK_EMAIL': 'test@example.com',
        'ZENDESK_API_TOKEN': 'test-token'
    })
    @patch('src.integrations.zendesk_client.Zenpy')
    def test_init_with_valid_credentials(self, mock_zenpy):
        """Test initialization with valid credentials"""
        mock_client = Mock()
        mock_client.users.me.return_value = {'id': 123}
        mock_zenpy.return_value = mock_client

        client = ZendeskClient()

        assert client.subdomain == 'test'
        assert client.email == 'test@example.com'
        assert client.token == 'test-token'
        assert client.client is not None

    @patch.dict('os.environ', {}, clear=True)
    def test_init_without_credentials(self):
        """Test graceful degradation without credentials"""
        client = ZendeskClient()

        assert client.client is None
        assert client.subdomain is None

    @patch.dict('os.environ', {
        'ZENDESK_SUBDOMAIN': 'test',
        'ZENDESK_EMAIL': 'test@example.com',
        'ZENDESK_API_TOKEN': 'test-token'
    })
    @patch('src.integrations.zendesk_client.Zenpy')
    def test_init_with_connection_error(self, mock_zenpy):
        """Test initialization handles connection errors"""
        mock_client = Mock()
        mock_client.users.me.side_effect = Exception("Connection failed")
        mock_zenpy.return_value = mock_client

        client = ZendeskClient()

        # Should degrade gracefully
        assert client.client is None


class TestZendeskTicketCreation:
    """Test ticket creation"""

    @patch.dict('os.environ', {
        'ZENDESK_SUBDOMAIN': 'test',
        'ZENDESK_EMAIL': 'test@example.com',
        'ZENDESK_API_TOKEN': 'test-token'
    })
    @patch('src.integrations.zendesk_client.Zenpy')
    def test_create_ticket_success(self, mock_zenpy):
        """Test successful ticket creation"""
        # Setup mock
        mock_ticket = Mock()
        mock_ticket.id = 12345
        mock_ticket.created_at = datetime.now()
        mock_ticket.priority = 'high'
        mock_ticket.status = 'new'

        mock_client = Mock()
        mock_client.users.me.return_value = {'id': 123}
        mock_client.tickets.create.return_value = mock_ticket
        mock_zenpy.return_value = mock_client

        # Create client and ticket
        client = ZendeskClient()
        result = client.create_ticket(
            subject="Test Issue",
            description="This is a test",
            requester_email="user@example.com",
            priority="high",
            tags=["test", "api"]
        )

        # Verify result
        assert result['status'] == 'success'
        assert result['ticket_id'] == '12345'
        assert 'ticket_url' in result
        assert 'test.zendesk.com' in result['ticket_url']

    def test_create_ticket_without_client(self):
        """Test ticket creation without configured client"""
        client = ZendeskClient()
        client.client = None

        result = client.create_ticket(
            subject="Test",
            description="Test",
            requester_email="user@example.com"
        )

        assert result['status'] == 'degraded'
        assert 'error' in result

    @patch.dict('os.environ', {
        'ZENDESK_SUBDOMAIN': 'test',
        'ZENDESK_EMAIL': 'test@example.com',
        'ZENDESK_API_TOKEN': 'test-token'
    })
    @patch('src.integrations.zendesk_client.Zenpy')
    def test_create_ticket_with_api_error(self, mock_zenpy):
        """Test ticket creation handles API errors"""
        mock_client = Mock()
        mock_client.users.me.return_value = {'id': 123}
        mock_client.tickets.create.side_effect = Exception("API Error")
        mock_zenpy.return_value = mock_client

        client = ZendeskClient()
        result = client.create_ticket(
            subject="Test",
            description="Test",
            requester_email="user@example.com"
        )

        assert result['status'] == 'failed'
        assert 'error' in result


class TestZendeskRetryLogic:
    """Test retry logic with exponential backoff"""

    @patch.dict('os.environ', {
        'ZENDESK_SUBDOMAIN': 'test',
        'ZENDESK_EMAIL': 'test@example.com',
        'ZENDESK_API_TOKEN': 'test-token'
    })
    @patch('src.integrations.zendesk_client.Zenpy')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_retry_on_transient_error(self, mock_sleep, mock_zenpy):
        """Test retry logic retries on transient errors"""
        mock_client = Mock()
        mock_client.users.me.return_value = {'id': 123}

        # Fail twice, then succeed
        mock_client.tickets.create.side_effect = [
            Exception("Temporary error"),
            Exception("Temporary error"),
            Mock(id=12345, created_at=datetime.now(), priority='normal', status='new')
        ]

        mock_zenpy.return_value = mock_client

        client = ZendeskClient()
        result = client.create_ticket(
            subject="Test",
            description="Test",
            requester_email="user@example.com"
        )

        # Should eventually succeed
        assert result['status'] == 'success'
        # Should have called create 3 times (2 failures + 1 success)
        assert mock_client.tickets.create.call_count == 3

    @patch.dict('os.environ', {
        'ZENDESK_SUBDOMAIN': 'test',
        'ZENDESK_EMAIL': 'test@example.com',
        'ZENDESK_API_TOKEN': 'test-token'
    })
    @patch('src.integrations.zendesk_client.Zenpy')
    @patch('time.sleep')
    def test_rate_limit_handling(self, mock_sleep, mock_zenpy):
        """Test rate limit (429) handling"""
        mock_client = Mock()
        mock_client.users.me.return_value = {'id': 123}

        # Create a mock 429 response
        rate_limit_error = Exception("Rate limited")
        rate_limit_error.response = Mock()
        rate_limit_error.response.status_code = 429
        rate_limit_error.response.headers = {'Retry-After': '5'}

        # Fail once with rate limit, then succeed
        mock_client.tickets.create.side_effect = [
            rate_limit_error,
            Mock(id=12345, created_at=datetime.now(), priority='normal', status='new')
        ]

        mock_zenpy.return_value = mock_client

        client = ZendeskClient()
        result = client.create_ticket(
            subject="Test",
            description="Test",
            requester_email="user@example.com"
        )

        # Should succeed after retry
        assert result['status'] == 'success'
        # Should have slept for the retry-after duration
        mock_sleep.assert_called_with(5)


class TestZendeskTicketRetrieval:
    """Test ticket retrieval"""

    @patch.dict('os.environ', {
        'ZENDESK_SUBDOMAIN': 'test',
        'ZENDESK_EMAIL': 'test@example.com',
        'ZENDESK_API_TOKEN': 'test-token'
    })
    @patch('src.integrations.zendesk_client.Zenpy')
    def test_get_ticket_success(self, mock_zenpy):
        """Test successful ticket retrieval"""
        mock_ticket = Mock()
        mock_ticket.id = 12345
        mock_ticket.subject = "Test Issue"
        mock_ticket.description = "Description"
        mock_ticket.status = "open"
        mock_ticket.priority = "high"
        mock_ticket.created_at = datetime.now()
        mock_ticket.updated_at = datetime.now()
        mock_ticket.requester_id = 999
        mock_ticket.assignee_id = 888
        mock_ticket.tags = ["test"]

        mock_client = Mock()
        mock_client.users.me.return_value = {'id': 123}
        mock_client.tickets.return_value = mock_ticket
        mock_zenpy.return_value = mock_client

        client = ZendeskClient()
        result = client.get_ticket("12345")

        assert result['status'] == 'success'
        assert result['ticket_id'] == '12345'
        assert result['subject'] == "Test Issue"
        assert result['status_zendesk'] == "open"


class TestZendeskTicketUpdate:
    """Test ticket updates"""

    @patch.dict('os.environ', {
        'ZENDESK_SUBDOMAIN': 'test',
        'ZENDESK_EMAIL': 'test@example.com',
        'ZENDESK_API_TOKEN': 'test-token'
    })
    @patch('src.integrations.zendesk_client.Zenpy')
    def test_update_ticket_status(self, mock_zenpy):
        """Test updating ticket status"""
        mock_ticket = Mock()
        mock_ticket.id = 12345
        mock_ticket.status = "open"
        mock_ticket.priority = "normal"
        mock_ticket.tags = []
        mock_ticket.updated_at = datetime.now()

        mock_client = Mock()
        mock_client.users.me.return_value = {'id': 123}
        mock_client.tickets.return_value = mock_ticket
        mock_client.tickets.update.return_value = mock_ticket
        mock_zenpy.return_value = mock_client

        client = ZendeskClient()
        result = client.update_ticket(
            ticket_id="12345",
            status="solved",
            priority="high"
        )

        assert result['status'] == 'success'
        assert mock_ticket.status == "solved"
        assert mock_ticket.priority == "high"


class TestZendeskUserOperations:
    """Test user-related operations"""

    @patch.dict('os.environ', {
        'ZENDESK_SUBDOMAIN': 'test',
        'ZENDESK_EMAIL': 'test@example.com',
        'ZENDESK_API_TOKEN': 'test-token'
    })
    @patch('src.integrations.zendesk_client.Zenpy')
    def test_get_user_by_email(self, mock_zenpy):
        """Test retrieving user by email"""
        mock_user = Mock()
        mock_user.id = 999
        mock_user.name = "John Doe"
        mock_user.email = "john@example.com"
        mock_user.role = "end-user"
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        mock_user.organization_id = 123
        mock_user.tags = []

        mock_client = Mock()
        mock_client.users.me.return_value = {'id': 123}
        mock_client.search.return_value = [mock_user]
        mock_zenpy.return_value = mock_client

        client = ZendeskClient()
        result = client.get_user("john@example.com")

        assert result['status'] == 'success'
        assert result['user_id'] == 999
        assert result['name'] == "John Doe"
        assert result['email'] == "john@example.com"


class TestZendeskTicketSearch:
    """Test ticket search functionality"""

    @patch.dict('os.environ', {
        'ZENDESK_SUBDOMAIN': 'test',
        'ZENDESK_EMAIL': 'test@example.com',
        'ZENDESK_API_TOKEN': 'test-token'
    })
    @patch('src.integrations.zendesk_client.Zenpy')
    def test_search_tickets(self, mock_zenpy):
        """Test searching tickets"""
        mock_tickets = []
        for i in range(3):
            mock_ticket = Mock()
            mock_ticket.id = 1000 + i
            mock_ticket.subject = f"Issue {i}"
            mock_ticket.status = "open"
            mock_ticket.priority = "normal"
            mock_ticket.created_at = datetime.now()
            mock_ticket.updated_at = datetime.now()
            mock_ticket.requester_id = 999
            mock_ticket.assignee_id = None
            mock_ticket.tags = ["test"]
            mock_tickets.append(mock_ticket)

        mock_client = Mock()
        mock_client.users.me.return_value = {'id': 123}
        mock_client.search.return_value = mock_tickets
        mock_zenpy.return_value = mock_client

        client = ZendeskClient()
        result = client.search_tickets(
            status="open",
            priority="normal"
        )

        assert result['status'] == 'success'
        assert result['results_count'] == 3
        assert len(result['tickets']) == 3


class TestZendeskComments:
    """Test adding comments to tickets"""

    @patch.dict('os.environ', {
        'ZENDESK_SUBDOMAIN': 'test',
        'ZENDESK_EMAIL': 'test@example.com',
        'ZENDESK_API_TOKEN': 'test-token'
    })
    @patch('src.integrations.zendesk_client.Zenpy')
    def test_add_comment(self, mock_zenpy):
        """Test adding comment to ticket"""
        mock_ticket = Mock()
        mock_ticket.id = 12345
        mock_ticket.updated_at = datetime.now()

        mock_client = Mock()
        mock_client.users.me.return_value = {'id': 123}
        mock_client.tickets.return_value = mock_ticket
        mock_client.tickets.update.return_value = mock_ticket
        mock_zenpy.return_value = mock_client

        client = ZendeskClient()
        result = client.add_comment(
            ticket_id="12345",
            comment_body="This is a test comment",
            public=True
        )

        assert result['status'] == 'success'
        assert result['comment_added'] is True
        assert result['public'] is True


class TestGracefulDegradation:
    """Test graceful degradation when Zendesk is not configured"""

    def test_all_methods_degrade_gracefully(self):
        """Test all methods return degraded status when client not configured"""
        client = ZendeskClient()
        client.client = None

        # Test create_ticket
        result = client.create_ticket("Test", "Test", "user@example.com")
        assert result['status'] == 'degraded'

        # Test get_ticket
        result = client.get_ticket("123")
        assert result['status'] == 'degraded'

        # Test update_ticket
        result = client.update_ticket("123", status="solved")
        assert result['status'] == 'degraded'

        # Test add_comment
        result = client.add_comment("123", "comment")
        assert result['status'] == 'degraded'

        # Test get_user
        result = client.get_user("user@example.com")
        assert result['status'] == 'degraded'

        # Test search_tickets
        result = client.search_tickets(query="test")
        assert result['status'] == 'degraded'
        assert result['tickets'] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
