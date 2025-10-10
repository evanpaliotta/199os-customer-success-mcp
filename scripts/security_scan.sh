#!/bin/bash

##############################################################################
# Security Scan Script for Customer Success MCP
#
# This script runs comprehensive security checks:
# 1. Bandit - Python code security analysis
# 2. Safety - Python dependency vulnerability check
# 3. Trivy - Docker image vulnerability scan
# 4. Secret detection - Check for exposed secrets
# 5. Configuration security - Validate security settings
#
# Usage:
#   chmod +x scripts/security_scan.sh
#   ./scripts/security_scan.sh
#
# Options:
#   --strict: Fail on any warnings (use in CI/CD)
#   --report: Generate HTML reports
#   --quick: Skip Trivy scan (faster)
#
# Exit Codes:
#   0 - All checks passed
#   1 - Critical vulnerabilities found
#   2 - High severity issues found
#   3 - Medium severity issues found (with --strict)
##############################################################################

set -e  # Exit on error (except where handled)

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
STRICT_MODE=false
GENERATE_REPORTS=false
SKIP_TRIVY=false

for arg in "$@"; do
    case $arg in
        --strict)
            STRICT_MODE=true
            shift
            ;;
        --report)
            GENERATE_REPORTS=true
            shift
            ;;
        --quick)
            SKIP_TRIVY=true
            shift
            ;;
    esac
done

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORTS_DIR="$PROJECT_ROOT/security_reports"

# Create reports directory
mkdir -p "$REPORTS_DIR"

# Track results
CRITICAL_COUNT=0
HIGH_COUNT=0
MEDIUM_COUNT=0
LOW_COUNT=0

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed. Installing..."
        pip install $1
    fi
}

##############################################################################
# Main Script
##############################################################################

print_header "CUSTOMER SUCCESS MCP - SECURITY SCAN"
echo "Starting security scan at: $(date)"
echo "Project root: $PROJECT_ROOT"
echo "Reports directory: $REPORTS_DIR"
echo ""

cd "$PROJECT_ROOT"

##############################################################################
# 1. Bandit - Python Code Security Analysis
##############################################################################

print_header "1. Bandit - Python Code Security Analysis"

check_command bandit

echo "Running Bandit security scan..."
echo "Target: src/"
echo ""

if [ "$GENERATE_REPORTS" = true ]; then
    BANDIT_OUTPUT="--format json --output $REPORTS_DIR/bandit_report.json"
else
    BANDIT_OUTPUT=""
fi

# Run Bandit
if bandit -r src/ -f screen $BANDIT_OUTPUT -ll -i; then
    print_success "Bandit: No security issues found"
else
    BANDIT_EXIT=$?
    print_warning "Bandit: Security issues detected (see output above)"

    # Parse severity (simplified - in production use JSON parsing)
    # Bandit exit codes: 0=clean, 1=issues found
    if [ $BANDIT_EXIT -eq 1 ]; then
        HIGH_COUNT=$((HIGH_COUNT + 1))
    fi
fi

# Generate HTML report if requested
if [ "$GENERATE_REPORTS" = true ] && [ -f "$REPORTS_DIR/bandit_report.json" ]; then
    bandit -r src/ -f html -o "$REPORTS_DIR/bandit_report.html" -ll -i 2>/dev/null || true
    print_info "Bandit HTML report: $REPORTS_DIR/bandit_report.html"
fi

echo ""

##############################################################################
# 2. Safety - Dependency Vulnerability Check
##############################################################################

print_header "2. Safety - Python Dependency Vulnerability Check"

check_command safety

echo "Running Safety vulnerability check..."
echo "Target: requirements.txt"
echo ""

# Run Safety
if [ "$GENERATE_REPORTS" = true ]; then
    SAFETY_OUTPUT="--json --output $REPORTS_DIR/safety_report.json"
else
    SAFETY_OUTPUT=""
fi

if safety check --file requirements.txt $SAFETY_OUTPUT; then
    print_success "Safety: No known vulnerabilities in dependencies"
else
    SAFETY_EXIT=$?
    print_warning "Safety: Vulnerabilities detected in dependencies"

    if [ $SAFETY_EXIT -eq 64 ]; then
        CRITICAL_COUNT=$((CRITICAL_COUNT + 1))
        print_error "Critical vulnerabilities found!"
    else
        HIGH_COUNT=$((HIGH_COUNT + 1))
    fi
fi

echo ""

##############################################################################
# 3. Trivy - Docker Image Vulnerability Scan
##############################################################################

if [ "$SKIP_TRIVY" = false ]; then
    print_header "3. Trivy - Docker Image Vulnerability Scan"

    if ! command -v trivy &> /dev/null; then
        print_warning "Trivy is not installed. Skipping Docker image scan."
        print_info "Install Trivy: https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
    else
        echo "Checking for Docker images..."

        # Find latest Docker image
        if docker images cs-mcp --format "{{.Repository}}:{{.Tag}}" | head -1 | grep -q "cs-mcp"; then
            IMAGE=$(docker images cs-mcp --format "{{.Repository}}:{{.Tag}}" | head -1)
            echo "Scanning image: $IMAGE"
            echo ""

            # Run Trivy
            if [ "$GENERATE_REPORTS" = true ]; then
                trivy image --severity HIGH,CRITICAL --format json --output "$REPORTS_DIR/trivy_report.json" "$IMAGE"
                trivy image --severity HIGH,CRITICAL --format table "$IMAGE"
            else
                trivy image --severity HIGH,CRITICAL "$IMAGE"
            fi

            TRIVY_EXIT=$?

            if [ $TRIVY_EXIT -eq 0 ]; then
                print_success "Trivy: No critical vulnerabilities in Docker image"
            else
                print_warning "Trivy: Vulnerabilities detected in Docker image"
                HIGH_COUNT=$((HIGH_COUNT + 1))
            fi
        else
            print_warning "No cs-mcp Docker image found. Skipping scan."
            print_info "Build image first: docker build -t cs-mcp:latest ."
        fi
    fi

    echo ""
else
    print_info "Skipping Trivy scan (--quick mode)"
fi

##############################################################################
# 4. Secret Detection
##############################################################################

print_header "4. Secret Detection"

echo "Checking for exposed secrets..."
echo ""

# Check for common secret patterns in code
SECRETS_FOUND=0

# Check for API keys
if grep -rn "api_key\s*=\s*['\"][^'\"]*['\"]" src/ 2>/dev/null | grep -v "PLACEHOLDER" | grep -v "YOUR_" | grep -v "test_" | grep -q .; then
    print_warning "Potential API keys found in source code:"
    grep -rn "api_key\s*=\s*['\"][^'\"]*['\"]" src/ 2>/dev/null | grep -v "PLACEHOLDER" | grep -v "YOUR_" | grep -v "test_" || true
    SECRETS_FOUND=$((SECRETS_FOUND + 1))
    MEDIUM_COUNT=$((MEDIUM_COUNT + 1))
fi

# Check for passwords
if grep -rn "password\s*=\s*['\"][^'\"]*['\"]" src/ 2>/dev/null | grep -v "PLACEHOLDER" | grep -v "YOUR_" | grep -v "test_" | grep -q .; then
    print_warning "Potential passwords found in source code:"
    grep -rn "password\s*=\s*['\"][^'\"]*['\"]" src/ 2>/dev/null | grep -v "PLACEHOLDER" | grep -v "YOUR_" | grep -v "test_" || true
    SECRETS_FOUND=$((SECRETS_FOUND + 1))
    HIGH_COUNT=$((HIGH_COUNT + 1))
fi

# Check for AWS keys
if grep -rn "AKIA[0-9A-Z]{16}" src/ 2>/dev/null | grep -q .; then
    print_error "AWS Access Key ID found in source code!"
    grep -rn "AKIA[0-9A-Z]{16}" src/ 2>/dev/null || true
    SECRETS_FOUND=$((SECRETS_FOUND + 1))
    CRITICAL_COUNT=$((CRITICAL_COUNT + 1))
fi

# Check for private keys
if grep -rn "BEGIN.*PRIVATE KEY" src/ 2>/dev/null | grep -q .; then
    print_error "Private key found in source code!"
    grep -rn "BEGIN.*PRIVATE KEY" src/ 2>/dev/null || true
    SECRETS_FOUND=$((SECRETS_FOUND + 1))
    CRITICAL_COUNT=$((CRITICAL_COUNT + 1))
fi

# Check .env file is not committed
if [ -f ".env" ]; then
    if git ls-files --error-unmatch .env 2>/dev/null; then
        print_error ".env file is tracked by Git! This should be in .gitignore"
        SECRETS_FOUND=$((SECRETS_FOUND + 1))
        HIGH_COUNT=$((HIGH_COUNT + 1))
    else
        print_success ".env file is not tracked by Git"
    fi
else
    print_info "No .env file found (expected in development)"
fi

if [ $SECRETS_FOUND -eq 0 ]; then
    print_success "No exposed secrets detected"
fi

echo ""

##############################################################################
# 5. Configuration Security
##############################################################################

print_header "5. Configuration Security Check"

echo "Checking security configuration..."
echo ""

CONFIG_ISSUES=0

# Check Dockerfile security
if [ -f "Dockerfile" ]; then
    print_info "Checking Dockerfile security..."

    # Check for non-root user
    if grep -q "USER.*root\|^USER\s*$" Dockerfile; then
        print_error "Dockerfile runs as root user (security risk)"
        CONFIG_ISSUES=$((CONFIG_ISSUES + 1))
        HIGH_COUNT=$((HIGH_COUNT + 1))
    elif grep -q "USER\s\+[a-z]" Dockerfile; then
        print_success "Dockerfile uses non-root user"
    else
        print_warning "Cannot determine Dockerfile user"
    fi

    # Check for COPY with proper ownership
    if grep -q "COPY --chown=" Dockerfile; then
        print_success "Dockerfile uses --chown with COPY"
    else
        print_warning "Dockerfile COPY commands may not set ownership"
    fi

    # Check for health check
    if grep -q "HEALTHCHECK" Dockerfile; then
        print_success "Dockerfile includes HEALTHCHECK"
    else
        print_warning "Dockerfile missing HEALTHCHECK"
        MEDIUM_COUNT=$((MEDIUM_COUNT + 1))
    fi
fi

# Check .env.example for secure defaults
if [ -f ".env.example" ]; then
    print_info "Checking .env.example for insecure defaults..."

    if grep -q "password=\|secret=\|key=" .env.example | grep -v "YOUR_\|CHANGE_THIS\|PLACEHOLDER" | grep -q .; then
        print_warning ".env.example may contain real secrets (should use placeholders)"
        CONFIG_ISSUES=$((CONFIG_ISSUES + 1))
        MEDIUM_COUNT=$((MEDIUM_COUNT + 1))
    else
        print_success ".env.example uses placeholders for secrets"
    fi
fi

# Check for security headers in code
if grep -rq "X-Frame-Options\|X-Content-Type-Options\|X-XSS-Protection" src/; then
    print_success "Security headers configured in code"
else
    print_warning "Security headers may not be configured"
    LOW_COUNT=$((LOW_COUNT + 1))
fi

# Check for input validation
if grep -rq "validate_client_id\|validate_email\|SQL injection" src/; then
    print_success "Input validation found in code"
else
    print_warning "Input validation may be missing"
    HIGH_COUNT=$((HIGH_COUNT + 1))
fi

if [ $CONFIG_ISSUES -eq 0 ]; then
    print_success "Configuration security checks passed"
fi

echo ""

##############################################################################
# 6. Additional Security Checks
##############################################################################

print_header "6. Additional Security Checks"

echo "Running additional security checks..."
echo ""

# Check for debug mode in production
if grep -rq "DEBUG\s*=\s*True" src/ 2>/dev/null; then
    print_warning "DEBUG mode enabled in source code (should be False for production)"
    MEDIUM_COUNT=$((MEDIUM_COUNT + 1))
fi

# Check for SQL concatenation (potential SQL injection)
if grep -rq "execute.*[\"'].*%s\|execute.*format" src/ 2>/dev/null; then
    print_warning "Potential SQL injection risk: string formatting in queries detected"
    print_info "Use parameterized queries instead"
    HIGH_COUNT=$((HIGH_COUNT + 1))
fi

# Check for eval() or exec() (dangerous)
if grep -rq "eval\|exec" src/ 2>/dev/null; then
    print_error "Dangerous functions (eval/exec) found in code"
    CRITICAL_COUNT=$((CRITICAL_COUNT + 1))
else
    print_success "No dangerous functions (eval/exec) found"
fi

# Check for pickle (potential security risk)
if grep -rq "import pickle\|pickle.load" src/ 2>/dev/null; then
    print_warning "Pickle usage detected (potential security risk with untrusted data)"
    MEDIUM_COUNT=$((MEDIUM_COUNT + 1))
fi

echo ""

##############################################################################
# Summary Report
##############################################################################

print_header "SECURITY SCAN SUMMARY"

echo "Scan completed at: $(date)"
echo ""

echo "📊 FINDINGS:"
printf "  Critical: %d\n" $CRITICAL_COUNT
printf "  High: %d\n" $HIGH_COUNT
printf "  Medium: %d\n" $MEDIUM_COUNT
printf "  Low: %d\n" $LOW_COUNT
echo ""

# Determine overall status
if [ $CRITICAL_COUNT -gt 0 ]; then
    print_error "SECURITY SCAN FAILED: Critical vulnerabilities found"
    EXIT_CODE=1
elif [ $HIGH_COUNT -gt 0 ]; then
    print_warning "SECURITY SCAN WARNING: High severity issues found"
    EXIT_CODE=2
elif [ $MEDIUM_COUNT -gt 0 ] && [ "$STRICT_MODE" = true ]; then
    print_warning "SECURITY SCAN WARNING: Medium severity issues found (strict mode)"
    EXIT_CODE=3
else
    print_success "SECURITY SCAN PASSED: No critical or high severity issues found"
    EXIT_CODE=0
fi

echo ""
echo "Exit code: $EXIT_CODE"

# Print recommendations
if [ $CRITICAL_COUNT -gt 0 ] || [ $HIGH_COUNT -gt 0 ]; then
    echo ""
    print_info "RECOMMENDED ACTIONS:"
    echo "  1. Review all findings above"
    echo "  2. Fix critical and high severity issues immediately"
    echo "  3. Update vulnerable dependencies"
    echo "  4. Remove exposed secrets and rotate credentials"
    echo "  5. Re-run security scan after fixes"
    echo ""
fi

# Print report locations
if [ "$GENERATE_REPORTS" = true ]; then
    echo ""
    print_info "REPORTS GENERATED:"
    echo "  Bandit: $REPORTS_DIR/bandit_report.html"
    echo "  Bandit (JSON): $REPORTS_DIR/bandit_report.json"
    echo "  Safety: $REPORTS_DIR/safety_report.json"
    echo "  Trivy: $REPORTS_DIR/trivy_report.json"
    echo ""
fi

# Exit with appropriate code
exit $EXIT_CODE
