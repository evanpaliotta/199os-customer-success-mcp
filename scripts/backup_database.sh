#!/bin/bash
# Customer Success MCP - Automated Database Backup Script
#
# Features:
# - Full PostgreSQL database backup using pg_dump
# - Automatic compression (gzip)
# - S3 upload with versioning
# - Backup verification
# - Retention policy (keeps last 30 daily backups)
# - Slack/email notifications
# - Detailed logging
#
# Usage:
#   ./backup_database.sh [--full|--schema-only]
#
# Environment variables required:
#   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
#   AWS_S3_BUCKET, AWS_REGION
#   SLACK_WEBHOOK_URL (optional)
#   BACKUP_NOTIFICATION_EMAIL (optional)

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Backup configuration
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
BACKUP_TYPE="${1:-full}"  # full or schema-only
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILENAME="cs_mcp_backup_${TIMESTAMP}.sql.gz"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILENAME"
LOG_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.log"

# Retention policy (days)
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# S3 configuration
S3_BUCKET="${AWS_S3_BUCKET:-}"
S3_PREFIX="${AWS_S3_PREFIX:-backups/database}"
S3_PATH="s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_FILENAME}"

# Database configuration (with defaults)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-cs_mcp_production}"
DB_USER="${DB_USER:-postgres}"

# Notification configuration
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
NOTIFICATION_EMAIL="${BACKUP_NOTIFICATION_EMAIL:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# Functions
# ============================================================================

log() {
    local level="$1"
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "$@"
    echo -e "${GREEN}✓${NC} $@"
}

log_warn() {
    log "WARN" "$@"
    echo -e "${YELLOW}⚠${NC} $@"
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}✗${NC} $@"
}

send_slack_notification() {
    local status="$1"
    local message="$2"

    if [ -z "$SLACK_WEBHOOK_URL" ]; then
        return 0
    fi

    local color="good"
    local icon=":white_check_mark:"

    if [ "$status" = "failure" ]; then
        color="danger"
        icon=":x:"
    fi

    local payload=$(cat <<EOF
{
    "attachments": [{
        "color": "$color",
        "title": "$icon Database Backup $status",
        "text": "$message",
        "fields": [
            {
                "title": "Environment",
                "value": "${ENVIRONMENT:-production}",
                "short": true
            },
            {
                "title": "Database",
                "value": "$DB_NAME",
                "short": true
            },
            {
                "title": "Timestamp",
                "value": "$(date '+%Y-%m-%d %H:%M:%S %Z')",
                "short": false
            }
        ]
    }]
}
EOF
)

    curl -X POST -H 'Content-type: application/json' \
        --data "$payload" \
        "$SLACK_WEBHOOK_URL" \
        2>/dev/null || log_warn "Failed to send Slack notification"
}

send_email_notification() {
    local status="$1"
    local message="$2"

    if [ -z "$NOTIFICATION_EMAIL" ]; then
        return 0
    fi

    local subject="Database Backup $status - $DB_NAME - $(date '+%Y-%m-%d')"

    echo "$message" | mail -s "$subject" "$NOTIFICATION_EMAIL" || \
        log_warn "Failed to send email notification"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check required commands
    local required_commands=("pg_dump" "gzip" "aws")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "Required command not found: $cmd"
            return 1
        fi
    done

    # Check database credentials
    if [ -z "$DB_PASSWORD" ]; then
        log_error "DB_PASSWORD environment variable is not set"
        return 1
    fi

    # Check AWS credentials
    if [ -z "$S3_BUCKET" ]; then
        log_warn "AWS_S3_BUCKET not set - S3 upload will be skipped"
    fi

    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"

    # Test database connection
    log_info "Testing database connection..."
    if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
        log_error "Cannot connect to database"
        return 1
    fi

    log_info "Prerequisites check passed"
    return 0
}

create_backup() {
    log_info "Starting database backup ($BACKUP_TYPE)..."
    log_info "Backup file: $BACKUP_FILENAME"

    local pg_dump_args=(
        -h "$DB_HOST"
        -p "$DB_PORT"
        -U "$DB_USER"
        -d "$DB_NAME"
        --verbose
        --format=plain
        --no-owner
        --no-acl
    )

    if [ "$BACKUP_TYPE" = "schema-only" ]; then
        pg_dump_args+=(--schema-only)
        log_info "Creating schema-only backup"
    else
        log_info "Creating full backup (schema + data)"
    fi

    # Create backup with compression
    local start_time=$(date +%s)

    if PGPASSWORD="$DB_PASSWORD" pg_dump "${pg_dump_args[@]}" 2>>"$LOG_FILE" | gzip > "$BACKUP_PATH"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local size=$(du -h "$BACKUP_PATH" | cut -f1)

        log_info "Backup created successfully"
        log_info "Duration: ${duration}s"
        log_info "Size: $size"

        return 0
    else
        log_error "Backup failed"
        return 1
    fi
}

verify_backup() {
    log_info "Verifying backup integrity..."

    # Check if file exists and is not empty
    if [ ! -s "$BACKUP_PATH" ]; then
        log_error "Backup file is empty or does not exist"
        return 1
    fi

    # Verify gzip integrity
    if ! gzip -t "$BACKUP_PATH" 2>/dev/null; then
        log_error "Backup file is corrupted (gzip test failed)"
        return 1
    fi

    # Check if backup contains SQL statements
    if ! gunzip -c "$BACKUP_PATH" | head -n 20 | grep -q "PostgreSQL database dump"; then
        log_error "Backup file does not appear to be a valid PostgreSQL dump"
        return 1
    fi

    log_info "Backup verification passed"
    return 0
}

upload_to_s3() {
    if [ -z "$S3_BUCKET" ]; then
        log_warn "S3 upload skipped (no bucket configured)"
        return 0
    fi

    log_info "Uploading backup to S3..."
    log_info "Destination: $S3_PATH"

    # Upload with server-side encryption and metadata
    if aws s3 cp "$BACKUP_PATH" "$S3_PATH" \
        --storage-class STANDARD_IA \
        --server-side-encryption AES256 \
        --metadata "backup-type=$BACKUP_TYPE,database=$DB_NAME,timestamp=$TIMESTAMP" \
        --region "${AWS_REGION:-us-east-1}" \
        2>>"$LOG_FILE"; then
        log_info "S3 upload successful"

        # Upload log file as well
        aws s3 cp "$LOG_FILE" "s3://${S3_BUCKET}/${S3_PREFIX}/logs/backup_${TIMESTAMP}.log" \
            --region "${AWS_REGION:-us-east-1}" \
            2>/dev/null || log_warn "Failed to upload log file to S3"

        return 0
    else
        log_error "S3 upload failed"
        return 1
    fi
}

cleanup_old_backups() {
    log_info "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."

    # Clean up local backups
    local deleted_count=0
    while IFS= read -r old_backup; do
        rm -f "$old_backup"
        ((deleted_count++))
    done < <(find "$BACKUP_DIR" -name "cs_mcp_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS})

    if [ $deleted_count -gt 0 ]; then
        log_info "Deleted $deleted_count old local backup(s)"
    fi

    # Clean up old log files
    find "$BACKUP_DIR" -name "backup_*.log" -type f -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true

    # Clean up S3 backups (if configured)
    if [ -n "$S3_BUCKET" ]; then
        log_info "Cleaning up old S3 backups..."

        # List and delete old backups from S3
        local cutoff_date=$(date -d "${RETENTION_DAYS} days ago" +%Y%m%d 2>/dev/null || date -v-${RETENTION_DAYS}d +%Y%m%d)

        aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" --region "${AWS_REGION:-us-east-1}" 2>/dev/null | \
        while read -r line; do
            local filename=$(echo "$line" | awk '{print $4}')
            if [[ $filename =~ cs_mcp_backup_([0-9]{8})_ ]]; then
                local backup_date="${BASH_REMATCH[1]}"
                if [ "$backup_date" -lt "$cutoff_date" ]; then
                    aws s3 rm "s3://${S3_BUCKET}/${S3_PREFIX}/$filename" \
                        --region "${AWS_REGION:-us-east-1}" 2>/dev/null || true
                    log_info "Deleted old S3 backup: $filename"
                fi
            fi
        done
    fi

    log_info "Cleanup completed"
}

# ============================================================================
# Main Script
# ============================================================================

main() {
    log_info "========================================"
    log_info "Customer Success MCP Database Backup"
    log_info "========================================"
    log_info "Started at: $(date '+%Y-%m-%d %H:%M:%S')"

    local exit_code=0
    local status_message=""

    # Check prerequisites
    if ! check_prerequisites; then
        status_message="Prerequisite check failed"
        exit_code=1
    # Create backup
    elif ! create_backup; then
        status_message="Backup creation failed"
        exit_code=1
    # Verify backup
    elif ! verify_backup; then
        status_message="Backup verification failed"
        exit_code=1
    # Upload to S3
    elif ! upload_to_s3; then
        status_message="S3 upload failed (backup exists locally)"
        log_warn "$status_message"
        # Don't fail the entire script if S3 upload fails
    fi

    # Clean up old backups (regardless of current backup status)
    cleanup_old_backups

    # Set success message if no errors
    if [ $exit_code -eq 0 ]; then
        status_message="Backup completed successfully: $BACKUP_FILENAME ($(du -h "$BACKUP_PATH" | cut -f1))"
        log_info "========================================"
        log_info "$status_message"
        log_info "========================================"

        send_slack_notification "success" "$status_message"
        send_email_notification "Success" "$status_message"
    else
        log_error "========================================"
        log_error "$status_message"
        log_error "========================================"

        send_slack_notification "failure" "$status_message"
        send_email_notification "Failure" "$status_message"
    fi

    log_info "Completed at: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "Log file: $LOG_FILE"

    exit $exit_code
}

# Run main function
main "$@"
