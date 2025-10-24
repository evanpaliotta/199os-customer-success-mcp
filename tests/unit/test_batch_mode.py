"""
Unit tests for Customer Success MCP batch mode onboarding.

Tests the batch mode functionality including:
- Mode selection
- Batch configuration collection
- Summary generation
- Configuration application
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import tempfile
import os
from io import StringIO

# Import the wizard
import sys
cs_mcp_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(cs_mcp_path / "src"))

from tools.onboarding_wizard import (
    CustomerSuccessOnboardingWizard,
    WizardMode,
    WizardStep,
    OnboardingState
)


@pytest.fixture
def temp_state_file():
    """Create temporary state file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def wizard(temp_state_file, monkeypatch):
    """Create wizard instance with mocked console and temp state."""
    # Mock the state file location
    monkeypatch.setattr('tools.onboarding_wizard.STATE_FILE', Path(temp_state_file))

    wizard = CustomerSuccessOnboardingWizard()

    # Mock console to prevent actual output
    wizard.console = Mock()
    wizard.console.print = Mock()

    return wizard


class TestModeSelection:
    """Test mode selection functionality."""

    def test_mode_selection_displays_comparison(self, wizard):
        """Test that mode selection shows comparison table."""
        with patch('tools.onboarding_wizard.Prompt.ask', return_value='1'):
            mode = wizard.select_mode()

            assert mode == WizardMode.INTERACTIVE
            assert wizard.state.mode == WizardMode.INTERACTIVE
            # Verify console.print was called (table display)
            assert wizard.console.print.called

    def test_batch_mode_selection(self, wizard):
        """Test selecting batch mode."""
        with patch('tools.onboarding_wizard.Prompt.ask', return_value='2'):
            mode = wizard.select_mode()

            assert mode == WizardMode.BATCH
            assert wizard.state.mode == WizardMode.BATCH

    def test_mode_selection_with_string_input(self, wizard):
        """Test mode selection with string inputs."""
        with patch('tools.onboarding_wizard.Prompt.ask', return_value='batch'):
            mode = wizard.select_mode()
            assert mode == WizardMode.BATCH

        # Reset state
        wizard.state.mode = None

        with patch('tools.onboarding_wizard.Prompt.ask', return_value='interactive'):
            mode = wizard.select_mode()
            assert mode == WizardMode.INTERACTIVE

    def test_mode_already_set_returns_existing(self, wizard):
        """Test that if mode is already set, it's returned without prompting."""
        wizard.state.mode = WizardMode.BATCH

        # No prompt should be called
        with patch('tools.onboarding_wizard.Prompt.ask') as mock_prompt:
            mode = wizard.select_mode()

            assert mode == WizardMode.BATCH
            mock_prompt.assert_not_called()


class TestBatchSecurityCollection:
    """Test security configuration collection."""

    def test_collect_security_auto_generate(self, wizard):
        """Test security collection with auto-generation."""
        with patch('tools.onboarding_wizard.Confirm.ask', return_value=True), \
             patch('tools.onboarding_wizard.Prompt.ask', side_effect=[
                 'test_master_password',  # master password
                 'test_master_password'   # confirm password
             ]):

            config = wizard._collect_batch_security()

            assert config is not None
            assert 'encryption_key' in config
            assert 'jwt_secret' in config
            assert 'master_password' in config
            assert config['master_password'] == 'test_master_password'
            assert 'redis_url' in config
            assert config['redis_url'] == 'redis://localhost:6379/0'

    def test_collect_security_manual_entry(self, wizard):
        """Test security collection with manual entry."""
        with patch('tools.onboarding_wizard.Confirm.ask', return_value=False), \
             patch('tools.onboarding_wizard.Prompt.ask', side_effect=[
                 'manual_encryption_key_1234567890123456789012',  # encryption key
                 'manual_jwt_secret_1234567890123456',           # JWT secret
                 'test_master_password',                         # master password
                 'test_master_password',                         # confirm password
                 'redis.example.com',                            # redis host
                 '6380',                                         # redis port
                 '1',                                            # redis database
                 ''                                              # redis password (empty)
             ]):

            config = wizard._collect_batch_security()

            assert config is not None
            assert config['encryption_key'] == 'manual_encryption_key_1234567890123456789012'
            assert config['jwt_secret'] == 'manual_jwt_secret_1234567890123456'
            assert config['redis_url'] == 'redis://redis.example.com:6380/1'

    def test_collect_security_password_mismatch(self, wizard):
        """Test that password mismatch returns None."""
        with patch('tools.onboarding_wizard.Confirm.ask', return_value=True), \
             patch('tools.onboarding_wizard.Prompt.ask', side_effect=[
                 'password1',  # master password
                 'password2'   # confirm password (different)
             ]):

            config = wizard._collect_batch_security()

            assert config is None
            # Verify error message was printed
            wizard.console.print.assert_called()

    def test_collect_security_password_too_short(self, wizard):
        """Test that short password returns None."""
        with patch('tools.onboarding_wizard.Confirm.ask', return_value=True), \
             patch('tools.onboarding_wizard.Prompt.ask', side_effect=[
                 'short',  # master password (too short)
                 'short'   # confirm password
             ]):

            config = wizard._collect_batch_security()

            assert config is None


class TestBatchPlatformCollection:
    """Test platform configuration collection."""

    def test_collect_platforms_none_selected(self, wizard):
        """Test platform collection when no platforms selected."""
        with patch('tools.onboarding_wizard.Confirm.ask', return_value=False):
            config = wizard._collect_batch_platforms()

            assert config == {}

    def test_collect_zendesk_platform(self, wizard):
        """Test collecting Zendesk credentials."""
        with patch('tools.onboarding_wizard.Confirm.ask', side_effect=[
                True,   # Configure Zendesk? Yes
                False,  # All other platforms? No
                False, False, False, False, False, False, False, False, False
             ]), \
             patch('tools.onboarding_wizard.Prompt.ask', side_effect=[
                 'mycompany',           # subdomain
                 'admin@example.com',   # email
                 'api_token_12345'      # API token
             ]):

            config = wizard._collect_batch_platforms()

            assert 'zendesk' in config
            assert config['zendesk']['subdomain'] == 'mycompany'
            assert config['zendesk']['email'] == 'admin@example.com'
            assert config['zendesk']['api_token'] == 'api_token_12345'

    def test_collect_multiple_platforms(self, wizard):
        """Test collecting multiple platform credentials."""
        with patch('tools.onboarding_wizard.Confirm.ask', side_effect=[
                True,   # Zendesk
                True,   # Intercom
                False,  # Mixpanel
                False,  # SendGrid
                False,  # Gainsight
                False,  # Amplitude
                False,  # Salesforce
                False,  # HubSpot
                False,  # Slack
                False,  # Typeform
                False   # Freshdesk
             ]), \
             patch('tools.onboarding_wizard.Prompt.ask', side_effect=[
                 # Zendesk
                 'mycompany', 'admin@example.com', 'api_token_12345',
                 # Intercom
                 'intercom_access_token_xyz'
             ]):

            config = wizard._collect_batch_platforms()

            assert len(config) == 2
            assert 'zendesk' in config
            assert 'intercom' in config


class TestBatchCSConfigCollection:
    """Test CS configuration collection."""

    def test_collect_cs_config_defaults(self, wizard):
        """Test CS config collection with defaults."""
        with patch('tools.onboarding_wizard.Confirm.ask', return_value=True):
            config = wizard._collect_batch_cs_config()

            assert config is not None

            # Verify default weights
            assert 'weights' in config
            assert config['weights']['usage'] == 0.35
            assert config['weights']['engagement'] == 0.25
            assert config['weights']['support'] == 0.15
            assert config['weights']['satisfaction'] == 0.15
            assert config['weights']['payment'] == 0.10

            # Verify default thresholds
            assert 'thresholds' in config
            assert config['thresholds']['churn_risk'] == 40.0
            assert config['thresholds']['at_risk'] == 60.0
            assert config['thresholds']['healthy'] == 75.0
            assert config['thresholds']['champion'] == 90.0

            # Verify default SLAs
            assert 'slas' in config
            assert config['slas']['first_response_minutes'] == 15
            assert config['slas']['p1_resolution_minutes'] == 240
            assert config['slas']['p2_resolution_minutes'] == 480
            assert config['slas']['p3_resolution_minutes'] == 1440

    def test_collect_cs_config_custom(self, wizard):
        """Test CS config collection with custom values."""
        with patch('tools.onboarding_wizard.Confirm.ask', return_value=False), \
             patch('tools.onboarding_wizard.Prompt.ask', side_effect=[
                 # Custom weights
                 '0.40', '0.30', '0.10', '0.10', '0.10',
                 # Custom thresholds
                 '50', '70', '85', '95',
                 # Custom SLAs
                 '30', '360', '600', '2880'
             ]):

            config = wizard._collect_batch_cs_config()

            assert config['weights']['usage'] == 0.40
            assert config['thresholds']['at_risk'] == 70.0
            assert config['slas']['p1_resolution_minutes'] == 360


class TestBatchDatabaseCollection:
    """Test database configuration collection."""

    def test_collect_database_defaults(self, wizard):
        """Test database collection with defaults."""
        with patch('tools.onboarding_wizard.Confirm.ask', side_effect=[True, True, True]), \
             patch('tools.onboarding_wizard.Prompt.ask', return_value='test_password'):

            config = wizard._collect_batch_database()

            assert config is not None
            assert config['host'] == 'localhost'
            assert config['port'] == '5432'
            assert config['user'] == 'postgres'
            assert config['password'] == 'test_password'
            assert config['database'] == 'cs_mcp_db'
            assert config['run_migrations'] is True
            assert config['create_defaults'] is True

    def test_collect_database_custom(self, wizard):
        """Test database collection with custom values."""
        with patch('tools.onboarding_wizard.Confirm.ask', side_effect=[
                False,  # Use default? No
                False,  # Run migrations? No
                False   # Create defaults? No
             ]), \
             patch('tools.onboarding_wizard.Prompt.ask', side_effect=[
                 'db.example.com',   # host
                 '5433',             # port
                 'csuser',           # user
                 'secure_password',  # password
                 'cs_production_db'  # database
             ]):

            config = wizard._collect_batch_database()

            assert config['host'] == 'db.example.com'
            assert config['port'] == '5433'
            assert config['user'] == 'csuser'
            assert config['database'] == 'cs_production_db'
            assert config['run_migrations'] is False
            assert config['create_defaults'] is False


class TestBatchSummary:
    """Test batch summary generation."""

    def test_show_batch_summary_displays_all_sections(self, wizard):
        """Test that summary displays all configuration sections."""
        security_config = {
            'encryption_key': 'test_key',
            'jwt_secret': 'test_secret',
            'redis_url': 'redis://localhost:6379/0'
        }

        platform_config = {
            'zendesk': {'subdomain': 'test', 'email': 'test@example.com'}
        }

        cs_config = {
            'weights': {'usage': 0.35},
            'thresholds': {'at_risk': 60.0},
            'slas': {'p1_resolution_minutes': 240}
        }

        database_config = {
            'host': 'localhost',
            'database': 'cs_mcp_db'
        }

        with patch('tools.onboarding_wizard.Confirm.ask', return_value=True):
            result = wizard._show_batch_summary(
                security_config,
                platform_config,
                cs_config,
                database_config
            )

            assert result is True
            # Verify console.print was called multiple times (for table, panels, etc.)
            assert wizard.console.print.call_count > 0

    def test_show_batch_summary_user_cancels(self, wizard):
        """Test that summary returns False if user cancels."""
        with patch('tools.onboarding_wizard.Confirm.ask', return_value=False):
            result = wizard._show_batch_summary({}, {}, {}, {})

            assert result is False


class TestConfigApplication:
    """Test configuration application methods."""

    def test_apply_security_config(self, wizard, tmp_path, monkeypatch):
        """Test applying security configuration."""
        # Mock .env file location
        env_file = tmp_path / ".env"
        monkeypatch.setattr('tools.onboarding_wizard.Path.cwd', lambda: tmp_path)

        security_config = {
            'encryption_key': 'test_encryption_key',
            'jwt_secret': 'test_jwt_secret',
            'master_password': 'test_master_password',
            'redis_url': 'redis://localhost:6379/0'
        }

        wizard._apply_security_config(security_config)

        # Verify environment variables were set
        assert os.getenv('ENCRYPTION_KEY') == 'test_encryption_key'
        assert os.getenv('JWT_SECRET') == 'test_jwt_secret'
        assert os.getenv('REDIS_URL') == 'redis://localhost:6379/0'

    def test_apply_cs_config(self, wizard, tmp_path, monkeypatch):
        """Test applying CS configuration."""
        monkeypatch.setattr('tools.onboarding_wizard.Path.cwd', lambda: tmp_path)

        cs_config = {
            'weights': {
                'usage': 0.35,
                'engagement': 0.25
            },
            'thresholds': {
                'at_risk': 60.0,
                'healthy': 75.0
            },
            'slas': {
                'p1_resolution_minutes': 240
            }
        }

        wizard._apply_cs_config(cs_config)

        # Verify state was updated
        assert wizard.state.health_weights is not None
        assert wizard.state.health_thresholds is not None


class TestBatchModeIntegration:
    """Test batch mode integration with main run() method."""

    def test_run_selects_mode_first_time(self, wizard):
        """Test that run() calls select_mode when mode not set."""
        wizard.state.mode = None

        with patch.object(wizard, 'select_mode', return_value=WizardMode.BATCH), \
             patch.object(wizard, 'run_batch_mode', return_value=True):

            wizard.run()

            wizard.select_mode.assert_called_once()
            wizard.run_batch_mode.assert_called_once()

    def test_run_uses_existing_mode(self, wizard):
        """Test that run() uses existing mode without prompting."""
        wizard.state.mode = WizardMode.BATCH

        with patch.object(wizard, 'select_mode') as mock_select, \
             patch.object(wizard, 'run_batch_mode', return_value=True):

            wizard.run()

            # select_mode should still be called but will return early
            wizard.run_batch_mode.assert_called_once()

    def test_run_batch_mode_branches_correctly(self, wizard):
        """Test that batch mode branches to run_batch_mode()."""
        wizard.state.mode = None

        with patch.object(wizard, 'select_mode', return_value=WizardMode.BATCH), \
             patch.object(wizard, 'run_batch_mode', return_value=True), \
             patch.object(wizard, 'step_welcome') as mock_welcome:

            wizard.run()

            # run_batch_mode should be called
            wizard.run_batch_mode.assert_called_once()
            # Interactive steps should NOT be called
            mock_welcome.assert_not_called()

    def test_run_interactive_mode_continues_normal_flow(self, wizard):
        """Test that interactive mode continues with normal step flow."""
        wizard.state.mode = None

        with patch.object(wizard, 'select_mode', return_value=WizardMode.INTERACTIVE), \
             patch.object(wizard, 'run_batch_mode') as mock_batch, \
             patch.object(wizard, 'step_welcome', return_value=False):

            wizard.run()

            # run_batch_mode should NOT be called
            mock_batch.assert_not_called()
            # Interactive step should be called
            wizard.step_welcome.assert_called_once()


class TestBatchModeOrchestration:
    """Test the main batch mode orchestration."""

    def test_run_batch_mode_complete_flow(self, wizard):
        """Test complete batch mode flow."""
        # Mock all collection methods
        security_config = {'encryption_key': 'test'}
        platform_config = {}
        cs_config = {'weights': {}}
        database_config = {'host': 'localhost'}

        with patch.object(wizard, '_collect_batch_security', return_value=security_config), \
             patch.object(wizard, '_collect_batch_platforms', return_value=platform_config), \
             patch.object(wizard, '_collect_batch_cs_config', return_value=cs_config), \
             patch.object(wizard, '_collect_batch_database', return_value=database_config), \
             patch.object(wizard, '_show_batch_summary', return_value=True), \
             patch.object(wizard, '_apply_security_config'), \
             patch.object(wizard, '_apply_platform_config'), \
             patch.object(wizard, '_apply_cs_config'), \
             patch.object(wizard, '_apply_database_config', return_value=True), \
             patch.object(wizard, 'step_completion', return_value=True), \
             patch('tools.onboarding_wizard.Confirm.ask', return_value=True), \
             patch('builtins.input'):

            result = wizard.run_batch_mode()

            assert result is True
            # Verify all collection methods were called
            wizard._collect_batch_security.assert_called_once()
            wizard._collect_batch_platforms.assert_called_once()
            wizard._collect_batch_cs_config.assert_called_once()
            wizard._collect_batch_database.assert_called_once()
            # Verify summary was shown
            wizard._show_batch_summary.assert_called_once()
            # Verify all apply methods were called
            wizard._apply_security_config.assert_called_once()
            wizard._apply_platform_config.assert_called_once()
            wizard._apply_cs_config.assert_called_once()
            wizard._apply_database_config.assert_called_once()
            # Verify completion step was called
            wizard.step_completion.assert_called_once()

    def test_run_batch_mode_user_cancels_ready_check(self, wizard):
        """Test batch mode when user cancels at ready check."""
        with patch('tools.onboarding_wizard.Confirm.ask', return_value=False):
            result = wizard.run_batch_mode()

            assert result is False

    def test_run_batch_mode_security_collection_fails(self, wizard):
        """Test batch mode when security collection fails."""
        with patch('tools.onboarding_wizard.Confirm.ask', return_value=True), \
             patch.object(wizard, '_collect_batch_security', return_value=None):

            result = wizard.run_batch_mode()

            assert result is False

    def test_run_batch_mode_user_cancels_summary(self, wizard):
        """Test batch mode when user cancels at summary."""
        with patch('tools.onboarding_wizard.Confirm.ask', return_value=True), \
             patch.object(wizard, '_collect_batch_security', return_value={}), \
             patch.object(wizard, '_collect_batch_platforms', return_value={}), \
             patch.object(wizard, '_collect_batch_cs_config', return_value={}), \
             patch.object(wizard, '_collect_batch_database', return_value={}), \
             patch.object(wizard, '_show_batch_summary', return_value=False):

            result = wizard.run_batch_mode()

            assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
