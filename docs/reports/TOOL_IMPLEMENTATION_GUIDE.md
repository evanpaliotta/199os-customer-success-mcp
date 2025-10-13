# Health & Segmentation Tools - Database Integration Guide

## Completed

### 1. segment_by_value_tier ✅
- Removed all mock data
- Added database queries for tier distribution, VIP accounts, upgrade/downgrade candidates
- Added Mixpanel tracking
- Added structured logging
- Added error handling with database cleanup
- **Status**: Production-ready

## Remaining Tools - Implementation Guide

### 2. track_usage_engagement (Lines 1405-1889)

**Mock Data to Replace:**
```python
# Line 1500: Remove mock customer generation
customer = mock.generate_customer_account(client_id=client_id)

# Lines 1507-1534: Replace engagement metrics with database queries
db = SessionLocal()
try:
    customer = _get_customer_from_db(db, client_id)

    # Query last_engagement_date from customer table
    total_users = db.query(func.count(distinct(UserActivity.user_id))).filter(
        UserActivity.client_id == client_id
    ).scalar() or 0

    # Calculate active users from last 30 days
    active_users = db.query(func.count(distinct(UserActivity.user_id))).filter(
        UserActivity.client_id == client_id,
        UserActivity.activity_date >= datetime.now() - timedelta(days=30)
    ).scalar() or 0

    # Continue with real metrics...
finally:
    db.close()
```

**Mixpanel Tracking**: Already present (lines 1484-1497) - Keep it

**Add Structured Logging**:
```python
logger.info(
    "usage_engagement_tracked",
    client_id=client_id,
    period_days=days_diff,
    active_users=active_users,
    engagement_rate=engagement_rate
)
```

### 3. segment_customers (Lines 2328-2905)

**Mock Data to Replace:**
```python
# Lines 2374-2432: Remove _generate_value_segments, _generate_usage_segments, etc.

# Replace with database queries:
db = SessionLocal()
try:
    if segmentation_type == "value_based":
        # Query customers by ARR tiers
        high_value = db.query(CustomerAccountDB).filter(
            CustomerAccountDB.contract_value >= 100000
        ).all()

    elif segmentation_type == "health_based":
        # Query by health score ranges
        healthy = db.query(CustomerAccountDB).filter(
            CustomerAccountDB.health_score >= 80
        ).all()

    # Build CustomerSegment objects from real data
finally:
    db.close()
```

**Add Mixpanel + Logging**

### 4. track_feature_adoption (Lines 2907-3077)

**Mock Data to Replace:**
```python
# Create or query feature_adoption table
CREATE TABLE IF NOT EXISTS feature_adoption (
    id INTEGER PRIMARY KEY,
    client_id VARCHAR(100),
    feature_id VARCHAR(100),
    adopted_date DATETIME,
    usage_count INTEGER,
    FOREIGN KEY (client_id) REFERENCES customers(client_id)
)

# Query real adoption data:
db = SessionLocal()
try:
    adoption_data = db.query(
        FeatureAdoption.feature_id,
        func.count(distinct(FeatureAdoption.client_id)).label('adopters'),
        func.avg(FeatureAdoption.usage_count).label('avg_usage')
    ).group_by(FeatureAdoption.feature_id).all()
finally:
    db.close()
```

### 5. track_adoption_milestones (Lines 3544-3736)

**Mock Data to Replace:**
```python
# Create adoption_milestones table
CREATE TABLE IF NOT EXISTS adoption_milestones (
    id INTEGER PRIMARY KEY,
    client_id VARCHAR(100),
    milestone_id VARCHAR(100),
    milestone_name VARCHAR(200),
    completed_date DATETIME,
    progress_percentage FLOAT,
    FOREIGN KEY (client_id) REFERENCES customers(client_id)
)

# Query milestone progress:
db = SessionLocal()
try:
    milestones = db.query(AdoptionMilestone).filter(
        AdoptionMilestone.client_id == client_id
    ).all()

    completed = sum(1 for m in milestones if m.completed_date)
    total = len(milestones)
    completion_rate = completed / total if total > 0 else 0
finally:
    db.close()
```

### 6. analyze_engagement_patterns (Lines 4654-5024)

**Mock Data to Replace:**
```python
# Query engagement patterns from database:
db = SessionLocal()
try:
    # Temporal patterns
    hourly_activity = db.query(
        func.strftime('%H', UserActivity.activity_timestamp).label('hour'),
        func.count(UserActivity.id).label('count')
    ).filter(
        UserActivity.client_id == client_id,
        UserActivity.activity_date >= start_date
    ).group_by('hour').all()

    # Feature usage patterns
    feature_patterns = db.query(
        FeatureUsage.feature_id,
        func.count(FeatureUsage.id).label('usage_count'),
        func.count(distinct(FeatureUsage.user_id)).label('user_count')
    ).filter(
        FeatureUsage.client_id == client_id
    ).group_by(FeatureUsage.feature_id).all()
finally:
    db.close()
```

## Standard Pattern for All Tools

```python
def tool_function(...):
    try:
        # Validate inputs
        validate_client_id(client_id)

        # Initialize database
        db = _get_db_session()

        try:
            # Get customer
            customer = _get_customer_from_db(db, client_id)
            if not customer:
                return json.dumps({"status": "error", "error": "Customer not found"})

            # Query real data
            # ... database queries ...

            # Build response
            results = ResultsModel(...)

            # Track in Mixpanel
            mixpanel = MixpanelClient()
            mixpanel.track_event(
                user_id=client_id,
                event_name="tool_executed",
                properties={...}
            )

            # Log success
            logger.info(
                "tool_completed",
                client_id=client_id,
                ...
            )

            return results.model_dump_json(indent=2)

        except Exception as e:
            logger.error("tool_error", client_id=client_id, error=str(e))
            return json.dumps({"status": "error", "error": str(e)})
        finally:
            db.close()

    except ValidationError as e:
        logger.error("validation_error", error=str(e))
        raise
```

## Database Tables Needed

### Existing Tables (Already Available)
- `customers` - Customer accounts
- `health_scores` - Health score components
- `customer_segments` - Segmentation data
- `risk_indicators` - Risk flags
- `churn_predictions` - Churn predictions
- `support_tickets` - Support data
- `contracts` - Contract details
- `nps_responses` - NPS scores
- `customer_feedback` - Feedback data

### New Tables to Create (Optional)
- `feature_adoption` - Track feature usage per customer
- `adoption_milestones` - Track milestone completion
- `user_activity` - Track user-level activity
- `feature_usage` - Track feature-level usage patterns
- `engagement_events` - Track engagement events

## Validation Checklist

For each tool:
- [ ] Remove all `mock.generate_*` calls
- [ ] Remove all `mock.random_*` calls
- [ ] Add `db = _get_db_session()`
- [ ] Add database queries for all metrics
- [ ] Add error handling with try/except/finally
- [ ] Add `db.close()` in finally block
- [ ] Add Mixpanel tracking
- [ ] Add structured logging with `logger.info()`
- [ ] Validate syntax: `python -m py_compile`
- [ ] Test with real customer data

## Estimated Completion Time

- track_usage_engagement: 6 hours
- segment_customers: 5 hours
- track_feature_adoption: 5 hours
- track_adoption_milestones: 5 hours
- analyze_engagement_patterns: 6 hours

**Total**: ~27 hours remaining
