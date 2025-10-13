# Secrets Management Guide

Comprehensive guide for managing secrets, credentials, and sensitive configuration in the Customer Success MCP system.

## Table of Contents

- [Overview](#overview)
- [Secret Types](#secret-types)
- [Storage Solutions](#storage-solutions)
- [Environment-Specific Configuration](#environment-specific-configuration)
- [Secret Rotation](#secret-rotation)
- [Access Control](#access-control)
- [Development Workflow](#development-workflow)
- [Production Deployment](#production-deployment)
- [Emergency Procedures](#emergency-procedures)
- [Audit and Compliance](#audit-and-compliance)

## Overview

### Security Principles

1. **Never commit secrets to version control**
2. **Use different secrets per environment**
3. **Rotate secrets regularly**
4. **Implement least privilege access**
5. **Encrypt secrets at rest and in transit**
6. **Audit all secret access**
7. **Have a secret rotation plan**

### What is a Secret?

Secrets are sensitive data that should never be exposed:
- Database passwords
- API keys and tokens
- Encryption keys
- OAuth client secrets
- Service account credentials
- Webhook signing secrets
- TLS/SSL certificates
- Session secrets
- JWT signing keys

## Secret Types

### 1. Database Credentials

```bash
# PostgreSQL
DB_HOST=postgres.example.com
DB_PORT=5432
DB_NAME=cs_mcp_production
DB_USER=cs_mcp_app
DB_PASSWORD=<strong_random_password>
DB_SSL_MODE=require
DB_CONNECTION_TIMEOUT=10000

# Redis
REDIS_HOST=redis.example.com
REDIS_PORT=6379
REDIS_PASSWORD=<strong_random_password>
REDIS_TLS=true
```

**Best Practices**:
- Use strong, randomly generated passwords (32+ characters)
- Enable SSL/TLS for all connections
- Use separate credentials per environment
- Rotate passwords quarterly

### 2. External Integration API Keys

```bash
# Zendesk
ZENDESK_SUBDOMAIN=yourcompany
ZENDESK_API_TOKEN=<api_token>
ZENDESK_EMAIL=api@yourcompany.com

# Intercom
INTERCOM_ACCESS_TOKEN=<access_token>

# Mixpanel
MIXPANEL_API_SECRET=<api_secret>
MIXPANEL_PROJECT_TOKEN=<project_token>
```

**Best Practices**:
- Use OAuth tokens over API keys when possible
- Set API key expiration dates
- Use scoped tokens (minimal permissions)
- Monitor API usage for anomalies
- Store in secrets manager, not environment variables in production

### 3. Encryption Keys

```bash
# Application encryption
ENCRYPTION_KEY=<256-bit_base64_encoded_key>
ENCRYPTION_ALGORITHM=AES-256-GCM

# JWT signing
JWT_SECRET=<strong_random_secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Session encryption
SESSION_SECRET=<strong_random_secret>
```

**Best Practices**:
- Use cryptographically secure random generation
- Store master keys in HSM or KMS
- Implement key versioning for rotation
- Never reuse keys across environments

### 4. AWS Credentials

```bash
# AWS Access
AWS_ACCESS_KEY_ID=<access_key>
AWS_SECRET_ACCESS_KEY=<secret_key>
AWS_REGION=us-east-1

# Or prefer IAM roles (no credentials needed)
AWS_ROLE_ARN=arn:aws:iam::123456789012:role/cs-mcp-app
```

**Best Practices**:
- Use IAM roles instead of access keys when possible
- Enable MFA for production accounts
- Use temporary credentials (STS) for short-lived access
- Set up CloudTrail for audit logging

### 5. Monitoring and Alerting

```bash
# Slack webhooks
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
SLACK_ALERT_CHANNEL=#mcp-alerts

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@yourcompany.com
SMTP_PASSWORD=<app_specific_password>

# PagerDuty
PAGERDUTY_SERVICE_KEY=<service_key>
```

**Best Practices**:
- Use webhook URLs with authentication
- Rotate webhook URLs if exposed
- Monitor webhook usage for abuse
- Use app-specific passwords for email

## Storage Solutions

### 1. AWS Secrets Manager (Recommended for Production)

**Advantages**:
- Automatic rotation
- Fine-grained access control (IAM)
- Encryption at rest (KMS)
- Audit logging (CloudTrail)
- Cross-region replication
- Integration with RDS, ECS, Lambda

**Setup**:

```bash
# Install AWS CLI
pip install awscli

# Create secret
aws secretsmanager create-secret \
    --name cs-mcp/production/database \
    --description "Database credentials for CS MCP production" \
    --secret-string '{
        "username": "cs_mcp_app",
        "password": "strong_random_password",
        "host": "postgres.example.com",
        "port": 5432,
        "database": "cs_mcp_production"
    }'

# Enable automatic rotation
aws secretsmanager rotate-secret \
    --secret-id cs-mcp/production/database \
    --rotation-lambda-arn arn:aws:lambda:region:account:function:SecretsManager-rotation \
    --rotation-rules AutomaticallyAfterDays=90
```

**Application Integration**:

```python
import boto3
import json
from functools import lru_cache

@lru_cache(maxsize=1)
def get_secret(secret_name: str) -> dict:
    """Retrieve secret from AWS Secrets Manager with caching"""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        logger.error(f"Failed to retrieve secret: {e}")
        raise

# Usage
db_credentials = get_secret('cs-mcp/production/database')
DATABASE_URL = f"postgresql://{db_credentials['username']}:{db_credentials['password']}@{db_credentials['host']}:{db_credentials['port']}/{db_credentials['database']}"
```

### 2. HashiCorp Vault

**Advantages**:
- Multi-cloud and on-premises support
- Dynamic secrets (generated on-demand)
- Encryption as a service
- Detailed audit logs
- Secrets versioning
- Lease management with automatic renewal

**Setup**:

```bash
# Install Vault
brew install vault  # macOS
# or
wget https://releases.hashicorp.com/vault/1.15.0/vault_1.15.0_linux_amd64.zip

# Start Vault server (dev mode for testing)
vault server -dev

# Enable secrets engine
vault secrets enable -path=cs-mcp kv-v2

# Store secret
vault kv put cs-mcp/production/database \
    username=cs_mcp_app \
    password=strong_random_password \
    host=postgres.example.com

# Read secret
vault kv get cs-mcp/production/database

# Enable audit logging
vault audit enable file file_path=/var/log/vault_audit.log
```

**Application Integration**:

```python
import hvac
import os

def get_vault_client():
    """Initialize Vault client"""
    client = hvac.Client(
        url=os.getenv('VAULT_ADDR', 'http://localhost:8200'),
        token=os.getenv('VAULT_TOKEN')
    )

    if not client.is_authenticated():
        raise Exception("Vault authentication failed")

    return client

def get_secret_from_vault(path: str) -> dict:
    """Retrieve secret from Vault"""
    client = get_vault_client()
    secret = client.secrets.kv.v2.read_secret_version(
        path=path,
        mount_point='cs-mcp'
    )
    return secret['data']['data']

# Usage
db_credentials = get_secret_from_vault('production/database')
```

### 3. Environment Variables (Development Only)

**Use only for**:
- Local development
- Testing environments
- Non-sensitive configuration

**Never use for**:
- Production secrets
- Committed `.env` files
- Shared development environments

**Setup**:

```bash
# .env.local (gitignored)
DB_PASSWORD=local_dev_password
API_KEY=test_api_key

# Load with python-dotenv
from dotenv import load_dotenv
load_dotenv('.env.local')
```

### 4. Kubernetes Secrets

**For containerized deployments**:

```yaml
# Create secret
apiVersion: v1
kind: Secret
metadata:
  name: cs-mcp-secrets
  namespace: production
type: Opaque
stringData:
  db_password: strong_random_password
  api_key: your_api_key

# Mount as environment variables
spec:
  containers:
  - name: cs-mcp
    envFrom:
    - secretRef:
        name: cs-mcp-secrets
```

**Best Practices**:
- Use external secret operators (AWS Secrets Manager CSI driver)
- Enable encryption at rest for etcd
- Use RBAC to restrict secret access
- Rotate secrets regularly

## Environment-Specific Configuration

### Development

**File**: `.env.development` (gitignored)

```bash
# Use non-sensitive values
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cs_mcp_dev
DB_USER=postgres
DB_PASSWORD=dev_password

# Use test API keys
ZENDESK_API_TOKEN=test_token
INTERCOM_ACCESS_TOKEN=test_token

# Disable external services
MONITORING_ENABLED=false
SLACK_WEBHOOK_URL=
```

### Staging

**File**: `.env.staging` (never committed)

```bash
# Use staging credentials
DB_HOST=staging-db.internal
DB_PASSWORD=<staging_password>

# Use staging API keys
ZENDESK_SUBDOMAIN=yourcompany-staging
ZENDESK_API_TOKEN=<staging_token>

# Enable monitoring
MONITORING_ENABLED=true
```

### Production

**Storage**: AWS Secrets Manager / HashiCorp Vault (never in files)

```bash
# All secrets retrieved from secrets manager
# No .env file in production

# Example: Retrieve from AWS Secrets Manager
SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:cs-mcp-prod
```

## Secret Rotation

### Rotation Schedule

| Secret Type | Rotation Frequency | Method |
|-------------|-------------------|--------|
| Database passwords | Every 90 days | Automated |
| API keys | Every 180 days | Manual |
| Encryption keys | Every 365 days | Automated with versioning |
| JWT secrets | Every 30 days | Automated |
| TLS certificates | Before expiration | Automated (Let's Encrypt) |

### Automated Rotation Process

**1. Create Rotation Lambda (AWS)**:

```python
# lambda/rotate_secret.py
import boto3
import psycopg2
import secrets
import string

def generate_password(length=32):
    """Generate secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def lambda_handler(event, context):
    """Rotate database password"""
    service_client = boto3.client('secretsmanager')

    # Get secret ARN
    arn = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']

    # Get current secret
    current_dict = get_secret_dict(service_client, arn, "AWSCURRENT")

    if step == "createSecret":
        # Generate new password
        new_password = generate_password()

        # Store new version
        service_client.put_secret_value(
            SecretId=arn,
            ClientRequestToken=token,
            SecretString=json.dumps({
                **current_dict,
                'password': new_password
            }),
            VersionStages=['AWSPENDING']
        )

    elif step == "setSecret":
        # Update database with new password
        pending_dict = get_secret_dict(service_client, arn, "AWSPENDING", token)

        conn = psycopg2.connect(
            host=current_dict['host'],
            user=current_dict['username'],
            password=current_dict['password'],
            database='postgres'
        )

        with conn.cursor() as cur:
            cur.execute(
                f"ALTER USER {current_dict['username']} PASSWORD %s",
                (pending_dict['password'],)
            )
        conn.commit()
        conn.close()

    elif step == "testSecret":
        # Test new password works
        pending_dict = get_secret_dict(service_client, arn, "AWSPENDING", token)

        conn = psycopg2.connect(
            host=pending_dict['host'],
            user=pending_dict['username'],
            password=pending_dict['password'],
            database=pending_dict['database']
        )
        conn.close()

    elif step == "finishSecret":
        # Move AWSCURRENT to AWSPENDING
        service_client.update_secret_version_stage(
            SecretId=arn,
            VersionStage="AWSCURRENT",
            MoveToVersionId=token,
            RemoveFromVersionId=current_dict['version']
        )

    return {"statusCode": 200}
```

**2. Manual Rotation Procedure**:

```bash
#!/bin/bash
# scripts/rotate_api_key.sh

SECRET_NAME="cs-mcp/production/api-keys"
KEY_NAME="zendesk_api_token"

echo "Starting rotation for $KEY_NAME..."

# 1. Generate new API key in Zendesk UI
echo "Step 1: Generate new API key in Zendesk admin panel"
echo "Go to: Admin > Channels > API > Add API Token"
read -p "Enter new API token: " NEW_TOKEN

# 2. Store new token in Secrets Manager
echo "Step 2: Storing new token..."
aws secretsmanager put-secret-value \
    --secret-id $SECRET_NAME \
    --secret-string "{\"$KEY_NAME\": \"$NEW_TOKEN\"}"

# 3. Update application configuration
echo "Step 3: Restarting application..."
kubectl rollout restart deployment/cs-mcp -n production

# 4. Wait for deployment
kubectl rollout status deployment/cs-mcp -n production

# 5. Test new token
echo "Step 4: Testing new token..."
curl -H "Authorization: Bearer $NEW_TOKEN" \
    https://yourcompany.zendesk.com/api/v2/tickets.json

# 6. Revoke old token
echo "Step 5: Revoke old token in Zendesk admin panel"
echo "IMPORTANT: Manually revoke the old token now!"

echo "Rotation complete!"
```

## Access Control

### IAM Policy for AWS Secrets Manager

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:cs-mcp/production/*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
    }
  ]
}
```

### Principle of Least Privilege

**Production Access**:
- Application: Read-only access to production secrets
- Ops team: Rotate, create, delete secrets
- Developers: No access to production secrets
- CI/CD: Read-only access for deployments

**Access Matrix**:

| Role | Development | Staging | Production |
|------|-------------|---------|------------|
| Developers | Read/Write | Read | None |
| DevOps | Read/Write | Read/Write | Read |
| SRE | Read/Write | Read/Write | Read/Write |
| CI/CD | Read | Read | Read |
| Application | Read | Read | Read |

## Development Workflow

### 1. Local Development Setup

```bash
# 1. Copy example env file
cp .env.example .env.local

# 2. Request access to development secrets
# Contact ops team for shared development credentials

# 3. Load secrets into environment
source .env.local

# 4. Verify secrets loaded
python scripts/verify_secrets.py
```

### 2. Never Commit Secrets

**.gitignore**:
```gitignore
# Environment files
.env
.env.local
.env.development
.env.staging
.env.production
.env.*.local

# Secret files
secrets/
*.pem
*.key
*.p12
*.pfx
credentials.json
service-account.json

# AWS
.aws/credentials

# Terraform
terraform.tfvars
*.tfstate
*.tfstate.backup
```

### 3. Pre-commit Hooks

**Install git-secrets**:
```bash
# macOS
brew install git-secrets

# Initialize
cd /path/to/repo
git secrets --install
git secrets --register-aws
```

**Custom patterns** (`.git-secrets-patterns`):
```
(password|passwd|pwd)[\s]*=[\s]*['\"][^'\"]+['\"]
(api[_-]?key|apikey)[\s]*=[\s]*['\"][^'\"]+['\"]
(secret|token)[\s]*=[\s]*['\"][^'\"]+['\"]
(access[_-]?key[_-]?id)[\s]*=[\s]*['\"]AK[A-Z0-9]{16,}['\"]
-----BEGIN (RSA|OPENSSH|DSA|EC|PGP) PRIVATE KEY-----
```

### 4. Secret Scanning

**Use tools**:
- **truffleHog**: `trufflehog --regex --entropy=True .`
- **gitleaks**: `gitleaks detect --source . --verbose`
- **detect-secrets**: `detect-secrets scan --all-files`

**GitHub Integration**:
```yaml
# .github/workflows/secret-scan.yml
name: Secret Scanning
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@v2
```

## Production Deployment

### 1. Secrets Initialization

```bash
# scripts/init_production_secrets.sh
#!/bin/bash

set -euo pipefail

echo "Initializing production secrets..."

# Database credentials
aws secretsmanager create-secret \
    --name cs-mcp/production/database \
    --secret-string '{
        "username": "cs_mcp_app",
        "password": "'$(openssl rand -base64 32)'",
        "host": "prod-db.example.com",
        "port": 5432,
        "database": "cs_mcp_production"
    }' \
    --tags Key=Environment,Value=production Key=Application,Value=cs-mcp

# Redis credentials
aws secretsmanager create-secret \
    --name cs-mcp/production/redis \
    --secret-string '{
        "host": "prod-redis.example.com",
        "port": 6379,
        "password": "'$(openssl rand -base64 32)'"
    }' \
    --tags Key=Environment,Value=production

# Encryption keys
aws secretsmanager create-secret \
    --name cs-mcp/production/encryption \
    --secret-string '{
        "key": "'$(openssl rand -base64 32)'",
        "algorithm": "AES-256-GCM"
    }' \
    --tags Key=Environment,Value=production

echo "Production secrets initialized successfully"
```

### 2. Application Startup

```python
# src/config/secrets.py
import os
import boto3
import json
from functools import lru_cache
from typing import Dict, Any

class SecretsManager:
    """Centralized secrets management"""

    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.region = os.getenv('AWS_REGION', 'us-east-1')

        if self.environment == 'production':
            self.client = boto3.client('secretsmanager', region_name=self.region)
        else:
            self.client = None

    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """Retrieve secret from appropriate source"""

        if self.environment == 'development':
            # Use environment variables in development
            return self._get_from_env(secret_name)

        # Use AWS Secrets Manager in staging/production
        full_secret_name = f"cs-mcp/{self.environment}/{secret_name}"

        try:
            response = self.client.get_secret_value(SecretId=full_secret_name)
            return json.loads(response['SecretString'])
        except Exception as e:
            logger.error(f"Failed to retrieve secret {full_secret_name}: {e}")
            raise

    def _get_from_env(self, secret_name: str) -> Dict[str, Any]:
        """Fallback to environment variables"""
        # Map secret names to env vars
        env_mapping = {
            'database': {
                'host': os.getenv('DB_HOST'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'username': os.getenv('DB_USER'),
                'password': os.getenv('DB_PASSWORD'),
                'database': os.getenv('DB_NAME')
            },
            'redis': {
                'host': os.getenv('REDIS_HOST'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'password': os.getenv('REDIS_PASSWORD')
            }
        }
        return env_mapping.get(secret_name, {})

# Global instance
secrets_manager = SecretsManager()

# Usage in application
def get_database_url() -> str:
    """Get database connection URL"""
    db = secrets_manager.get_secret('database')
    return f"postgresql://{db['username']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}"
```

### 3. Container Deployment (ECS)

```json
{
  "family": "cs-mcp-production",
  "taskRoleArn": "arn:aws:iam::123456789012:role/cs-mcp-task-role",
  "executionRoleArn": "arn:aws:iam::123456789012:role/cs-mcp-execution-role",
  "containerDefinitions": [
    {
      "name": "cs-mcp",
      "image": "cs-mcp:latest",
      "secrets": [
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:cs-mcp/production/database:password::"
        },
        {
          "name": "REDIS_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:cs-mcp/production/redis:password::"
        }
      ]
    }
  ]
}
```

## Emergency Procedures

### 1. Secret Leak Response

**If a secret is exposed (e.g., committed to Git)**:

```bash
#!/bin/bash
# scripts/emergency_secret_rotation.sh

echo "🚨 EMERGENCY SECRET ROTATION 🚨"
echo "This will rotate all production secrets immediately"
read -p "Are you sure? (type 'EMERGENCY' to continue): " confirm

if [ "$confirm" != "EMERGENCY" ]; then
    echo "Aborted"
    exit 1
fi

# 1. Rotate database password
echo "Rotating database password..."
aws secretsmanager rotate-secret \
    --secret-id cs-mcp/production/database \
    --rotation-lambda-arn arn:aws:lambda:us-east-1:123456789012:function:RotateSecret \
    --rotate-immediately

# 2. Rotate API keys
echo "Rotating API keys..."
# ... manual steps for each integration ...

# 3. Rotate encryption keys
echo "Rotating encryption keys..."
aws secretsmanager rotate-secret \
    --secret-id cs-mcp/production/encryption \
    --rotate-immediately

# 4. Force restart all services
echo "Restarting all services..."
kubectl rollout restart deployment/cs-mcp -n production

# 5. Notify team
echo "Notifying ops team..."
curl -X POST $SLACK_WEBHOOK_URL -d '{
    "text": "🚨 EMERGENCY: All production secrets rotated due to exposure",
    "channel": "#ops-alerts"
}'

echo "Emergency rotation complete. Monitor logs for issues."
```

**Git History Cleanup**:
```bash
# Remove secret from Git history
git filter-branch --force --index-filter \
    'git rm --cached --ignore-unmatch path/to/secret/file' \
    --prune-empty --tag-name-filter cat -- --all

# Or use BFG Repo-Cleaner (faster)
bfg --delete-files secret_file.env
bfg --replace-text passwords.txt  # File containing secrets to replace

# Force push
git push origin --force --all
git push origin --force --tags
```

### 2. Lost Access Recovery

**If AWS access is lost**:
1. Use root account to reset IAM credentials
2. Create new IAM user with appropriate policies
3. Update application with new credentials
4. Test access before removing old credentials

### 3. Compromise Detection

**Signs of compromise**:
- Unusual API usage patterns
- Failed authentication attempts
- Access from unexpected IP addresses
- Secrets accessed outside normal hours

**Response**:
1. Immediately rotate all affected secrets
2. Review CloudTrail/audit logs
3. Check for unauthorized changes
4. Notify security team
5. Document incident

## Audit and Compliance

### 1. Enable Audit Logging

**AWS CloudTrail**:
```bash
aws cloudtrail create-trail \
    --name cs-mcp-secrets-audit \
    --s3-bucket-name cs-mcp-audit-logs \
    --include-global-service-events \
    --is-multi-region-trail \
    --enable-log-file-validation

# Start logging
aws cloudtrail start-logging --name cs-mcp-secrets-audit

# Query logs
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=ResourceType,AttributeValue=AWS::SecretsManager::Secret \
    --max-results 50
```

### 2. Regular Audits

**Monthly audit checklist**:
- [ ] Review all secret access logs
- [ ] Verify rotation schedules are being followed
- [ ] Check for unused secrets (delete if not needed)
- [ ] Validate IAM policies (principle of least privilege)
- [ ] Test secret rotation procedures
- [ ] Review list of people with access
- [ ] Check for secrets in Git history
- [ ] Verify backup and recovery procedures

### 3. Compliance Requirements

**For SOC 2 / ISO 27001**:
- Documented secrets management policy
- Regular access reviews (quarterly)
- Encryption at rest and in transit
- Automated rotation where possible
- Audit logging enabled
- Incident response procedures
- Annual penetration testing

**For GDPR / CCPA**:
- Data encryption using managed keys
- Access controls and authentication
- Audit trail of all secret access
- Documented data retention policies
- Procedures for data deletion

## Best Practices Summary

### Do's ✅

1. **Use a secrets manager** (AWS Secrets Manager, Vault)
2. **Rotate secrets regularly** (automated where possible)
3. **Use different secrets per environment**
4. **Enable audit logging** (CloudTrail, Vault audit)
5. **Implement least privilege access**
6. **Encrypt secrets at rest and in transit**
7. **Use pre-commit hooks** to prevent commits
8. **Have an incident response plan**
9. **Test rotation procedures regularly**
10. **Document all secrets and their purpose**

### Don'ts ❌

1. **Never commit secrets to Git**
2. **Never hardcode secrets in code**
3. **Never share secrets via email/Slack**
4. **Never use same secret across environments**
5. **Never log secrets** (even in debug mode)
6. **Never store secrets in CI/CD configs**
7. **Never use default/weak passwords**
8. **Never skip rotation after exposure**
9. **Never grant unnecessary access**
10. **Never ignore security alerts**

## Tools and Resources

### Secret Management Tools
- **AWS Secrets Manager**: https://aws.amazon.com/secrets-manager/
- **HashiCorp Vault**: https://www.vaultproject.io/
- **Azure Key Vault**: https://azure.microsoft.com/en-us/services/key-vault/
- **Google Secret Manager**: https://cloud.google.com/secret-manager

### Secret Scanning Tools
- **truffleHog**: https://github.com/trufflesecurity/trufflehog
- **gitleaks**: https://github.com/gitleaks/gitleaks
- **detect-secrets**: https://github.com/Yelp/detect-secrets
- **git-secrets**: https://github.com/awslabs/git-secrets

### Password Generation
```bash
# Generate secure random password
openssl rand -base64 32

# Generate alphanumeric password
openssl rand -hex 16

# Generate password with special characters
< /dev/urandom tr -dc 'A-Za-z0-9!"#$%&()*+,-./:;<=>?@[\]^_{|}~' | head -c 32
```

### Encryption Key Generation
```bash
# Generate 256-bit AES key
openssl rand -base64 32

# Generate RSA key pair
openssl genrsa -out private.pem 4096
openssl rsa -in private.pem -pubout -out public.pem
```

## Support and Questions

For questions about secrets management:
1. Review this documentation
2. Check AWS Secrets Manager docs
3. Consult with the security team
4. Contact DevOps for access issues

**Security incidents**: Report immediately to security@yourcompany.com
