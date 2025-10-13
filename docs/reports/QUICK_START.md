# Customer Success MCP - Quick Start Guide

## First-Time Setup

### 1. Run the Onboarding Wizard

```bash
cd /Users/evanpaliotta/199os-customer-success-mcp
python -m src.tools.onboarding_wizard
```

The wizard will guide you through:
- ✅ System requirements check
- ✅ Security setup (encryption keys, Redis)
- ✅ Platform integrations (Zendesk, Salesforce, etc.)
- ✅ Health score configuration
- ✅ Database initialization
- ✅ Integration testing

**Estimated time**: 10-15 minutes

### 2. What You'll Need

#### Required
- Python 3.10+ installed
- PostgreSQL database running
- Redis server running

#### Optional (for integrations)
- Zendesk: subdomain, email, API token
- Intercom: access token
- Mixpanel: project token, API secret
- SendGrid: API key, from email
- Salesforce: username, password, security token
- HubSpot: access token
- And 6 more integrations...

### 3. After Setup

```bash
# Start the MCP server
python server.py

# Or skip validation during development
python server.py --skip-validation
```

## Troubleshooting

### Wizard Interrupted?
No problem! Just run it again - it will resume from where you left off:
```bash
python -m src.tools.onboarding_wizard
```

### Want to Reconfigure?
Delete the state file and start fresh:
```bash
rm ~/.config/cs-mcp/onboarding_state.json
python -m src.tools.onboarding_wizard
```

### Validation Errors?
Check the logs:
```bash
cat logs/startup_validation.log
```

### Manual Configuration
Edit `.env` file directly if needed:
```bash
nano .env
```

## Configuration Files

| File | Purpose | Example |
|------|---------|---------|
| `.env` | Environment variables | `DATABASE_URL=postgresql://...` |
| `~/.config/cs-mcp/onboarding_state.json` | Wizard progress | Auto-generated |
| `~/.config/cs-mcp/setup_report.json` | Setup summary | Auto-generated |
| `logs/startup_validation.log` | Validation results | Auto-generated |

## Security Best Practices

✅ **DO**:
- Use strong master password (16+ characters)
- Keep `.env` file secure (chmod 600)
- Use auto-generated encryption keys
- Enable all security validations

❌ **DON'T**:
- Commit `.env` to version control
- Share master password
- Disable security validations in production
- Use default/weak passwords

## Next Steps

1. **Test the setup**: Register a sample customer
2. **Configure team**: Add team members
3. **Set up alerts**: Configure churn alerts
4. **Import data**: Bulk import existing customers
5. **Enable features**: Turn on advanced features

## Support

- Documentation: `docs/`
- User Guide: `docs/USER_GUIDE.md`
- API Reference: `docs/API_REFERENCE.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`

---

**Ready to go!** Run the wizard and you'll be up and running in 10-15 minutes.
