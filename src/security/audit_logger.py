"""
GDPR-Compliant Audit Logging System
Provides immutable audit trails for all system operations with full compliance to data protection regulations
"""

import os
import json
import hashlib
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class AuditEventType(Enum):
    """Types of auditable events."""
    # Authentication & Authorization
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    AUTH_TOKEN_CREATED = "auth.token.created"
    AUTH_TOKEN_REVOKED = "auth.token.revoked"

    # Data Access
    DATA_READ = "data.read"
    DATA_CREATE = "data.create"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"

    # GDPR Operations
    GDPR_EXPORT_REQUEST = "gdpr.export.request"
    GDPR_EXPORT_COMPLETED = "gdpr.export.completed"
    GDPR_DELETE_REQUEST = "gdpr.delete.request"
    GDPR_DELETE_COMPLETED = "gdpr.delete.completed"
    GDPR_CONSENT_GRANTED = "gdpr.consent.granted"
    GDPR_CONSENT_REVOKED = "gdpr.consent.revoked"

    # Credential Management
    CREDENTIAL_STORED = "credential.stored"
    CREDENTIAL_ACCESSED = "credential.accessed"
    CREDENTIAL_DELETED = "credential.deleted"
    CREDENTIAL_ROTATED = "credential.rotated"

    # Tool Execution
    TOOL_EXECUTED = "tool.executed"
    TOOL_FAILED = "tool.failed"

    # Configuration
    CONFIG_UPDATED = "config.updated"
    CONFIG_DELETED = "config.deleted"

    # System Events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog:
    """
    Represents a single immutable audit log entry.

    Each log entry is cryptographically chained to the previous entry
    to ensure tamper-evidence.
    """

    def __init__(
        self,
        event_type: AuditEventType,
        client_id: str,
        user_id: Optional[str],
        severity: AuditSeverity,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        previous_hash: Optional[str] = None
    ):
        """Initialize an audit log entry."""
        self.event_id = self._generate_event_id()
        self.timestamp = datetime.utcnow()
        self.event_type = event_type
        self.client_id = client_id
        self.user_id = user_id
        self.severity = severity
        self.description = description
        self.metadata = metadata or {}
        self.previous_hash = previous_hash
        self.hash = self._compute_hash()

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        timestamp_ns = datetime.utcnow().timestamp() * 1_000_000
        random_component = os.urandom(8).hex()
        return f"{int(timestamp_ns)}-{random_component}"

    def _compute_hash(self) -> str:
        """
        Compute cryptographic hash of this log entry.

        This creates a chain of hashes similar to blockchain,
        making tampering immediately detectable.
        """
        hash_data = {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'client_id': self.client_id,
            'user_id': self.user_id,
            'severity': self.severity.value,
            'description': self.description,
            'metadata': self.metadata,
            'previous_hash': self.previous_hash
        }

        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'client_id': self.client_id,
            'user_id': self.user_id,
            'severity': self.severity.value,
            'description': self.description,
            'metadata': self.metadata,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditLog':
        """Reconstruct audit log from dictionary."""
        log = cls.__new__(cls)
        log.event_id = data['event_id']
        log.timestamp = datetime.fromisoformat(data['timestamp'])
        log.event_type = AuditEventType(data['event_type'])
        log.client_id = data['client_id']
        log.user_id = data['user_id']
        log.severity = AuditSeverity(data['severity'])
        log.description = data['description']
        log.metadata = data['metadata']
        log.previous_hash = data['previous_hash']
        log.hash = data['hash']
        return log

    def verify_integrity(self) -> bool:
        """Verify the integrity of this log entry."""
        computed_hash = self._compute_hash()
        return computed_hash == self.hash


class AuditLogger:
    """
    Production-grade audit logging system with GDPR compliance.

    Features:
    - Immutable log entries with cryptographic chaining
    - Client isolation for multi-tenant systems
    - Automatic log rotation
    - GDPR-compliant data retention
    - Tamper detection
    - Efficient searching and filtering
    """

    def __init__(
        self,
        log_directory: Path,
        retention_days: int = 2555,  # 7 years for GDPR compliance
        max_file_size_mb: int = 100
    ):
        """
        Initialize the audit logger.

        Args:
            log_directory: Directory for storing audit logs
            retention_days: Number of days to retain logs (default 7 years)
            max_file_size_mb: Maximum size of a single log file before rotation
        """
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)

        self.retention_days = retention_days
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

        # Cache the last hash for chain continuity
        self._last_hash_cache: Dict[str, Optional[str]] = {}

        logger.info(
            "audit_logger_initialized",
            log_directory=str(log_directory),
            retention_days=retention_days
        )

    def log(
        self,
        event_type: AuditEventType,
        client_id: str,
        description: str,
        user_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an immutable audit log entry.

        Args:
            event_type: Type of event being logged
            client_id: Client identifier
            description: Human-readable description
            user_id: Optional user identifier
            severity: Event severity
            metadata: Additional structured data

        Returns:
            Event ID of the created log entry
        """
        try:
            # Get the previous hash for chain continuity
            previous_hash = self._get_last_hash(client_id)

            # Create the audit log entry
            audit_log = AuditLog(
                event_type=event_type,
                client_id=client_id,
                user_id=user_id,
                severity=severity,
                description=description,
                metadata=metadata,
                previous_hash=previous_hash
            )

            # Write to log file
            self._write_log_entry(client_id, audit_log)

            # Update the last hash cache
            self._last_hash_cache[client_id] = audit_log.hash

            # Log to structured logger as well
            logger.info(
                "audit_log_created",
                event_id=audit_log.event_id,
                event_type=event_type.value,
                client_id=client_id,
                severity=severity.value
            )

            return audit_log.event_id

        except Exception as e:
            logger.error(
                "audit_log_creation_failed",
                event_type=event_type.value,
                client_id=client_id,
                error=str(e)
            )
            raise

    def get_logs(
        self,
        client_id: str,
        event_type: Optional[AuditEventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[AuditLog]:
        """
        Retrieve audit logs with filtering.

        Args:
            client_id: Client identifier
            event_type: Optional filter by event type
            start_date: Optional start date filter
            end_date: Optional end date filter
            user_id: Optional filter by user
            limit: Maximum number of logs to return

        Returns:
            List of audit log entries
        """
        try:
            logs = []
            log_files = self._get_log_files(client_id)

            for log_file in log_files:
                if len(logs) >= limit:
                    break

                file_logs = self._read_log_file(log_file)

                for log in file_logs:
                    # Apply filters
                    if event_type and log.event_type != event_type:
                        continue

                    if start_date and log.timestamp < start_date:
                        continue

                    if end_date and log.timestamp > end_date:
                        continue

                    if user_id and log.user_id != user_id:
                        continue

                    logs.append(log)

                    if len(logs) >= limit:
                        break

            return logs

        except Exception as e:
            logger.error(
                "audit_log_retrieval_failed",
                client_id=client_id,
                error=str(e)
            )
            return []

    def verify_chain_integrity(self, client_id: str) -> bool:
        """
        Verify the integrity of the audit log chain for a client.

        Args:
            client_id: Client identifier

        Returns:
            True if the chain is intact and unmodified
        """
        try:
            log_files = self._get_log_files(client_id)
            previous_hash = None

            for log_file in log_files:
                logs = self._read_log_file(log_file)

                for log in logs:
                    # Verify individual log integrity
                    if not log.verify_integrity():
                        logger.error(
                            "audit_log_integrity_violation",
                            client_id=client_id,
                            event_id=log.event_id,
                            reason="hash_mismatch"
                        )
                        return False

                    # Verify chain continuity
                    if log.previous_hash != previous_hash:
                        logger.error(
                            "audit_log_chain_violation",
                            client_id=client_id,
                            event_id=log.event_id,
                            expected_previous=previous_hash,
                            actual_previous=log.previous_hash
                        )
                        return False

                    previous_hash = log.hash

            logger.info("audit_chain_verified", client_id=client_id)
            return True

        except Exception as e:
            logger.error(
                "audit_chain_verification_failed",
                client_id=client_id,
                error=str(e)
            )
            return False

    def purge_old_logs(self) -> int:
        """
        Remove logs older than retention period.

        Returns:
            Number of files deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            deleted_count = 0

            for log_file in self.log_directory.glob("*.jsonl"):
                # Parse date from filename
                try:
                    date_str = log_file.stem.split('_')[-1]
                    file_date = datetime.strptime(date_str, "%Y%m%d")

                    if file_date < cutoff_date:
                        log_file.unlink()
                        deleted_count += 1
                        logger.info("audit_log_purged", file=str(log_file))
                except (ValueError, IndexError):
                    # Skip files that don't match expected naming
                    continue

            logger.info("audit_log_purge_completed", deleted_count=deleted_count)
            return deleted_count

        except Exception as e:
            logger.error("audit_log_purge_failed", error=str(e))
            return 0

    def export_logs(
        self,
        client_id: str,
        output_path: Path,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bool:
        """
        Export audit logs for GDPR compliance.

        Args:
            client_id: Client identifier
            output_path: Path to export file
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            True if export successful
        """
        try:
            logs = self.get_logs(
                client_id=client_id,
                start_date=start_date,
                end_date=end_date,
                limit=1_000_000  # No practical limit for export
            )

            export_data = {
                'client_id': client_id,
                'export_date': datetime.utcnow().isoformat(),
                'total_logs': len(logs),
                'logs': [log.to_dict() for log in logs]
            }

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(export_data, indent=2))

            # Log the export operation itself
            self.log(
                event_type=AuditEventType.GDPR_EXPORT_COMPLETED,
                client_id=client_id,
                description=f"Exported {len(logs)} audit logs",
                severity=AuditSeverity.INFO,
                metadata={'output_path': str(output_path), 'log_count': len(logs)}
            )

            logger.info(
                "audit_logs_exported",
                client_id=client_id,
                log_count=len(logs),
                output_path=str(output_path)
            )

            return True

        except Exception as e:
            logger.error(
                "audit_log_export_failed",
                client_id=client_id,
                error=str(e)
            )
            return False

    def _get_log_file_path(self, client_id: str) -> Path:
        """Get the current log file path for a client."""
        # Sanitize client_id
        safe_client_id = "".join(c for c in client_id if c.isalnum() or c in ('_', '-'))
        date_str = datetime.utcnow().strftime("%Y%m%d")
        return self.log_directory / f"audit_{safe_client_id}_{date_str}.jsonl"

    def _get_log_files(self, client_id: str) -> List[Path]:
        """Get all log files for a client, sorted by date."""
        safe_client_id = "".join(c for c in client_id if c.isalnum() or c in ('_', '-'))
        pattern = f"audit_{safe_client_id}_*.jsonl"
        files = list(self.log_directory.glob(pattern))
        return sorted(files)

    def _write_log_entry(self, client_id: str, audit_log: AuditLog):
        """Write a log entry to file."""
        log_file = self._get_log_file_path(client_id)

        # Check if rotation needed
        if log_file.exists() and log_file.stat().st_size > self.max_file_size_bytes:
            # Create new file with timestamp suffix
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_client_id = "".join(c for c in client_id if c.isalnum() or c in ('_', '-'))
            log_file = self.log_directory / f"audit_{safe_client_id}_{timestamp}.jsonl"

        # Append log entry as JSON line
        with log_file.open('a') as f:
            f.write(json.dumps(audit_log.to_dict()) + '\n')

        # Ensure secure permissions
        os.chmod(log_file, 0o600)

    def _read_log_file(self, log_file: Path) -> List[AuditLog]:
        """Read all log entries from a file."""
        logs = []

        try:
            with log_file.open('r') as f:
                for line in f:
                    if line.strip():
                        log_data = json.loads(line)
                        logs.append(AuditLog.from_dict(log_data))
        except Exception as e:
            logger.error("log_file_read_failed", file=str(log_file), error=str(e))

        return logs

    def _get_last_hash(self, client_id: str) -> Optional[str]:
        """Get the hash of the last log entry for chain continuity."""
        # Check cache first
        if client_id in self._last_hash_cache:
            return self._last_hash_cache[client_id]

        # Read from files
        log_files = self._get_log_files(client_id)
        if not log_files:
            return None

        # Read the last file
        last_file = log_files[-1]
        logs = self._read_log_file(last_file)

        if logs:
            last_hash = logs[-1].hash
            self._last_hash_cache[client_id] = last_hash
            return last_hash

        return None


def test_audit_logger():
    """Test the audit logging system."""
    import tempfile
    import shutil

    temp_dir = Path(tempfile.mkdtemp())

    try:
        print("Test 1: Creating audit logger...")
        audit_logger = AuditLogger(temp_dir, retention_days=365)
        print("✓ Audit logger created")

        print("\nTest 2: Logging events...")
        event_id1 = audit_logger.log(
            event_type=AuditEventType.AUTH_LOGIN,
            client_id='test_client',
            user_id='user123',
            description='User logged in successfully',
            severity=AuditSeverity.INFO,
            metadata={'ip_address': '192.168.1.1'}
        )
        print(f"✓ Event 1 logged: {event_id1}")

        event_id2 = audit_logger.log(
            event_type=AuditEventType.DATA_READ,
            client_id='test_client',
            user_id='user123',
            description='User accessed customer data',
            severity=AuditSeverity.INFO,
            metadata={'resource': 'customer_123'}
        )
        print(f"✓ Event 2 logged: {event_id2}")

        print("\nTest 3: Retrieving logs...")
        logs = audit_logger.get_logs('test_client')
        assert len(logs) == 2, f"Expected 2 logs, got {len(logs)}"
        print(f"✓ Retrieved {len(logs)} logs")

        print("\nTest 4: Verifying chain integrity...")
        is_valid = audit_logger.verify_chain_integrity('test_client')
        assert is_valid, "Chain integrity check failed"
        print("✓ Chain integrity verified")

        print("\nTest 5: Filtering logs by event type...")
        auth_logs = audit_logger.get_logs(
            'test_client',
            event_type=AuditEventType.AUTH_LOGIN
        )
        assert len(auth_logs) == 1, f"Expected 1 auth log, got {len(auth_logs)}"
        print(f"✓ Filtered logs: {len(auth_logs)}")

        print("\nTest 6: Exporting logs...")
        export_path = temp_dir / "export.json"
        success = audit_logger.export_logs('test_client', export_path)
        assert success, "Export failed"
        assert export_path.exists(), "Export file not created"
        print(f"✓ Logs exported to {export_path}")

        print("\nTest 7: Testing tamper detection...")
        # Manually modify a log file
        log_files = list(temp_dir.glob("*.jsonl"))
        if log_files:
            with log_files[0].open('r+') as f:
                lines = f.readlines()
                if lines:
                    # Modify the description
                    log_data = json.loads(lines[0])
                    log_data['description'] = 'TAMPERED'
                    f.seek(0)
                    f.write(json.dumps(log_data) + '\n')
                    f.truncate()

            # Verify integrity should fail
            is_valid = audit_logger.verify_chain_integrity('test_client')
            assert not is_valid, "Tamper detection failed"
            print("✓ Tampering detected successfully")

        print("\n✅ All tests passed!")

    finally:
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    test_audit_logger()
