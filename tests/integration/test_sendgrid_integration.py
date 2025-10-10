"""
Integration tests for SendGrid email integration

Tests the SendGridClient class with both mock mode and real API mode.
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from src.integrations.sendgrid_client import SendGridClient


class TestSendGridClient:
    """Test SendGridClient class"""

    def test_client_initialization_mock_mode(self):
        """Test client initializes in mock mode when API key not configured"""
        with patch.dict(os.environ, {}, clear=True):
            client = SendGridClient()
            assert client.mock_mode is True
            assert client.client is None

    def test_client_initialization_with_api_key(self):
        """Test client initializes with real API key"""
        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_key'}):
            client = SendGridClient()
            assert client.mock_mode is False
            assert client.client is not None

    def test_email_validation(self):
        """Test email address validation"""
        client = SendGridClient()

        # Valid emails
        assert client.validate_email('test@example.com') is True
        assert client.validate_email('user.name+tag@example.co.uk') is True

        # Invalid emails
        assert client.validate_email('invalid') is False
        assert client.validate_email('invalid@') is False
        assert client.validate_email('@example.com') is False
        assert client.validate_email('') is False
        assert client.validate_email(None) is False

    def test_send_email_mock_mode(self):
        """Test send_email in mock mode"""
        with patch.dict(os.environ, {}, clear=True):
            client = SendGridClient()

            result = client.send_email(
                to_email='test@example.com',
                subject='Test Subject',
                text_content='Test message'
            )

            assert result['status'] == 'success'
            assert result['mock'] is True
            assert 'message_id' in result
            assert result['to_email'] == 'test@example.com'

    def test_send_email_missing_required_fields(self):
        """Test send_email validates required fields"""
        client = SendGridClient()

        # Missing to_email
        result = client.send_email(
            to_email='',
            subject='Test',
            text_content='Test'
        )
        assert 'error' in result

        # Missing subject
        result = client.send_email(
            to_email='test@example.com',
            subject='',
            text_content='Test'
        )
        assert 'error' in result

        # Missing both html and text content
        result = client.send_email(
            to_email='test@example.com',
            subject='Test'
        )
        assert 'error' in result

    def test_send_email_invalid_email(self):
        """Test send_email rejects invalid email addresses"""
        client = SendGridClient()

        result = client.send_email(
            to_email='invalid-email',
            subject='Test',
            text_content='Test'
        )

        assert 'error' in result
        assert 'Invalid' in result['error']

    @patch('src.integrations.sendgrid_client.SendGridAPIClient')
    def test_send_email_with_real_client(self, mock_sendgrid_api):
        """Test send_email with real SendGrid client"""
        # Mock the SendGrid API response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_msg_123'}

        mock_client_instance = Mock()
        mock_client_instance.send = Mock(return_value=mock_response)
        mock_sendgrid_api.return_value = mock_client_instance

        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_key'}):
            client = SendGridClient()

            result = client.send_email(
                to_email='test@example.com',
                subject='Test Subject',
                html_content='<h1>Test</h1>',
                text_content='Test'
            )

            assert result['status'] == 'success'
            assert result['message_id'] == 'test_msg_123'
            assert result['status_code'] == 202
            mock_client_instance.send.assert_called_once()

    @patch('src.integrations.sendgrid_client.SendGridAPIClient')
    def test_send_email_with_attachments(self, mock_sendgrid_api):
        """Test send_email with attachments"""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_msg_123'}

        mock_client_instance = Mock()
        mock_client_instance.send = Mock(return_value=mock_response)
        mock_sendgrid_api.return_value = mock_client_instance

        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_key'}):
            client = SendGridClient()

            attachments = [
                {
                    'content': 'base64encodedcontent',
                    'filename': 'test.pdf',
                    'type': 'application/pdf'
                }
            ]

            result = client.send_email(
                to_email='test@example.com',
                subject='Test with Attachment',
                text_content='Please see attachment',
                attachments=attachments
            )

            assert result['status'] == 'success'

    @patch('src.integrations.sendgrid_client.SendGridAPIClient')
    def test_send_email_with_custom_args_and_categories(self, mock_sendgrid_api):
        """Test send_email with custom args and categories for tracking"""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_msg_123'}

        mock_client_instance = Mock()
        mock_client_instance.send = Mock(return_value=mock_response)
        mock_sendgrid_api.return_value = mock_client_instance

        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_key'}):
            client = SendGridClient()

            result = client.send_email(
                to_email='test@example.com',
                subject='Test',
                text_content='Test',
                custom_args={'campaign_id': 'camp_123', 'client_id': 'client_456'},
                categories=['newsletter', 'marketing']
            )

            assert result['status'] == 'success'

    def test_send_template_email_mock_mode(self):
        """Test send_template_email in mock mode"""
        with patch.dict(os.environ, {}, clear=True):
            client = SendGridClient()

            result = client.send_template_email(
                to_email='test@example.com',
                template_id='d-1234567890',
                dynamic_data={'name': 'John', 'company': 'Acme Inc'}
            )

            assert result['status'] == 'success'
            assert result['mock'] is True
            assert result['template_id'] == 'd-1234567890'

    def test_send_template_email_missing_fields(self):
        """Test send_template_email validates required fields"""
        client = SendGridClient()

        # Missing to_email
        result = client.send_template_email(
            to_email='',
            template_id='d-123',
            dynamic_data={}
        )
        assert 'error' in result

        # Missing template_id
        result = client.send_template_email(
            to_email='test@example.com',
            template_id='',
            dynamic_data={}
        )
        assert 'error' in result

    @patch('src.integrations.sendgrid_client.SendGridAPIClient')
    def test_send_template_email_with_real_client(self, mock_sendgrid_api):
        """Test send_template_email with real SendGrid client"""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_msg_123'}

        mock_client_instance = Mock()
        mock_client_instance.send = Mock(return_value=mock_response)
        mock_sendgrid_api.return_value = mock_client_instance

        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_key'}):
            client = SendGridClient()

            result = client.send_template_email(
                to_email='test@example.com',
                template_id='d-1234567890',
                dynamic_data={'name': 'John', 'company': 'Acme Inc'}
            )

            assert result['status'] == 'success'
            assert result['message_id'] == 'test_msg_123'
            mock_client_instance.send.assert_called_once()

    def test_send_bulk_emails_mock_mode(self):
        """Test send_bulk_emails in mock mode"""
        with patch.dict(os.environ, {}, clear=True):
            client = SendGridClient()

            emails = [
                {
                    'to_email': 'user1@example.com',
                    'subject': 'Test 1',
                    'text_content': 'Message 1'
                },
                {
                    'to_email': 'user2@example.com',
                    'subject': 'Test 2',
                    'text_content': 'Message 2'
                }
            ]

            result = client.send_bulk_emails(emails)

            assert result['status'] == 'success'
            assert result['mock'] is True
            assert result['total_emails'] == 2
            assert result['successful'] == 2
            assert result['failed'] == 0

    def test_send_bulk_emails_empty_list(self):
        """Test send_bulk_emails with empty list"""
        client = SendGridClient()

        result = client.send_bulk_emails([])

        assert 'error' in result

    @patch('src.integrations.sendgrid_client.SendGridAPIClient')
    def test_send_bulk_emails_with_real_client(self, mock_sendgrid_api):
        """Test send_bulk_emails with real SendGrid client"""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {'X-Message-Id': 'test_msg'}

        mock_client_instance = Mock()
        mock_client_instance.send = Mock(return_value=mock_response)
        mock_sendgrid_api.return_value = mock_client_instance

        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_key'}):
            client = SendGridClient()

            emails = [
                {'to_email': 'user1@example.com', 'subject': 'Test', 'text_content': 'Message'},
                {'to_email': 'user2@example.com', 'subject': 'Test', 'text_content': 'Message'}
            ]

            result = client.send_bulk_emails(emails)

            assert result['status'] == 'success'
            assert result['total_emails'] == 2
            assert result['successful'] == 2
            assert result['failed'] == 0

    def test_track_email_events_single_event(self):
        """Test track_email_events with single event"""
        client = SendGridClient()

        webhook_data = {
            'event': 'delivered',
            'email': 'test@example.com',
            'timestamp': 1234567890,
            'sg_message_id': 'msg_123',
            'category': ['newsletter'],
            'custom_args': {'campaign_id': 'camp_123'}
        }

        result = client.track_email_events(webhook_data)

        assert result['status'] == 'success'
        assert result['count'] == 1
        assert len(result['events']) == 1
        assert result['events'][0]['event_type'] == 'delivered'
        assert result['events'][0]['email'] == 'test@example.com'

    def test_track_email_events_multiple_events(self):
        """Test track_email_events with multiple events"""
        client = SendGridClient()

        webhook_data = [
            {'event': 'open', 'email': 'test1@example.com', 'timestamp': 123},
            {'event': 'click', 'email': 'test2@example.com', 'timestamp': 456, 'url': 'https://example.com'},
            {'event': 'bounce', 'email': 'test3@example.com', 'timestamp': 789, 'reason': 'Invalid', 'type': 'hard'}
        ]

        result = client.track_email_events(webhook_data)

        assert result['status'] == 'success'
        assert result['count'] == 3
        assert len(result['events']) == 3

        # Check click event has URL
        click_event = next(e for e in result['events'] if e['event_type'] == 'click')
        assert click_event['url'] == 'https://example.com'

        # Check bounce event has reason
        bounce_event = next(e for e in result['events'] if e['event_type'] == 'bounce')
        assert bounce_event['reason'] == 'Invalid'
        assert bounce_event['bounce_type'] == 'hard'

    def test_track_email_events_empty_data(self):
        """Test track_email_events with empty data"""
        client = SendGridClient()

        result = client.track_email_events(None)

        assert 'error' in result

    def test_get_stats_mock_mode(self):
        """Test get_stats in mock mode"""
        with patch.dict(os.environ, {}, clear=True):
            client = SendGridClient()

            result = client.get_stats(
                start_date='2024-01-01',
                end_date='2024-01-31',
                aggregated_by='day'
            )

            assert result['status'] == 'success'
            assert result['mock'] is True
            assert 'stats' in result
            assert result['stats']['requests'] > 0
            assert result['stats']['delivered'] > 0

    @patch('src.integrations.sendgrid_client.SendGridAPIClient')
    def test_retry_logic_on_server_error(self, mock_sendgrid_api):
        """Test retry logic on server error (5xx)"""
        from python_http_client.exceptions import HTTPError

        # Mock HTTPError with 500 status
        mock_error = HTTPError(
            Mock(status_code=500, body='Server Error'),
            'Server Error'
        )
        mock_error.status_code = 500

        mock_client_instance = Mock()
        # Fail first two attempts, succeed on third
        mock_success_response = Mock()
        mock_success_response.status_code = 202
        mock_success_response.headers = {'X-Message-Id': 'test_msg'}

        mock_client_instance.send = Mock(
            side_effect=[mock_error, mock_error, mock_success_response]
        )
        mock_sendgrid_api.return_value = mock_client_instance

        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_key'}):
            with patch('time.sleep'):  # Skip actual sleep delays
                client = SendGridClient()
                client.retry_delay = 0.01  # Fast retries for testing

                result = client.send_email(
                    to_email='test@example.com',
                    subject='Test',
                    text_content='Test'
                )

                assert result['status'] == 'success'
                assert mock_client_instance.send.call_count == 3

    @patch('src.integrations.sendgrid_client.SendGridAPIClient')
    def test_no_retry_on_client_error(self, mock_sendgrid_api):
        """Test no retry on client error (4xx except 429)"""
        from python_http_client.exceptions import HTTPError

        # Mock HTTPError with 400 status
        mock_error = HTTPError(
            Mock(status_code=400, body='Bad Request'),
            'Bad Request'
        )
        mock_error.status_code = 400

        mock_client_instance = Mock()
        mock_client_instance.send = Mock(side_effect=mock_error)
        mock_sendgrid_api.return_value = mock_client_instance

        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_key'}):
            client = SendGridClient()

            result = client.send_email(
                to_email='test@example.com',
                subject='Test',
                text_content='Test'
            )

            # Should fail immediately without retries
            assert 'error' in result
            assert mock_client_instance.send.call_count == 1

    @patch('src.integrations.sendgrid_client.SendGridAPIClient')
    def test_retry_on_rate_limit(self, mock_sendgrid_api):
        """Test retry on rate limit (429)"""
        from python_http_client.exceptions import HTTPError

        # Mock HTTPError with 429 status
        mock_error = HTTPError(
            Mock(status_code=429, body='Rate Limit'),
            'Rate Limit Exceeded'
        )
        mock_error.status_code = 429

        mock_client_instance = Mock()
        mock_success_response = Mock()
        mock_success_response.status_code = 202
        mock_success_response.headers = {'X-Message-Id': 'test_msg'}

        # Fail first attempt with 429, succeed on second
        mock_client_instance.send = Mock(
            side_effect=[mock_error, mock_success_response]
        )
        mock_sendgrid_api.return_value = mock_client_instance

        with patch.dict(os.environ, {'SENDGRID_API_KEY': 'test_key'}):
            with patch('time.sleep'):
                client = SendGridClient()

                result = client.send_email(
                    to_email='test@example.com',
                    subject='Test',
                    text_content='Test'
                )

                assert result['status'] == 'success'
                assert mock_client_instance.send.call_count == 2


class TestSendGridConfiguration:
    """Test SendGrid configuration and environment variables"""

    def test_default_from_email(self):
        """Test default from email when not configured"""
        with patch.dict(os.environ, {}, clear=True):
            client = SendGridClient()
            assert client.from_email == 'noreply@yourcompany.com'

    def test_custom_from_email(self):
        """Test custom from email from environment"""
        with patch.dict(os.environ, {
            'SENDGRID_FROM_EMAIL': 'support@example.com',
            'SENDGRID_FROM_NAME': 'Example Support'
        }):
            client = SendGridClient()
            assert client.from_email == 'support@example.com'
            assert client.from_name == 'Example Support'

    def test_custom_retry_settings(self):
        """Test custom retry settings from environment"""
        with patch.dict(os.environ, {
            'SENDGRID_MAX_RETRIES': '5',
            'SENDGRID_RETRY_DELAY': '2',
            'SENDGRID_BATCH_SIZE': '500'
        }):
            client = SendGridClient()
            assert client.max_retries == 5
            assert client.retry_delay == 2
            assert client.batch_size == 500
