# Onboarding & Training Tools - Quick Reference Guide

## Tool Overview

| Tool | Process | Purpose | Key Features |
|------|---------|---------|--------------|
| `create_onboarding_plan` | 79 | Create customized onboarding plans | Milestones, timelines, success criteria |
| `activate_onboarding_automation` | 80 | Automate onboarding workflows | 8 workflows, triggers, notifications |
| `deliver_training_session` | 81 | Deliver training with verification | Multiple formats, assessments, certification |
| `manage_certification_program` | 82 | Manage certifications | 4 levels, tracking, credentials |
| `optimize_onboarding_process` | 83 | Improve onboarding effectiveness | Bottlenecks, benchmarks, recommendations |
| `map_customer_journey` | 84 | Visualize customer journey | Stages, touchpoints, milestones |
| `optimize_time_to_value` | 85 | Reduce time-to-value | Strategies, measurement, benchmarks |
| `track_onboarding_progress` | 86 | Track onboarding metrics | Real-time progress, risks, predictions |

---

## Tool 1: create_onboarding_plan

**Purpose:** Create customized onboarding plan with milestones and timelines

**Parameters:**
```python
client_id: str                          # Required - Customer ID
customer_goals: List[str]               # Required - Success goals
product_tier: str = "professional"      # starter|standard|professional|enterprise
team_size: int = 10                     # Number of users to onboard
technical_complexity: str = "medium"    # low|medium|high
timeline_weeks: int = 4                 # 1-12 weeks
success_criteria: List[str] = None      # Custom criteria (auto-generated if None)
```

**Returns:**
- Onboarding plan with 4-6 milestones
- Timeline and dates
- Success metrics
- Recommendations

**Example:**
```python
result = await create_onboarding_plan(
    ctx=context,
    client_id="cs_1696800000_acme",
    customer_goals=["Automate workflows", "Train 15 users"],
    product_tier="professional",
    team_size=15,
    technical_complexity="medium",
    timeline_weeks=4
)
```

---

## Tool 2: activate_onboarding_automation

**Purpose:** Activate automated workflows for onboarding delivery

**Parameters:**
```python
client_id: str                              # Required - Customer ID
plan_id: str                                # Required - Onboarding plan ID
automation_triggers: List[str] = None       # Trigger events (auto if None)
notification_preferences: Dict = None       # Notification settings (auto if None)
```

**Returns:**
- 8 automated workflows
- Progress tracking config
- Quality assurance checks
- Escalation rules

**Example:**
```python
result = await activate_onboarding_automation(
    ctx=context,
    client_id="cs_1696800000_acme",
    plan_id="onb_cs_1696800000_acme_1728576000",
    automation_triggers=["milestone_completion", "training_completion"]
)
```

---

## Tool 3: deliver_training_session

**Purpose:** Deliver training with engagement tracking and certification

**Parameters:**
```python
client_id: str                          # Required - Customer ID
training_module_id: str                 # Required - Module to deliver
session_format: str = "live_webinar"    # Format type
attendee_emails: List[str] = None       # Attendee list (auto if None)
session_date: str = None                # Date (YYYY-MM-DD HH:MM)
duration_minutes: int = 90              # 15-480 minutes
recording_enabled: bool = True          # Enable recording
```

**Valid Formats:**
- `live_webinar` - Live online session
- `self_paced` - Self-paced online
- `one_on_one` - Individual coaching
- `workshop` - Interactive workshop
- `video` - Pre-recorded video
- `documentation` - Written materials

**Returns:**
- Training session details
- Attendee results and scores
- Engagement metrics
- Certifications issued

**Example:**
```python
result = await deliver_training_session(
    ctx=context,
    client_id="cs_1696800000_acme",
    training_module_id="train_getting_started_101",
    session_format="live_webinar",
    attendee_emails=["user1@acme.com", "user2@acme.com"],
    duration_minutes=90,
    recording_enabled=True
)
```

---

## Tool 4: manage_certification_program

**Purpose:** Manage customer education and certification program

**Parameters:**
```python
client_id: str                      # Required - Customer ID
action: str = "list"                # list|create|issue|revoke|track
certification_level: str = None     # basic|intermediate|advanced|expert
user_email: str = None              # For individual actions
module_ids: List[str] = None        # Required modules
```

**Certification Levels:**
1. **basic** - Platform Fundamentals (6 hours, 75% pass)
2. **intermediate** - Professional (12 hours, 80% pass)
3. **advanced** - Expert (20 hours, 85% pass)
4. **expert** - Master (30 hours, 90% pass)

**Returns:**
- Certification programs
- User certifications
- Program statistics
- Tracking data

**Example:**
```python
# List all certifications
result = await manage_certification_program(
    ctx=context,
    client_id="cs_1696800000_acme",
    action="list"
)

# Issue certificate
result = await manage_certification_program(
    ctx=context,
    client_id="cs_1696800000_acme",
    action="issue",
    certification_level="basic",
    user_email="user1@acme.com"
)
```

---

## Tool 5: optimize_onboarding_process

**Purpose:** Analyze and improve onboarding effectiveness

**Parameters:**
```python
analysis_period_days: int = 90      # 7-365 days to analyze
min_completed_onboardings: int = 5  # Minimum sample size
include_in_progress: bool = True    # Include ongoing onboardings
```

**Returns:**
- Success metrics and KPIs
- Time-to-value analysis
- Bottleneck identification
- 6 optimization recommendations
- Performance benchmarks
- Implementation roadmap

**Example:**
```python
result = await optimize_onboarding_process(
    ctx=context,
    analysis_period_days=90,
    min_completed_onboardings=10,
    include_in_progress=True
)
```

---

## Tool 6: map_customer_journey

**Purpose:** Visualize and optimize customer journey across lifecycle

**Parameters:**
```python
client_id: str                          # Required - Customer ID
journey_stage: str = None               # Filter: onboarding|adoption|expansion|renewal
include_touchpoints: bool = True        # Include all touchpoints
include_milestones: bool = True         # Include milestone tracking
include_experience_metrics: bool = True # Include metrics and sentiment
```

**Returns:**
- 4 journey stages (onboarding → adoption → expansion → renewal)
- All customer touchpoints
- Journey milestones
- Experience metrics (NPS, CSAT, effort score)
- Optimization opportunities
- Intervention points

**Example:**
```python
result = await map_customer_journey(
    ctx=context,
    client_id="cs_1696800000_acme",
    include_touchpoints=True,
    include_milestones=True,
    include_experience_metrics=True
)
```

---

## Tool 7: optimize_time_to_value

**Purpose:** Reduce time required to achieve customer value

**Parameters:**
```python
client_id: str                          # Required - Customer ID
current_time_to_value_days: int = None  # Auto-detected if None
target_time_to_value_days: int = None   # Defaults to 21 days
include_benchmarks: bool = True         # Include industry benchmarks
```

**Returns:**
- Time-to-value analysis
- 6 optimization strategies with time savings
- Benchmarks (industry, company, tier)
- 3-phase improvement plan
- Value milestone definitions
- Measurement framework

**Example:**
```python
result = await optimize_time_to_value(
    ctx=context,
    client_id="cs_1696800000_acme",
    current_time_to_value_days=24,
    target_time_to_value_days=21,
    include_benchmarks=True
)
```

---

## Tool 8: track_onboarding_progress

**Purpose:** Real-time tracking of onboarding progress and metrics

**Parameters:**
```python
client_id: str                      # Required - Customer ID
plan_id: str = None                 # Specific plan (uses active if None)
include_team_metrics: bool = True   # Team performance metrics
include_risk_analysis: bool = True  # Risk assessment and blockers
```

**Returns:**
- Overall progress (completion %)
- Milestone status (4 milestones)
- Training metrics (completion, scores)
- Engagement metrics (usage, adoption)
- Team collaboration metrics
- Success criteria tracking
- Risk analysis
- Predictive insights (success likelihood)
- Performance comparison

**Example:**
```python
result = await track_onboarding_progress(
    ctx=context,
    client_id="cs_1696800000_acme",
    plan_id="onb_cs_1696800000_acme_1728576000",
    include_team_metrics=True,
    include_risk_analysis=True
)
```

---

## Common Response Structure

All tools return this consistent structure:

```python
{
    'status': 'success',                    # 'success' or 'failed'
    'message': 'Operation completed...',    # Human-readable message
    'data_field_name': {...},               # Primary data (varies by tool)
    'metrics': {...},                       # Relevant metrics
    'insights': {...},                      # Key insights and analysis
    'recommendations': [...],               # Action recommendations
    'next_steps': [...]                     # Suggested next actions
}
```

**Error Response:**
```python
{
    'status': 'failed',
    'error': 'Error description...'
}
```

---

## Common Patterns

### 1. Client ID Validation
All tools validate client_id format:
```python
try:
    client_id = validate_client_id(client_id)
except ValidationError as e:
    return {'status': 'failed', 'error': f'Invalid client_id: {str(e)}'}
```

### 2. Parameter Validation
Each tool validates its parameters:
```python
if timeline_weeks < 1 or timeline_weeks > 12:
    return {'status': 'failed', 'error': 'timeline_weeks must be between 1 and 12'}
```

### 3. Logging Pattern
All operations are logged:
```python
logger.info("operation_name", client_id=client_id, key_metric=value)
logger.error("operation_failed", error=str(e), client_id=client_id)
```

### 4. Try-Except Wrapper
All tools use comprehensive error handling:
```python
try:
    # Tool implementation
    return {'status': 'success', ...}
except Exception as e:
    logger.error("tool_failed", error=str(e))
    return {'status': 'failed', 'error': f'Failed: {str(e)}'}
```

---

## Integration with MCP Server

### Registration
```python
# In src/tools/__init__.py
from src.tools import onboarding_training_tools

def register_all_tools(mcp):
    onboarding_training_tools.register_tools(mcp)
    # ... other tool categories
```

### Server Usage
```python
# In server.py
from src.initialization import initialize_all

mcp, adaptive_agent, enhanced_agent, logger = initialize_all()

# All tools are now registered and available
if __name__ == "__main__":
    mcp.run()
```

---

## Key Metrics & KPIs

### Onboarding Success Metrics
- **Completion Rate:** Target >95%
- **Time-to-Value:** Target <21 days
- **Training Completion:** Target >85%
- **Customer Satisfaction:** Target >4.5/5
- **On-Time Completion:** Target >80%

### Training Metrics
- **Attendance Rate:** Target >80%
- **Pass Rate:** Target >85%
- **Certification Rate:** Target >75%
- **Engagement Score:** Target >0.8

### Journey Metrics
- **Health Score:** Target >75/100
- **NPS Score:** Target >50
- **Feature Adoption:** Target >70%
- **Retention Rate:** Target >90%

---

## File Location

**Full Path:** `/Users/evanpaliotta/199os-customer-success-mcp/src/tools/onboarding_training_tools.py`

**Import Statement:**
```python
from src.tools import onboarding_training_tools
```

**Direct Tool Import:**
```python
from src.tools.onboarding_training_tools import (
    create_onboarding_plan,
    activate_onboarding_automation,
    deliver_training_session,
    manage_certification_program,
    optimize_onboarding_process,
    map_customer_journey,
    optimize_time_to_value,
    track_onboarding_progress
)
```

---

**Ready for production use!** 🚀
