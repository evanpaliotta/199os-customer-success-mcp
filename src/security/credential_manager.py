"""
Secure Credential Management System
Encrypts and stores client credentials for external tool access

Version 2.0: OWASP 2023 compliant with 600k iterations and cryptographically random salts
"""

import os
import json
import base64
import secrets
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import structlog

logger = structlog.get_logger(__name__)

# OWASP 2023 standard for PBKDF2-HMAC-SHA256
PBKDF2_ITERATIONS_V2 = 600000
PBKDF2_ITERATIONS_V1 = 390000  # Legacy support

# Credential format versions
CREDENTIAL_VERSION_V2 = "2.0"
CREDENTIAL_VERSION_V1 = "1.0"


class SecureCredentialManager:
    """
    Production-grade credential management with encryption at rest.

    Features:
    - AES-256 encryption via Fernet
    - OWASP 2023 compliant (PBKDF2-HMAC-SHA256, 600k iterations)
    - Cryptographically secure random salts (not client_id-derived)
    - Per-client credential isolation
    - Backward compatibility with v1.0 credentials
    - Audit logging of all access
    """

    def __init__(self, config_path: Path, master_password: Optional[str] = None) -> Any:
        """
        Initialize credential manager.

        Args:
            config_path: Base path for configuration storage
            master_password: Master password for encryption (from env in production)
        """
        self.config_path = Path(config_path)
        self.credentials_dir = self.config_path / "credentials"
        self.credentials_dir.mkdir(parents=True, exist_ok=True)

        # Get or generate master password
        self.master_password = master_password or os.getenv('CREDENTIAL_MASTER_PASSWORD')
        if not self.master_password:
            raise ValueError(
                "Master password required. Set CREDENTIAL_MASTER_PASSWORD environment variable."
            )

        # Store master key bytes for per-credential encryption
        self.master_key_bytes = self.master_password.encode()

        logger.info("credential_manager_initialized",
                   config_path=str(config_path),
                   version=CREDENTIAL_VERSION_V2,
                   pbkdf2_iterations=PBKDF2_ITERATIONS_V2)

    def _generate_random_salt(self) -> bytes:
        """
        Generate cryptographically secure random salt.

        Uses secrets module (not os.urandom) for cryptographic strength.
        32 bytes = 256 bits of entropy.
        """
        return secrets.token_bytes(32)

    def _derive_encryption_key(self, salt: bytes, iterations: int = PBKDF2_ITERATIONS_V2) -> bytes:
        """
        Derive encryption key from master password using PBKDF2-HMAC-SHA256.

        Args:
            salt: Random salt (32 bytes)
            iterations: PBKDF2 iteration count (600k for v2.0, 390k for v1.0)

        Returns:
            Base64-encoded Fernet key (44 bytes)
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )

        derived_key = kdf.derive(self.master_key_bytes)
        return base64.urlsafe_b64encode(derived_key)

    def store_credential(self,
                        client_id: str,
                        tool_type: str,
                        credential_key: str,
                        credential_value: str) -> bool:
        """
        Encrypt and store a credential using v2.0 format.

        Args:
            client_id: Unique client identifier
            tool_type: Type of tool (salesforce, gmail, etc.)
            credential_key: Credential name (api_key, client_secret, etc.)
            credential_value: Actual credential value

        Returns:
            True if successful
        """
        try:
            # Validate inputs
            if not all([client_id, tool_type, credential_key, credential_value]):
                raise ValueError("All credential fields required")

            # Load or create client credential file
            creds_file = self._get_credentials_file(client_id)
            credentials = self._load_credentials_file(creds_file)

            # Ensure tool type exists
            if tool_type not in credentials:
                credentials[tool_type] = {}

            # Generate random salt for this credential
            salt = self._generate_random_salt()

            # Derive encryption key from salt
            encryption_key = self._derive_encryption_key(salt, PBKDF2_ITERATIONS_V2)
            cipher = Fernet(encryption_key)

            # Encrypt the credential value
            encrypted_value = cipher.encrypt(credential_value.encode()).decode()

            # Store with metadata (v2.0 format includes salt and version)
            credentials[tool_type][credential_key] = {
                'value': encrypted_value,
                'salt': base64.b64encode(salt).decode(),
                'version': CREDENTIAL_VERSION_V2,
                'iterations': PBKDF2_ITERATIONS_V2,
                'algorithm': 'Fernet-PBKDF2-HMAC-SHA256',
                'created_at': datetime.utcnow().isoformat(),
                'last_accessed': None
            }

            # Save encrypted credentials
            self._save_credentials_file(creds_file, credentials)

            logger.info(
                "credential_stored",
                client_id=client_id,
                tool_type=tool_type,
                credential_key=credential_key,
                version=CREDENTIAL_VERSION_V2
            )

            return True

        except Exception as e:
            logger.error(
                "credential_store_failed",
                client_id=client_id,
                tool_type=tool_type,
                error=str(e)
            )
            raise

    def get_credential(self,
                      client_id: str,
                      tool_type: str,
                      credential_key: str) -> Optional[str]:
        """
        Retrieve and decrypt a credential (supports v1.0 and v2.0).

        Automatically migrates v1.0 credentials to v2.0 on read.

        Args:
            client_id: Unique client identifier
            tool_type: Type of tool
            credential_key: Credential name

        Returns:
            Decrypted credential value or None if not found
        """
        try:
            creds_file = self._get_credentials_file(client_id)

            if not creds_file.exists():
                return None

            credentials = self._load_credentials_file(creds_file)

            if tool_type not in credentials:
                return None

            if credential_key not in credentials[tool_type]:
                return None

            cred_data = credentials[tool_type][credential_key]
            encrypted_value = cred_data['value']

            # Check credential version
            version = cred_data.get('version', CREDENTIAL_VERSION_V1)

            if version == CREDENTIAL_VERSION_V2:
                # v2.0: Use stored salt and iterations
                salt = base64.b64decode(cred_data['salt'].encode())
                iterations = cred_data.get('iterations', PBKDF2_ITERATIONS_V2)

                encryption_key = self._derive_encryption_key(salt, iterations)
                cipher = Fernet(encryption_key)
                decrypted_value = cipher.decrypt(encrypted_value.encode()).decode()

            else:
                # v1.0 (legacy): Use old global cipher method
                # Migrate to v2.0 on next save
                decrypted_value = self._decrypt_v1_credential(encrypted_value)

                # Auto-migrate to v2.0
                logger.info(
                    "migrating_credential_to_v2",
                    client_id=client_id,
                    tool_type=tool_type,
                    credential_key=credential_key
                )
                # Re-encrypt with v2.0 format
                self.store_credential(client_id, tool_type, credential_key, decrypted_value)

            # Update last accessed timestamp
            credentials[tool_type][credential_key]['last_accessed'] = datetime.utcnow().isoformat()
            self._save_credentials_file(creds_file, credentials)

            logger.info(
                "credential_accessed",
                client_id=client_id,
                tool_type=tool_type,
                credential_key=credential_key,
                version=version
            )

            return decrypted_value

        except Exception as e:
            logger.error(
                "credential_retrieval_failed",
                client_id=client_id,
                tool_type=tool_type,
                credential_key=credential_key,
                error=str(e)
            )
            return None

    def _decrypt_v1_credential(self, encrypted_value: str) -> str:
        """
        Decrypt v1.0 credential using legacy global cipher method.

        This maintains backward compatibility with credentials encrypted
        before the v2.0 upgrade (390k iterations, shared salt).
        """
        # Legacy v1.0 used a global cipher with shared salt
        salt_file = self.credentials_dir / ".salt"
        if salt_file.exists():
            salt = salt_file.read_bytes()
        else:
            raise ValueError("v1.0 salt file not found - cannot decrypt legacy credential")

        # Derive key using v1.0 parameters
        encryption_key = self._derive_encryption_key(salt, PBKDF2_ITERATIONS_V1)
        cipher = Fernet(encryption_key)

        return cipher.decrypt(encrypted_value.encode()).decode()

    def get_all_credentials(self, client_id: str, tool_type: str) -> Dict[str, str]:
        """
        Get all credentials for a tool type (supports v1.0 and v2.0).

        Args:
            client_id: Unique client identifier
            tool_type: Type of tool

        Returns:
            Dictionary of decrypted credentials
        """
        try:
            creds_file = self._get_credentials_file(client_id)

            if not creds_file.exists():
                return {}

            credentials = self._load_credentials_file(creds_file)

            if tool_type not in credentials:
                return {}

            # Decrypt all credentials for this tool
            decrypted = {}
            for key, data in credentials[tool_type].items():
                # Use get_credential which handles both versions
                value = self.get_credential(client_id, tool_type, key)
                if value:
                    decrypted[key] = value

            return decrypted

        except Exception as e:
            logger.error(
                "credentials_retrieval_failed",
                client_id=client_id,
                tool_type=tool_type,
                error=str(e)
            )
            return {}

    def delete_credentials(self, client_id: str, tool_type: Optional[str] = None) -> bool:
        """
        Delete credentials for a client.

        Args:
            client_id: Unique client identifier
            tool_type: Optional specific tool type to delete. If None, deletes all.

        Returns:
            True if successful
        """
        try:
            creds_file = self._get_credentials_file(client_id)

            if not creds_file.exists():
                return True

            if tool_type is None:
                # Delete entire credentials file
                creds_file.unlink()
                logger.info("all_credentials_deleted", client_id=client_id)
            else:
                # Delete specific tool credentials
                credentials = self._load_credentials_file(creds_file)
                if tool_type in credentials:
                    del credentials[tool_type]
                    self._save_credentials_file(creds_file, credentials)
                    logger.info(
                        "tool_credentials_deleted",
                        client_id=client_id,
                        tool_type=tool_type
                    )

            return True

        except Exception as e:
            logger.error(
                "credential_deletion_failed",
                client_id=client_id,
                tool_type=tool_type,
                error=str(e)
            )
            return False

    def list_configured_tools(self, client_id: str) -> Dict[str, Any]:
        """
        List all configured tools for a client.

        Args:
            client_id: Unique client identifier

        Returns:
            Dictionary of tool types with metadata
        """
        try:
            creds_file = self._get_credentials_file(client_id)

            if not creds_file.exists():
                return {}

            credentials = self._load_credentials_file(creds_file)

            tools = {}
            for tool_type, creds in credentials.items():
                tools[tool_type] = {
                    'credential_count': len(creds),
                    'credentials': list(creds.keys()),
                    'last_accessed': max(
                        (c.get('last_accessed') for c in creds.values() if c.get('last_accessed')),
                        default=None
                    )
                }

            return tools

        except Exception as e:
            logger.error(
                "list_tools_failed",
                client_id=client_id,
                error=str(e)
            )
            return {}

    def _get_credentials_file(self, client_id: str) -> Path:
        """Get path to client credentials file."""
        # Sanitize client_id for filesystem
        safe_client_id = "".join(c for c in client_id if c.isalnum() or c in ('_', '-'))
        return self.credentials_dir / f"{safe_client_id}.enc"

    def _load_credentials_file(self, creds_file: Path) -> Dict:
        """Load and parse encrypted credentials file."""
        if not creds_file.exists():
            return {}

        try:
            # Read file with restricted permissions check
            if oct(creds_file.stat().st_mode)[-3:] != '600':
                logger.warning(
                    "insecure_permissions",
                    file=str(creds_file),
                    permissions=oct(creds_file.stat().st_mode)
                )

            encrypted_data = creds_file.read_text()
            return json.loads(encrypted_data)
        except Exception as e:
            logger.error("credentials_file_load_failed", file=str(creds_file), error=str(e))
            return {}

    def _save_credentials_file(self, creds_file: Path, credentials: Dict) -> Any:
        """Save encrypted credentials file with secure permissions."""
        try:
            # Write with secure permissions
            creds_file.write_text(json.dumps(credentials, indent=2))
            os.chmod(creds_file, 0o600)  # Owner read/write only

        except Exception as e:
            logger.error("credentials_file_save_failed", file=str(creds_file), error=str(e))
            raise


def test_credential_manager() -> Any:
    """Test the credential manager."""
    import tempfile
    import shutil

    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Set test master password
        os.environ['CREDENTIAL_MASTER_PASSWORD'] = 'test_password_12345'

        # Initialize manager
        manager = SecureCredentialManager(temp_dir)

        # Test 1: Store credential
        print("Test 1: Storing credential...")
        success = manager.store_credential(
            client_id='test_client',
            tool_type='salesforce',
            credential_key='api_key',
            credential_value='secret_key_12345'
        )
        assert success, "Failed to store credential"
        print("✓ Credential stored successfully")

        # Test 2: Retrieve credential
        print("\nTest 2: Retrieving credential...")
        retrieved = manager.get_credential(
            client_id='test_client',
            tool_type='salesforce',
            credential_key='api_key'
        )
        assert retrieved == 'secret_key_12345', f"Retrieved wrong value: {retrieved}"
        print("✓ Credential retrieved successfully")

        # Test 3: Verify encryption
        print("\nTest 3: Verifying encryption...")
        creds_file = manager._get_credentials_file('test_client')
        raw_content = creds_file.read_text()
        assert 'secret_key_12345' not in raw_content, "Credential not encrypted!"
        print("✓ Credential is encrypted in storage")

        # Test 4: List configured tools
        print("\nTest 4: Listing configured tools...")
        tools = manager.list_configured_tools('test_client')
        assert 'salesforce' in tools, "Tool not listed"
        assert tools['salesforce']['credential_count'] == 1, "Wrong credential count"
        print(f"✓ Tools listed: {tools}")

        # Test 5: Delete credentials
        print("\nTest 5: Deleting credentials...")
        success = manager.delete_credentials('test_client', 'salesforce')
        assert success, "Failed to delete credentials"
        retrieved = manager.get_credential('test_client', 'salesforce', 'api_key')
        assert retrieved is None, "Credential not deleted"
        print("✓ Credentials deleted successfully")

        print("\n✅ All tests passed!")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    test_credential_manager()


# Backward compatibility alias for existing imports
CredentialManager = SecureCredentialManager
