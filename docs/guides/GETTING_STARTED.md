# Getting Started with Customer Success MCP Server

**Quick guide to building the 199OS Customer Success MCP Server**

---

## 📚 Step 1: Read the Documentation

### Essential Reading (In Order)

1. **Process Organization** (15 minutes)
   - File: `docs/prompts/CUSTOMER_SUCCESS_MCP_PROCESSES.md`
   - Purpose: Understand the 49 processes and how they're categorized
   - What you'll learn: The 7 tool categories and what each process does

2. **Implementation Prompt** (60 minutes)
   - File: `docs/prompts/CUSTOMER_SUCCESS_MCP_IMPLEMENTATION_PROMPT.md`
   - Purpose: Complete step-by-step implementation guide
   - What you'll learn: Exact file structure, code patterns, and how to build everything

3. **Reference Implementation** (30 minutes)
   - Directory: `/Users/evanpaliotta/199os-sales-mcp`
   - Purpose: See working example of MCP server architecture
   - What you'll learn: Code patterns, security features, agent integration

---

## 🚀 Step 2: Environment Setup

### Prerequisites

```bash
# Verify Python version (3.10+ required)
python --version

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**Required Environment Variables:**
- `MASTER_PASSWORD` - For credential encryption (generate with: `openssl rand -base64 32`)
- `ENCRYPTION_KEY` - For data encryption (generate with: `openssl rand -hex 32`)
- Platform API keys (Zendesk, Intercom, Mixpanel, etc.)

---

## 🛠️ Step 3: Build the Core System

### Phase 1: Entry Points (Day 1)

1. **Create server.py**
   - Follow section "STEP 2: CORE ENTRY POINTS" in implementation prompt
   - This is your main entry point
   - Imports and runs the MCP server

2. **Create src/initialization.py**
   - Centralizes all startup logic
   - Sets up logging, MCP server, agents, and tools
   - Critical for system organization

3. **Test the skeleton:**
   ```bash
   python server.py
   # Should start without errors (but won't do much yet)
   ```

### Phase 2: Security Layer (Day 2)

```bash
# Copy security module from Sales MCP
cp -r /Users/evanpaliotta/199os-sales-mcp/src/security /Users/evanpaliotta/199os-customer-success-mcp/src/

# Security includes:
# - credential_manager.py (encrypted storage)
# - encryption.py (AES-256)
# - input_validation.py (sanitization)
# - safe_file_operations.py (secure file I/O)
```

**IMPORTANT:** Use `SafeFileOperations` for ALL file operations in your tools.

### Phase 3: Agent Systems (Day 3)

```bash
# Copy agent modules from Sales MCP
cp -r /Users/evanpaliotta/199os-sales-mcp/src/agents /Users/evanpaliotta/199os-customer-success-mcp/src/
```

Update class names:
- `EnhancedSalesAgent` → `EnhancedCSAgent`
- Context references from "sales" to "customer success"

### Phase 4: Database Models (Day 4)

Create data models in `src/models/`:
- `customer_models.py` - Customer accounts, health scores
- `onboarding_models.py` - Onboarding plans, milestones
- `health_models.py` - Health scoring, segments
- `support_models.py` - Tickets, KB articles
- `renewal_models.py` - Renewals, contracts
- `feedback_models.py` - Surveys, NPS, sentiment

Use Pydantic `BaseModel` for all models (see implementation prompt for examples).

---

## 🔧 Step 4: Implement Tools (The Core Work)

### Tool Implementation Order (by priority)

#### Week 1: Core + Onboarding (Foundation)
1. **src/tools/core_system_tools.py**
   - `register_client` - Client registration
   - `get_client_overview` - Client data retrieval
   - System configuration tools

2. **src/tools/onboarding_training_tools.py** (Processes 79-86)
   - `create_onboarding_plan` - Process 79
   - `activate_onboarding_automation` - Process 80
   - `deliver_training_session` - Process 81
   - `manage_certification_program` - Process 82
   - `optimize_onboarding_process` - Process 83
   - `map_customer_journey` - Process 84
   - `optimize_time_to_value` - Process 85
   - `track_onboarding_progress` - Process 86

#### Week 2: Health & Retention (High Value)
3. **src/tools/health_segmentation_tools.py** (Processes 87-94)
   - Health scoring, engagement analytics, segmentation

4. **src/tools/retention_risk_tools.py** (Processes 95-101)
   - Churn prediction, retention campaigns, risk scoring

#### Week 3: Engagement & Support (Customer-Facing)
5. **src/tools/communication_engagement_tools.py** (Processes 102-107)
   - Email campaigns, EBRs, advocacy programs

6. **src/tools/support_selfservice_tools.py** (Processes 108-113)
   - Ticket routing, KB management, portal automation

#### Week 4: Revenue & Intelligence (Revenue Impact)
7. **src/tools/expansion_revenue_tools.py** (Processes 114-121)
   - Upsell, cross-sell, renewals, CLV optimization

8. **src/tools/feedback_intelligence_tools.py** (Processes 122-127)
   - Feedback collection, sentiment analysis, product insights

### Tool Implementation Pattern

Every tool follows this pattern:

```python
def register_tools(mcp):
    """Register all tools in this category"""

    @mcp.tool()
    async def tool_name(
        ctx: Context,
        client_id: str,
        param1: str,
        param2: int = 10
    ) -> Dict[str, Any]:
        """
        Process XX: Tool Name

        Description of what this tool does.

        Args:
            client_id: Customer identifier
            param1: Description
            param2: Description

        Returns:
            Result dictionary with status and data
        """
        try:
            # Validate input
            try:
                client_id = validate_client_id(client_id)
            except ValidationError as e:
                return {"status": "failed", "error": f"Invalid client_id: {str(e)}"}

            # Log action
            await ctx.info(f"Performing action for client: {client_id}")

            # Tool logic here
            result = {
                "status": "success",
                "data": {}
            }

            # Log success
            logger.info("action_completed", client_id=client_id)

            return result

        except Exception as e:
            logger.error("action_failed", error=str(e))
            return {"status": "failed", "error": str(e)}
```

---

## 🔌 Step 5: Platform Integrations

### Priority Order

1. **Zendesk** (Support tickets) - Day 1
2. **Intercom** (Customer messaging) - Day 2
3. **Mixpanel** (Product analytics) - Day 3
4. **SendGrid** (Email delivery) - Day 4
5. **Salesforce** (CRM sync) - Day 5
6. Others as needed

### Integration Template

Create `src/integrations/{platform}_client.py`:

```python
class PlatformClient:
    """Platform API client"""

    def __init__(self):
        self.api_key = os.getenv("PLATFORM_API_KEY")
        if not self.api_key:
            logger.warning("Platform not configured")
            self.client = None
        else:
            self.client = PlatformSDK(api_key=self.api_key)

    def method_name(self, args):
        """Method description"""
        if not self.client:
            return {"error": "Platform not configured"}

        try:
            # API call
            result = self.client.api_method(args)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error("api_call_failed", error=str(e))
            return {"error": str(e)}
```

---

## 🧪 Step 6: Testing

### Create Test Files

For each tool file, create corresponding test file in `tests/unit/`:

```python
# tests/unit/test_onboarding_tools.py

import pytest
from unittest.mock import Mock, AsyncMock
from src.tools import onboarding_training_tools

@pytest.mark.asyncio
async def test_create_onboarding_plan():
    """Test onboarding plan creation"""
    ctx = Mock()
    ctx.info = AsyncMock()

    result = await create_onboarding_plan(
        ctx=ctx,
        client_id="cs_test_123",
        customer_goals=["Goal 1", "Goal 2"],
        product_tier="professional"
    )

    assert result["status"] == "success"
    assert "onboarding_plan" in result
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_onboarding_tools.py

# Run with coverage
pytest --cov=src
```

---

## 📊 Step 7: Verification Checklist

Before moving to production:

### Functionality ✅
- [ ] All 49 tools implemented and working
- [ ] All 8 integrations connected and tested
- [ ] Security features active (encryption, validation)
- [ ] Agents initialized and functional
- [ ] Database models created and validated

### Testing ✅
- [ ] Unit tests pass for all tool categories
- [ ] Integration tests pass for all platforms
- [ ] Manual testing completed for key workflows
- [ ] Error handling tested
- [ ] Edge cases covered

### Security ✅
- [ ] Input validation on all tools
- [ ] Credentials encrypted
- [ ] SafeFileOperations used everywhere
- [ ] Audit logging active
- [ ] Rate limiting configured

### Documentation ✅
- [ ] README.md complete
- [ ] API documentation created
- [ ] Deployment guide written
- [ ] Integration setup guides complete

---

## 🚢 Step 8: Deployment

### Development Environment

```bash
# Run locally
python server.py
```

### Docker Deployment

```bash
# Build image
docker build -t 199os-cs-mcp .

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f customer-success-mcp
```

### Production Deployment

See `docs/guides/DEPLOYMENT_GUIDE.md` (to be created following implementation prompt)

---

## 🎯 Success Criteria

You're ready for production when:

1. ✅ All 49 processes implemented
2. ✅ All tests passing
3. ✅ Security audit complete
4. ✅ Documentation complete
5. ✅ Docker deployment working
6. ✅ Monitoring and logging active
7. ✅ At least 3 platform integrations working

---

## 📞 Getting Help

### Resources

1. **Implementation Prompt:** `docs/prompts/CUSTOMER_SUCCESS_MCP_IMPLEMENTATION_PROMPT.md`
2. **Process Reference:** `docs/prompts/CUSTOMER_SUCCESS_MCP_PROCESSES.md`
3. **Sales MCP Example:** `/Users/evanpaliotta/199os-sales-mcp`

### Common Issues

**Issue:** Import errors
**Solution:** Check `src/__init__.py` files exist in all directories

**Issue:** Validation errors
**Solution:** Use `validate_client_id()` from `src.security.input_validation`

**Issue:** File operation failures
**Solution:** Use `SafeFileOperations` instead of built-in file operations

**Issue:** Integration not working
**Solution:** Verify API keys in `.env` and check integration client initialization

---

## 🎓 Learning Path

### For Beginners (8 weeks)
- Week 1-2: Study implementation prompt and Sales MCP
- Week 3-4: Implement core + onboarding tools
- Week 5-6: Implement remaining tools
- Week 7: Testing and integration
- Week 8: Documentation and deployment

### For Experienced Developers (4 weeks)
- Week 1: Core system + 3 tool categories
- Week 2: Remaining 4 tool categories
- Week 3: Integrations + testing
- Week 4: Documentation + deployment

---

**Good luck building your Customer Success MCP Server! 🚀**

**Questions?** Check the implementation prompt first - it has 2,850 lines of detailed guidance.

**Last Updated:** October 9, 2025
