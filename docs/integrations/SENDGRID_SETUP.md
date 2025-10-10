# SendGrid Integration Setup Guide

Complete guide to integrating Customer Success MCP with SendGrid for email delivery, templates, and tracking.

## Overview

The SendGrid integration enables:
- Send transactional emails
- Use dynamic email templates
- Track email engagement (opens, clicks)
- Handle bounces and spam reports
- Batch email delivery
- A/B testing campaigns
- SPF/DKIM email authentication

## Prerequisites

- SendGrid account (Free tier or higher)
- Verified sender email address
- API access enabled

## Creating API Key

### Step 1: Access API Keys

1. Log into SendGrid
2. Navigate to **Settings** → **API Keys**
3. Click **Create API Key**

### Step 2: Configure Permissions

1. **API Key Name**: `Customer Success MCP`
2. **API Key Permissions**: Select **Full Access** or customize:
   - Mail Send: **Full Access**
   - Templates: **Read Access**
   - Stats: **Read Access**
   - Suppressions: **Read Access**

### Step 3: Generate and Save

1. Click **Create & View**
2. **IMPORTANT**: Copy API key immediately (shown only once)
3. Store securely

Key format:
```
SG.abcdefghijklmnop.qrstuvwxyz1234567890ABCDEFGH
```

## Sender Verification

### Verify Single Sender

1. Go to **Settings** → **Sender Authentication** → **Single Sender Verification**
2. Click **Create New Sender**
3. Fill in details:
   - **From Name**: Your Company
   - **From Email Address**: noreply@yourcompany.com
   - **Reply To**: support@yourcompany.com
   - **Company Address**: (required)
4. Click **Save**
5. Check email inbox and click verification link

### Domain Authentication (Recommended for Production)

1. Go to **Settings** → **Sender Authentication** → **Authenticate Your Domain**
2. Enter your domain: `yourcompany.com`
3. Follow DNS configuration steps
4. Add provided DNS records (CNAME for SPF/DKIM)
5. Click **Verify**

Example DNS records:
```
Type: CNAME
Host: em1234.yourcompany.com
Value: u1234567.wl123.sendgrid.net

Type: CNAME
Host: s1._domainkey.yourcompany.com
Value: s1.domainkey.u1234567.wl123.sendgrid.net

Type: CNAME
Host: s2._domainkey.yourcompany.com
Value: s2.domainkey.u1234567.wl123.sendgrid.net
```

## Configuration

Add to `.env`:

```bash
# SendGrid Configuration
SENDGRID_API_KEY=SG.abcdefghijklmnop.qrstuvwxyz1234567890ABCDEFGH
SENDGRID_FROM_EMAIL=noreply@yourcompany.com
SENDGRID_FROM_NAME=Your Company
SENDGRID_REPLY_TO=support@yourcompany.com
SENDGRID_MAX_RETRIES=3
SENDGRID_RETRY_DELAY=1
SENDGRID_BATCH_SIZE=1000
```

Restart services:
```bash
docker-compose restart cs-mcp
```

## Testing the Integration

### Test Connection

```bash
curl -X POST http://localhost:8080/tools/test_sendgrid_connection
```

Expected response:
```json
{
  "status": "success",
  "verified_senders": ["noreply@yourcompany.com"],
  "domain_authenticated": true
}
```

### Send Test Email

```bash
curl -X POST http://localhost:8080/tools/send_personalized_email \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test-client",
    "to_email": "test@example.com",
    "subject": "Test Email from CS MCP",
    "content": "This is a test email to verify SendGrid integration.",
    "content_type": "text/plain"
  }'
```

### Send HTML Email

```bash
curl -X POST http://localhost:8080/tools/send_personalized_email \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test-client",
    "to_email": "jane@acmecorp.com",
    "subject": "Welcome to Our Platform",
    "content": "<h1>Welcome!</h1><p>We'\''re excited to have you.</p>",
    "content_type": "text/html"
  }'
```

## Email Templates

### Creating Dynamic Templates

1. In SendGrid, go to **Email API** → **Dynamic Templates**
2. Click **Create a Dynamic Template**
3. Enter template name: `Customer Welcome`
4. Click **Add Version**
5. Choose **Code Editor** or **Design Editor**
6. Add content with merge fields:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Welcome {{company_name}}</title>
</head>
<body>
  <h1>Welcome {{contact_name}}!</h1>
  <p>Thank you for joining {{company_name}}.</p>
  <p>Your health score is: {{health_score}}/100</p>
  <a href="{{dashboard_url}}">View Dashboard</a>
</body>
</html>
```

7. Save template and copy Template ID: `d-1234567890abcdef`

### Using Templates

```bash
curl -X POST http://localhost:8080/tools/send_template_email \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "acme-corp",
    "to_email": "jane@acmecorp.com",
    "template_id": "d-1234567890abcdef",
    "dynamic_data": {
      "company_name": "Acme Corp",
      "contact_name": "Jane",
      "health_score": 85,
      "dashboard_url": "https://app.example.com/dashboard"
    }
  }'
```

### Common Templates

**Welcome Email**:
```
Template ID: d-welcome
Merge Fields: company_name, contact_name, onboarding_url
```

**Health Score Alert**:
```
Template ID: d-health-alert
Merge Fields: company_name, health_score, issues, action_url
```

**Renewal Reminder**:
```
Template ID: d-renewal-reminder
Merge Fields: company_name, renewal_date, contract_value, renew_url
```

**Onboarding Milestone**:
```
Template ID: d-milestone
Merge Fields: company_name, milestone_name, progress, next_steps
```

## Batch Email Sending

For bulk emails, use batch sending:

```bash
curl -X POST http://localhost:8080/tools/send_bulk_emails \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "d-newsletter",
    "recipients": [
      {
        "email": "user1@example.com",
        "name": "User One",
        "data": {"custom_field": "value1"}
      },
      {
        "email": "user2@example.com",
        "name": "User Two",
        "data": {"custom_field": "value2"}
      }
    ]
  }'
```

Configuration:
```bash
SENDGRID_BATCH_SIZE=1000      # Max recipients per batch
SENDGRID_BATCH_DELAY=1        # Seconds between batches
```

## Email Tracking

### Tracking Settings

Enable in SendGrid: **Settings** → **Tracking**

- **Open Tracking**: Track email opens
- **Click Tracking**: Track link clicks
- **Subscription Tracking**: Unsubscribe links
- **Google Analytics**: UTM parameters

### Webhook Events

Receive real-time email events:

1. **Set Up Webhook**:
   - Go to **Settings** → **Mail Settings** → **Event Webhook**
   - HTTP Post URL: `https://your-server.com/webhooks/sendgrid`
   - Select events: Delivered, Opened, Clicked, Bounced, Spam Report

2. **Configure Webhook Secret**:
   ```bash
   SENDGRID_WEBHOOK_SECRET=your-webhook-verification-key
   ```

3. **Events Tracked**:
   - `delivered`: Email delivered successfully
   - `open`: Email opened
   - `click`: Link clicked
   - `bounce`: Hard or soft bounce
   - `dropped`: Email dropped (spam, invalid)
   - `spam_report`: Marked as spam
   - `unsubscribe`: User unsubscribed

### Query Email Stats

```bash
curl -X POST http://localhost:8080/tools/get_sendgrid_stats \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-10-01",
    "end_date": "2025-10-10"
  }'
```

Response:
```json
{
  "sent": 1500,
  "delivered": 1485,
  "opens": 892,
  "clicks": 345,
  "bounces": 8,
  "spam_reports": 2,
  "open_rate": 60.1,
  "click_rate": 23.2
}
```

## SPF and DKIM Setup

### Why Authentication Matters

- Prevents emails from being marked as spam
- Increases deliverability rates
- Builds sender reputation
- Required for high-volume sending

### SPF Configuration

Add to your domain's DNS:

```
Type: TXT
Host: @
Value: v=spf1 include:sendgrid.net ~all
```

Or if you have existing SPF:
```
v=spf1 include:sendgrid.net include:_spf.google.com ~all
```

### DKIM Configuration

SendGrid provides CNAME records during domain authentication. Add all three:

```
s1._domainkey.yourcompany.com → s1.domainkey.u1234567.wl123.sendgrid.net
s2._domainkey.yourcompany.com → s2.domainkey.u1234567.wl123.sendgrid.net
```

### Verify Setup

```bash
# Check SPF
dig TXT yourcompany.com +short

# Check DKIM
dig TXT s1._domainkey.yourcompany.com +short

# Test with SendGrid
curl -X GET http://localhost:8080/tools/verify_sendgrid_authentication
```

## Common Errors

### Error: Unauthorized (401)

**Cause**: Invalid API key

**Solution**:
```bash
# Test API key directly
curl -i --request POST \
  --url https://api.sendgrid.com/v3/mail/send \
  --header "Authorization: Bearer YOUR_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{"personalizations":[{"to":[{"email":"test@example.com"}]}],"from":{"email":"from@yourdomain.com"},"subject":"Test","content":[{"type":"text/plain","value":"Test"}]}'

# Generate new key if invalid
```

### Error: Forbidden (403)

**Cause**: Insufficient API key permissions

**Solution**:
- Recreate API key with Full Access
- Or grant specific permissions: Mail Send, Templates

### Error: Sender Identity Not Verified

**Cause**: From email not verified in SendGrid

**Solution**:
1. Go to Sender Authentication
2. Verify sender email
3. Check spam folder for verification email
4. Or use domain authentication

### Error: Template Not Found

**Cause**: Invalid template ID or not published

**Solution**:
```bash
# List all templates
curl -X GET http://localhost:8080/tools/list_sendgrid_templates

# Verify template ID
# Ensure template version is active
```

### Error: Daily Send Limit Exceeded

**Cause**: Free plan limits (100 emails/day)

**Solution**:
- Upgrade SendGrid plan
- Or spread sends over multiple days

### Error: Bounced Email

**Types**:
- **Hard Bounce**: Invalid email address (permanent)
- **Soft Bounce**: Mailbox full (temporary)

**Solution**:
```bash
# Check bounces
curl -X GET http://localhost:8080/tools/get_sendgrid_bounces

# Remove from future sends
curl -X POST http://localhost:8080/tools/suppress_email \
  -d '{"email": "bounced@example.com"}'
```

## Best Practices

### 1. Warm Up Your Domain

For new domains, gradually increase send volume:
- Week 1: 50 emails/day
- Week 2: 200 emails/day
- Week 3: 500 emails/day
- Week 4+: Full volume

### 2. Maintain List Hygiene

```bash
# Remove hard bounces
# Remove spam complaints
# Remove unsubscribes
# Re-engage inactive subscribers
```

### 3. Personalize Content

Always use recipient names and relevant data:
```html
<p>Hi {{first_name}},</p>
<p>Your {{company_name}} account health score is {{health_score}}.</p>
```

### 4. Monitor Engagement

Track and optimize:
- Open rates (target: >20%)
- Click rates (target: >3%)
- Bounce rates (keep <5%)
- Spam complaints (keep <0.1%)

### 5. Use Consistent From Address

Don't change sender frequently. Build reputation with single address.

### 6. Provide Unsubscribe Option

Required by law. Use SendGrid's subscription tracking:
```bash
SENDGRID_ENABLE_SUBSCRIPTION_TRACKING=true
```

## Advanced Configuration

### Custom Headers

Add custom headers to emails:

```bash
curl -X POST http://localhost:8080/tools/send_personalized_email \
  -d '{
    "to_email": "user@example.com",
    "subject": "Test",
    "content": "Test",
    "custom_headers": {
      "X-Campaign-ID": "retention-2025-q4",
      "X-Customer-Tier": "enterprise"
    }
  }'
```

### Categories and Tags

Organize emails for analytics:

```bash
{
  "categories": ["onboarding", "automated"],
  "custom_args": {
    "client_id": "acme-corp",
    "health_score": "85"
  }
}
```

### Send Time Optimization

Schedule emails for optimal delivery:

```bash
SENDGRID_ENABLE_SEND_TIME_OPTIMIZATION=true
SENDGRID_PREFERRED_SEND_TIME=09:00  # 9 AM local time
```

### A/B Testing

Test subject lines and content:

```bash
curl -X POST http://localhost:8080/tools/create_ab_test \
  -d '{
    "name": "Subject Line Test",
    "variant_a": {
      "subject": "Improve Your Health Score",
      "template_id": "d-template-a"
    },
    "variant_b": {
      "subject": "Your Account Needs Attention",
      "template_id": "d-template-b"
    },
    "split_percentage": 50
  }'
```

## Suppression Management

### Suppression Types

- **Global Unsubscribes**: Never email again
- **Group Unsubscribes**: Unsubscribed from specific category
- **Bounces**: Invalid addresses
- **Spam Reports**: Marked as spam
- **Blocks**: Blocked by recipient server

### Check Suppression Status

```bash
curl -X POST http://localhost:8080/tools/check_suppression_status \
  -d '{"email": "user@example.com"}'
```

### Remove from Suppression

```bash
# Only if user explicitly re-opts in
curl -X POST http://localhost:8080/tools/remove_from_suppression \
  -d '{"email": "user@example.com", "type": "bounces"}'
```

## Performance Optimization

### Async Sending

Emails are sent asynchronously:
```bash
SENDGRID_ASYNC_SENDING=true
SENDGRID_ASYNC_WORKERS=4
```

### Connection Pooling

Reuse HTTP connections:
```bash
SENDGRID_CONNECTION_POOL_SIZE=10
SENDGRID_CONNECTION_TIMEOUT=30
```

### Retry Logic

Automatic retries on failures:
```bash
SENDGRID_MAX_RETRIES=3
SENDGRID_RETRY_DELAY=1  # Seconds
SENDGRID_RETRY_BACKOFF=2  # Exponential multiplier
```

## Security

### API Key Rotation

Rotate keys every 90 days:
1. Create new API key
2. Update .env with new key
3. Test thoroughly
4. Delete old key

### Webhook Signature Verification

Verify webhook requests:
```bash
SENDGRID_VERIFY_WEBHOOK_SIGNATURES=true
SENDGRID_WEBHOOK_PUBLIC_KEY=your-public-key
```

### Rate Limiting

Respect SendGrid rate limits:
- Free: 100 emails/day
- Essentials: 100 emails/day (paid features)
- Pro: 100,000 emails/month
- Premier: 1.5M+ emails/month

## Support Resources

- [SendGrid API Docs](https://docs.sendgrid.com/api-reference)
- [Dynamic Templates Guide](https://docs.sendgrid.com/ui/sending-email/how-to-send-an-email-with-dynamic-templates)
- [Event Webhook](https://docs.sendgrid.com/for-developers/tracking-events/event)
- [CS MCP Tool Reference](../api/TOOL_REFERENCE.md)

---

**Last Updated**: October 2025