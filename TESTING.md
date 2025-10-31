# MCP Server Testing Guide

## 🎯 Quick Start (What You Actually Want)

### Option 1: Automated Testing (Fastest)
```bash
cd /Users/evanpaliotta/199os-customer-success-mcp
./quick-test.sh
```
This script automatically:
- Kills any old server instances
- Clears Python cache
- Starts the MCP Inspector
- Opens your browser with the testing interface

### Option 2: Manual Testing Steps
```bash
cd /Users/evanpaliotta/199os-customer-success-mcp
./dev-test.sh
```
Then open http://localhost:5173 in your browser.

---

## 🚨 The Problem We're Solving

### Why Testing Was Frustrating:
1. **Connection Hell**: Claude Code doesn't reconnect reliably to MCP servers
2. **Restart Cycle**: Code change → Restart Claude Code → Paste history → Hope it connects → Repeat
3. **Time Waste**: 2+ minutes per test cycle
4. **Inconsistent**: Sometimes connects, sometimes doesn't
5. **No Clear Errors**: Just "Not connected" with no explanation

### The Solution:
**Use MCP Inspector for development testing, Claude Code only for final integration testing.**

---

## 📋 Testing Workflow

### Phase 1: Core Infrastructure (4 tools)
Test these first to ensure basic functionality:

1. `health_check` - Verify server is responding
2. `system_metrics` - Check resource usage works
3. `error_summary` - Confirm error logging works
4. `performance_summary` - Validate analytics work

**Test in Inspector:**
```
Tool: health_check
Params: {"ctx": {}, "detail_level": "summary"}
Expected: Status "healthy", no errors
```

### Phase 2: Standalone Tools (~60 tools)
Test all tools that don't require process data.

**Categories:**
- Health & Segmentation (13 tools)
- Churn Prevention (8 tools)
- Usage Analytics (7 tools)
- Customer Journey (9 tools)
- Account Health (11 tools)
- Engagement (6 tools)
- Success Planning (5 tools)

### Phase 3: Process Integration (17 tools)
Test tools that depend on process execution state.

---

## 🔧 Development Workflow

### When You Make Code Changes:

**In MCP Inspector:**
1. Make your code change
2. Click "Reconnect" button (top-right)
3. Re-test the tool
4. Repeat

**No more:**
- ❌ Restarting Claude Code
- ❌ Reopening terminals
- ❌ Pasting conversation history
- ❌ Praying for connections

### When to Use Claude Code:
- ✅ Final integration testing
- ✅ Testing AI-driven workflows
- ✅ Testing tool sequences
- ✅ User acceptance testing

**For bug fixes and individual tool testing: Always use Inspector**

---

## 🐛 Common Issues & Fixes

### Issue: "ctx.info() takes 1 positional argument but 2 were given"
**Cause:** Old logging syntax (Django-style) vs new syntax (Python logging-style)

**Fix:**
```python
# OLD (breaks)
ctx.info("message", extra_data=data)

# NEW (works)
ctx.info("message", extra={"data": data})
```

### Issue: MCP Inspector shows "Connection Failed"
**Fix:**
```bash
# Kill any orphaned server processes
pkill -f "199os-customer-success-mcp"

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Restart inspector
./dev-test.sh
```

### Issue: Claude Code won't connect to MCP
**Fix:**
```bash
# Kill orphaned server
pkill -f "199os-customer-success-mcp"

# Quit Claude Code completely (Cmd+Q)
# Restart Claude Code

# If still not working: Use Inspector instead
```

---

## 📊 Testing Checklist

### Before Testing Session:
- [ ] Killed any orphaned server processes: `pkill -f "199os-customer-success-mcp"`
- [ ] Cleared Python cache: `./clear-cache.sh` (if exists) or manual cleanup
- [ ] Have testing script ready: `./quick-test.sh`

### During Testing:
- [ ] Using MCP Inspector (not Claude Code) for individual tool tests
- [ ] Testing tools in order (Phase 1 → Phase 2 → Phase 3)
- [ ] Documenting failures in a file (not just telling Claude)
- [ ] Using "Reconnect" button after code changes

### After Testing:
- [ ] All Phase 1 tools passing
- [ ] Documented any failing tools with exact error messages
- [ ] Ready for Phase 2 or integration testing

---

## 🎬 Video Walkthrough (If You Were Recording)

1. **Start**: `cd /Users/evanpaliotta/199os-customer-success-mcp && ./quick-test.sh`
2. **Browser Opens**: MCP Inspector at localhost:5173
3. **Test Tool**: Click tool → Fill params → "Call Tool"
4. **See Response**: Green = pass, Red = error details
5. **Fix Code**: Edit Python file
6. **Reconnect**: Click "Reconnect" button
7. **Re-test**: Instant feedback
8. **Repeat**: 2-second cycle, not 2-minute cycle

---

## 📞 Quick Reference Commands

```bash
# Start testing
cd ~/199os-customer-success-mcp && ./quick-test.sh

# Kill orphaned servers
pkill -f "199os-customer-success-mcp"

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} + && find . -type f -name "*.pyc" -delete

# Check server logs
tail -f logs/startup_validation.log

# Manually start inspector
npx @modelcontextprotocol/inspector /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 server.py
```

---

## 🎯 Success Criteria

You know testing is working well when:
1. ✅ You can test a tool change in under 10 seconds
2. ✅ You never restart Claude Code for bug fixes
3. ✅ You see exact error messages immediately
4. ✅ You can test 20+ tools in 5 minutes
5. ✅ Connection issues are eliminated

---

## 🚀 Future Self Instructions

**When you come back to test this MCP server:**

1. Open terminal
2. Run: `cd ~/199os-customer-success-mcp && cat TESTING.md | head -20`
3. Follow the "Quick Start" section
4. Or tell Claude: "I want to test my MCP server, read TESTING.md"

**That's it. No more frustration.**
