#!/bin/bash
# Customer Success MCP - Database Restore Script
#
# Features:
# - Restore from local or S3 backup
# - Pre-restore database backup (safety)
# - Connection termination for active sessions
# - Verification after restore
# - Rollback capability
#
# Usage:
#   ./restore_database.sh <backup_file>
#   ./restore_database.sh --from-s3 <s3_key>
#   ./restore_database.sh --latest
#
# WARNING: This will DROP and recreate the target database!
#          All existing data will be lost unless backed up.

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-cs_mcp_production}"
DB_USER="${DB_USER:-postgres}"

# S3 configuration
S3_BUCKET="${AWS_S3_BUCKET:-}"
S3_PREFIX="${AWS_S3_PREFIX:-backups/database}"

# Backup directory
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$BACKUP_DIR/restore_${TIMESTAMP}.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

usage() {
    cat << EOF
Usage: $0 [OPTIONS] <backup_file>

Restore Customer Success MCP database from backup.

OPTIONS:
    --from-s3 <key>     Restore from S3 backup (specify S3 key)
    --latest            Restore from the latest local backup
    --no-safety-backup  Skip pre-restore safety backup
    --force             Skip confirmation prompt
    -h, --help          Show this help message

EXAMPLES:
    # Restore from local file
    $0 backups/cs_mcp_backup_20240101_120000.sql.gz

    # Restore from S3
    $0 --from-s3 cs_mcp_backup_20240101_120000.sql.gz

    # Restore latest backup
    $0 --latest

ENVIRONMENT VARIABLES:
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    AWS_S3_BUCKET, AWS_REGION (for S3 operations)

WARNING: This will DROP and recreate the database, losing all existing data!
EOF
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check required commands
    local required_commands=("psql" "gunzip" "pg_restore")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "Required command not found: $cmd"
            return 1
        fi
    done

    # Check database password
    if [ -z "$DB_PASSWORD" ]; then
        log_error "DB_PASSWORD environment variable is not set"
        return 1
    fi

    # Test database connection
    log_info "Testing database connection..."
    if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "SELECT 1" > /dev/null 2>&1; then
        log_error "Cannot connect to PostgreSQL server"
        return 1
    fi

    log_info "Prerequisites check passed"
    return 0
}

get_latest_backup() {
    local latest=$(find "$BACKUP_DIR" -name "cs_mcp_backup_*.sql.gz" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)

    if [ -z "$latest" ]; then
        log_error "No backup files found in $BACKUP_DIR"
        return 1
    fi

    echo "$latest"
}

download_from_s3() {
    local s3_key="$1"
    local local_path="$BACKUP_DIR/$s3_key"

    if [ -z "$S3_BUCKET" ]; then
        log_error "AWS_S3_BUCKET not configured"
        return 1
    fi

    log_info "Downloading backup from S3..."
    log_info "Source: s3://${S3_BUCKET}/${S3_PREFIX}/${s3_key}"
    log_info "Destination: $local_path"

    mkdir -p "$BACKUP_DIR"

    if aws s3 cp "s3://${S3_BUCKET}/${S3_PREFIX}/${s3_key}" "$local_path" \
        --region "${AWS_REGION:-us-east-1}" \
        2>>"$LOG_FILE"; then
        log_info "Download completed"
        echo "$local_path"
        return 0
    else
        log_error "Failed to download backup from S3"
        return 1
    fi
}

verify_backup_file() {
    local backup_file="$1"

    log_info "Verifying backup file..."

    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi

    if [ ! -s "$backup_file" ]; then
        log_error "Backup file is empty: $backup_file"
        return 1
    fi

    # Verify gzip integrity
    if ! gzip -t "$backup_file" 2>/dev/null; then
        log_error "Backup file is corrupted (gzip test failed)"
        return 1
    fi

    # Check if it's a PostgreSQL dump
    if ! gunzip -c "$backup_file" | head -n 20 | grep -q "PostgreSQL database dump"; then
        log_error "File does not appear to be a valid PostgreSQL dump"
        return 1
    fi

    local size=$(du -h "$backup_file" | cut -f1)
    log_info "Backup file verified successfully ($size)"
    return 0
}

create_safety_backup() {
    log_info "Creating safety backup of current database..."

    local safety_backup="$BACKUP_DIR/pre_restore_safety_${TIMESTAMP}.sql.gz"

    if PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --format=plain \
        --no-owner \
        --no-acl \
        2>>"$LOG_FILE" | gzip > "$safety_backup"; then
        log_info "Safety backup created: $(basename "$safety_backup")"
        echo "$safety_backup"
        return 0
    else
        log_error "Failed to create safety backup"
        return 1
    fi
}

terminate_connections() {
    log_info "Terminating active database connections..."

    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<EOF 2>>"$LOG_FILE"
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$DB_NAME'
  AND pid <> pg_backend_pid();
EOF

    log_info "Active connections terminated"
}

drop_and_recreate_database() {
    log_info "Dropping and recreating database..."

    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<EOF 2>>"$LOG_FILE"
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME;
EOF

    if [ $? -eq 0 ]; then
        log_info "Database recreated successfully"
        return 0
    else
        log_error "Failed to recreate database"
        return 1
    fi
}

restore_from_backup() {
    local backup_file="$1"

    log_info "Restoring database from backup..."
    log_info "Source: $(basename "$backup_file")"

    local start_time=$(date +%s)

    if gunzip -c "$backup_file" | \
        PGPASSWORD="$DB_PASSWORD" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            2>>"$LOG_FILE"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        log_info "Restore completed successfully"
        log_info "Duration: ${duration}s"
        return 0
    else
        log_error "Restore failed"
        return 1
    fi
}

verify_restored_database() {
    log_info "Verifying restored database..."

    # Check if database exists and is accessible
    if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
        log_error "Cannot connect to restored database"
        return 1
    fi

    # Check if key tables exist
    local table_count=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'" 2>/dev/null)

    if [ -z "$table_count" ] || [ "$table_count" -eq 0 ]; then
        log_error "No tables found in restored database"
        return 1
    fi

    log_info "Verification passed: Found $table_count tables"
    return 0
}

confirm_restore() {
    local backup_file="$1"

    echo
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                        WARNING                                 ║${NC}"
    echo -e "${RED}║                                                                ║${NC}"
    echo -e "${RED}║  This will DROP and RECREATE the database, losing all data!   ║${NC}"
    echo -e "${RED}║                                                                ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo -e "${BLUE}Database:${NC} $DB_NAME"
    echo -e "${BLUE}Host:${NC} $DB_HOST:$DB_PORT"
    echo -e "${BLUE}Backup file:${NC} $(basename "$backup_file")"
    echo -e "${BLUE}Backup size:${NC} $(du -h "$backup_file" | cut -f1)"
    echo

    read -p "Are you sure you want to proceed? Type 'yes' to continue: " confirmation

    if [ "$confirmation" != "yes" ]; then
        log_info "Restore cancelled by user"
        return 1
    fi

    return 0
}

# ============================================================================
# Main Script
# ============================================================================

main() {
    local backup_file=""
    local from_s3=false
    local use_latest=false
    local skip_safety_backup=false
    local force=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --from-s3)
                from_s3=true
                shift
                backup_file="$1"
                shift
                ;;
            --latest)
                use_latest=true
                shift
                ;;
            --no-safety-backup)
                skip_safety_backup=true
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                backup_file="$1"
                shift
                ;;
        esac
    done

    # Initialize log
    mkdir -p "$BACKUP_DIR"

    log_info "========================================"
    log_info "Customer Success MCP Database Restore"
    log_info "========================================"
    log_info "Started at: $(date '+%Y-%m-%d %H:%M:%S')"

    # Check prerequisites
    if ! check_prerequisites; then
        exit 1
    fi

    # Determine backup file
    if [ "$use_latest" = true ]; then
        log_info "Using latest backup..."
        backup_file=$(get_latest_backup) || exit 1
    elif [ "$from_s3" = true ]; then
        backup_file=$(download_from_s3 "$backup_file") || exit 1
    elif [ -z "$backup_file" ]; then
        log_error "No backup file specified"
        usage
        exit 1
    fi

    # Verify backup file
    if ! verify_backup_file "$backup_file"; then
        exit 1
    fi

    # Confirm restore (unless --force is used)
    if [ "$force" = false ]; then
        if ! confirm_restore "$backup_file"; then
            exit 1
        fi
    fi

    # Create safety backup
    local safety_backup=""
    if [ "$skip_safety_backup" = false ]; then
        safety_backup=$(create_safety_backup) || {
            log_error "Failed to create safety backup - aborting"
            exit 1
        }
    fi

    # Perform restore
    local restore_failed=false

    if ! terminate_connections; then
        restore_failed=true
    elif ! drop_and_recreate_database; then
        restore_failed=true
    elif ! restore_from_backup "$backup_file"; then
        restore_failed=true
    elif ! verify_restored_database; then
        restore_failed=true
    fi

    # Handle result
    if [ "$restore_failed" = true ]; then
        log_error "========================================"
        log_error "Restore failed!"
        log_error "========================================"

        if [ -n "$safety_backup" ]; then
            log_warn "Safety backup available at: $safety_backup"
            log_warn "To rollback, run: $0 $safety_backup"
        fi

        exit 1
    else
        log_info "========================================"
        log_info "Restore completed successfully!"
        log_info "========================================"

        if [ -n "$safety_backup" ]; then
            log_info "Safety backup preserved at: $safety_backup"
        fi

        log_info "Completed at: $(date '+%Y-%m-%d %H:%M:%S')"
        log_info "Log file: $LOG_FILE"
        exit 0
    fi
}

# Run main function
main "$@"
