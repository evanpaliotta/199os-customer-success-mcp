"""
GDPR Compliance Tools
Implements GDPR Article 15 (Right to Access) and Article 17 (Right to be Forgotten)
"""

import os
import json
import shutil
from typing import Dict, Optional, Any, List, Set
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class GDPRRequestType(Enum):
    """Types of GDPR requests."""
    DATA_EXPORT = "data_export"  # Article 15: Right to Access
    DATA_DELETE = "data_delete"  # Article 17: Right to be Forgotten
    CONSENT_WITHDRAW = "consent_withdraw"
    DATA_PORTABILITY = "data_portability"  # Article 20
    RECTIFICATION = "rectification"  # Article 16


class GDPRRequestStatus(Enum):
    """Status of GDPR request processing."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


class DataCategory(Enum):
    """Categories of personal data."""
    IDENTITY = "identity"  # Name, email, user ID
    CREDENTIALS = "credentials"  # API keys, tokens
    USAGE = "usage"  # Tool executions, queries
    CONFIGURATION = "configuration"  # Client settings
    CONVERSATION = "conversation"  # Chat history
    LEARNING = "learning"  # AI learning data
    AUDIT = "audit"  # Audit logs


class GDPRRequest:
    """Represents a GDPR data subject request."""

    def __init__(
        self,
        request_type: GDPRRequestType,
        client_id: str,
        user_id: Optional[str] = None,
        categories: Optional[List[DataCategory]] = None,
        reason: Optional[str] = None
    ):
        """Initialize a GDPR request."""
        self.request_id = self._generate_request_id()
        self.request_type = request_type
        self.client_id = client_id
        self.user_id = user_id
        self.categories = categories or list(DataCategory)
        self.reason = reason
        self.status = GDPRRequestStatus.PENDING
        self.created_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        self.results: Dict[str, Any] = {}
        self.errors: List[str] = []

    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        random_component = os.urandom(6).hex()
        return f"gdpr-{timestamp}-{random_component}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'request_id': self.request_id,
            'request_type': self.request_type.value,
            'client_id': self.client_id,
            'user_id': self.user_id,
            'categories': [c.value for c in self.categories],
            'reason': self.reason,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'results': self.results,
            'errors': self.errors
        }


class GDPRComplianceManager:
    """
    Production-grade GDPR compliance management system.

    Features:
    - Article 15: Right to Access (data export)
    - Article 17: Right to be Forgotten (data deletion)
    - Article 20: Right to Data Portability
    - Comprehensive data inventory
    - Request tracking and auditing
    - Data retention policies
    """

    def __init__(
        self,
        data_directory: Path,
        audit_logger: Optional[Any] = None
    ):
        """
        Initialize GDPR compliance manager.

        Args:
            data_directory: Base directory containing all data
            audit_logger: Optional audit logger instance
        """
        self.data_directory = Path(data_directory)
        self.audit_logger = audit_logger
        self.requests_directory = self.data_directory / "gdpr_requests"
        self.requests_directory.mkdir(parents=True, exist_ok=True)

        # Define data locations for each category
        self.data_locations = {
            DataCategory.CREDENTIALS: self.data_directory / "credentials",
            DataCategory.CONFIGURATION: self.data_directory / "config",
            DataCategory.CONVERSATION: self.data_directory / "conversations",
            DataCategory.LEARNING: self.data_directory / "learning",
            DataCategory.AUDIT: self.data_directory / "audit_logs",
            DataCategory.USAGE: self.data_directory / "usage_metrics"
        }

        logger.info("gdpr_compliance_manager_initialized", data_directory=str(data_directory))

    def request_data_export(
        self,
        client_id: str,
        user_id: Optional[str] = None,
        categories: Optional[List[DataCategory]] = None
    ) -> GDPRRequest:
        """
        Handle GDPR Article 15 - Right to Access.

        Creates a comprehensive export of all personal data.

        Args:
            client_id: Client identifier
            user_id: Optional specific user identifier
            categories: Optional list of data categories to export

        Returns:
            GDPRRequest object with export results
        """
        try:
            # Create request
            request = GDPRRequest(
                request_type=GDPRRequestType.DATA_EXPORT,
                client_id=client_id,
                user_id=user_id,
                categories=categories
            )

            # Log to audit trail
            if self.audit_logger:
                self.audit_logger.log(
                    event_type=self.audit_logger.AuditEventType.GDPR_EXPORT_REQUEST,
                    client_id=client_id,
                    user_id=user_id,
                    description="GDPR data export requested",
                    metadata={'request_id': request.request_id}
                )

            # Process the export
            request.status = GDPRRequestStatus.IN_PROGRESS
            self._save_request(request)

            export_data = self._collect_personal_data(
                client_id,
                user_id,
                request.categories
            )

            # Create export package
            export_path = self._create_export_package(request, export_data)

            request.status = GDPRRequestStatus.COMPLETED
            request.completed_at = datetime.utcnow()
            request.results = {
                'export_path': str(export_path),
                'total_records': sum(len(v) if isinstance(v, list) else 1 for v in export_data.values()),
                'categories_included': [c.value for c in request.categories]
            }

            self._save_request(request)

            # Log completion
            if self.audit_logger:
                self.audit_logger.log(
                    event_type=self.audit_logger.AuditEventType.GDPR_EXPORT_COMPLETED,
                    client_id=client_id,
                    user_id=user_id,
                    description="GDPR data export completed",
                    metadata={'request_id': request.request_id, 'export_path': str(export_path)}
                )

            logger.info(
                "gdpr_export_completed",
                request_id=request.request_id,
                client_id=client_id
            )

            return request

        except Exception as e:
            logger.error(
                "gdpr_export_failed",
                client_id=client_id,
                error=str(e)
            )

            request.status = GDPRRequestStatus.FAILED
            request.errors.append(str(e))
            self._save_request(request)

            raise

    def request_data_deletion(
        self,
        client_id: str,
        user_id: Optional[str] = None,
        categories: Optional[List[DataCategory]] = None,
        keep_audit_logs: bool = True
    ) -> GDPRRequest:
        """
        Handle GDPR Article 17 - Right to be Forgotten.

        Permanently deletes personal data with option to retain audit logs
        for legal compliance.

        Args:
            client_id: Client identifier
            user_id: Optional specific user identifier
            categories: Optional list of data categories to delete
            keep_audit_logs: If True, retains audit logs (legally required)

        Returns:
            GDPRRequest object with deletion results
        """
        try:
            # Create request
            request = GDPRRequest(
                request_type=GDPRRequestType.DATA_DELETE,
                client_id=client_id,
                user_id=user_id,
                categories=categories
            )

            # Log to audit trail BEFORE deletion
            if self.audit_logger:
                self.audit_logger.log(
                    event_type=self.audit_logger.AuditEventType.GDPR_DELETE_REQUEST,
                    client_id=client_id,
                    user_id=user_id,
                    description="GDPR data deletion requested",
                    metadata={'request_id': request.request_id, 'keep_audit_logs': keep_audit_logs}
                )

            # Process deletion
            request.status = GDPRRequestStatus.IN_PROGRESS
            self._save_request(request)

            # Filter categories if audit logs should be kept
            deletion_categories = request.categories.copy()
            if keep_audit_logs and DataCategory.AUDIT in deletion_categories:
                deletion_categories.remove(DataCategory.AUDIT)
                logger.info("audit_logs_retained", client_id=client_id)

            # Perform deletion
            deletion_results = self._delete_personal_data(
                client_id,
                user_id,
                deletion_categories
            )

            request.status = GDPRRequestStatus.COMPLETED
            request.completed_at = datetime.utcnow()
            request.results = deletion_results

            self._save_request(request)

            # Log completion
            if self.audit_logger:
                self.audit_logger.log(
                    event_type=self.audit_logger.AuditEventType.GDPR_DELETE_COMPLETED,
                    client_id=client_id,
                    user_id=user_id,
                    description="GDPR data deletion completed",
                    metadata={'request_id': request.request_id, 'results': deletion_results}
                )

            logger.info(
                "gdpr_deletion_completed",
                request_id=request.request_id,
                client_id=client_id,
                deleted_categories=len(deletion_categories)
            )

            return request

        except Exception as e:
            logger.error(
                "gdpr_deletion_failed",
                client_id=client_id,
                error=str(e)
            )

            request.status = GDPRRequestStatus.FAILED
            request.errors.append(str(e))
            self._save_request(request)

            raise

    def get_data_inventory(self, client_id: str) -> Dict[str, Any]:
        """
        Get comprehensive inventory of all data for a client.

        Args:
            client_id: Client identifier

        Returns:
            Dictionary with data categories and counts
        """
        try:
            inventory = {}

            for category, location in self.data_locations.items():
                if not location.exists():
                    inventory[category.value] = {
                        'exists': False,
                        'record_count': 0,
                        'storage_size_bytes': 0
                    }
                    continue

                # Count files and size
                file_pattern = self._get_file_pattern(client_id, category)
                matching_files = list(location.glob(file_pattern))

                total_size = sum(f.stat().st_size for f in matching_files if f.is_file())
                record_count = len(matching_files)

                inventory[category.value] = {
                    'exists': True,
                    'record_count': record_count,
                    'storage_size_bytes': total_size,
                    'storage_size_mb': round(total_size / (1024 * 1024), 2)
                }

            logger.info("data_inventory_generated", client_id=client_id)
            return inventory

        except Exception as e:
            logger.error(
                "data_inventory_failed",
                client_id=client_id,
                error=str(e)
            )
            return {}

    def get_request_status(self, request_id: str) -> Optional[GDPRRequest]:
        """
        Get status of a GDPR request.

        Args:
            request_id: Request identifier

        Returns:
            GDPRRequest object or None if not found
        """
        try:
            request_file = self.requests_directory / f"{request_id}.json"

            if not request_file.exists():
                return None

            data = json.loads(request_file.read_text())

            # Reconstruct request object
            request = GDPRRequest.__new__(GDPRRequest)
            request.request_id = data['request_id']
            request.request_type = GDPRRequestType(data['request_type'])
            request.client_id = data['client_id']
            request.user_id = data['user_id']
            request.categories = [DataCategory(c) for c in data['categories']]
            request.reason = data['reason']
            request.status = GDPRRequestStatus(data['status'])
            request.created_at = datetime.fromisoformat(data['created_at'])
            request.completed_at = datetime.fromisoformat(data['completed_at']) if data['completed_at'] else None
            request.results = data['results']
            request.errors = data['errors']

            return request

        except Exception as e:
            logger.error(
                "request_status_retrieval_failed",
                request_id=request_id,
                error=str(e)
            )
            return None

    def apply_retention_policy(
        self,
        retention_days: Dict[DataCategory, int]
    ) -> Dict[str, int]:
        """
        Apply data retention policies across all clients.

        Args:
            retention_days: Dictionary mapping categories to retention days

        Returns:
            Dictionary with deletion counts per category
        """
        try:
            deletion_counts = {}

            for category, days in retention_days.items():
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                count = self._delete_old_data(category, cutoff_date)
                deletion_counts[category.value] = count

            logger.info(
                "retention_policy_applied",
                deletion_counts=deletion_counts
            )

            return deletion_counts

        except Exception as e:
            logger.error("retention_policy_failed", error=str(e))
            return {}

    def _collect_personal_data(
        self,
        client_id: str,
        user_id: Optional[str],
        categories: List[DataCategory]
    ) -> Dict[str, Any]:
        """Collect all personal data for export."""
        data = {
            'client_id': client_id,
            'user_id': user_id,
            'export_date': datetime.utcnow().isoformat(),
            'categories': {}
        }

        for category in categories:
            location = self.data_locations.get(category)

            if not location or not location.exists():
                data['categories'][category.value] = []
                continue

            try:
                category_data = self._collect_category_data(
                    client_id,
                    user_id,
                    category,
                    location
                )
                data['categories'][category.value] = category_data

            except Exception as e:
                logger.error(
                    "category_collection_failed",
                    category=category.value,
                    error=str(e)
                )
                data['categories'][category.value] = {'error': str(e)}

        return data

    def _collect_category_data(
        self,
        client_id: str,
        user_id: Optional[str],
        category: DataCategory,
        location: Path
    ) -> List[Dict[str, Any]]:
        """Collect data for a specific category."""
        data = []

        file_pattern = self._get_file_pattern(client_id, category)
        matching_files = list(location.glob(file_pattern))

        for file in matching_files:
            if not file.is_file():
                continue

            try:
                # Read and parse file
                if file.suffix == '.json':
                    content = json.loads(file.read_text())
                    data.append({
                        'file': file.name,
                        'data': content
                    })
                elif file.suffix == '.jsonl':
                    # Read JSON lines
                    lines = []
                    with file.open('r') as f:
                        for line in f:
                            if line.strip():
                                lines.append(json.loads(line))
                    data.append({
                        'file': file.name,
                        'data': lines
                    })
                else:
                    # For other files, include metadata only
                    data.append({
                        'file': file.name,
                        'size_bytes': file.stat().st_size,
                        'modified': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                    })

            except Exception as e:
                logger.error(
                    "file_read_failed",
                    file=str(file),
                    error=str(e)
                )

        return data

    def _delete_personal_data(
        self,
        client_id: str,
        user_id: Optional[str],
        categories: List[DataCategory]
    ) -> Dict[str, Any]:
        """Delete personal data across categories."""
        results = {
            'deleted_files': 0,
            'deleted_bytes': 0,
            'categories_processed': [],
            'errors': []
        }

        for category in categories:
            location = self.data_locations.get(category)

            if not location or not location.exists():
                continue

            try:
                file_pattern = self._get_file_pattern(client_id, category)
                matching_files = list(location.glob(file_pattern))

                for file in matching_files:
                    if file.is_file():
                        size = file.stat().st_size
                        file.unlink()
                        results['deleted_files'] += 1
                        results['deleted_bytes'] += size

                results['categories_processed'].append(category.value)

                logger.info(
                    "category_deletion_completed",
                    category=category.value,
                    files_deleted=len(matching_files)
                )

            except Exception as e:
                error_msg = f"{category.value}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(
                    "category_deletion_failed",
                    category=category.value,
                    error=str(e)
                )

        return results

    def _delete_old_data(
        self,
        category: DataCategory,
        cutoff_date: datetime
    ) -> int:
        """Delete data older than cutoff date for a category."""
        location = self.data_locations.get(category)

        if not location or not location.exists():
            return 0

        deleted_count = 0

        try:
            for file in location.glob("*"):
                if not file.is_file():
                    continue

                file_mtime = datetime.fromtimestamp(file.stat().st_mtime)

                if file_mtime < cutoff_date:
                    file.unlink()
                    deleted_count += 1

            logger.info(
                "old_data_deleted",
                category=category.value,
                count=deleted_count
            )

        except Exception as e:
            logger.error(
                "old_data_deletion_failed",
                category=category.value,
                error=str(e)
            )

        return deleted_count

    def _create_export_package(
        self,
        request: GDPRRequest,
        export_data: Dict[str, Any]
    ) -> Path:
        """Create export package as JSON file."""
        export_dir = self.requests_directory / "exports"
        export_dir.mkdir(exist_ok=True)

        export_file = export_dir / f"{request.request_id}_export.json"

        export_package = {
            'request': request.to_dict(),
            'data': export_data,
            'metadata': {
                'format_version': '1.0',
                'exported_by': '199OS Sales MCP Server',
                'export_date': datetime.utcnow().isoformat()
            }
        }

        export_file.write_text(json.dumps(export_package, indent=2))

        # Secure permissions
        os.chmod(export_file, 0o600)

        return export_file

    def _get_file_pattern(self, client_id: str, category: DataCategory) -> str:
        """Get file pattern for client and category."""
        safe_client_id = "".join(c for c in client_id if c.isalnum() or c in ('_', '-'))

        # Different patterns for different categories
        if category == DataCategory.CREDENTIALS:
            return f"{safe_client_id}.enc"
        elif category == DataCategory.AUDIT:
            return f"audit_{safe_client_id}_*.jsonl"
        elif category == DataCategory.CONFIGURATION:
            return f"{safe_client_id}_config.json"
        else:
            return f"{safe_client_id}_*.json*"

    def _save_request(self, request: GDPRRequest):
        """Save request to disk."""
        request_file = self.requests_directory / f"{request.request_id}.json"
        request_file.write_text(json.dumps(request.to_dict(), indent=2))
        os.chmod(request_file, 0o600)


def test_gdpr_compliance():
    """Test GDPR compliance manager."""
    import tempfile

    temp_dir = Path(tempfile.mkdtemp())

    try:
        print("Test 1: Initializing GDPR compliance manager...")
        manager = GDPRComplianceManager(temp_dir)
        print("✓ Manager initialized")

        # Create test data
        print("\nTest 2: Creating test data...")
        credentials_dir = temp_dir / "credentials"
        credentials_dir.mkdir(exist_ok=True)
        (credentials_dir / "test_client.enc").write_text('{"test": "data"}')
        print("✓ Test data created")

        print("\nTest 3: Getting data inventory...")
        inventory = manager.get_data_inventory('test_client')
        print(f"✓ Inventory: {inventory}")

        print("\nTest 4: Requesting data export...")
        export_request = manager.request_data_export(
            client_id='test_client',
            categories=[DataCategory.CREDENTIALS]
        )
        assert export_request.status == GDPRRequestStatus.COMPLETED
        print(f"✓ Export completed: {export_request.request_id}")

        print("\nTest 5: Getting request status...")
        status = manager.get_request_status(export_request.request_id)
        assert status is not None
        assert status.request_id == export_request.request_id
        print(f"✓ Request status: {status.status.value}")

        print("\nTest 6: Requesting data deletion...")
        delete_request = manager.request_data_deletion(
            client_id='test_client',
            categories=[DataCategory.CREDENTIALS],
            keep_audit_logs=True
        )
        assert delete_request.status == GDPRRequestStatus.COMPLETED
        print(f"✓ Deletion completed: {delete_request.request_id}")

        print("\nTest 7: Verifying deletion...")
        inventory_after = manager.get_data_inventory('test_client')
        assert inventory_after[DataCategory.CREDENTIALS.value]['record_count'] == 0
        print("✓ Data deleted successfully")

        print("\n✅ All tests passed!")

    finally:
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    test_gdpr_compliance()
