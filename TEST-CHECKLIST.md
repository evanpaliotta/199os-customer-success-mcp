# MCP Server Testing Checklist

## 🚀 Quick Start
```bash
cd ~/199os-customer-success-mcp && ./quick-test.sh
```

---

## Phase 1: Core Infrastructure ✅

### Must Pass Before Continuing

- [ ] **health_check**
  - Params: `{"ctx": {}, "detail_level": "summary"}`
  - Expected: `status: "healthy"`, no exceptions
  - Tests: Server initialization, basic connectivity

- [ ] **system_metrics**
  - Params: `{"ctx": {}, "hours": 1, "detail_level": "summary"}`
  - Expected: CPU, memory, disk metrics returned
  - Tests: System monitoring capabilities

- [ ] **error_summary**
  - Params: `{"ctx": {}, "detail_level": "summary"}`
  - Expected: Error count and summaries (even if zero)
  - Tests: Error logging and aggregation

- [ ] **performance_summary**
  - Params: `{"ctx": {}, "hours": 1, "detail_level": "summary"}`
  - Expected: Performance metrics and statistics
  - Tests: Performance tracking system

**Status:** ⬜ Not Started | ⏳ In Progress | ✅ Complete

---

## Phase 2: Standalone Tools (~60 tools)

### Health & Segmentation (13 tools)

- [ ] `analyze_health_score`
- [ ] `segment_customer_health`
- [ ] `identify_at_risk_accounts`
- [ ] `predict_churn_probability`
- [ ] `calculate_health_trends`
- [ ] `compare_health_segments`
- [ ] `generate_health_report`
- [ ] `set_health_thresholds`
- [ ] `track_health_history`
- [ ] `analyze_health_factors`
- [ ] `benchmark_health_scores`
- [ ] `detect_health_anomalies`
- [ ] `prioritize_health_actions`

### Churn Prevention (8 tools)

- [ ] `identify_churn_risk_factors`
- [ ] `create_retention_strategy`
- [ ] `calculate_retention_metrics`
- [ ] `predict_renewal_probability`
- [ ] `track_churn_trends`
- [ ] `analyze_win_back_opportunities`
- [ ] `measure_retention_roi`
- [ ] `optimize_retention_tactics`

### Usage Analytics (7 tools)

- [ ] `track_product_usage`
- [ ] `analyze_feature_adoption`
- [ ] `measure_engagement_metrics`
- [ ] `identify_usage_patterns`
- [ ] `calculate_usage_scores`
- [ ] `detect_usage_anomalies`
- [ ] `benchmark_usage_metrics`

### Customer Journey (9 tools)

- [ ] `map_customer_journey`
- [ ] `track_journey_milestones`
- [ ] `identify_journey_bottlenecks`
- [ ] `analyze_journey_performance`
- [ ] `optimize_journey_stages`
- [ ] `measure_journey_velocity`
- [ ] `predict_journey_outcomes`
- [ ] `personalize_journey_paths`
- [ ] `benchmark_journey_metrics`

### Account Health (11 tools)

- [ ] `assess_account_health`
- [ ] `track_health_indicators`
- [ ] `calculate_health_scores`
- [ ] `identify_health_trends`
- [ ] `predict_health_trajectory`
- [ ] `compare_account_health`
- [ ] `generate_health_alerts`
- [ ] `measure_health_impact`
- [ ] `optimize_health_metrics`
- [ ] `benchmark_health_standards`
- [ ] `visualize_health_dashboard`

### Engagement (6 tools)

- [ ] `track_engagement_activity`
- [ ] `measure_engagement_quality`
- [ ] `analyze_engagement_patterns`
- [ ] `optimize_engagement_strategy`
- [ ] `predict_engagement_trends`
- [ ] `benchmark_engagement_metrics`

### Success Planning (5 tools)

- [ ] `create_success_plan`
- [ ] `track_success_milestones`
- [ ] `measure_success_outcomes`
- [ ] `optimize_success_strategies`
- [ ] `benchmark_success_metrics`

**Status:** ⬜ Not Started | ⏳ In Progress | ✅ Complete

---

## Phase 3: Process Integration (17 tools)

### Requires Process Execution First

- [ ] `execute_customer_onboarding`
- [ ] `execute_adoption_acceleration`
- [ ] `execute_expansion_opportunity`
- [ ] `execute_renewal_management`
- [ ] `execute_churn_prevention`
- [ ] `execute_health_monitoring`
- [ ] `execute_engagement_campaign`
- [ ] `execute_success_review`
- [ ] `execute_risk_mitigation`
- [ ] `execute_value_realization`
- [ ] `execute_advocacy_development`
- [ ] `execute_feedback_collection`
- [ ] `execute_training_program`
- [ ] `execute_escalation_management`
- [ ] `execute_strategic_planning`
- [ ] `execute_performance_analysis`
- [ ] `execute_optimization_cycle`

**Status:** ⬜ Not Started | ⏳ In Progress | ✅ Complete

---

## 🐛 Known Issues

### Issue: ctx.info() takes 1 positional argument
**Solution:** Changed all logging from Django-style to Python logging-style
**Status:** ✅ Fixed in health_segmentation_tools.py (25 calls)
**To Verify:** All Phase 1 and Phase 2 tools should pass

### Issue: MCP connection drops on server restart
**Solution:** Use MCP Inspector for development, Claude Code for integration
**Status:** ✅ Workflow documented in TESTING.md

---

## 📊 Testing Progress

### Summary
- Phase 1: ⬜ 0/4 complete
- Phase 2: ⬜ 0/59 complete
- Phase 3: ⬜ 0/17 complete
- **Total:** ⬜ 0/80 tools tested

### Last Updated
Date: 2025-10-29
Tester: [Your Name]
Notes: Initial checklist created

---

## 🎯 Success Criteria

- [ ] All Phase 1 tools pass
- [ ] 90%+ of Phase 2 tools pass (some may be incomplete features)
- [ ] All Phase 3 tools pass after process execution
- [ ] No ctx.info() argument errors
- [ ] Response times under 2 seconds for simple queries
- [ ] Proper error messages (not stack traces) for invalid inputs

---

## 💡 Tips

1. **Test in order** - Phase 1 → 2 → 3
2. **Use Inspector** - Fastest feedback loop
3. **Document failures** - Save error messages
4. **Group similar tools** - Test all health tools together
5. **Take breaks** - Don't burn out on 80 tools
6. **Update this file** - Check off as you go
