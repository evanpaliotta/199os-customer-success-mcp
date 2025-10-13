# Security Policy

## 🔒 Security Overview

The 199OS Customer Success MCP Server implements enterprise-grade security controls to protect sensitive customer data and ensure secure operations. This document outlines our security architecture, compliance frameworks, and incident response procedures.

**Last Updated:** October 10, 2025
**Security Contact:** security@199os.com
**Vulnerability Disclosure:** See section 9 below

---

## 1. Security Architecture

### 1.1 Defense in Depth

The platform implements multiple layers of security:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Network Security (TLS/SSL, Firewall)              │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Authentication & Authorization (JWT, API Keys)    │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Input Validation & Sanitization (873-line module) │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Encryption (AES-256, Transit & At-Rest)           │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: Audit Logging (Complete Activity Trail)           │
├─────────────────────────────────────────────────────────────┤
│  Layer 6: Secure File Operations (Path Traversal Prevention)│
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Security Modules

**Location:** `src/security/`

| Module | Lines | Purpose |
|--------|-------|---------|
| `input_validation.py` | 873 | SQL injection, XSS, path traversal, command injection prevention |
| `credential_manager.py` | 193 | AES-256 credential encryption and secure storage |
| `audit_logger.py` | 266 | Comprehensive activity audit trail |
| `gdpr_compliance.py` | 288 | GDPR data handling and compliance |

---

## 2. Authentication & Authorization

### 2.1 Supported Authentication Methods

#### JWT (JSON Web Tokens)
- **Use Case:** API authentication
- **Algorithm:** HS256 (HMAC with SHA-256)
- **Token Expiration:** 24 hours (configurable)
- **Refresh Tokens:** Supported with 7-day expiration
- **Secret Length:** Minimum 32 characters (64 recommended)

**Configuration:**
```bash
JWT_SECRET=<generate-with-openssl-rand-base64-64>
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=7
```

#### API Key Authentication
- **Use Case:** MCP server authentication
- **Format:** Bearer token
- **Rotation:** Recommended every 90 days
- **Scope:** Server-level access

**Configuration:**
```bash
MCP_API_KEY=<your-secure-api-key>
```

#### Platform Integration Authentication
Each platform integration uses its own authentication:
- **Zendesk:** Email + API Token
- **Intercom:** Access Token
- **Mixpanel:** Project Token + API Secret
- **SendGrid:** API Key
- **Salesforce:** Username + Password + Security Token
- **HubSpot:** Access Token

### 2.2 Password Requirements

**Master Password (for credential encryption):**
- Minimum length: 16 characters
- Recommended: 32 characters
- Must be cryptographically random
- **Generation:**
  ```bash
  openssl rand -base64 32
  ```

**User Passwords (if implementing user management):**
- Minimum length: 12 characters
- Must contain: uppercase, lowercase, number, special character
- Cannot reuse last 5 passwords
- Password hashing: bcrypt with cost factor 12

### 2.3 Multi-Factor Authentication (MFA)

**Status:** Supported for user accounts
**Methods:**
- Time-based One-Time Password (TOTP)
- SMS (via Twilio integration)
- Email verification codes

---

## 3. Encryption Standards

### 3.1 Data at Rest

#### Credentials Encryption
- **Algorithm:** AES-256-CBC
- **Key Derivation:** PBKDF2 with 600,000 iterations (OWASP 2023 recommendation)
- **Implementation:** `src/security/credential_manager.py`
- **Master Password:** Required for encryption/decryption

**What's Encrypted:**
- Platform API keys and tokens
- Database credentials
- Webhook secrets
- OAuth tokens and refresh tokens
- Custom integration credentials

**Configuration:**
```bash
ENCRYPTION_KEY=<generate-with-openssl-rand-hex-32>
MASTER_PASSWORD=<your-secure-master-password>
```

#### Database Encryption
- **PostgreSQL:** TLS connections required (`DB_SSL_MODE=require`)
- **Column-Level Encryption:** Available for PII fields
- **Backup Encryption:** Enabled by default

### 3.2 Data in Transit

#### TLS/SSL Requirements
- **Minimum Version:** TLS 1.2
- **Recommended:** TLS 1.3
- **Cipher Suites:** Only strong ciphers allowed (no RC4, 3DES, MD5)
- **Certificate Validation:** Strict mode enabled

**Platform API Connections:**
All external platform integrations use HTTPS with certificate pinning where supported:
- Zendesk: HTTPS with TLS 1.2+
- Intercom: HTTPS with TLS 1.2+
- Mixpanel: HTTPS with TLS 1.2+
- SendGrid: HTTPS with TLS 1.2+

#### Webhook Security
- **HMAC Signature Validation:** All incoming webhooks verified
- **Algorithm:** HMAC-SHA256
- **Secret Rotation:** Supported via configuration
- **Replay Prevention:** Timestamp validation (5-minute window)

**Configuration:**
```bash
WEBHOOK_SECRET=<your-webhook-secret>
WEBHOOK_TIMESTAMP_TOLERANCE=300  # seconds
```

---

## 4. Input Validation & Sanitization

### 4.1 Comprehensive Input Validation

**Module:** `src/security/input_validation.py` (873 lines)

#### SQL Injection Prevention
- **9 Detection Patterns:** SELECT, INSERT, UPDATE, DELETE, DROP, UNION, --, ;, xp_
- **Method:** Regex pattern matching + Pydantic validation
- **Coverage:** All database query inputs

**Blocked Patterns:**
```python
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|DECLARE)\b)",
    r"(--|;|\/\*|\*\/|xp_|sp_)",
    r"('(\s)*(OR|AND)(\s)*')",
    r"(\bOR\b\s+\d+\s*=\s*\d+)",
    # ... 5 more patterns
]
```

#### XSS (Cross-Site Scripting) Prevention
- **6 Detection Patterns:** `<script>`, `javascript:`, `on*=`, `<iframe>`, `<object>`, `<embed>`
- **Method:** HTML tag and event handler detection
- **Coverage:** All user-generated content fields

#### Path Traversal Prevention
- **6 Detection Patterns:** `../`, `..`, `%2e%2e`, `..\`, `\\..\`, `/\.\./`
- **Method:** Path normalization + whitelist validation
- **Coverage:** All file path inputs

#### Command Injection Prevention
- **Pattern Detection:** Shell metacharacters (`;`, `&`, `|`, `` ` ``, `$`, `(`, `)`)
- **Method:** Character blacklisting
- **Coverage:** All system command inputs

### 4.2 Pydantic Validators

All tool inputs validated using Pydantic models with security validators:

```python
class SafeString(BaseModel):
    value: constr(min_length=1, max_length=1000)

    @field_validator('value')
    @classmethod
    def validate_security(cls, v: str) -> str:
        SecurityValidator.validate_no_sql_injection(v)
        SecurityValidator.validate_no_xss(v)
        return v
```

**Validator Classes:**
- `SafeString` - General string validation
- `ClientIdentifier` - Client ID validation (alphanumeric + hyphen/underscore)
- `EmailAddress` - RFC 5321 compliant email validation
- `PhoneNumber` - E.164 format validation
- `URLValidator` - Safe URL validation
- `QueryFilter` - Safe database query filters
- `PaginationInput` - Pagination parameter validation

### 4.3 Rate Limiting

**Purpose:** Prevent abuse and brute-force attacks

**Limits:**
```bash
MAX_REQUESTS_PER_MINUTE=1000  # Global limit
MAX_REQUESTS_PER_HOUR=10000
RATE_LIMIT_PER_CLIENT_PER_MINUTE=100  # Per-client limit
```

**Implementation:**
- Token bucket algorithm
- Redis-backed storage for distributed rate limiting
- Automatic IP blocking after threshold violations

---

## 5. Secure File Operations

### 5.1 SafeFileOperations Class

**Module:** `src/utils/file_operations.py`

**Security Features:**
- **Path Traversal Prevention:** All file paths validated before access
- **Whitelist Validation:** Only allowed directories accessible
- **Filename Sanitization:** Removes dangerous characters
- **Permission Checks:** Verifies read/write permissions before operations
- **Size Limits:** Maximum file size enforced

**Allowed Directories:**
```python
ALLOWED_DIRECTORIES = [
    './data/',
    './logs/',
    './config/preferences/',
    './credentials/',
]
```

**Dangerous Filename Patterns Blocked:**
```python
# Hidden files
if filename.startswith('.') or filename in ('.', '..'):
    raise ValidationError("Invalid filename")

# Dangerous extensions
BLOCKED_EXTENSIONS = ['.exe', '.bat', '.sh', '.ps1', '.dll']
```

### 5.2 Credential Storage

**Location:** `./credentials/` directory

**Permissions:**
- **Directory:** `chmod 700` (owner read/write/execute only)
- **Files:** `chmod 600` (owner read/write only)
- **Owner:** Application user (non-root)

**File Structure:**
```
credentials/
├── platform_credentials.enc  # AES-256 encrypted
├── api_keys.enc
└── oauth_tokens.enc
```

---

## 6. Audit Logging

### 6.1 Comprehensive Audit Trail

**Module:** `src/security/audit_logger.py` (266 lines)

**What's Logged:**
- All authentication attempts (success and failure)
- Tool executions with parameters
- Data modifications (create, update, delete)
- Credential access and changes
- Security policy violations
- System configuration changes
- Administrative actions

**Log Format:**
```json
{
  "timestamp": "2025-10-10T14:23:45.123Z",
  "event_type": "tool_execution",
  "user_id": "user_12345",
  "client_id": "cs_client_abc",
  "tool_name": "calculate_health_score",
  "parameters": {
    "client_id": "cs_client_abc",
    "scoring_model": "weighted_composite"
  },
  "result_status": "success",
  "ip_address": "192.168.1.100",
  "user_agent": "MCP/1.0",
  "session_id": "sess_xyz789"
}
```

**Sensitive Data Exclusion:**
- Passwords never logged
- API keys never logged
- Encryption keys never logged
- PII redacted from logs

### 6.2 Log Retention

**Default Retention:** 90 days
**Long-term Archive:** 7 years (for compliance)
**Log Rotation:** Daily
**Backup:** Encrypted backups to secure storage

**Configuration:**
```bash
AUDIT_LOG_RETENTION_DAYS=90
AUDIT_LOG_DIR=./config/audit_logs
AUDIT_LOG_MAX_SIZE_MB=100
```

### 6.3 Log Access Control

**Who Can Access Logs:**
- Security administrators
- Compliance officers (read-only)
- Platform administrators (with MFA)

**Log Integrity:**
- Cryptographic hashing (SHA-256)
- Tamper detection mechanisms
- Immutable append-only writes

---

## 7. Compliance Frameworks

### 7.1 GDPR (General Data Protection Regulation)

**Module:** `src/security/gdpr_compliance.py` (288 lines)

**Implemented Features:**

#### Right to Access (Article 15)
- Tool: `export_customer_data(client_id)` → Full data export in JSON format

#### Right to Erasure (Article 17 - "Right to be Forgotten")
- Tool: `delete_customer_data(client_id, verification_code)` → Complete data deletion
- **Verification Required:** Double confirmation for safety
- **Cascading Delete:** All related records removed
- **Audit Trail:** Deletion logged permanently

#### Right to Data Portability (Article 20)
- Export Format: JSON, CSV, XML
- Includes: All customer data, health scores, interaction history

#### Data Breach Notification (Article 33-34)
- **Detection:** Automated breach detection systems
- **Notification Timeline:** Within 72 hours
- **Stakeholders:** Supervisory authority + affected individuals
- **Documentation:** Breach register maintained

**Configuration:**
```bash
GDPR_COMPLIANCE_ENABLED=true
DATA_RETENTION_POLICY_DAYS=730  # 2 years default
GDPR_CONTACT_EMAIL=privacy@199os.com
```

**Data Processing Agreement:**
- Available in `docs/compliance/DPA_TEMPLATE.md`
- Must be signed before processing customer data
- Reviewed annually

### 7.2 SOC 2 Type II

**Status:** Preparing for SOC 2 Type II audit

**Trust Service Principles:**
1. **Security** ✅ - Comprehensive security controls implemented
2. **Availability** ✅ - 99.9% uptime SLA, monitoring, health checks
3. **Processing Integrity** ✅ - Data validation, audit logging
4. **Confidentiality** ✅ - Encryption at rest and in transit
5. **Privacy** ✅ - GDPR compliance, data minimization

**Key Controls:**
- Access control policies
- Change management procedures
- Incident response plan
- Backup and disaster recovery
- Vendor management
- Security awareness training

### 7.3 HIPAA (Health Insurance Portability and Accountability Act)

**Status:** HIPAA-ready architecture

**Technical Safeguards:**
- **Access Control** ✅ - Unique user identification, emergency access
- **Audit Controls** ✅ - Comprehensive logging of access to ePHI
- **Integrity** ✅ - Encryption, checksums, version control
- **Transmission Security** ✅ - TLS 1.2+, encrypted communications

**Note:** Full HIPAA compliance requires Business Associate Agreement (BAA)

### 7.4 PCI DSS (Payment Card Industry Data Security Standard)

**Status:** Not applicable (no credit card data stored)

If integrating with payment systems:
- Use tokenization (never store raw card data)
- Stripe, PayPal, or other PCI-compliant processors
- SAQ A (Cardholder Not Present, Fully Outsourced) questionnaire

---

## 8. Security Incident Response

### 8.1 Incident Response Team

**Security Incident Commander:** CTO
**Security Lead:** Head of Engineering
**Communications Lead:** Customer Success Director
**Legal Advisor:** General Counsel

**Contact:** security@199os.com
**Emergency Hotline:** +1-XXX-XXX-XXXX (24/7)

### 8.2 Incident Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| **P0 - Critical** | Active data breach, system compromise | Immediate (< 15 min) | Database breach, credential leak |
| **P1 - High** | Potential data exposure, major vulnerability | < 1 hour | Unpatched critical CVE, failed access control |
| **P2 - Medium** | Security policy violation, minor vulnerability | < 4 hours | Suspicious login attempts, configuration error |
| **P3 - Low** | Security concern, informational | < 24 hours | Non-sensitive log exposure, outdated documentation |

### 8.3 Incident Response Procedure

#### Phase 1: Detection & Analysis (0-15 minutes)
1. Incident identified via monitoring, alert, or report
2. Severity assessed using criteria above
3. Incident Commander notified
4. Initial assessment documented

#### Phase 2: Containment (15-60 minutes)
1. **Short-term Containment:**
   - Isolate affected systems
   - Block malicious IPs
   - Rotate compromised credentials
   - Enable additional logging

2. **Long-term Containment:**
   - Apply temporary patches
   - Implement compensating controls
   - Prepare production fixes

#### Phase 3: Eradication & Recovery (1-24 hours)
1. Identify root cause
2. Remove malicious artifacts
3. Patch vulnerabilities
4. Restore from clean backups (if needed)
5. Verify system integrity
6. Monitor for re-infection

#### Phase 4: Post-Incident (24-72 hours)
1. **Lessons Learned Meeting:**
   - What happened?
   - What was done?
   - What could be improved?

2. **Documentation:**
   - Incident timeline
   - Root cause analysis
   - Remediation steps taken
   - Prevention measures

3. **Notifications:**
   - Customers (if data breach)
   - Regulators (if required)
   - Public disclosure (if severe)

### 8.4 Incident Response Checklist

**Immediate Actions (P0/P1):**
- [ ] Assess severity and impact
- [ ] Notify Incident Commander
- [ ] Activate incident response team
- [ ] Preserve evidence (logs, memory dumps)
- [ ] Contain the incident
- [ ] Begin investigation
- [ ] Document all actions with timestamps

**Investigation:**
- [ ] Identify attack vector
- [ ] Determine scope of compromise
- [ ] Identify affected systems and data
- [ ] Collect forensic evidence
- [ ] Analyze attacker TTPs (Tactics, Techniques, Procedures)

**Communication:**
- [ ] Internal stakeholders notified
- [ ] Customer notification prepared (if breach)
- [ ] Regulatory notification (if required within 72 hours)
- [ ] PR/communications team briefed
- [ ] Status page updated

**Recovery:**
- [ ] Malware removed
- [ ] Vulnerabilities patched
- [ ] Credentials rotated
- [ ] Systems restored and verified
- [ ] Monitoring enhanced
- [ ] Security controls strengthened

**Post-Incident:**
- [ ] Incident report completed
- [ ] Lessons learned documented
- [ ] Remediation plan created
- [ ] Security policies updated
- [ ] Training conducted (if needed)

### 8.5 Data Breach Notification

**Required if:**
- Personal data of EU citizens accessed (GDPR)
- Protected health information accessed (HIPAA)
- >500 individuals affected (various state laws)

**Notification Timeline:**
- **GDPR:** Within 72 hours to supervisory authority
- **HIPAA:** Within 60 days to affected individuals
- **US State Laws:** Varies (typically "without unreasonable delay")

**Notification Contents:**
- Nature of the breach
- Categories and approximate number of affected individuals
- Likely consequences
- Measures taken or proposed to address breach
- Contact point for more information
- Mitigation advice for affected individuals

---

## 9. Vulnerability Disclosure Policy

### 9.1 Responsible Disclosure

We appreciate the security research community's efforts to help keep our platform secure.

**How to Report:**
1. **Email:** security@199os.com
2. **PGP Key:** Available at https://199os.com/.well-known/pgp-key.txt
3. **Subject Line:** "SECURITY: [Brief Description]"

**What to Include:**
- Description of the vulnerability
- Steps to reproduce
- Proof of concept (if applicable)
- Your name/handle (for recognition)
- Preferred contact method

### 9.2 Safe Harbor

We will not pursue legal action against security researchers who:
- Make a good faith effort to avoid privacy violations
- Do not exploit vulnerabilities beyond what is necessary to demonstrate them
- Give us reasonable time to fix issues before public disclosure
- Do not disrupt production services

### 9.3 Recognition

**Hall of Fame:** https://199os.com/security/hall-of-fame

**Rewards:**
- Public acknowledgment (with permission)
- Swag (t-shirts, stickers)
- Bounties for qualifying vulnerabilities (coming soon)

### 9.4 Response Timeline

- **Acknowledgment:** Within 24 hours
- **Triage:** Within 72 hours
- **Fix Timeline:**
  - Critical: 7 days
  - High: 30 days
  - Medium: 90 days
  - Low: Next release

**Disclosure Coordination:**
We prefer 90-day disclosure timeline to allow proper fixes and testing.

---

## 10. Security Best Practices

### 10.1 For Operators/Administrators

#### Credential Management
✅ **DO:**
- Use `openssl rand` to generate all secrets
- Store `.env` file with `chmod 600` permissions
- Rotate credentials every 90 days
- Use different credentials for dev/staging/prod
- Enable MFA for all administrative accounts

❌ **DON'T:**
- Commit `.env` to version control
- Share credentials via email or Slack
- Reuse credentials across environments
- Use default or weak passwords

#### Server Hardening
✅ **DO:**
- Run server as non-root user (UID 1000)
- Keep all dependencies up to date
- Enable firewall (allow only necessary ports)
- Use TLS for all connections
- Regular security scans (`scripts/security_scan.sh`)

❌ **DON'T:**
- Run as root
- Expose unnecessary ports
- Disable security features for convenience
- Ignore security warnings

#### Monitoring & Logging
✅ **DO:**
- Monitor audit logs daily
- Set up alerts for suspicious activity
- Review access logs weekly
- Maintain log backups
- Use centralized logging (Datadog, Splunk, ELK)

❌ **DON'T:**
- Ignore security alerts
- Delete audit logs
- Log sensitive data
- Disable audit logging

### 10.2 For Developers

#### Secure Coding
✅ **DO:**
- Always validate user inputs
- Use Pydantic models for validation
- Parameterize database queries
- Escape output in templates
- Use security linters (Bandit, Safety)

❌ **DON'T:**
- Trust user input
- Use string concatenation for SQL
- Disable security validators
- Hard-code secrets
- Use `eval()` or `exec()`

#### Testing
✅ **DO:**
- Write security tests
- Test with malicious inputs
- Fuzz test API endpoints
- Run SAST tools (Bandit, Semgrep)
- Scan dependencies (Safety, pip-audit)

❌ **DON'T:**
- Skip security tests
- Assume inputs are safe
- Ignore security warnings
- Use outdated dependencies

#### Code Review
✅ **DO:**
- Review for security issues
- Check for hardcoded secrets
- Verify input validation
- Confirm error handling
- Use automated security checks

❌ **DON'T:**
- Approve without security review
- Ignore linter warnings
- Rush critical changes
- Skip testing

### 10.3 For Customers

#### Data Protection
✅ **DO:**
- Use strong API keys
- Enable MFA if available
- Regularly review access logs
- Limit API key permissions
- Report suspicious activity immediately

❌ **DON'T:**
- Share API keys
- Use the same key across environments
- Ignore security notifications
- Grant excessive permissions

#### Integration Security
✅ **DO:**
- Use secure webhooks (HMAC validation)
- Validate webhook signatures
- Use HTTPS for all callbacks
- Rotate webhook secrets periodically
- Monitor integration logs

❌ **DON'T:**
- Accept unsigned webhooks
- Use HTTP for callbacks
- Ignore integration errors
- Disable signature validation

---

## 11. Security Tools & Scanning

### 11.1 Automated Security Scanning

**Script:** `scripts/security_scan.sh`

**What It Checks:**
1. **Bandit** - Python code security analysis
2. **Safety** - Dependency vulnerability check
3. **Trivy** - Docker image vulnerability scan
4. **Secret Detection** - Exposed secrets in code
5. **Configuration Security** - Security settings validation

**Run Frequency:**
- **Development:** Before every commit (pre-commit hooks)
- **CI/CD:** On every pull request
- **Production:** Weekly scheduled scans

**Usage:**
```bash
# Quick scan (skips Trivy)
./scripts/security_scan.sh --quick

# Full scan with HTML reports
./scripts/security_scan.sh --report

# Strict mode (warnings = errors)
./scripts/security_scan.sh --strict
```

### 11.2 Dependency Management

**Tools:**
- `pip-audit` - Check for known vulnerabilities
- `safety` - Database of insecure packages
- Dependabot - Automated dependency updates

**Policy:**
- **Critical vulnerabilities:** Patch within 7 days
- **High vulnerabilities:** Patch within 30 days
- **Medium vulnerabilities:** Patch within 90 days

**Configuration:**
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

### 11.3 Static Application Security Testing (SAST)

**Tools:**
- **Bandit:** Python security linting
- **Semgrep:** Pattern-based security scanning
- **MyPy:** Type checking (prevents type confusion attacks)

**Integrated Into:**
- Pre-commit hooks
- CI/CD pipeline
- IDE extensions (VS Code, PyCharm)

---

## 12. Incident History & Transparency

### 12.1 Security Incidents

**To Date:** No security incidents reported

**Last Updated:** October 10, 2025

We maintain transparency about security incidents. All significant incidents will be disclosed here with:
- Incident date
- Impact assessment
- Root cause
- Remediation actions
- Preventive measures

### 12.2 Security Updates

| Date | Update | Severity |
|------|--------|----------|
| 2025-10-10 | Initial security policy published | N/A |
| 2025-10-10 | Comprehensive input validation implemented (873 lines) | Preventive |
| 2025-10-10 | AES-256 credential encryption enabled | Enhancement |
| 2025-10-10 | GDPR compliance module added | Compliance |

---

## 13. Cryptographic Details

### 13.1 Algorithms Used

| Purpose | Algorithm | Key Size | Notes |
|---------|-----------|----------|-------|
| Credential Encryption | AES-256-CBC | 256 bits | FIPS 140-2 compliant |
| Key Derivation | PBKDF2-HMAC-SHA256 | N/A | 600,000 iterations (OWASP 2023) |
| Password Hashing | bcrypt | N/A | Cost factor 12 |
| JWT Signing | HS256 | 256 bits | Minimum secret length 256 bits |
| Webhook Signing | HMAC-SHA256 | 256 bits | RFC 2104 compliant |
| Log Integrity | SHA-256 | 256 bits | Tamper detection |

### 13.2 Key Management

**Master Encryption Key:**
- Generated via `openssl rand -hex 32`
- Stored in environment variable (`ENCRYPTION_KEY`)
- **Never** stored in code or version control
- Rotated annually or after suspected compromise

**Key Rotation Procedure:**
1. Generate new encryption key
2. Decrypt all secrets with old key
3. Re-encrypt with new key
4. Update `ENCRYPTION_KEY` environment variable
5. Restart server
6. Verify all integrations working
7. Securely destroy old key

---

## 14. Contact Information

### 14.1 Security Team

**Security Contact:** security@199os.com
**PGP Fingerprint:** [To be added]
**Response Time:** < 24 hours for initial acknowledgment

### 14.2 Compliance & Privacy

**Privacy Officer:** privacy@199os.com
**DPO (Data Protection Officer):** dpo@199os.com
**Compliance Contact:** compliance@199os.com

### 14.3 Emergency Contacts

**Security Incident (24/7):** security-emergency@199os.com
**Data Breach Hotline:** +1-XXX-XXX-XXXX

---

## 15. Updates & Versioning

**Current Version:** 1.0.0
**Last Reviewed:** October 10, 2025
**Next Review:** January 10, 2026

**Change Log:**
- **v1.0.0** (2025-10-10) - Initial security policy published

This security policy is reviewed quarterly and updated as needed to reflect current security practices and compliance requirements.

---

**For more information:**
- Technical Documentation: `docs/architecture/`
- Compliance Documentation: `docs/compliance/`
- Operational Security: `docs/operations/RUNBOOK.md`
- Security Scanning: `scripts/security_scan.sh`

---

© 2025 199OS. All rights reserved.
