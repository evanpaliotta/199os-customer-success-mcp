"""
Tests for startup validation functions in src/initialization.py

This module tests the 4-step validation system:
1. validate_dependencies() - Package installation and versions
2. validate_configuration_files() - Environment variables and config files
3. validate_startup_health() - Database connections, disk space, ports
4. validate_security_configuration() - Encryption keys, JWT secrets, permissions
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

# Import only the validation functions to avoid circular dependencies
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# We'll import the functions directly by mocking problematic imports
with patch.dict('sys.modules', {
    'src.agents.agent_integration': MagicMock(),
    'src.agents.enhanced_agent_system': MagicMock(),
    'src.tools': MagicMock(),
}):
    from src.initialization import (
        validate_dependencies,
        validate_configuration_files,
        validate_startup_health,
        validate_security_configuration,
        run_startup_validation,
    )


class TestValidateDependencies:
    """Test suite for validate_dependencies() function"""

    def test_all_required_packages_installed(self):
        """Test that validation passes when all required packages are installed"""
        success, errors, warnings = validate_dependencies()

        # Should succeed if running in proper environment
        assert isinstance(success, bool)
        assert isinstance(errors, list)
        assert isinstance(warnings, list)

    @patch('src.initialization.version')
    def test_missing_required_package(self, mock_version):
        """Test that missing required package generates error"""
        from importlib.metadata import PackageNotFoundError

        mock_version.side_effect = PackageNotFoundError("package not found")

        success, errors, warnings = validate_dependencies()

        assert success is False
        assert len(errors) > 0
        assert any("not installed" in error for error in errors)

    @patch('src.initialization.version')
    def test_outdated_required_package(self, mock_version):
        """Test that outdated required package generates error"""
        # Mock an old version
        mock_version.return_value = "0.1.0"

        success, errors, warnings = validate_dependencies()

        assert success is False
        assert len(errors) > 0
        assert any("version" in error.lower() for error in errors)

    @patch('src.initialization.version')
    def test_missing_optional_package_generates_warning(self, mock_version):
        """Test that missing optional package generates warning, not error"""
        from importlib.metadata import PackageNotFoundError

        def version_side_effect(package_name):
            if package_name in ['zenpy', 'python-intercom', 'mixpanel', 'sendgrid']:
                raise PackageNotFoundError("optional package not found")
            return "999.0.0"  # High version for required packages

        mock_version.side_effect = version_side_effect

        success, errors, warnings = validate_dependencies()

        # Should still succeed despite missing optional packages
        assert success is True
        assert len(errors) == 0
        assert len(warnings) > 0
        assert any("optional" in warning.lower() for warning in warnings)


class TestValidateConfigurationFiles:
    """Test suite for validate_configuration_files() function"""

    def test_missing_env_file_generates_warning(self, monkeypatch, tmp_path):
        """Test that missing .env file generates warning"""
        monkeypatch.chdir(tmp_path)

        success, errors, warnings = validate_configuration_files()

        assert len(warnings) > 0
        assert any(".env" in warning for warning in warnings)

    def test_missing_required_env_vars_generate_errors(self, monkeypatch):
        """Test that missing required environment variables generate errors"""
        # Clear required env vars
        monkeypatch.delenv('DATABASE_URL', raising=False)
        monkeypatch.delenv('REDIS_URL', raising=False)
        monkeypatch.delenv('ENCRYPTION_KEY', raising=False)

        success, errors, warnings = validate_configuration_files()

        assert success is False
        assert len(errors) >= 3
        assert any("DATABASE_URL" in error for error in errors)
        assert any("REDIS_URL" in error for error in errors)
        assert any("ENCRYPTION_KEY" in error for error in errors)

    def test_health_score_weights_sum_validation(self, monkeypatch):
        """Test that health score weights must sum to 1.0"""
        # Set required vars to avoid other errors
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
        monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')
        monkeypatch.setenv('ENCRYPTION_KEY', 'a' * 32)

        # Set weights that don't sum to 1.0
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_USAGE', '0.5')
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_ENGAGEMENT', '0.3')
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_SUPPORT', '0.1')
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_SATISFACTION', '0.05')
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_PAYMENT', '0.01')  # Sum = 0.96

        success, errors, warnings = validate_configuration_files()

        assert success is False
        assert any("sum to 1.0" in error for error in errors)

    def test_health_score_weights_valid_sum(self, monkeypatch):
        """Test that valid health score weights pass validation"""
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
        monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')
        monkeypatch.setenv('ENCRYPTION_KEY', 'a' * 32)

        # Set weights that sum to 1.0
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_USAGE', '0.35')
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_ENGAGEMENT', '0.25')
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_SUPPORT', '0.15')
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_SATISFACTION', '0.15')
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_PAYMENT', '0.10')  # Sum = 1.0

        success, errors, warnings = validate_configuration_files()

        # Should not have weight sum error
        assert not any("sum to 1.0" in error for error in errors)

    def test_invalid_threshold_value(self, monkeypatch):
        """Test that non-numeric threshold values generate errors"""
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
        monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')
        monkeypatch.setenv('ENCRYPTION_KEY', 'a' * 32)
        monkeypatch.setenv('HEALTH_SCORE_AT_RISK_THRESHOLD', 'not-a-number')

        success, errors, warnings = validate_configuration_files()

        assert success is False
        assert any("must be a number" in error for error in errors)

    def test_negative_threshold_value(self, monkeypatch):
        """Test that negative threshold values generate errors"""
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
        monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')
        monkeypatch.setenv('ENCRYPTION_KEY', 'a' * 32)
        monkeypatch.setenv('TIME_TO_VALUE_TARGET', '-10')

        success, errors, warnings = validate_configuration_files()

        assert success is False
        assert any("positive number" in error for error in errors)

    @pytest.mark.skipif(os.name == 'nt', reason="File permissions test not applicable on Windows")
    def test_world_readable_env_file_generates_warning(self, monkeypatch, tmp_path):
        """Test that world-readable .env file generates warning"""
        monkeypatch.chdir(tmp_path)

        # Create .env file with loose permissions
        env_file = tmp_path / '.env'
        env_file.write_text('DATABASE_URL=test')
        env_file.chmod(0o644)  # World-readable

        # Set required env vars
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
        monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')
        monkeypatch.setenv('ENCRYPTION_KEY', 'a' * 32)

        success, errors, warnings = validate_configuration_files()

        assert any("world-readable" in warning for warning in warnings)


class TestValidateStartupHealth:
    """Test suite for validate_startup_health() function"""

    @patch('psycopg2.connect')
    def test_successful_postgresql_connection(self, mock_connect, monkeypatch):
        """Test successful PostgreSQL connection"""
        monkeypatch.setenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/db')

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        success, errors, warnings = validate_startup_health()

        mock_connect.assert_called_once()
        mock_conn.close.assert_called_once()
        # Should not have database connection error
        assert not any("PostgreSQL connection failed" in error for error in errors)

    @patch('psycopg2.connect')
    def test_failed_postgresql_connection(self, mock_connect, monkeypatch):
        """Test failed PostgreSQL connection generates error"""
        monkeypatch.setenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/db')

        mock_connect.side_effect = Exception("Connection refused")

        success, errors, warnings = validate_startup_health()

        assert success is False
        assert any("PostgreSQL connection failed" in error for error in errors)

    @patch('redis.Redis')
    def test_successful_redis_connection(self, mock_redis_class, monkeypatch):
        """Test successful Redis connection"""
        monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')

        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis

        success, errors, warnings = validate_startup_health()

        mock_redis.ping.assert_called_once()
        mock_redis.close.assert_called_once()

    @patch('redis.Redis')
    def test_failed_redis_connection(self, mock_redis_class, monkeypatch):
        """Test failed Redis connection generates error"""
        monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')

        mock_redis = MagicMock()
        mock_redis.ping.side_effect = Exception("Connection refused")
        mock_redis_class.return_value = mock_redis

        success, errors, warnings = validate_startup_health()

        assert success is False
        assert any("Redis connection failed" in error for error in errors)

    def test_write_permissions_to_required_directories(self, monkeypatch, tmp_path):
        """Test write permissions to logs, data, credentials directories"""
        monkeypatch.chdir(tmp_path)

        success, errors, warnings = validate_startup_health()

        # Should create directories and verify write access
        assert (tmp_path / 'logs').exists()
        assert (tmp_path / 'data').exists()
        assert (tmp_path / 'credentials').exists()

    @patch('shutil.disk_usage')
    def test_low_disk_space_generates_warning(self, mock_disk_usage, monkeypatch):
        """Test that low disk space generates warning"""
        # Mock low disk space (0.5 GB)
        mock_usage = MagicMock()
        mock_usage.free = 0.5 * 1024**3
        mock_disk_usage.return_value = mock_usage

        success, errors, warnings = validate_startup_health()

        assert any("disk space" in warning.lower() for warning in warnings)

    @patch('socket.socket')
    def test_port_already_in_use_generates_warning(self, mock_socket_class, monkeypatch):
        """Test that port already in use generates warning"""
        monkeypatch.setenv('SERVER_PORT', '8080')

        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 0  # Port is in use
        mock_socket_class.return_value = mock_socket

        success, errors, warnings = validate_startup_health()

        assert any("already in use" in warning for warning in warnings)

    def test_enabled_integration_missing_credentials(self, monkeypatch):
        """Test that enabled integration with missing credentials generates warning"""
        monkeypatch.setenv('MCP_ENABLE_ZENDESK', 'true')
        monkeypatch.delenv('ZENDESK_SUBDOMAIN', raising=False)
        monkeypatch.delenv('ZENDESK_EMAIL', raising=False)
        monkeypatch.delenv('ZENDESK_API_TOKEN', raising=False)

        success, errors, warnings = validate_startup_health()

        assert any("ZENDESK" in warning and "missing credentials" in warning for warning in warnings)


class TestValidateSecurityConfiguration:
    """Test suite for validate_security_configuration() function"""

    def test_missing_encryption_key_generates_error(self, monkeypatch):
        """Test that missing ENCRYPTION_KEY generates error"""
        monkeypatch.delenv('ENCRYPTION_KEY', raising=False)

        success, errors, warnings = validate_security_configuration()

        assert success is False
        assert any("ENCRYPTION_KEY is not set" in error for error in errors)

    def test_short_encryption_key_generates_error(self, monkeypatch):
        """Test that short ENCRYPTION_KEY generates error"""
        monkeypatch.setenv('ENCRYPTION_KEY', 'short')  # Less than 32 bytes

        success, errors, warnings = validate_security_configuration()

        assert success is False
        assert any("too short" in error for error in errors)

    def test_valid_encryption_key(self, monkeypatch):
        """Test that valid ENCRYPTION_KEY passes validation"""
        monkeypatch.setenv('ENCRYPTION_KEY', 'a' * 32)
        monkeypatch.setenv('JWT_SECRET', 'b' * 32)

        success, errors, warnings = validate_security_configuration()

        # Should not have encryption key error
        assert not any("ENCRYPTION_KEY" in error for error in errors)

    def test_missing_jwt_secret_generates_error(self, monkeypatch):
        """Test that missing JWT_SECRET generates error"""
        monkeypatch.setenv('ENCRYPTION_KEY', 'a' * 32)
        monkeypatch.delenv('JWT_SECRET', raising=False)

        success, errors, warnings = validate_security_configuration()

        assert success is False
        assert any("JWT_SECRET is not set" in error for error in errors)

    def test_short_jwt_secret_generates_error(self, monkeypatch):
        """Test that short JWT_SECRET generates error"""
        monkeypatch.setenv('ENCRYPTION_KEY', 'a' * 32)
        monkeypatch.setenv('JWT_SECRET', 'short')

        success, errors, warnings = validate_security_configuration()

        assert success is False
        assert any("JWT_SECRET" in error and "too short" in error for error in errors)

    def test_audit_log_directory_creation(self, monkeypatch, tmp_path):
        """Test that audit log directory is created if missing"""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv('ENCRYPTION_KEY', 'a' * 32)
        monkeypatch.setenv('JWT_SECRET', 'b' * 32)
        monkeypatch.setenv('AUDIT_LOG_DIR', str(tmp_path / 'audit_logs'))

        success, errors, warnings = validate_security_configuration()

        assert (tmp_path / 'audit_logs').exists()

    def test_missing_master_password_generates_warning(self, monkeypatch):
        """Test that missing MASTER_PASSWORD generates warning"""
        monkeypatch.setenv('ENCRYPTION_KEY', 'a' * 32)
        monkeypatch.setenv('JWT_SECRET', 'b' * 32)
        monkeypatch.delenv('MASTER_PASSWORD', raising=False)

        success, errors, warnings = validate_security_configuration()

        assert any("MASTER_PASSWORD" in warning for warning in warnings)

    def test_weak_master_password_generates_warning(self, monkeypatch):
        """Test that weak MASTER_PASSWORD generates warning"""
        monkeypatch.setenv('ENCRYPTION_KEY', 'a' * 32)
        monkeypatch.setenv('JWT_SECRET', 'b' * 32)
        monkeypatch.setenv('MASTER_PASSWORD', 'weak')  # Less than 16 chars

        success, errors, warnings = validate_security_configuration()

        assert any("weak" in warning.lower() for warning in warnings)


class TestRunStartupValidation:
    """Test suite for run_startup_validation() function"""

    def test_skip_validation_flag(self, monkeypatch):
        """Test that --skip-validation flag skips all validation"""
        success, error_count, warning_count = run_startup_validation(skip_validation=True)

        assert success is True
        assert error_count == 0
        assert warning_count == 0

    @patch('src.initialization.validate_dependencies')
    @patch('src.initialization.validate_configuration_files')
    @patch('src.initialization.validate_startup_health')
    @patch('src.initialization.validate_security_configuration')
    @patch('src.initialization.validate_python_version')
    def test_all_validations_called(
        self,
        mock_python_version,
        mock_security,
        mock_health,
        mock_config,
        mock_deps
    ):
        """Test that all validation functions are called"""
        # Mock successful validations
        mock_deps.return_value = (True, [], [])
        mock_config.return_value = (True, [], [])
        mock_health.return_value = (True, [], [])
        mock_security.return_value = (True, [], [])

        success, error_count, warning_count = run_startup_validation()

        mock_python_version.assert_called_once()
        mock_deps.assert_called_once()
        mock_config.assert_called_once()
        mock_health.assert_called_once()
        mock_security.assert_called_once()

    @patch('src.initialization.validate_dependencies')
    @patch('src.initialization.validate_configuration_files')
    @patch('src.initialization.validate_startup_health')
    @patch('src.initialization.validate_security_configuration')
    @patch('src.initialization.validate_python_version')
    def test_validation_failure_aggregation(
        self,
        mock_python_version,
        mock_security,
        mock_health,
        mock_config,
        mock_deps
    ):
        """Test that errors from all validations are aggregated"""
        # Mock failures
        mock_deps.return_value = (False, ["dep error"], ["dep warning"])
        mock_config.return_value = (False, ["config error"], [])
        mock_health.return_value = (True, [], ["health warning"])
        mock_security.return_value = (False, ["security error"], [])

        success, error_count, warning_count = run_startup_validation()

        assert success is False
        assert error_count == 3  # 3 errors total
        assert warning_count == 2  # 2 warnings total

    @patch('src.initialization.validate_dependencies')
    @patch('src.initialization.validate_configuration_files')
    @patch('src.initialization.validate_startup_health')
    @patch('src.initialization.validate_security_configuration')
    @patch('src.initialization.validate_python_version')
    def test_strict_mode_treats_warnings_as_errors(
        self,
        mock_python_version,
        mock_security,
        mock_health,
        mock_config,
        mock_deps
    ):
        """Test that strict mode treats warnings as errors"""
        # Mock successful validations with warnings
        mock_deps.return_value = (True, [], ["warning 1"])
        mock_config.return_value = (True, [], ["warning 2"])
        mock_health.return_value = (True, [], [])
        mock_security.return_value = (True, [], [])

        # Normal mode - should succeed
        success, error_count, warning_count = run_startup_validation(strict=False)
        assert success is True
        assert error_count == 0
        assert warning_count == 2

        # Strict mode - should fail
        success, error_count, warning_count = run_startup_validation(strict=True)
        assert success is False
        assert error_count == 0
        assert warning_count == 2

    def test_validation_log_file_created(self, monkeypatch, tmp_path):
        """Test that validation results are logged to file"""
        monkeypatch.chdir(tmp_path)

        run_startup_validation()

        log_file = tmp_path / 'logs' / 'startup_validation.log'
        assert log_file.exists()
        assert log_file.stat().st_size > 0


class TestIntegrationScenarios:
    """Integration tests for common validation scenarios"""

    def test_fresh_install_no_config(self, monkeypatch, tmp_path):
        """Test validation on fresh install with no configuration"""
        monkeypatch.chdir(tmp_path)

        # Clear all env vars
        for var in ['DATABASE_URL', 'REDIS_URL', 'ENCRYPTION_KEY', 'JWT_SECRET']:
            monkeypatch.delenv(var, raising=False)

        success, errors, warnings = validate_configuration_files()

        assert success is False
        assert len(errors) >= 3  # Missing required vars

    def test_minimal_valid_configuration(self, monkeypatch, tmp_path):
        """Test validation with minimal valid configuration"""
        monkeypatch.chdir(tmp_path)

        # Set minimal required config
        monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
        monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')
        monkeypatch.setenv('ENCRYPTION_KEY', 'a' * 32)
        monkeypatch.setenv('JWT_SECRET', 'b' * 32)

        success, errors, warnings = validate_configuration_files()

        # Should succeed with minimal config (may have warnings)
        assert success is True

    @patch('psycopg2.connect')
    @patch('redis.Redis')
    def test_production_ready_configuration(
        self,
        mock_redis_class,
        mock_connect,
        monkeypatch,
        tmp_path
    ):
        """Test validation with production-ready configuration"""
        monkeypatch.chdir(tmp_path)

        # Set full production config
        monkeypatch.setenv('DATABASE_URL', 'postgresql://user:pass@db.example.com:5432/prod')
        monkeypatch.setenv('REDIS_URL', 'redis://cache.example.com:6379')
        monkeypatch.setenv('ENCRYPTION_KEY', 'a' * 64)
        monkeypatch.setenv('JWT_SECRET', 'b' * 64)
        monkeypatch.setenv('MASTER_PASSWORD', 'c' * 32)

        # Set health score weights
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_USAGE', '0.35')
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_ENGAGEMENT', '0.25')
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_SUPPORT', '0.15')
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_SATISFACTION', '0.15')
        monkeypatch.setenv('HEALTH_SCORE_WEIGHT_PAYMENT', '0.10')

        # Mock successful connections
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis

        success_config, errors_config, warnings_config = validate_configuration_files()
        success_security, errors_security, warnings_security = validate_security_configuration()
        success_health, errors_health, warnings_health = validate_startup_health()

        # All should succeed
        assert success_config is True
        assert success_security is True
        assert success_health is True
        assert len(errors_config) == 0
        assert len(errors_security) == 0
        assert len(errors_health) == 0
