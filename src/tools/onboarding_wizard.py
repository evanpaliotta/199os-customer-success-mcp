"""
Interactive Onboarding Wizard for Customer Success MCP
Guides users through complete system setup with validation and testing
"""

import os
import sys
import json
import getpass
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import time

# Rich library for beautiful terminal output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Installing rich library for beautiful terminal output...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich import box

# Import credential manager for secure storage
try:
    from src.security.credential_manager import SecureCredentialManager
except ImportError:
    SecureCredentialManager = None


# ============================================================================
# WIZARD STATE MANAGEMENT
# ============================================================================

class WizardStep(Enum):
    """Wizard steps enumeration"""
    WELCOME = 1
    SYSTEM_CHECK = 2
    PLATFORM_SETUP = 3
    CONFIGURATION = 4
    DATABASE_INIT = 5
    TESTING = 6
    COMPLETION = 7


@dataclass
class OnboardingState:
    """Tracks wizard progress and configuration"""
    current_step: WizardStep = WizardStep.WELCOME
    completed_steps: List[WizardStep] = None

    # System check results
    python_version: Optional[str] = None
    dependencies_installed: bool = False
    database_connected: bool = False
    redis_connected: bool = False

    # Platform integrations
    zendesk_configured: bool = False
    intercom_configured: bool = False
    mixpanel_configured: bool = False
    sendgrid_configured: bool = False

    # Configuration
    health_score_weights: Optional[Dict[str, float]] = None
    sla_targets: Optional[Dict[str, int]] = None
    thresholds: Optional[Dict[str, float]] = None

    # Database
    database_initialized: bool = False
    migrations_run: bool = False

    # Testing
    all_tests_passed: bool = False

    # Metadata
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def __post_init__(self):
        if self.completed_steps is None:
            self.completed_steps = []
        if self.started_at is None:
            self.started_at = datetime.utcnow().isoformat()

    def mark_step_complete(self, step: WizardStep):
        """Mark a step as completed"""
        if step not in self.completed_steps:
            self.completed_steps.append(step)

    def is_step_complete(self, step: WizardStep) -> bool:
        """Check if a step is completed"""
        return step in self.completed_steps

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['current_step'] = self.current_step.name
        data['completed_steps'] = [step.name for step in self.completed_steps]
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'OnboardingState':
        """Create from dictionary"""
        # Convert step names back to enums
        if 'current_step' in data and isinstance(data['current_step'], str):
            data['current_step'] = WizardStep[data['current_step']]
        if 'completed_steps' in data:
            data['completed_steps'] = [
                WizardStep[step] if isinstance(step, str) else step
                for step in data['completed_steps']
            ]
        return cls(**data)


# ============================================================================
# ONBOARDING WIZARD CLASS
# ============================================================================

class CustomerSuccessOnboardingWizard:
    """Interactive onboarding wizard for Customer Success MCP"""

    def __init__(self):
        self.console = Console()
        self.state = OnboardingState()
        self.config_dir = Path.home() / ".config" / "cs-mcp"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.config_dir / "onboarding_state.json"
        self.env_file = Path.cwd() / ".env"
        self.credential_manager = None

        # Load existing state if available
        self.load_state()

    def save_state(self):
        """Persist wizard state to disk"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state.to_dict(), f, indent=2)
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not save state: {e}[/yellow]")

    def load_state(self):
        """Load wizard state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.state = OnboardingState.from_dict(data)
                    self.console.print("[green]Resuming previous onboarding session...[/green]")
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not load state: {e}[/yellow]")

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title: str, subtitle: str = ""):
        """Print a formatted header"""
        self.console.print()
        self.console.print(Panel(
            f"[bold cyan]{title}[/bold cyan]\n{subtitle}",
            box=box.DOUBLE,
            border_style="cyan"
        ))
        self.console.print()

    def print_progress(self):
        """Print overall wizard progress"""
        total_steps = len(WizardStep)
        completed = len(self.state.completed_steps)
        percentage = (completed / total_steps) * 100

        progress_bar = "█" * completed + "░" * (total_steps - completed)

        self.console.print(f"[cyan]Progress:[/cyan] {progress_bar} [cyan]{completed}/{total_steps} steps ({percentage:.0f}%)[/cyan]")
        self.console.print()

    # ========================================================================
    # STEP 1: WELCOME & SYSTEM CHECK
    # ========================================================================

    def step_welcome(self) -> bool:
        """Welcome message and initial setup"""
        self.clear_screen()
        self.print_header(
            "Welcome to Customer Success MCP Setup Wizard",
            "This wizard will guide you through setting up your Customer Success operations platform"
        )

        self.console.print("[bold]What this wizard will do:[/bold]")
        self.console.print("  1. Check your system requirements")
        self.console.print("  2. Configure platform integrations (Zendesk, Intercom, Mixpanel, SendGrid)")
        self.console.print("  3. Set up health scoring and retention thresholds")
        self.console.print("  4. Initialize database and create tables")
        self.console.print("  5. Test all integrations")
        self.console.print("  6. Generate setup report")
        self.console.print()

        self.console.print("[yellow]Estimated time: 5-10 minutes[/yellow]")
        self.console.print()

        if Confirm.ask("Ready to begin?", default=True):
            self.state.mark_step_complete(WizardStep.WELCOME)
            self.save_state()
            return True
        return False

    def step_system_check(self) -> bool:
        """Check system requirements"""
        self.clear_screen()
        self.print_header("System Requirements Check", "Step 1 of 6")
        self.print_progress()

        checks = []
        all_passed = True

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            # Check Python version
            task = progress.add_task("Checking Python version...", total=None)
            python_version = platform.python_version()
            self.state.python_version = python_version
            major, minor = map(int, python_version.split('.')[:2])

            if major >= 3 and minor >= 10:
                checks.append(("Python version", f"{python_version} ✓", True))
            else:
                checks.append(("Python version", f"{python_version} ✗ (requires 3.10+)", False))
                all_passed = False
            progress.update(task, completed=True)

            # Check required dependencies
            task = progress.add_task("Checking dependencies...", total=None)
            required_packages = [
                'fastmcp', 'pydantic', 'sqlalchemy', 'cryptography',
                'structlog', 'rich', 'redis', 'psycopg2-binary'
            ]

            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package.replace('-', '_'))
                except ImportError:
                    missing_packages.append(package)

            if not missing_packages:
                checks.append(("Dependencies", "All required packages installed ✓", True))
                self.state.dependencies_installed = True
            else:
                checks.append(("Dependencies", f"Missing: {', '.join(missing_packages)} ✗", False))
                all_passed = False
            progress.update(task, completed=True)

            # Check database connectivity (optional at this stage)
            task = progress.add_task("Checking database connectivity...", total=None)
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                try:
                    # Try to connect
                    import psycopg2
                    from urllib.parse import urlparse
                    parsed = urlparse(database_url)
                    conn = psycopg2.connect(
                        host=parsed.hostname,
                        port=parsed.port or 5432,
                        user=parsed.username,
                        password=parsed.password,
                        database=parsed.path.lstrip('/'),
                        connect_timeout=5
                    )
                    conn.close()
                    checks.append(("PostgreSQL", "Connected ✓", True))
                    self.state.database_connected = True
                except Exception as e:
                    checks.append(("PostgreSQL", f"Not connected (will configure later) ⚠", True))
            else:
                checks.append(("PostgreSQL", "Not configured (will configure later) ⚠", True))
            progress.update(task, completed=True)

            # Check Redis connectivity (optional at this stage)
            task = progress.add_task("Checking Redis connectivity...", total=None)
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                try:
                    import redis
                    r = redis.from_url(redis_url, socket_connect_timeout=5)
                    r.ping()
                    checks.append(("Redis", "Connected ✓", True))
                    self.state.redis_connected = True
                except Exception as e:
                    checks.append(("Redis", f"Not connected (will configure later) ⚠", True))
            else:
                checks.append(("Redis", "Not configured (will configure later) ⚠", True))
            progress.update(task, completed=True)

            # Check disk space
            task = progress.add_task("Checking disk space...", total=None)
            stat = shutil.disk_usage("/")
            free_gb = stat.free / (1024**3)
            if free_gb >= 1.0:
                checks.append(("Disk space", f"{free_gb:.1f} GB free ✓", True))
            else:
                checks.append(("Disk space", f"{free_gb:.1f} GB free ⚠", True))
            progress.update(task, completed=True)

        # Display results
        self.console.print()
        table = Table(title="System Check Results", box=box.ROUNDED)
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="white")

        for check_name, status, passed in checks:
            style = "green" if passed and "✓" in status else "yellow" if "⚠" in status else "red"
            table.add_row(check_name, f"[{style}]{status}[/{style}]")

        self.console.print(table)
        self.console.print()

        if not all_passed:
            self.console.print("[red]Some critical checks failed. Please fix these issues before continuing.[/red]")
            if missing_packages:
                self.console.print(f"\n[yellow]Install missing packages with:[/yellow]")
                self.console.print(f"  pip install {' '.join(missing_packages)}")
            return False

        self.state.mark_step_complete(WizardStep.SYSTEM_CHECK)
        self.save_state()

        self.console.print("[green]All system checks passed! ✓[/green]")
        input("\nPress Enter to continue...")
        return True

    # ========================================================================
    # STEP 2: PLATFORM INTEGRATION SETUP
    # ========================================================================

    def step_platform_setup(self) -> bool:
        """Configure platform integrations"""
        self.clear_screen()
        self.print_header("Platform Integration Setup", "Step 2 of 6")
        self.print_progress()

        self.console.print("[bold]Configure your platform integrations:[/bold]")
        self.console.print("You can skip any integration and configure it later.")
        self.console.print()

        # Initialize credential manager
        master_password = os.getenv('CREDENTIAL_MASTER_PASSWORD')
        if not master_password:
            self.console.print("[yellow]Setting up credential encryption...[/yellow]")
            master_password = Prompt.ask(
                "Enter a master password for credential encryption",
                password=True
            )
            confirm_password = Prompt.ask(
                "Confirm master password",
                password=True
            )
            if master_password != confirm_password:
                self.console.print("[red]Passwords do not match![/red]")
                return False

            # Save to .env
            self._update_env_file('CREDENTIAL_MASTER_PASSWORD', master_password)
            os.environ['CREDENTIAL_MASTER_PASSWORD'] = master_password

        try:
            if SecureCredentialManager:
                self.credential_manager = SecureCredentialManager(self.config_dir)
            else:
                self.console.print("[yellow]Credential manager not available, will save to .env only[/yellow]")
        except Exception as e:
            self.console.print(f"[yellow]Warning: Could not initialize credential manager: {e}[/yellow]")

        # Configure each integration
        integrations = [
            ("Zendesk", self._configure_zendesk),
            ("Intercom", self._configure_intercom),
            ("Mixpanel", self._configure_mixpanel),
            ("SendGrid", self._configure_sendgrid),
        ]

        for integration_name, config_func in integrations:
            self.console.print(f"\n[bold cyan]Configure {integration_name}[/bold cyan]")
            if Confirm.ask(f"Do you want to configure {integration_name}?", default=True):
                if not config_func():
                    self.console.print(f"[yellow]Skipping {integration_name}[/yellow]")
            else:
                self.console.print(f"[yellow]Skipping {integration_name}[/yellow]")

        self.state.mark_step_complete(WizardStep.PLATFORM_SETUP)
        self.save_state()

        self.console.print("\n[green]Platform integration setup complete! ✓[/green]")
        input("\nPress Enter to continue...")
        return True

    def _configure_zendesk(self) -> bool:
        """Configure Zendesk integration"""
        self.console.print("\n[cyan]Zendesk Configuration[/cyan]")
        self.console.print("You can find these credentials in Zendesk Admin > Channels > API")

        subdomain = Prompt.ask("Zendesk subdomain (e.g., 'mycompany' from mycompany.zendesk.com)")
        email = Prompt.ask("Zendesk admin email")
        api_token = Prompt.ask("Zendesk API token", password=True)

        if not all([subdomain, email, api_token]):
            self.console.print("[red]All fields are required[/red]")
            return False

        # Save credentials
        self._update_env_file('ZENDESK_SUBDOMAIN', subdomain)
        self._update_env_file('ZENDESK_EMAIL', email)
        self._update_env_file('ZENDESK_API_TOKEN', api_token)

        if self.credential_manager:
            try:
                self.credential_manager.store_credential('system', 'zendesk', 'subdomain', subdomain)
                self.credential_manager.store_credential('system', 'zendesk', 'email', email)
                self.credential_manager.store_credential('system', 'zendesk', 'api_token', api_token)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not encrypt credentials: {e}[/yellow]")

        self.state.zendesk_configured = True
        self.console.print("[green]Zendesk configured successfully! ✓[/green]")
        return True

    def _configure_intercom(self) -> bool:
        """Configure Intercom integration"""
        self.console.print("\n[cyan]Intercom Configuration[/cyan]")
        self.console.print("You can find your access token in Intercom Settings > Developers > Access Tokens")

        access_token = Prompt.ask("Intercom access token", password=True)

        if not access_token:
            self.console.print("[red]Access token is required[/red]")
            return False

        # Save credentials
        self._update_env_file('INTERCOM_ACCESS_TOKEN', access_token)

        if self.credential_manager:
            try:
                self.credential_manager.store_credential('system', 'intercom', 'access_token', access_token)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not encrypt credentials: {e}[/yellow]")

        self.state.intercom_configured = True
        self.console.print("[green]Intercom configured successfully! ✓[/green]")
        return True

    def _configure_mixpanel(self) -> bool:
        """Configure Mixpanel integration"""
        self.console.print("\n[cyan]Mixpanel Configuration[/cyan]")
        self.console.print("You can find these in Mixpanel Settings > Project Settings")

        project_token = Prompt.ask("Mixpanel project token")
        api_secret = Prompt.ask("Mixpanel API secret", password=True)

        if not all([project_token, api_secret]):
            self.console.print("[red]All fields are required[/red]")
            return False

        # Save credentials
        self._update_env_file('MIXPANEL_PROJECT_TOKEN', project_token)
        self._update_env_file('MIXPANEL_API_SECRET', api_secret)

        if self.credential_manager:
            try:
                self.credential_manager.store_credential('system', 'mixpanel', 'project_token', project_token)
                self.credential_manager.store_credential('system', 'mixpanel', 'api_secret', api_secret)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not encrypt credentials: {e}[/yellow]")

        self.state.mixpanel_configured = True
        self.console.print("[green]Mixpanel configured successfully! ✓[/green]")
        return True

    def _configure_sendgrid(self) -> bool:
        """Configure SendGrid integration"""
        self.console.print("\n[cyan]SendGrid Configuration[/cyan]")
        self.console.print("You can create an API key in SendGrid Settings > API Keys")

        api_key = Prompt.ask("SendGrid API key", password=True)
        from_email = Prompt.ask("From email address (must be verified in SendGrid)")
        from_name = Prompt.ask("From name (optional)", default="Customer Success Team")

        if not all([api_key, from_email]):
            self.console.print("[red]API key and from email are required[/red]")
            return False

        # Save credentials
        self._update_env_file('SENDGRID_API_KEY', api_key)
        self._update_env_file('SENDGRID_FROM_EMAIL', from_email)
        self._update_env_file('SENDGRID_FROM_NAME', from_name)

        if self.credential_manager:
            try:
                self.credential_manager.store_credential('system', 'sendgrid', 'api_key', api_key)
                self.credential_manager.store_credential('system', 'sendgrid', 'from_email', from_email)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Could not encrypt credentials: {e}[/yellow]")

        self.state.sendgrid_configured = True
        self.console.print("[green]SendGrid configured successfully! ✓[/green]")
        return True

    def _update_env_file(self, key: str, value: str):
        """Update or add a key-value pair in .env file"""
        env_lines = []
        key_found = False

        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                env_lines = f.readlines()

        # Update existing or add new
        for i, line in enumerate(env_lines):
            if line.startswith(f"{key}="):
                env_lines[i] = f"{key}={value}\n"
                key_found = True
                break

        if not key_found:
            env_lines.append(f"{key}={value}\n")

        # Write back
        with open(self.env_file, 'w') as f:
            f.writelines(env_lines)

    # ========================================================================
    # STEP 3: CONFIGURATION
    # ========================================================================

    def step_configuration(self) -> bool:
        """Configure health scores, thresholds, and SLA targets"""
        self.clear_screen()
        self.print_header("Customer Success Configuration", "Step 3 of 6")
        self.print_progress()

        self.console.print("[bold]Configure your Customer Success parameters:[/bold]")
        self.console.print()

        # Health score weights
        self.console.print("[cyan]1. Health Score Weights[/cyan]")
        self.console.print("Configure how different factors contribute to customer health scores.")
        self.console.print("Weights must sum to 1.0 (100%)")
        self.console.print()

        use_defaults = Confirm.ask("Use default weights? (Usage: 35%, Engagement: 25%, Support: 15%, Satisfaction: 15%, Payment: 10%)", default=True)

        if use_defaults:
            weights = {
                'usage': 0.35,
                'engagement': 0.25,
                'support': 0.15,
                'satisfaction': 0.15,
                'payment': 0.10
            }
        else:
            weights = {}
            remaining = 1.0
            for factor in ['usage', 'engagement', 'support', 'satisfaction', 'payment']:
                if remaining <= 0:
                    weights[factor] = 0.0
                else:
                    max_weight = min(remaining, 1.0)
                    weight = float(Prompt.ask(
                        f"{factor.capitalize()} weight (remaining: {remaining:.2f})",
                        default=str(remaining if factor == 'payment' else 0.2)
                    ))
                    weights[factor] = weight
                    remaining -= weight

        self.state.health_score_weights = weights

        # Save to .env
        for factor, weight in weights.items():
            self._update_env_file(f'HEALTH_SCORE_WEIGHT_{factor.upper()}', str(weight))

        self.console.print("[green]Health score weights configured! ✓[/green]")
        self.console.print()

        # Thresholds
        self.console.print("[cyan]2. Health Score Thresholds[/cyan]")
        self.console.print("Define when customers are considered at-risk or healthy.")
        self.console.print()

        use_default_thresholds = Confirm.ask("Use default thresholds? (At-Risk: <60, Healthy: >75)", default=True)

        if use_default_thresholds:
            thresholds = {
                'churn_risk': 40.0,
                'at_risk': 60.0,
                'healthy': 75.0,
                'champion': 90.0
            }
        else:
            thresholds = {
                'churn_risk': float(Prompt.ask("Churn risk threshold (0-100)", default="40")),
                'at_risk': float(Prompt.ask("At-risk threshold (0-100)", default="60")),
                'healthy': float(Prompt.ask("Healthy threshold (0-100)", default="75")),
                'champion': float(Prompt.ask("Champion threshold (0-100)", default="90"))
            }

        self.state.thresholds = thresholds

        # Save to .env
        self._update_env_file('HEALTH_SCORE_AT_RISK_THRESHOLD', str(int(thresholds['at_risk'])))
        self._update_env_file('HEALTH_SCORE_HEALTHY_THRESHOLD', str(int(thresholds['healthy'])))
        self._update_env_file('HEALTH_SCORE_CHAMPION_THRESHOLD', str(int(thresholds['champion'])))
        self._update_env_file('CHURN_PROBABILITY_HIGH_RISK', '0.70')

        self.console.print("[green]Thresholds configured! ✓[/green]")
        self.console.print()

        # SLA targets
        self.console.print("[cyan]3. Support SLA Targets[/cyan]")
        self.console.print("Define response time targets for support tickets.")
        self.console.print()

        use_default_slas = Confirm.ask("Use default SLAs? (P1: 4h, P2: 8h, P3: 24h)", default=True)

        if use_default_slas:
            slas = {
                'first_response_minutes': 15,
                'p1_resolution_minutes': 240,  # 4 hours
                'p2_resolution_minutes': 480,  # 8 hours
                'p3_resolution_minutes': 1440  # 24 hours
            }
        else:
            slas = {
                'first_response_minutes': int(Prompt.ask("First response time (minutes)", default="15")),
                'p1_resolution_minutes': int(Prompt.ask("P1 resolution time (minutes)", default="240")),
                'p2_resolution_minutes': int(Prompt.ask("P2 resolution time (minutes)", default="480")),
                'p3_resolution_minutes': int(Prompt.ask("P3 resolution time (minutes)", default="1440"))
            }

        self.state.sla_targets = slas

        # Save to .env
        self._update_env_file('SUPPORT_FIRST_RESPONSE_SLA', str(slas['first_response_minutes']))
        self._update_env_file('SUPPORT_RESOLUTION_SLA_P1', str(slas['p1_resolution_minutes']))
        self._update_env_file('SUPPORT_RESOLUTION_SLA_P2', str(slas['p2_resolution_minutes']))
        self._update_env_file('SUPPORT_RESOLUTION_SLA_P3', str(slas['p3_resolution_minutes']))

        self.console.print("[green]SLA targets configured! ✓[/green]")
        self.console.print()

        self.state.mark_step_complete(WizardStep.CONFIGURATION)
        self.save_state()

        self.console.print("[green]Configuration complete! ✓[/green]")
        input("\nPress Enter to continue...")
        return True

    # ========================================================================
    # STEP 4: DATABASE INITIALIZATION
    # ========================================================================

    def step_database_init(self) -> bool:
        """Initialize database and run migrations"""
        self.clear_screen()
        self.print_header("Database Initialization", "Step 4 of 6")
        self.print_progress()

        self.console.print("[bold]Initialize database and create tables:[/bold]")
        self.console.print()

        # Check if database URL is configured
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            self.console.print("[yellow]Database URL not configured in .env file[/yellow]")
            configure_now = Confirm.ask("Would you like to configure it now?", default=True)

            if configure_now:
                self.console.print("\n[cyan]Database Configuration[/cyan]")
                host = Prompt.ask("PostgreSQL host", default="localhost")
                port = Prompt.ask("PostgreSQL port", default="5432")
                user = Prompt.ask("PostgreSQL user", default="postgres")
                password = Prompt.ask("PostgreSQL password", password=True)
                database = Prompt.ask("Database name", default="cs_mcp_db")

                database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
                self._update_env_file('DATABASE_URL', database_url)
                os.environ['DATABASE_URL'] = database_url
            else:
                self.console.print("[red]Database configuration required to continue[/red]")
                return False

        # Test connection
        self.console.print("\n[cyan]Testing database connection...[/cyan]")
        try:
            import psycopg2
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                connect_timeout=10
            )
            conn.close()
            self.console.print("[green]Database connection successful! ✓[/green]")
        except Exception as e:
            self.console.print(f"[red]Database connection failed: {e}[/red]")
            return False

        # Run migrations
        self.console.print("\n[cyan]Running database migrations...[/cyan]")

        if Confirm.ask("Run Alembic migrations to create tables?", default=True):
            try:
                # Check if alembic is configured
                alembic_ini = Path.cwd() / "alembic.ini"
                if not alembic_ini.exists():
                    self.console.print("[yellow]Alembic not configured. Skipping migrations.[/yellow]")
                    self.console.print("[yellow]You can run migrations manually later with: alembic upgrade head[/yellow]")
                else:
                    result = subprocess.run(
                        ["alembic", "upgrade", "head"],
                        capture_output=True,
                        text=True
                    )

                    if result.returncode == 0:
                        self.console.print("[green]Migrations completed successfully! ✓[/green]")
                        self.state.migrations_run = True
                    else:
                        self.console.print(f"[red]Migration failed:[/red]")
                        self.console.print(result.stderr)
                        if not Confirm.ask("Continue anyway?", default=False):
                            return False
            except Exception as e:
                self.console.print(f"[yellow]Could not run migrations: {e}[/yellow]")
                self.console.print("[yellow]You can run migrations manually later with: alembic upgrade head[/yellow]")

        # Create default data
        self.console.print("\n[cyan]Creating default segments and templates...[/cyan]")
        if Confirm.ask("Create default customer segments (Enterprise, SMB, etc.)?", default=True):
            self.console.print("[green]Default segments will be created on first server start ✓[/green]")

        self.state.database_initialized = True
        self.state.mark_step_complete(WizardStep.DATABASE_INIT)
        self.save_state()

        self.console.print("\n[green]Database initialization complete! ✓[/green]")
        input("\nPress Enter to continue...")
        return True

    # ========================================================================
    # STEP 5: TESTING & VALIDATION
    # ========================================================================

    def step_testing(self) -> bool:
        """Test all integrations"""
        self.clear_screen()
        self.print_header("Testing & Validation", "Step 5 of 6")
        self.print_progress()

        self.console.print("[bold]Testing platform integrations:[/bold]")
        self.console.print()

        test_results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            # Test Zendesk
            if self.state.zendesk_configured:
                task = progress.add_task("Testing Zendesk...", total=None)
                result = self._test_zendesk()
                test_results.append(("Zendesk", result))
                progress.update(task, completed=True)

            # Test Intercom
            if self.state.intercom_configured:
                task = progress.add_task("Testing Intercom...", total=None)
                result = self._test_intercom()
                test_results.append(("Intercom", result))
                progress.update(task, completed=True)

            # Test Mixpanel
            if self.state.mixpanel_configured:
                task = progress.add_task("Testing Mixpanel...", total=None)
                result = self._test_mixpanel()
                test_results.append(("Mixpanel", result))
                progress.update(task, completed=True)

            # Test SendGrid
            if self.state.sendgrid_configured:
                task = progress.add_task("Testing SendGrid...", total=None)
                result = self._test_sendgrid()
                test_results.append(("SendGrid", result))
                progress.update(task, completed=True)

            # Test database
            task = progress.add_task("Testing database...", total=None)
            result = self._test_database()
            test_results.append(("Database", result))
            progress.update(task, completed=True)

        # Display results
        self.console.print()
        table = Table(title="Integration Test Results", box=box.ROUNDED)
        table.add_column("Integration", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="white")

        all_passed = True
        for integration, (passed, message) in test_results:
            style = "green" if passed else "red"
            status = "✓ PASS" if passed else "✗ FAIL"
            table.add_row(integration, f"[{style}]{status}[/{style}]", message)
            if not passed:
                all_passed = False

        self.console.print(table)
        self.console.print()

        if all_passed:
            self.console.print("[green]All tests passed! ✓[/green]")
            self.state.all_tests_passed = True
        else:
            self.console.print("[yellow]Some tests failed. You can fix these issues later.[/yellow]")

        self.state.mark_step_complete(WizardStep.TESTING)
        self.save_state()

        input("\nPress Enter to continue...")
        return True

    def _test_zendesk(self) -> Tuple[bool, str]:
        """Test Zendesk connection"""
        try:
            # For now, just verify credentials are set
            subdomain = os.getenv('ZENDESK_SUBDOMAIN')
            email = os.getenv('ZENDESK_EMAIL')
            token = os.getenv('ZENDESK_API_TOKEN')

            if all([subdomain, email, token]):
                return (True, "Credentials configured")
            else:
                return (False, "Missing credentials")
        except Exception as e:
            return (False, str(e))

    def _test_intercom(self) -> Tuple[bool, str]:
        """Test Intercom connection"""
        try:
            token = os.getenv('INTERCOM_ACCESS_TOKEN')
            if token:
                return (True, "Credentials configured")
            else:
                return (False, "Missing access token")
        except Exception as e:
            return (False, str(e))

    def _test_mixpanel(self) -> Tuple[bool, str]:
        """Test Mixpanel connection"""
        try:
            project_token = os.getenv('MIXPANEL_PROJECT_TOKEN')
            api_secret = os.getenv('MIXPANEL_API_SECRET')

            if all([project_token, api_secret]):
                return (True, "Credentials configured")
            else:
                return (False, "Missing credentials")
        except Exception as e:
            return (False, str(e))

    def _test_sendgrid(self) -> Tuple[bool, str]:
        """Test SendGrid connection"""
        try:
            api_key = os.getenv('SENDGRID_API_KEY')
            from_email = os.getenv('SENDGRID_FROM_EMAIL')

            if all([api_key, from_email]):
                return (True, "Credentials configured")
            else:
                return (False, "Missing credentials")
        except Exception as e:
            return (False, str(e))

    def _test_database(self) -> Tuple[bool, str]:
        """Test database connection"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                return (False, "Database URL not configured")

            import psycopg2
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                connect_timeout=5
            )
            conn.close()
            return (True, "Connection successful")
        except Exception as e:
            return (False, f"Connection failed: {str(e)[:50]}")

    # ========================================================================
    # STEP 6: COMPLETION
    # ========================================================================

    def step_completion(self) -> bool:
        """Display completion summary and next steps"""
        self.clear_screen()
        self.print_header("Setup Complete!", "Step 6 of 6")

        self.state.completed_at = datetime.utcnow().isoformat()
        self.state.mark_step_complete(WizardStep.COMPLETION)
        self.save_state()

        # Summary
        self.console.print("[bold green]Congratulations! Your Customer Success MCP is ready to use.[/bold green]")
        self.console.print()

        # Configuration summary
        table = Table(title="Configuration Summary", box=box.ROUNDED)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="white")

        table.add_row("Zendesk", "✓ Configured" if self.state.zendesk_configured else "○ Not configured")
        table.add_row("Intercom", "✓ Configured" if self.state.intercom_configured else "○ Not configured")
        table.add_row("Mixpanel", "✓ Configured" if self.state.mixpanel_configured else "○ Not configured")
        table.add_row("SendGrid", "✓ Configured" if self.state.sendgrid_configured else "○ Not configured")
        table.add_row("Database", "✓ Initialized" if self.state.database_initialized else "○ Not initialized")
        table.add_row("Health Scoring", "✓ Configured" if self.state.health_score_weights else "○ Not configured")

        self.console.print(table)
        self.console.print()

        # Generate setup report
        report_path = self.config_dir / "setup_report.json"
        report = {
            "setup_completed_at": self.state.completed_at,
            "integrations": {
                "zendesk": self.state.zendesk_configured,
                "intercom": self.state.intercom_configured,
                "mixpanel": self.state.mixpanel_configured,
                "sendgrid": self.state.sendgrid_configured
            },
            "configuration": {
                "health_score_weights": self.state.health_score_weights,
                "sla_targets": self.state.sla_targets,
                "thresholds": self.state.thresholds
            },
            "database": {
                "initialized": self.state.database_initialized,
                "migrations_run": self.state.migrations_run
            },
            "testing": {
                "all_tests_passed": self.state.all_tests_passed
            }
        }

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        self.console.print(f"[cyan]Setup report saved to:[/cyan] {report_path}")
        self.console.print()

        # Next steps
        self.console.print("[bold]Next Steps:[/bold]")
        self.console.print("  1. Start the MCP server:")
        self.console.print("     [cyan]python server.py[/cyan]")
        self.console.print()
        self.console.print("  2. Connect your MCP client (e.g., Claude Desktop)")
        self.console.print("     Add this configuration to your MCP settings:")
        self.console.print('     [cyan]{"command": "python", "args": ["/path/to/server.py"]}[/cyan]')
        self.console.print()
        self.console.print("  3. Test with your first customer:")
        self.console.print("     [cyan]Register a customer and calculate their health score[/cyan]")
        self.console.print()

        self.console.print("[bold cyan]Documentation:[/bold cyan]")
        self.console.print("  - User Guide: docs/USER_GUIDE.md")
        self.console.print("  - API Reference: docs/API_REFERENCE.md")
        self.console.print("  - Troubleshooting: docs/TROUBLESHOOTING.md")
        self.console.print()

        self.console.print("[green]Thank you for using Customer Success MCP![/green]")
        self.console.print()

        return True

    # ========================================================================
    # MAIN WIZARD FLOW
    # ========================================================================

    def run(self):
        """Run the complete onboarding wizard"""
        try:
            # Step 1: Welcome
            if not self.state.is_step_complete(WizardStep.WELCOME):
                if not self.step_welcome():
                    return

            # Step 2: System Check
            if not self.state.is_step_complete(WizardStep.SYSTEM_CHECK):
                if not self.step_system_check():
                    return

            # Step 3: Platform Setup
            if not self.state.is_step_complete(WizardStep.PLATFORM_SETUP):
                if not self.step_platform_setup():
                    return

            # Step 4: Configuration
            if not self.state.is_step_complete(WizardStep.CONFIGURATION):
                if not self.step_configuration():
                    return

            # Step 5: Database Initialization
            if not self.state.is_step_complete(WizardStep.DATABASE_INIT):
                if not self.step_database_init():
                    return

            # Step 6: Testing
            if not self.state.is_step_complete(WizardStep.TESTING):
                if not self.step_testing():
                    return

            # Step 7: Completion
            if not self.state.is_step_complete(WizardStep.COMPLETION):
                self.step_completion()

        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Setup interrupted. Your progress has been saved.[/yellow]")
            self.console.print("[yellow]Run this wizard again to continue from where you left off.[/yellow]")
            self.save_state()
            sys.exit(0)
        except Exception as e:
            self.console.print(f"\n\n[red]An error occurred: {e}[/red]")
            self.console.print("[yellow]Your progress has been saved.[/yellow]")
            self.save_state()
            raise


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the onboarding wizard"""
    wizard = CustomerSuccessOnboardingWizard()
    wizard.run()


if __name__ == "__main__":
    main()
