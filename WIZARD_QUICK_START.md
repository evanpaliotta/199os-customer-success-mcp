# Customer Success MCP - Onboarding Wizard Quick Start

## Installation

```bash
# Install required dependencies
pip install rich cryptography psycopg2-binary redis pydantic sqlalchemy structlog

# Navigate to project directory
cd /path/to/199os-customer-success-mcp
```

## Running the Wizard

```bash
# Method 1: Direct execution
python src/tools/onboarding_wizard.py

# Method 2: Module execution (recommended)
python -m src.tools.onboarding_wizard

# Method 3: From anywhere (if installed)
cs-mcp-wizard
```

## What to Prepare

Before running the wizard, have these credentials ready:

### Required
- **PostgreSQL Database**
  - Host, port, username, password, database name
- **Master Password**
  - For credential encryption (you'll set this during wizard)

### Optional Platform Integrations
- **Zendesk**
  - Subdomain (e.g., 'mycompany' from mycompany.zendesk.com)
  - Admin email
  - API token (Admin > Channels > API)

- **Intercom**
  - Access token (Settings > Developers > Access Tokens)

- **Mixpanel**
  - Project token
  - API secret (Settings > Project Settings)

- **SendGrid**
  - API key (Settings > API Keys)
  - Verified from email

## Wizard Steps

The wizard takes 5-10 minutes and walks you through:

1. **Welcome & System Check** (1 min)
   - Python version validation
   - Dependency verification
   - Disk space check

2. **Platform Integration Setup** (3-5 min)
   - Configure Zendesk, Intercom, Mixpanel, SendGrid
   - Credentials encrypted and stored securely
   - Skip any integrations you don't use

3. **Configuration** (2 min)
   - Health score weights (default: 35% usage, 25% engagement, etc.)
   - Risk thresholds (default: <60 at-risk, >75 healthy)
   - SLA targets (default: P1=4h, P2=8h, P3=24h)

4. **Database Initialization** (1 min)
   - Test database connection
   - Run migrations (creates all tables)
   - Create default segments

5. **Testing & Validation** (1 min)
   - Test all configured integrations
   - Verify database connectivity
   - Generate test report

6. **Completion** (1 min)
   - View configuration summary
   - Get setup report (saved to JSON)
   - See next steps

## Resume Interrupted Setup

If you need to stop the wizard (Ctrl+C), your progress is automatically saved:

```bash
# Simply run the wizard again
python -m src.tools.onboarding_wizard

# It will resume from the last completed step
```

State is saved to: `~/.config/cs-mcp/onboarding_state.json`

## After Setup

### Start the Server

```bash
python server.py
```

### Connect MCP Client

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "customer-success": {
      "command": "python",
      "args": ["/path/to/199os-customer-success-mcp/server.py"]
    }
  }
}
```

### Test Your Setup

1. Register your first customer
2. Calculate their health score
3. Create a support ticket (if Zendesk configured)
4. Send a test email (if SendGrid configured)

## Configuration Files

After setup, you'll have:

- `.env` - Environment variables and credentials
- `~/.config/cs-mcp/onboarding_state.json` - Wizard state
- `~/.config/cs-mcp/setup_report.json` - Setup summary
- `~/.config/cs-mcp/credentials/` - Encrypted credentials

## Troubleshooting

### Python Version Error
**Error:** "Python 3.8.0 ✗ (requires 3.10+)"
**Solution:** Upgrade Python to 3.10 or higher

### Missing Dependencies
**Error:** "Missing: fastmcp, pydantic ✗"
**Solution:** `pip install fastmcp pydantic sqlalchemy redis cryptography`

### Database Connection Failed
**Error:** "Database connection failed: Connection refused"
**Solution:** 
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify credentials are correct
- Check host/port are accessible

### Credential Manager Error
**Error:** "Could not initialize credential manager"
**Solution:**
- Ensure `cryptography` package is installed
- Check file permissions on `~/.config/cs-mcp/`
- Set CREDENTIAL_MASTER_PASSWORD environment variable

## Security Notes

- Credentials are encrypted with AES-256
- Master password required for encryption
- Credential files have 0600 permissions (owner only)
- Sensitive inputs are masked during entry
- Never commit `.env` file to version control

## Getting Help

- Documentation: `docs/`
- Issues: GitHub Issues
- Support: support@199os.com

## Example Session

```
$ python -m src.tools.onboarding_wizard

┌───────────────────────────────────────────────────────────┐
│ Welcome to Customer Success MCP Setup Wizard              │
│ This wizard will guide you through setting up your        │
│ Customer Success operations platform                      │
└───────────────────────────────────────────────────────────┘

What this wizard will do:
  1. Check your system requirements
  2. Configure platform integrations (Zendesk, Intercom, Mixpanel, SendGrid)
  3. Set up health scoring and retention thresholds
  4. Initialize database and create tables
  5. Test all integrations
  6. Generate setup report

Estimated time: 5-10 minutes

Ready to begin? [Y/n]: y

... [wizard runs through all steps] ...

┌───────────────────────────────────────────────────────────┐
│ Setup Complete!                                           │
└───────────────────────────────────────────────────────────┘

Congratulations! Your Customer Success MCP is ready to use.

Next Steps:
  1. Start the MCP server:
     python server.py

  2. Connect your MCP client (e.g., Claude Desktop)
     Add this configuration to your MCP settings:
     {"command": "python", "args": ["/path/to/server.py"]}

  3. Test with your first customer:
     Register a customer and calculate their health score

Thank you for using Customer Success MCP!
```

---

**Last Updated:** October 10, 2025
