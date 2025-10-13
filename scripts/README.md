# Database Backup and Restore Scripts

Automated backup and restore scripts for the Customer Success MCP PostgreSQL database.

## Quick Start

### 1. Configure Environment Variables

Create or update your `.env.production` file:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cs_mcp_production
DB_USER=postgres
DB_PASSWORD=your_secure_password

# AWS S3 Configuration (for offsite backups)
AWS_S3_BUCKET=your-backup-bucket
AWS_S3_PREFIX=backups/database
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Backup Configuration
BACKUP_RETENTION_DAYS=30
BACKUP_DIR=/opt/cs_mcp/backups

# Notification Configuration (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
BACKUP_NOTIFICATION_EMAIL=ops-team@yourcompany.com
```

### 2. Make Scripts Executable

```bash
chmod +x scripts/backup_database.sh
chmod +x scripts/restore_database.sh
chmod +x scripts/backup_cron.sh
```

### 3. Test Backup

```bash
# Create a full backup
./scripts/backup_database.sh

# Create a schema-only backup
./scripts/backup_database.sh --schema-only
```

### 4. Test Restore (in non-production environment!)

```bash
# Restore from latest backup
./scripts/restore_database.sh --latest

# Restore from specific file
./scripts/restore_database.sh backups/cs_mcp_backup_20240101_120000.sql.gz

# Restore from S3
./scripts/restore_database.sh --from-s3 cs_mcp_backup_20240101_120000.sql.gz
```

## Backup Script (`backup_database.sh`)

### Features

- **Full PostgreSQL Backup**: Complete database dump using `pg_dump`
- **Automatic Compression**: Gzip compression for efficient storage
- **S3 Upload**: Automatic upload to S3 with versioning
- **Backup Verification**: Integrity checks after backup creation
- **Retention Policy**: Automatic deletion of old backups (default: 30 days)
- **Notifications**: Slack and email notifications on success/failure
- **Detailed Logging**: Comprehensive logs for troubleshooting

### Usage

```bash
# Full backup (schema + data)
./scripts/backup_database.sh

# Schema-only backup
./scripts/backup_database.sh --schema-only
```

### Output

Backups are stored in:
- **Local**: `backups/cs_mcp_backup_YYYYMMDD_HHMMSS.sql.gz`
- **S3**: `s3://your-bucket/backups/database/cs_mcp_backup_YYYYMMDD_HHMMSS.sql.gz`
- **Logs**: `backups/backup_YYYYMMDD_HHMMSS.log`

### Backup Process

1. Check prerequisites (commands, credentials, connectivity)
2. Create compressed backup with `pg_dump | gzip`
3. Verify backup integrity (gzip test, SQL content check)
4. Upload to S3 (if configured)
5. Clean up old backups based on retention policy
6. Send notifications

## Restore Script (`restore_database.sh`)

### Features

- **Multiple Restore Sources**: Local file, S3, or latest backup
- **Safety Backup**: Automatic pre-restore backup of current database
- **Connection Management**: Terminates active connections before restore
- **Verification**: Post-restore integrity checks
- **Rollback Support**: Can restore from safety backup if needed

### Usage

```bash
# Restore from latest local backup
./scripts/restore_database.sh --latest

# Restore from specific file
./scripts/restore_database.sh backups/cs_mcp_backup_20240101_120000.sql.gz

# Restore from S3
./scripts/restore_database.sh --from-s3 cs_mcp_backup_20240101_120000.sql.gz

# Restore without safety backup (faster, but riskier)
./scripts/restore_database.sh --no-safety-backup --latest

# Force restore without confirmation
./scripts/restore_database.sh --force --latest
```

### Restore Process

1. Check prerequisites
2. Verify backup file integrity
3. Show warning and request confirmation
4. Create safety backup of current database
5. Terminate all active database connections
6. Drop and recreate database
7. Restore from backup file
8. Verify restored database

### Safety Features

- **Confirmation Required**: Must type "yes" to proceed (unless `--force`)
- **Safety Backup**: Automatic backup before restore
- **Verification**: Checks table count after restore
- **Rollback Instructions**: Shows how to rollback if restore fails

### WARNING

**This script will DROP and RECREATE the database, losing all existing data!**

Always:
- Test restore procedures in a non-production environment first
- Verify backups are valid before attempting restore
- Ensure you have a recent backup before restoring
- Notify stakeholders before performing restore in production

## Automated Backups with Cron

### Setup Daily Backups

1. **Edit crontab**:
   ```bash
   crontab -e
   ```

2. **Add cron job** (daily at 2 AM):
   ```cron
   # Customer Success MCP Database Backup
   # Runs daily at 2:00 AM
   0 2 * * * /opt/cs_mcp/scripts/backup_cron.sh >> /var/log/cs_mcp_backup_cron.log 2>&1

   # Weekly full backup on Sunday at 3:00 AM
   0 3 * * 0 /opt/cs_mcp/scripts/backup_cron.sh >> /var/log/cs_mcp_backup_cron.log 2>&1
   ```

3. **Verify cron job**:
   ```bash
   crontab -l
   ```

### Alternative Cron Schedules

```cron
# Every 6 hours
0 */6 * * * /opt/cs_mcp/scripts/backup_cron.sh

# Every day at 2 AM and 2 PM
0 2,14 * * * /opt/cs_mcp/scripts/backup_cron.sh

# Every weekday at 1 AM
0 1 * * 1-5 /opt/cs_mcp/scripts/backup_cron.sh

# First day of every month at midnight
0 0 1 * * /opt/cs_mcp/scripts/backup_cron.sh
```

### Monitor Cron Logs

```bash
# View recent backup logs
tail -f /var/log/cs_mcp_backup_cron.log

# View all backup logs
ls -lh /opt/cs_mcp/backups/backup_*.log

# Check last backup status
cat /opt/cs_mcp/backups/backup_*.log | tail -20
```

## AWS S3 Configuration

### 1. Create S3 Bucket

```bash
aws s3 mb s3://your-backup-bucket --region us-east-1
```

### 2. Enable Versioning

```bash
aws s3api put-bucket-versioning \
    --bucket your-backup-bucket \
    --versioning-configuration Status=Enabled
```

### 3. Configure Lifecycle Policy

Create `s3-lifecycle.json`:

```json
{
  "Rules": [
    {
      "Id": "MoveToGlacierAfter90Days",
      "Status": "Enabled",
      "Prefix": "backups/database/",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ]
    },
    {
      "Id": "DeleteAfter2Years",
      "Status": "Enabled",
      "Prefix": "backups/database/",
      "Expiration": {
        "Days": 730
      }
    }
  ]
}
```

Apply lifecycle policy:

```bash
aws s3api put-bucket-lifecycle-configuration \
    --bucket your-backup-bucket \
    --lifecycle-configuration file://s3-lifecycle.json
```

### 4. Configure Bucket Encryption

```bash
aws s3api put-bucket-encryption \
    --bucket your-backup-bucket \
    --server-side-encryption-configuration '{
      "Rules": [{
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }]
    }'
```

## Backup Strategy Recommendations

### Frequency

- **Production**: Daily full backups + transaction log archiving
- **Staging**: Daily backups
- **Development**: Weekly backups

### Retention

- **Production**:
  - Local: 7 days
  - S3 Standard: 30 days
  - S3 Glacier: 90 days
  - S3 Deep Archive: 2 years
- **Staging/Dev**: 7 days local, 30 days S3

### Testing

- **Monthly**: Test full restore procedure in staging environment
- **Quarterly**: Disaster recovery drill
- **After major changes**: Immediate backup and restore test

### Monitoring

- Set up Slack/email notifications for backup failures
- Monitor backup size trends (sudden changes may indicate issues)
- Alert on missing backups (cron job failures)
- Track restore time metrics

## Troubleshooting

### Backup Fails with "Connection Refused"

**Problem**: Cannot connect to database.

**Solutions**:
```bash
# Check database is running
pg_isready -h $DB_HOST -p $DB_PORT

# Check credentials
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1"

# Check network connectivity
telnet $DB_HOST $DB_PORT
```

### Backup Fails with "Permission Denied"

**Problem**: User lacks sufficient privileges.

**Solution**:
```sql
-- Grant necessary privileges
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup_user;
```

### S3 Upload Fails

**Problem**: AWS credentials not configured or invalid.

**Solutions**:
```bash
# Configure AWS CLI
aws configure

# Test S3 access
aws s3 ls s3://your-backup-bucket/

# Check IAM permissions (need s3:PutObject, s3:GetObject, s3:ListBucket)
```

### Restore Fails with "Database in Use"

**Problem**: Active connections prevent database drop.

**Solution**:
The restore script automatically terminates connections, but if it fails:
```sql
-- Manually terminate connections
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'cs_mcp_production'
  AND pid <> pg_backend_pid();
```

### Backup File Corrupted

**Problem**: Gzip integrity test fails.

**Solutions**:
```bash
# Verify backup integrity
gzip -t backup_file.sql.gz

# Try to recover partial data
gunzip -c backup_file.sql.gz > recovered.sql

# Use S3 versioning to retrieve earlier version
aws s3api list-object-versions --bucket your-backup-bucket --prefix backups/database/
```

### Out of Disk Space

**Problem**: Backup fails due to insufficient disk space.

**Solutions**:
```bash
# Check disk usage
df -h

# Clean up old backups manually
find backups/ -name "*.sql.gz" -mtime +30 -delete

# Reduce retention period
export BACKUP_RETENTION_DAYS=7
```

## Security Best Practices

1. **Encrypt Backups**:
   - Use S3 server-side encryption (AES256 or KMS)
   - Consider client-side encryption for sensitive data

2. **Secure Credentials**:
   - Never commit `.env` files to version control
   - Use IAM roles instead of access keys when possible
   - Rotate credentials regularly

3. **Access Control**:
   - Limit S3 bucket access to backup scripts only
   - Use separate IAM user for backups
   - Enable MFA Delete on S3 bucket

4. **Audit Logging**:
   - Enable S3 access logging
   - Monitor backup/restore operations
   - Alert on unauthorized access

5. **Network Security**:
   - Use SSL/TLS for database connections
   - Restrict database access to backup servers
   - Use VPC endpoints for S3 access (AWS)

## Performance Optimization

### For Large Databases

```bash
# Use parallel backup (requires PostgreSQL 9.3+)
pg_dump --format=directory --jobs=4 -f backup_dir/

# Compress with pigz (parallel gzip)
pg_dump | pigz > backup.sql.gz

# Use custom format for faster restore
pg_dump --format=custom -f backup.dump

# Skip large tables that can be rebuilt
pg_dump --exclude-table=logs --exclude-table=analytics_raw
```

### Reduce Backup Time

1. **Use pg_dump custom format**: Faster than plain SQL
2. **Parallel dumps**: Use `--jobs` flag for multi-threaded backup
3. **Exclude unnecessary data**: Skip log tables, temp tables
4. **Incremental backups**: Use WAL archiving for point-in-time recovery

### Reduce Storage Costs

1. **Better compression**: Use `pigz` or `zstd` instead of `gzip`
2. **Lifecycle policies**: Move to Glacier after 90 days
3. **Deduplication**: Use tools like `restic` or `borg`
4. **Schema-only backups**: Periodic schema backups are much smaller

## Disaster Recovery

### Complete Database Loss

1. Provision new database server
2. Install PostgreSQL (same version as backup)
3. Restore from most recent backup:
   ```bash
   ./scripts/restore_database.sh --from-s3 <latest_backup>
   ```
4. Apply transaction logs (if using WAL archiving)
5. Verify data integrity
6. Update DNS/load balancer to point to new server

### Partial Data Corruption

1. Identify corrupted data
2. Create safety backup of current state
3. Restore specific tables from backup:
   ```bash
   # Extract specific table
   pg_restore -t specific_table backup.dump
   ```
4. Verify table integrity
5. Re-enable application access

### Accidental Data Deletion

1. Immediately create backup of current state
2. Identify backup taken before deletion
3. Extract and restore only affected data
4. Verify data consistency
5. Implement additional safeguards (row-level security, audit triggers)

## References

- [PostgreSQL Backup & Restore](https://www.postgresql.org/docs/current/backup.html)
- [pg_dump Documentation](https://www.postgresql.org/docs/current/app-pgdump.html)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/backup-best-practices.html)
- [Database Backup Strategies](https://www.postgresql.org/docs/current/backup-strategies.html)

## Support

For issues or questions:
- Check script logs in `backups/backup_*.log` or `backups/restore_*.log`
- Review this README
- Contact the ops team
