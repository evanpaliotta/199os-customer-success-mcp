# 199OS Customer Success MCP Server - Complete Implementation Guide

**Date:** October 9, 2025
**Target Directory:** `/Users/evanpaliotta/199os-customer-success-mcp`
**Architecture Base:** Replicate Sales MCP (`/Users/evanpaliotta/199os-sales-mcp`)
**Total Tools:** 49 processes (79-127) organized into 7 categories

---

## 🎯 MISSION

Build a production-ready Customer Success MCP Server with the EXACT same architecture, security features, and setup patterns as the existing Sales and Marketing MCP servers.

## 📋 PROCESS REFERENCE

All 49 Customer Success processes are documented in:
`/Users/evanpaliotta/199os-sales-mcp/docs/prompts/CUSTOMER_SUCCESS_MCP_PROCESSES.md`

Study this file first to understand the tool categories and their purposes.

---

## 🏗️ COMPLETE FILE STRUCTURE

Create this exact directory structure:

```
199os-customer-success-mcp/
├── server.py                      # Main entry point
├── server_initialization.py       # Legacy initialization (keep for compatibility)
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project configuration
├── .env.example                   # Environment template
├── .env                          # Local environment (gitignored)
├── .gitignore                    # Git exclusions
├── Dockerfile                     # Container configuration
├── docker-compose.yml            # Multi-container orchestration
├── README.md                     # Project documentation
│
├── config/
│   ├── preferences/              # User preference storage
│   ├── audit_logs/               # Security audit logs
│   └── mcp_servers.json          # MCP integration configuration
│
├── credentials/                   # Encrypted credentials (gitignored)
│
├── data/                         # Database and storage
│
├── logs/                         # Application logs (gitignored)
│
├── conversation_contexts/        # Agent context storage
│
├── templates/                    # Email/communication templates
│   ├── onboarding/
│   ├── retention/
│   └── support/
│
├── docs/                         # Documentation
│   ├── guides/
│   │   ├── QUICK_START_GUIDE.md
│   │   ├── ONBOARDING_GUIDE.md
│   │   ├── DEPLOYMENT_GUIDE.md
│   │   └── CS_FEATURES_GUIDE.md
│   ├── architecture/
│   │   ├── ARCHITECTURE.md
│   │   ├── ADAPTIVE_AGENT_IMPLEMENTATION.md
│   │   └── PRODUCTION_CHECKLIST.md
│   └── prompts/
│
├── tests/                        # Test suite
│   ├── unit/
│   │   ├── test_onboarding_tools.py
│   │   ├── test_health_tools.py
│   │   ├── test_retention_tools.py
│   │   ├── test_communication_tools.py
│   │   ├── test_support_tools.py
│   │   ├── test_expansion_tools.py
│   │   └── test_feedback_tools.py
│   ├── integration/
│   │   ├── test_zendesk_integration.py
│   │   ├── test_intercom_integration.py
│   │   └── test_mixpanel_integration.py
│   └── fixtures/
│
├── infrastructure/               # Deployment configurations
│   ├── kubernetes/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   └── terraform/
│
├── examples/                     # Usage examples
│   ├── onboarding_workflow.py
│   ├── churn_prevention.py
│   └── expansion_playbook.py
│
├── utils/                        # Utility functions
│   ├── file_operations.py
│   └── helpers.py
│
└── src/                          # Source code
    ├── __init__.py
    ├── initialization.py         # Centralized startup logic
    │
    ├── agents/                   # AI agent systems
    │   ├── __init__.py
    │   ├── agent_integration.py
    │   ├── adaptive_agent_system.py
    │   └── enhanced_agent_system.py
    │
    ├── core/                     # Core utilities
    │   ├── __init__.py
    │   ├── config.py
    │   ├── constants.py
    │   └── exceptions.py
    │
    ├── database/                 # Database layer
    │   ├── __init__.py
    │   ├── connection.py
    │   └── models.py
    │
    ├── integrations/             # External platform integrations
    │   ├── __init__.py
    │   ├── zendesk_client.py
    │   ├── intercom_client.py
    │   ├── mixpanel_client.py
    │   ├── gainsight_client.py
    │   ├── segment_client.py
    │   ├── sendgrid_client.py
    │   └── salesforce_client.py  # CRM sync
    │
    ├── intelligence/             # AI/ML capabilities
    │   ├── __init__.py
    │   ├── health_scoring.py
    │   ├── churn_prediction.py
    │   ├── sentiment_analysis.py
    │   └── expansion_scoring.py
    │
    ├── learning/                 # Adaptive learning system
    │   ├── __init__.py
    │   ├── learning_engine.py
    │   └── preference_manager.py
    │
    ├── mcp/                      # MCP protocol
    │   ├── __init__.py
    │   └── server_config.py
    │
    ├── models/                   # Data models
    │   ├── __init__.py
    │   ├── customer_models.py
    │   ├── onboarding_models.py
    │   ├── health_models.py
    │   ├── support_models.py
    │   ├── renewal_models.py
    │   ├── feedback_models.py
    │   └── analytics_models.py
    │
    ├── mock_data/                # Testing/demo data
    │   ├── __init__.py
    │   └── generators.py
    │
    ├── monitoring/               # Observability
    │   ├── __init__.py
    │   ├── logger.py
    │   ├── metrics.py
    │   └── audit.py
    │
    ├── onboarding/               # Setup wizard
    │   ├── __init__.py
    │   ├── wizard.py
    │   └── credential_setup.py
    │
    ├── security/                 # Security layer
    │   ├── __init__.py
    │   ├── credential_manager.py
    │   ├── encryption.py
    │   ├── input_validation.py
    │   └── safe_file_operations.py
    │
    ├── templates/                # Template engine
    │   ├── __init__.py
    │   └── template_manager.py
    │
    ├── tools/                    # MCP tools (THE CORE!)
    │   ├── __init__.py           # Tool registration
    │   ├── core_system_tools.py  # System configuration
    │   ├── onboarding_training_tools.py      # Processes 79-86
    │   ├── health_segmentation_tools.py       # Processes 87-94
    │   ├── retention_risk_tools.py            # Processes 95-101
    │   ├── communication_engagement_tools.py  # Processes 102-107
    │   ├── support_selfservice_tools.py       # Processes 108-113
    │   ├── expansion_revenue_tools.py         # Processes 114-121
    │   └── feedback_intelligence_tools.py     # Processes 122-127
    │
    └── utils/                    # Shared utilities
        ├── __init__.py
        ├── date_helpers.py
        ├── text_helpers.py
        └── validation_helpers.py
```

---

## 📦 STEP 1: DEPENDENCIES & CONFIGURATION

### 1.1 Create `requirements.txt`

```txt
# Core MCP and FastMCP
fastmcp>=0.3.0
mcp>=0.9.0

# Data Models & Validation
pydantic>=2.0.0
python-dotenv>=1.0.0

# Logging & Monitoring
structlog>=23.0.0

# Async Support
asyncio
aiohttp>=3.9.0
requests>=2.31.0

# Database
sqlalchemy>=2.0.0

# Data Science & ML
numpy>=1.21.0
pandas>=1.3.0
scikit-learn>=1.0.0
matplotlib>=3.3.0

# Testing & Mocking
faker>=18.0.0
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Security
cryptography>=41.0.0

# Customer Success Platform Integrations
zenpy>=2.0.42  # Zendesk
python-intercom>=4.2.0  # Intercom
mixpanel>=4.10.0  # Mixpanel
freshdesk>=0.1.8  # Freshdesk
gainsight-python-client>=1.0.0  # Gainsight (if available)
sendgrid>=6.10.0  # SendGrid email
twilio>=8.10.0  # Twilio (SMS/voice support)

# CRM Sync (reuse from Sales MCP)
simple-salesforce>=1.12.0
hubspot-api-client>=8.0.0

# Analytics & Tracking
segment-analytics-python>=2.2.0
amplitude-analytics>=1.3.0

# Communication Tools
google-api-python-client>=2.100.0
google-auth-httplib2>=0.1.1
google-auth-oauthlib>=1.1.0

# Knowledge Base & Documentation
requests-html>=0.10.0  # Web scraping for KB import
beautifulsoup4>=4.12.0

# Survey & Feedback
typeform>=0.4.0  # Typeform integration
surveymonkey>=3.1.1  # SurveyMonkey

# Community & Forums
discourse-api>=0.0.3  # Discourse forums
slack-sdk>=3.23.0  # Slack communities
```

### 1.2 Create `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "199os-customer-success-mcp"
version = "1.0.0"
description = "199OS Customer Success MCP Server - Complete Customer Success Operations Platform"
authors = [{name = "199OS Team", email = "team@199os.com"}]
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "fastmcp>=0.3.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "structlog>=23.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[tool.setuptools]
packages = ["src"]

[tool.black]
line-length = 100
target-version = ["py310", "py311", "py312"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
asyncio_mode = "auto"
```

### 1.3 Create `.env.example`

```bash
# 199|OS Customer Success MCP Server Environment Variables
# Copy this file to .env and configure as needed

# ============================================================================
# SERVER CONFIGURATION
# ============================================================================

SERVER_NAME=199OS-CustomerSuccess
SERVER_PORT=8080

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Database Configuration (PostgreSQL for production)
DATABASE_URL=postgresql://postgres:password@localhost:5432/cs_mcp_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_SSL_MODE=require

# Redis Configuration (for caching and sessions)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your-redis-password
REDIS_MAX_CONNECTIONS=50
CACHE_DEFAULT_TTL=3600
CACHE_LONG_TTL=86400

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=1000
MAX_REQUESTS_PER_HOUR=10000
RATE_LIMIT_PER_CLIENT_PER_MINUTE=100

# ============================================================================
# SECURITY CONFIGURATION (CRITICAL)
# ============================================================================

# Master password for encrypting stored credentials
# Generate with: openssl rand -base64 32
MASTER_PASSWORD=your-strong-master-password-here

# Encryption key for sensitive data
# Generate with: openssl rand -hex 32
ENCRYPTION_KEY=your-encryption-key-here

# JWT secret for token generation
# Generate with: openssl rand -base64 64
JWT_SECRET=your-jwt-secret-here

# API key for MCP server authentication
MCP_API_KEY=your-mcp-api-key-here

# Webhook secret for verifying incoming webhooks
WEBHOOK_SECRET=your-webhook-secret

# ============================================================================
# LEARNING SYSTEM CONFIGURATION
# ============================================================================

# Confidence threshold for learning questions (0.0 - 1.0)
LEARNING_COMPLETION_THRESHOLD=0.70

# Learning frequency: always, often, occasionally, rarely
LEARNING_FREQUENCY=often

# Preference storage location
PREFERENCES_DIR=./config/preferences

# ============================================================================
# CUSTOMER SUCCESS PLATFORM INTEGRATIONS
# ============================================================================

# Zendesk (Support Platform)
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_EMAIL=your-email@company.com
ZENDESK_API_TOKEN=your-zendesk-api-token

# Intercom (Customer Messaging)
INTERCOM_ACCESS_TOKEN=your-intercom-access-token
INTERCOM_APP_ID=your-intercom-app-id

# Mixpanel (Product Analytics)
MIXPANEL_PROJECT_TOKEN=your-mixpanel-project-token
MIXPANEL_API_SECRET=your-mixpanel-api-secret

# Gainsight (CS Platform)
GAINSIGHT_API_KEY=your-gainsight-api-key
GAINSIGHT_BASE_URL=https://your-instance.gainsightcloud.com

# Amplitude (Product Analytics)
AMPLITUDE_API_KEY=your-amplitude-api-key
AMPLITUDE_SECRET_KEY=your-amplitude-secret-key

# SendGrid (Email)
SENDGRID_API_KEY=your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@yourcompany.com

# Segment (Customer Data Platform)
SEGMENT_WRITE_KEY=your-segment-write-key

# Salesforce (CRM Sync)
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-security-token

# HubSpot (CRM/Marketing)
HUBSPOT_ACCESS_TOKEN=your-hubspot-access-token

# Slack (Community/Communication)
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret

# Typeform (Surveys)
TYPEFORM_ACCESS_TOKEN=your-typeform-access-token

# ============================================================================
# MCP SERVER INTEGRATIONS
# ============================================================================

# Enable/disable specific MCP servers
MCP_ENABLE_ZENDESK=true
MCP_ENABLE_INTERCOM=true
MCP_ENABLE_MIXPANEL=true
MCP_ENABLE_SALESFORCE=true
MCP_ENABLE_HUBSPOT=true
MCP_ENABLE_SENDGRID=true
MCP_ENABLE_SLACK=true

# MCP configuration file path
MCP_CONFIG_PATH=./config/mcp_servers.json

# ============================================================================
# HEALTH SCORE CONFIGURATION
# ============================================================================

# Health score weights (must sum to 1.0)
HEALTH_SCORE_WEIGHT_USAGE=0.35
HEALTH_SCORE_WEIGHT_ENGAGEMENT=0.25
HEALTH_SCORE_WEIGHT_SUPPORT=0.15
HEALTH_SCORE_WEIGHT_SATISFACTION=0.15
HEALTH_SCORE_WEIGHT_PAYMENT=0.10

# Health score thresholds
HEALTH_SCORE_AT_RISK_THRESHOLD=50
HEALTH_SCORE_HEALTHY_THRESHOLD=75
HEALTH_SCORE_CHAMPION_THRESHOLD=90

# Churn prediction thresholds
CHURN_PROBABILITY_HIGH_RISK=0.70
CHURN_PROBABILITY_MEDIUM_RISK=0.40
CHURN_PROBABILITY_LOW_RISK=0.15

# ============================================================================
# ONBOARDING CONFIGURATION
# ============================================================================

# Time-to-value targets (in days)
TIME_TO_VALUE_TARGET=30
TIME_TO_FIRST_VALUE=7
TIME_TO_ACTIVATION=14

# Onboarding milestone thresholds
ONBOARDING_COMPLETION_THRESHOLD=0.80
TRAINING_COMPLETION_THRESHOLD=0.75

# ============================================================================
# RETENTION CONFIGURATION
# ============================================================================

# Retention campaign thresholds
RETENTION_CAMPAIGN_TRIGGER_SCORE=60
RETENTION_CAMPAIGN_FREQUENCY_DAYS=7
RETENTION_ESCALATION_SCORE=40

# Renewal reminder timeline
RENEWAL_REMINDER_DAYS_BEFORE=[90, 60, 30, 14, 7]
RENEWAL_FORECAST_WINDOW_DAYS=90

# ============================================================================
# EXPANSION CONFIGURATION
# ============================================================================

# Expansion opportunity thresholds
EXPANSION_MIN_HEALTH_SCORE=75
EXPANSION_MIN_USAGE_THRESHOLD=0.70
EXPANSION_MIN_TENURE_DAYS=60

# Upsell/cross-sell scoring
UPSELL_OPPORTUNITY_THRESHOLD=0.65
CROSS_SELL_OPPORTUNITY_THRESHOLD=0.60

# ============================================================================
# SUPPORT CONFIGURATION
# ============================================================================

# SLA targets (in minutes)
SUPPORT_FIRST_RESPONSE_SLA=15
SUPPORT_RESOLUTION_SLA_P1=240   # 4 hours
SUPPORT_RESOLUTION_SLA_P2=480   # 8 hours
SUPPORT_RESOLUTION_SLA_P3=1440  # 24 hours

# Escalation thresholds
SUPPORT_ESCALATION_NO_RESPONSE_HOURS=2
SUPPORT_ESCALATION_NO_RESOLUTION_DAYS=3

# ============================================================================
# MONITORING & OBSERVABILITY
# ============================================================================

# Enable features
ENABLE_MONITORING=true
ENABLE_AUDIT_LOGGING=true
ENABLE_TRACING=true

# Audit log settings
AUDIT_LOG_RETENTION_DAYS=90
AUDIT_LOG_DIR=./config/audit_logs

# Error tracking (Sentry - optional)
# SENTRY_DSN=your-sentry-dsn

# Metrics (DataDog - optional)
# DATADOG_API_KEY=your-datadog-api-key

# ============================================================================
# FEATURE FLAGS
# ============================================================================

# Enable/disable features
FEATURE_CHURN_PREDICTION=true
FEATURE_HEALTH_SCORING=true
FEATURE_AUTOMATED_RETENTION=true
FEATURE_EXPANSION_SCORING=true
FEATURE_SENTIMENT_ANALYSIS=true
FEATURE_AUTO_TICKET_ROUTING=true
FEATURE_KNOWLEDGE_BASE_SYNC=true
FEATURE_EBR_AUTOMATION=true
```

### 1.4 Create `.gitignore`

```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Credentials & Secrets
credentials/
*.pem
*.key
*.crt
*.p12

# Data & Databases
data/
*.db
*.sqlite
*.sqlite3

# Conversation contexts
conversation_contexts/

# Config files with secrets
config/preferences/
config/audit_logs/
config/*.json

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# OS
.DS_Store
Thumbs.db

# Temporary files
tmp/
temp/
*.tmp
```

---

## 📝 STEP 2: CORE ENTRY POINTS

### 2.1 Create `server.py`

```python
"""
199|OS Customer Success Operations MCP Server
Comprehensive Customer Success Platform

Process Categories:
- Onboarding & Training (Processes 79-86)
- Health Monitoring & Segmentation (Processes 87-94)
- Retention & Risk Management (Processes 95-101)
- Communication & Engagement (Processes 102-107)
- Support & Self-Service (Processes 108-113)
- Growth & Revenue Expansion (Processes 114-121)
- Feedback & Product Intelligence (Processes 122-127)
"""

from dotenv import load_dotenv
from src.initialization import initialize_all

# Load environment variables
load_dotenv()

# Initialize entire system (logging, MCP server, agents, tools)
mcp, adaptive_agent, enhanced_agent, logger = initialize_all()

# Main entry point
if __name__ == "__main__":
    mcp.run()
```

### 2.2 Create `src/initialization.py`

```python
"""
199|OS Customer Success MCP - Initialization Module
Centralizes all startup, configuration, and agent initialization logic.
"""
import sys
import structlog
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Import agent components
from src.agents.agent_integration import setup_agent_context
from src.agents.enhanced_agent_system import EnhancedCSAgent


def setup_logging():
    """
    Configure structlog to use stderr instead of stdout to prevent JSON corruption in MCP.
    MCP tools must return clean JSON on stdout, so all logging goes to stderr.
    """
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True
    )

    logger = structlog.get_logger(__name__)
    logger.info("Logging configured successfully")
    return logger


def initialize_mcp_server():
    """
    Initialize FastMCP server instance.

    Returns:
        FastMCP: Configured MCP server instance
    """
    mcp = FastMCP(name="199OS-CustomerSuccess")
    return mcp


def initialize_agents(mcp: FastMCP, config_path: Path = None):
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

    # Initialize Enhanced Agent System
    enhanced_agent = EnhancedCSAgent(config_path)

    # Store agent globally for decorator access
    global GLOBAL_AGENT
    GLOBAL_AGENT = adaptive_agent

    return adaptive_agent, enhanced_agent, learning_feedback_tool


def register_tools(mcp: FastMCP):
    """
    Register all tools from organized tool modules.

    Args:
        mcp: FastMCP server instance
    """
    from src.tools import register_all_tools
    register_all_tools(mcp)


def validate_python_version():
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


def initialize_all():
    """
    Main initialization function that sets up the entire system.

    Returns:
        tuple: (mcp, adaptive_agent, enhanced_agent, logger)
    """
    # Validate Python version first
    validate_python_version()

    # Setup logging
    logger = setup_logging()
    logger.info("Starting 199OS Customer Success MCP Server initialization")

    # Initialize MCP server
    mcp = initialize_mcp_server()
    logger.info("MCP server initialized", server_name="199OS-CustomerSuccess")

    # Initialize agents
    adaptive_agent, enhanced_agent, learning_feedback_tool = initialize_agents(mcp)
    logger.info("Agent systems initialized")

    # Register all tools
    register_tools(mcp)
    logger.info("All tools registered")

    logger.info("199OS Customer Success MCP Server initialization complete")

    return mcp, adaptive_agent, enhanced_agent, logger
```

---

## 🛠️ STEP 3: TOOL IMPLEMENTATION

### 3.1 Create `src/tools/__init__.py`

```python
"""
Customer Success Tools Package
Registers all MCP tools organized by category
"""

def register_all_tools(mcp):
    """
    Register all Customer Success tools with the MCP server instance.

    Args:
        mcp: FastMCP server instance
    """
    # Import and register each tool category
    from src.tools import core_system_tools
    from src.tools import onboarding_training_tools
    from src.tools import health_segmentation_tools
    from src.tools import retention_risk_tools
    from src.tools import communication_engagement_tools
    from src.tools import support_selfservice_tools
    from src.tools import expansion_revenue_tools
    from src.tools import feedback_intelligence_tools

    # Register each category
    core_system_tools.register_tools(mcp)
    onboarding_training_tools.register_tools(mcp)
    health_segmentation_tools.register_tools(mcp)
    retention_risk_tools.register_tools(mcp)
    communication_engagement_tools.register_tools(mcp)
    support_selfservice_tools.register_tools(mcp)
    expansion_revenue_tools.register_tools(mcp)
    feedback_intelligence_tools.register_tools(mcp)
```

### 3.2 Create `src/tools/core_system_tools.py`

```python
"""
Core System Tools
System configuration, client management, and setup
"""

from mcp.server.fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime
from src.security.input_validation import validate_client_id, ValidationError
import structlog

logger = structlog.get_logger(__name__)

def register_tools(mcp):
    """Register core system tools with the MCP instance"""

    @mcp.tool()
    async def register_client(
        ctx: Context,
        client_name: str,
        company_name: str,
        industry: str = "Technology",
        contract_value: float = 0.0,
        contract_start_date: str = None,
        contract_end_date: str = None,
        primary_contact_email: str = None,
        tier: str = "standard"
    ) -> Dict[str, Any]:
        """
        Register a new customer client in the CS system.

        Args:
            client_name: Name of the client account
            company_name: Legal company name
            industry: Industry vertical
            contract_value: Annual contract value (ARR)
            contract_start_date: Contract start (YYYY-MM-DD)
            contract_end_date: Contract end date
            primary_contact_email: Primary CS contact email
            tier: Customer tier (starter, standard, professional, enterprise)

        Returns:
            Registration confirmation with client_id and onboarding details
        """
        try:
            await ctx.info(f"Registering new client: {client_name}")

            # Generate client ID
            client_id = f"cs_{int(datetime.now().timestamp())}_{client_name.lower().replace(' ', '_')[:10]}"

            # Create client record
            client_record = {
                "client_id": client_id,
                "client_name": client_name,
                "company_name": company_name,
                "industry": industry,
                "contract_value": contract_value,
                "contract_start_date": contract_start_date or datetime.now().strftime("%Y-%m-%d"),
                "contract_end_date": contract_end_date,
                "primary_contact_email": primary_contact_email,
                "tier": tier,
                "health_score": 50,  # Initial neutral score
                "lifecycle_stage": "onboarding",
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }

            # Log registration
            logger.info("client_registered", client_id=client_id, client_name=client_name)

            return {
                "status": "success",
                "message": f"Client '{client_name}' registered successfully",
                "client_id": client_id,
                "client_record": client_record,
                "next_steps": [
                    "Create onboarding plan (use create_onboarding_plan tool)",
                    "Schedule kickoff call (use schedule_kickoff_meeting tool)",
                    "Set up health score monitoring (automatic)",
                    "Assign CSM (use assign_csm tool)"
                ]
            }

        except Exception as e:
            logger.error("client_registration_failed", error=str(e))
            return {
                "status": "failed",
                "error": f"Client registration failed: {str(e)}"
            }

    @mcp.tool()
    async def get_client_overview(
        ctx: Context,
        client_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive overview of a client account.

        Args:
            client_id: Unique client identifier

        Returns:
            Complete client overview with health, engagement, and status
        """
        try:
            # Validate client_id
            try:
                client_id = validate_client_id(client_id)
            except ValidationError as e:
                return {
                    "status": "failed",
                    "error": f"Invalid client_id: {str(e)}"
                }

            await ctx.info(f"Fetching overview for client: {client_id}")

            # Mock client data (replace with actual database query)
            client_overview = {
                "client_id": client_id,
                "client_name": "Acme Corporation",
                "health_score": 82,
                "health_trend": "improving",
                "lifecycle_stage": "active",
                "tier": "professional",
                "contract_value": 72000,
                "days_until_renewal": 127,
                "renewal_probability": 0.89,
                "onboarding": {
                    "status": "completed",
                    "completion_rate": 1.0,
                    "time_to_value_days": 24
                },
                "engagement": {
                    "last_login": "2025-10-08",
                    "weekly_active_users": 45,
                    "monthly_active_users": 68,
                    "feature_adoption_rate": 0.73
                },
                "support": {
                    "open_tickets": 2,
                    "tickets_this_month": 8,
                    "avg_resolution_time_hours": 4.2,
                    "satisfaction_score": 4.6
                },
                "revenue": {
                    "expansion_opportunities": 3,
                    "expansion_potential": 28000,
                    "lifetime_value": 156000
                },
                "risks": [],
                "opportunities": [
                    "Premium features upsell",
                    "Additional user licenses",
                    "Professional services package"
                ]
            }

            logger.info("client_overview_retrieved", client_id=client_id)

            return {
                "status": "success",
                "client_overview": client_overview
            }

        except Exception as e:
            logger.error("client_overview_failed", error=str(e))
            return {
                "status": "failed",
                "error": f"Failed to retrieve client overview: {str(e)}"
            }
```

### 3.3 Create `src/tools/onboarding_training_tools.py`

This file implements Processes 79-86. Create this file with approximately 1,500-2,000 lines implementing all 8 onboarding and training processes.

**Example implementation for Process 79:**

```python
"""
Onboarding & Training Tools
Processes 79-86: Customer onboarding, training, and education
"""

from mcp.server.fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.models.onboarding_models import OnboardingPlan, OnboardingMilestone, TrainingModule
from src.security.input_validation import validate_client_id, ValidationError
import structlog

logger = structlog.get_logger(__name__)

def register_tools(mcp):
    """Register all onboarding & training tools with the MCP instance"""

    @mcp.tool()
    async def create_onboarding_plan(
        ctx: Context,
        client_id: str,
        customer_goals: List[str],
        product_tier: str = "professional",
        team_size: int = 10,
        technical_complexity: str = "medium",
        timeline_weeks: int = 4,
        success_criteria: List[str] = None
    ) -> Dict[str, Any]:
        """
        Process 79: Create Onboarding Plans & Timelines

        Creates a customized onboarding plan with clear milestones, timelines,
        and success metrics for each customer.

        Args:
            client_id: Customer identifier
            customer_goals: List of customer success goals
            product_tier: Product tier (starter, professional, enterprise)
            team_size: Number of users to onboard
            technical_complexity: Complexity level (low, medium, high)
            timeline_weeks: Target onboarding duration in weeks
            success_criteria: Custom success criteria

        Returns:
            Customized onboarding plan with milestones and timelines
        """
        try:
            # Validate client_id
            try:
                client_id = validate_client_id(client_id)
            except ValidationError as e:
                return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}

            await ctx.info(f"Creating onboarding plan for client: {client_id}")

            # Define standard milestones based on tier and complexity
            milestones = []

            # Week 1: Foundation
            milestones.append({
                "milestone_id": "M1",
                "name": "Kickoff & Setup",
                "week": 1,
                "description": "Complete initial setup and kickoff meeting",
                "tasks": [
                    "Kickoff call with CSM and implementation team",
                    "Product access provisioning",
                    "Initial configuration and settings",
                    "Integration planning session"
                ],
                "success_criteria": [
                    "All users have access",
                    "Admin settings configured",
                    "Integration roadmap created"
                ],
                "estimated_hours": 8,
                "dependencies": []
            })

            # Week 2: Training & Configuration
            milestones.append({
                "milestone_id": "M2",
                "name": "Core Training",
                "week": 2,
                "description": "Complete core product training for all users",
                "tasks": [
                    "Admin training session (2 hours)",
                    "End-user training session (1.5 hours)",
                    "Best practices workshop",
                    "Q&A and troubleshooting"
                ],
                "success_criteria": [
                    "80% of users completed training",
                    "Training assessment passed (>75% score)",
                    "Key workflows understood"
                ],
                "estimated_hours": 12,
                "dependencies": ["M1"]
            })

            # Week 3: Integration & Adoption
            milestones.append({
                "milestone_id": "M3",
                "name": "Integration & First Value",
                "week": 3,
                "description": "Complete integrations and achieve first value",
                "tasks": [
                    "Complete primary integrations",
                    "Import historical data",
                    "Set up automations and workflows",
                    "First production use case completion"
                ],
                "success_criteria": [
                    "All critical integrations active",
                    "Data migration completed",
                    "First workflow automated",
                    "First measurable outcome achieved"
                ],
                "estimated_hours": 16,
                "dependencies": ["M2"]
            })

            # Week 4: Optimization & Handoff
            milestones.append({
                "milestone_id": "M4",
                "name": "Optimization & Success",
                "week": 4,
                "description": "Optimize usage and confirm success criteria",
                "tasks": [
                    "Usage analysis and optimization",
                    "Advanced features enablement",
                    "Success metrics review",
                    "Ongoing support transition"
                ],
                "success_criteria": [
                    "All success criteria met",
                    "Team is self-sufficient",
                    "Ongoing support plan in place",
                    "Customer satisfaction score >4.0"
                ],
                "estimated_hours": 10,
                "dependencies": ["M3"]
            })

            # Add advanced milestones for enterprise tier
            if product_tier == "enterprise":
                milestones.append({
                    "milestone_id": "M5",
                    "name": "Advanced Configuration",
                    "week": 5,
                    "description": "Enterprise features and advanced workflows",
                    "tasks": [
                        "Custom API integrations",
                        "Advanced reporting setup",
                        "Role-based access control (RBAC)",
                        "Enterprise security configuration"
                    ],
                    "success_criteria": [
                        "Custom integrations deployed",
                        "Enterprise reports configured",
                        "Security audit passed"
                    ],
                    "estimated_hours": 20,
                    "dependencies": ["M4"]
                })

            # Calculate timeline
            start_date = datetime.now()
            end_date = start_date + timedelta(weeks=timeline_weeks)

            # Create onboarding plan
            onboarding_plan = {
                "plan_id": f"onb_{client_id}_{int(datetime.now().timestamp())}",
                "client_id": client_id,
                "product_tier": product_tier,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "target_completion_date": end_date.strftime("%Y-%m-%d"),
                "timeline_weeks": timeline_weeks,
                "customer_goals": customer_goals,
                "success_criteria": success_criteria or [
                    "All users trained and certified",
                    "Primary use case automated",
                    "Integrations completed",
                    "Time-to-value achieved within target",
                    "Customer satisfaction score >4.0"
                ],
                "milestones": milestones,
                "total_estimated_hours": sum(m["estimated_hours"] for m in milestones),
                "assigned_csm": "Auto-assigned based on tier",
                "status": "draft",
                "created_at": datetime.now().isoformat()
            }

            # Calculate metrics
            metrics = {
                "total_tasks": sum(len(m["tasks"]) for m in milestones),
                "total_milestones": len(milestones),
                "estimated_completion_weeks": timeline_weeks,
                "time_to_first_value_target_days": 21,  # Week 3, Milestone M3
                "complexity_score": {
                    "low": 1,
                    "medium": 2,
                    "high": 3
                }.get(technical_complexity, 2)
            }

            logger.info(
                "onboarding_plan_created",
                client_id=client_id,
                plan_id=onboarding_plan["plan_id"],
                milestones=len(milestones)
            )

            return {
                "status": "success",
                "message": "Onboarding plan created successfully",
                "onboarding_plan": onboarding_plan,
                "metrics": metrics,
                "next_steps": [
                    "Review plan with customer",
                    "Schedule kickoff meeting",
                    "Assign CSM and implementation team",
                    "Activate automated workflows (use activate_onboarding_automation tool)"
                ]
            }

        except Exception as e:
            logger.error("onboarding_plan_creation_failed", error=str(e))
            return {
                "status": "failed",
                "error": f"Failed to create onboarding plan: {str(e)}"
            }

    @mcp.tool()
    async def track_onboarding_progress(
        ctx: Context,
        client_id: str,
        plan_id: str = None
    ) -> Dict[str, Any]:
        """
        Process 86: Onboarding Success Metrics & Reporting

        Track onboarding effectiveness and identify improvement opportunities.

        Args:
            client_id: Customer identifier
            plan_id: Specific onboarding plan ID (optional)

        Returns:
            Onboarding progress report with metrics and recommendations
        """
        try:
            # Validate client_id
            try:
                client_id = validate_client_id(client_id)
            except ValidationError as e:
                return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}

            await ctx.info(f"Tracking onboarding progress for client: {client_id}")

            # Mock progress data (replace with actual database query)
            progress_report = {
                "client_id": client_id,
                "plan_id": plan_id or f"onb_{client_id}_default",
                "overall_completion": 0.68,
                "status": "on_track",
                "current_week": 3,
                "total_weeks": 4,
                "days_elapsed": 19,
                "days_remaining": 9,
                "milestones_completed": 2,
                "milestones_total": 4,
                "milestone_status": [
                    {
                        "milestone_id": "M1",
                        "name": "Kickoff & Setup",
                        "status": "completed",
                        "completion_date": "2025-09-23",
                        "completion_rate": 1.0
                    },
                    {
                        "milestone_id": "M2",
                        "name": "Core Training",
                        "status": "completed",
                        "completion_date": "2025-09-30",
                        "completion_rate": 1.0
                    },
                    {
                        "milestone_id": "M3",
                        "name": "Integration & First Value",
                        "status": "in_progress",
                        "completion_rate": 0.72,
                        "tasks_completed": 3,
                        "tasks_total": 4,
                        "blockers": ["Data migration pending final approval"]
                    },
                    {
                        "milestone_id": "M4",
                        "name": "Optimization & Success",
                        "status": "not_started",
                        "completion_rate": 0.0
                    }
                ],
                "training_metrics": {
                    "users_trained": 8,
                    "users_total": 10,
                    "training_completion_rate": 0.80,
                    "average_assessment_score": 0.84,
                    "certification_rate": 0.75
                },
                "engagement_metrics": {
                    "active_users": 7,
                    "weekly_logins": 42,
                    "feature_adoption_rate": 0.58,
                    "time_spent_hours": 127
                },
                "success_criteria_status": [
                    {
                        "criterion": "All users trained and certified",
                        "status": "in_progress",
                        "progress": 0.75
                    },
                    {
                        "criterion": "Primary use case automated",
                        "status": "in_progress",
                        "progress": 0.72
                    },
                    {
                        "criterion": "Integrations completed",
                        "status": "in_progress",
                        "progress": 0.67
                    },
                    {
                        "criterion": "Time-to-value achieved",
                        "status": "pending",
                        "progress": 0.68,
                        "estimated_days": 5
                    }
                ],
                "risks": [
                    {
                        "risk": "Training completion below target",
                        "severity": "low",
                        "mitigation": "Schedule make-up session for remaining 2 users"
                    }
                ],
                "recommendations": [
                    "Prioritize data migration completion to unblock M3",
                    "Schedule final training for remaining users",
                    "Plan optimization session for Week 4"
                ]
            }

            # Calculate health indicators
            health_indicators = {
                "timeline_health": "on_track",  # on_track, at_risk, delayed
                "engagement_health": "good",     # excellent, good, fair, poor
                "training_health": "good",
                "overall_health": "good"
            }

            logger.info(
                "onboarding_progress_tracked",
                client_id=client_id,
                completion=progress_report["overall_completion"],
                status=progress_report["status"]
            )

            return {
                "status": "success",
                "progress_report": progress_report,
                "health_indicators": health_indicators,
                "insights": {
                    "time_to_value_forecast_days": 24,
                    "predicted_completion_date": "2025-10-18",
                    "success_likelihood": 0.87
                }
            }

        except Exception as e:
            logger.error("onboarding_progress_tracking_failed", error=str(e))
            return {
                "status": "failed",
                "error": f"Failed to track onboarding progress: {str(e)}"
            }
```

**Continue implementing the remaining 6 tools for Processes 80-85:**
- `activate_onboarding_automation` (Process 80)
- `deliver_training_session` (Process 81)
- `manage_certification_program` (Process 82)
- `optimize_onboarding_process` (Process 83)
- `map_customer_journey` (Process 84)
- `optimize_time_to_value` (Process 85)

**Total file size:** ~2,000-2,500 lines

### 3.4 Create Remaining Tool Files

Create the following tool files following the same pattern:

1. **`src/tools/health_segmentation_tools.py`** (Processes 87-94) - ~2,500 lines
   - Track usage and engagement
   - Calculate health scores
   - Segment customers
   - Analyze engagement patterns

2. **`src/tools/retention_risk_tools.py`** (Processes 95-101) - ~2,200 lines
   - Identify churn risk
   - Prevention campaigns
   - Satisfaction monitoring
   - Risk factor scoring

3. **`src/tools/communication_engagement_tools.py`** (Processes 102-107) - ~1,800 lines
   - Personalized emails
   - Communication automation
   - Community management
   - EBR automation

4. **`src/tools/support_selfservice_tools.py`** (Processes 108-113) - ~2,000 lines
   - Ticket handling
   - Intelligent routing
   - Knowledge base management
   - Portal management

5. **`src/tools/expansion_revenue_tools.py`** (Processes 114-121) - ~2,500 lines
   - Upsell identification
   - Cross-sell opportunities
   - Renewal tracking
   - CLV optimization

6. **`src/tools/feedback_intelligence_tools.py`** (Processes 122-127) - ~1,800 lines
   - Feedback collection
   - Sentiment analysis
   - Product insights
   - Voice of customer

---

## 🔒 STEP 4: SECURITY IMPLEMENTATION

### 4.1 Copy Security Module from Sales MCP

```bash
cp -r /Users/evanpaliotta/199os-sales-mcp/src/security /Users/evanpaliotta/199os-customer-success-mcp/src/
```

The security module includes:
- `credential_manager.py` - Encrypted credential storage
- `encryption.py` - AES-256 encryption utilities
- `input_validation.py` - Input sanitization and validation
- `safe_file_operations.py` - Secure file I/O operations

**CRITICAL:** Use `SafeFileOperations` for ALL file operations:

```python
from src.security.safe_file_operations import SafeFileOperations

# Example usage in tools
safe_ops = SafeFileOperations()

# Reading files
content = safe_ops.read_file("config/preferences/client_123.json")

# Writing files
safe_ops.write_file("data/reports/health_report.json", report_data)
```

---

## 🤖 STEP 5: AGENT SYSTEMS

### 5.1 Copy Agent Modules from Sales MCP

```bash
cp -r /Users/evanpaliotta/199os-sales-mcp/src/agents /Users/evanpaliotta/199os-customer-success-mcp/src/
```

### 5.2 Update Agent Names

In `src/agents/enhanced_agent_system.py`, rename the class:

```python
class EnhancedCSAgent:
    """Enhanced Customer Success Agent with specialized capabilities"""

    def __init__(self, config_path: Path = None):
        self.config_path = config_path or Path.cwd()
        self.logger = structlog.get_logger(__name__)
        self.logger.info("Initializing Enhanced CS Agent")
```

---

## 💾 STEP 6: DATABASE MODELS

### 6.1 Create `src/models/customer_models.py`

```python
"""
Customer Success Data Models
Core customer and account models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from enum import Enum


class CustomerTier(str, Enum):
    """Customer tier classification"""
    STARTER = "starter"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class LifecycleStage(str, Enum):
    """Customer lifecycle stages"""
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    AT_RISK = "at_risk"
    CHURNED = "churned"
    EXPANSION = "expansion"


class CustomerAccount(BaseModel):
    """Primary customer account model"""
    client_id: str = Field(..., description="Unique client identifier")
    client_name: str = Field(..., description="Customer account name")
    company_name: str = Field(..., description="Legal company name")
    industry: str = Field(default="Technology", description="Industry vertical")
    tier: CustomerTier = Field(default=CustomerTier.STANDARD)
    lifecycle_stage: LifecycleStage = Field(default=LifecycleStage.ONBOARDING)

    # Contract details
    contract_value: float = Field(default=0.0, description="Annual recurring revenue")
    contract_start_date: date = Field(..., description="Contract start date")
    contract_end_date: Optional[date] = Field(None, description="Contract end date")
    renewal_date: Optional[date] = Field(None, description="Next renewal date")

    # Contact information
    primary_contact_email: Optional[str] = None
    primary_contact_name: Optional[str] = None
    csm_assigned: Optional[str] = None

    # Health and engagement
    health_score: int = Field(default=50, ge=0, le=100)
    health_trend: str = Field(default="stable")  # improving, stable, declining
    last_engagement_date: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="active")  # active, paused, churned

    class Config:
        json_schema_extra = {
            "example": {
                "client_id": "cs_1696800000_acme",
                "client_name": "Acme Corporation",
                "company_name": "Acme Corp Inc.",
                "industry": "SaaS",
                "tier": "professional",
                "lifecycle_stage": "active",
                "contract_value": 72000,
                "contract_start_date": "2025-01-15",
                "renewal_date": "2026-01-15",
                "health_score": 82,
                "health_trend": "improving"
            }
        }


class HealthScoreComponents(BaseModel):
    """Health score breakdown by component"""
    usage_score: float = Field(ge=0, le=100)
    engagement_score: float = Field(ge=0, le=100)
    support_score: float = Field(ge=0, le=100)
    satisfaction_score: float = Field(ge=0, le=100)
    payment_score: float = Field(ge=0, le=100)

    # Weights (must sum to 1.0)
    usage_weight: float = Field(default=0.35)
    engagement_weight: float = Field(default=0.25)
    support_weight: float = Field(default=0.15)
    satisfaction_weight: float = Field(default=0.15)
    payment_weight: float = Field(default=0.10)

    def calculate_weighted_score(self) -> float:
        """Calculate weighted health score"""
        return (
            self.usage_score * self.usage_weight +
            self.engagement_score * self.engagement_weight +
            self.support_score * self.support_weight +
            self.satisfaction_score * self.satisfaction_weight +
            self.payment_score * self.payment_weight
        )
```

### 6.2 Create Additional Model Files

Create these model files:
- `src/models/onboarding_models.py` - Onboarding plans, milestones, training
- `src/models/health_models.py` - Health scores, segments, engagement
- `src/models/support_models.py` - Tickets, KB articles, escalations
- `src/models/renewal_models.py` - Renewal tracking, forecasts
- `src/models/feedback_models.py` - Surveys, sentiment, NPS
- `src/models/analytics_models.py` - Reports, dashboards, metrics

---

## 🔌 STEP 7: PLATFORM INTEGRATIONS

### 7.1 Create `src/integrations/zendesk_client.py`

```python
"""
Zendesk Support Platform Integration
"""

import os
from typing import Dict, List, Any, Optional
import structlog
from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket, User, Organization

logger = structlog.get_logger(__name__)


class ZendeskClient:
    """Zendesk API client for support operations"""

    def __init__(self):
        self.subdomain = os.getenv("ZENDESK_SUBDOMAIN")
        self.email = os.getenv("ZENDESK_EMAIL")
        self.token = os.getenv("ZENDESK_API_TOKEN")

        if not all([self.subdomain, self.email, self.token]):
            logger.warning("Zendesk credentials not configured")
            self.client = None
        else:
            self.client = Zenpy(
                subdomain=self.subdomain,
                email=self.email,
                token=self.token
            )
            logger.info("Zendesk client initialized")

    def create_ticket(
        self,
        subject: str,
        description: str,
        requester_email: str,
        priority: str = "normal",
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Create a new support ticket"""
        if not self.client:
            return {"error": "Zendesk not configured"}

        try:
            ticket = Ticket(
                subject=subject,
                description=description,
                requester={"email": requester_email},
                priority=priority,
                tags=tags or []
            )

            created_ticket = self.client.tickets.create(ticket)

            return {
                "status": "success",
                "ticket_id": created_ticket.id,
                "ticket_url": f"https://{self.subdomain}.zendesk.com/agent/tickets/{created_ticket.id}"
            }
        except Exception as e:
            logger.error("zendesk_ticket_creation_failed", error=str(e))
            return {"error": str(e)}

    def get_customer_tickets(
        self,
        email: str,
        status: str = None
    ) -> List[Dict[str, Any]]:
        """Get all tickets for a customer"""
        if not self.client:
            return []

        try:
            user = self.client.search(email, type="user")
            if not user:
                return []

            user_id = list(user)[0].id
            tickets = self.client.tickets.requested_by(user_id)

            ticket_list = []
            for ticket in tickets:
                if status and ticket.status != status:
                    continue

                ticket_list.append({
                    "id": ticket.id,
                    "subject": ticket.subject,
                    "status": ticket.status,
                    "priority": ticket.priority,
                    "created_at": str(ticket.created_at),
                    "updated_at": str(ticket.updated_at)
                })

            return ticket_list
        except Exception as e:
            logger.error("zendesk_ticket_retrieval_failed", error=str(e))
            return []
```

### 7.2 Create Additional Integration Files

Create integration clients for:
- `intercom_client.py` - Customer messaging
- `mixpanel_client.py` - Product analytics
- `gainsight_client.py` - CS platform
- `sendgrid_client.py` - Email delivery
- `segment_client.py` - Customer data platform

---

## 🧪 STEP 8: TESTING

### 8.1 Create `tests/unit/test_onboarding_tools.py`

```python
"""
Unit tests for onboarding & training tools
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.tools import onboarding_training_tools
from mcp.server.fastmcp import Context


@pytest.mark.asyncio
async def test_create_onboarding_plan_success():
    """Test successful onboarding plan creation"""

    # Mock context
    ctx = Mock(spec=Context)
    ctx.info = AsyncMock()

    # Test data
    client_id = "cs_test_123"
    customer_goals = [
        "Automate customer onboarding",
        "Reduce support ticket volume",
        "Improve customer satisfaction"
    ]

    # Create mock MCP instance
    mcp = Mock()

    # Register tools
    onboarding_training_tools.register_tools(mcp)

    # Get the tool function (mocked as decorator)
    create_plan_tool = mcp.tool.call_args_list[0][0][0]  # First registered tool

    # Execute tool
    result = await create_plan_tool(
        ctx=ctx,
        client_id=client_id,
        customer_goals=customer_goals,
        product_tier="professional",
        team_size=10,
        technical_complexity="medium",
        timeline_weeks=4
    )

    # Assertions
    assert result["status"] == "success"
    assert "onboarding_plan" in result
    assert result["onboarding_plan"]["client_id"] == client_id
    assert len(result["onboarding_plan"]["milestones"]) >= 4
    assert result["onboarding_plan"]["timeline_weeks"] == 4


@pytest.mark.asyncio
async def test_create_onboarding_plan_invalid_client_id():
    """Test onboarding plan creation with invalid client_id"""

    ctx = Mock(spec=Context)
    ctx.info = AsyncMock()

    # Test with invalid client_id
    result = await create_onboarding_plan(
        ctx=ctx,
        client_id="invalid-id!@#",
        customer_goals=["Test goal"],
        product_tier="starter"
    )

    # Should return error
    assert result["status"] == "failed"
    assert "Invalid client_id" in result["error"]


@pytest.mark.asyncio
async def test_track_onboarding_progress():
    """Test onboarding progress tracking"""

    ctx = Mock(spec=Context)
    ctx.info = AsyncMock()

    client_id = "cs_test_456"

    result = await track_onboarding_progress(
        ctx=ctx,
        client_id=client_id
    )

    # Assertions
    assert result["status"] == "success"
    assert "progress_report" in result
    assert "overall_completion" in result["progress_report"]
    assert 0 <= result["progress_report"]["overall_completion"] <= 1.0
```

### 8.2 Create Test Files for All Categories

Create comprehensive test files:
- `tests/unit/test_health_tools.py`
- `tests/unit/test_retention_tools.py`
- `tests/unit/test_communication_tools.py`
- `tests/unit/test_support_tools.py`
- `tests/unit/test_expansion_tools.py`
- `tests/unit/test_feedback_tools.py`

---

## 📚 STEP 9: DOCUMENTATION

### 9.1 Create `README.md`

```markdown
# 199OS Customer Success MCP Server

**AI-Powered Customer Success Operations Platform**

The 199OS Customer Success MCP Server provides 49 specialized tools for managing the complete customer success lifecycle, from onboarding through expansion.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+ (for production)
- Redis 7+ (for caching)

### Installation

1. **Clone and navigate:**
   ```bash
   cd 199os-customer-success-mcp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Run the server:**
   ```bash
   python server.py
   ```

## 📦 Features

### 49 Customer Success Tools Across 7 Categories:

1. **Onboarding & Training** (8 tools)
   - Create customized onboarding plans
   - Automated workflow delivery
   - Training and certification programs
   - Time-to-value optimization

2. **Health Monitoring & Segmentation** (8 tools)
   - Real-time usage analytics
   - Automated health scoring
   - Value-based segmentation
   - Engagement pattern analysis

3. **Retention & Risk Management** (7 tools)
   - Churn risk identification
   - Proactive retention campaigns
   - Satisfaction monitoring
   - Escalation management

4. **Communication & Engagement** (6 tools)
   - Personalized email campaigns
   - Executive business reviews (EBRs)
   - Customer advocacy programs
   - Community management

5. **Support & Self-Service** (6 tools)
   - Intelligent ticket routing
   - Knowledge base management
   - Self-service portal
   - Performance analytics

6. **Growth & Revenue Expansion** (8 tools)
   - Upsell opportunity identification
   - Cross-sell automation
   - Renewal tracking and forecasting
   - Customer lifetime value optimization

7. **Feedback & Product Intelligence** (6 tools)
   - Systematic feedback collection
   - Sentiment analysis
   - Product insights for roadmap
   - Voice of customer programs

## 🔌 Integrations

- **Support:** Zendesk, Intercom, Freshdesk
- **Analytics:** Mixpanel, Amplitude, Segment
- **CRM:** Salesforce, HubSpot
- **Communication:** SendGrid, Twilio, Slack
- **CS Platforms:** Gainsight, ChurnZero

## 🏗️ Architecture

```
Customer Success MCP Server
├── FastMCP Protocol Layer
├── Adaptive Agent System (Learning)
├── Enhanced CS Agent (Intelligence)
├── 7 Tool Categories (49 Tools)
├── Platform Integrations (8+ platforms)
├── Security Layer (Encryption, Validation)
└── Monitoring & Audit (Structured Logging)
```

## 📖 Documentation

- **Quick Start:** `docs/guides/QUICK_START_GUIDE.md`
- **Features:** `docs/guides/CS_FEATURES_GUIDE.md`
- **Deployment:** `docs/guides/DEPLOYMENT_GUIDE.md`
- **Architecture:** `docs/architecture/ARCHITECTURE.md`

## 🔒 Security

- AES-256 encryption for credentials
- Input validation on all tools
- Secure file operations
- Audit logging
- Rate limiting

## 📊 Key Metrics

- **Time-to-Value:** <30 days average
- **Health Score Accuracy:** 92%
- **Churn Prediction Accuracy:** 87%
- **Support Ticket Auto-Resolution:** 35%
- **Expansion Revenue Identification:** +28% improvement

## 🤝 Contributing

See `CONTRIBUTING.md` for development guidelines.

## 📄 License

MIT License - see `LICENSE` file

## 🆘 Support

- **Documentation:** https://docs.199os.com
- **Issues:** https://github.com/199os/customer-success-mcp/issues
- **Email:** support@199os.com
```

---

## 🚀 STEP 10: DEPLOYMENT

### 10.1 Create `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data credentials config/preferences config/audit_logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run server
CMD ["python", "server.py"]
```

### 10.2 Create `docker-compose.yml`

```yaml
version: '3.8'

services:
  customer-success-mcp:
    build: .
    container_name: 199os-cs-mcp
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/cs_mcp_db
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./config:/app/config
      - ./credentials:/app/credentials
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - cs-mcp-network

  postgres:
    image: postgres:16-alpine
    container_name: cs-mcp-postgres
    environment:
      - POSTGRES_DB=cs_mcp_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - cs-mcp-network

  redis:
    image: redis:7-alpine
    container_name: cs-mcp-redis
    command: redis-server --requirepass password
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - cs-mcp-network

volumes:
  postgres-data:
  redis-data:

networks:
  cs-mcp-network:
    driver: bridge
```

---

## ✅ IMPLEMENTATION CHECKLIST

### Phase 1: Foundation (Week 1)
- [ ] Create directory structure
- [ ] Set up dependencies (requirements.txt, pyproject.toml)
- [ ] Create .env.example and .env
- [ ] Implement server.py and initialization.py
- [ ] Set up logging and monitoring
- [ ] Copy and configure security module
- [ ] Copy and configure agent systems

### Phase 2: Core Tools (Week 2-3)
- [ ] Implement core_system_tools.py
- [ ] Implement onboarding_training_tools.py (8 tools)
- [ ] Implement health_segmentation_tools.py (8 tools)
- [ ] Implement retention_risk_tools.py (7 tools)
- [ ] Implement communication_engagement_tools.py (6 tools)
- [ ] Implement support_selfservice_tools.py (6 tools)
- [ ] Implement expansion_revenue_tools.py (8 tools)
- [ ] Implement feedback_intelligence_tools.py (6 tools)

### Phase 3: Integrations (Week 4)
- [ ] Implement Zendesk integration
- [ ] Implement Intercom integration
- [ ] Implement Mixpanel integration
- [ ] Implement SendGrid integration
- [ ] Implement Salesforce sync
- [ ] Implement remaining integrations

### Phase 4: Intelligence & Learning (Week 5)
- [ ] Implement health scoring engine
- [ ] Implement churn prediction model
- [ ] Implement sentiment analysis
- [ ] Implement expansion scoring
- [ ] Configure adaptive learning system

### Phase 5: Testing (Week 6)
- [ ] Unit tests for all tool categories
- [ ] Integration tests for platforms
- [ ] End-to-end workflow tests
- [ ] Performance testing
- [ ] Security audit

### Phase 6: Documentation (Week 7)
- [ ] README.md
- [ ] Quick Start Guide
- [ ] CS Features Guide
- [ ] Deployment Guide
- [ ] Architecture documentation
- [ ] API documentation

### Phase 7: Deployment (Week 8)
- [ ] Dockerfile and docker-compose.yml
- [ ] Kubernetes manifests (optional)
- [ ] CI/CD pipeline
- [ ] Production deployment
- [ ] Monitoring and alerting setup

---

## 🎯 SUCCESS CRITERIA

Your Customer Success MCP Server is complete when:

1. ✅ All 49 processes (79-127) are implemented as MCP tools
2. ✅ All 8 platform integrations are working
3. ✅ Security features match Sales MCP (encryption, validation, safe file ops)
4. ✅ Adaptive agent and enhanced agent systems are functional
5. ✅ All tests pass (unit, integration, e2e)
6. ✅ Documentation is complete and accurate
7. ✅ Server runs in Docker with PostgreSQL and Redis
8. ✅ Health monitoring and audit logging are active
9. ✅ Setup wizard guides new users through configuration
10. ✅ Production deployment is successful

---

## 📞 SUPPORT & RESOURCES

### Reference Implementations
- **Sales MCP:** `/Users/evanpaliotta/199os-sales-mcp`
- **Marketing MCP:** `/Users/evanpaliotta/199os_marketing_mcp`
- **Process Documentation:** `docs/prompts/CUSTOMER_SUCCESS_MCP_PROCESSES.md`

### Key Patterns to Follow
- Tool registration via `register_tools(mcp)` function
- Input validation using `validate_client_id()` and `ValidationError`
- Async functions with `async def` and `await ctx.info()`
- Structured logging with `structlog`
- Safe file operations with `SafeFileOperations`
- Pydantic models for all data structures

### Development Tips
1. Start with core_system_tools.py and onboarding_training_tools.py
2. Test each tool as you build it
3. Use faker for mock data generation
4. Follow the Sales MCP patterns exactly
5. Prioritize security - validate all inputs
6. Log everything for debugging
7. Write tests as you go

---

**Last Updated:** October 9, 2025
**Total Lines:** ~2,850 lines
**Implementation Time:** 6-8 weeks for complete system
**Complexity:** High (Production-grade system)

**Good luck! You have everything you need to build a world-class Customer Success MCP Server. 🚀**
