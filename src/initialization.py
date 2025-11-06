"""
199|OS Customer Success MCP - Initialization Module
Centralizes all startup, configuration, and agent initialization logic.
"""
import os
import sys
import socket
import shutil
import structlog
from pathlib import Path
from typing import Any, Tuple, List
from importlib.metadata import version, PackageNotFoundError
from packaging.version import parse as parse_version
from mcp.server.fastmcp import FastMCP

# Import agent components
from src.agents.agent_integration import setup_agent_context
from src.agents.enhanced_agent_system import EnhancedSalesAgent  # Will update class name


def validate_dependencies() -> Tuple[bool, List[str], List[str]]:
    """
    Validate that all required Python packages are installed and meet minimum version requirements.

    Returns:
        Tuple of (success: bool, errors: List[str], warnings: List[str])
    """
    errors = []
    warnings = []

    # Required packages with minimum versions
    required_packages = {
        'fastmcp': '0.3.0',
        'mcp': '0.9.0',
        'pydantic': '2.0.0',
        'structlog': '23.0.0',
        'python-dotenv': '1.0.0',
        'sqlalchemy': '2.0.0',
        'alembic': '1.16.0',
        'psycopg2-binary': '2.9.0',
        'aiohttp': '3.9.0',
        'cryptography': '41.0.0',
    }

    # Optional packages (for platform integrations)
    optional_packages = {
        'zenpy': '2.0.42',
        'python-intercom': '4.2.0',
        'mixpanel': '4.10.0',
        'sendgrid': '6.10.0',
    }

    # Check required packages
    for package_name, min_version in required_packages.items():
        try:
            installed_version = version(package_name)
            if parse_version(installed_version) < parse_version(min_version):
                errors.append(
                    f"Package '{package_name}' version {installed_version} is installed, "
                    f"but version {min_version}+ is required"
                )
        except PackageNotFoundError:
            errors.append(f"Required package '{package_name}' is not installed")

    # Check optional packages
    for package_name, min_version in optional_packages.items():
        try:
            installed_version = version(package_name)
            if parse_version(installed_version) < parse_version(min_version):
                warnings.append(
                    f"Optional package '{package_name}' version {installed_version} is installed, "
                    f"but version {min_version}+ is recommended"
                )
        except PackageNotFoundError:
            warnings.append(
                f"Optional package '{package_name}' is not installed. "
                f"Some platform integrations may not be available."
            )

    success = len(errors) == 0
    return success, errors, warnings


def validate_configuration_files() -> Tuple[bool, List[str], List[str]]:
    """
    Validate configuration files and environment variables.

    Returns:
        Tuple of (success: bool, errors: List[str], warnings: List[str])
    """
    errors = []
    warnings = []

    # Check .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        warnings.append(
            ".env file not found. Using environment variables or defaults. "
            "Run onboarding wizard or copy .env.example to .env"
        )
    else:
        # Check file permissions (should not be world-readable)
        if os.name != 'nt':  # Skip on Windows
            file_stat = env_file.stat()
            if file_stat.st_mode & 0o004:  # World-readable
                warnings.append(
                    ".env file is world-readable. Run: chmod 600 .env"
                )

    # Check required environment variables
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'ENCRYPTION_KEY',
    ]

    for var in required_vars:
        if not os.getenv(var):
            errors.append(
                f"Required environment variable '{var}' is not set. "
                f"Run onboarding wizard or set in .env file"
            )

    # Validate health score weights sum to 1.0
    health_weights = [
        'HEALTH_SCORE_WEIGHT_USAGE',
        'HEALTH_SCORE_WEIGHT_ENGAGEMENT',
        'HEALTH_SCORE_WEIGHT_SUPPORT',
        'HEALTH_SCORE_WEIGHT_SATISFACTION',
        'HEALTH_SCORE_WEIGHT_PAYMENT',
    ]

    weights_sum = 0.0
    all_weights_present = True
    for weight_var in health_weights:
        weight_value = os.getenv(weight_var)
        if weight_value:
            try:
                weights_sum += float(weight_value)
            except ValueError:
                errors.append(f"Invalid value for {weight_var}: must be a number")
        else:
            all_weights_present = False

    if all_weights_present and abs(weights_sum - 1.0) > 0.01:
        errors.append(
            f"Health score weights sum to {weights_sum:.2f}, but must sum to 1.0"
        )

    # Validate thresholds are positive numbers
    threshold_vars = [
        'HEALTH_SCORE_AT_RISK_THRESHOLD',
        'HEALTH_SCORE_HEALTHY_THRESHOLD',
        'HEALTH_SCORE_CHAMPION_THRESHOLD',
        'TIME_TO_VALUE_TARGET',
    ]

    for threshold_var in threshold_vars:
        threshold_value = os.getenv(threshold_var)
        if threshold_value:
            try:
                value = float(threshold_value)
                if value <= 0:
                    errors.append(f"{threshold_var} must be a positive number")
            except ValueError:
                errors.append(f"Invalid value for {threshold_var}: must be a number")

    # Check credential directory permissions
    cred_dir = Path('credentials')
    if cred_dir.exists():
        if os.name != 'nt':  # Skip on Windows
            dir_stat = cred_dir.stat()
            if dir_stat.st_mode & 0o077:  # Group or world accessible
                warnings.append(
                    "credentials/ directory has loose permissions. Run: chmod 700 credentials/"
                )

    success = len(errors) == 0
    return success, errors, warnings


def validate_startup_health() -> Tuple[bool, List[str], List[str]]:
    """
    Validate system health: database connectivity, disk space, ports, etc.

    Returns:
        Tuple of (success: bool, errors: List[str], warnings: List[str])
    """
    errors = []
    warnings = []

    # Test PostgreSQL connection
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        try:
            import psycopg2
            from urllib.parse import urlparse

            parsed = urlparse(database_url)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:] if parsed.path else 'postgres',
                connect_timeout=5
            )
            conn.close()
        except Exception as e:
            errors.append(f"PostgreSQL connection failed: {str(e)}")

    # Test Redis connection
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        try:
            import redis
            from urllib.parse import urlparse

            parsed = urlparse(redis_url)
            r = redis.Redis(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 6379,
                password=os.getenv('REDIS_PASSWORD'),
                socket_connect_timeout=5
            )
            r.ping()
            r.close()
        except Exception as e:
            errors.append(f"Redis connection failed: {str(e)}")

    # Test write permissions to required directories
    required_dirs = ['logs', 'data', 'credentials']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)

        test_file = dir_path / '.write_test'
        try:
            test_file.write_text('test')
            test_file.unlink()
        except Exception as e:
            errors.append(f"Cannot write to {dir_name}/ directory: {str(e)}")

    # Verify disk space (>1GB available)
    try:
        stat = shutil.disk_usage('.')
        available_gb = stat.free / (1024**3)
        if available_gb < 1.0:
            warnings.append(
                f"Low disk space: {available_gb:.2f}GB available. "
                f"At least 1GB recommended."
            )
    except Exception as e:
        warnings.append(f"Could not check disk space: {str(e)}")

    # Check port 8080 is available
    port = int(os.getenv('SERVER_PORT', 8080))
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()

        if result == 0:
            warnings.append(
                f"Port {port} is already in use. Server may fail to start."
            )
    except Exception as e:
        warnings.append(f"Could not check port {port}: {str(e)}")

    # Ping enabled platform integrations (optional check)
    integration_checks = {
        'ZENDESK': ('ZENDESK_SUBDOMAIN', 'ZENDESK_EMAIL', 'ZENDESK_API_TOKEN'),
        'INTERCOM': ('INTERCOM_ACCESS_TOKEN',),
        'MIXPANEL': ('MIXPANEL_PROJECT_TOKEN',),
        'SENDGRID': ('SENDGRID_API_KEY',),
    }

    for integration_name, required_vars in integration_checks.items():
        enabled = os.getenv(f'MCP_ENABLE_{integration_name}', 'false').lower() == 'true'
        if enabled:
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                warnings.append(
                    f"{integration_name} is enabled but missing credentials: "
                    f"{', '.join(missing_vars)}"
                )

    success = len(errors) == 0
    return success, errors, warnings


def validate_security_configuration() -> Tuple[bool, List[str], List[str]]:
    """
    Validate security configuration: encryption keys, JWT secrets, audit logs, etc.

    Returns:
        Tuple of (success: bool, errors: List[str], warnings: List[str])
    """
    errors = []
    warnings = []

    # Check ENCRYPTION_KEY is set and >=32 bytes
    encryption_key = os.getenv('ENCRYPTION_KEY')
    if not encryption_key:
        errors.append(
            "ENCRYPTION_KEY is not set. Generate with: openssl rand -hex 32"
        )
    elif len(encryption_key) < 32:
        errors.append(
            f"ENCRYPTION_KEY is too short ({len(encryption_key)} chars). "
            f"Must be at least 32 bytes. Generate with: openssl rand -hex 32"
        )

    # Check JWT_SECRET is set and >=32 characters
    jwt_secret = os.getenv('JWT_SECRET')
    if not jwt_secret:
        errors.append(
            "JWT_SECRET is not set. Generate with: openssl rand -base64 64"
        )
    elif len(jwt_secret) < 32:
        errors.append(
            f"JWT_SECRET is too short ({len(jwt_secret)} chars). "
            f"Must be at least 32 characters. Generate with: openssl rand -base64 64"
        )

    # Verify credential files directory exists and has proper permissions
    cred_dir = Path('credentials')
    if not cred_dir.exists():
        cred_dir.mkdir(mode=0o700, exist_ok=True)
        warnings.append("Created credentials/ directory with secure permissions")

    # Check audit log directory is writable
    audit_log_dir = Path(os.getenv('AUDIT_LOG_DIR', './config/audit_logs'))
    if not audit_log_dir.exists():
        try:
            audit_log_dir.mkdir(parents=True, mode=0o755, exist_ok=True)
            warnings.append(f"Created audit log directory: {audit_log_dir}")
        except Exception as e:
            errors.append(f"Cannot create audit log directory: {str(e)}")
    else:
        # Test write permissions
        test_file = audit_log_dir / '.write_test'
        try:
            test_file.write_text('test')
            test_file.unlink()
        except Exception as e:
            errors.append(f"Audit log directory is not writable: {str(e)}")

    # Warn if running without HTTPS in production
    if os.getenv('LOG_LEVEL', 'INFO') == 'INFO':  # Proxy for production
        warnings.append(
            "Ensure HTTPS/TLS is enabled in production. "
            "Never transmit credentials over HTTP."
        )

    # Check master password is set
    master_password = os.getenv('MASTER_PASSWORD')
    if not master_password:
        warnings.append(
            "MASTER_PASSWORD is not set. Required for credential encryption. "
            "Generate with: openssl rand -base64 32"
        )
    elif len(master_password) < 16:
        warnings.append(
            f"MASTER_PASSWORD is weak ({len(master_password)} chars). "
            f"Use at least 16 characters."
        )

    success = len(errors) == 0
    return success, errors, warnings


def setup_logging() -> Any:
    """
    Configure structlog AND standard Python logging to use stderr for MCP compliance.
    MCP tools must return clean JSON on stdout, so all logging goes to stderr.
    """
    import logging

    # Configure standard Python logging to use stderr (for autonomous tools, etc.)
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(name)s: %(message)s',
        stream=sys.stderr,
        force=True  # Override any existing configuration
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            # Use plain renderer without colors to avoid MCP protocol violations
            structlog.dev.ConsoleRenderer(colors=False)
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True
    )

    logger = structlog.get_logger(__name__)
    logger.info("Logging configured successfully")
    return logger


def initialize_mcp_server() -> Any:
    """
    Initialize FastMCP server instance.

    Returns:
        FastMCP: Configured MCP server instance
    """
    mcp = FastMCP(name="199OS-CustomerSuccess")
    return mcp


def initialize_agents(mcp: FastMCP, config_path: Path = None) -> Any:
    """
    Initialize both Adaptive Agent System and Enhanced Agent System.

    Args:
        mcp: FastMCP server instance for agent registration
        config_path: Path to configuration directory (defaults to project root)

    Returns:
        tuple: (adaptive_agent, enhanced_agent, learning_feedback_tool)
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent

    # Initialize Adaptive Agent System
    adaptive_agent, learning_feedback_tool = setup_agent_context(mcp, config_path)

    # Initialize Enhanced Agent System (using Sales agent as base for now)
    enhanced_agent = EnhancedSalesAgent(config_path)

    # Store agent globally for decorator access
    global GLOBAL_AGENT
    GLOBAL_AGENT = adaptive_agent

    return adaptive_agent, enhanced_agent, learning_feedback_tool


def register_tools(mcp: FastMCP) -> Any:
    """
    Register all tools from organized tool modules.

    Args:
        mcp: FastMCP server instance
    """
    from src.tools import register_all_tools
    register_all_tools(mcp)


def validate_python_version() -> Any:
    """
    Validate Python version meets minimum requirements.

    Raises:
        RuntimeError: If Python version is too old
    """
    import sys

    logger = structlog.get_logger(__name__)

    required_major = 3
    required_minor = 10

    current_version = sys.version_info

    if current_version.major < required_major or (
        current_version.major == required_major and current_version.minor < required_minor
    ):
        error_msg = (
            f"Python {required_major}.{required_minor}+ required. "
            f"Current version: {current_version.major}.{current_version.minor}"
        )
        logger.error("python_version_check_failed", error=error_msg)
        raise RuntimeError(error_msg)

    logger.info(
        "python_version_validated",
        version=f"{current_version.major}.{current_version.minor}.{current_version.micro}"
    )


def run_startup_validation(
    skip_validation: bool = False,
    strict: bool = False
) -> Tuple[bool, int, int]:
    """
    Run all startup validation checks and display results.

    Args:
        skip_validation: If True, skip all validation checks
        strict: If True, treat warnings as errors

    Returns:
        Tuple of (success: bool, total_errors: int, total_warnings: int)
    """
    from datetime import datetime

    logger = structlog.get_logger(__name__)

    if skip_validation:
        logger.warning("Validation skipped via --skip-validation flag")
        return True, 0, 0

    logger.info("Starting startup validation...")

    # Track timing
    start_time = datetime.now()

    all_errors = []
    all_warnings = []

    # Step 1: Validate Python version (already exists)
    try:
        validate_python_version()
        logger.info("Python version check", status="PASS")
    except RuntimeError as e:
        all_errors.append(f"Python version check failed: {str(e)}")
        logger.error("Python version check", status="FAIL", error=str(e))

    # Step 2: Validate dependencies
    logger.info("Validating dependencies...")
    dep_success, dep_errors, dep_warnings = validate_dependencies()
    all_errors.extend(dep_errors)
    all_warnings.extend(dep_warnings)

    if dep_success:
        logger.info("Dependency validation", status="PASS")
    else:
        logger.error("Dependency validation", status="FAIL", errors=len(dep_errors))

    # Step 3: Validate configuration files
    logger.info("Validating configuration files...")
    config_success, config_errors, config_warnings = validate_configuration_files()
    all_errors.extend(config_errors)
    all_warnings.extend(config_warnings)

    if config_success:
        logger.info("Configuration validation", status="PASS")
    else:
        logger.error("Configuration validation", status="FAIL", errors=len(config_errors))

    # Step 4: Validate security configuration
    logger.info("Validating security configuration...")
    sec_success, sec_errors, sec_warnings = validate_security_configuration()
    all_errors.extend(sec_errors)
    all_warnings.extend(sec_warnings)

    if sec_success:
        logger.info("Security validation", status="PASS")
    else:
        logger.error("Security validation", status="FAIL", errors=len(sec_errors))

    # Step 5: Validate startup health
    logger.info("Validating startup health...")
    health_success, health_errors, health_warnings = validate_startup_health()
    all_errors.extend(health_errors)
    all_warnings.extend(health_warnings)

    if health_success:
        logger.info("Health validation", status="PASS")
    else:
        logger.error("Health validation", status="FAIL", errors=len(health_errors))

    # Calculate timing
    duration = (datetime.now() - start_time).total_seconds()

    # Display summary
    logger.info(
        "Validation summary",
        duration_seconds=f"{duration:.2f}",
        errors=len(all_errors),
        warnings=len(all_warnings)
    )

    # Display errors
    for error in all_errors:
        logger.error("Validation error", message=error)

    # Display warnings
    for warning in all_warnings:
        logger.warning("Validation warning", message=warning)

    # Save to log file
    try:
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / 'startup_validation.log'
        with log_file.open('a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Validation run at {datetime.now().isoformat()}\n")
            f.write(f"Duration: {duration:.2f}s\n")
            f.write(f"Errors: {len(all_errors)}, Warnings: {len(all_warnings)}\n")
            f.write(f"{'='*80}\n")

            if all_errors:
                f.write("\nERRORS:\n")
                for i, error in enumerate(all_errors, 1):
                    f.write(f"  {i}. {error}\n")

            if all_warnings:
                f.write("\nWARNINGS:\n")
                for i, warning in enumerate(all_warnings, 1):
                    f.write(f"  {i}. {warning}\n")
    except Exception as e:
        logger.warning("Could not write validation log", error=str(e))

    # Determine success
    success = len(all_errors) == 0
    if strict and len(all_warnings) > 0:
        logger.error("Validation failed in strict mode (warnings treated as errors)")
        success = False

    return success, len(all_errors), len(all_warnings)


def initialize_all(skip_validation: bool = False, strict: bool = False) -> Any:
    """
    Main initialization function that sets up the entire system.

    Args:
        skip_validation: Skip startup validation checks
        strict: Treat validation warnings as errors

    Returns:
        tuple: (mcp, adaptive_agent, enhanced_agent, logger)
    """
    # Setup logging first
    logger = setup_logging()
    logger.info("Starting 199OS Customer Success MCP Server initialization")

    # Run startup validation
    validation_success, error_count, warning_count = run_startup_validation(
        skip_validation=skip_validation,
        strict=strict
    )

    if not validation_success:
        logger.error(
            "Startup validation failed - cannot start server",
            errors=error_count,
            warnings=warning_count
        )
        logger.error("Run onboarding wizard to configure the system properly")
        sys.exit(1)

    if warning_count > 0:
        logger.warning(
            f"Validation passed with {warning_count} warning(s). "
            f"Some features may not be available."
        )

    # Initialize MCP server
    mcp = initialize_mcp_server()
    logger.info("MCP server initialized", server_name="199OS-CustomerSuccess")

    # Initialize agents
    adaptive_agent, enhanced_agent, learning_feedback_tool = initialize_agents(mcp)
    logger.info("Agent systems initialized")

    # Register all tools
    register_tools(mcp)
    logger.info("All tools registered")

    # Start performance monitoring metrics server
    metrics_port = int(os.getenv('METRICS_PORT', 9090))
    metrics_host = os.getenv('METRICS_HOST', '0.0.0.0')
    prometheus_enabled = os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true'

    if prometheus_enabled:
        try:
            from src.monitoring import start_metrics_server, PROMETHEUS_AVAILABLE

            if PROMETHEUS_AVAILABLE:
                start_metrics_server(port=metrics_port, host=metrics_host)
                logger.info(
                    "Performance monitoring initialized",
                    metrics_url=f"http://{metrics_host}:{metrics_port}/metrics"
                )
            else:
                logger.warning(
                    "Prometheus monitoring requested but prometheus-client not installed. "
                    "Install with: pip install prometheus-client"
                )
        except Exception as e:
            logger.warning(f"Failed to start metrics server: {e}")
    else:
        logger.info("Performance monitoring disabled (PROMETHEUS_ENABLED=false)")

    logger.info("199OS Customer Success MCP Server initialization complete")

    return mcp, adaptive_agent, enhanced_agent, logger
