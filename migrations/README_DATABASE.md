# Database Migrations - Customer Success MCP

## Overview

This document describes the database schema and migration setup for the Customer Success MCP (Model Context Protocol) server.

## Migration Summary

**Migration ID**: `6b022f57af5f`
**Migration File**: `/Users/evanpaliotta/199os-customer-success-mcp/migrations/versions/6b022f57af5f_initial_migration_create_all_27_tables_.py`

### Statistics
- **Total Tables**: 24 tables
- **Total Indexes**: 134 indexes (including composite indexes)
- **Foreign Key Constraints**: 12 foreign keys with CASCADE delete
- **Check Constraints**: 12 check constraints for data integrity

## Database Schema

### Customer Tables (5 tables)

1. **customers** - Main customer account table
   - Primary key on client_id (unique customer identifier)
   - Indexes: client_id, tier, lifecycle_stage, health_score, status, csm_assigned, dates
   - Composite indexes: (client_id, created_at), (health_score, status), (csm_assigned, lifecycle_stage)

2. **health_scores** - Health score component breakdowns
   - Foreign key to customers.client_id (CASCADE delete)
   - Tracks 5 component scores (usage, engagement, support, satisfaction, payment)
   - Weighted scoring with configurable weights

3. **customer_segments** - Customer segmentation definitions
   - JSON criteria for flexible segmentation rules
   - Aggregate metrics (customer_count, total_arr, avg_health_score)

4. **risk_indicators** - Individual risk factors for churn
   - Foreign key to customers.client_id (CASCADE delete)
   - Indexed by category, severity, and detection date

5. **churn_predictions** - ML-based churn prediction outputs
   - Foreign key to customers.client_id (CASCADE delete)
   - Probability ranges validated (0-1)
   - Tracks model version for A/B testing

### Onboarding Tables (4 tables)

6. **onboarding_plans** - Onboarding plan definitions
   - Foreign key to customers.client_id (CASCADE delete)
   - Tracks timeline, goals, success criteria
   - Status tracking with completion percentage

7. **onboarding_milestones** - Individual plan milestones
   - Foreign key to onboarding_plans.plan_id (CASCADE delete)
   - Supports dependencies and blockers
   - Time tracking (estimated vs actual hours)

8. **training_modules** - Training module catalog
   - Supports multiple formats (webinar, self-paced, etc.)
   - Assessment requirements and passing scores
   - Certification tracking

9. **training_completions** - User training completion records
   - Foreign key to training_modules.module_id (CASCADE delete)
   - Tracks attempts, scores, and certification issuance
   - User feedback and ratings

### Support Tables (3 tables)

10. **support_tickets** - Support ticket tracking
    - Foreign key to customers.client_id (CASCADE delete)
    - SLA tracking (first response, resolution)
    - Escalation management
    - Satisfaction ratings (1-5 validated)

11. **ticket_comments** - Ticket conversation history
    - Foreign key to support_tickets.ticket_id (CASCADE delete)
    - Public vs internal notes
    - Attachment tracking

12. **knowledge_base_articles** - Self-service KB articles
    - Version control and publishing workflow
    - View count and helpfulness voting
    - Tag-based search optimization
    - Access control per tier

### Renewal Tables (4 tables)

13. **renewal_forecasts** - Renewal prediction and planning
    - Foreign key to customers.client_id (CASCADE delete)
    - Probability-based forecasting (0-1 validated)
    - Risk factors and positive indicators
    - Expansion opportunity identification

14. **contracts** - Contract details and terms
    - Foreign key to customers.client_id (CASCADE delete)
    - Multi-currency support
    - Auto-renewal tracking
    - Payment status monitoring

15. **expansion_opportunities** - Upsell/cross-sell tracking
    - Probability and confidence scoring
    - Stage-based pipeline management
    - Stakeholder and champion tracking

16. **renewal_campaigns** - Campaign management for renewals
    - Win rate and performance tracking
    - Bulk renewal operations
    - Success metric monitoring

### Feedback Tables (4 tables)

17. **customer_feedback** - General customer feedback
    - Foreign key to customers.client_id (CASCADE delete)
    - Sentiment analysis (-1 to 1 validated)
    - Priority and status workflow
    - Follow-up tracking

18. **nps_responses** - Net Promoter Score surveys
    - Foreign key to customers.client_id (CASCADE delete)
    - Score validation (0-10)
    - Category auto-assignment (detractor/passive/promoter)
    - Response time tracking

19. **sentiment_analysis** - Aggregated sentiment reports
    - Time-series sentiment tracking
    - Theme extraction and analysis
    - NPS/CSAT score aggregation

20. **survey_templates** - Survey template definitions
    - Question configuration (JSON)
    - Targeting criteria
    - Frequency scheduling

### Analytics Tables (4 tables)

21. **health_metrics** - Comprehensive health analytics
    - Time-series health tracking
    - Component-level trends
    - Benchmark comparisons
    - Predictive scoring

22. **engagement_metrics** - User engagement analytics
    - DAU/WAU/MAU tracking
    - Session and activity metrics
    - Feature adoption rates
    - User segmentation (power users, at-risk)

23. **usage_analytics** - Product usage analytics
    - Feature utilization tracking
    - Integration usage monitoring
    - API usage statistics
    - Growth rate calculations

24. **cohort_analysis** - Customer cohort analytics
    - Retention tracking over time
    - Revenue metrics (NRR, expansion)
    - Engagement trends by cohort
    - Benchmark comparisons

## Index Strategy

### Primary Lookup Indexes
All tables include indexes on primary lookup keys:
- `client_id` - Primary customer identifier (most queries filter by customer)
- `status` fields - Workflow state filtering
- Timestamp fields - Time-range queries

### Composite Indexes
Strategic composite indexes for common query patterns:
- `(client_id, created_at)` - Customer timeline queries
- `(client_id, status)` - Customer-specific status filtering
- `(health_score, status)` - Health-based segmentation
- `(csm_assigned, lifecycle_stage)` - CSM workload queries
- `(priority, created_at)` - Priority-based queues

### Performance Considerations
- Total of 134 indexes across 24 tables (~5.6 indexes per table)
- Indexes chosen based on expected query patterns
- Avoid over-indexing on rarely queried columns
- JSON columns indexed where appropriate for filtering

## Foreign Key Constraints

All foreign keys use **CASCADE delete** for referential integrity:
- Deleting a customer removes all associated records
- Deleting an onboarding plan removes all milestones
- Deleting a training module removes all completions
- Deleting a support ticket removes all comments

This ensures no orphaned records and maintains data consistency.

## Check Constraints

Data validation at the database level:
- `health_score` range: 0-100
- `contract_value` >= 0
- `churn_probability` range: 0-1
- `renewal_probability` range: 0-1
- `sentiment_score` range: -1 to 1
- `satisfaction_rating` range: 1-5
- `nps_score` range: 0-10

## Running Migrations

### Prerequisites
1. Set DATABASE_URL environment variable:
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/customer_success"
   ```

2. Ensure PostgreSQL is running and database exists:
   ```bash
   createdb customer_success
   ```

### Apply Migration
```bash
# Run the migration
alembic upgrade head
```

### Verify Migration
```bash
# Check current version
alembic current

# View migration history
alembic history

# Show SQL (without executing)
alembic upgrade head --sql
```

### Rollback Migration
```bash
# Rollback one version
alembic downgrade -1

# Rollback to base (remove all tables)
alembic downgrade base
```

## Query Performance Tips

### Optimize Common Queries

1. **Customer Health Dashboard**
   ```sql
   SELECT c.client_id, c.client_name, c.health_score, c.health_trend, c.lifecycle_stage
   FROM customers c
   WHERE c.health_score < 70 AND c.status = 'active'
   ORDER BY c.health_score ASC;
   -- Uses ix_customers_health_score_status composite index
   ```

2. **CSM Workload**
   ```sql
   SELECT c.csm_assigned, COUNT(*) as customer_count, AVG(c.health_score) as avg_health
   FROM customers c
   WHERE c.status = 'active'
   GROUP BY c.csm_assigned;
   -- Uses ix_customers_csm_assigned and ix_customers_status indexes
   ```

3. **Renewal Pipeline**
   ```sql
   SELECT r.client_id, r.renewal_date, r.renewal_probability, r.forecasted_arr
   FROM renewal_forecasts r
   WHERE r.days_until_renewal <= 90 AND r.renewal_status = 'at_risk'
   ORDER BY r.renewal_date ASC;
   -- Uses ix_renewal_forecasts_status_days composite index
   ```

4. **Support SLA Monitoring**
   ```sql
   SELECT t.ticket_id, t.client_id, t.priority, t.created_at,
          t.first_response_sla_status, t.resolution_sla_status
   FROM support_tickets t
   WHERE t.status IN ('open', 'in_progress')
     AND (t.first_response_sla_status = 'breached'
          OR t.resolution_sla_status = 'at_risk')
   ORDER BY t.priority, t.created_at;
   -- Uses ix_support_tickets_priority_created composite index
   ```

5. **Churn Risk Analysis**
   ```sql
   SELECT c.client_id, c.client_name, c.health_score,
          cp.churn_probability, cp.churn_risk_level
   FROM customers c
   JOIN churn_predictions cp ON c.client_id = cp.client_id
   WHERE cp.churn_risk_level IN ('high', 'critical')
     AND c.status = 'active'
   ORDER BY cp.churn_probability DESC;
   -- Uses ix_churn_predictions_risk_level and ix_customers_status indexes
   ```

### EXPLAIN ANALYZE Examples

Run `EXPLAIN ANALYZE` to verify index usage:
```sql
EXPLAIN ANALYZE
SELECT c.client_id, c.client_name, c.health_score
FROM customers c
WHERE c.csm_assigned = 'Sarah Johnson' AND c.lifecycle_stage = 'active';
-- Should use ix_customers_csm_lifecycle composite index
```

## Database Maintenance

### Regular Tasks

1. **Analyze Tables** (update statistics for query planner)
   ```sql
   ANALYZE customers;
   ANALYZE support_tickets;
   ANALYZE renewal_forecasts;
   ```

2. **Vacuum** (reclaim storage)
   ```sql
   VACUUM ANALYZE;
   ```

3. **Reindex** (if index bloat detected)
   ```sql
   REINDEX TABLE customers;
   ```

4. **Monitor Slow Queries**
   ```sql
   -- Enable slow query logging in postgresql.conf
   log_min_duration_statement = 1000  # Log queries > 1 second
   ```

### Monitoring Queries

1. **Check Index Usage**
   ```sql
   SELECT schemaname, tablename, indexname, idx_scan
   FROM pg_stat_user_indexes
   ORDER BY idx_scan ASC;
   -- Indexes with idx_scan = 0 are unused
   ```

2. **Table Size**
   ```sql
   SELECT tablename,
          pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables
   WHERE schemaname = 'public'
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

3. **Index Size**
   ```sql
   SELECT indexname,
          pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) AS size
   FROM pg_indexes
   WHERE schemaname = 'public'
   ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC;
   ```

## Future Migrations

When creating new migrations:

1. **Always test rollback**:
   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

2. **Use meaningful names**:
   ```bash
   alembic revision -m "add_customer_subscription_tier_column"
   ```

3. **Add indexes strategically**:
   - Only index columns used in WHERE, JOIN, ORDER BY
   - Consider composite indexes for multi-column queries
   - Monitor query performance before adding

4. **Use constraints for data integrity**:
   - Foreign keys for relationships
   - Check constraints for valid ranges
   - Unique constraints for business keys

## Troubleshooting

### Common Issues

1. **Migration fails with "relation already exists"**
   ```bash
   # Check current version
   alembic current

   # If version is wrong, stamp correct version
   alembic stamp head
   ```

2. **Foreign key constraint violation**
   ```sql
   -- Find orphaned records before migration
   SELECT client_id FROM health_scores
   WHERE client_id NOT IN (SELECT client_id FROM customers);
   ```

3. **Slow migration**
   - Large datasets may require batching
   - Consider creating indexes CONCURRENTLY
   - Run during low-traffic windows

## Additional Resources

- Alembic Documentation: https://alembic.sqlalchemy.org/
- PostgreSQL Performance: https://wiki.postgresql.org/wiki/Performance_Optimization
- Index Tuning: https://wiki.postgresql.org/wiki/Index_Maintenance

## Contact

For questions about the database schema or migrations, contact the Customer Success MCP team.
