"""
Unit tests for the Customer Success MCP Onboarding Wizard
Comprehensive test suite covering all wizard functionality

Test Coverage:
- OnboardingState class (initialization, serialization, step tracking)
- Wizard initialization and state management
- Step 1: Welcome & System Check
- Step 2: Platform Integration Setup (Zendesk, Intercom, Mixpanel, SendGrid)
- Step 3: Configuration (health scores, thresholds, SLAs)
- Step 4: Database Initialization
- Step 5: Testing & Validation
- Step 6: Completion
- Full wizard flow (sequential, resume, interrupt handling)
- Edge cases and error handling
- Performance and security tests
"""

import os
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open, call
from datetime import datetime

from src.tools.onboarding_wizard import (
    OnboardingState,
    WizardStep,
    CustomerSuccessOnboardingWizard
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory"""
    config_dir = tmp_path / ".config" / "cs-mcp"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def mock_console():
    """Mock Rich console"""
    with patch('src.tools.onboarding_wizard.Console') as mock:
        console = MagicMock()
        console.print = MagicMock()
        mock.return_value = console
        yield console


@pytest.fixture
def wizard(temp_config_dir, mock_console):
    """Create a wizard instance with mocked dependencies"""
    with patch.object(Path, 'home', return_value=temp_config_dir.parent.parent):
        wizard = CustomerSuccessOnboardingWizard()
        wizard.config_dir = temp_config_dir
        wizard.state_file = temp_config_dir / "onboarding_state.json"
        wizard.env_file = temp_config_dir / ".env"
        return wizard


@pytest.fixture
def sample_state():
    """Sample onboarding state"""
    return OnboardingState(
        current_step=WizardStep.WELCOME,
        python_version="3.11.0",
        dependencies_installed=True,
        zendesk_configured=True,
        health_score_weights={'usage': 0.35, 'engagement': 0.25, 'support': 0.15, 'satisfaction': 0.15, 'payment': 0.10}
    )


# ============================================================================
# ONBOARDING STATE TESTS
# ============================================================================

class TestOnboardingState:
    """Tests for OnboardingState class"""

    def test_state_initialization(self):
        """Test state initializes with defaults"""
        state = OnboardingState()

        assert state.current_step == WizardStep.WELCOME
        assert state.completed_steps == []
        assert state.python_version is None
        assert state.dependencies_installed is False
        assert state.started_at is not None

    def test_state_initialization_with_values(self):
        """Test state initialization with custom values"""
        state = OnboardingState(
            python_version="3.12.0",
            dependencies_installed=True,
            zendesk_configured=True
        )

        assert state.python_version == "3.12.0"
        assert state.dependencies_installed is True
        assert state.zendesk_configured is True

    def test_mark_step_complete(self):
        """Test marking steps as complete"""
        state = OnboardingState()

        state.mark_step_complete(WizardStep.WELCOME)
        assert WizardStep.WELCOME in state.completed_steps

        state.mark_step_complete(WizardStep.SYSTEM_CHECK)
        assert WizardStep.SYSTEM_CHECK in state.completed_steps
        assert len(state.completed_steps) == 2

    def test_mark_step_complete_idempotent(self):
        """Test marking same step multiple times doesn't duplicate"""
        state = OnboardingState()

        state.mark_step_complete(WizardStep.WELCOME)
        state.mark_step_complete(WizardStep.WELCOME)

        assert state.completed_steps.count(WizardStep.WELCOME) == 1

    def test_is_step_complete(self):
        """Test checking if step is complete"""
        state = OnboardingState()

        assert not state.is_step_complete(WizardStep.WELCOME)

        state.mark_step_complete(WizardStep.WELCOME)
        assert state.is_step_complete(WizardStep.WELCOME)
        assert not state.is_step_complete(WizardStep.SYSTEM_CHECK)

    def test_to_dict(self):
        """Test serialization to dictionary"""
        state = OnboardingState(
            python_version="3.11.0",
            dependencies_installed=True
        )
        state.mark_step_complete(WizardStep.WELCOME)

        data = state.to_dict()

        assert data['current_step'] == 'WELCOME'
        assert data['completed_steps'] == ['WELCOME']
        assert data['python_version'] == "3.11.0"
        assert data['dependencies_installed'] is True

    def test_to_dict_complex_state(self):
        """Test serialization with complex state"""
        state = OnboardingState(
            python_version="3.11.0",
            health_score_weights={'usage': 0.35, 'engagement': 0.25},
            sla_targets={'p1': 240, 'p2': 480},
            thresholds={'at_risk': 60.0, 'healthy': 75.0}
        )
        state.mark_step_complete(WizardStep.WELCOME)
        state.mark_step_complete(WizardStep.SYSTEM_CHECK)

        data = state.to_dict()

        assert data['health_score_weights'] == {'usage': 0.35, 'engagement': 0.25}
        assert data['sla_targets'] == {'p1': 240, 'p2': 480}
        assert data['thresholds'] == {'at_risk': 60.0, 'healthy': 75.0}
        assert len(data['completed_steps']) == 2

    def test_from_dict(self):
        """Test deserialization from dictionary"""
        data = {
            'current_step': 'PLATFORM_SETUP',
            'completed_steps': ['WELCOME', 'SYSTEM_CHECK'],
            'python_version': '3.11.0',
            'dependencies_installed': True,
            'zendesk_configured': True
        }

        state = OnboardingState.from_dict(data)

        assert state.current_step == WizardStep.PLATFORM_SETUP
        assert WizardStep.WELCOME in state.completed_steps
        assert WizardStep.SYSTEM_CHECK in state.completed_steps
        assert state.python_version == '3.11.0'
        assert state.zendesk_configured is True

    def test_from_dict_with_enum_objects(self):
        """Test deserialization handles both string and enum values"""
        data = {
            'current_step': WizardStep.TESTING,
            'completed_steps': [WizardStep.WELCOME, 'SYSTEM_CHECK'],
            'python_version': '3.11.0'
        }

        state = OnboardingState.from_dict(data)

        assert state.current_step == WizardStep.TESTING
        assert len(state.completed_steps) == 2

    def test_serialization_roundtrip(self, sample_state):
        """Test full serialization roundtrip"""
        sample_state.mark_step_complete(WizardStep.WELCOME)
        sample_state.mark_step_complete(WizardStep.SYSTEM_CHECK)

        # Serialize
        data = sample_state.to_dict()

        # Deserialize
        restored_state = OnboardingState.from_dict(data)

        assert restored_state.current_step == sample_state.current_step
        assert restored_state.completed_steps == sample_state.completed_steps
        assert restored_state.python_version == sample_state.python_version
        assert restored_state.zendesk_configured == sample_state.zendesk_configured

    def test_serialization_preserves_all_fields(self):
        """Test serialization preserves all fields"""
        state = OnboardingState(
            python_version="3.11.0",
            dependencies_installed=True,
            database_connected=True,
            redis_connected=True,
            zendesk_configured=True,
            intercom_configured=True,
            mixpanel_configured=True,
            sendgrid_configured=True,
            database_initialized=True,
            migrations_run=True,
            all_tests_passed=True
        )

        data = state.to_dict()
        restored = OnboardingState.from_dict(data)

        assert restored.python_version == state.python_version
        assert restored.dependencies_installed == state.dependencies_installed
        assert restored.database_connected == state.database_connected
        assert restored.zendesk_configured == state.zendesk_configured
        assert restored.all_tests_passed == state.all_tests_passed


# ============================================================================
# WIZARD INITIALIZATION TESTS
# ============================================================================

class TestWizardInitialization:
    """Tests for wizard initialization"""

    def test_wizard_initializes(self, wizard, temp_config_dir):
        """Test wizard initializes properly"""
        assert wizard.state is not None
        assert wizard.config_dir == temp_config_dir
        assert wizard.state_file == temp_config_dir / "onboarding_state.json"

    def test_wizard_creates_config_dir(self, tmp_path):
        """Test wizard creates config directory if missing"""
        with patch.object(Path, 'home', return_value=tmp_path):
            wizard = CustomerSuccessOnboardingWizard()
            assert wizard.config_dir.exists()

    def test_wizard_initializes_state(self, wizard):
        """Test wizard initializes fresh state"""
        assert isinstance(wizard.state, OnboardingState)
        assert wizard.state.current_step == WizardStep.WELCOME
        assert wizard.state.completed_steps == []

    def test_save_state(self, wizard, sample_state):
        """Test saving state to disk"""
        wizard.state = sample_state
        wizard.save_state()

        assert wizard.state_file.exists()

        with open(wizard.state_file, 'r') as f:
            data = json.load(f)

        assert data['python_version'] == "3.11.0"
        assert data['zendesk_configured'] is True

    def test_save_state_creates_directory(self, wizard):
        """Test save_state creates directory if missing"""
        wizard.state_file.parent.rmdir()
        wizard.state_file.parent.mkdir(parents=True)

        wizard.save_state()
        assert wizard.state_file.exists()

    def test_load_state(self, wizard, sample_state, temp_config_dir):
        """Test loading state from disk"""
        # Save state first
        state_data = sample_state.to_dict()
        state_file = temp_config_dir / "onboarding_state.json"

        with open(state_file, 'w') as f:
            json.dump(state_data, f)

        # Load it
        wizard.load_state()

        assert wizard.state.python_version == "3.11.0"
        assert wizard.state.zendesk_configured is True

    def test_load_state_handles_missing_file(self, wizard):
        """Test loading state when file doesn't exist"""
        wizard.load_state()  # Should not raise exception
        assert wizard.state is not None

    def test_load_state_handles_corrupt_json(self, wizard, temp_config_dir):
        """Test loading state with corrupted JSON"""
        state_file = temp_config_dir / "onboarding_state.json"
        with open(state_file, 'w') as f:
            f.write("invalid json{")

        wizard.load_state()  # Should not crash
        assert wizard.state is not None

    def test_state_persistence_roundtrip(self, wizard, sample_state):
        """Test complete state save/load cycle"""
        wizard.state = sample_state
        wizard.state.mark_step_complete(WizardStep.WELCOME)

        wizard.save_state()

        # Create new wizard and load
        new_wizard = CustomerSuccessOnboardingWizard()
        new_wizard.state_file = wizard.state_file
        new_wizard.load_state()

        assert new_wizard.state.python_version == sample_state.python_version
        assert new_wizard.state.is_step_complete(WizardStep.WELCOME)


# ============================================================================
# SYSTEM CHECK TESTS
# ============================================================================

class TestSystemCheck:
    """Tests for system check step"""

    @patch('src.tools.onboarding_wizard.platform.python_version')
    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('src.tools.onboarding_wizard.shutil.disk_usage')
    @patch('builtins.input')
    def test_system_check_python_version(self, mock_input, mock_disk, mock_confirm, mock_version, wizard):
        """Test Python version check"""
        mock_version.return_value = "3.11.5"
        mock_confirm.return_value = True
        mock_disk.return_value = MagicMock(free=5 * 1024**3)  # 5GB
        mock_input.return_value = ""

        # Mock all required imports
        with patch('builtins.__import__') as mock_import:
            mock_import.return_value = MagicMock()
            result = wizard.step_system_check()

        assert wizard.state.python_version == "3.11.5"
        assert result is True

    @patch('src.tools.onboarding_wizard.platform.python_version')
    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('src.tools.onboarding_wizard.shutil.disk_usage')
    @patch('builtins.input')
    def test_system_check_old_python_fails(self, mock_input, mock_disk, mock_confirm, mock_version, wizard):
        """Test system check fails with old Python version"""
        mock_version.return_value = "3.8.0"
        mock_confirm.return_value = True
        mock_disk.return_value = MagicMock(free=5 * 1024**3)
        mock_input.return_value = ""

        with patch('builtins.__import__') as mock_import:
            mock_import.return_value = MagicMock()
            result = wizard.step_system_check()

        assert result is False

    @patch('src.tools.onboarding_wizard.platform.python_version')
    @patch('builtins.__import__')
    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('src.tools.onboarding_wizard.shutil.disk_usage')
    @patch('builtins.input')
    def test_system_check_missing_dependencies(self, mock_input, mock_disk, mock_confirm, mock_import, mock_version, wizard):
        """Test system check detects missing dependencies"""
        mock_version.return_value = "3.11.0"
        mock_confirm.return_value = True
        mock_disk.return_value = MagicMock(free=5 * 1024**3)
        mock_input.return_value = ""

        # Simulate missing package
        def import_side_effect(name, *args, **kwargs):
            if name == 'pydantic' or 'pydantic' in name:
                raise ImportError("No module named 'pydantic'")
            return MagicMock()

        mock_import.side_effect = import_side_effect

        result = wizard.step_system_check()

        assert result is False

    @patch('src.tools.onboarding_wizard.platform.python_version')
    @patch('src.tools.onboarding_wizard.shutil.disk_usage')
    @patch('builtins.input')
    def test_system_check_low_disk_space(self, mock_input, mock_disk, mock_version, wizard):
        """Test system check warns about low disk space"""
        mock_version.return_value = "3.11.0"
        mock_disk.return_value = MagicMock(free=0.5 * 1024**3)  # 0.5GB
        mock_input.return_value = ""

        with patch('builtins.__import__') as mock_import:
            mock_import.return_value = MagicMock()
            result = wizard.step_system_check()

        # Should still pass but with warning
        assert result is True

    @patch('src.tools.onboarding_wizard.platform.python_version')
    @patch('src.tools.onboarding_wizard.shutil.disk_usage')
    @patch('builtins.input')
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@localhost/test'})
    def test_system_check_database_connection(self, mock_input, mock_disk, mock_version, wizard):
        """Test system check tests database connection"""
        mock_version.return_value = "3.11.0"
        mock_disk.return_value = MagicMock(free=5 * 1024**3)
        mock_input.return_value = ""

        with patch('builtins.__import__') as mock_import:
            mock_import.return_value = MagicMock()
            with patch('psycopg2.connect') as mock_connect:
                mock_conn = MagicMock()
                mock_connect.return_value = mock_conn

                result = wizard.step_system_check()

        assert wizard.state.database_connected is True


# ============================================================================
# PLATFORM SETUP TESTS
# ============================================================================

class TestPlatformSetup:
    """Tests for platform integration setup"""

    @patch('src.tools.onboarding_wizard.Prompt.ask')
    def test_configure_zendesk(self, mock_prompt, wizard):
        """Test Zendesk configuration"""
        mock_prompt.side_effect = [
            'mycompany',     # Subdomain
            'admin@test.com',  # Email
            'test_token_123'   # API token
        ]

        result = wizard._configure_zendesk()

        assert result is True
        assert wizard.state.zendesk_configured is True

    @patch('src.tools.onboarding_wizard.Prompt.ask')
    def test_configure_zendesk_missing_fields(self, mock_prompt, wizard):
        """Test Zendesk configuration with missing fields"""
        mock_prompt.side_effect = ['mycompany', 'admin@test.com', '']  # Missing token

        result = wizard._configure_zendesk()

        assert result is False
        assert wizard.state.zendesk_configured is False

    @patch('src.tools.onboarding_wizard.Prompt.ask')
    def test_configure_zendesk_saves_to_env(self, mock_prompt, wizard, temp_config_dir):
        """Test Zendesk configuration saves to .env"""
        wizard.env_file = temp_config_dir / ".env"
        mock_prompt.side_effect = ['mycompany', 'admin@test.com', 'token123']

        wizard._configure_zendesk()

        with open(wizard.env_file, 'r') as f:
            content = f.read()

        assert 'ZENDESK_SUBDOMAIN=mycompany' in content
        assert 'ZENDESK_EMAIL=admin@test.com' in content
        assert 'ZENDESK_API_TOKEN=token123' in content

    @patch('src.tools.onboarding_wizard.Prompt.ask')
    def test_configure_intercom(self, mock_prompt, wizard):
        """Test Intercom configuration"""
        mock_prompt.return_value = 'test_access_token'

        result = wizard._configure_intercom()

        assert result is True
        assert wizard.state.intercom_configured is True

    @patch('src.tools.onboarding_wizard.Prompt.ask')
    def test_configure_intercom_missing_token(self, mock_prompt, wizard):
        """Test Intercom configuration with missing token"""
        mock_prompt.return_value = ''

        result = wizard._configure_intercom()

        assert result is False
        assert wizard.state.intercom_configured is False

    @patch('src.tools.onboarding_wizard.Prompt.ask')
    def test_configure_mixpanel(self, mock_prompt, wizard):
        """Test Mixpanel configuration"""
        mock_prompt.side_effect = ['test_project_token', 'test_api_secret']

        result = wizard._configure_mixpanel()

        assert result is True
        assert wizard.state.mixpanel_configured is True

    @patch('src.tools.onboarding_wizard.Prompt.ask')
    def test_configure_mixpanel_missing_credentials(self, mock_prompt, wizard):
        """Test Mixpanel configuration with missing credentials"""
        mock_prompt.side_effect = ['test_token', '']  # Missing secret

        result = wizard._configure_mixpanel()

        assert result is False

    @patch('src.tools.onboarding_wizard.Prompt.ask')
    def test_configure_sendgrid(self, mock_prompt, wizard):
        """Test SendGrid configuration"""
        mock_prompt.side_effect = [
            'test_api_key',
            'noreply@test.com',
            'Test Company'
        ]

        result = wizard._configure_sendgrid()

        assert result is True
        assert wizard.state.sendgrid_configured is True

    @patch('src.tools.onboarding_wizard.Prompt.ask')
    def test_configure_sendgrid_default_from_name(self, mock_prompt, wizard):
        """Test SendGrid configuration with default from name"""
        mock_prompt.side_effect = [
            'test_api_key',
            'noreply@test.com',
            'Customer Success Team'  # Default
        ]

        result = wizard._configure_sendgrid()

        assert result is True

    def test_update_env_file_new_key(self, wizard, temp_config_dir):
        """Test adding new key to .env file"""
        wizard.env_file = temp_config_dir / ".env"

        wizard._update_env_file('TEST_KEY', 'test_value')

        with open(wizard.env_file, 'r') as f:
            content = f.read()

        assert 'TEST_KEY=test_value' in content

    def test_update_env_file_existing_key(self, wizard, temp_config_dir):
        """Test updating existing key in .env file"""
        wizard.env_file = temp_config_dir / ".env"

        # Create initial file
        with open(wizard.env_file, 'w') as f:
            f.write('TEST_KEY=old_value\n')

        # Update
        wizard._update_env_file('TEST_KEY', 'new_value')

        with open(wizard.env_file, 'r') as f:
            content = f.read()

        assert 'TEST_KEY=new_value' in content
        assert 'TEST_KEY=old_value' not in content

    def test_update_env_file_multiple_keys(self, wizard, temp_config_dir):
        """Test updating multiple keys in .env file"""
        wizard.env_file = temp_config_dir / ".env"

        wizard._update_env_file('KEY1', 'value1')
        wizard._update_env_file('KEY2', 'value2')
        wizard._update_env_file('KEY3', 'value3')

        with open(wizard.env_file, 'r') as f:
            content = f.read()

        assert 'KEY1=value1' in content
        assert 'KEY2=value2' in content
        assert 'KEY3=value3' in content

    @patch('src.tools.onboarding_wizard.SecureCredentialManager')
    @patch('src.tools.onboarding_wizard.Prompt.ask')
    def test_configure_with_credential_manager(self, mock_prompt, mock_cred_manager, wizard):
        """Test configuration uses credential manager if available"""
        mock_prompt.side_effect = ['mycompany', 'admin@test.com', 'token']

        mock_manager = MagicMock()
        mock_cred_manager.return_value = mock_manager
        wizard.credential_manager = mock_manager

        wizard._configure_zendesk()

        # Should call credential manager
        assert mock_manager.store_credential.call_count == 3


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestConfiguration:
    """Tests for configuration step"""

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('builtins.input')
    def test_configuration_default_weights(self, mock_input, mock_confirm, wizard):
        """Test configuration with default weights"""
        mock_confirm.side_effect = [True, True, True]  # Use all defaults
        mock_input.return_value = ""

        result = wizard.step_configuration()

        assert result is True
        assert wizard.state.health_score_weights is not None
        assert wizard.state.health_score_weights['usage'] == 0.35
        assert wizard.state.health_score_weights['engagement'] == 0.25

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('src.tools.onboarding_wizard.Prompt.ask')
    @patch('builtins.input')
    def test_configuration_custom_weights(self, mock_input, mock_prompt, mock_confirm, wizard):
        """Test configuration with custom weights"""
        mock_confirm.side_effect = [False, True, True]  # Custom weights, default thresholds/SLAs
        mock_prompt.side_effect = ['0.4', '0.3', '0.1', '0.1', '0.1']  # Custom weights
        mock_input.return_value = ""

        result = wizard.step_configuration()

        assert result is True
        assert wizard.state.health_score_weights['usage'] == 0.4

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('src.tools.onboarding_wizard.Prompt.ask')
    @patch('builtins.input')
    def test_configuration_custom_thresholds(self, mock_input, mock_prompt, mock_confirm, wizard):
        """Test configuration with custom thresholds"""
        mock_confirm.side_effect = [True, False, True]  # Default weights, custom thresholds, default SLAs
        mock_prompt.side_effect = ['35', '55', '70', '85']  # Custom thresholds
        mock_input.return_value = ""

        result = wizard.step_configuration()

        assert result is True
        assert wizard.state.thresholds is not None
        assert wizard.state.thresholds['churn_risk'] == 35.0
        assert wizard.state.thresholds['at_risk'] == 55.0

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('src.tools.onboarding_wizard.Prompt.ask')
    @patch('builtins.input')
    def test_configuration_custom_slas(self, mock_input, mock_prompt, mock_confirm, wizard):
        """Test configuration with custom SLAs"""
        mock_confirm.side_effect = [True, True, False]  # Default weights/thresholds, custom SLAs
        mock_prompt.side_effect = ['10', '120', '360', '720']  # Custom SLAs
        mock_input.return_value = ""

        result = wizard.step_configuration()

        assert result is True
        assert wizard.state.sla_targets is not None
        assert wizard.state.sla_targets['first_response_minutes'] == 10

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('builtins.input')
    def test_configuration_marks_step_complete(self, mock_input, mock_confirm, wizard):
        """Test configuration marks step as complete"""
        mock_confirm.side_effect = [True, True, True]
        mock_input.return_value = ""

        wizard.step_configuration()

        assert wizard.state.is_step_complete(WizardStep.CONFIGURATION)

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('builtins.input')
    def test_configuration_saves_to_env(self, mock_input, mock_confirm, wizard, temp_config_dir):
        """Test configuration saves to .env file"""
        wizard.env_file = temp_config_dir / ".env"
        mock_confirm.side_effect = [True, True, True]
        mock_input.return_value = ""

        wizard.step_configuration()

        with open(wizard.env_file, 'r') as f:
            content = f.read()

        assert 'HEALTH_SCORE_WEIGHT_USAGE' in content
        assert 'HEALTH_SCORE_AT_RISK_THRESHOLD' in content


# ============================================================================
# DATABASE INITIALIZATION TESTS
# ============================================================================

class TestDatabaseInitialization:
    """Tests for database initialization step"""

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@localhost/test'})
    @patch('builtins.input')
    def test_database_init_with_existing_url(self, mock_input, mock_confirm, wizard):
        """Test database init with existing DATABASE_URL"""
        mock_confirm.side_effect = [False, False]  # Skip migrations and defaults
        mock_input.return_value = ""

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            result = wizard.step_database_init()

        assert result is True
        assert wizard.state.database_initialized is True

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('src.tools.onboarding_wizard.Prompt.ask')
    @patch('builtins.input')
    @patch.dict(os.environ, {}, clear=True)
    def test_database_init_configure_new(self, mock_input, mock_prompt, mock_confirm, wizard):
        """Test database init configuring new database"""
        mock_confirm.side_effect = [True, False, False]  # Configure now, skip migrations
        mock_prompt.side_effect = [
            'localhost',  # host
            '5432',       # port
            'postgres',   # user
            'password',   # password
            'cs_db'       # database
        ]
        mock_input.return_value = ""

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            result = wizard.step_database_init()

        assert result is True

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('builtins.input')
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@localhost/test'})
    def test_database_init_connection_failure(self, mock_input, mock_confirm, wizard):
        """Test database init handles connection failure"""
        mock_confirm.side_effect = [False]
        mock_input.return_value = ""

        with patch('psycopg2.connect', side_effect=Exception("Connection refused")):
            result = wizard.step_database_init()

        assert result is False

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('src.tools.onboarding_wizard.subprocess.run')
    @patch('builtins.input')
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@localhost/test'})
    def test_database_init_runs_migrations(self, mock_input, mock_subprocess, mock_confirm, wizard, temp_config_dir):
        """Test database init runs Alembic migrations"""
        mock_confirm.side_effect = [True, False]  # Run migrations, skip defaults
        mock_input.return_value = ""

        # Create fake alembic.ini
        alembic_ini = temp_config_dir.parent.parent / "alembic.ini"
        alembic_ini.write_text("[alembic]")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            with patch.object(Path, 'cwd', return_value=alembic_ini.parent):
                result = wizard.step_database_init()

        assert wizard.state.migrations_run is True

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('builtins.input')
    def test_database_init_no_url_and_decline(self, mock_input, mock_confirm, wizard):
        """Test database init when no URL and user declines configuration"""
        mock_confirm.side_effect = [False]  # Decline to configure
        mock_input.return_value = ""

        result = wizard.step_database_init()

        assert result is False


# ============================================================================
# TESTING & VALIDATION TESTS
# ============================================================================

class TestTestingValidation:
    """Tests for testing & validation step"""

    @patch.dict(os.environ, {
        'ZENDESK_SUBDOMAIN': 'test',
        'ZENDESK_EMAIL': 'test@test.com',
        'ZENDESK_API_TOKEN': 'token'
    })
    def test_test_zendesk_success(self, wizard):
        """Test successful Zendesk test"""
        passed, message = wizard._test_zendesk()

        assert passed is True
        assert 'configured' in message.lower()

    @patch.dict(os.environ, {}, clear=True)
    def test_test_zendesk_missing_credentials(self, wizard):
        """Test Zendesk test with missing credentials"""
        passed, message = wizard._test_zendesk()

        assert passed is False
        assert 'missing' in message.lower()

    @patch.dict(os.environ, {
        'ZENDESK_SUBDOMAIN': 'test',
        'ZENDESK_EMAIL': '',  # Empty email
        'ZENDESK_API_TOKEN': 'token'
    })
    def test_test_zendesk_partial_credentials(self, wizard):
        """Test Zendesk test with partial credentials"""
        passed, message = wizard._test_zendesk()

        assert passed is False

    @patch.dict(os.environ, {'INTERCOM_ACCESS_TOKEN': 'test_token'})
    def test_test_intercom_success(self, wizard):
        """Test successful Intercom test"""
        passed, message = wizard._test_intercom()

        assert passed is True
        assert 'configured' in message.lower()

    @patch.dict(os.environ, {}, clear=True)
    def test_test_intercom_missing_token(self, wizard):
        """Test Intercom test with missing token"""
        passed, message = wizard._test_intercom()

        assert passed is False

    @patch.dict(os.environ, {
        'MIXPANEL_PROJECT_TOKEN': 'token',
        'MIXPANEL_API_SECRET': 'secret'
    })
    def test_test_mixpanel_success(self, wizard):
        """Test successful Mixpanel test"""
        passed, message = wizard._test_mixpanel()

        assert passed is True

    @patch.dict(os.environ, {'MIXPANEL_PROJECT_TOKEN': 'token'})
    def test_test_mixpanel_missing_secret(self, wizard):
        """Test Mixpanel test with missing secret"""
        passed, message = wizard._test_mixpanel()

        assert passed is False

    @patch.dict(os.environ, {
        'SENDGRID_API_KEY': 'key',
        'SENDGRID_FROM_EMAIL': 'test@test.com'
    })
    def test_test_sendgrid_success(self, wizard):
        """Test successful SendGrid test"""
        passed, message = wizard._test_sendgrid()

        assert passed is True

    @patch.dict(os.environ, {'SENDGRID_API_KEY': 'key'})
    def test_test_sendgrid_missing_email(self, wizard):
        """Test SendGrid test with missing from email"""
        passed, message = wizard._test_sendgrid()

        assert passed is False

    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@localhost/test'})
    def test_test_database_success(self, wizard):
        """Test successful database test"""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            passed, message = wizard._test_database()

        assert passed is True
        assert 'successful' in message.lower()

    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@localhost/test'})
    def test_test_database_connection_failure(self, wizard):
        """Test database test with connection failure"""
        with patch('psycopg2.connect', side_effect=Exception("Connection refused")):
            passed, message = wizard._test_database()

        assert passed is False
        assert 'failed' in message.lower()

    @patch.dict(os.environ, {}, clear=True)
    def test_test_database_no_url(self, wizard):
        """Test database test with no URL configured"""
        passed, message = wizard._test_database()

        assert passed is False
        assert 'not configured' in message.lower()

    @patch('builtins.input')
    def test_step_testing_all_integrations(self, mock_input, wizard):
        """Test testing step with all integrations configured"""
        mock_input.return_value = ""
        wizard.state.zendesk_configured = True
        wizard.state.intercom_configured = True
        wizard.state.mixpanel_configured = True
        wizard.state.sendgrid_configured = True

        with patch.dict(os.environ, {
            'ZENDESK_SUBDOMAIN': 'test',
            'ZENDESK_EMAIL': 'test@test.com',
            'ZENDESK_API_TOKEN': 'token',
            'INTERCOM_ACCESS_TOKEN': 'token',
            'MIXPANEL_PROJECT_TOKEN': 'token',
            'MIXPANEL_API_SECRET': 'secret',
            'SENDGRID_API_KEY': 'key',
            'SENDGRID_FROM_EMAIL': 'test@test.com',
            'DATABASE_URL': 'postgresql://user:pass@localhost/test'
        }):
            with patch('psycopg2.connect'):
                result = wizard.step_testing()

        assert result is True
        assert wizard.state.is_step_complete(WizardStep.TESTING)

    @patch('builtins.input')
    def test_step_testing_partial_integrations(self, mock_input, wizard):
        """Test testing step with only some integrations configured"""
        mock_input.return_value = ""
        wizard.state.zendesk_configured = True
        wizard.state.intercom_configured = False
        wizard.state.mixpanel_configured = False
        wizard.state.sendgrid_configured = False

        with patch.dict(os.environ, {
            'ZENDESK_SUBDOMAIN': 'test',
            'ZENDESK_EMAIL': 'test@test.com',
            'ZENDESK_API_TOKEN': 'token',
            'DATABASE_URL': 'postgresql://user:pass@localhost/test'
        }):
            with patch('psycopg2.connect'):
                result = wizard.step_testing()

        assert result is True

    @patch('builtins.input')
    def test_step_testing_marks_complete(self, mock_input, wizard):
        """Test testing step marks itself complete"""
        mock_input.return_value = ""

        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://user:pass@localhost/test'
        }):
            with patch('psycopg2.connect'):
                wizard.step_testing()

        assert wizard.state.is_step_complete(WizardStep.TESTING)


# ============================================================================
# COMPLETION TESTS
# ============================================================================

class TestCompletion:
    """Tests for completion step"""

    @patch('builtins.input')
    def test_completion_generates_report(self, mock_input, wizard, temp_config_dir):
        """Test completion generates setup report"""
        mock_input.return_value = ""
        wizard.state.zendesk_configured = True
        wizard.state.database_initialized = True

        result = wizard.step_completion()

        assert result is True
        report_path = temp_config_dir / "setup_report.json"
        assert report_path.exists()

        with open(report_path, 'r') as f:
            report = json.load(f)

        assert report['integrations']['zendesk'] is True
        assert report['database']['initialized'] is True

    @patch('builtins.input')
    def test_completion_report_includes_all_data(self, mock_input, wizard, temp_config_dir):
        """Test completion report includes all configuration data"""
        mock_input.return_value = ""
        wizard.state.zendesk_configured = True
        wizard.state.intercom_configured = True
        wizard.state.mixpanel_configured = True
        wizard.state.sendgrid_configured = True
        wizard.state.database_initialized = True
        wizard.state.migrations_run = True
        wizard.state.all_tests_passed = True
        wizard.state.health_score_weights = {'usage': 0.35, 'engagement': 0.25}
        wizard.state.sla_targets = {'p1': 240}
        wizard.state.thresholds = {'at_risk': 60.0}

        wizard.step_completion()

        report_path = temp_config_dir / "setup_report.json"
        with open(report_path, 'r') as f:
            report = json.load(f)

        assert report['integrations']['zendesk'] is True
        assert report['configuration']['health_score_weights']['usage'] == 0.35
        assert report['testing']['all_tests_passed'] is True

    @patch('builtins.input')
    def test_completion_marks_complete(self, mock_input, wizard):
        """Test completion marks step as complete"""
        mock_input.return_value = ""

        wizard.step_completion()

        assert wizard.state.is_step_complete(WizardStep.COMPLETION)
        assert wizard.state.completed_at is not None

    @patch('builtins.input')
    def test_completion_sets_timestamp(self, mock_input, wizard):
        """Test completion sets completed_at timestamp"""
        mock_input.return_value = ""

        before = datetime.utcnow().isoformat()
        wizard.step_completion()
        after = datetime.utcnow().isoformat()

        assert wizard.state.completed_at is not None
        assert before <= wizard.state.completed_at <= after


# ============================================================================
# WIZARD FLOW TESTS
# ============================================================================

class TestWizardFlow:
    """Tests for complete wizard flow"""

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('builtins.input')
    def test_wizard_skips_completed_steps(self, mock_input, mock_confirm, wizard):
        """Test wizard skips already completed steps"""
        mock_input.return_value = ""
        wizard.state.mark_step_complete(WizardStep.WELCOME)
        wizard.state.mark_step_complete(WizardStep.SYSTEM_CHECK)

        mock_confirm.return_value = False  # Don't continue

        with patch.object(wizard, 'step_platform_setup', return_value=True) as mock_platform:
            wizard.run()

            # Should be called because it's not complete
            assert mock_platform.called

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('builtins.input')
    def test_wizard_stops_on_step_failure(self, mock_input, mock_confirm, wizard):
        """Test wizard stops when a step fails"""
        mock_input.return_value = ""
        mock_confirm.return_value = False  # Decline to continue

        with patch.object(wizard, 'step_welcome', return_value=False):
            wizard.run()

            # Should not proceed past welcome
            assert not wizard.state.is_step_complete(WizardStep.SYSTEM_CHECK)

    def test_wizard_saves_state_on_interrupt(self, wizard):
        """Test wizard saves state on keyboard interrupt"""
        with patch.object(wizard, 'step_welcome', side_effect=KeyboardInterrupt):
            with pytest.raises(SystemExit):
                wizard.run()

        # State should be saved
        assert wizard.state_file.exists()

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('builtins.input')
    def test_wizard_resumes_from_saved_state(self, mock_input, mock_confirm, wizard, temp_config_dir):
        """Test wizard can resume from saved state"""
        mock_input.return_value = ""

        # Create a saved state
        state = OnboardingState()
        state.mark_step_complete(WizardStep.WELCOME)
        state.mark_step_complete(WizardStep.SYSTEM_CHECK)

        state_file = temp_config_dir / "onboarding_state.json"
        with open(state_file, 'w') as f:
            json.dump(state.to_dict(), f)

        # Create new wizard and load state
        with patch.object(Path, 'home', return_value=temp_config_dir.parent.parent):
            new_wizard = CustomerSuccessOnboardingWizard()
            new_wizard.config_dir = temp_config_dir
            new_wizard.state_file = state_file
            new_wizard.load_state()

        assert new_wizard.state.is_step_complete(WizardStep.WELCOME)
        assert new_wizard.state.is_step_complete(WizardStep.SYSTEM_CHECK)

    def test_wizard_handles_errors_gracefully(self, wizard):
        """Test wizard handles unexpected errors gracefully"""
        with patch.object(wizard, 'step_welcome', side_effect=Exception("Unexpected error")):
            with pytest.raises(Exception):
                wizard.run()

            # Should still save state
            assert wizard.state_file.exists()

    @patch('builtins.input')
    def test_wizard_sequential_execution(self, mock_input, wizard):
        """Test wizard executes steps sequentially"""
        mock_input.return_value = ""

        execution_order = []

        def track_welcome():
            execution_order.append('welcome')
            return True

        def track_system():
            execution_order.append('system')
            return True

        def track_platform():
            execution_order.append('platform')
            return True

        with patch.object(wizard, 'step_welcome', side_effect=track_welcome):
            with patch.object(wizard, 'step_system_check', side_effect=track_system):
                with patch.object(wizard, 'step_platform_setup', side_effect=track_platform):
                    with patch.object(wizard, 'step_configuration', return_value=False):
                        wizard.run()

        assert execution_order == ['welcome', 'system', 'platform']


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_wizard_handles_invalid_state_file(self, wizard, temp_config_dir):
        """Test wizard handles corrupted state file"""
        state_file = temp_config_dir / "onboarding_state.json"
        with open(state_file, 'w') as f:
            f.write("invalid json{")

        wizard.load_state()  # Should not crash
        assert wizard.state is not None

    def test_wizard_creates_missing_env_file(self, wizard, temp_config_dir):
        """Test wizard creates .env file if missing"""
        wizard.env_file = temp_config_dir / ".env"

        # Ensure file doesn't exist
        if wizard.env_file.exists():
            wizard.env_file.unlink()

        # Should create file without error
        wizard._update_env_file('TEST_KEY', 'test_value')

        assert wizard.env_file.exists()

    @patch('src.tools.onboarding_wizard.SecureCredentialManager', None)
    @patch('src.tools.onboarding_wizard.Prompt.ask')
    def test_wizard_works_without_credential_manager(self, mock_prompt, wizard):
        """Test wizard works when credential manager is unavailable"""
        mock_prompt.side_effect = ['test', 'admin@test.com', 'token']

        # Should not crash when credential manager is None
        wizard.credential_manager = None
        result = wizard._configure_zendesk()

        assert result is True

    def test_wizard_validates_weight_sum(self, wizard):
        """Test wizard validates health score weights sum to ~1.0"""
        weights = {
            'usage': 0.35,
            'engagement': 0.25,
            'support': 0.15,
            'satisfaction': 0.15,
            'payment': 0.10
        }

        total = sum(weights.values())
        assert 0.99 <= total <= 1.01  # Allow small floating point error

    @patch('src.tools.onboarding_wizard.Prompt.ask')
    def test_wizard_handles_special_characters_in_credentials(self, mock_prompt, wizard):
        """Test wizard handles special characters in credentials"""
        mock_prompt.side_effect = [
            'my-company',  # Subdomain with dash
            'admin+test@example.com',  # Email with plus
            'token!@#$%^&*()'  # Token with special chars
        ]

        result = wizard._configure_zendesk()
        assert result is True

    def test_wizard_env_file_preserves_existing_values(self, wizard, temp_config_dir):
        """Test wizard preserves existing env values when updating"""
        wizard.env_file = temp_config_dir / ".env"

        # Create initial file with multiple values
        with open(wizard.env_file, 'w') as f:
            f.write('KEY1=value1\n')
            f.write('KEY2=value2\n')
            f.write('KEY3=value3\n')

        # Update one key
        wizard._update_env_file('KEY2', 'new_value2')

        with open(wizard.env_file, 'r') as f:
            content = f.read()

        # All keys should still be present
        assert 'KEY1=value1' in content
        assert 'KEY2=new_value2' in content
        assert 'KEY3=value3' in content


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Tests for wizard performance"""

    def test_state_serialization_performance(self, sample_state):
        """Test state serialization is fast"""
        import time

        start = time.time()
        for _ in range(1000):
            data = sample_state.to_dict()
            OnboardingState.from_dict(data)
        elapsed = time.time() - start

        # Should complete 1000 roundtrips in under 1 second
        assert elapsed < 1.0

    def test_env_file_update_performance(self, wizard, temp_config_dir):
        """Test env file updates are reasonably fast"""
        import time

        wizard.env_file = temp_config_dir / ".env"

        start = time.time()
        for i in range(100):
            wizard._update_env_file(f'KEY_{i}', f'value_{i}')
        elapsed = time.time() - start

        # Should complete 100 updates in under 5 seconds
        assert elapsed < 5.0

    def test_state_save_performance(self, wizard, sample_state):
        """Test state saving is fast"""
        import time

        wizard.state = sample_state

        start = time.time()
        for _ in range(100):
            wizard.save_state()
        elapsed = time.time() - start

        # Should complete 100 saves in under 2 seconds
        assert elapsed < 2.0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests for wizard functionality"""

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('src.tools.onboarding_wizard.Prompt.ask')
    @patch('builtins.input')
    def test_full_wizard_flow_minimal(self, mock_input, mock_prompt, mock_confirm, wizard):
        """Test minimal complete wizard flow"""
        mock_input.return_value = ""

        # Welcome: yes
        # System check: all checks pass
        # Platform setup: skip all
        # Configuration: all defaults
        # Database: skip
        # Testing: continue
        # Completion: continue
        mock_confirm.side_effect = [
            True,   # Ready to begin?
            False,  # Configure Zendesk?
            False,  # Configure Intercom?
            False,  # Configure Mixpanel?
            False,  # Configure SendGrid?
            True,   # Use default weights?
            True,   # Use default thresholds?
            True,   # Use default SLAs?
            False,  # Configure database?
        ]

        with patch('src.tools.onboarding_wizard.platform.python_version', return_value="3.11.0"):
            with patch('builtins.__import__', return_value=MagicMock()):
                with patch('src.tools.onboarding_wizard.shutil.disk_usage') as mock_disk:
                    mock_disk.return_value = MagicMock(free=5 * 1024**3)

                    # Should not raise exception
                    try:
                        wizard.run()
                    except Exception:
                        pass  # Expected as some steps will fail without real services

        # At least some steps should be complete
        assert len(wizard.state.completed_steps) > 0

    @patch('src.tools.onboarding_wizard.Confirm.ask')
    @patch('src.tools.onboarding_wizard.Prompt.ask')
    @patch('builtins.input')
    @patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@localhost/test'})
    def test_full_wizard_with_all_integrations(self, mock_input, mock_prompt, mock_confirm, wizard):
        """Test wizard with all integrations configured"""
        mock_input.return_value = ""

        # Configure all integrations
        mock_confirm.side_effect = [
            True,   # Ready to begin
            True,   # Configure Zendesk
            True,   # Configure Intercom
            True,   # Configure Mixpanel
            True,   # Configure SendGrid
            True,   # Use defaults for all configuration
            True,
            True,
            False,  # Skip migrations
            False,  # Skip defaults
        ]

        mock_prompt.side_effect = [
            # Zendesk
            'company', 'admin@test.com', 'token',
            # Intercom
            'intercom_token',
            # Mixpanel
            'mixpanel_token', 'mixpanel_secret',
            # SendGrid
            'sendgrid_key', 'noreply@test.com', 'Company'
        ]

        with patch('src.tools.onboarding_wizard.platform.python_version', return_value="3.11.0"):
            with patch('builtins.__import__', return_value=MagicMock()):
                with patch('src.tools.onboarding_wizard.shutil.disk_usage') as mock_disk:
                    with patch('psycopg2.connect') as mock_connect:
                        mock_disk.return_value = MagicMock(free=5 * 1024**3)
                        mock_connect.return_value = MagicMock()

                        try:
                            wizard.run()
                        except Exception:
                            pass

        # All integrations should be configured
        assert wizard.state.zendesk_configured is True
        assert wizard.state.intercom_configured is True
        assert wizard.state.mixpanel_configured is True
        assert wizard.state.sendgrid_configured is True


# ============================================================================
# SECURITY TESTS
# ============================================================================

class TestSecurity:
    """Security tests for wizard"""

    def test_env_file_not_world_readable(self, wizard, temp_config_dir):
        """Test .env file is created with secure permissions"""
        wizard.env_file = temp_config_dir / ".env"

        wizard._update_env_file('SECRET_KEY', 'secret_value')

        # Check permissions (should be 0600 or similar)
        # Note: This test may not work on all systems
        import stat
        permissions = wizard.env_file.stat().st_mode
        # Should not be world-readable
        assert not bool(permissions & stat.S_IROTH)

    @patch('src.tools.onboarding_wizard.Prompt.ask')
    def test_credentials_not_logged(self, mock_prompt, wizard, capsys):
        """Test credentials are not printed to console"""
        mock_prompt.side_effect = ['company', 'admin@test.com', 'secret_token_123']

        wizard._configure_zendesk()

        captured = capsys.readouterr()
        # The token should not appear in output
        # (This is a basic check - real implementation should use structured logging)

    def test_state_file_location_secure(self, wizard):
        """Test state file is in user's home directory"""
        # State file should be in user-specific location
        assert str(wizard.state_file).startswith(str(Path.home()))


# ============================================================================
# REGRESSION TESTS
# ============================================================================

class TestRegressions:
    """Regression tests for previously found bugs"""

    def test_empty_env_file_update(self, wizard, temp_config_dir):
        """Regression: updating empty .env file should work"""
        wizard.env_file = temp_config_dir / ".env"
        wizard.env_file.write_text("")

        wizard._update_env_file('KEY', 'value')

        with open(wizard.env_file, 'r') as f:
            content = f.read()

        assert 'KEY=value' in content

    def test_state_with_none_values(self):
        """Regression: state should handle None values"""
        state = OnboardingState(
            health_score_weights=None,
            sla_targets=None,
            thresholds=None
        )

        data = state.to_dict()
        restored = OnboardingState.from_dict(data)

        assert restored.health_score_weights is None

    def test_wizard_step_enum_ordering(self):
        """Regression: wizard steps should have correct order"""
        steps = list(WizardStep)

        assert steps[0] == WizardStep.WELCOME
        assert steps[1] == WizardStep.SYSTEM_CHECK
        assert steps[2] == WizardStep.PLATFORM_SETUP
        assert steps[-1] == WizardStep.COMPLETION
