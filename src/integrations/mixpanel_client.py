"""Mixpanel Product Analytics Integration

Production-ready Mixpanel client for event tracking, profile management,
and analytics querying via the Mixpanel HTTP API.

Features:
- Event tracking with batching
- User profile management (set, increment)
- JQL query API for analytics
- Retry logic with exponential backoff
- Circuit breaker pattern
- Graceful error handling
"""
import os
import time
import json
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import structlog
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = structlog.get_logger(__name__)


class CircuitBreaker:
    """Circuit breaker pattern for API resilience"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == 'open':
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = 'half_open'
                logger.info("circuit_breaker_half_open", message="Attempting recovery")
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            result = func(*args, **kwargs)
            if self.state == 'half_open':
                self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise e

    def record_failure(self):
        """Record a failure and potentially open circuit"""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = 'open'
            logger.warning(
                "circuit_breaker_opened",
                failures=self.failures,
                threshold=self.failure_threshold
            )

    def reset(self):
        """Reset circuit breaker to closed state"""
        self.failures = 0
        self.last_failure_time = None
        self.state = 'closed'
        logger.info("circuit_breaker_closed", message="Circuit breaker reset")


class MixpanelClient:
    """Production-ready Mixpanel API client for product analytics"""

    # API endpoints
    TRACK_URL = "https://api.mixpanel.com/track"
    ENGAGE_URL = "https://api.mixpanel.com/engage"
    IMPORT_URL = "https://api.mixpanel.com/import"
    QUERY_URL = "https://mixpanel.com/api/2.0/jql"

    def __init__(
        self,
        project_token: Optional[str] = None,
        api_secret: Optional[str] = None,
        batch_size: int = 50,
        flush_interval: int = 10
    ):
        """
        Initialize Mixpanel client

        Args:
            project_token: Mixpanel project token (for tracking)
            api_secret: Mixpanel API secret (for querying)
            batch_size: Number of events to batch before auto-flush
            flush_interval: Seconds between auto-flushes
        """
        self.project_token = project_token or os.getenv("MIXPANEL_PROJECT_TOKEN")
        self.api_secret = api_secret or os.getenv("MIXPANEL_API_SECRET")

        if not self.project_token:
            logger.warning("mixpanel_not_configured", message="MIXPANEL_PROJECT_TOKEN not set")
            self.client = None
        else:
            logger.info("mixpanel_client_initialized", project_token_set=True)
            self.client = True

            # Setup HTTP session with retry logic
            self.session = self._create_session()

            # Batch tracking setup
            self.batch_size = batch_size
            self.flush_interval = flush_interval
            self.event_buffer = deque()
            self.last_flush_time = time.time()

            # Circuit breaker for resilience
            self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry configuration"""
        session = requests.Session()

        # Retry strategy: 3 retries with exponential backoff
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,  # 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _is_configured(self) -> bool:
        """Check if client is properly configured"""
        if not self.client:
            logger.warning("mixpanel_not_configured", message="Mixpanel client not initialized")
            return False
        return True

    def track_event(
        self,
        user_id: str,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Track a custom event for a user

        Args:
            user_id: Unique user identifier (distinct_id)
            event_name: Name of the event to track
            properties: Optional event properties
            timestamp: Optional event timestamp (defaults to now)

        Returns:
            dict: Status response with event_tracked boolean
        """
        if not self._is_configured():
            return {"status": "error", "error": "Mixpanel not configured", "event_tracked": False}

        try:
            # Build event payload
            event_data = {
                "event": event_name,
                "properties": {
                    "distinct_id": user_id,
                    "token": self.project_token,
                    "time": int((timestamp or datetime.now()).timestamp()),
                    **(properties or {})
                }
            }

            # Add to batch buffer
            self.event_buffer.append(event_data)

            # Auto-flush if batch size reached or interval expired
            if len(self.event_buffer) >= self.batch_size or \
               time.time() - self.last_flush_time >= self.flush_interval:
                self.flush()

            logger.info(
                "mixpanel_event_tracked",
                user_id=user_id,
                event=event_name,
                buffered=len(self.event_buffer)
            )

            return {
                "status": "success",
                "event_tracked": True,
                "buffered_events": len(self.event_buffer),
                "message": f"Event '{event_name}' queued for user {user_id}"
            }

        except Exception as e:
            logger.error("mixpanel_track_failed", user_id=user_id, event=event_name, error=str(e))
            return {"status": "error", "error": str(e), "event_tracked": False}

    def flush(self) -> Dict[str, Any]:
        """
        Flush buffered events to Mixpanel

        Returns:
            dict: Status with number of events flushed
        """
        if not self._is_configured() or not self.event_buffer:
            return {"status": "success", "events_flushed": 0}

        try:
            events_to_send = list(self.event_buffer)
            event_count = len(events_to_send)

            # Encode events
            data = base64.b64encode(json.dumps(events_to_send).encode()).decode()

            # Send to Mixpanel with circuit breaker
            def send_request():
                response = self.session.post(
                    self.TRACK_URL,
                    data={"data": data},
                    timeout=10
                )
                response.raise_for_status()
                return response.json()

            result = self.circuit_breaker.call(send_request)

            # Clear buffer on success
            self.event_buffer.clear()
            self.last_flush_time = time.time()

            logger.info("mixpanel_flush_success", events_flushed=event_count)

            return {
                "status": "success",
                "events_flushed": event_count,
                "api_response": result
            }

        except Exception as e:
            logger.error("mixpanel_flush_failed", events=len(self.event_buffer), error=str(e))
            return {"status": "error", "error": str(e), "events_flushed": 0}

    def set_profile(
        self,
        user_id: str,
        properties: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set user profile properties (creates or updates)

        Args:
            user_id: Unique user identifier
            properties: Profile properties to set
            ip_address: Optional IP address for geolocation

        Returns:
            dict: Status response
        """
        if not self._is_configured():
            return {"status": "error", "error": "Mixpanel not configured"}

        try:
            # Build profile update payload
            profile_data = {
                "$token": self.project_token,
                "$distinct_id": user_id,
                "$set": properties
            }

            if ip_address:
                profile_data["$ip"] = ip_address

            # Encode and send
            data = base64.b64encode(json.dumps([profile_data]).encode()).decode()

            def send_request():
                response = self.session.post(
                    self.ENGAGE_URL,
                    data={"data": data},
                    timeout=10
                )
                response.raise_for_status()
                return response.json()

            result = self.circuit_breaker.call(send_request)

            logger.info("mixpanel_profile_updated", user_id=user_id, properties=list(properties.keys()))

            return {
                "status": "success",
                "profile_updated": True,
                "user_id": user_id,
                "properties_set": len(properties),
                "api_response": result
            }

        except Exception as e:
            logger.error("mixpanel_profile_update_failed", user_id=user_id, error=str(e))
            return {"status": "error", "error": str(e), "profile_updated": False}

    def increment(
        self,
        user_id: str,
        properties: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Increment numeric user profile properties

        Args:
            user_id: Unique user identifier
            properties: Properties to increment (property_name: increment_amount)

        Returns:
            dict: Status response
        """
        if not self._is_configured():
            return {"status": "error", "error": "Mixpanel not configured"}

        try:
            # Build increment payload
            profile_data = {
                "$token": self.project_token,
                "$distinct_id": user_id,
                "$add": properties
            }

            # Encode and send
            data = base64.b64encode(json.dumps([profile_data]).encode()).decode()

            def send_request():
                response = self.session.post(
                    self.ENGAGE_URL,
                    data={"data": data},
                    timeout=10
                )
                response.raise_for_status()
                return response.json()

            result = self.circuit_breaker.call(send_request)

            logger.info("mixpanel_profile_incremented", user_id=user_id, properties=properties)

            return {
                "status": "success",
                "profile_incremented": True,
                "user_id": user_id,
                "increments": properties,
                "api_response": result
            }

        except Exception as e:
            logger.error("mixpanel_profile_increment_failed", user_id=user_id, error=str(e))
            return {"status": "error", "error": str(e), "profile_incremented": False}

    def get_events(
        self,
        jql_query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query events using Mixpanel JQL (JavaScript Query Language)

        Args:
            jql_query: JQL query string
            params: Optional query parameters

        Returns:
            dict: Query results or error

        Example JQL:
            function main() {
                return Events({
                    from_date: '2025-10-01',
                    to_date: '2025-10-31'
                })
                .filter(event => event.name === 'page_view')
                .groupBy(['properties.client_id'], mixpanel.reducer.count());
            }
        """
        if not self.api_secret:
            logger.warning("mixpanel_query_failed", message="MIXPANEL_API_SECRET not configured")
            return {"status": "error", "error": "API secret required for querying"}

        try:
            # Prepare authentication
            auth = (self.api_secret, '')

            # Prepare payload
            payload = {
                "script": jql_query,
                **(params or {})
            }

            def send_request():
                response = self.session.post(
                    self.QUERY_URL,
                    json=payload,
                    auth=auth,
                    timeout=30
                )
                response.raise_for_status()
                return response.json()

            result = self.circuit_breaker.call(send_request)

            logger.info("mixpanel_query_success", query_length=len(jql_query))

            return {
                "status": "success",
                "data": result,
                "query_executed": True
            }

        except requests.exceptions.HTTPError as e:
            logger.error("mixpanel_query_http_error", status_code=e.response.status_code, error=str(e))
            return {
                "status": "error",
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "query_executed": False
            }
        except Exception as e:
            logger.error("mixpanel_query_failed", error=str(e))
            return {"status": "error", "error": str(e), "query_executed": False}

    def track_usage_engagement(
        self,
        client_id: str,
        event_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track customer usage and engagement event

        Convenience method for tracking product usage events

        Args:
            client_id: Customer identifier
            event_type: Type of usage event (login, feature_usage, session_start, etc.)
            properties: Additional event properties

        Returns:
            dict: Tracking result
        """
        event_properties = {
            "client_id": client_id,
            "event_type": event_type,
            **(properties or {})
        }

        return self.track_event(
            user_id=client_id,
            event_name=f"cs_{event_type}",
            properties=event_properties
        )

    def close(self):
        """Close the client and flush any remaining events"""
        if self._is_configured() and self.event_buffer:
            logger.info("mixpanel_client_closing", buffered_events=len(self.event_buffer))
            self.flush()

        if hasattr(self, 'session'):
            self.session.close()

        logger.info("mixpanel_client_closed")
