"""
API Fixtures
Mock API responses for external integrations - Zendesk, Intercom, Mixpanel, SendGrid
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any


# Zendesk API Response Fixtures
@pytest.fixture
def mock_zendesk_ticket_response() -> Dict[str, Any]:
    """Mock successful Zendesk ticket creation response"""
    return {
        "ticket": {
            "id": 12345,
            "url": "https://test.zendesk.com/api/v2/tickets/12345.json",
            "subject": "Login issue with SSO",
            "description": "Users cannot login using SSO authentication",
            "status": "open",
            "priority": "high",
            "type": "problem",
            "requester_id": 67890,
            "submitter_id": 67890,
            "assignee_id": None,
            "organization_id": 11111,
            "tags": ["sso", "authentication", "urgent"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "due_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
    }


@pytest.fixture
def mock_zendesk_tickets_list_response() -> Dict[str, Any]:
    """Mock Zendesk tickets list response"""
    return {
        "tickets": [
            {
                "id": 12345 + i,
                "subject": f"Test Ticket {i+1}",
                "status": ["new", "open", "pending", "solved"][i % 4],
                "priority": ["low", "normal", "high", "urgent"][i % 4],
                "created_at": (datetime.now() - timedelta(days=i)).isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            for i in range(10)
        ],
        "next_page": None,
        "previous_page": None,
        "count": 10
    }


@pytest.fixture
def mock_zendesk_user_response() -> Dict[str, Any]:
    """Mock Zendesk user response"""
    return {
        "user": {
            "id": 67890,
            "name": "John Smith",
            "email": "john.smith@acme.com",
            "phone": "+1-555-0123",
            "organization_id": 11111,
            "role": "end-user",
            "verified": True,
            "active": True,
            "created_at": (datetime.now() - timedelta(days=180)).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "tags": ["vip", "enterprise"],
            "custom_fields": {
                "customer_tier": "enterprise",
                "health_score": 82
            }
        }
    }


@pytest.fixture
def mock_zendesk_search_response() -> Dict[str, Any]:
    """Mock Zendesk search response"""
    return {
        "results": [
            {
                "id": 12345,
                "result_type": "ticket",
                "subject": "Login issue",
                "status": "open",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": 12346,
                "result_type": "ticket",
                "subject": "Feature request",
                "status": "pending",
                "created_at": (datetime.now() - timedelta(days=1)).isoformat()
            }
        ],
        "count": 2
    }


@pytest.fixture
def mock_zendesk_error_responses() -> Dict[str, Dict[str, Any]]:
    """Mock Zendesk error responses"""
    return {
        "unauthorized": {
            "error": "Unauthorized",
            "description": "Invalid API credentials"
        },
        "forbidden": {
            "error": "Forbidden",
            "description": "Insufficient permissions"
        },
        "rate_limit": {
            "error": "Rate limit exceeded",
            "description": "Too many requests. Retry after 60 seconds.",
            "retry_after": 60
        },
        "server_error": {
            "error": "Internal Server Error",
            "description": "Something went wrong on Zendesk's end"
        },
        "not_found": {
            "error": "RecordNotFound",
            "description": "Ticket not found"
        }
    }


# Intercom API Response Fixtures
@pytest.fixture
def mock_intercom_message_response() -> Dict[str, Any]:
    """Mock successful Intercom message response"""
    return {
        "type": "admin_message",
        "id": "msg_abc123",
        "created_at": int(datetime.now().timestamp()),
        "subject": "Welcome to Customer Success",
        "body": "<p>Thank you for being a valued customer!</p>",
        "message_type": "email",
        "conversation_id": "conv_xyz789",
        "admin": {
            "type": "admin",
            "id": "admin_123",
            "name": "Sarah Johnson",
            "email": "sarah@company.com"
        },
        "owner": {
            "type": "user",
            "id": "user_456",
            "email": "john.smith@acme.com"
        }
    }


@pytest.fixture
def mock_intercom_user_response() -> Dict[str, Any]:
    """Mock Intercom user response"""
    return {
        "type": "user",
        "id": "user_456",
        "user_id": "cs_1696800000_acme",
        "email": "john.smith@acme.com",
        "name": "John Smith",
        "phone": "+1-555-0123",
        "created_at": int((datetime.now() - timedelta(days=180)).timestamp()),
        "updated_at": int(datetime.now().timestamp()),
        "last_seen_at": int((datetime.now() - timedelta(hours=2)).timestamp()),
        "signed_up_at": int((datetime.now() - timedelta(days=180)).timestamp()),
        "custom_attributes": {
            "customer_tier": "enterprise",
            "health_score": 82,
            "lifecycle_stage": "active",
            "arr": 72000
        },
        "tags": {
            "type": "tag.list",
            "tags": [
                {"id": "tag_1", "name": "enterprise"},
                {"id": "tag_2", "name": "high_value"}
            ]
        },
        "companies": {
            "type": "company.list",
            "companies": [
                {
                    "id": "company_789",
                    "name": "Acme Corporation",
                    "company_id": "cs_1696800000_acme"
                }
            ]
        }
    }


@pytest.fixture
def mock_intercom_event_response() -> Dict[str, Any]:
    """Mock Intercom event tracking response"""
    return {
        "type": "event",
        "event_name": "feature_activated",
        "created_at": int(datetime.now().timestamp()),
        "user_id": "cs_1696800000_acme",
        "email": "john.smith@acme.com",
        "metadata": {
            "feature_name": "advanced_analytics",
            "activation_date": datetime.now().isoformat(),
            "user_count": 10
        }
    }


@pytest.fixture
def mock_intercom_error_responses() -> Dict[str, Dict[str, Any]]:
    """Mock Intercom error responses"""
    return {
        "unauthorized": {
            "type": "error.list",
            "request_id": "req_123",
            "errors": [
                {
                    "code": "unauthorized",
                    "message": "Access Token Invalid"
                }
            ]
        },
        "rate_limit": {
            "type": "error.list",
            "request_id": "req_124",
            "errors": [
                {
                    "code": "rate_limit_exceeded",
                    "message": "You have exceeded the rate limit"
                }
            ]
        },
        "server_error": {
            "type": "error.list",
            "request_id": "req_125",
            "errors": [
                {
                    "code": "server_error",
                    "message": "Internal Server Error"
                }
            ]
        }
    }


# Mixpanel API Response Fixtures
@pytest.fixture
def mock_mixpanel_track_response() -> Dict[str, Any]:
    """Mock successful Mixpanel event tracking response"""
    return {
        "status": 1,
        "error": None
    }


@pytest.fixture
def mock_mixpanel_batch_response() -> Dict[str, Any]:
    """Mock successful Mixpanel batch import response"""
    return {
        "status": 1,
        "num_records_imported": 100,
        "error": None
    }


@pytest.fixture
def mock_mixpanel_profile_response() -> Dict[str, Any]:
    """Mock Mixpanel user profile response"""
    return {
        "$distinct_id": "cs_1696800000_acme",
        "$properties": {
            "$email": "john.smith@acme.com",
            "$name": "John Smith",
            "$created": (datetime.now() - timedelta(days=180)).isoformat(),
            "$last_seen": (datetime.now() - timedelta(hours=2)).isoformat(),
            "customer_tier": "enterprise",
            "health_score": 82,
            "lifecycle_stage": "active",
            "total_logins": 245,
            "features_used": 12
        }
    }


@pytest.fixture
def mock_mixpanel_query_response() -> Dict[str, Any]:
    """Mock Mixpanel query API response"""
    return {
        "results": {
            "data": [
                {
                    "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                    "value": 50 + i * 5
                }
                for i in range(7, 0, -1)
            ]
        },
        "legend_size": 1,
        "status": "ok"
    }


@pytest.fixture
def mock_mixpanel_error_responses() -> Dict[str, Dict[str, Any]]:
    """Mock Mixpanel error responses"""
    return {
        "unauthorized": {
            "status": 0,
            "error": "Invalid API credentials"
        },
        "rate_limit": {
            "status": 0,
            "error": "Rate limit exceeded. Please retry after 60 seconds."
        },
        "invalid_request": {
            "status": 0,
            "error": "Invalid request parameters"
        },
        "server_error": {
            "status": 0,
            "error": "Internal server error"
        }
    }


# SendGrid API Response Fixtures
@pytest.fixture
def mock_sendgrid_send_response() -> Dict[str, Any]:
    """Mock successful SendGrid email send response"""
    return {
        "status_code": 202,
        "body": "",
        "headers": {
            "X-Message-Id": "msg_abc123xyz",
            "Content-Type": "text/plain; charset=utf-8"
        }
    }


@pytest.fixture
def mock_sendgrid_template_response() -> Dict[str, Any]:
    """Mock SendGrid template response"""
    return {
        "id": "template_123",
        "name": "Customer Success Welcome Email",
        "generation": "dynamic",
        "updated_at": datetime.now().isoformat(),
        "versions": [
            {
                "id": "version_456",
                "template_id": "template_123",
                "active": 1,
                "name": "Welcome Email V2",
                "subject": "Welcome to {{company_name}}!",
                "updated_at": datetime.now().isoformat()
            }
        ]
    }


@pytest.fixture
def mock_sendgrid_webhook_event() -> Dict[str, Any]:
    """Mock SendGrid webhook event"""
    return {
        "email": "john.smith@acme.com",
        "timestamp": int(datetime.now().timestamp()),
        "event": "delivered",
        "sg_event_id": "evt_abc123",
        "sg_message_id": "msg_abc123xyz",
        "campaign_id": "campaign_789",
        "response": "250 2.0.0 OK",
        "smtp-id": "<smtp_abc123@server.sendgrid.net>"
    }


@pytest.fixture
def mock_sendgrid_webhook_events() -> List[Dict[str, Any]]:
    """Mock multiple SendGrid webhook events"""
    event_types = ["delivered", "opened", "clicked", "bounced", "dropped"]
    return [
        {
            "email": "john.smith@acme.com",
            "timestamp": int((datetime.now() - timedelta(hours=i)).timestamp()),
            "event": event_types[i % len(event_types)],
            "sg_event_id": f"evt_{i:06d}",
            "sg_message_id": "msg_abc123xyz",
            "campaign_id": "campaign_789"
        }
        for i in range(10)
    ]


@pytest.fixture
def mock_sendgrid_error_responses() -> Dict[str, Dict[str, Any]]:
    """Mock SendGrid error responses"""
    return {
        "unauthorized": {
            "errors": [
                {
                    "message": "The provided authorization grant is invalid, expired, or revoked",
                    "field": None,
                    "help": None
                }
            ]
        },
        "rate_limit": {
            "errors": [
                {
                    "message": "Rate limit exceeded",
                    "field": None,
                    "help": "https://sendgrid.com/docs/api-rate-limits"
                }
            ]
        },
        "invalid_request": {
            "errors": [
                {
                    "message": "Invalid email address",
                    "field": "to",
                    "help": None
                }
            ]
        },
        "server_error": {
            "errors": [
                {
                    "message": "Internal server error",
                    "field": None,
                    "help": None
                }
            ]
        }
    }


# Generic API error responses
@pytest.fixture
def mock_api_timeout_error() -> Exception:
    """Mock API timeout error"""
    import requests
    return requests.exceptions.Timeout("Request timed out after 30 seconds")


@pytest.fixture
def mock_api_connection_error() -> Exception:
    """Mock API connection error"""
    import requests
    return requests.exceptions.ConnectionError("Failed to establish connection")


@pytest.fixture
def mock_api_network_error() -> Exception:
    """Mock generic network error"""
    import requests
    return requests.exceptions.RequestException("Network error occurred")


# HTTP Status Code Fixtures
@pytest.fixture
def mock_http_status_codes() -> Dict[int, str]:
    """Mock HTTP status codes and their meanings"""
    return {
        200: "OK",
        201: "Created",
        202: "Accepted",
        204: "No Content",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout"
    }


# Rate Limit Response Fixtures
@pytest.fixture
def mock_rate_limit_headers() -> Dict[str, str]:
    """Mock rate limit headers"""
    return {
        "X-RateLimit-Limit": "1000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(int((datetime.now() + timedelta(seconds=60)).timestamp())),
        "Retry-After": "60"
    }


# Webhook Signature Fixtures
@pytest.fixture
def mock_webhook_signatures() -> Dict[str, str]:
    """Mock webhook signature validation data"""
    return {
        "sendgrid_signature": "sha256=abc123def456",
        "intercom_signature": "sha1=xyz789abc123",
        "mixpanel_signature": "hmac_sha256=def456ghi789"
    }
