"""
Autonomous Workers - Customer Success MCP
Each worker monitors a specific aspect of customer success operations
"""

from .base_worker import AutonomousWorker
from .churn_risk_monitor import ChurnRiskMonitor
from .usage_drop_alerts import UsageDropAlerts
from .onboarding_progress import OnboardingProgress
from .nps_csat_monitor import NPSCSATMonitor
from .support_sla_tracker import SupportSLATracker
from .upsell_detector import UpsellDetector
from .retention_analyzer import RetentionAnalyzer

# Worker registry - maps config keys to worker classes
WORKER_REGISTRY = {
    "churn_risk_monitor": ChurnRiskMonitor,
    "usage_drop_alerts": UsageDropAlerts,
    "onboarding_progress": OnboardingProgress,
    "nps_csat_monitor": NPSCSATMonitor,
    "support_sla_tracker": SupportSLATracker,
    "upsell_detector": UpsellDetector,
    "retention_analyzer": RetentionAnalyzer,
}

__all__ = [
    "AutonomousWorker",
    "WORKER_REGISTRY",
    "ChurnRiskMonitor",
    "UsageDropAlerts",
    "OnboardingProgress",
    "NPSCSATMonitor",
    "SupportSLATracker",
    "UpsellDetector",
    "RetentionAnalyzer",
]
