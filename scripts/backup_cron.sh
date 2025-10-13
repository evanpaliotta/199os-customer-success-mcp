#!/bin/bash
# Cron wrapper script for database backups
# This script sources environment variables and runs the backup
#
# Add to crontab:
#   0 2 * * * /path/to/scripts/backup_cron.sh >> /var/log/cs_mcp_backup_cron.log 2>&1

# Load environment variables from .env file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -f "$PROJECT_ROOT/.env.production" ]; then
    # Export all variables from .env.production
    set -a
    source "$PROJECT_ROOT/.env.production"
    set +a
fi

# Run backup script
exec "$SCRIPT_DIR/backup_database.sh" "$@"
