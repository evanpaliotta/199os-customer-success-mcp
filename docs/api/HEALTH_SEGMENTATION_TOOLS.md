# Health & Segmentation Tools API Reference

**Category:** Health Monitoring & Customer Segmentation
**Tools:** 8
**Module:** `src/tools/health_segmentation_tools.py`
**Status:** ✅ Production Ready

---

## Overview

The Health & Segmentation tools provide comprehensive customer health monitoring, scoring, and segmentation capabilities. These tools are essential for proactive customer success management, churn prevention, and identifying expansion opportunities.

**Key Capabilities:**
- Real-time health score calculation with predictive analytics
- Usage and engagement tracking with behavioral insights
- Multi-dimensional customer segmentation
- Feature adoption monitoring and optimization
- Lifecycle stage management
- Adoption milestone tracking
- Value-tier segmentation
- Engagement pattern analysis with ML predictions

---

## Tool 1: track_usage_engagement

**Purpose:** Track detailed product usage and engagement analytics for a customer.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Customer identifier |
| `period_start` | string (ISO 8601) | Yes | Analysis period start date |
| `period_end` | string (ISO 8601) | Yes | Analysis period end date |
| `granularity` | string | No | Data granularity: `hourly`, `daily` (default), `weekly`, `monthly` |
| `include_feature_breakdown` | boolean | No | Include feature-level usage breakdown (default: true) |
| `include_user_segmentation` | boolean | No | Include user cohort analysis (default: true) |
| `benchmark_comparison` | boolean | No | Compare against industry benchmarks (default: true) |

### Returns

```json
{
  "client_id": "cs_client_123",
  "analysis_period": {
    "start": "2025-09-01T00:00:00Z",
    "end": "2025-10-01T00:00:00Z"
  },
  "engagement_metrics": {
    "weekly_active_users": 45,
    "monthly_active_users": 68,
    "daily_active_users": 23,
    "user_activation_rate": 0.91,
    "feature_adoption_rate": 0.73,
    "average_session_duration_minutes": 42,
    "sessions_per_user_per_week": 4.2
  },
  "usage_analytics": {
    "total_sessions": 1248,
    "total_events": 45892,
    "unique_features_used": 18,
    "api_calls_count": 45230
  },
  "usage_trends": {
    "trend_direction": "increasing",
    "weekly_growth_rate": 0.12,
    "usage_velocity": "accelerating"
  },
  "user_cohorts": {
    "power_users": 12,
    "regular_users": 33,
    "at_risk_users": 8,
    "inactive_users": 15
  },
  "feature_adoption_timeline": [
    {
      "feature": "Advanced Analytics",
      "first_use_date": "2025-09-05",
      "adoption_rate": 0.65,
      "weekly_usage": 23
    }
  ],
  "activity_heatmap": {
    "peak_days": ["Tuesday", "Wednesday", "Thursday"],
    "peak_hours": ["9-11am", "2-4pm"]
  },
  "benchmark_insights": {
    "vs_industry_average": "+18% higher engagement",
    "percentile_rank": 78
  },
  "recommendations": [
    "Accelerate feature adoption sequence",
    "Optimize outreach timing (Tue-Thu mornings)",
    "Engage at-risk users with personalized campaigns"
  ],
  "alerts": [
    {
      "type": "usage_decline",
      "severity": "medium",
      "message": "8 users showing decreased activity over past 7 days"
    }
  ]
}
```

### Use Cases
- Monitor product usage trends
- Identify power users vs. at-risk users
- Optimize feature rollout timing
- Detect engagement anomalies
- Benchmark against industry standards

### Related Tools
- `calculate_health_score` - Incorporate usage data into health scoring
- `track_feature_adoption` - Deep dive into specific feature adoption
- `analyze_engagement_patterns` - ML-based pattern detection

---

## Tool 2: calculate_health_score

**Purpose:** Calculate comprehensive customer health score with predictive analytics.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Customer identifier |
| `scoring_model` | string | No | Model: `weighted_composite` (default), `ml_predictive`, `custom` |
| `component_weights` | object | No | Custom weights for components (if using custom model) |
| `lookback_period_days` | integer | No | Days for trend analysis (default: 30, max: 365) |
| `include_predictions` | boolean | No | Include future health predictions (default: true) |
| `risk_threshold` | float | No | Threshold for risk alerts (default: 60.0, range: 0-100) |
| `alert_preferences` | object | No | Alert configuration |

### Component Weights (Default)
```json
{
  "usage_weight": 0.35,
  "engagement_weight": 0.25,
  "support_weight": 0.15,
  "satisfaction_weight": 0.15,
  "payment_weight": 0.10
}
```

### Returns

```json
{
  "client_id": "cs_client_123",
  "calculation_timestamp": "2025-10-10T14:23:45Z",
  "current_health_score": 82,
  "health_trend": "improving",
  "score_change": +5,
  "component_scores": {
    "usage_score": 85,
    "engagement_score": 88,
    "support_score": 82,
    "satisfaction_score": 92,
    "payment_score": 100
  },
  "health_metrics": {
    "weekly_active_users": 45,
    "feature_adoption_rate": 0.73,
    "support_ticket_count": 2,
    "nps_score": 45,
    "payment_status": "current"
  },
  "risk_level": "low",
  "risk_indicators": [],
  "churn_prediction": {
    "churn_probability": 0.12,
    "churn_risk_level": "low",
    "confidence": 0.87,
    "key_risk_factors": [],
    "protective_factors": [
      "High engagement",
      "Excellent support satisfaction",
      "Multiple integrations active"
    ]
  },
  "historical_scores": [
    {
      "date": "2025-09-10",
      "score": 77
    },
    {
      "date": "2025-10-10",
      "score": 82
    }
  ],
  "predicted_scores": [
    {
      "date": "2025-11-10",
      "predicted_score": 84,
      "confidence": 0.78
    }
  ],
  "contributing_factors": {
    "positive": [
      "Usage increased 12% over past month",
      "Feature adoption accelerating",
      "NPS score +45 (promoter)"
    ],
    "negative": []
  },
  "improvement_opportunities": [
    {
      "area": "Advanced feature adoption",
      "current_state": "4/15 advanced features used",
      "target_state": "8/15 features",
      "impact": "+3-5 points health score",
      "effort": "medium"
    }
  ],
  "recommended_actions": [
    "Present expansion proposal (high likelihood)",
    "Schedule quarterly business review",
    "Introduce advanced analytics features"
  ]
}
```

### Use Cases
- Real-time customer health monitoring
- Churn prediction and prevention
- Identify upsell-ready customers
- Prioritize CSM outreach
- Track health score trends over time

### Related Tools
- `track_usage_engagement` - Provides usage component data
- `identify_churn_risk` - Focused churn risk analysis
- `identify_expansion_opportunities` - Revenue expansion based on health

---

## Tool 3: segment_customers

**Purpose:** Segment customers by value, usage, health, industry, or lifecycle stage.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `segmentation_criteria` | object | Yes | Segmentation parameters |
| `segment_type` | string | Yes | Type: `value`, `usage`, `health`, `industry`, `lifecycle`, `custom` |
| `min_segment_size` | integer | No | Minimum customers per segment (default: 5) |
| `max_segments` | integer | No | Maximum number of segments (default: 10) |
| `include_recommendations` | boolean | No | Include engagement recommendations (default: true) |
| `output_format` | string | No | Format: `detailed` (default), `summary`, `ids_only` |

### Segmentation Criteria Examples

**Value Segmentation:**
```json
{
  "segment_type": "value",
  "segmentation_criteria": {
    "arr_thresholds": [10000, 50000, 100000],
    "include_expansion_potential": true
  }
}
```

**Health Segmentation:**
```json
{
  "segment_type": "health",
  "segmentation_criteria": {
    "health_score_thresholds": [40, 60, 80],
    "trend_weighting": 0.3
  }
}
```

### Returns

```json
{
  "total_customers": 250,
  "segments_created": 4,
  "segmentation_type": "health",
  "segments": [
    {
      "segment_id": "seg_champion_001",
      "segment_name": "Champions",
      "segment_description": "High health (80+), active engagement",
      "customer_count": 78,
      "percentage_of_total": 31.2,
      "segment_criteria": {
        "health_score_min": 80,
        "health_score_max": 100,
        "health_trend": "stable_or_improving"
      },
      "segment_characteristics": {
        "avg_health_score": 88,
        "avg_arr": 65000,
        "avg_tenure_months": 18,
        "feature_adoption_rate": 0.82
      },
      "recommended_engagement_strategy": {
        "primary_focus": "Expansion & advocacy",
        "communication_frequency": "monthly",
        "content_themes": ["Advanced features", "ROI showcase", "Best practices"],
        "csm_touch_frequency": "monthly",
        "automation_level": "medium"
      },
      "recommended_channels": ["email", "in-app", "webinar"],
      "recommended_content": {
        "newsletters": "Advanced tips & tricks",
        "webinars": "Power user masterclass",
        "case_studies": true
      },
      "escalation_criteria": [
        "Health score drops below 75",
        "Engagement decreases >20%"
      ]
    },
    {
      "segment_id": "seg_at_risk_004",
      "segment_name": "At Risk",
      "segment_description": "Low health (40-60), declining trends",
      "customer_count": 45,
      "percentage_of_total": 18.0,
      "recommended_engagement_strategy": {
        "primary_focus": "Retention & reactivation",
        "communication_frequency": "weekly",
        "content_themes": ["Support resources", "Quick wins", "Success stories"],
        "csm_touch_frequency": "weekly",
        "automation_level": "low"
      },
      "recommended_actions": [
        "Immediate CSM outreach",
        "Identify and address pain points",
        "Create personalized success plan",
        "Escalate to management if no improvement in 14 days"
      ]
    }
  ],
  "segment_summary": {
    "champions": 78,
    "healthy": 102,
    "at_risk": 45,
    "critical": 25
  },
  "pareto_analysis": {
    "top_20_percent_contribute": "68% of total ARR",
    "segment": "Champions & Healthy"
  },
  "cross_segment_insights": [
    "Champions have 3x higher feature adoption than At Risk segment",
    "At Risk segment has 4x more open support tickets"
  ],
  "recommended_actions": [
    "Prioritize retention efforts on At Risk segment (45 customers, $1.2M ARR at stake)",
    "Launch advocacy program for Champions segment",
    "Create targeted onboarding for Healthy segment to prevent decline"
  ]
}
```

### Use Cases
- Targeted marketing campaigns
- CSM resource allocation
- Personalized engagement strategies
- Risk prioritization
- Expansion pipeline building

### Related Tools
- `segment_by_value_tier` - Value-specific segmentation
- `calculate_health_score` - Health data for segmentation
- `identify_expansion_opportunities` - Target high-value segments

---

## Tool 4: track_feature_adoption

**Purpose:** Monitor feature adoption rates, patterns, and optimization opportunities.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | No | Specific customer (omit for all customers) |
| `feature_category` | string | No | Category: `core`, `advanced`, `premium`, `all` (default) |
| `time_period_days` | integer | No | Analysis period (default: 30) |
| `include_adoption_funnel` | boolean | No | Include adoption funnel analysis (default: true) |
| `include_correlation_analysis` | boolean | No | Correlate adoption with outcomes (default: true) |
| `benchmark_against` | string | No | Benchmark: `tier`, `industry`, `all_customers` |

### Returns

```json
{
  "analysis_scope": "All customers",
  "analysis_period_days": 30,
  "feature_adoption_summary": {
    "core_features": {
      "total_features": 25,
      "adopted_features": 18,
      "adoption_rate": 0.72,
      "average_time_to_adopt_days": 14
    },
    "advanced_features": {
      "total_features": 15,
      "adopted_features": 4,
      "adoption_rate": 0.27,
      "average_time_to_adopt_days": 45
    }
  },
  "feature_details": [
    {
      "feature_name": "Advanced Analytics",
      "feature_category": "advanced",
      "adoption_rate": 0.65,
      "customers_using": 162,
      "total_customers": 250,
      "average_time_to_first_use_days": 32,
      "usage_frequency": "weekly",
      "customer_satisfaction": 4.5,
      "correlation_with_retention": 0.78
    }
  ],
  "adoption_funnel": {
    "awareness": 250,
    "trial": 180,
    "first_use": 162,
    "regular_use": 98,
    "power_use": 45,
    "conversion_rate": 0.39
  },
  "adoption_patterns": [
    {
      "pattern": "Sequential adopters",
      "percentage": 45,
      "characteristics": "Adopt features in recommended sequence",
      "avg_time_to_value": 28,
      "retention_rate": 0.92
    },
    {
      "pattern": "Fast explorers",
      "percentage": 25,
      "characteristics": "Rapidly try multiple features",
      "avg_time_to_value": 18,
      "retention_rate": 0.88
    }
  ],
  "correlation_analysis": {
    "adoption_vs_health_score": 0.82,
    "adoption_vs_retention": 0.78,
    "adoption_vs_expansion": 0.71
  },
  "benchmark_comparison": {
    "vs_tier_average": "+12% higher adoption",
    "vs_industry_average": "+8% higher adoption"
  },
  "recommendations": [
    {
      "feature": "Advanced Analytics",
      "current_adoption": 0.65,
      "target_adoption": 0.80,
      "recommended_actions": [
        "Create guided tutorial for first-time users",
        "Highlight in onboarding checklist",
        "Share customer success stories"
      ],
      "expected_impact": "+15% adoption within 60 days"
    }
  ],
  "low_adoption_features": [
    {
      "feature": "API Webhooks",
      "adoption_rate": 0.15,
      "barriers": ["Technical complexity", "Unclear value proposition"],
      "improvement_strategies": ["Better documentation", "Code examples", "Webinar"]
    }
  ]
}
```

### Use Cases
- Optimize feature rollout strategy
- Identify underutilized features
- Improve onboarding sequences
- Correlate features with retention
- Prioritize product development

### Related Tools
- `track_usage_engagement` - Overall usage context
- `optimize_onboarding_process` - Incorporate into onboarding
- `track_adoption_milestones` - Milestone-based tracking

---

## Tool 5: manage_lifecycle_stages

**Purpose:** Manage customer lifecycle stage transitions and automation.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Customer identifier |
| `action` | string | Yes | Action: `get_stage`, `update_stage`, `transition`, `get_history` |
| `new_stage` | string | No | New stage (for `update_stage` or `transition`) |
| `transition_reason` | string | No | Reason for stage change |
| `automated` | boolean | No | Automated transition (default: false) |
| `notify_team` | boolean | No | Notify CSM team (default: true) |

### Lifecycle Stages
- `prospect` - Potential customer
- `trial` - Trial period
- `onboarding` - Active onboarding
- `active` - Active customer
- `engaged` - Highly engaged
- `at_risk` - At risk of churn
- `renewing` - Renewal process
- `expanded` - Expansion completed
- `churned` - Lost customer

### Returns (for `transition` action)

```json
{
  "client_id": "cs_client_123",
  "previous_stage": "onboarding",
  "current_stage": "active",
  "transition_date": "2025-10-10T14:23:45Z",
  "transition_reason": "Completed all onboarding milestones",
  "automated": false,
  "days_in_previous_stage": 24,
  "stage_progression": [
    {
      "stage": "trial",
      "start_date": "2025-08-15",
      "end_date": "2025-08-29",
      "duration_days": 14
    },
    {
      "stage": "onboarding",
      "start_date": "2025-08-30",
      "end_date": "2025-10-10",
      "duration_days": 42
    },
    {
      "stage": "active",
      "start_date": "2025-10-10",
      "end_date": null,
      "duration_days": 0
    }
  ],
  "stage_health": {
    "current_stage_typical_duration_days": "ongoing",
    "health_score": 82,
    "stage_appropriate_health": true
  },
  "automated_actions_triggered": [
    {
      "action": "send_welcome_email",
      "status": "scheduled",
      "scheduled_for": "2025-10-11T09:00:00Z"
    },
    {
      "action": "update_crm_stage",
      "status": "completed"
    },
    {
      "action": "notify_csm",
      "status": "completed"
    }
  ],
  "next_stage_criteria": {
    "target_stage": "engaged",
    "criteria": [
      "Health score > 80 for 30+ days",
      "Feature adoption rate > 70%",
      "Regular usage (3+ sessions/week)",
      "No open critical support tickets"
    ],
    "progress": {
      "criteria_met": 2,
      "criteria_total": 4,
      "estimated_days_to_transition": 18
    }
  },
  "recommended_actions": [
    "Monitor health score for next 30 days",
    "Encourage advanced feature adoption",
    "Schedule 30-day check-in call"
  ]
}
```

### Use Cases
- Automate lifecycle management
- Track customer journey
- Trigger stage-specific playbooks
- Measure time-to-value
- Identify stuck customers

### Related Tools
- `calculate_health_score` - Health context for stage transitions
- `track_adoption_milestones` - Milestone-based transitions
- `map_customer_journey` - Journey mapping

---

## Tool 6: track_adoption_milestones

**Purpose:** Track onboarding and adoption milestones with progress monitoring.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Customer identifier |
| `milestone_category` | string | No | Category: `onboarding`, `adoption`, `expansion`, `all` (default) |
| `include_overdue` | boolean | No | Include overdue milestones (default: true) |
| `include_recommendations` | boolean | No | Include acceleration recommendations (default: true) |

### Returns

```json
{
  "client_id": "cs_client_123",
  "overall_progress": {
    "total_milestones": 15,
    "completed_milestones": 9,
    "in_progress_milestones": 4,
    "not_started_milestones": 2,
    "completion_rate": 0.60,
    "on_track": true
  },
  "milestone_details": [
    {
      "milestone_id": "ms_onboarding_001",
      "milestone_name": "Admin account setup",
      "milestone_category": "onboarding",
      "status": "completed",
      "target_completion_days": 1,
      "actual_completion_days": 0.5,
      "completion_date": "2025-08-30T10:00:00Z",
      "ahead_behind": "ahead",
      "days_ahead": 0.5
    },
    {
      "milestone_id": "ms_adoption_003",
      "milestone_name": "First advanced feature usage",
      "milestone_category": "adoption",
      "status": "in_progress",
      "target_completion_days": 30,
      "actual_completion_days": null,
      "started_date": "2025-09-15",
      "expected_completion_date": "2025-10-15",
      "days_remaining": 5,
      "progress_percentage": 0.83,
      "blocker": null
    },
    {
      "milestone_id": "ms_adoption_005",
      "milestone_name": "API integration active",
      "milestone_category": "adoption",
      "status": "overdue",
      "target_completion_days": 45,
      "actual_completion_days": 50,
      "expected_completion_date": "2025-10-01",
      "days_overdue": 9,
      "blocker": "Technical resource availability"
    }
  ],
  "category_progress": {
    "onboarding": {
      "completed": 5,
      "total": 5,
      "completion_rate": 1.0,
      "avg_days_to_complete": 20
    },
    "adoption": {
      "completed": 4,
      "total": 8,
      "completion_rate": 0.50,
      "avg_days_to_complete": 35
    }
  },
  "time_to_value": {
    "first_value_days": 7,
    "activation_days": 14,
    "full_adoption_days": null,
    "vs_target": {
      "first_value": "on_target",
      "activation": "ahead",
      "full_adoption": "in_progress"
    }
  },
  "blockers": [
    {
      "milestone_id": "ms_adoption_005",
      "blocker": "Technical resource availability",
      "severity": "medium",
      "age_days": 9,
      "recommended_action": "Assign dedicated technical CSM support"
    }
  ],
  "recommendations": [
    {
      "milestone": "API integration active",
      "current_status": "overdue",
      "recommended_actions": [
        "Schedule technical onboarding call",
        "Provide code samples and documentation",
        "Assign technical CSM for hands-on support"
      ],
      "estimated_acceleration": "5-7 days"
    }
  ],
  "success_probability": {
    "overall_success_likelihood": 0.85,
    "risk_factors": [
      "1 overdue milestone"
    ],
    "positive_factors": [
      "Onboarding completed on time",
      "High engagement rate",
      "Regular usage established"
    ]
  }
}
```

### Use Cases
- Monitor onboarding progress
- Identify and resolve blockers
- Predict time-to-value
- Automate milestone-based triggers
- Benchmark against targets

### Related Tools
- `manage_lifecycle_stages` - Stage transitions based on milestones
- `create_onboarding_plan` - Define milestones
- `optimize_time_to_value` - Accelerate milestone completion

---

## Tool 7: segment_by_value_tier

**Purpose:** Segment customers by value tier (Enterprise, Mid-Market, SMB, etc.).

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `segmentation_model` | string | No | Model: `arr_based` (default), `potential_based`, `strategic_value` |
| `arr_thresholds` | array | No | ARR thresholds (default: [10000, 50000, 100000, 250000]) |
| `include_expansion_potential` | boolean | No | Factor in expansion potential (default: true) |
| `include_strategic_value` | boolean | No | Consider strategic value (default: false) |
| `output_detail_level` | string | No | Detail: `summary`, `detailed` (default), `full` |

### Returns

```json
{
  "total_customers": 250,
  "total_arr": 18500000,
  "segmentation_model": "arr_based",
  "value_tiers": [
    {
      "tier_name": "Enterprise",
      "tier_description": "ARR > $250,000",
      "customer_count": 12,
      "percentage_of_customers": 4.8,
      "total_arr": 8400000,
      "percentage_of_arr": 45.4,
      "avg_arr_per_customer": 700000,
      "characteristics": {
        "avg_health_score": 88,
        "avg_tenure_months": 24,
        "avg_user_count": 250,
        "feature_adoption_rate": 0.85,
        "support_tier": "premium"
      },
      "engagement_strategy": {
        "csm_ratio": "1 CSM per 3-5 accounts",
        "touch_frequency": "weekly",
        "executive_engagement": "quarterly EBRs",
        "support_sla": "< 1 hour response",
        "success_programs": ["Strategic account planning", "Executive sponsorship"]
      },
      "expansion_pipeline": {
        "total_expansion_potential": 2100000,
        "avg_expansion_potential": 175000,
        "high_probability_expansions": 8
      }
    },
    {
      "tier_name": "Mid-Market",
      "tier_description": "$50,000 < ARR <= $250,000",
      "customer_count": 45,
      "percentage_of_customers": 18.0,
      "total_arr": 5850000,
      "percentage_of_arr": 31.6,
      "avg_arr_per_customer": 130000,
      "engagement_strategy": {
        "csm_ratio": "1 CSM per 15-20 accounts",
        "touch_frequency": "bi-weekly",
        "support_sla": "< 4 hours response"
      }
    },
    {
      "tier_name": "SMB",
      "tier_description": "ARR <= $50,000",
      "customer_count": 193,
      "percentage_of_customers": 77.2,
      "total_arr": 4250000,
      "percentage_of_arr": 23.0,
      "avg_arr_per_customer": 22000,
      "engagement_strategy": {
        "csm_ratio": "1 CSM per 50-75 accounts (pooled)",
        "touch_frequency": "monthly (automated + human)",
        "support_tier": "standard",
        "automation_level": "high"
      }
    }
  ],
  "pareto_analysis": {
    "top_20_percent_customers": 50,
    "top_20_percent_arr_contribution": "77%",
    "tier_distribution": "12 Enterprise + 38 Mid-Market"
  },
  "resource_allocation_recommendations": [
    {
      "tier": "Enterprise",
      "recommended_csm_count": 3,
      "current_csm_count": 2,
      "gap": 1,
      "priority": "critical"
    }
  ],
  "tier_health_summary": {
    "enterprise": {
      "avg_health": 88,
      "at_risk_count": 0,
      "expansion_ready_count": 8
    },
    "mid_market": {
      "avg_health": 76,
      "at_risk_count": 5,
      "expansion_ready_count": 12
    },
    "smb": {
      "avg_health": 68,
      "at_risk_count": 28,
      "expansion_ready_count": 15
    }
  },
  "recommended_actions": [
    "Hire 1 additional Enterprise CSM (covering 12 accounts with $8.4M ARR)",
    "Implement automated playbooks for SMB tier (193 accounts, $4.25M ARR)",
    "Focus expansion efforts on 8 Enterprise accounts (highest ROI)"
  ]
}
```

### Use Cases
- Resource allocation (CSM assignments)
- Pricing tier analysis
- Revenue concentration analysis
- Strategic account identification
- Scalability planning

### Related Tools
- `segment_customers` - Multi-dimensional segmentation
- `identify_expansion_opportunities` - Target high-value expansions
- `forecast_renewals` - Tier-based renewal forecasting

---

## Tool 8: analyze_engagement_patterns

**Purpose:** Analyze customer engagement patterns using ML to predict behavior and optimize strategies.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analysis_scope` | string | Yes | Scope: `single_customer`, `segment`, `all_customers` |
| `client_id` | string | No | Customer ID (required if scope is `single_customer`) |
| `segment_id` | string | No | Segment ID (required if scope is `segment`) |
| `analysis_period_days` | integer | No | Analysis window (default: 90, max: 365) |
| `pattern_categories` | array | No | Categories: `temporal`, `feature_usage`, `communication`, `support`, `all` (default) |
| `include_predictions` | boolean | No | Include predictive insights (default: true) |
| `min_pattern_confidence` | float | No | Minimum confidence threshold (default: 0.70, range: 0-1) |

### Returns

```json
{
  "analysis_id": "pattern_1728567890",
  "analysis_scope": {
    "scope_type": "segment",
    "segment_id": "seg_champion_001",
    "segment_name": "Champions"
  },
  "customers_analyzed": 78,
  "analysis_period": {
    "start_date": "2025-07-12",
    "end_date": "2025-10-10",
    "days": 90
  },
  "identified_patterns": [
    {
      "pattern_id": "ptn_001",
      "pattern_name": "Tuesday morning power users",
      "pattern_type": "temporal",
      "confidence": 0.85,
      "prevalence": 0.62,
      "description": "62% of high-value users are most active on Tuesday mornings (9-11am)",
      "business_impact": "high",
      "actionable_insight": "Schedule product updates, webinars, and important communications for Tuesday mornings"
    }
  ],
  "temporal_patterns": {
    "peak_activity_days": ["Tuesday", "Wednesday", "Thursday"],
    "peak_activity_hours": ["9-11am", "2-4pm"],
    "low_activity_periods": ["Friday afternoon", "Weekends"],
    "seasonal_trends": "15% usage increase in Q4 (budget planning season)"
  },
  "feature_usage_patterns": {
    "sequential_adoption": {
      "common_sequences": [
        ["Dashboard", "Reports", "Advanced Analytics", "API Integration"],
        ["Basic Setup", "Team Collaboration", "Automation", "Integrations"]
      ],
      "optimal_sequence": ["Dashboard", "Reports", "Advanced Analytics"],
      "avg_time_between_steps_days": 14
    },
    "feature_bundles": [
      {
        "bundle": ["Advanced Analytics", "Custom Reports", "Data Export"],
        "co_usage_rate": 0.78,
        "success_correlation": 0.82
      }
    ]
  },
  "communication_patterns": {
    "preferred_channels": {
      "email": 0.65,
      "in_app": 0.45,
      "webinar": 0.28,
      "direct_csm": 0.18
    },
    "optimal_frequency": {
      "newsletters": "weekly",
      "product_updates": "monthly",
      "csm_touchpoints": "bi-weekly"
    },
    "engagement_rate_by_content": {
      "how_to_guides": 0.72,
      "case_studies": 0.58,
      "product_updates": 0.45,
      "webinars": 0.38
    }
  },
  "support_patterns": {
    "common_issue_sequences": [
      "Initial setup questions → Advanced feature questions → Integration support"
    ],
    "time_to_resolution_trends": "Improving (avg 8h → 4h over 90 days)",
    "self_service_adoption": 0.65
  },
  "user_personas": [
    {
      "persona_name": "Data-driven analyst",
      "percentage": 35,
      "characteristics": [
        "Heavy dashboard and reporting usage",
        "Frequent data exports",
        "Low support ticket volume",
        "High satisfaction scores"
      ],
      "recommended_engagement": "Advanced analytics content, API documentation"
    },
    {
      "persona_name": "Collaborative team lead",
      "percentage": 40,
      "characteristics": [
        "High team collaboration features usage",
        "Frequent user invitations",
        "Regular CSM interactions",
        "Strong advocacy potential"
      ],
      "recommended_engagement": "Team success stories, best practices webinars"
    }
  ],
  "success_patterns": [
    {
      "pattern": "Early API integration",
      "success_metric": "retention_rate",
      "correlation": 0.78,
      "insight": "Customers who integrate API within first 30 days have 78% higher retention"
    }
  ],
  "risk_patterns": [
    {
      "pattern": "Usage decline >20% over 30 days",
      "risk_type": "churn",
      "early_warning_indicators": [
        "Decrease in weekly active users",
        "Decline in feature diversity",
        "Increase in support ticket severity"
      ],
      "probability_of_churn": 0.65,
      "recommended_intervention": "Immediate CSM outreach, usage audit, personalized re-engagement campaign"
    }
  ],
  "anomalies": [
    {
      "anomaly_type": "unusual_spike",
      "date": "2025-09-15",
      "description": "45% usage increase across segment",
      "likely_cause": "Product launch announcement (external event)",
      "action_required": false
    }
  ],
  "pattern_transitions": {
    "from_at_risk_to_healthy": {
      "common_interventions": [
        "CSM intervention call",
        "Personalized training session",
        "Feature showcase webinar"
      ],
      "success_rate": 0.62,
      "avg_transition_time_days": 28
    }
  },
  "predictive_insights": {
    "likely_expansion_candidates": 23,
    "likely_churn_candidates": 4,
    "optimal_intervention_timing": "14 days before predicted event",
    "confidence_score": 0.82
  },
  "engagement_optimization": [
    {
      "opportunity": "Optimize outreach timing",
      "current_state": "Outreach distributed evenly across week",
      "opportunity_state": "Concentrate during peak windows (Tue-Thu, 9-11am)",
      "potential_impact": "+25% engagement rate",
      "effort": "Low",
      "priority": "High"
    }
  ],
  "recommended_actions": [
    "Implement automated alerts for top 5 risk patterns",
    "Optimize communication timing (focus on Tue-Thu mornings)",
    "Deploy pattern-based customer segmentation",
    "Create power user recognition program",
    "Monitor and address anomalies within 48 hours"
  ]
}
```

### Use Cases
- Predictive churn prevention
- Optimize engagement timing
- Personalize customer journeys
- Identify success patterns
- Automate risk detection

### Related Tools
- `track_usage_engagement` - Provides raw engagement data
- `calculate_health_score` - Incorporate patterns into health scoring
- `segment_customers` - Create pattern-based segments

---

## Error Codes

All tools return standardized error responses:

| Code | Error | Description |
|------|-------|-------------|
| `400` | `INVALID_CLIENT_ID` | Client ID validation failed |
| `400` | `INVALID_PARAMETERS` | Parameter validation error |
| `404` | `CLIENT_NOT_FOUND` | Customer not found in database |
| `500` | `CALCULATION_ERROR` | Health score calculation failed |
| `500` | `DATA_RETRIEVAL_ERROR` | Failed to retrieve customer data |
| `503` | `INTEGRATION_ERROR` | External integration (Mixpanel, etc.) unavailable |

**Error Response Format:**
```json
{
  "status": "error",
  "error_code": "INVALID_CLIENT_ID",
  "error_message": "Invalid client_id: can only contain alphanumeric, underscore, hyphen",
  "details": {
    "parameter": "client_id",
    "value_provided": "cs_client@123",
    "validation_rule": "^[a-zA-Z0-9_-]+$"
  }
}
```

---

## Integration Requirements

### Mixpanel Integration (Optional)
Several tools integrate with Mixpanel for enhanced analytics:
- `track_usage_engagement`
- `track_feature_adoption`
- `analyze_engagement_patterns`

**Configuration:**
```bash
MIXPANEL_PROJECT_TOKEN=your-project-token
MIXPANEL_API_SECRET=your-api-secret
MCP_ENABLE_MIXPANEL=true
```

**Graceful Degradation:**
If Mixpanel is unavailable, tools use mock data with reduced functionality.

---

## Performance Considerations

**Response Times:**
- `track_usage_engagement`: 1-3 seconds
- `calculate_health_score`: < 1 second
- `segment_customers`: 2-5 seconds (depends on customer count)
- `track_feature_adoption`: 1-2 seconds
- `manage_lifecycle_stages`: < 1 second
- `track_adoption_milestones`: < 1 second
- `segment_by_value_tier`: 1-2 seconds
- `analyze_engagement_patterns`: 3-8 seconds (ML analysis)

**Rate Limits:**
- 100 requests per minute per client
- 1,000 requests per hour globally

**Caching:**
- Health scores cached for 1 hour
- Segment data cached for 4 hours
- Usage analytics cached for 30 minutes

---

## Best Practices

1. **Health Monitoring:**
   - Calculate health scores daily
   - Set up automated alerts for scores < 60
   - Review health trends weekly

2. **Segmentation:**
   - Re-segment monthly
   - Combine multiple segmentation types (value + health)
   - Use segments to personalize engagement

3. **Feature Adoption:**
   - Track adoption weekly
   - Correlate with retention data
   - Optimize onboarding based on adoption patterns

4. **Lifecycle Management:**
   - Automate stage transitions where possible
   - Define clear transition criteria
   - Monitor time spent in each stage

5. **Pattern Analysis:**
   - Run pattern analysis quarterly
   - Act on high-confidence patterns (>0.70)
   - Combine patterns with health scoring

---

## Related Documentation

- **Core System Tools:** `docs/api/CORE_TOOLS.md`
- **Onboarding Tools:** `docs/api/ONBOARDING_TRAINING_TOOLS.md`
- **Security:** `SECURITY.md`
- **Integration Setup:** `docs/integrations/MIXPANEL_SETUP.md`

---

**API Version:** 1.0.0
**Last Updated:** October 10, 2025
**Status:** ✅ Production Ready
